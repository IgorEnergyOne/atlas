class ATL_File:
    """docstring"""

    def __init__(
            self,
            text=None,
            observs_num=None
    ):

        """Constructor"""
        if self.text is None:
            self.text = {}
        else:
            self.text = text

        if self.observs_num is None:
            self.observs_num = 0
        else:
            self.observs_num = observs_num

    @property
    def observs_num(self):
        return self.observs_num

    @observs_num.setter
    def observs_num(self, value):
        self._observs_num = value

    @property
    def text(self):
        return self.text

    @text.setter
    def text(self, value):
        self._text = value

    def calc_observs_num(self):
        start = 0
        key_substring = 'OBJECT.....'
        while True:
            start = self.text.find(key_substring, start)
            if start == -1:
                return
            yield start
            start += len(key_substring)  # use start += 1 to find overlapping matches
