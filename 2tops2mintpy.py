# %%
import os
from pathlib import Path
from tqdm import tqdm

ifg_home = Path('/data/sentinel1/result/interferogams')
stack_home = Path('/data/sentinel1/result/stacks')


# %%
############  make dirs #############
def ensure_folder(folder):
    if not folder.is_dir():
        folder.mkdir(parents=True)


baseline_dir = stack_home / 'baselines'
reference_dir = stack_home / 'reference'
secondarys_dir = stack_home / 'secondarys'
mintpy_dir = stack_home / 'mintpy'

merged_dir = stack_home / 'merged'
geom_reference_dir = merged_dir / 'geom_reference'
interferograms_dir = merged_dir / 'interferograms'

stack_fld_list = [baseline_dir, reference_dir,
                  secondarys_dir, mintpy_dir,
                  merged_dir, geom_reference_dir,
                  interferograms_dir]

for fld in stack_fld_list:
    ensure_folder(fld)


# %%       link files
def looks(vrt_file, rdr_file, nlook_a, nlook_r):
    os.system(f'looks.py -i {vrt_file} -o {rdr_file} -a {nlook_a} -r {nlook_r}')

ifgs_files = sorted(ifg_home.iterdir())
for file in tqdm(ifgs_files, desc='link files'):
    name = file.name
    ref_name, sec_name = name.split('_')
    merged = file / 'merged'
    i = 0
    if merged.exists():
        os.chdir(file)
        if i == 0:
            ####################################################################
            # For the folder 'reference' and 'merged/geom_reference', you only 
            # need to get it from the first interferogram            
            #####################################################################
            i += 1
            
            ######### link to 'reference' folder ######
            ref_dir = file / ref_name
            ref_cmd = f'ln -sf {ref_dir}/* {reference_dir}/'
            os.system(ref_cmd)

            ####################################################################
            #     multi-looking geo_info files into 'geom_reference' folder
            #####################################################################
            # For the files that contain the geo info of ifgs, only 'los' was 
            # processed well (multi-looked and with '.rdr' format). We need 
            # to convert the full resolution geo info files into multi-looked 
            # files with ISCE format('.rdr'). In this script, azimuth/range looks
            # are: 4*20.
			#####################################################################
            looks(merged.joinpath('z.rdr.full.xml'),
                    geom_reference_dir.joinpath('hgt.rdr'),
                    4,20)
            looks(merged.joinpath('lat.rdr.full.xml'),
                    geom_reference_dir.joinpath('lat.rdr'),
                    4,20)
            looks(merged.joinpath('lon.rdr.full.xml'),
                    geom_reference_dir.joinpath('lon.rdr'),
                    4,20)
            looks(merged.joinpath('los.rdr.full.xml'),
                    geom_reference_dir.joinpath('los.rdr'),
                    4,20)


        # ########## link ifgs  ################
        ifg_out = interferograms_dir / name
        ensure_folder(ifg_out)

        # ifgs
        ln_cmd1 = f'ln -sf {merged}/filt_* {ifg_out}/'
        os.system(ln_cmd1)

        # cor
        ln_cmd2 = f'ln -sf {merged}/phsig.cor* {ifg_out}/'
        os.system(ln_cmd2)
        # ########## link secondarys  ################
        sec_dir = file / sec_name
        sec_cmd = f'ln -sf {sec_dir} {secondarys_dir}/'
        os.system(sec_cmd)

#%%
########## generate_baseline  #############
def get_dates_from_ifgs(ifgs):
    dates_all = []
    for ifg in ifgs:
        dates_all.extend(ifg.split('_'))
    dates = sorted(set(dates_all))
    return dates


ifgs = [i.name for i in ifgs_files]
dates = get_dates_from_ifgs(ifgs)

ref_name = dates[0]
ref_dir = ifgs_files[0] / ref_name
for sec_name in tqdm(dates[1:], desc='generate baselines'):
    sec_dir = secondarys_dir / sec_name

    bl_name = f'{ref_name}_{sec_name}'
    bl_dir = baseline_dir / bl_name
    ensure_folder(bl_dir)

    bl_file = bl_dir / f'{bl_name}.txt'
    bl_cmd = f'/data/isce2/contrib/stack/topsStack/computeBaseline.py -m {ref_dir}/ -s {sec_dir}/ -b {bl_file}'
    os.system(bl_cmd)


# %%        prep_isce.py

os.chdir(reference_dir)
prep_cmd = ('/root/miniconda3/bin/prep_isce.py'
            f' -f "{interferograms_dir}/*/filt_*.unw"'
            f' -m {reference_dir}/IW2.xml'
            f' -b {baseline_dir}/'
            f' -g {geom_reference_dir}/')
print(prep_cmd)
os.system(prep_cmd)

# %%       write options file

opt_file = mintpy_dir / 'mintpy_data_options.txt'

opt_info = f'''mintpy.load.processor        = isce
##---------for ISCE only:
mintpy.load.metaFile         = {reference_dir}/IW*.xml
mintpy.load.baselineDir      = {baseline_dir}
##---------interferogram datasets:
mintpy.load.unwFile          = {interferograms_dir}/*/filt_*.unw
mintpy.load.corFile          = {interferograms_dir}/*/phsig.cor
mintpy.load.connCompFile     = {interferograms_dir}/*/filt_*.unw.conncomp
##---------geometry datasets:
mintpy.load.demFile          = {geom_reference_dir}/hgt.rdr
mintpy.load.lookupYFile      = {geom_reference_dir}/lat.rdr
mintpy.load.lookupXFile      = {geom_reference_dir}/lon.rdr
mintpy.load.incAngleFile     = {geom_reference_dir}/los.rdr
mintpy.load.azAngleFile      = {geom_reference_dir}/los.rdr
# mintpy.load.shadowMaskFile   = {geom_reference_dir}/shadowMask.rdr
'''

with open(opt_file, 'w') as f:
    f.write(opt_info)
