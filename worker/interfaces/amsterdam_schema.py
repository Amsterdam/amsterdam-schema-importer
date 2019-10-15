from collections import UserDict


class AmsterdamSchema(UserDict):
    @property
    def name(self):
        return self['id']