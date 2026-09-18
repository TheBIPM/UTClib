#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tabarray  - A python class to acces nupy strcutured array with matrix like syntax
Copyright (C) 2024  Giulio Tagliaferro, ....

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import numpy as np

class tabarray(np.ndarray):

    @classmethod
    def empty(cls, nrows, dtypes):
        """
        Create empty tabarray with `nrows` rows 
        and columns specs per `dtypes`
        """
        obj = tabarray(np.empty((nrows,), dtype=dtypes))
        # default values
        def get_fill_value(dt):
            kind = dt.kind
            if kind == 'f':       # Float
                return np.nan
            elif kind in ('i', 'u'):  # Signed or Unsigned Integer
                return np.iinfo(dt).max
            elif kind == 'b':     # Boolean
                return False
            elif kind == 'U':     # Unicode String
                # dt.itemsize is in bytes; Unicode uses 4 bytes per character
                # This creates a string of spaces equal to the max string length
                str_length = dt.itemsize // 4
                return ' ' * str_length
            else:
                return 0 # Fallback for other types
        # 4. Apply the fill values
        if obj.dtype.names is not None:
            # Structured Array: Fill each column (field) individually
            for col_name in obj.dtype.names:
                fill_val = get_fill_value(obj.dtype[col_name])
                obj[col_name] = fill_val
        return obj


    def __new__(cls, input_array):
        if type(input_array) is np.ndarray and input_array.ndim > 1:
            raise Exception("Sorry, mulitidmensional array not supported") 
        return np.asarray(input_array).view(cls)
    
    def __getitem__(self, key):
        """
         Summary line.
        
         overloading the __getitem__ method from ndarray.
         This way array[:][array.dtype.names[0]] becomes simply array[:,0]
         For a one dimensional structured array array[:,0] would throw an error so no coflict is possible
    
        
         """
        if type(key) is tuple and len(key) == 2:
            t_obj = super(tabarray, self).__getitem__(key[0])
            if type(t_obj) is np.void:
                return t_obj[key[1]]  # case single
            else:
                return super(tabarray,t_obj).__getitem__(self.dtype.names[key[1]]) # case slice
        else:
            return super(tabarray, self).__getitem__(key)

    def __setitem__(self, key, value):
        """
         Summary line.
        
         overloading the __setitem__ method from ndarray.
         This way array[:][array.dtype.names[0]] = ... becomes simply array[:,0] = ...
         For a one dimensional structured array array[:,0] would throw an error so no coflict is possible
    
        
         """
        if not isinstance(key, int) and len(key) == (self.ndim +1):
            if type(key[0]) is slice:
                if key[0].start is None:
                    start = 0
                else:
                    start = key[0].start
                
                if key[0].stop is None:
                    stop = len(self)
                else:
                    stop = key[0].stop
                
                if key[0].step is None:
                    step = 1
                else:
                    step = key[0].step
                    
                
                for d in range(start, stop, step):
                    super(tabarray, self).__getitem__(d).__setitem__(key[1],value[d-start])
                    
            else:
                super(tabarray, self).__getitem__(key[0]).__setitem__(key[1],value)
        else:
            super(tabarray, self).__setitem__(key,value)
        

