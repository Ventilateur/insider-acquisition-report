import json
from typing import List, Dict
from urllib.parse import urlparse

from xlsxwriter import Workbook

from sec4.const import sec4_transactions as tb


class ExcelColumn:
    def __init__(self, idx, name, fmt=None, transform=lambda v: v):
        self.idx = idx
        self.name = name
        self.format = fmt if fmt else {}
        self.transform = transform
        self.width = len(name)


def _to_web(sec4_url):
    return f"https://sec.report/Document/{str(urlparse(sec4_url).path.split('/')[-1]).split('.')[0]}/"


db_to_excel = {
    tb.company_name: ExcelColumn(0, 'Company name'),
    tb.company_code: ExcelColumn(1, 'Company code'),
    tb.insiders: ExcelColumn(2, 'Insiders', {'text_wrap': True}, lambda v: "\n\r".join(filter(None, json.loads(v)))),
    tb.price: ExcelColumn(3, 'Price', {'num_format': '#,##0.00'}),
    tb.nb_shares: ExcelColumn(4, 'Quantity', {'num_format': '#,##0'}),
    tb.transaction_date: ExcelColumn(6, 'Transaction date', {'num_format': 'dd-mmm-yyyy'}),
    tb.buy_or_sell: ExcelColumn(7, 'Buy/Sell'),
    tb.security_title: ExcelColumn(8, 'Security title'),
    tb.sec4_file_location: ExcelColumn(9, 'SEC4 file', transform=lambda v: _to_web(v))
}

col_total = ExcelColumn(5, 'Total amount', {'num_format': '#,##0.00'})


def build(data: List[Dict], file_name: str):
    with Workbook(file_name) as wb:
        ws = wb.add_worksheet('Detail')

        # Write data
        for i, transaction in enumerate(data):
            for db_col, excel_col in db_to_excel.items():
                cell_data = excel_col.transform(transaction[db_col.name])
                w = max([len(line) for line in str(cell_data).split('\n\r')])
                if w > excel_col.width:
                    excel_col.width = w
                ws.write(i + 1, excel_col.idx, cell_data, wb.add_format(excel_col.format))

            total_amount = transaction[tb.price.name] * transaction[tb.nb_shares.name]
            ws.write(i + 1, col_total.idx, total_amount, wb.add_format(col_total.format))
            w = len(str(total_amount))
            if w > col_total.width:
                col_total.width = w

        # Write headers and adjust column widths
        for col in db_to_excel.values():
            ws.write(0, col.idx, col.name, wb.add_format({'bold': True, 'align': 'center'}))
            ws.set_column(col.idx, col.idx, col.width * 1.1)
        ws.write(0, col_total.idx, col_total.name, wb.add_format({'bold': True, 'align': 'center'}))
        ws.set_column(col_total.idx, col_total.idx, col_total.width * 1.1)
