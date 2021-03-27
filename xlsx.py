from enum import IntEnum
from typing import List, Mapping

from xlsxwriter import Workbook


class Column(IntEnum):
    def __new__(cls, col_idx, col_name):
        obj = int.__new__(cls, col_idx)
        obj._value_ = col_name
        return obj

    COMPANY = 0, 'Company'
    INSIDERS = 1, 'Insiders'
    PRICE = 2, 'Price'
    NB_SHARES = 3, 'Number of shares'
    DATE = 4, 'Transaction date'
    SECU_TYPE = 5, 'Security type'
    FILE_LOC = 6, 'SEC4 file location'


class ColumnProps:
    def __init__(self, col_format=None, col_width=None):
        self.format = col_format
        self.width = col_width


def build_xlsx_file(data: List[Mapping], file_name):
    with Workbook(file_name) as wb:
        ws = wb.add_worksheet('Sheet1')

        base_format = {'valign': 'vcenter'}
        columns_props = {
            Column.COMPANY: ColumnProps(wb.add_format({**base_format, 'align': 'left'})),
            Column.INSIDERS: ColumnProps(wb.add_format({**base_format, 'align': 'left', 'text_wrap': True})),
            Column.PRICE: ColumnProps(wb.add_format({**base_format, 'align': 'right', 'num_format': '#,##0.00'})),
            Column.NB_SHARES: ColumnProps(wb.add_format({**base_format, 'align': 'right', 'num_format': '#,##0'})),
            Column.DATE: ColumnProps(wb.add_format({**base_format, 'align': 'center'})),
            Column.SECU_TYPE: ColumnProps(wb.add_format({**base_format, 'align': 'left'})),
            Column.FILE_LOC: ColumnProps(wb.add_format({**base_format, 'align': 'left'})),
        }
        for col, prop in columns_props.items():
            prop.width = len(col.value)

        # Write header
        ws.write_row(0, 0, [col.value for col in Column], wb.add_format({'bold': True, 'align': 'center'}))

        def write(row_idx, col_idx, cell_data):
            w = max([len(line) for line in str(cell_data).split('\n\r')])
            if w > columns_props[col_idx].width:
                columns_props[col_idx].width = w
            ws.write(row_idx, col_idx, cell_data, columns_props[col_idx].format)

        row = 0
        for sec4 in data:
            insiders = "\n\r".join(filter(None, sec4['insiders']))
            for transaction in sec4['transactions']:
                row += 1
                write(row, Column.COMPANY, sec4['company'])
                write(row, Column.INSIDERS, insiders)
                write(row, Column.FILE_LOC, sec4['sec4_file'])
                write(row, Column.PRICE, transaction['price'])
                write(row, Column.NB_SHARES, transaction['nb_shares'])
                write(row, Column.DATE, transaction['date'])
                write(row, Column.SECU_TYPE, transaction['security_title'])

        # Adjust column widths
        for col, prop in columns_props.items():
            ws.set_column(col, col, prop.width * 1.1)
