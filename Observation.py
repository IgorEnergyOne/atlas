import Functions as fn

class Observation:
    """"""
    # len of fields in a header
    len_field = 15
    """docstring"""

    def __init__(self,
                 text=None,
                 header=None,
                 obs_data=None,
                 obs_obj=None,
                 obs_site=None,
                 query_data=None
                 ):

        """Constructor"""
        self.text = text
        self.header = header
        self.obs_data = obs_data
        self.obs_obj = obs_obj
        self.obs_site = obs_site
        self.query_data = query_data

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        if value is None:
            self._text = None
        else:
            self._text = value

    @property
    def header(self):
        return self._header

    @header.setter
    def header(self, value):
        if value is None:
            self._header = None
        else:
            self._header = value

    @property
    def obs_data(self):
        return self._obs_data

    @obs_data.setter
    def obs_data(self, value):
        if value is None:
            self._obs_data = None
        else:
            self._obs_data = value

    @property
    def obs_obj(self):
        return self._obs_obj

    @obs_obj.setter
    def obs_obj(self, value):
        if value is None:
            self._obs_obj = None
        else:
            self._obs_obj = value

    @property
    def obs_site(self):
        return self._obs_site

    @obs_site.setter
    def obs_site(self, value):
        if value is None:
            self._obs_site = None
        else:
            self._obs_site = value

    @property
    def query_data(self):
        return self._query_data

    @query_data.setter
    def query_data(self, value):
        if value is None:
            self._query_data = None
        else:
            self._query_data = value

    def read_header(self):
        """"""
        sep = "DATA:"
        sep_idx = self.find_row_idx(self._text, sep)
        header = self._text[:sep_idx]
        header_dict = {}
        for row in header:
            field = row[:self.len_field].strip('.:')
            value = row[self.len_field:].strip('\n " "')
            header_dict.update({field: value})
        self._header = header_dict
        return 0

    def read_obs_site(self):
        """"""
        field = "OBSERVING SITE"
        self._obs_site = self._header[field]
        obs_site_dict = fn.init_obs_dict()
        obs_code = obs_site_dict.get(self._obs_site)
        if obs_code is not None:
            self._obs_site = obs_code
        else:
            self._obs_site = input("Enter observatory code for {} \n".format(self._obs_site))
        return 0

    def read_object(self):
        """"""
        field = "OBJECT"
        self._obs_obj = self._header[field].split(maxsplit=1)[1]
        return 0

    def read_obs_times(self):
        """"""
        field_unit = "UNIT OF TIME"
        unit = self._header[field_unit]
        field_start = "ZERO TIME"
        try:
            start = float(self._header[field_start])
        except ValueError:
            start = float(self._header[field_start].split()[0])
        obs_times = [float(row.split()[0]) for row in self._obs_data]
        obs_times_jd_full = [fn.decimal_to_jd(obs_time) + start for obs_time in obs_times]
        return obs_times_jd_full

    def read_obs_data(self):
        sep = "DATA:"
        sep_idx = self.find_row_idx(self._text, sep)
        self._obs_data = self._text[sep_idx + 1:-1]
        return 0

    def find_row_idx(self, where: list, what: str) -> int:
        """doctring"""
        idx = [idx for idx, row in
               enumerate(where) if what in row][0]
        return idx

    def make_query(self, to_csv=False, **kwargs):
        """"""
        query_data = fn.jpl_query_eph(body=self.obs_obj,
                                      location=self._obs_site,
                                      epochs=self.read_obs_times(),
                                      to_csv=to_csv,
                                      **kwargs)
        self._query_data = query_data
        new_columns = ' '.join(query_data.columns)
        return 0

    def add_query_to_atl(self):
        column_field = 'COLUMNS'
        new_columns = ' '.join(self._query_data.columns)
        field_idx = self.find_row_idx(where=self._text, what=column_field)
        self._text[field_idx] = self._text[field_idx].strip('\n') + ' ' + new_columns + '\n'
        # finding the end of header:
        data_start_field = 'DATA:'
        data_start_idx = self.find_row_idx(where=self._text, what=data_start_field)
        for idx, row in enumerate(self._query_data.values.tolist()):
            str_row = ' '.join(["{:.4f}".format(i) for i in row])
            self._text[idx + data_start_idx+1] = self._obs_data[idx].strip('\n') + ' ' + str_row + '\n'
        return 0

    def obs_pipeline(self, to_csv=False):
        self.read_header()
        self.read_object()
        self.read_obs_site()
        self.read_obs_data()
        self.read_obs_times()
        self.make_query(to_csv=to_csv)
        self.add_query_to_atl()
        return 0

    # def build_modified_obs(self):
    #     modified_obs = self._header + self._obs_data


