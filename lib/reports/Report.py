class Report:
    def __init__(self, name: str = '', title: str = '', spreadsheet_id: str = '', datasource: str = '', add_filter: bool = True, frequency: int = 1, excel_filename: str = ''):
        self.summary_sheet_id = '1s_oro-4tJy_1R1G99TTPnL4-5ACR4BD-R1XWFvFuviQ'
        self.name = name
        self.title = title
        self.spreadsheet_id = spreadsheet_id
        self.excel_filename = excel_filename
        self.datasource = datasource
        self.result_query = ''
        self.add_filter = add_filter
        self.frequency = frequency