# -*- coding: utf-8 -*-
from collections.abc import MutableMapping as DictMixin


def _hkey(s):
    return s.title().replace('_', '-')


class MultiDict(DictMixin):
    """ This dict stores multiple values per key, but behaves exactly like a
        normal dict in that it returns only the newest value for any given key.
        There are special methods available to access the full list of values.

        Basic Usage:

            >>> d = MultiDict([('a', 'b'), ('a', 'c')])
            >>> d
            MultiDict([('a', 'b'), ('a', 'c')])
            >>> d['a']
            'b'
            >>> d.getlist('a')
            ['b', 'c']
            >>> 'a' in d
            True
    """

    def __init__(self, *a, **kwargs):
        self.dict = {}
        for pl in a:
            for k, v in pl:
                l = self.dict.setdefault(k, [])
                l.append(v)
        for k, v in kwargs.items():
            l = self.dict.setdefault(k, [])
            l.append(v)

    def __len__(self):
        return len(self.dict)

    def __iter__(self):
        return iter(self.dict)

    def __contains__(self, key):
        return key in self.dict

    def __delitem__(self, key):
        del self.dict[key]

    def __getitem__(self, key):
        return self.dict[key][0]

    def __setitem__(self, key, value):
        self.append(key, value)

    def keys(self):
        return self.dict.keys()

    def values(self):
        return (v[0] for v in self.dict.values())

    def items(self):
        return ((k, v[0]) for k, v in self.dict.items())

    def allitems(self):
        return ((k, v) for k, vl in self.dict.items() for v in vl)

    iterkeys = keys
    itervalues = values
    iteritems = items
    iterallitems = allitems


    def get(self, key, default=None, index=0, type=None):
        """ Return the most recent value for a key.
            Args:

              * default: The default value to be returned if the key is not
                   present or the type conversion fails.
              * index: An index for the list of available values.
              * type: If defined, this callable is used to cast the value
                    into a specific type. Exception are suppressed and result in
                    the default value to be returned.
        """
        try:
            val = self.dict[key][index]
            return type(val) if type else val
        except Exception:
            pass
        return default

    def append(self, key, value):
        """ Add a new value to the list of values for this key. """
        self.dict.setdefault(key, []).append(value)

    def replace(self, key, value):
        """ Replace the list of values with a single value. """
        self.dict[key] = [value]

    def getall(self, key):
        """ Return a (possibly empty) list of values for a key. """
        return self.dict.get(key) or []

    #: Aliases for WTForms to mimic other multi-dict APIs (Django)
    getone = get
    getlist = getall


class HeaderDict(MultiDict):
    """ A case-insensitive version of `MultiDict` that defaults to
        replace the old value instead of appending it. """

    def __init__(self, *a, **ka):
        self.dict = {}
        if a or ka: self.update(*a, **ka)

    def __contains__(self, key):
        return _hkey(key) in self.dict

    def __delitem__(self, key):
        del self.dict[_hkey(key)]

    def __getitem__(self, key):
        return self.dict[_hkey(key)][0]

    def __setitem__(self, key, value):
        self.dict[_hkey(key)] = [value if isinstance(value, str) else
                                 str(value)]

    def append(self, key, value):
        self.dict.setdefault(_hkey(key), []).append(
            value if isinstance(value, str) else str(value))

    def replace(self, key, value):
        self.dict[_hkey(key)] = [value if isinstance(value, str) else
                                 str(value)]

    def getall(self, key):
        return self.dict.get(_hkey(key)) or []

    def get(self, key, default=None, index=0):
        return MultiDict.get(self, _hkey(key), default, index)



