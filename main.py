import Functions as func
from pprint import pprint
import ATL

if __name__ == "__main__":

    path_to_files = 'atlas_test_files/'
    file = 'Z6391.ATL'

    #with open(path_to_files + file, 'r') as file:
    #    atl_file = file.readlines()

    #file = ATL
    #file.text = atl_file
    #obs_sites = func.read_observatories('', 'observatories.dat')
    #print(obs_sites)

    func.queryATL_add_eph(path=path_to_files, file_name="Z6391.ATL")

    #result = func.queryATL_to_csv(path="../../Desktop/2020-FB7_2020-03-31_Blagoveschensk/", file_name="Z0001.ATL")