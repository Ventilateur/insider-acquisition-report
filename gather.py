from typing import Any, List, Mapping
from csv import writer, QUOTE_MINIMAL


def build_csv_file(data: List[List]):
    with open("weekly_report.csv", newline="", mode="w") as report_file:
        report_writer = writer(report_file, delimiter="|", quotechar='"', quoting=QUOTE_MINIMAL)
        report_writer.writerow([
            "Company",
            "Company code",
            "Insider name",
            "Insider title",
            "Is director",
            "Is officer",
            "Is 10% owner",
            "Total amount",
            "Number of shares",
            "Price per share",
            "Date",
            "Security title",
            "Form file"
        ])
        report_writer.writerows(data)


def flatten(data: List[List[List]]) -> List[List]:
    return [item for sub_list in data for item in sub_list]


def lambda_handler(event: List[List[List]], context):
    build_csv_file(flatten(event))


if __name__ == '__main__':
    data = [
        [
            ['PG&E Corp', 'PCG', 'Foster Christopher A', 'EVP & Chief Financial Officer', 'No', 'Yes', 'No', '0.0$',
             25113.0, '0.0$', '2021-03-22', 'Common Stock']
        ],
        [
            ['SIGNET JEWELERS LTD', 'SIG', 'FINN MARY ELIZABETH', 'Chief People Officer', 'No', 'Yes', 'No', '0.0$',
             4846.0, '0.0$', '2021-03-22', 'Common Shares, par value $0.18']
        ],
        [
            ['Mistras Group, Inc.', 'MG', 'Lohmeier Michelle', 'N/A', 'Yes', 'No', 'No', '0.0$', 4110.0, '0.0$',
             '2021-03-23', 'Common Stock']
        ]
    ]
    lambda_handler(data, None)
