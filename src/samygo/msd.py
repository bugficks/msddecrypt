#!/usr/bin/env python
# (c) bugficks@samygo 2016
# GPL v2

import sys
import ctypes
from ctypes import * #c_uint32, byref, pointer, cast

###############################################################################
#
class MSDU10_PARTITION(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("id", c_uint32),
        ("offs", c_uint32),
        ("size", c_uint32),
    ]

class MSDU10_STRING(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("len", c_uint8),
        #("s", c_char * 0),
    ]
    s = str()

class MSDU10_OUITDATA(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("offs", c_uint32),
        ("size", c_uint32),
        ("label_len", c_uint8),
        #("label", MSDU10_STRING),
    ]
    label = str()

class MSDU10_OUITHDR(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("zero", c_uint32),
        ("nitems", c_uint32),
        #("items",MSDU10_OUITDATA),
    ]
    items = []

class MSDU10_HDR(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("magic", c_char * 6),
        ("nitems", c_uint32),
        #("items", MSDU10_PARTITION * 0),
    ]
    parts = []

###############################################################################
#
class MSDU11_PARTITION(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("id", c_uint32),
        ("offs", c_uint64),
        ("size", c_uint64),
    ]

class MSDU11_STRING(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("len", c_uint8),
        #("s", c_char * 0),
    ]
    s = str()

class MSDU11_OUITDATA(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("offs", c_uint64),
        ("size", c_uint32),
        ("label_len", c_uint8),
        #("label", MSDU11_STRING),
    ]
    label = str()

class MSDU11_OUITHDR(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("nitems", c_uint32),
        #("items",MSDU11_OUITDATA),
    ]
    items = []

class MSDU11_HDR(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("magic", c_char * 6),
        ("unk0", c_uint32),
        ("unk1", c_uint32),
        ("unk2", c_uint32),
        ("nitems", c_uint32),
        #("items", MSDU11_PARTITION * 0),
    ]
    parts = []

###############################################################################
#
class MSDFileException(Exception):
    pass

class MSDFile(object):
    _f = None

    def __init__(self, path):
        self._f = open(path, 'rb')
        self.path = path
        magic = self._f.read(6)
        if magic == "MSDU10":
            MSDU_PARTITION = MSDU10_PARTITION
            MSDU_STRING    = MSDU10_STRING
            MSDU_OUITDATA  = MSDU10_OUITDATA
            MSDU_OUITHDR   = MSDU10_OUITHDR
            MSDU_HDR       = MSDU10_HDR
        elif magic == "MSDU11":
            MSDU_PARTITION = MSDU11_PARTITION
            MSDU_STRING    = MSDU11_STRING
            MSDU_OUITDATA  = MSDU11_OUITDATA
            MSDU_OUITHDR   = MSDU11_OUITHDR
            MSDU_HDR       = MSDU11_HDR
        else:
            raise MSDFileException('Invalid Magic')

        self._f.seek(0)
        msdHdr = MSDU_HDR()
        self._f.readinto(msdHdr)

        for x in range(0, msdHdr.nitems):
            part = MSDU_PARTITION()
            self._f.readinto(part)
            msdHdr.parts.append(part)
        self.msdHdr = msdHdr

        msdOUITHdr = MSDU_OUITHDR()
        self._f.readinto(msdOUITHdr)
        for x in range(0, msdOUITHdr.nitems):
            data = MSDU_OUITDATA()
            self._f.readinto(data)

            data.label = self._f.read(data.label_len)
            msdOUITHdr.items.append(data)

        self.msdOUITHdr = msdOUITHdr

    def magic(self):
        return self.msdHdr.magic

    def parts(self):
        return self.msdHdr.parts

    def headers(self):
        return self.msdOUITHdr.items

    def seek(self, offs):
        return self._f.seek(offs)

    def read(self, size):
        return self._f.read(size)

    def readfrom(self, offs, size):
        self._f.seek(offs)
        return self._f.read(size)


    def file_extract(self, offs, size, dest):
        self._f.seek(offs)
        with open(dest, 'wb') as o:
            l = abs(size)
            while l > 0:
                r = min(l, 1024 * 16)
                d = self._f.read(l)
                o.write(d)
                l -= len(d)
