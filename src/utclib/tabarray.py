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
        

