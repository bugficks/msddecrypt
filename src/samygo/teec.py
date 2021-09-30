#!/usr/bin/env python
# (c) bugficks@samygo 2016
# GPL v2

import ctypes
from ctypes import c_char, c_byte, c_ushort, c_int32, c_uint32, c_char_p, c_void_p
from ctypes import POINTER, CFUNCTYPE, CDLL, RTLD_GLOBAL

##############################################################################
#
# libteec depends on libdlog
try:
    _dlog = CDLL('libdlog.so', RTLD_GLOBAL)
    _libteec = CDLL('libteec.so')
except:
    _libteec = None

##############################################################################
#

TEEC_CONFIG_SHAREDMEM_MAX_SIZE = 0x800000

TEEC_MEM_INPUT              = (1 << 0)
TEEC_MEM_OUTPUT             = (1 << 1)

TEEC_NONE                   = 0x00000000
TEEC_VALUE_INPUT            = 0x00000001
TEEC_VALUE_OUTPUT           = 0x00000002
TEEC_VALUE_INOUT            = 0x00000003
TEEC_MEMREF_TEMP_INPUT      = 0x00000005
TEEC_MEMREF_TEMP_OUTPUT     = 0x00000006
TEEC_MEMREF_TEMP_INOUT      = 0x00000007
TEEC_MEMREF_WHOLE           = 0x0000000C
TEEC_MEMREF_PARTIAL_INPUT   = 0x0000000D
TEEC_MEMREF_PARTIAL_OUTPUT  = 0x0000000E
TEEC_MEMREF_PARTIAL_INOUT   = 0x0000000F

TEE_PARAM_TYPE_NONE         = 0x00000000
TEE_PARAM_TYPE_VALUE_INPUT  = 0x00000001
TEE_PARAM_TYPE_VALUE_OUTPUT = 0x00000002
TEE_PARAM_TYPE_VALUE_INOUT  = 0x00000003
TEE_PARAM_TYPE_MEMREF_INPUT = 0x00000005
TEE_PARAM_TYPE_MEMREF_OUTPUT= 0x00000006
TEE_PARAM_TYPE_MEMREF_INOUT = 0x00000007

TEEC_SHMEM_IMP_NONE         = 0x00000000
TEEC_SHMEM_IMP_ALLOCED      = 0x00000001

#open session
TEEC_LOGIN_PUBLIC           = 0x00000000
TEEC_LOGIN_USER             = 0x00000001
TEEC_LOGIN_GROUP            = 0x00000002
TEEC_LOGIN_APPLICATION      = 0x00000004
TEEC_LOGIN_USER_APPLICATION = 0x00000005
TEEC_LOGIN_GROUP_APPLICATION= 0x00000006
TEEC_LOGIN_IMP_MIN          = 0x80000000
TEEC_LOGIN_IMP_MAX          = 0xFFFFFFFF

##############################################################################
#
TEEC_Result = c_uint32

class TEEC_UUID(ctypes.LittleEndianStructure):
    _pack_ = 4
    _fields_ = [
        ("timeLow", c_uint32),
        ("timeMid", c_ushort),
        ("timeHiAndVersion", c_ushort),
        ("clockSeqAndNode", c_byte * 8),
    ]

class TEEC_Context(ctypes.LittleEndianStructure):
    _pack_ = 4
    _fields_ = [
        ("imp", c_void_p),
    ]

class TEEC_Session(ctypes.LittleEndianStructure):
    _pack_ = 4
    _fields_ = [
        ("imp", c_void_p),
    ]

class TEEC_SharedMemoryImp(ctypes.LittleEndianStructure):
    _pack_ = 4
    _fields_ = [
        ("le_next", POINTER('TEEC_SharedMemoryImp')),
        ("le_prev", POINTER(POINTER('TEEC_SharedMemoryImp'))),
        ("context", POINTER(TEEC_Context)),
        ("context_imp", c_void_p),
        ("flags", c_uint32),
        ("memid", c_int32),
    ]

class TEEC_SharedMemory(ctypes.LittleEndianStructure):
    _pack_ = 4
    _fields_ = [
        ("buffer", c_void_p),
        ("size", c_uint32),
        ("flags", c_uint32),
        ("imp", TEEC_SharedMemoryImp),
    ]

class TEEC_TempMemoryReference(ctypes.LittleEndianStructure):
    _pack_ = 4
    _fields_ = [
        ("buffer", c_void_p),
        ("size", c_uint32),
    ]

class TEEC_RegisteredMemoryReference(ctypes.LittleEndianStructure):
    _pack_ = 4
    _fields_ = [
        ("parent", POINTER(TEEC_SharedMemory)),
        ("size", c_uint32),
        ("offset", c_uint32),
    ]

class TEEC_Value(ctypes.LittleEndianStructure):
    _pack_ = 4
    _fields_ = [
        ("a", c_uint32),
        ("b", c_uint32),
    ]

class TEEC_Parameter(ctypes.Union):
    _pack_ = 4
    _fields_ = [
        ("tmpref", TEEC_TempMemoryReference),
        ("memref", TEEC_RegisteredMemoryReference),
        ("value", TEEC_Value),
    ]

class TEEC_Operation(ctypes.LittleEndianStructure):
    _pack_ = 4
    _fields_ = [
        ("started", c_uint32),
        ("paramTypes", c_uint32),
        ("params", TEEC_Parameter * 4),
        ("imp", c_void_p),
    ]

##############################################################################
#
def TEEC_PARAM_TYPES(param0Type, param1Type, param2Type, param3Type):
    return c_uint32(
        (param0Type  & 0x7F) |
        ((param1Type & 0x7F) << 8 ) |
        ((param2Type & 0x7F) << 16) |
        ((param3Type & 0x7F) << 24)
    ).value


def hwsupport():
    return _libteec != None

if _libteec:
    ##############################################################################
    #
    # TEEC_Result TEEC_InitializeContext(const char *name, TEEC_Context *context);
    TEEC_InitializeContext = _libteec.TEEC_InitializeContext
    TEEC_InitializeContext.restype = TEEC_Result
    TEEC_InitializeContext.argtypes = [c_char_p, POINTER(TEEC_Context)]

    # void TEEC_FinalizeContext(TEEC_Context *context);
    TEEC_FinalizeContext = _libteec.TEEC_FinalizeContext
    TEEC_FinalizeContext.restype = None
    TEEC_FinalizeContext.argtypes = [POINTER(TEEC_Context)]

    ##############################################################################
    #
    # TEEC_Result TEEC_RegisterSharedMemory(TEEC_Context *context, TEEC_SharedMemory *sharedMem);
    TEEC_RegisterSharedMemory = _libteec.TEEC_RegisterSharedMemory
    TEEC_RegisterSharedMemory.restype = TEEC_Result
    TEEC_RegisterSharedMemory.argtypes = [POINTER(TEEC_Context), POINTER(TEEC_SharedMemory)]

    # TEEC_Result TEEC_AllocateSharedMemory(TEEC_Context *context, TEEC_SharedMemory *sharedMem);
    TEEC_AllocateSharedMemory = _libteec.TEEC_AllocateSharedMemory
    TEEC_AllocateSharedMemory.restype = TEEC_Result
    TEEC_AllocateSharedMemory.argtypes = [POINTER(TEEC_Context), POINTER(TEEC_SharedMemory)]

    # void TEEC_ReleaseSharedMemory(TEEC_SharedMemory *sharedMem);
    TEEC_ReleaseSharedMemory = _libteec.TEEC_ReleaseSharedMemory
    TEEC_ReleaseSharedMemory.restype = None
    TEEC_ReleaseSharedMemory.argtypes = [POINTER(TEEC_SharedMemory)]

    ##############################################################################
    #
    # TEEC_Result TEEC_OpenSession(TEEC_Context *context, TEEC_Session *session, const TEEC_UUID *destination, uint32_t connectionMethod, const void *connectionData, TEEC_Operation *operation, uint32_t *returnOrigin);
    TEEC_OpenSession = _libteec.TEEC_OpenSession
    TEEC_OpenSession.restype = TEEC_Result
    TEEC_OpenSession.argtypes = [POINTER(TEEC_Context), POINTER(TEEC_Session), POINTER(TEEC_UUID), c_uint32, c_void_p, POINTER(TEEC_Operation), POINTER(c_uint32)]

    # void TEEC_CloseSession(TEEC_Session *session);
    TEEC_CloseSession = _libteec.TEEC_CloseSession
    TEEC_CloseSession.restype = None
    TEEC_CloseSession.argtypes = [POINTER(TEEC_Session)]

    ##############################################################################
    #
    # TEEC_Result TEEC_InvokeCommand(TEEC_Session *session, uint32_t commandID, TEEC_Operation *operation, uint32_t *returnOrigin);
    TEEC_InvokeCommand = _libteec.TEEC_InvokeCommand
    TEEC_InvokeCommand.restype = TEEC_Result
    TEEC_InvokeCommand.argtypes = [POINTER(TEEC_Session), c_uint32, POINTER(TEEC_Operation), POINTER(c_uint32)]

    # void TEEC_RequestCancellation(TEEC_Operation *operation);
    TEEC_RequestCancellation = _libteec.TEEC_RequestCancellation
    TEEC_RequestCancellation.restype = None
    TEEC_RequestCancellation.argtypes = [POINTER(TEEC_Operation)]
