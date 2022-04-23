from Report import Report
from SheetsWrapper import SingleSheetsWrapper


class DQReport(Report):
    def __init__(self, name: str = '', title: str = '', spreadsheet_id: str = '', datasource: str = ''):
        Report.__init__(self, name=name, title=title, spreadsheet_id=spreadsheet_id, datasource=datasource)

    @staticmethod
    def run_report():
        sheets_wrapper = SingleSheetsWrapper.get_wrapper()
        print('init of a sheetswrapper succeeded')