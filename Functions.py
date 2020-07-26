import math
import numpy as np
import pandas as pd
from astropy.table import QTable, Table, vstack
#from astroquery.jplsbdb import SBDB
from astroquery.jplhorizons import Horizons
from astropy.time import Time
#from astroquery.mpc import MPC
#from pprint import pprint
from tqdm import tqdm_notebook, tqdm
from decimal import *

pd.options.display.float_format = '{:,.4f}'.format


def decimal_to_hours(dec_time: float) -> (int, float, float):
    """transform decimal time into conventional time"""
    hours = int(dec_time)
    minutes = (dec_time * 60) % 60
    seconds = (dec_time * 3600) % 60
    return hours, minutes, seconds


def decimal_to_jd(dec_time: float) -> float:
    """transforms decimal time into fraction of jd"""
    frac_jd = float(dec_time) * 60 * 60 / 86400
    return frac_jd


def jpl_query_ephemerides(body, epochs, **kwargs):
    # =============================================
    if 'location' in kwargs:
        location = kwargs['location']
    else:
        location = '121'  # Kharkiv observatory, 121 - outtown observatory
    if 'columns' in kwargs:
        columns = kwargs['columns']
    else:
        # available query parameters
        names = ('targetname', 'datetime_str', 'datetime_jd', 'H', 'G', 'solar_presence', 'flags', 'RA', 'DEC',
                 'RA_app', 'DEC_app', 'RA_rate', 'DEC_rate', 'AZ', 'EL', 'AZ_rate', 'EL_rate', 'sat_X', 'sat_Y',
                 'sat_PANG', 'siderealtime', 'airmass', 'magextinct', 'V', 'surfbright', 'illumination', 'illum_defect',
                 'sat_sep', 'sat_vis', 'ang_width', 'PDObsLon', 'PDObsLat', 'PDSunLon', 'PDSunLat', 'SubSol_ang',
                 'SubSol_dist',
                 'NPole_ang', 'NPole_dist', 'EclLon', 'EclLat', 'r', 'r_rate', 'delta', 'delta_rate', 'lighttime',
                 'vel_sun', 'vel_obs',
                 'elong', 'elongFlag', 'alpha', 'lunar_elong', 'lunar_illum', 'sat_alpha', 'sunTargetPA', 'velocityPA',
                 'OrbPlaneAng',
                 'constellation', 'TDB-UT', 'ObsEclLon', 'ObsEclLat', 'NPole_RA', 'NPole_DEC', 'GlxLon', 'GlxLat',
                 'solartime',
                 'earth_lighttime', 'RA_3sigma', 'DEC_3sigma', 'SMAA_3sigma', 'SMIA_3sigma', 'Theta_3sigma',
                 'Area_3sigma',
                 'RSS_3sigma', 'r_3sigma', 'r_rate_3sigma', 'SBand_3sigma', 'XBand_3sigma', 'DoppDelay_3sigma',
                 'true_anom',
                 'hour_angle', 'alpha_true', 'PABLon', 'PABLat')
    quantities = '1,4,8,9,19,20,21,23,25,43'
    # ===============================================
    start = 0
    end = len(epochs)
    step = 200
    full_ephemerides = []
    for i in tqdm(range(start, end, step)):
        obj = Horizons(id="{}".format(body), location=location, epochs=epochs[i:i + step])
        chunk_ephemerides = obj.ephemerides(quantities=quantities)
        full_ephemerides = vstack([full_ephemerides, chunk_ephemerides])
        full_ephemerides_pd = full_ephemerides.to_pandas()
    full_ephemerides_pd = full_ephemerides_pd.drop(columns=['col0', 'H', 'G', 'solar_presence'])
    full_ephemerides_pd.to_csv('../../Desktop/{}_ephemerides_short.csv'.format(body),
                               mode='w', index=False, header=True, encoding='utf8', float_format='%.6f')
    full_ephemerides_pd.round(3)
    return full_ephemerides_pd


def JPL_query_eph_to_db(body, epochs, **kwargs):
    # =============================================
    if 'location' in kwargs:
        location = kwargs['location']
    elif 'location' == 'NaN':
        location = '121'
    else:
        location = '101'  # Kharkiv observatory, 121 - outtown observatory
    if 'columns' in kwargs:
        columns = kwargs['columns']
    quantities = '1, 20, 43'
    '''1.Astrometric RA & DEC
    '''
    # ===============================================
    start = 0
    end = len(epochs)
    step = 200
    full_ephemerides = []
    for i in range(start, end, step):
        obj = Horizons(id="{}".format(body), location=location, epochs=epochs[i:i + step])
        chunk_ephemerides = obj.ephemerides(quantities=quantities)
        full_ephemerides = vstack([full_ephemerides, chunk_ephemerides])
        full_ephemerides_pd = full_ephemerides.to_pandas()
    pd.options.display.float_format = '{:,.5f}'.format
    full_ephemerides_pd = full_ephemerides_pd.drop(
        columns=['col0', 'H', 'G', 'solar_presence', 'targetname', 'datetime_str', 'datetime_jd', 'flags'])
    full_ephemerides_pd = full_ephemerides_pd.round(4)
    return full_ephemerides_pd


def get_orbital_elem(body, epochs, **kwargs):
    if 'location' in kwargs:
        location = kwargs['location']
    else:
        location = '500@10'
    obj = Horizons(id='{}'.format(body), location=location, epochs=jd_dates)
    orb_elem = obj.elements()
    orb_elem_df = orb_elem.to_pandas()
    return orb_elem_df


def queryATL_add_eph(path, file_name):
    # reading file for headers
    colspecs = [[0, 15], [16, 150]]
    full_db_headers = pd.read_fwf(path + file_name, colspecs=colspecs, header=None)

    # reading whole file
    with open("{}{}".format(path, file_name), "r") as file:
        full_db_arrays = file.readlines()

    # getting indexes for start/end of headers and data
    start_of_headers = full_db_headers.loc[full_db_headers[0].str.contains('OBJECT.....')].index
    end_of_headers = full_db_headers.loc[full_db_headers[0] == 'DATA:'].index + 1
    end_of_arrays = full_db_headers.loc[full_db_headers[0].str.contains('====')].index

    # creating arrays to store separated data
    data = [0] * len(start_of_headers)
    header = [0] * len(start_of_headers)
    data_pd = [0] * len(start_of_headers)

    # splitting datafile into separate arrays
    for i in range(len(start_of_headers)):
        data[i] = full_db_arrays[end_of_headers[i]:end_of_arrays[i]]
        data[i] = [data[i][j].split() for j in range(len(data[i]))]
        data_pd[i] = pd.DataFrame(data[i])
        header[i] = full_db_headers[start_of_headers[i]:end_of_headers[i]]

    # getting header
    headers_horizontal = [item.T for item in header]  # transpose array to read header
    headers_header = [headers_horizontal[i].iloc[0] for i in range(len(headers_horizontal))]
    # getting header
    headers_horizontal = [headers_horizontal[i][1:] for i in range(len(headers_horizontal))]

    # adding header to header arrays
    for i in range(len(headers_horizontal)):
        headers_horizontal[i].columns = headers_header[i]

    # creating keyword translator for easy access purposes
    try:
        keywords = headers_horizontal[1].columns
    except IndexError:
        keywords = headers_horizontal[0].columns
    keywords_strp = [list(keywords)[i].strip('.:') for i in range(len(keywords))]
    kw_tls = {keywords_strp[i]: keywords[i] for i in range(len(keywords))}
    # getting observing sites
    obs_sites = []
    for i in range(len(headers_horizontal)):
        obs_sites.append(headers_horizontal[i][kw_tls['OBSERVING SITE']][1])
    obs_sites = pd.DataFrame(obs_sites)

    # getting unique observing sites to create keyword translator
    obs_sites_unique = obs_sites[0].unique()
    # print(obs_sites_unique)
    obs_codes_unique = ['D53', '186', '119', 'V26', 'N42', {'lon': 66.90,
                                                            'lat': 38.67, 'elevation': 2.6}, '121', '583', '071', '061']
    obs_codes_kwd = {obs_sites_unique[i]: obs_codes_unique[i] for i in range(len(obs_sites_unique))}

    # getting object_numbers, start observe times and observatory codes
    object_nums = [headers_horizontal[i][kw_tls['OBJECT']].str.split(' ')[1][0] + ' ' +
                   headers_horizontal[i][kw_tls['OBJECT']].str.split(' ')[1][1] for i in range(len(header))]
    zero_times = [headers_horizontal[i][kw_tls['ZERO TIME']].str.split(' ')[1][0] for i in range(len(header))]
    obs_codes = [obs_codes_kwd[headers_horizontal[i][kw_tls['OBSERVING SITE']][1]] for i in range(len(header))]
    # print(obs_codes)

    # getting starting times
    arr_len = range(len(data_pd))
    start_jd = [zero_times[i] for i in arr_len]
    # get observation epochs
    epochs_times = [data_pd[i][0] for i in arr_len]
    # transtating dec-times to jd_times
    epochs_jd = [epochs_times[i].apply(decimal_to_jd) for i in arr_len]
    # adding starting time to observation epochs
    epochs_full_1 = [epochs_jd[i].add(float(start_jd[i])) for i in arr_len]
    epochs_full_l = [list(epochs_full_1[i]) for i in arr_len]
    # get data(ephemerides) from JPL:
    # object_nums[0] = '2019 OK'
    # print(object_nums)
    jpl_data = [JPL_query_eph_to_db(
        body='{}'.format(object_nums[i]),
        epochs=epochs_full_l[i],
        location=obs_codes[i],
        columns=['datetime_str', 'RA', 'DEC', 'alpha', 'delta', 'PABLon'])
        for i in tqdm(arr_len)]

    dropcols1 = ['elongFlag', 'airmass', 'magextinct', 'V',
                 'surfbright', 'r', 'r_rate', 'delta', 'delta_rate',
                 'lighttime', 'elong', 'lunar_elong', 'lunar_illum',
                 'PABLon', 'PABLat', 'AZ', 'EL']
    dropcols = ['elongFlag', 'delta_rate', 'PABLon', 'PABLat']
    # print(jpl_data[0].columns)
    for key in dropcols:
        if key not in jpl_data[0].columns:
            dropcols.remove(key)
    jpl_data_reduc = [jpl_data[i].drop(columns=dropcols) for i in range(len(jpl_data))]
    jpl_data_rows = [[(jpl_data_reduc[j].values[i])
                      for i in range(len(jpl_data_reduc[j]))]
                     for j in range(len(jpl_data_reduc))]
    # print(jpl_data_reduc[0].to_numpy())
    jpl_data_rows1 = [[str(jpl_data_reduc[j].values[i]).strip('[]')
                       for i in range(len(jpl_data_reduc[j]))]
                      for j in range(len(jpl_data_reduc))]

    # reading whole file(again) to add JPL data to the existing file
    file = open("{}{}".format(path, file_name), "r")
    full_db_arrays = file.readlines()
    file.close()
    full_db_arrays_copy = full_db_arrays
    getcontext().prec = 5

    # adding data to existing file
    for arr_num in range(len(end_of_arrays)):
        for k, j in enumerate(range(end_of_headers[arr_num], end_of_arrays[arr_num])):
            row = ''
            for i in range(len(jpl_data_rows[arr_num][k])):
                row += '{0:.4f}'.format(jpl_data_rows[arr_num][k][i]) + ' '
                # print(row)
            full_db_arrays_copy[j] = full_db_arrays_copy[j].strip('\n') + ' ' + row + '\n'
    # writing modified data to file
    with open(path + "{}_modified.ATL".format(file_name[:-4]), 'w') as output_file:
        for i in range(len(full_db_arrays_copy)):
            output_file.write(full_db_arrays_copy[i])

    return full_db_arrays_copy


def read_file(path, file_name):
    """reads file and returns plain text"""
    with open("{}{}".format(path, file_name), "r") as file:
        file_text = file.readlines()
        return file_text


def queryATL_add_eph(path, file_name):
    """docstring"""
    # reading file for the following parsing
    full_db_arrays = read_file(path=path, file_name=file_name)

    # making a copy of file for future changes
    file_origin = full_db_arrays

    # reading file for headers
    colspecs = [[0, 15], [16, 150]]
    db_headers = pd.read_fwf(path + file_name, colspecs=colspecs, header=None)

    # getting indexes for start/end of headers and data
    start_of_headers = db_headers.loc[db_headers[0].str.contains('OBJECT.....')].index
    end_of_headers = db_headers.loc[db_headers[0] == 'DATA:'].index + 1
    end_of_arrays = db_headers.loc[db_headers[0].str.contains('====')].index

    # creating arrays to store separated data
    data = [0] * len(start_of_headers)
    header = [0] * len(start_of_headers)
    data_pd = [0] * len(start_of_headers)

    # splitting datafile into separate arrays
    for i in range(len(start_of_headers)):
        data[i] = full_db_arrays[end_of_headers[i]:end_of_arrays[i]]
        data[i] = [data[i][j].split() for j in range(len(data[i]))]
        data_pd[i] = pd.DataFrame(data[i])
        header[i] = db_headers[start_of_headers[i]:end_of_headers[i]]

    # getting header
    headers_horizontal = [item.T for item in header]  # transpose array to read header
    headers_header = [headers_horizontal[i].iloc[0] for i in range(len(headers_horizontal))]
    # getting header
    headers_horizontal = [headers_horizontal[i][1:] for i in range(len(headers_horizontal))]

    # adding header to header arrays
    for i in range(len(headers_horizontal)):
        headers_horizontal[i].columns = headers_header[i]

    # creating keyword translator for easy access purposes
    try:
        keywords = headers_horizontal[1].columns
    except IndexError:
        keywords = headers_horizontal[0].columns
    keywords_strp = [list(keywords)[i].strip('.:') for i in range(len(keywords))]
    kw_tls = {keywords_strp[i]: keywords[i] for i in range(len(keywords))}
    # getting observing sites
    obs_sites = []
    for i in range(len(headers_horizontal)):
        obs_sites.append(headers_horizontal[i][kw_tls['OBSERVING SITE']][1])
    obs_sites = pd.DataFrame(obs_sites)

    # getting unique observing sites to create keyword translator
    obs_sites_unique = obs_sites[0].unique()
    print(obs_sites_unique)
    # print(obs_sites_unique)
    obs_codes_unique = ['D53', '186', '119', 'V26', 'N42', {'lon': 66.90,
                                                            'lat': 38.67, 'elevation': 2.6}, '121', '583', '071', '061']
    obs_codes_kwd = {obs_sites_unique[i]: obs_codes_unique[i] for i in range(len(obs_sites_unique))}
    print(obs_codes_kwd)

    # getting object_numbers, start observe times and observatory codes
    object_nums = [headers_horizontal[i][kw_tls['OBJECT']].str.split(' ')[1][0] + ' ' +
                   headers_horizontal[i][kw_tls['OBJECT']].str.split(' ')[1][1] for i in range(len(header))]
    zero_times = [headers_horizontal[i][kw_tls['ZERO TIME']].str.split(' ')[1][0] for i in range(len(header))]
    obs_codes = [obs_codes_kwd[headers_horizontal[i][kw_tls['OBSERVING SITE']][1]] for i in range(len(header))]
    # print(obs_codes)

    # getting starting times
    arr_len = range(len(data_pd))
    start_jd = [zero_times[i] for i in arr_len]
    # get observation epochs
    epochs_times = [data_pd[i][0] for i in arr_len]
    # transtating dec-times to jd_times
    epochs_jd = [epochs_times[i].apply(decimal_to_jd) for i in arr_len]
    # adding starting time to observation epochs
    epochs_full_1 = [epochs_jd[i].add(float(start_jd[i])) for i in arr_len]
    epochs_full_l = [list(epochs_full_1[i]) for i in arr_len]
    # get data(ephemerides) from JPL:
    # object_nums[0] = '2019 OK'
    # print(object_nums)
    jpl_data = [JPL_query_eph_to_db(
        body='{}'.format(object_nums[i]),
        epochs=epochs_full_l[i],
        location=obs_codes[i],
        columns=['r', 'delta', 'alpha_true', 'PABLon', 'PABLat'])
        for i in tqdm(arr_len)]

    print('obs_codes:', obs_codes)
    print('object_ids:', object_nums)

    '''
    dropcols = ['elongFlag', 'airmass', 'magextinct', 'V',
                 'surfbright', 'r_rate', 'delta_rate',
                 'lighttime', 'elong', 'lunar_elong', 'lunar_illum',
                 'AZ', 'EL']
    for key in dropcols:
        if key not in jpl_data[0].columns:
            dropcols.remove(key)
    '''

    jpl_data_reduc = jpl_data#[jpl_data[i].drop(columns=dropcols) for i in range(len(jpl_data))]
    jpl_data_rows = [[(jpl_data_reduc[j].values[i])
                      for i in range(len(jpl_data_reduc[j]))]
                     for j in range(len(jpl_data_reduc))]

    # reading whole file(again) to add JPL data to the existing file
    with open("{}{}".format(path, file_name), "r") as file:
        full_db_arrays = file.readlines()
    full_db_arrays_copy = full_db_arrays
    getcontext().prec = 5

    # adding data to existing file
    for arr_num in range(len(end_of_arrays)):
        for k, j in enumerate(range(end_of_headers[arr_num], end_of_arrays[arr_num])):
            row = ''
            for i in range(len(jpl_data_rows[arr_num][k])):
                row += '{0:.4f}'.format(jpl_data_rows[arr_num][k][i]) + ' '
            full_db_arrays_copy[j] = full_db_arrays_copy[j].strip('\n') + ' ' + row + '\n'

    # writing modified data to file
    with open(path + "{}_modified.ATL".format(file_name[:-4]), 'w') as output_file:
        for i in range(len(full_db_arrays_copy)):
            output_file.write(full_db_arrays_copy[i])
    print("Done!")

    return full_db_arrays_copy


def queryATL_to_csv(path, file_name):
    # reading file for headers
    colspecs = [[0, 15], [16, 150]]
    full_db_headers = pd.read_fwf(path + file_name, colspecs=colspecs, header=None)

    # reading whole file
    file = open("{}{}".format(path, file_name), "r")
    full_db_arrays = file.readlines()
    file.close()

    # getting indexes for start/end of headers and data
    start_of_headers = full_db_headers.loc[full_db_headers[0].str.contains('OBJECT.....')].index
    end_of_headers = full_db_headers.loc[full_db_headers[0] == 'DATA:'].index + 1
    end_of_arrays = full_db_headers.loc[full_db_headers[0].str.contains('====')].index

    # creating arrays to store separated data
    data = [0] * len(start_of_headers)
    header = [0] * len(start_of_headers)
    data_pd = [0] * len(start_of_headers)

    # splitting datafile into separate arrays
    for i in range(len(start_of_headers)):
        data[i] = full_db_arrays[end_of_headers[i]:end_of_arrays[i]]
        data[i] = [data[i][j].split() for j in range(len(data[i]))]
        data_pd[i] = pd.DataFrame(data[i])
        header[i] = full_db_headers[start_of_headers[i]:end_of_headers[i]]

    # getting header
    headers_horizontal = [item.T for item in header]  # transpose array to read header
    headers_header = [headers_horizontal[i].iloc[0] for i in range(len(headers_horizontal))]
    # getting header
    headers_horizontal = [headers_horizontal[i][1:] for i in range(len(headers_horizontal))]
    # print(headers_horizontal)
    # adding header to header arrays
    for i in range(len(headers_horizontal)):
        headers_horizontal[i].columns = headers_header[i]
    # print(headers_horizontal[0])
    # creating keyword translator for easy access purposes
    try:
        keywords = headers_horizontal[1].columns
    except IndexError:
        keywords = headers_horizontal[0].columns
    keywords_strp = [list(keywords)[i].strip('.:') for i in range(len(keywords))]
    kw_tls = {keywords_strp[i]: keywords[i] for i in range(len(keywords))}
    # getting observing sites
    obs_sites = []
    for i in range(len(headers_horizontal)):
        obs_sites.append(headers_horizontal[i][kw_tls['OBSERVING SITE']][1])
    obs_sites = pd.DataFrame(obs_sites)

    # getting unique observing sites to create keyword translator
    obs_sites_unique = obs_sites[0].unique()
    # print(obs_sites_unique)
    obs_codes_unique = ['D53', '186', '119', 'V26', 'N42', {'lon': 66.90,
                                                            'lat': 38.67, 'elevation': 2.6}, '121', '583', '071', '061']
    obs_codes_kwd = {obs_sites_unique[i]: obs_codes_unique[i] for i in range(len(obs_sites_unique))}

    # getting object_numbers, start observe times and observatory codes
    object_nums = [headers_horizontal[i][kw_tls['OBJECT']].str.split(' ')[1][0] + ' ' +
                   headers_horizontal[i][kw_tls['OBJECT']].str.split(' ')[1][1] for i in range(len(header))]
    zero_times = [headers_horizontal[i][kw_tls['ZERO TIME']].str.split(' ')[1][0] for i in range(len(header))]
    obs_codes = [obs_codes_kwd[headers_horizontal[i][kw_tls['OBSERVING SITE']][1]] for i in range(len(header))]
    # print(obs_codes)

    # getting starting times
    arr_len = range(len(data_pd))
    start_jd = [zero_times[i] for i in arr_len]
    # get observation epochs
    epochs_times = [data_pd[i][0] for i in arr_len]
    # transtating dec-times to jd_times
    epochs_jd = [epochs_times[i].apply(decimal_to_jd) for i in arr_len]
    # adding starting time to observation epochs
    epochs_full_1 = [epochs_jd[i].add(float(start_jd[i])) for i in arr_len]
    epochs_full_l = [list(epochs_full_1[i]) for i in arr_len]
    # get data(ephemerides) from JPL:
    # object_nums[0] = '2019 OK'
    # print(object_nums)
    jpl_data = [jpl_query_ephemerides(
        body='{}'.format(object_nums[i]),
        epochs=epochs_full_l[i],
        location=obs_codes[i],
        columns=['datetime_str', 'RA', 'DEC', 'alpha', 'delta', 'PABLon'])
        for i in tqdm(arr_len)]

    dropcols1 = ['elongFlag', 'airmass', 'magextinct', 'V',
                 'surfbright', 'r', 'r_rate', 'delta', 'delta_rate',
                 'lighttime', 'elong', 'lunar_elong', 'lunar_illum',
                 'PABLon', 'PABLat', 'AZ', 'EL']
    dropcols = ['elongFlag', 'PABLon', 'PABLat']
    for idx, data_part in enumerate(jpl_data):
        data_part.to_csv(path + '{}_{}{}'.format(file_name[:-4], idx, '.csv'))

    return jpl_data
'''
def queryATL_add_eph(path, file_name):
    # reading file for headers
    colspecs = [[0, 15], [16, 150]]
    full_db_headers = pd.read_fwf(path + file_name, colspecs=colspecs, header=None)

    # reading whole file
    with open("{}{}".format(path, file_name), "r") as file:
        full_db_arrays = file.readlines()

    # getting indexes for start/end of headers and data
    start_of_headers = full_db_headers.loc[full_db_headers[0].str.contains('OBJECT.....')].index
    end_of_headers = full_db_headers.loc[full_db_headers[0] == 'DATA:'].index + 1
    end_of_arrays = full_db_headers.loc[full_db_headers[0].str.contains('====')].index

    # creating arrays to store separated data
    data = [0] * len(start_of_headers)
    header = [0] * len(start_of_headers)
    data_pd = [0] * len(start_of_headers)

    # splitting datafile into separate arrays
    for i in range(len(start_of_headers)):
        data[i] = full_db_arrays[end_of_headers[i]:end_of_arrays[i]]
        data[i] = [data[i ][j].split() for j in range(len(data[i]))]
        data_pd[i] = pd.DataFrame(data[i])
        header[i] = full_db_headers[start_of_headers[i]:end_of_headers[i]]

    # getting header
    headers_horizontal = [item.T for item in header]  # transpose array to read header
    headers_header = [headers_horizontal[i].iloc[0] for i in range(len(headers_horizontal))]
    # getting header
    headers_horizontal = [headers_horizontal[i][1:] for i in range(len(headers_horizontal))]

    # adding header to header arrays
    for i in range(len(headers_horizontal)):
        headers_horizontal[i].columns = headers_header[i]

    # creating keyword translator for easy access purposes
    try:
        keywords = headers_horizontal[1].columns
    except IndexError:
        keywords = headers_horizontal[0].columns
    keywords_strp = [list(keywords)[i].strip('.:') for i in range(len(keywords))]
    kw_tls = {keywords_strp[i]: keywords[i] for i in range(len(keywords))}
    # getting observing sites
    obs_sites = []
    for i in range(len(headers_horizontal)):
        obs_sites.append(headers_horizontal[i][kw_tls['OBSERVING SITE']][1])
    obs_sites = pd.DataFrame(obs_sites)

    # getting unique observing sites to create keyword translator
    obs_sites_unique = obs_sites[0].unique()
    # print(obs_sites_unique)
    obs_codes_unique = ['D53', '186', '119', 'V26', 'N42', {'lon': 66.90,
                                                            'lat': 38.67, 'elevation': 2.6}, '121', '583', '071', '061']
    obs_codes_kwd = {obs_sites_unique[i]: obs_codes_unique[i] for i in range(len(obs_sites_unique))}

    # getting object_numbers, start observe times and observatory codes
    object_nums = [headers_horizontal[i][kw_tls['OBJECT']].str.split(' ')[1][0] + ' ' +
                   headers_horizontal[i][kw_tls['OBJECT']].str.split(' ')[1][1] for i in range(len(header))]
    zero_times = [headers_horizontal[i][kw_tls['ZERO TIME']].str.split(' ')[1][0] for i in range(len(header))]
    obs_codes = [obs_codes_kwd[headers_horizontal[i][kw_tls['OBSERVING SITE']][1]] for i in range(len(header))]
    # print(obs_codes)

    # getting starting times
    arr_len = range(len(data_pd))
    start_jd = [zero_times[i] for i in arr_len]
    # get observation epochs
    epochs_times = [data_pd[i][0] for i in arr_len]
    # transtating dec-times to jd_times
    epochs_jd = [epochs_times[i].apply(decimal_to_jd) for i in arr_len]
    # adding starting time to observation epochs
    epochs_full_1 = [epochs_jd[i].add(float(start_jd[i])) for i in arr_len]
    epochs_full_l = [list(epochs_full_1[i]) for i in arr_len]
    # get data(ephemerides) from JPL:
    # object_nums[0] = '2019 OK'
    # print(object_nums)
    jpl_data = [JPL_query_eph_to_db(
        body='{}'.format(object_nums[i]),
        epochs=epochs_full_l[i],
        location=obs_codes[i],
        columns=['r', 'delta', 'alpha_true', 'PABLon', 'PABLat'])
        # columns=['datetime_str', 'RA', 'DEC', 'alpha', 'delta', 'PABLon'])
        for i in tqdm(arr_len)]

    dropcols1 = ['elongFlag', 'airmass', 'magextinct', 'V',
                 'surfbright', 'r', 'r_rate', 'delta', 'delta_rate',
                 'lighttime', 'elong', 'lunar_elong', 'lunar_illum',
                 'PABLon', 'PABLat', 'AZ', 'EL']
    dropcols = ['elongFlag', 'delta_rate', 'PABLon', 'PABLat']
    # print(jpl_data[0].columns)
    for key in dropcols:
        if key not in jpl_data[0].columns:
            dropcols.remove(key)
    jpl_data_reduc = [jpl_data[i].drop(columns=dropcols) for i in range(len(jpl_data))]
    jpl_data_rows = [[(jpl_data_reduc[j].values[i])
                      for i in range(len(jpl_data_reduc[j]))]
                     for j in range(len(jpl_data_reduc))]
    # print(jpl_data_reduc[0].to_numpy())
    jpl_data_rows1 = [[str(jpl_data_reduc[j].values[i]).strip('[]')
                       for i in range(len(jpl_data_reduc[j]))]
                      for j in range(len(jpl_data_reduc))]

    # reading whole file(again) to add JPL data to the existing file
    file = open("{}{}".format(path, file_name), "r")
    full_db_arrays = file.readlines()
    file.close()
    full_db_arrays_copy = full_db_arrays
    getcontext().prec = 5

    # adding data to existing file
    for arr_num in range(len(end_of_arrays)):
        for k, j in enumerate(range(end_of_headers[arr_num], end_of_arrays[arr_num])):
            row = ''
            for i in range(len(jpl_data_rows[arr_num][k])):
                row += '{0:.4f}'.format(jpl_data_rows[arr_num][k][i]) + ' '
                # print(row)
            full_db_arrays_copy[j] = full_db_arrays_copy[j].strip('\n') + ' ' + row + '\n'
    # writing modified data to file
    with open(path + "{}_modified.ATL".format(file_name[:-4]), 'w') as output_file:
        for i in range(len(full_db_arrays_copy)):
            output_file.write(full_db_arrays_copy[i])

    return full_db_arrays_copy
'''

def queryATL_to_csv(path, file_name):
    # reading file for headers
    colspecs = [[0, 15], [16, 150]]
    full_db_headers = pd.read_fwf(path + file_name, colspecs=colspecs, header=None)

    # reading whole file
    file = open("{}{}".format(path, file_name), "r")
    full_db_arrays = file.readlines()
    file.close()

    # getting indexes for start/end of headers and data
    start_of_headers = full_db_headers.loc[full_db_headers[0].str.contains('OBJECT.....')].index
    end_of_headers = full_db_headers.loc[full_db_headers[0] == 'DATA:'].index + 1
    end_of_arrays = full_db_headers.loc[full_db_headers[0].str.contains('====')].index

    # creating arrays to store separated data
    data = [0] * len(start_of_headers)
    header = [0] * len(start_of_headers)
    data_pd = [0] * len(start_of_headers)

    # splitting datafile into separate arrays
    for i in range(len(start_of_headers)):
        data[i] = full_db_arrays[end_of_headers[i]:end_of_arrays[i]]
        data[i] = [data[i][j].split() for j in range(len(data[i]))]
        data_pd[i] = pd.DataFrame(data[i])
        header[i] = full_db_headers[start_of_headers[i]:end_of_headers[i]]

    # getting header
    headers_horizontal = [item.T for item in header]  # transpose array to read header
    headers_header = [headers_horizontal[i].iloc[0] for i in range(len(headers_horizontal))]
    # getting header
    headers_horizontal = [headers_horizontal[i][1:] for i in range(len(headers_horizontal))]
    # print(headers_horizontal)
    # adding header to header arrays
    for i in range(len(headers_horizontal)):
        headers_horizontal[i].columns = headers_header[i]
    # print(headers_horizontal[0])
    # creating keyword translator for easy access purposes
    try:
        keywords = headers_horizontal[1].columns
    except IndexError:
        keywords = headers_horizontal[0].columns
    keywords_strp = [list(keywords)[i].strip('.:') for i in range(len(keywords))]
    kw_tls = {keywords_strp[i]: keywords[i] for i in range(len(keywords))}
    # getting observing sites
    obs_sites = []
    for i in range(len(headers_horizontal)):
        obs_sites.append(headers_horizontal[i][kw_tls['OBSERVING SITE']][1])
    obs_sites = pd.DataFrame(obs_sites)

    # getting unique observing sites to create keyword translator
    obs_sites_unique = obs_sites[0].unique()
    # print(obs_sites_unique)
    obs_codes_unique = ['D53', '186', '119', 'V26', 'N42', {'lon': 66.90,
                                                            'lat': 38.67, 'elevation': 2.6}, '121', '583', '071', '061']
    obs_codes_kwd = {obs_sites_unique[i]: obs_codes_unique[i] for i in range(len(obs_sites_unique))}

    # getting object_numbers, start observe times and observatory codes
    object_nums = [headers_horizontal[i][kw_tls['OBJECT']].str.split(' ')[1][0] + ' ' +
                   headers_horizontal[i][kw_tls['OBJECT']].str.split(' ')[1][1] for i in range(len(header))]
    zero_times = [headers_horizontal[i][kw_tls['ZERO TIME']].str.split(' ')[1][0] for i in range(len(header))]
    obs_codes = [obs_codes_kwd[headers_horizontal[i][kw_tls['OBSERVING SITE']][1]] for i in range(len(header))]
    # print(obs_codes)

    # getting starting times
    arr_len = range(len(data_pd))
    start_jd = [zero_times[i] for i in arr_len]
    # get observation epochs
    epochs_times = [data_pd[i][0] for i in arr_len]
    # transtating dec-times to jd_times
    epochs_jd = [epochs_times[i].apply(decimal_to_jd) for i in arr_len]
    # adding starting time to observation epochs
    epochs_full_1 = [epochs_jd[i].add(float(start_jd[i])) for i in arr_len]
    epochs_full_l = [list(epochs_full_1[i]) for i in arr_len]
    # get data(ephemerides) from JPL:
    # object_nums[0] = '2019 OK'
    # print(object_nums)
    jpl_data = [jpl_query_ephemerides(
        body='{}'.format(object_nums[i]),
        epochs=epochs_full_l[i],
        location=obs_codes[i],
        columns=['datetime_str', 'RA', 'DEC', 'alpha', 'delta', 'PABLon'])
        for i in tqdm(arr_len)]

    dropcols1 = ['elongFlag', 'airmass', 'magextinct', 'V',
                 'surfbright', 'r', 'r_rate', 'delta', 'delta_rate',
                 'lighttime', 'elong', 'lunar_elong', 'lunar_illum',
                 'PABLon', 'PABLat', 'AZ', 'EL']
    dropcols = ['elongFlag', 'PABLon', 'PABLat']
    for idx, data_part in enumerate(jpl_data):
        data_part.to_csv(path + '{}_{}{}'.format(file_name[:-4], idx, '.csv'))

    return jpl_data
