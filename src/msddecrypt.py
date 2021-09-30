#!/usr/bin/env python
# (c) bugficks@samygo 2016
# GPL

import sys
import os
from os import path
from ctypes import *
import fnmatch
import tempfile
import shutil
import binascii
from binascii import hexlify, unhexlify
import datetime

import samygo
from samygo import swu
from samygo.msd import MSDFile

########################################################################################################################

TIZEN_OUIT_HDR_MAGIC18 = "Tizen Software Upgrade Tree Binary Format ver. 1.8"
TIZEN_OUIT_HDR_MAGIC19 = "Tizen Software Upgrade Tree Binary Format ver. 1.9"

MAGIC_SALTED = 'Salted__'
SIZE_SALT = 8

#TIZEN_OUIT_SIGN_SIZE = 0x100

SWU_KEYS = {
    "T-HKM":    "1ac8989ff57db5e75ea67b033050871c",
    "T-HKP":    "cce8a3ef92f3e94895999e928f4dd6c3",
    "T-JZM":    "9b1d077c0d137d406c79ddacb6b159fe",
    "T-HKMFK":  "c7097975e8ab994beb5eaae57e0ba77c",
    "T-KTM":    "d0d49d5f36f5c0da50062fbf32168f5b",
    "T-KTSU":   "19e1ba41163f03735e692d9daa2cbb47",
    "T-KTSD":   "39332605ff47a0aea999b10ce9087389",
    "T-KTM2":   "29110e0ce940b3a9b67d3e158f3f1342",
    "T-KTM2L":  "46b04f5e794ca4377a20951c9ea00427",
}

if 'SWU_KEYS' in os.environ:
    import json
    swuKeys = json.loads(os.environ.get('SWU_KEYS'))
    SWU_KEYS.update(swuKeys)

########################################################################################################################

class OUITHeaderException(Exception):
    pass

def MSDDecrypt(f, dirOut, extractNames):

    print "magic:", f.magic()
    print 'headers [%d]' % len(f.headers())
    for hdr in f.headers():
        l = hdr.label
        l += ' ' * (12-len(l))
        print "%s: offs: %08x size: %08x" % (l, hdr.offs, hdr.size)
    print ''

    dataOffs = None
    hdrDecr = None
    for key in SWU_KEYS.values():
        if dataOffs >= 0:
            break

        for hdr in f.headers():
            hdrEncr = f.readfrom(hdr.offs, hdr.size)
            delta = hdrEncr.find(MAGIC_SALTED)
            if delta < 0:
                raise OUITHeaderException(MAGIC_SALTED)

            saltStart = len(MAGIC_SALTED) + delta
            salt = hdrEncr[saltStart : saltStart + SIZE_SALT]
            hdrEncr = hdrEncr[saltStart + len(salt) :]

            with swu.SWUClient() as SWUClient:
                SWUClient.init(0, key, salt)
                hdrDecr = SWUClient.update(hdrEncr) + SWUClient.finalize()

            dataOffs = hdrDecr.find(TIZEN_OUIT_HDR_MAGIC18)
            if dataOffs < 0:
                dataOffs = hdrDecr.find(TIZEN_OUIT_HDR_MAGIC19)

            if dataOffs >= 0:
                print 'Found valid header magic'
                print "%s %s 0x%08x" % (hdr.label, key, dataOffs)
                break

    if False:
        #passDecr = SWUClient.generatePassphrase(0, SWUClient.itemsAESPassphraseEncrypted, salt)
        open('/opt/out/_hdr.decr', 'wb').write(hdrDecr)
        open('/opt/out/_hdr.encr', 'wb').write(hdrEncr)
        open('/opt/out/_hdr.salt', 'wb').write(salt)
        #open('_aes.key', 'wb').write(passDecr.strip())
        sys.exit(1)

    is18 = True
    dataOffs = hdrDecr.find(TIZEN_OUIT_HDR_MAGIC18)
    if dataOffs < 0:
        dataOffs = hdrDecr.find(TIZEN_OUIT_HDR_MAGIC19)
        is18 = False
    if dataOffs < 0:
        raise OUITHeaderException('Invalid header magic')

    hdrDecr = hdrDecr[dataOffs:]

    def getPartNamesHack(hdrDecr):
        if is18:
            sss = unhexlify("0000000A01")
        else:
            sss = unhexlify("00000A00000001")
        partnames = []
        start = 0
        while True:
            start = hdrDecr.find(sss, start)
            if start <= 0:
                break
            start += len(sss)
            l = ord(hdrDecr[start])
            partname = hdrDecr[start+1 : start+1+l]
            partnames.append(partname)
            start += len(partname)
        return partnames

    def getPartSaltsHack(hdrDecr):
        if is18:
            sss = unhexlify("01000000160000000E010000000108")
        else:
            sss = unhexlify("01160000000E0000000108")
        salts = []
        start = 0
        while True:
            start = hdrDecr.find(sss, start)
            if start <= 0:
                break
            start += len(sss)
            salt = hdrDecr[start:start+8]
            salts.append(salt)
            start += 8
        return salts

    def getPartCRC32sHack(hdrDecr):
        import struct

        if is18:
            sss = unhexlify("00000007010300000001000000090000001201")
        else:
            sss = unhexlify("01000007000000010300000001090000001200000001")

        crc32s = []
        start = 0
        while True:
            start = hdrDecr.find(sss, start)
            if start <= 0:
                break
            start += len(sss)
            crc32 = hdrDecr[start:start+4]
            if is18:
                crc32 = struct.unpack(">L", crc32)[0]
            else:
                crc32 = struct.unpack("<L", crc32)[0]
            #crc32 = int(hexlify(crc32), 16) & 0xFFFFFFFF
            crc32s.append(crc32)
            start += 4
        return crc32s

    def getOUSWImageVersionDescHack():
        import struct

        if is18:
            sss = unhexlify("000000170000001901")
        else:
            sss = unhexlify("0000001900000001")

        start = hdrDecr.find(sss)
        if start <= 0:
            return None
        start += len(sss)
        l = ord(hdrDecr[start])
        platname = hdrDecr[start+1 : start+1+l]
        start += len(platname)+1

        if is18:
            major, minor = struct.unpack(">HH", hdrDecr[start:start+4])
        else:
            major, minor = struct.unpack("<HH", hdrDecr[start:start+4])
        start += 4

        date = ""
        if is18:
            yyyy, mm, dd = struct.unpack(">HBB", hdrDecr[start:start+4])
            date = datetime.date(yyyy, mm, dd)

        return platname, (major, minor), date

    platname, ver, date = getOUSWImageVersionDescHack()
    print "image ver: %s %d.%d %s" % (platname, ver[0], ver[1], date)
    print ""

    parts = f.parts()
    salts = getPartSaltsHack(hdrDecr)
    partnames = getPartNamesHack(hdrDecr)
    crc32s = getPartCRC32sHack(hdrDecr)
    print 'partitions [%d]' % len(f.parts())
    for x in range(0, len(salts)):
        partname = partnames[x]
        print "id: %d name: %s salt: %s offs: %08x size: %08x crc32: %08x" % (x+1, partname.ljust(13), hexlify(salts[x]), parts[x].offs, parts[x].size, crc32s[x])

        doExtract = False
        if dirOut:
            doExtract = True
            if len(extractNames) and partname not in extractNames:
                doExtract = False

        if doExtract:
            outn = path.join(dirOut, '%s' % partname)
            outf = open(outn, 'wb')
            part = parts[x]
            salt = salts[x]

            f.seek(part.offs)
            with swu.SWUClient() as SWUClient:
                SWUClient.init(0, key, salt)

                nsize = part.size

                while True:
                    progress = ((part.size - nsize) * 100) / part.size
                    sys.stdout.write("\r* Decrypting '%s' %3d%% [%10d of %d]" % (outn, progress, part.size - nsize, part.size))
                    sys.stdout.flush()

                    toread = min(nsize, 0x10000)
                    if toread == 0:
                        break
                    encr = f.read(toread)
                    if len(encr) != toread:
                        break

                    nsize -= len(encr)

                    decr = SWUClient.update(encr)
                    outf.write(decr)

                padLen = decr[-1:]
                decr = SWUClient.finalize()
                if len(decr):
                    outf.write(decr)
                    padLen = decr[-1:]

                destSize = part.size - ord(padLen)
                outf.truncate(destSize)

            print("\r* Decrypting '%s' 100%% [%10d of %d]" % (outn, part.size, part.size))

            outf.close()
            outf = open(outn, 'rb')
            crc = 0
            nsize = 0
            while True:
                data = outf.read(0x10000)
                if len(data) == 0:
                    break
                crc = binascii.crc32(data, crc) & 0xFFFFFFFF
                nsize += len(data)

                progress = (nsize * 100) / destSize
                sys.stdout.write("\r* CRC32ing   '%s' %3d%%" % (outn, progress))
                sys.stdout.flush()

            print('')
            if crc != crc32s[x]:
                print "- CRC32 mismatch! [msd: %08x file: %08x]" % (crc, crc32s[x])
            else:
                print "+ CRC32 passed!"

if __name__ == "__main__":
    print "Tizen msd Decryptor v0.4.1"
    print "(c) bugficks@samygo 2016-2021"
    print ""

    argc = len(sys.argv)
    if argc < 2:
        print "Usage: msddecrypt.py </path/to/upgrade.msd> [/path/to/outdir [partition names]]"
        print ""
        sys.exit(0)

    pathMSD = sys.argv[1]
    dirOut = None
    extractNames = []

    if argc > 2:
        dirOut = sys.argv[2]
        extractNames =  sys.argv[3:]

    if dirOut:
        if not os.path.exists(dirOut):
            os.makedirs(dirOut)
        elif os.path.isfile(dirOut):
            raise ValueError("Invalid output directory: '%s'" % dirOut)

    f = MSDFile(pathMSD)
    MSDDecrypt(f, dirOut, extractNames)
