#!/usr/bin/env python3

import os
import csv
from datetime import datetime


def mapper_date_data(folder, suffix):
    '''映射日期到数据文件
    Select the data files from the folder,and then return 
    a mapper from year to data file
    '''
    files_s1 = sorted([i for i in os.listdir(folder)
                      if i.split('.')[-1] == suffix])
    dates = [i[17:25] for i in files_s1]
    mapper = dict()
    for i, date in enumerate(dates):
        mapper.update({date: files_s1[i]})
    return mapper


def day_interval(date_start, date_end):
    date_start = datetime.strptime(date_start, '%Y%m%d')
    date_end = datetime.strptime(date_end, '%Y%m%d')
    interval = (date_end - date_start).days

    return interval


def generate_interferogram_pairs(sar_dir,  pair_file, sar_suffix='zip',
                                 max_interval=2, max_day=180, delimiter=','):
    '''generate interferogram pairs to a file
    Generate and save a reference-secondary pair automatically. Time interval 
    of reference-secondary pair is 1 and 2

    Parameters:
    -----------
    dates: str 
        date string with format of '%Y%m%d'
    max_interval: int
        干涉对最大相邻获取间隔, 相邻间隔为1
    max_day:int
        干涉对最大的间隔天数
    pair_file: str
        the path of file out.if None, will not save. 
    delimiter: str
        reference与secondary日期之间的分割符号
    '''
    mapper = mapper_date_data(sar_dir, suffix=sar_suffix)
    dates = sorted(mapper.keys())

    num = len(dates)
    reference_secondary_pair_list = []
    for i, date in enumerate(dates):
        dti_temp = 1
        while dti_temp <= max_interval:
            if i + dti_temp < num:
                if day_interval(date, dates[i + dti_temp]) < max_day:
                    reference_secondary_pair_list.append(
                        [date, dates[i + dti_temp]])
                    dti_temp += 1
                else:
                    break
            else:
                break

    with open(pair_file, 'w', newline='') as f:
        csv_writer = csv.writer(f, delimiter=delimiter)
        csv_writer.writerows(reference_secondary_pair_list)


if __name__ == "__main__":
    # the folder contains the SAR data
    sar_dir = r'F:\DaTong River'

    # the file to save the pairs
    pair_file = './ifg_pairs.csv'

    generate_interferogram_pairs(sar_dir, pair_file, sar_suffix='zip',
                                 max_interval=3, max_day=180, delimiter=',')
