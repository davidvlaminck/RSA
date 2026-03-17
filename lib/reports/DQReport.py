import logging
from datetime import datetime, date, timedelta, UTC
from typing import Any

from googleapiclient.errors import HttpError

from lib.mail.MailSender import MailSender
from lib.reports.Report import Report
from outputs.sheets_cell import SheetsCell
from outputs.sheets_wrapper import SingleSheetsWrapper, SheetsWrapper
from factories import make_datasource, make_output
from outputs.base import OutputWriteContext


class DQReport(Report):
    def __init__(self, name: str = '', title: str = '', spreadsheet_id: str = '', datasource: str = '',
                 add_filter: bool = True, persistent_column: str = '', frequency: int = 1,
                 convert_columns_to_numbers: list | None = None, link_type: str = 'awvinfra',
                 recalculate_cells: list[tuple[str, str]] | None = None,
                 output: str = 'GoogleSheets', output_settings: dict | None = None,
                 excel_filename: str = ''):
        Report.__init__(self, name=name, title=title, spreadsheet_id=spreadsheet_id, datasource=datasource, add_filter=add_filter,
                        frequency=frequency, excel_filename=excel_filename)
        self.last_data_update = ''
        self.now = ''
        self.link_type = link_type
        self.recalculate_cells = recalculate_cells
        if self.recalculate_cells is None:
            self.recalculate_cells = []
        self.persistent_column = persistent_column
        self.persistent_dict = {}
        if convert_columns_to_numbers is None:
            self.convert_columns_to_numbers = []
        else:
            self.convert_columns_to_numbers = convert_columns_to_numbers
        self.output = output
        self.output_settings = output_settings or {}

    def run_report(self, startcell: str = 'A1', sender: MailSender = None):
        logging.info(f'start running report {self.name}: {self.title}')

        # Resolve adapters
        ds = make_datasource(self.datasource)
        # If this report has an excel_filename configured, prefer Excel output adapter
        if getattr(self, 'excel_filename', None):
            out = make_output('Excel', settings=self.output_settings)
        else:
            out = make_output(self.output, settings=self.output_settings)

        # test connection first before proceeding with the report
        ds.test_connection()

        sheets_wrapper = SingleSheetsWrapper.get_wrapper()

        # read mail receivers (unchanged behavior)
        mail_receivers = None
        try:
            mail_receivers_raw = sheets_wrapper.read_data_from_sheet(spreadsheet_id=self.spreadsheet_id, sheet_name='Overzicht',
                                                                 sheetrange='emails', return_raw_results=True)
            # Normalize fallback return shapes:
            # - if a list was returned, wrap into dict
            # - if a dict without 'range' was returned (Excel fallback), synthesize a range
            if isinstance(mail_receivers_raw, list):
                mail_receivers_raw = {'values': mail_receivers_raw, 'range': 'Overzicht!A1:A{}'.format(len(mail_receivers_raw))}
            if isinstance(mail_receivers_raw, dict):
                values = mail_receivers_raw.get('values', [])
                if not values:
                    mail_receivers = []
                    mail_receivers_dict = []
                    # no receivers configured; continue without adding sheet info
                    mail_receivers = []
                else:
                    # ensure 'range' exists
                    if 'range' not in mail_receivers_raw:
                        # estimate a reasonable range based on values length and columns
                        cols = max((len(r) for r in values), default=1)
                        end_col = chr(64 + cols) if cols <= 26 else 'Z'
                        mail_receivers_raw['range'] = f'Overzicht!A1:{end_col}{len(values)}'
                    mail_receivers = mail_receivers_raw.get('values', [])
                    mail_receivers_dict = self.transform_raw_to_dict(mail_receivers_raw)
                    sender.add_sheet_info(spreadsheet_id=self.spreadsheet_id, mail_receivers_dict=mail_receivers_dict)
            else:
                # unexpected return type: skip mail receivers
                mail_receivers = []
                mail_receivers_dict = []
        except HttpError as exc:
            # Common failure: Google API returns 403 when the service account/app has no access to the
            # target spreadsheet. For robustness we try to fall back to the Excel-backed SheetsCompatAdapter
            # (if available) or otherwise continue without mail receivers (safe default).
            status = None
            try:
                status = getattr(exc, 'resp', None) and getattr(exc.resp, 'status', None)
            except Exception:
                status = None

            if status == 403 or 'permission' in str(exc).lower() or 'permission_denied' in str(exc).lower():
                logging.warning(f'Google Sheets permission error reading Overzicht!emails: {exc}; falling back to Excel or skipping mail receivers')
                # Attempt to register Excel-backed adapter as a fallback and retry once
                try:
                    from outputs.excel_wrapper import SingleExcelWriter
                    from outputs.sheets_compat import SheetsCompatAdapter
                    if getattr(SingleExcelWriter, 'get_wrapper', None):
                        SingleSheetsWrapper.sheets_wrapper = SheetsCompatAdapter(SingleExcelWriter.get_wrapper())
                        sheets_wrapper = SingleSheetsWrapper.get_wrapper()
                        try:
                            mail_receivers_raw = sheets_wrapper.read_data_from_sheet(spreadsheet_id=self.spreadsheet_id,
                                                                                     sheet_name='Overzicht',
                                                                                     sheetrange='emails', return_raw_results=True)
                        except Exception:
                            mail_receivers_raw = []
                    else:
                        mail_receivers_raw = []
                except Exception:
                    # If any of the fallback steps fail, continue with empty receivers
                    mail_receivers_raw = []
            elif getattr(exc, 'error_details', None) == 'Unable to parse range: Overzicht!emails':
                logging.info(f'{self.__class__.__name__} does not have a range Overzicht!emails')
                mail_receivers_raw = []
            else:
                # Unknown HttpError: log and continue without mail receivers instead of failing the whole report
                logging.warning(f'Unexpected HttpError while reading Overzicht!emails: {exc}; continuing without mail receivers')
                mail_receivers_raw = []

        previous_result, latest_data_sync = self.get_historiek_record_info(sheets_wrapper)

        # persistent column (unchanged logic): read existing values from current Resultaat sheet
        if self.persistent_column != '':
            self.persistent_dict = {}

            sheets = sheets_wrapper.get_sheets_in_spreadsheet(spreadsheet_id=self.spreadsheet_id)
            if 'Resultaat' in sheets:
                first_cell = SheetsCell(self.persistent_column + '1')
                first_nonempty_row = sheets_wrapper.find_first_nonempty_row_from_starting_cell(spreadsheet_id=self.spreadsheet_id,
                                                                                               sheet_name='Resultaat',
                                                                                               start_cell=first_cell.cell)

                grid_props = sheets['Resultaat']['gridProperties']
                max_row = grid_props['rowCount']

                ids = sheets_wrapper.read_data_from_sheet(spreadsheet_id=self.spreadsheet_id,
                                                          sheet_name='Resultaat',
                                                          sheetrange='A' + str(first_nonempty_row) + ':A' + str(max_row))
                persisent_column_data = sheets_wrapper.read_data_from_sheet(spreadsheet_id=self.spreadsheet_id,
                                                                            sheet_name='Resultaat',
                                                                            sheetrange=self.persistent_column + str(
                                                                                first_nonempty_row) + ':' + self.persistent_column + str(
                                                                                max_row))

                combined_list = zip(ids, persisent_column_data)
                for id, persistent_item in combined_list:
                    if id != [] and id[0] != '' and persistent_item != [] and persistent_item[0] != '':
                        self.persistent_dict[id[0]] = persistent_item[0]

        # execute query via datasource adapter
        query_time = None
        self.now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")

        if self.datasource == 'Neo4J':
            self.result_query = self.clean_query(self.result_query)

        qr = ds.execute(self.result_query)
        query_time = qr.query_time_seconds
        self.last_data_update = qr.last_data_update or ''

        # If a per-report `last_update_query` is configured, prefer its result as the
        # authoritative datasource last-update timestamp. This allows reports to run a
        # lightweight metadata query (e.g., SELECT max(updated_at) FROM ...) and return
        # the precise value to be shown in Overzicht column C.
        if getattr(self, 'last_update_query', None):
            try:
                lu_qr = ds.execute(self.last_update_query)
                # extract first cell of first row if available
                lu_val = None
                if lu_qr and getattr(lu_qr, 'rows', None):
                    if len(lu_qr.rows) > 0:
                        first = lu_qr.rows[0]
                        if isinstance(first, dict):
                            # pick first value
                            vals = list(first.values())
                            if vals:
                                lu_val = vals[0]
                        elif isinstance(first, (list, tuple)):
                            if len(first) > 0:
                                lu_val = first[0]
                if lu_val is not None:
                    # normalize using same helper used for historiek staging
                    def _normalize_to_utc_string_local(val):
                        from datetime import datetime, timezone
                        import re
                        if val is None:
                            return ''
                        if isinstance(val, (int, float)):
                            return str(val)
                        s = str(val).strip()
                        if s == '':
                            return ''
                        try:
                            iso = s.replace('Z', '+00:00') if s.endswith('Z') else s
                            try:
                                dt = datetime.fromisoformat(iso)
                            except Exception:
                                dt = None
                            if dt is None:
                                fmts = [
                                    '%Y-%m-%d %H:%M:%S',
                                    '%Y-%m-%dT%H:%M:%S.%f%z',
                                    '%Y-%m-%dT%H:%M:%S%z',
                                    '%Y-%m-%d %H:%M:%S%z',
                                    '%Y-%m-%dT%H:%M:%S.%f',
                                    '%Y-%m-%dT%H:%M:%S',
                                ]
                                for f in fmts:
                                    try:
                                        dt = datetime.strptime(s, f)
                                        break
                                    except Exception:
                                        dt = None
                            if dt is None:
                                m = re.search(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[+-]\d{2}:?\d{2}|Z)?", s)
                                if m:
                                    piece = m.group(0).replace('Z', '+00:00')
                                    try:
                                        dt = datetime.fromisoformat(piece)
                                    except Exception:
                                        dt = None
                            if dt is None:
                                return s
                            if dt.tzinfo is None:
                                dt = dt.replace(tzinfo=timezone.utc)
                            dt_utc = dt.astimezone(timezone.utc)
                            return dt_utc.strftime('%Y-%m-%d %H:%M:%S')
                        except Exception:
                            return str(val)

                    normalized_lu = _normalize_to_utc_string_local(lu_val)
                    if normalized_lu:
                        self.last_data_update = normalized_lu
                        try:
                            logging.info('%s: last_update_query override supplied last_data_update=%r', self.name, self.last_data_update)
                        except Exception:
                            pass
            except Exception:
                logging.exception('Failed to execute last_update_query for %s', self.name)
        # Log datasource-provided last_data_update for troubleshooting Overzicht timestamps
        try:
            logging.info('%s: datasource last_data_update=%r', self.name, self.last_data_update)
        except Exception:
            pass

        # write output via output adapter
        ctx = OutputWriteContext(
            spreadsheet_id=self.spreadsheet_id,
            report_title=self.title,
            datasource_name=self.datasource,
            now_utc=self.now,
            excel_filename=self.excel_filename or None,
        )
        # Capture metadata returned by the output writer (e.g., file path, rows_written)
        try:
            meta = out.write_report(
                ctx,
                qr,
                startcell=startcell,
                add_filter=self.add_filter,
                persistent_column=self.persistent_column,
                persistent_dict=self.persistent_dict,
                convert_columns_to_numbers=self.convert_columns_to_numbers,
                link_type=self.link_type,
                recalculate_cells=self.recalculate_cells,
            )
        except Exception:
            meta = None

        # store for diagnostics and log
        self.last_output_meta = meta
        logging.info('Output writer meta: %s', meta)

        # historiek: instead of writing directly to sheets (which may be Google or Excel),
        # stage an append_row payload for the aggregator to apply later. This avoids concurrent
        # writers clobbering each other in parallel runs.
        try:
            from outputs.summary_stager import stage_summary_update
            staged_dir = self.output_settings.get('staged_dir') if isinstance(self.output_settings, dict) and self.output_settings.get('staged_dir') else None
            # determine target workbook identifier for aggregator: prefer excel_filename if created
            target_workbook = ctx.excel_filename if getattr(ctx, 'excel_filename', None) else self.spreadsheet_id

            # compute rowFound using column F 'rapportnummer' which should contain the report class name.
            # Read the Overzicht sheet and search column F for self.name. Default to row 4 if not found.
            try:
                # Read column F (rapportnummer) and column B (links) to robustly locate the report row.
                ovF = sheets_wrapper.read_data_from_sheet(spreadsheet_id=self.summary_sheet_id, sheet_name='Overzicht', sheetrange='F4:F1000')
                # read B with raw cell data to inspect hyperlinks if available
                try:
                    ovB_raw = sheets_wrapper.read_celldata_from_sheet(spreadsheet_id=self.summary_sheet_id, sheet_name='Overzicht', sheetrange='B4:B1000')
                    ovB_values = ovB_raw.get('values', [])
                    ovB_rowdata = ovB_raw.get('rowData', [])
                except Exception:
                    ovB_values = sheets_wrapper.read_data_from_sheet(spreadsheet_id=self.summary_sheet_id, sheet_name='Overzicht', sheetrange='B4:B1000') or []
                    ovB_rowdata = []

                rowFound = 4
                target_name = (self.name or '').strip().lower()
                target_sheet_id = (self.spreadsheet_id or '')

                # iterate rows and try multiple matching strategies
                max_rows = max(len(ovF or []), len(ovB_values or []))
                for idx in range(max_rows):
                    # check F column match first (rapportnummer)
                    try:
                        fval = ovF[idx][0] if ovF and idx < len(ovF) and ovF[idx] and len(ovF[idx]) > 0 else ''
                    except Exception:
                        fval = ''
                    if str(fval).strip().lower() == target_name and target_name != '':
                        rowFound = 4 + idx
                        break

                    # check B column hyperlinks/values for spreadsheet id or excel filename
                    try:
                        bval = ovB_values[idx][0] if ovB_values and idx < len(ovB_values) and ovB_values[idx] and len(ovB_values[idx]) > 0 else ''
                    except Exception:
                        bval = ''

                    # inspect rich rowData hyperlink if available
                    hyperlink_found = False
                    try:
                        if ovB_rowdata and idx < len(ovB_rowdata):
                            cellinfo = ovB_rowdata[idx]['values'][0]
                            link = cellinfo.get('hyperlink') or ''
                            if link and target_sheet_id and target_sheet_id in str(link):
                                hyperlink_found = True
                    except Exception:
                        hyperlink_found = False

                    if hyperlink_found:
                        rowFound = 4 + idx
                        break

                    # fallback: direct value match in B to spreadsheet_id or excel_filename
                    if target_sheet_id and str(bval).strip() != '' and target_sheet_id in str(bval):
                        rowFound = 4 + idx
                        break

                # if nothing matched, leave rowFound as 4 (default)
            except Exception:
                rowFound = 4  # fallback

            try:
                logging.info('%s: determined rowFound=%s for summary target=%s', self.name, rowFound, summary_target)
            except Exception:
                pass

            last_data_update = None
            historiek_data = None
            try:
                historiek_data = sheets_wrapper.read_data_from_sheet(spreadsheet_id=self.spreadsheet_id,
                                                                     sheet_name='Historiek',
                                                                     sheetrange='B2:B2')
                if len(historiek_data) > 0:
                    last_data_update = historiek_data[0][0]
            except Exception:
                last_data_update = None

            # append historiek row
            # Normalize last_data_update to UTC 'YYYY-MM-DD HH:MM:SS' when staging summary/historiek
            def _normalize_to_utc_string(val):
                from datetime import datetime, timezone
                import re
                if val is None:
                    return ''
                if isinstance(val, (int, float)):
                    return str(val)
                s = str(val).strip()
                if s == '':
                    return ''
                # try iso first (handle trailing Z)
                try:
                    iso = s.replace('Z', '+00:00') if s.endswith('Z') else s
                    try:
                        dt = datetime.fromisoformat(iso)
                    except Exception:
                        dt = None
                    if dt is None:
                        fmts = [
                            '%Y-%m-%d %H:%M:%S',
                            '%Y-%m-%dT%H:%M:%S.%f%z',
                            '%Y-%m-%dT%H:%M:%S%z',
                            '%Y-%m-%d %H:%M:%S%z',
                            '%Y-%m-%dT%H:%M:%S.%f',
                            '%Y-%m-%dT%H:%M:%S',
                        ]
                        for f in fmts:
                            try:
                                dt = datetime.strptime(s, f)
                                break
                            except Exception:
                                dt = None
                    if dt is None:
                        m = re.search(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[+-]\d{2}:?\d{2}|Z)?", s)
                        if m:
                            piece = m.group(0).replace('Z', '+00:00')
                            try:
                                dt = datetime.fromisoformat(piece)
                            except Exception:
                                dt = None
                    if dt is None:
                        return s
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    dt_utc = dt.astimezone(timezone.utc)
                    return dt_utc.strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    return str(val)

            payload_hist = {
                'operation': 'append_row',
                'excel_filename': target_workbook if ctx.excel_filename else None,
                'spreadsheet_id': None if ctx.excel_filename else self.spreadsheet_id,
                'sheet': 'Historiek',
                'row': [self.now, _normalize_to_utc_string(self.last_data_update), len(qr.rows)],
                'meta': {'report': self.name}
            }
            # clean payload: remove None keys
            if payload_hist['excel_filename'] is None:
                del payload_hist['excel_filename']
            if payload_hist['spreadsheet_id'] is None:
                del payload_hist['spreadsheet_id']

            stage_summary_update(payload_hist, staged_dir=staged_dir or 'RSA_OneDrive/staged_summaries')

            # Summary sheet updates: write last_data_update and count into Overzicht at column C and query_time into column H
            # rowFound already points to the row (e.g., 4-based). Use exact cell coordinates when staging payloads.
            summary_target = self.summary_sheet_id
            c_cell = f'C{rowFound}'
            h_cell = f'H{rowFound}'

            payload_summary_c = {
                'operation': 'write_cell',
                'spreadsheet_id': summary_target,
                'sheet': 'Overzicht',
                'cell': c_cell,
                'value': [_normalize_to_utc_string(self.last_data_update), len(qr.rows)],
                'meta': {'report': self.name}
            }

            payload_summary_h = {
                'operation': 'write_cell',
                'spreadsheet_id': summary_target,
                'sheet': 'Overzicht',
                'cell': h_cell,
                'value': query_time,
                'meta': {'report': self.name}
            }

            stage_summary_update(payload_summary_c, staged_dir=staged_dir or 'RSA_OneDrive/staged_summaries')
            stage_summary_update(payload_summary_h, staged_dir=staged_dir or 'RSA_OneDrive/staged_summaries')
            # Log the exact staged payloads for post-aggregation verification
            try:
                logging.info('%s: staged Overzicht C payload cell=%s value=%r', self.name, c_cell, payload_summary_c.get('value'))
                logging.info('%s: staged Overzicht H payload cell=%s value=%r', self.name, h_cell, payload_summary_h.get('value'))
            except Exception:
                pass

        except Exception as ex:
            # fallback to original direct writes if staging isn't available
            try:
                logging.warning(f'Summary staging failed: {ex}; falling back to direct writes')
                if last_data_update != self.last_data_update:
                    sheets_wrapper.insert_empty_rows(spreadsheet_id=self.spreadsheet_id, sheet_name='Historiek', start_cell='A2',
                                                     number_of_rows=1)
                sheets_wrapper.write_data_to_sheet(spreadsheet_id=self.spreadsheet_id, sheet_name='Historiek', start_cell='A2',
                                                   data=[[self.now, self.last_data_update, len(qr.rows)]])
                # Use the same rowFound that was computed above for staged payloads
                sheets_wrapper.write_data_to_sheet(spreadsheet_id=self.summary_sheet_id, sheet_name='Overzicht', start_cell='C' + str(rowFound),
                                                   data=[[self.last_data_update, len(qr.rows)]])
                try:
                    sheets_wrapper.write_data_to_sheet(spreadsheet_id=self.summary_sheet_id, sheet_name='Overzicht', start_cell='H' + str(rowFound),
                                                       data=[[query_time]])
                except Exception:
                    pass
            except Exception:
                logging.exception('Failed both staging and fallback writes for historiek/summary')

        if mail_receivers is not None:
            self.send_mails(sender=sender, named_range=mail_receivers, previous_result=previous_result,
                            result=len(qr.rows), latest_data_sync=self.last_data_update)

        logging.info(f'finished report {self.name}')

    @staticmethod
    def clean(result_data, headerrow: list[str] | None = None):
        """Removes the empty rows in the results, converts lists, decimals and dates to strings.

        Backwards compatible: headerrow is optional. If present and a row is a dict, use headerrow to
        order dict values; if headerrow is None and row is a dict, use the dict's keys iteration order.
        """
        new_result_data = []

        for row in result_data:
            if isinstance(row, dict):
                # if no headerrow provided, derive an order from dict keys
                cols = headerrow if headerrow is not None else list(row.keys())
                row = [row.get(key, '') for key in cols]

            if isinstance(row, tuple):
                row = list(row)

            if isinstance(row, list):
                # treat a row as empty if all columns are None or ''
                all_empty = True
                for column in row:
                    if column is not None and column != '':
                        all_empty = False
                        break
                if all_empty:
                    continue

            new_row = []
            for column in row:
                if column is None:
                    new_row.append(None)
                elif not isinstance(column, str):
                    if isinstance(column, datetime):
                        new_row.append(column.strftime('%Y-%m-%d %H:%M:%S'))
                    elif isinstance(column, date):
                        new_row.append(column.strftime('%Y-%m-%d'))
                    elif isinstance(column, list):
                        new_row.append(DQReport.make_list_into_strings(column))
                    else:
                        new_row.append(str(column))
                else:
                    new_row.append(column)
            row = new_row

            new_result_data.append(row)
        return new_result_data

    def send_mails(self, sender: MailSender, named_range: list[list[Any]], previous_result: int, result: int,
                   latest_data_sync: str = ''):
        if len(named_range) == 0:
            return

        for line in named_range:
            if line is None or len(line) < 2 or line[0] == '' or line[0] is None:
                continue
            if line[1] == 'Wijziging':
                if previous_result != result:
                    sender.add_mail(receiver=line[0], report_name=self.title, spreadsheet_id=self.spreadsheet_id,
                                    count=result, latest_sync=latest_data_sync, frequency=line[1],
                                    previous = previous_result)
                    # add frequency
            elif line[1] in ['Dagelijks', 'Wekelijks', 'Maandelijks', 'Jaarlijks']:
                if len(line) < 3 or line[2] == '' or line[2] is None:
                    sender.add_mail(receiver=line[0], report_name=self.title, spreadsheet_id=self.spreadsheet_id,
                                    count=result, latest_sync=latest_data_sync, frequency=line[1],
                                    previous = previous_result)
                else:
                    dt = datetime.strptime(line[2], '%Y-%m-%d %H:%M:%S')
                    last_sent = dt.date()
                    if line[1] == 'Dagelijks':
                        diff_days = date.today() - last_sent
                        if diff_days >= timedelta(days=1):
                            sender.add_mail(receiver=line[0], report_name=self.title, spreadsheet_id=self.spreadsheet_id,
                                            count=result, latest_sync=latest_data_sync, frequency=line[1])
                    elif line[1] == 'Wekelijks':
                        diff_days = date.today() - last_sent
                        if diff_days >= timedelta(days=7):
                            sender.add_mail(receiver=line[0], report_name=self.title, spreadsheet_id=self.spreadsheet_id,
                                            count=result, latest_sync=latest_data_sync, frequency=line[1])
                    elif line[1] == 'Maandelijks':
                        current_month = date.today().month
                        if current_month != last_sent.month:
                            sender.add_mail(receiver=line[0], report_name=self.title, spreadsheet_id=self.spreadsheet_id,
                                            count=result, latest_sync=latest_data_sync, frequency=line[1])
                    elif line[1] == 'Jaarlijks':
                        current_month = date.today().year
                        if current_month != last_sent.year:
                            sender.add_mail(receiver=line[0], report_name=self.title, spreadsheet_id=self.spreadsheet_id,
                                            count=result, latest_sync=latest_data_sync, frequency=line[1])

    def get_historiek_record_info(self, sheets_wrapper: SheetsWrapper) -> tuple[int | None, str]:
        results = sheets_wrapper.read_data_from_sheet(spreadsheet_id=self.spreadsheet_id, sheet_name='Historiek',
                                                      sheetrange='B2:C2')

        if len(results) == 0:
            return None, ''
        latest_sync = results[0][0]
        previous_count = results[0][1]
        return int(previous_count), latest_sync

    def transform_raw_to_dict(self, mail_receivers_raw) -> list[dict[str, Any]]:
        mail_dicts = []
        sheetrange = mail_receivers_raw['range'].split('!')[1]
        cells = sheetrange.split(':')
        # cells[0] may be empty (e.g. ':B') or may contain only column letters (e.g. 'B').
        # Normalize to a valid A1-style cell (column+row). Default row is 1 when missing.
        raw_start = cells[0].strip() if len(cells) > 0 else ''
        raw_end = cells[1].strip() if len(cells) > 1 else ''
        if not raw_start:
            raw_start = raw_end or 'A1'
        # if raw_start contains no digits (only column letters), append row 1
        if not any(ch.isdigit() for ch in raw_start):
            raw_start = raw_start + '1'
        try:
            startcell = SheetsCell(raw_start)
        except Exception as e:
            logging.warning('Could not parse start cell "%s" from range "%s": %s. Falling back to A1', raw_start, sheetrange, e)
            startcell = SheetsCell('A1')
        startcell.update_column_by_adding_number(2)
        if 'values' not in mail_receivers_raw:
            return mail_dicts
        for list_element in mail_receivers_raw['values']:
            if len(list_element) < 2:
                # Malformed entry: skip and log a warning instead of raising to allow offline runs
                # e.g. when Overzicht sheet is minimal during Excel-only testing.
                logging.warning('Skipping malformed mail receiver entry (expected >=2 columns): %s', list_element)
                continue

            mail_dict = {}
            mail_dicts.append(mail_dict)
            mail_dict['mail'] = list_element[0]
            mail_dict['frequency'] = list_element[1]
            mail_dict['cell'] = startcell.cell
            if len(list_element) > 2:
                mail_dict['last_update'] = list_element[2]

            startcell.row += 1

        return mail_dicts

    def clean_query(self, query):
        query_lines = query.split('\n')
        new_q = []
        for line in query_lines:
            if '//' not in line:
                new_q.append(line)
            else:
                new_q.append(line.split('//')[0])
        return '\n'.join(new_q)

    @classmethod
    def make_list_into_strings(cls, data: list, sep: str = '|'):
        if not isinstance(data, list):
            return data
        for index, value in enumerate(data):
            if isinstance(value, list):
                value = cls.make_list_into_strings(value, sep = f'|{sep}')
                data[index] = value
        return sep.join([str(d) for d in data])
