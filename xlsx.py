from enum import IntEnum
from typing import Mapping

from xlsxwriter import Workbook


class Column(IntEnum):
    def __new__(cls, col_idx, col_name):
        obj = int.__new__(cls, col_idx)
        obj._value_ = col_name
        return obj

    COMPANY = 0, 'Company'
    INSIDERS = 1, 'Insiders'
    TOTAL_AMOUNT = 2, 'Total amount'
    PRICE = 3, 'Price'
    NB_SHARES = 4, 'Number of shares'
    DATE = 5, 'Transaction date'
    SECU_TYPE = 6, 'Security type'
    FILE_LOC = 7, 'SEC4 file location'


class ColumnProps:
    def __init__(self, col_format=None, col_width=None):
        self.format = col_format
        self.width = col_width


def build_xlsx_file(data, file_name):
    with Workbook(file_name) as wb:
        ws = wb.add_worksheet('Sheet1')

        base_format = {'valign': 'vcenter'}
        columns_props = {
            Column.COMPANY: ColumnProps(wb.add_format({**base_format, 'align': 'left'})),
            Column.INSIDERS: ColumnProps(wb.add_format({**base_format, 'align': 'left', 'text_wrap': True})),
            Column.TOTAL_AMOUNT: ColumnProps(wb.add_format({**base_format, 'align': 'right', 'num_format': '0.00'})),
            Column.PRICE: ColumnProps(wb.add_format({**base_format, 'align': 'right'})),
            Column.NB_SHARES: ColumnProps(wb.add_format({**base_format, 'align': 'right', 'num_format': '0'})),
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

        def merge_col(start_row, stop_row, col_idx, cell_data):
            w = max([len(line) for line in str(cell_data).split('\n\r')])
            if w > columns_props[col_idx].width:
                columns_props[col_idx].width = w
            ws.merge_range(start_row, col_idx, stop_row, col_idx, cell_data, columns_props[col_idx].format)

        row = 0
        total_amount = 0
        for company, data in data.items():
            for transaction in data['transactions']:
                row += 1
                write(row, Column.PRICE, transaction['price'])
                write(row, Column.NB_SHARES, transaction['nb_shares'])
                write(row, Column.DATE, transaction['date'])
                write(row, Column.SECU_TYPE, transaction['security_title'])
                write(row, Column.FILE_LOC, transaction['sec4_file'])
                total_amount += float(transaction['price']) * float(transaction['nb_shares'])

            insiders = "\n\r".join(filter(None, data['insiders']))
            if len(data['transactions']) > 1:
                merge_first_row = row - len(data['transactions']) + 1
                merge_col(merge_first_row, row, Column.COMPANY, company)
                merge_col(merge_first_row, row, Column.INSIDERS, insiders)
                merge_col(merge_first_row, row, Column.TOTAL_AMOUNT, total_amount)
            else:
                write(row, Column.COMPANY, company)
                write(row, Column.INSIDERS, insiders)
                write(row, Column.TOTAL_AMOUNT, total_amount)

        for col, prop in columns_props.items():
            ws.set_column(col, col, prop.width * 1.1)


if __name__ == '__main__':
    sample = {
        'Quarta-Rad, Inc. (QURT)': {
            'insiders': ['Shvetsky Victor (Chief Ex. Officer)'],
            'transactions': [
                {'nb_shares': 333333.0, 'price': 1.5, 'date': '2020-12-16', 'security_title': 'Common stock',
                 'sec4_file': 'https://www.sec.gov/Archives/edgar/data/1549630/0001493152-21-006689.txt'}
            ]
        },
        'Solid Biosciences Inc. (SLDB)': {
            'insiders': [
                'RA CAPITAL MANAGEMENT, L.P. (Director, 10% owner)',
                'RA Capital Healthcare Fund LP (Director, 10% owner)',
                'Kolchinsky Peter (Director, 10% owner)',
                'Shah Rajeev M. (Director, 10% owner)'
            ],
            'transactions': [
                {'nb_shares': 2206685.0, 'price': 5.75, 'date': '2021-03-19', 'security_title': 'Common Stock',
                 'sec4_file': 'https://www.sec.gov/Archives/edgar/data/1619841/0001104659-21-040327.txt'}
            ]
        },
        'PHX MINERALS INC. (PHX)': {
            'insiders': ['DELANEY PETER B (Director)'],
            'transactions': [
                {'nb_shares': 21739.0, 'price': 0.0167, 'date': '2021-03-23', 'security_title': 'PHX Class A Common',
                 'sec4_file': 'https://www.sec.gov/Archives/edgar/data/1226548/0001209191-21-022812.txt'}
            ]
        },
        'PHX MINERALS. (PHX)': {
            'insiders': ['DELANEY PETER B (Director)'],
            'transactions': [
                {'nb_shares': 21739.0, 'price': 0.0167, 'date': '2021-03-23', 'security_title': 'PHX Class A Common',
                 'sec4_file': 'https://www.sec.gov/Archives/edgar/data/1226548/0001209191-21-022812.txt'}
            ]
        }
    }
    build_xlsx_file(sample, 'report.xlsx')
