import math
import numpy as np
import pandas as pd
from astropy.table import QTable, Table, vstack
#from astroquery.jplsbdb import SBDB
from astroquery.jplhorizons import Horizons
from astropy.time import Time
#from astroquery.mpc import MPC
from pprint import pprint
from tqdm import tqdm_notebook, tqdm, trange
from pathlib import Path
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

def init_obs_dict():
    """"""
    dict_path = 'data/observatories.dat'
    obs_dict = {}
    with open(dict_path, 'r') as file:
        obs_file = file.readlines()[1:]
    for obs_site in obs_file:
        code, site = obs_site.strip('\n').split(maxsplit=1)
        #print(code, site)
        obs_dict.update({site: code})
    return obs_dict


def modify_string(string, add_data):
    """"""
    mod_string = string.strip('\n') + ' ' + add_data + '\n'
    return mod_string


def jpl_query_eph(body, epochs, to_csv=False, **kwargs):
    # =============================================
    if 'location' in kwargs:
        location = kwargs['location']
    elif 'location' == 'NaN':
        location = '121'
    if 'columns' in kwargs:
        columns = kwargs['columns']
    else:
        columns = 'default'

    if columns == 'default' and not to_csv:
        columns = ['r', 'delta', 'alpha_true', 'PABLon', 'PABLat']
    elif columns == 'default' and to_csv:
        columns = ['targetname',
                   'datetime_str',
                   'datetime_jd',
                   'flags',
                   'RA',
                   'DEC',
                   'AZ',
                   'EL',
                   'airmass',
                   'magextinct',
                   'V',
                   'surfbright',
                   'r',
                   'r_rate',
                   'delta',
                   'delta_rate',
                   'lighttime',
                   'elong',
                   'elongFlag',
                   'lunar_elong',
                   'lunar_illum',
                   'alpha_true',
                   'PABLon',
                   'PABLat']

    # ===============================================
    # query is split into chunks of 200 elements
    start = 0
    step = 200
    end = len(epochs)
    full_ephemerides = []

    for i in range(start, end, step):
        obj = Horizons(id="{}".format(body), location=location, epochs=epochs[i:i + step])
        chunk_ephemerides = obj.ephemerides()[columns]
        full_ephemerides = vstack([full_ephemerides, chunk_ephemerides])

    full_ephemerides_pd = full_ephemerides.to_pandas().drop(columns="col0")
    pd.options.display.float_format = '{:,.4f}'.format
    if to_csv:
        full_ephemerides_pd.to_csv('test_files/tests/{}.csv'.format(body),
                                   mode='w', index=False, header=True, encoding='utf8', float_format='%.6f')
    full_ephemerides_pd = full_ephemerides_pd.round(5)
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


def read_file(path, file_name):
    """reads file and returns plain text"""
    with open("{}{}".format(path, file_name), "r") as file:
        file_text = file.readlines()
        return file_text


def read_observatories(path, file_name):
    obs_disc = {}
    with open(path + file_name) as file:
        for idx, line in enumerate(file):
            # skip header
            if idx == 0:
                continue
            value, key = line.rstrip().split('    ')
            obs_disc[key] = value
    return obs_disc


def queryATL_add_eph(path, file_name):
    """Adds HORIZON data to ATL file"""
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
        # getting measurements, splitting, and storing them as separate dataframe elements
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

    # creating headers keywords translator for easy access purposes
    try:
        # headers keywords
        keywords = headers_horizontal[1].columns
    except IndexError:
        keywords = headers_horizontal[0].columns
    # stripping keywords from "...."
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
    # read observatories and their codes to dict from dat file
    obs_data = read_observatories("", "../data/observatories.dat")
    # print(obs_sites_unique)
    obs_codes_kwd = {obs_sites_unique[i]:
                     obs_data.get(obs_sites_unique[i])
                     for i in range(len(obs_sites_unique))}

    # getting object_numbers, start observe times and observatory codes for every query
    object_nums = [headers_horizontal[i][kw_tls['OBJECT']].str.split(' ')[1][0] + ' ' +
                   headers_horizontal[i][kw_tls['OBJECT']].str.split(' ')[1][1] for i in range(len(header))]
    zero_times = [headers_horizontal[i][kw_tls['ZERO TIME']].str.split(' ')[1][0] for i in range(len(header))]
    obs_codes = [obs_codes_kwd[headers_horizontal[i][kw_tls['OBSERVING SITE']][1]] for i in range(len(header))]

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
    # print(object_nums)
    jpl_data = [JPL_query_eph_to_db(
        body='{}'.format(object_nums[i]),
        epochs=epochs_full_l[i],
        location=obs_codes[i],
        columns=['r', 'delta', 'alpha_true', 'PABLon', 'PABLat'])
        for i in tqdm(arr_len)]

    print('obs_codes:', obs_codes)
    print('object_ids:', object_nums)

    jpl_data_rows = [[(jpl_data[j].values[i])
                      for i in range(len(jpl_data[j]))]
                      for j in range(len(jpl_data))]

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
