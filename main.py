import timeit

from gather import build_csv_file
from sec4 import get_sec4_data, list_sec4_data
from edgar import gather_weekly_sec4_files

if __name__ == '__main__':
    def test1():
        # files = gather_weekly_sec4_files()
        # return list_sec4_data(files)
        # print(gather_weekly_sec4_files())
        # print(get_sec4_data("https://www.sec.gov/Archives/edgar/data/917251/0001638599-21-000294.txt").to_list())
        files = gather_weekly_sec4_files()
        data = list_sec4_data(files)
        build_csv_file(data)

    def test2():
        files = gather_weekly_sec4_files()
        print(files)

    exec_time = timeit.timeit(test2, number=1)
    print(exec_time)