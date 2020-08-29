#!/usr/bin/env python

""" run_atlas - wrapper for automated work with .atl files
"""

import argparse
from tqdm import tqdm
from src.MODULES import ATL


def run_atlas(filename, to_csv=False):
    """"""
    atl_file = ATL.ATLFile(file_path=filename)
    atl_file.read_atl_file()
    atl_file.separate_observations()
    for obs_idx, observation in enumerate(tqdm(atl_file.observations[:-1])):
        observation.obs_pipeline(to_csv=to_csv)
        atl_file.observations[obs_idx].text = observation.text

    atl_file.write_observations()
    print('Done!')


print("starting atlas...")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Automated ATL processing.')
    parser.add_argument('-file',
                        help='name of the file to process',
                        default=None)
    parser.add_argument('-to_csv',
                        help='write obtained ephemeris to csv file',
                        default=False)
    args = parser.parse_args()

    files = args.file
    to_csv_flag = args.to_csv
    run_atlas(filename=files, to_csv=to_csv_flag)