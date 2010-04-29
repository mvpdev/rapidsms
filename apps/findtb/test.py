#!/usr/bin/env python
# -*- coding= UTF-8 -*-


import unittest

def my_func(a_list, idx):
    """
    >>> a = ['larry', 'curly', 'moe']
    >>> my_func(a, 0)
    'larry'
    >>> my_func(a, 1)
    'curly'
    """
    return a_list[idx]


class MyFuncTestCase(unittest.TestCase):
    def testBasic(self):
        a = ['larry', 'curly', 'moe']
        self.assertEquals(my_func(a, 0), 'larry')
        self.assertEquals(my_func(a, 1), 'curly')

