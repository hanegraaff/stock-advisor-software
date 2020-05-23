"""Author: Mark Hanegraaff -- 2020
"""


class Nop(object):
    """
        A simple mock class that does nothing
    """

    def nop(self, *args, **kw):
        pass

    def __getattr__(self, _):
        return self.nop
