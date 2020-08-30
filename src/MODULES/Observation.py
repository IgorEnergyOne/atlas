from src.MODULES import Functions as fn


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
        """gets all the rows of the header from observation"""
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

    @staticmethod
    def read_code_parenthesis(obs_string):
        """"""
        obs_code = obs_string.rsplit(maxsplit=1)[1].strip("().{}|'\|/")
        return obs_code

    def read_obs_site(self):
        """get observing site"""
        field = "OBSERVING SITE"
        obs_site = self._header[field]
        obs_site_dict = fn.init_obs_dict()
        obs_code = obs_site_dict.get(obs_site)
        if obs_code is None:
            obs_code = self.read_code_parenthesis(obs_site)
            if fn.is_obscode_valid(obs_code):
                self._obs_site = obs_code
            else:
                self._obs_site = input("Enter observatory code for {} \n".format(self._obs_site))
        else:
            self._obs_site = obs_code
        return 0

    def read_object(self):
        """get the name of the object"""
        field = "OBJECT"
        self._obs_obj = fn.parse_ast_name(self._header[field])
        # print(self._obs_obj)
        return 0

    def read_obs_times(self):
        """"""
        field_unit = "UNIT OF TIME"
        field_start = "ZERO TIME"
        try:
            start = float(self._header[field_start])
        except ValueError:
            start = float(self._header[field_start].split()[0])
        obs_times = [float(row.split()[0]) for row in self._obs_data]
        obs_times_jd_full = [fn.decimal_to_jd(obs_time) + start for obs_time in obs_times]
        return obs_times_jd_full

    def read_obs_data(self):
        """"""
        sep = "DATA:"
        sep_idx = self.find_row_idx(self._text, sep)
        self._obs_data = self._text[sep_idx + 1:-1]
        return 0

    @staticmethod
    def find_row_idx(where: list, what: str) -> int:
        """doctring"""
        idx = [idx for idx, row in
               enumerate(where) if what in row][0]
        return idx

    def make_query(self, to_csv=False, **kwargs):
        """"""
        for id in reversed(self.obs_obj):
            if id is not None:
                query_data = fn.jpl_query_eph(body=id,
                                              location=self._obs_site,
                                              epochs=self.read_obs_times(),
                                              to_csv=to_csv,
                                              **kwargs)
                self._query_data = query_data
                break
            else:
                continue
        return 0

    def calc_mean_aspect_data(self):
        """calculates mean values for the aspect data
        using queried HORIZON data and writes it to ATL file
        """
        column_field = 'ASPECT DATA'
        median_vals = self._query_data.mean().values
        new_asp_data = ' '.join(["{:.4f}".format(val) for val in median_vals])
        new_asp_data += " (PABLon  PABLat)"
        field_idx = self.find_row_idx(where=self._text, what=column_field)
        self._text[field_idx] = fn.modify_string("ASPECT DATA...:", new_asp_data)
        return 0

    def add_query_to_atl(self):
        """"""
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
        """pipeline to make all procedures with atl file"""
        self.read_header()
        self.read_object()
        self.read_obs_site()
        self.read_obs_data()
        self.read_obs_times()
        self.make_query(to_csv=to_csv)
        self.calc_mean_aspect_data()
        self.add_query_to_atl()
        return 0


