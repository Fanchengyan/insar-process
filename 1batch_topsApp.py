# %%
import csv
import logging
import logging.config
import os
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
from isceobj.XmlUtil import FastXML as xml

logging.config.fileConfig(os.path.join(os.getcwd(), 'logging.conf'))
logger = logging.getLogger('batch_tops')

#########################################################
#  Modify following variables according to your condition
# ========================================================
# Folder contains insar data
sar_dir = '/data/sentinel1/data'
# Folder contains DEM data
dem = '/data/sentinel1/DEM/demLat_N38_N40_Lon_E097_E101.dem'
# dem = None
# Folder contains Precise orbits
orbit = '/data/sentinel1/aux/aux_poeorb'
# Folder contains Auxiliary data
aux = '/data/sentinel1/aux/aux_cal'

range_looks = 20
azimuth_looks = 4
filter_strength = 0.01
swath_number = None
unwrapper_name = 'snaphu'

roi = [38.4573, 39.0911, 98.6675, 99.3582]
# [S, N, W, E] convention (lat/lon)

def generate_topsApp_xml(
        reference_dir, secondary_dir, reference_file, secondary_file, roi, xml_file):
    '''导出干涉对xml配置文件'''

    # reference and secondary information
    fix_info = {"orbit directory": orbit,
                "auxiliary data directory": aux}
    if swath_number is not None:
        fix_info.update({"swath number": fix_info})

    reference = {"safe": reference_file,
                 "output directory": reference_dir}
    reference.update(fix_info)

    secondary = {"safe": secondary_file,
                 "output directory": secondary_dir}
    secondary.update(fix_info)

    tops = xml.Component('topsinsar')
    # parameters
    tops["Sensor name"] = 'SENTINEL1'

    tops['reference'] = reference
    tops['secondary'] = secondary

    if roi:
        tops["region of interest"] = roi
    if dem:
        tops["demFilename"] = Path(dem).name
    tops["use GPU"] = True
    tops["range looks"] = range_looks
    tops["azimuth looks"] = azimuth_looks
    tops["do unwrap"] = True
    tops["unwrapper name"] = unwrapper_name
    tops["filter strength"] = filter_strength

    tops.writeXML(xml_file, root='topsApp')


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


def load_interferogram_pairs(path_list, delimiter=','):
    '''加载干涉对文件'''
    with open(path_list) as f:
        ms_list = list(csv.reader(f, delimiter=delimiter))
    return ms_list


def day_interval(date_start, date_end):
    date_start = datetime.strptime(date_start, '%Y%m%d')
    date_end = datetime.strptime(date_end, '%Y%m%d')
    interval = (date_end - date_start).days

    return interval


def generate_interferogram_pairs(sar_dir,  pair_file, sar_suffix='zip',
                                 max_interval=2, max_day=180, delimiter=','):
    '''导出干涉对文件。
    Generate and save a reference-secondary pair automatically. Time interval 
    of reference-secondary pair is 1 and 2

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


# %%         generate_interferogram_pairs

home_dir = Path('/data/sentinel1/result')
pair_file = home_dir / 'ifg_pairs.csv'

generate_interferogram_pairs(sar_dir, pair_file, sar_suffix='zip',
                             max_interval=3, max_day=180, delimiter=',')

# %%   batch run topsApp.py
ifg_pairs = load_interferogram_pairs(pair_file)
mapper = mapper_date_data(sar_dir, suffix='zip')

for i, ifg in enumerate(tqdm(ifg_pairs)):
    reference, secondary = ifg
    reference_file = os.path.join(sar_dir, mapper[reference])
    secondary_file = os.path.join(sar_dir, mapper[secondary])

    ifg_name = f'{reference}_{secondary}'
    ifg_dir = home_dir / f'interferogams/{ifg_name}'
    if not ifg_dir.is_dir():
        ifg_dir.mkdir(parents=True)

    # create xml file
    reference_dir = ifg_dir / f'{reference}'
    secondary_dir = ifg_dir / f'{secondary}'
    xml_file = ifg_dir / 'topsApp.xml'

    generate_topsApp_xml(reference_dir, secondary_dir,
                         reference_file, secondary_file, roi, xml_file)

    # cd ifg folder
    os.chdir(ifg_dir)

    # link dem file to current folder
    print(ifg_name)
    cmd_link = f'ln -sf {str(Path(dem).parent)}/* ./'
    os.system(cmd_link)

    # execute topsApp.py
    cmd_tops = f'topsApp.py {xml_file} --start=startup'
    logger.info(cmd_tops)
    os.system(cmd_tops)
