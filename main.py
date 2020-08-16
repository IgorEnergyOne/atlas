import Functions as fn
import os
# os.path.join
from pprint import pprint
import ATL
import Observation

if __name__ == "__main__":
    path_to_files = 'atlas_test_files/'
    file = 'Z1685.ATL'
    file_2 = 'Z6391.ATL'
    file_path = os.path.join(path_to_files, file_2)

    print("path_to_file :", file_path)

    atl_file = ATL.ATLFile(file_path=file_path)
    atl_file.read_atl_file()
    #pprint(atl_file.text)
    atl_file.separate_observations()
    observation = atl_file.observations[1]
    observation.read_header()
    observation.read_object()
    observation.read_obs_site()
    observation.read_obs_data()
    observation.read_obs_times()
    print(observation.obs_obj)
    observation.make_query()
    print(observation.query_data)
    #pprint(atl_file.observations)
    # func.queryATL_add_eph(path=path_to_files, file_name="Z6391.ATL")
    # result = func.queryATL_to_csv(path="../../Desktop/2020-FB7_2020-03-31_Blagoveschensk/", file_name="Z0001.ATL")
