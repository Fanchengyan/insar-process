#!/usr/bin/env python3

import os
import csv
from datetime import datetime


def mapper_date_data(folder, suffix):
    '''映射日期到数据文件
    Select the data files from the folder,and then return 
    a mapper from year to data file
    '''
    files_s1 = [i for i in os.listdir(folder) if i.split('.')[-1] == suffix]
    dates = [i[17:25] for i in files_s1]
    mapper = dict()
    for i, date in enumerate(dates):
        mapper.update({date: files_s1[i]})
    return mapper


def day_interval(date_start, date_end):
    date_start = datetime.strptime(date_start, '%Y%m%d')
    date_end = datetime.strptime(date_end, '%Y%m%d')
    interval = date_end - date_start

    return interval.days


def export_master_slaves_file(dates, distance_time_interval=2, max_day_interval=180, path_out=None, delimiter='\t'):
    '''导出干涉对文件。
    Generate and save a master-slave pair automatically. Time interval 
    of master-slave pair is 1 and 2

    dates: str 
        date string with format of '%Y%m%d'
    distance_time_interval: int
        干涉对时间间隔距离，相邻时间间隔距离为1
    max_day_interval：int
        干涉对最大的间隔天数
    path_out: str
        the path of file out.if None, will not save. 
    delimiter: str
        master与slave日期之间的分割符号
    '''
    dates.sort()

    num = len(dates)
    master_slave_pair_list = []
    for i, date in enumerate(dates):
        dti_temp = 1
        while dti_temp <= distance_time_interval:
            if i + dti_temp < num:
                if day_interval(date, dates[i + dti_temp]) < max_day_interval:
                    master_slave_pair_list.append([date, dates[i + dti_temp]])
                    dti_temp += 1
                else:
                    break
            else:
                break

    with open(path_out, 'w', newline='') as f:
        csv_writer = csv.writer(f, delimiter=delimiter)
        csv_writer.writerows(master_slave_pair_list)


if __name__ == "__main__":
    # 存放insar的文件夹
    path_data = r'F:\DaTong River'
    # 存放干涉对时间序列的文件路径
    path_out = './mater_slave.list'

    mapper = mapper_date_data(path_data, suffix='zip')
    dates = list(mapper.keys())

    export_master_slaves_file(dates, distance_time_interval=5,
                              max_day_interval=180, path_out=path_out, delimiter='\t')
