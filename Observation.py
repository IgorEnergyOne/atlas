
class Observation:
    """docstring"""

    def __init__(
            self,
            text='',
            observs_idx=0,
            obs_obj=None,
            obs_cite=None,
            observatory=None,

    ):
        """Constructor"""
        self.text = text
        self.observs_idx = observs_idx
        pass

    @property
    def text(self):
        return self.text

    @text.setter
    def text(self, value):
        self._text = value

    @property
    def obs_obj(self):
        return self.obs_obj

    @obs_obj.setter
    def obs_obj(self, value):
        self._obs_obj = value

    @property
    def observatory(self):
        return self.observatory

    @observatory.setter
    def observatory(self, value):
        self._observatory = value

    def get_observs_idx(self):
        return 0

    def get_observat(self, num_of_obser):
        return 0  # observat
