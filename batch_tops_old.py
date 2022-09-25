import csv
import logging
import logging.config
import os
from datetime import datetime

from isceobj.XmlUtil import FastXML as xml

logging.config.fileConfig(os.path.join(os.getcwd(), 'logging.conf'))
logger = logging.getLogger('batch_tops')

#########################################################
#  Modify following variables according to your condition
# ========================================================
# Folder contains insar data
path_data = '/media/Seagate/Raw'
# Folder contains DEM data
dem = '/home/fanchengyan/insar_aux_data/DEM'
# Folder contains Precise orbits
orbit = '/home/fanchengyan/insar_aux_data/AUX_POEORB'
# Folder contains Auxiliary data
aux = '/home/fanchengyan/insar_aux_data/AUX_CAL'


range_looks = 20
azimuth_looks = 4
filter_strength = 0.3

# ========================================================

path_home = os.getcwd()
os.environ['DEMDB'] = dem


def export_master_slave_pair_xml(outputdir_master, outputdir_slave, masterdir, slavedir,
                                 roi, path_out):
    '''导出干涉对xml配置文件'''

    tops = xml.Component('topsinsar')

    # parameters
    tops["Sensor name"] = 'SENTINEL1'
    tops["range looks"] = range_looks
    tops["azimuth looks"] = azimuth_looks
    tops["do unwrap"] = True
    tops["unwrapper name"] = 'snaphu_mcf'
    tops["filter strength"] = filter_strength
    if roi:
        tops["region of interest"] = roi

    # master and slave information
    fix_info = {"orbit directory": orbit,
                "swath number": 2,
                "auxiliary data directory": aux}

    master = {"safe": masterdir,
              "output directory": outputdir_master}
    master.update(fix_info)

    slave = {"safe": slavedir,
             "output directory": outputdir_slave}
    slave.update(fix_info)

    tops['master'] = master
    tops['slave'] = slave

    tops.writeXML(path_out, root='topsApp')


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


def load_pair_master_slaves(path_list):
    '''加载干涉对文件'''
    with open(path_list) as f:
        ms_list = list(csv.reader(f))
    return ms_list


def SAFE_name(zipname):
    '''将文件字符串转化为后缀为SAFE的字符串'''
    SAFE_name = os.path.splitext(zipname)[0] + '.SAFE'
    return SAFE_name


def day_interval(date_start, date_end):
    date_start = datetime.strptime(date_start, '%Y%m%d')
    date_end = datetime.strptime(date_end, '%Y%m%d')
    interval = date_end - date_start

    return interval.days


def export_master_slaves_file(dates, distance_time_interval=2, max_day_interval=180, path_out=None):
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
        csv_writer = csv.writer(f)
        csv_writer.writerows(master_slave_pair_list)


def copy_result_file(giant_path, xml_file):
    if not os.path.exists(giant_path):
        os.makedirs(giant_path)
    file_names = ['filt_topophase.flat',
                  'filt_topophase.flat.xml',
                  'filt_topophase.flat.geo',
                  'filt_topophase.flat.geo.xml',
                  'filt_topophase.unw',
                  'filt_topophase.unw.xml',
                  'filt_topophase.unw.geo',
                  'filt_topophase.unw.geo.xml',
                  'topophase.cor',
                  'topophase.cor.xml',
                  'topophase.cor.geo',
                  'topophase.cor.geo.xml',
                  'phsig.cor',
                  'phsig.cor.xml',
                  'phsig.cor.geo',
                  'phsig.cor.geo.xml',
                  'los.rdr.geo',
                  'dem.crop']

    for file_name in file_names:
        cmd1 = 'cp ./merged/{file_name} {giant_path}/'.format(
            file_name=file_name, giant_path=giant_path)
        logger.info(cmd1)
        os.system(cmd1)

    cmd2 = 'cp {file_name} {giant_path}/'.format(
        giant_path=giant_path, file_name=xml_file)
    logger.info(cmd2)
    os.system(cmd2)


def main(export_master_slaves=True, export_master_slaves_only=False, copy_insar=True,
         copy_result_path=None, insar_file_type='SAFE', logfile=True):
    '''
    export_master_slaves: bool
        是否要计算导出master_slaves干涉对文件
    export_master_slaves_only: bool
        是否只计算导出master_slaves干涉对文件.当第一次运行本文件，需要对master_slaves干涉对文件修改时使用
    copy_insar：bool
        是否要复制InSAR原始文件到计算路径【计算后删除复制来的InSAR文件】
    copy_result：bool
        是否要复制干涉对生成文件到【计算后删除复制来的InSAR文件】
    insar_file_type：['SAFE','zip']
        InSAR文件是SAFE还是zip
    logfile：bool
        是否导出批处理的log文件
    aux: string
        auxiliary data directory
    roi:
        region of interest. like [37.1, 3839, 98.84, 101.336]
    '''
    # logs

    # 映射日期到文件
    mapper = mapper_date_data(path_data, suffix=insar_file_type)
    dates = list(mapper.keys())

    # 导出导入干涉对文件
    if export_master_slaves_only:
        print("dates:{}\n mapper:{}".format(dates, mapper))
        export_master_slaves_file(dates, path_out='./master_slave.list')
    else:
        if export_master_slaves:
            export_master_slaves_file(dates, path_out='./master_slave.list')

        list_master_slave = load_pair_master_slaves('./master_slave.list')

        # 打印总共要处理的干涉对数
        num_total_pair = len(list_master_slave)
        logger.info('There are {} pairs master-slave'.format(num_total_pair))

        # 循环处理干涉对
        for i, pair in enumerate(list_master_slave):
            # 原始 master slave 文件存放路径
            master, slave = pair
            masterdir = os.path.join(path_data, mapper[master])
            slavedir = os.path.join(path_data, mapper[slave])

            # 创建文件处理目录
            ms_pair = '{}-{}'.format(master, slave)
            data_dir = 'isce_process_data/{}'.format(ms_pair)

            if not os.path.exists(data_dir):
                os.makedirs(data_dir)

            path_pair_folder = os.path.join(os.getcwd(), data_dir)

            outputdir_master = os.path.join(path_pair_folder, 'dataout/master')
            outputdir_slave = os.path.join(path_pair_folder, 'dataout/slave')
            if not os.path.exists(outputdir_master):
                os.makedirs(outputdir_master)
            if not os.path.exists(outputdir_slave):
                os.makedirs(outputdir_slave)

            if copy_insar:
                # master slave要移到的文件路径
                masterdir_new = os.path.join(path_pair_folder, mapper[master])
                slavedir_new = os.path.join(path_pair_folder, mapper[slave])

                # copy insar raw file to current location
                cmd_cp1 = 'rsync -avh {} {}'.format(masterdir, masterdir_new)
                cmd_cp2 = 'rsync -avh {} {}'.format(slavedir, slavedir_new)
                logger.info(cmd_cp1)
                os.system(cmd_cp1)
                logger.info(cmd_cp2)
                os.system(cmd_cp2)
                logger.info('>>> copy done!')
                masterdir = masterdir_new
                slavedir = slavedir_new

            if insar_file_type == 'zip':
                folder_SAFE = os.path.split(masterdir)[0]
                # unzip insar raw file to current location
                logger.info('>>> Unzipping insar data')
                os.system('unzip -d {} {} '.format(folder_SAFE, masterdir))
                os.system('unzip -d {} {} '.format(folder_SAFE, slavedir))
                logger.info('>>> Unzip done!')

            # 创建xml配置文件
            xml_file = './{}.xml'.format(ms_pair)

            masterdir_SAFE = SAFE_name(masterdir)
            slavedir_SAFE = SAFE_name(slavedir)

            os.chdir(path_pair_folder)
            export_master_slave_pair_xml(outputdir_master, outputdir_slave,
                                         masterdir_SAFE, slavedir_SAFE, roi, xml_file)

            # execute topsApp.py
            logger.info('=============' * 5)
            logger.info('>>>  {}/{}: {}'.format(i, num_total_pair, ms_pair))
            cmd_tops = 'topsApp.py {}'.format(xml_file)
            logger.info(cmd_tops)

            os.system(cmd_tops)

            if copy_insar:
                # remove insar raw file
                logger.info('>>> Processed done! Removing insar data')
                os.system('rm -rf {}'.format(masterdir_SAFE))
                os.system('rm -rf {}'.format(slavedir_SAFE))
                os.system('rm -rf {}'.format(masterdir))
                os.system('rm -rf {}'.format(slavedir))
                logger.info('>>> Removing done!')

            # 复制结果到指定的Giant目录
            if copy_result_path:
                giant_path = os.path.join(copy_result_path, ms_pair)
                copy_result_file(giant_path, xml_file)

            # back to home path
            os.chdir(path_home)


if __name__ == "__main__":
    # region of interest. bounding box in [S, N, W, E] convention (lat/lon)
    roi = [37.126, 38.3766, 98.8496, 101.3043]
    # roi = None

    copy_result_path = '/media/Seagate/GIAnT_data_dir'
    # copy_result_path = None

    main(export_master_slaves=True, export_master_slaves_only=False,
         copy_insar=True, copy_result_path=copy_result_path,
         insar_file_type='zip')


# todo：
# 1. 多进程，可以在处理干涉对的时候，复制与减压文件
# 3. 考虑同一轨道相邻文件作为输入文件
# 5. 处理后文件是否复制到指定目录（复制所有还是复制GIANT需要的可选）
