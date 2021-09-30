#!/usr/bin/env python
# (c) bugficks@samygo 2016
# GPL v2

import sys
import ctypes
from ctypes import c_uint32, c_byte, byref, pointer, cast
from teec import *
from Crypto.Cipher import AES
import hashlib
from binascii import hexlify, unhexlify

##############################################################################
#

CMD_SWU_INIT            = 0
CMD_SWU_UPDATE_AES      = 1
CMD_SWU_FINALIZE_AES    = 2
CMD_SWU_PASSPHRASE      = 3

##############################################################################
#

SWU_UUID = TEEC_UUID(
    0x22222221,
    0,
    0,
    (c_byte * 8)(0, 0, 0, 0, 0, 0, 0, 1)
)

##############################################################################
#

class SWUTrustZoneClient(object):
    ctx = TEEC_Context()
    shmIn = TEEC_SharedMemory()
    shmOut0 = TEEC_SharedMemory()
    shmOut1 = TEEC_SharedMemory()
    session = TEEC_Session()
    operation = TEEC_Operation()
    is_open = False
    is_init = False

    def __init__(self):
        pass

    def open(self):
        TEEC_InitializeContext(None, byref(self.ctx))

        self.shmIn.size = 0x10000
        self.shmIn.flags = 3
        TEEC_AllocateSharedMemory(byref(self.ctx), byref(self.shmIn))

        self.shmOut0.size = 0x10000
        self.shmOut0.flags = 3
        TEEC_AllocateSharedMemory(byref(self.ctx), byref(self.shmOut0))

        self.shmOut1.size = 0x10000
        self.shmOut1.flags = 3
        TEEC_AllocateSharedMemory(byref(self.ctx), byref(self.shmOut1))

        rc = c_uint32()
        TEEC_OpenSession(byref(self.ctx), byref(self.session), byref(SWU_UUID), TEEC_LOGIN_PUBLIC, None, None, byref(rc))
        self.is_open = True

    def close(self):
        if not self.is_open:
            return

        if self.session:
            TEEC_CloseSession(byref(self.session))

        TEEC_ReleaseSharedMemory(byref(self.shmIn))
        TEEC_ReleaseSharedMemory(byref(self.shmOut0))
        TEEC_ReleaseSharedMemory(byref(self.shmOut1))

        TEEC_FinalizeContext(byref(self.ctx))

        self.is_open = False

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def init(self, encrypt, passEncr, salt):
        key = itemsAESPassphraseEncrypted
        ctypes.memmove(self.shmIn.buffer, key, len(key))
        ctypes.memmove(self.shmOut1.buffer, salt, len(salt))

        #self.operation.paramTypes = 0x30F0F
        self.operation.paramTypes = TEEC_PARAM_TYPES(TEEC_MEMREF_PARTIAL_INOUT, TEEC_MEMREF_PARTIAL_INOUT, TEEC_VALUE_INOUT, TEEC_NONE)
        params = self.operation.params

        params[0].memref.parent = pointer(self.shmIn)
        params[0].memref.size = len(key)
        params[0].memref.offset = 0

        params[1].memref.parent = pointer(self.shmOut1)
        params[1].memref.size = len(salt)
        params[1].memref.offset = 0

        params[2].value.a = encrypt
        params[2].value.b = 1

        returnOrigin = c_uint32(0)
        ret = TEEC_InvokeCommand(byref(self.session), CMD_SWU_INIT, byref(self.operation), byref(returnOrigin))
        if ret:
            return None

        return cast(self.shmOut1.buffer, POINTER(c_byte))[:len(key)]

    def update(self, data):
        ctypes.memmove(self.shmIn.buffer, data, len(data))
        ctypes.memset(self.shmOut0.buffer, 0, self.shmOut0.size)

        self.operation.paramTypes = TEEC_PARAM_TYPES(TEEC_MEMREF_PARTIAL_INOUT, TEEC_MEMREF_PARTIAL_INOUT, TEEC_VALUE_INOUT, TEEC_NONE)
        params = self.operation.params

        params[0].memref.parent = pointer(self.shmIn)
        params[0].memref.size = len(data)
        params[0].memref.offset = 0

        params[1].memref.parent = pointer(self.shmOut0)
        params[1].memref.size = len(data)
        params[1].memref.offset = 0

        returnOrigin = c_uint32(0)
        ret = TEEC_InvokeCommand(byref(self.session), CMD_SWU_UPDATE_AES, byref(self.operation), byref(returnOrigin))
        if ret:
            return None

        size = params[2].value.a
        return ctypes.string_at(self.shmOut0.buffer, size)

    def finalize(self):
        #self.operation.paramTypes = 0x30F
        self.operation.paramTypes = TEEC_PARAM_TYPES(TEEC_MEMREF_PARTIAL_INOUT, TEEC_VALUE_INOUT, TEEC_NONE, TEEC_NONE)
        params = self.operation.params

        params[0].memref.parent = pointer(self.shmOut0)
        #*(_QWORD *)&v17.params[0].value.b = 0x10000LL
        params[0].memref.size = 0x10000
        params[0].memref.offset = 0

        returnOrigin = c_uint32(0)
        ret = TEEC_InvokeCommand(byref(self.session), CMD_SWU_FINALIZE_AES, byref(self.operation), byref(returnOrigin))
        if ret:
            return None

        size = params[1].value.a
        return ctypes.string_at(self.shmOut0.buffer, size)

    def generatePassphrase(self, encrypt, passEncr, salt):
        ctypes.memmove(self.shmIn.buffer, passEncr, len(passEncr))
        ctypes.memmove(self.shmOut0.buffer, salt, len(salt))

        self.operation.paramTypes = TEEC_PARAM_TYPES(TEEC_MEMREF_PARTIAL_INOUT, TEEC_MEMREF_PARTIAL_INOUT, TEEC_VALUE_INOUT, TEEC_NONE)
        params = self.operation.params

        params[0].memref.parent = pointer(self.shmIn)
        params[0].memref.size = len(passEncr)
        params[0].memref.offset = 0

        params[1].memref.parent = pointer(self.shmOut0)
        params[1].memref.size = len(salt)
        params[1].memref.offset = 0

        params[2].value.a = encrypt
        params[2].value.b = 0

        returnOrigin = c_uint32(0)
        ret = TEEC_InvokeCommand(byref(self.session), CMD_SWU_PASSPHRASE, byref(self.operation), byref(returnOrigin))
        if ret:
            return None

        return cast(self.shmOut0.buffer, POINTER(c_char))[:len(passEncr)]

    @property
    def itemsAESPassphraseEncrypted(self):
        return open("/usr/share/org.tizen.tv.swu/itemsAESPassphraseEncrypted.txt", "rb").read()

    @property
    def itemsPublicRSAKey(self):
        return open("/usr/share/org.tizen.tv.swu/itemsPublicRSAKey.txt", "rb").read()

    @property
    def OpenAPIAESPassphraseEncrypted(self):
        return open("/usr/share/org.tizen.tv.swu/OpenAPIAESPassphraseEncrypted.txt", "rb").read()


class SWUAESClient(object):
    def open(self):
        pass

    def close(self):
        pass

    def init(self, encrypt, key, salt):
        key = unhexlify(key)
        iv = hashlib.md5(salt).digest()
        aes128cbc = AES.new(key, AES.MODE_CBC, iv)
        if encrypt:
            self.do_aes = aes128cbc.encrypt
        else:
            self.do_aes = aes128cbc.decrypt

    def update(self, data):
        return self.do_aes(data)

    def finalize(self):
        return ""

class SWUClient(object):
    def __init__(self, use_sw=True):
        self.use_sw = use_sw

    def __enter__(self):
        if not self.use_sw or hwsupport():
            client = SWUTrustZoneClient()
        else:
            client = SWUAESClient()
        client.open()
        self.client = client
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.client.close()
        self.client = None

    def init(self, encrypt, passEncr, salt):
        return self.client.init(encrypt, passEncr, salt)

    def update(self, data):
        return self.client.update(data)

    def finalize(self):
         return self.client.finalize()
