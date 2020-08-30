import re
from astropy.table import vstack
from astroquery.jplhorizons import Horizons
import pandas as pd

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
    """
    initialize dictionary of observing_sites
    from observatories.dat file
    """
    dict_path = 'src/data/observatories.dat'
    obs_dict = {}
    with open(dict_path, 'r') as file:
        obs_file = file.readlines()[1:]
    for obs_site in obs_file:
        code, site = obs_site.strip('\n').split(maxsplit=1)
        #print(code, site)
        obs_dict.update({site: code})
    return obs_dict


def modify_string(string, add_data):
    """adds data to the string"""
    mod_string = string.strip('\n') + ' ' + add_data + '\n'
    return mod_string


def jpl_query_eph(body, epochs, to_csv=False, **kwargs):
    """makes query to the JPL HORIZON system"""
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


def get_orbital_elem(body, epochs, jd_dates, **kwargs):
    """"""
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
    """"""
    obs_disc = {}
    with open(path + file_name) as file:
        for idx, line in enumerate(file):
            # skip header
            if idx == 0:
                continue
            value, key = line.rstrip().split('    ')
            obs_disc[key] = value
    return obs_disc


def read_mpc_codes(mpc_file):
    """"""
    with open(mpc_file, 'r') as file:
        mpc_file = file.readlines()
    codes = [line.split(maxsplit=1)[0] for line in mpc_file[1:]]
    return codes


def is_obscode_valid(obs_code: str) -> bool:
    """"""
    mpc_codes_path = 'src/data/observatories_mpc.dat'
    obs_code = str(obs_code)
    code_length = len(obs_code)
    if code_length != 3:
        is_valid = False
        return is_valid
    mpc_codes = read_mpc_codes(mpc_codes_path)
    if obs_code in mpc_codes:
        is_valid = True
    else:
        is_valid = False
    return is_valid


def read_code_parenthesis(obs_string):
    """"""
    obs_code = obs_string.rsplit(maxsplit=1)[1].strip("().{}|'\|/")
    return obs_code


def parse_ast_name(name_str):
    """parses asteroids namestring, splits into
    separate id's of the asteroid
    return number, name, and provisional name of an asteroid
    """
    prov_name = None  # provisional name (e.g. 2019 GG26)
    desg_num = None  # asteroid's number (e.g. 66391)
    name = None  # proper name (e.g. Justitia)

    name_stripped = re.sub('[() ?.!/;:]', ' ', name_str)
    namesplit = name_stripped.split()
    for npart in namesplit:
        try:
            # check if number
            npart_num = int(npart)
            # check part of prov_name
            if 1900 < npart_num < 2030:
                prov_name = str(npart_num)
            else:
                desg_num = npart_num
        # if not a number, than string
        except ValueError:
            # check if name
            if len(npart) > 4:
                name = npart
            # check if part of prov number
            contains_digit = any(map(str.isdigit, npart))
            if len(npart) <= 4 and contains_digit:
                prov_name += " " + npart
    return desg_num, name, prov_name



