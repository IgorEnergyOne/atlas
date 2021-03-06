import os
from tqdm import tqdm
from src.MODULES import ATL

if __name__ == "__main__":

    path_to_files = 'atlas_test_files/'
    file = 'Z1685.ATL'
    file_2 = 'Z6391.ATL'
    file_3 = 'Z2019.ATL'
    file_path = os.path.join(path_to_files, file)

    print("path_to_file :", file_path)

    atl_file = ATL.ATLFile(file_path=file_path)
    atl_file.read_atl_file()
    atl_file.separate_observations()
    for obs_idx, observation in enumerate(tqdm(atl_file.observations[:-1])):
        observation.obs_pipeline(to_csv=False)
        atl_file.observations[obs_idx].text = observation.text

    atl_file.write_observations()

    '''
    observation.read_header()
    observation.read_object()
    observation.read_obs_site()
    observation.read_obs_data()
    observation.read_obs_times()
    print(observation.obs_obj)
    observation.make_query(to_csv=False)
    #print(observation.query_data)
    observation.add_query_to_atl()
    pprint(observation.text)
    '''
