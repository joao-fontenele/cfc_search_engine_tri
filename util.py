#!/usr/bin/env python
#coding: utf-8

from collections import namedtuple

# an object to hold documents relevant info
Document = namedtuple("Document", ["id", "year", "title", "authors", "norm"])
Query = namedtuple("Query", ["id", "queryString", "relevants"])

if __name__ == '__main__':
    pass

