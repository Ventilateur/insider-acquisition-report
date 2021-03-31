import time
import timeit
from datetime import datetime

from scrape.sec4 import get_sec4_data, list_sec4_data
from scrape.edgar import list_sec4_files
from xlsx import build_xlsx_file

if __name__ == '__main__':
    def test1():
        # files = gather_weekly_sec4_files()
        # return list_sec4_data(files)
        # print(gather_weekly_sec4_files())
        # print(get_sec4_data("https://www.sec.gov/Archives/edgar/data/917251/0001638599-21-000294.txt").to_list())
        files = list_sec4_files()
        data = list_sec4_data(files)
        build_xlsx_file(data, "whole_week_report.xlsx")

    def test2():
        files = list_sec4_files()
        print(files)

    def test3():
        print(get_sec4_data("https://www.sec.gov/Archives/edgar/data/1851446/0000899243-21-013344.txt"))

    def test4():
        files = list_sec4_files(date_range=2)
        data = list_sec4_data(files[0:20])
        print(data)


    exec_time = timeit.timeit(test4, number=1)
    print(exec_time)

    # print(get_sec4_data("https://www.sec.gov/Archives/edgar/data/1851446/0000899243-21-013344.txt"))