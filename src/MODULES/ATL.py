from src.MODULES import Observation


class ATLFile:
    """docstring"""

    def __init__(self,
                 text=None,
                 file_path=None,
                 observations=None):

        """Constructor"""
        self.text = text
        self.file_path = file_path
        self.observations = observations

    @property
    def file_path(self):
        return self._file_path

    @file_path.setter
    def file_path(self, value):
        if value is None:
            self._file_path = None
        else:
            self._file_path = value

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        if value is None:
            self._text = None
        else:
            self._text = value

    def calc_observs_num(self):
        """"""
        start = 0
        key_substring = 'OBJECT.....'
        while True:
            start = self.text.find(key_substring, start)
            if start == -1:
                return
            yield start
            start += len(key_substring)  # use start += 1 to find overlapping matches

    def read_atl_file(self):
        """reads atl file into the text property by the provided path"""
        if self._file_path is None:
            raise Exception("path to file is not specified!")
        else:
            with open('{}'.format(self.file_path), 'r') as file:
                atl_text_full = file.readlines()
            self.text = atl_text_full
        return 0

    def separate_observations(self):
        """splits atl file into separate observations"""
        if self._text is None:
            self.read_atl_file()
        else:
            # finding separators indexes to split ATL
            # into separate observations
            sep = "====="
            size = len(self._text)
            sep_idxs = [sep_idx + 1 for sep_idx, row in
                        enumerate(self._text) if sep in row]
            # separating observations
            observations = [self._text[i: j] for i, j
                            in zip([0] + sep_idxs, sep_idxs
                            + ([size] if sep_idxs[-1] != size else []))]

            self.observations = [Observation.Observation(text=obs) for obs in observations]

    def write_observations(self, path=None):
        """write observations into separate files"""
        if path is None:
            path = self._file_path[:-4] + '_modified' + self._file_path[-4:]
        atl = ""
        for obs in self.observations:
            atl = atl + ''.join(obs.text)
        with open(path, 'w') as atl_file:
            atl_file.writelines(atl)
        return 0
