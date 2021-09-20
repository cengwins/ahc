# COMPLEX is not supported so changed the header a bit
#clang2py -v --clang-args="-I/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/include -I/Library/Developer/CommandLineTools/usr/include -std=c99" liquid-mod.h -o liquid.py


# -*- coding: utf-8 -*-
#
# TARGET arch is: ['-I/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/include', '-I/Library/Developer/CommandLineTools/usr/include', '-std=c99']
# WORD_SIZE is: 8
# POINTER_SIZE is: 8
# LONGDOUBLE_SIZE is: 16
#
import ctypes
import platform


class FunctionFactoryStub:
    def __getattr__(self, _):
        return ctypes.CFUNCTYPE(lambda y:y)

# libraries['FIXME_STUB'] explanation
# As you did not list (-l libraryname.so) a library that exports this function
# This is a non-working stub instead. 
# You can either re-run clan2py with -l /path/to/library.so
# Or manually fix this by comment the ctypes.CDLL loading
_libraries = {}
#liquiddsp = FunctionFactoryStub() #  ctypes.CDLL('FIXME_STUB')
myplatform = platform.system()
if myplatform == "Darwin":
    liquiddsp = ctypes.CDLL("/usr/local/lib/libliquid.dylib")

if myplatform == "Linux":
    liquiddsp = ctypes.CDLL("/usr/local/lib/libliquid.so")


def string_cast(char_pointer, encoding='utf-8', errors='strict'):
    value = ctypes.cast(char_pointer, ctypes.c_char_p).value
    if value is not None and encoding is not None:
        value = value.decode(encoding, errors=errors)
    return value


def char_pointer_cast(string, encoding='utf-8'):
    if encoding is not None:
        try:
            string = string.encode(encoding)
        except AttributeError:
            # In Python3, bytes has no encode attribute
            pass
    string = ctypes.c_char_p(string)
    return ctypes.cast(string, ctypes.POINTER(ctypes.c_char))



class AsDictMixin:
    @classmethod
    def as_dict(cls, self):
        result = {}
        if not isinstance(self, AsDictMixin):
            # not a structure, assume it's already a python object
            return self
        if not hasattr(cls, "_fields_"):
            return result
        # sys.version_info >= (3, 5)
        # for (field, *_) in cls._fields_:  # noqa
        for field_tuple in cls._fields_:  # noqa
            field = field_tuple[0]
            if field.startswith('PADDING_'):
                continue
            value = getattr(self, field)
            type_ = type(value)
            if hasattr(value, "_length_") and hasattr(value, "_type_"):
                # array
                if not hasattr(type_, "as_dict"):
                    value = [v for v in value]
                else:
                    type_ = type_._type_
                    value = [type_.as_dict(v) for v in value]
            elif hasattr(value, "contents") and hasattr(value, "_type_"):
                # pointer
                try:
                    if not hasattr(type_, "as_dict"):
                        value = value.contents
                    else:
                        type_ = type_._type_
                        value = type_.as_dict(value.contents)
                except ValueError:
                    # nullptr
                    value = None
            elif isinstance(value, AsDictMixin):
                # other structure
                value = type_.as_dict(value)
            result[field] = value
        return result


class Structure(ctypes.Structure, AsDictMixin):

    def __init__(self, *args, **kwds):
        # We don't want to use positional arguments fill PADDING_* fields

        args = dict(zip(self.__class__._field_names_(), args))
        args.update(kwds)
        super(Structure, self).__init__(**args)

    @classmethod
    def _field_names_(cls):
        if hasattr(cls, '_fields_'):
            return (f[0] for f in cls._fields_ if not f[0].startswith('PADDING'))
        else:
            return ()

    @classmethod
    def get_type(cls, field):
        for f in cls._fields_:
            if f[0] == field:
                return f[1]
        return None

    @classmethod
    def bind(cls, bound_fields):
        fields = {}
        for name, type_ in cls._fields_:
            if hasattr(type_, "restype"):
                if name in bound_fields:
                    if bound_fields[name] is None:
                        fields[name] = type_()
                    else:
                        # use a closure to capture the callback from the loop scope
                        fields[name] = (
                            type_((lambda callback: lambda *args: callback(*args))(
                                bound_fields[name]))
                        )
                    del bound_fields[name]
                else:
                    # default callback implementation (does nothing)
                    try:
                        default_ = type_(0).restype().value
                    except TypeError:
                        default_ = None
                    fields[name] = type_((
                        lambda default_: lambda *args: default_)(default_))
            else:
                # not a callback function, use default initialization
                if name in bound_fields:
                    fields[name] = bound_fields[name]
                    del bound_fields[name]
                else:
                    fields[name] = type_()
        if len(bound_fields) != 0:
            raise ValueError(
                "Cannot bind the following unknown callback(s) {}.{}".format(
                    cls.__name__, bound_fields.keys()
            ))
        return cls(**fields)


class Union(ctypes.Union, AsDictMixin):
    pass



c_int128 = ctypes.c_ubyte*16
c_uint128 = c_int128
void = None
if ctypes.sizeof(ctypes.c_longdouble) == 16:
    c_long_double_t = ctypes.c_longdouble
else:
    c_long_double_t = ctypes.c_ubyte*16



liquid_version = [] # Variable ctypes.c_char * 0
liquid_libversion = liquiddsp.liquid_libversion
liquid_libversion.restype = ctypes.POINTER(ctypes.c_char)
liquid_libversion.argtypes = []
liquid_libversion_number = liquiddsp.liquid_libversion_number
liquid_libversion_number.restype = ctypes.c_int32
liquid_libversion_number.argtypes = []

# values for enumeration 'c__EA_liquid_error_code'
c__EA_liquid_error_code__enumvalues = {
    0: 'LIQUID_OK',
    1: 'LIQUID_EINT',
    2: 'LIQUID_EIOBJ',
    3: 'LIQUID_EICONFIG',
    4: 'LIQUID_EIVAL',
    5: 'LIQUID_EIRANGE',
    6: 'LIQUID_EIMODE',
    7: 'LIQUID_EUMODE',
    8: 'LIQUID_ENOINIT',
    9: 'LIQUID_EIMEM',
    10: 'LIQUID_EIO',
}
LIQUID_OK = 0
LIQUID_EINT = 1
LIQUID_EIOBJ = 2
LIQUID_EICONFIG = 3
LIQUID_EIVAL = 4
LIQUID_EIRANGE = 5
LIQUID_EIMODE = 6
LIQUID_EUMODE = 7
LIQUID_ENOINIT = 8
LIQUID_EIMEM = 9
LIQUID_EIO = 10
c__EA_liquid_error_code = ctypes.c_uint32 # enum
liquid_error_code = c__EA_liquid_error_code
liquid_error_code__enumvalues = c__EA_liquid_error_code__enumvalues
liquid_error_str = [] # Variable ctypes.POINTER(ctypes.c_char) * 12
liquid_error_info = liquiddsp.liquid_error_info
liquid_error_info.restype = ctypes.POINTER(ctypes.c_char)
liquid_error_info.argtypes = [liquid_error_code]
class struct_c__SA_liquid_float_complex(Structure):
    pass

struct_c__SA_liquid_float_complex._pack_ = 1 # source:False
struct_c__SA_liquid_float_complex._fields_ = [
    ('real', ctypes.c_float),
    ('imag', ctypes.c_float),
]

liquid_float_complex = struct_c__SA_liquid_float_complex
class struct_c__SA_liquid_double_complex(Structure):
    pass

struct_c__SA_liquid_double_complex._pack_ = 1 # source:False
struct_c__SA_liquid_double_complex._fields_ = [
    ('real', ctypes.c_double),
    ('imag', ctypes.c_double),
]

liquid_double_complex = struct_c__SA_liquid_double_complex

# values for enumeration 'c__EA_agc_squelch_mode'
c__EA_agc_squelch_mode__enumvalues = {
    0: 'LIQUID_AGC_SQUELCH_UNKNOWN',
    1: 'LIQUID_AGC_SQUELCH_ENABLED',
    2: 'LIQUID_AGC_SQUELCH_RISE',
    3: 'LIQUID_AGC_SQUELCH_SIGNALHI',
    4: 'LIQUID_AGC_SQUELCH_FALL',
    5: 'LIQUID_AGC_SQUELCH_SIGNALLO',
    6: 'LIQUID_AGC_SQUELCH_TIMEOUT',
    7: 'LIQUID_AGC_SQUELCH_DISABLED',
}
LIQUID_AGC_SQUELCH_UNKNOWN = 0
LIQUID_AGC_SQUELCH_ENABLED = 1
LIQUID_AGC_SQUELCH_RISE = 2
LIQUID_AGC_SQUELCH_SIGNALHI = 3
LIQUID_AGC_SQUELCH_FALL = 4
LIQUID_AGC_SQUELCH_SIGNALLO = 5
LIQUID_AGC_SQUELCH_TIMEOUT = 6
LIQUID_AGC_SQUELCH_DISABLED = 7
c__EA_agc_squelch_mode = ctypes.c_uint32 # enum
agc_squelch_mode = c__EA_agc_squelch_mode
agc_squelch_mode__enumvalues = c__EA_agc_squelch_mode__enumvalues
class struct_agc_crcf_s(Structure):
    pass

agc_crcf = ctypes.POINTER(struct_agc_crcf_s)
agc_crcf_create = liquiddsp.agc_crcf_create
agc_crcf_create.restype = agc_crcf
agc_crcf_create.argtypes = []
agc_crcf_destroy = liquiddsp.agc_crcf_destroy
agc_crcf_destroy.restype = ctypes.c_int32
agc_crcf_destroy.argtypes = [agc_crcf]
agc_crcf_print = liquiddsp.agc_crcf_print
agc_crcf_print.restype = ctypes.c_int32
agc_crcf_print.argtypes = [agc_crcf]
agc_crcf_reset = liquiddsp.agc_crcf_reset
agc_crcf_reset.restype = ctypes.c_int32
agc_crcf_reset.argtypes = [agc_crcf]
agc_crcf_execute = liquiddsp.agc_crcf_execute
agc_crcf_execute.restype = ctypes.c_int32
agc_crcf_execute.argtypes = [agc_crcf, liquid_float_complex, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
agc_crcf_execute_block = liquiddsp.agc_crcf_execute_block
agc_crcf_execute_block.restype = ctypes.c_int32
agc_crcf_execute_block.argtypes = [agc_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
agc_crcf_lock = liquiddsp.agc_crcf_lock
agc_crcf_lock.restype = ctypes.c_int32
agc_crcf_lock.argtypes = [agc_crcf]
agc_crcf_unlock = liquiddsp.agc_crcf_unlock
agc_crcf_unlock.restype = ctypes.c_int32
agc_crcf_unlock.argtypes = [agc_crcf]
agc_crcf_set_bandwidth = liquiddsp.agc_crcf_set_bandwidth
agc_crcf_set_bandwidth.restype = ctypes.c_int32
agc_crcf_set_bandwidth.argtypes = [agc_crcf, ctypes.c_float]
agc_crcf_get_bandwidth = liquiddsp.agc_crcf_get_bandwidth
agc_crcf_get_bandwidth.restype = ctypes.c_float
agc_crcf_get_bandwidth.argtypes = [agc_crcf]
agc_crcf_get_signal_level = liquiddsp.agc_crcf_get_signal_level
agc_crcf_get_signal_level.restype = ctypes.c_float
agc_crcf_get_signal_level.argtypes = [agc_crcf]
agc_crcf_set_signal_level = liquiddsp.agc_crcf_set_signal_level
agc_crcf_set_signal_level.restype = ctypes.c_int32
agc_crcf_set_signal_level.argtypes = [agc_crcf, ctypes.c_float]
agc_crcf_get_rssi = liquiddsp.agc_crcf_get_rssi
agc_crcf_get_rssi.restype = ctypes.c_float
agc_crcf_get_rssi.argtypes = [agc_crcf]
agc_crcf_set_rssi = liquiddsp.agc_crcf_set_rssi
agc_crcf_set_rssi.restype = ctypes.c_int32
agc_crcf_set_rssi.argtypes = [agc_crcf, ctypes.c_float]
agc_crcf_get_gain = liquiddsp.agc_crcf_get_gain
agc_crcf_get_gain.restype = ctypes.c_float
agc_crcf_get_gain.argtypes = [agc_crcf]
agc_crcf_set_gain = liquiddsp.agc_crcf_set_gain
agc_crcf_set_gain.restype = ctypes.c_int32
agc_crcf_set_gain.argtypes = [agc_crcf, ctypes.c_float]
agc_crcf_get_scale = liquiddsp.agc_crcf_get_scale
agc_crcf_get_scale.restype = ctypes.c_float
agc_crcf_get_scale.argtypes = [agc_crcf]
agc_crcf_set_scale = liquiddsp.agc_crcf_set_scale
agc_crcf_set_scale.restype = ctypes.c_int32
agc_crcf_set_scale.argtypes = [agc_crcf, ctypes.c_float]
agc_crcf_init = liquiddsp.agc_crcf_init
agc_crcf_init.restype = ctypes.c_int32
agc_crcf_init.argtypes = [agc_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
agc_crcf_squelch_enable = liquiddsp.agc_crcf_squelch_enable
agc_crcf_squelch_enable.restype = ctypes.c_int32
agc_crcf_squelch_enable.argtypes = [agc_crcf]
agc_crcf_squelch_disable = liquiddsp.agc_crcf_squelch_disable
agc_crcf_squelch_disable.restype = ctypes.c_int32
agc_crcf_squelch_disable.argtypes = [agc_crcf]
agc_crcf_squelch_is_enabled = liquiddsp.agc_crcf_squelch_is_enabled
agc_crcf_squelch_is_enabled.restype = ctypes.c_int32
agc_crcf_squelch_is_enabled.argtypes = [agc_crcf]
agc_crcf_squelch_set_threshold = liquiddsp.agc_crcf_squelch_set_threshold
agc_crcf_squelch_set_threshold.restype = ctypes.c_int32
agc_crcf_squelch_set_threshold.argtypes = [agc_crcf, ctypes.c_float]
agc_crcf_squelch_get_threshold = liquiddsp.agc_crcf_squelch_get_threshold
agc_crcf_squelch_get_threshold.restype = ctypes.c_float
agc_crcf_squelch_get_threshold.argtypes = [agc_crcf]
agc_crcf_squelch_set_timeout = liquiddsp.agc_crcf_squelch_set_timeout
agc_crcf_squelch_set_timeout.restype = ctypes.c_int32
agc_crcf_squelch_set_timeout.argtypes = [agc_crcf, ctypes.c_uint32]
agc_crcf_squelch_get_timeout = liquiddsp.agc_crcf_squelch_get_timeout
agc_crcf_squelch_get_timeout.restype = ctypes.c_uint32
agc_crcf_squelch_get_timeout.argtypes = [agc_crcf]
agc_crcf_squelch_get_status = liquiddsp.agc_crcf_squelch_get_status
agc_crcf_squelch_get_status.restype = ctypes.c_int32
agc_crcf_squelch_get_status.argtypes = [agc_crcf]
class struct_agc_rrrf_s(Structure):
    pass

agc_rrrf = ctypes.POINTER(struct_agc_rrrf_s)
agc_rrrf_create = liquiddsp.agc_rrrf_create
agc_rrrf_create.restype = agc_rrrf
agc_rrrf_create.argtypes = []
agc_rrrf_destroy = liquiddsp.agc_rrrf_destroy
agc_rrrf_destroy.restype = ctypes.c_int32
agc_rrrf_destroy.argtypes = [agc_rrrf]
agc_rrrf_print = liquiddsp.agc_rrrf_print
agc_rrrf_print.restype = ctypes.c_int32
agc_rrrf_print.argtypes = [agc_rrrf]
agc_rrrf_reset = liquiddsp.agc_rrrf_reset
agc_rrrf_reset.restype = ctypes.c_int32
agc_rrrf_reset.argtypes = [agc_rrrf]
agc_rrrf_execute = liquiddsp.agc_rrrf_execute
agc_rrrf_execute.restype = ctypes.c_int32
agc_rrrf_execute.argtypes = [agc_rrrf, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
agc_rrrf_execute_block = liquiddsp.agc_rrrf_execute_block
agc_rrrf_execute_block.restype = ctypes.c_int32
agc_rrrf_execute_block.argtypes = [agc_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
agc_rrrf_lock = liquiddsp.agc_rrrf_lock
agc_rrrf_lock.restype = ctypes.c_int32
agc_rrrf_lock.argtypes = [agc_rrrf]
agc_rrrf_unlock = liquiddsp.agc_rrrf_unlock
agc_rrrf_unlock.restype = ctypes.c_int32
agc_rrrf_unlock.argtypes = [agc_rrrf]
agc_rrrf_set_bandwidth = liquiddsp.agc_rrrf_set_bandwidth
agc_rrrf_set_bandwidth.restype = ctypes.c_int32
agc_rrrf_set_bandwidth.argtypes = [agc_rrrf, ctypes.c_float]
agc_rrrf_get_bandwidth = liquiddsp.agc_rrrf_get_bandwidth
agc_rrrf_get_bandwidth.restype = ctypes.c_float
agc_rrrf_get_bandwidth.argtypes = [agc_rrrf]
agc_rrrf_get_signal_level = liquiddsp.agc_rrrf_get_signal_level
agc_rrrf_get_signal_level.restype = ctypes.c_float
agc_rrrf_get_signal_level.argtypes = [agc_rrrf]
agc_rrrf_set_signal_level = liquiddsp.agc_rrrf_set_signal_level
agc_rrrf_set_signal_level.restype = ctypes.c_int32
agc_rrrf_set_signal_level.argtypes = [agc_rrrf, ctypes.c_float]
agc_rrrf_get_rssi = liquiddsp.agc_rrrf_get_rssi
agc_rrrf_get_rssi.restype = ctypes.c_float
agc_rrrf_get_rssi.argtypes = [agc_rrrf]
agc_rrrf_set_rssi = liquiddsp.agc_rrrf_set_rssi
agc_rrrf_set_rssi.restype = ctypes.c_int32
agc_rrrf_set_rssi.argtypes = [agc_rrrf, ctypes.c_float]
agc_rrrf_get_gain = liquiddsp.agc_rrrf_get_gain
agc_rrrf_get_gain.restype = ctypes.c_float
agc_rrrf_get_gain.argtypes = [agc_rrrf]
agc_rrrf_set_gain = liquiddsp.agc_rrrf_set_gain
agc_rrrf_set_gain.restype = ctypes.c_int32
agc_rrrf_set_gain.argtypes = [agc_rrrf, ctypes.c_float]
agc_rrrf_get_scale = liquiddsp.agc_rrrf_get_scale
agc_rrrf_get_scale.restype = ctypes.c_float
agc_rrrf_get_scale.argtypes = [agc_rrrf]
agc_rrrf_set_scale = liquiddsp.agc_rrrf_set_scale
agc_rrrf_set_scale.restype = ctypes.c_int32
agc_rrrf_set_scale.argtypes = [agc_rrrf, ctypes.c_float]
agc_rrrf_init = liquiddsp.agc_rrrf_init
agc_rrrf_init.restype = ctypes.c_int32
agc_rrrf_init.argtypes = [agc_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
agc_rrrf_squelch_enable = liquiddsp.agc_rrrf_squelch_enable
agc_rrrf_squelch_enable.restype = ctypes.c_int32
agc_rrrf_squelch_enable.argtypes = [agc_rrrf]
agc_rrrf_squelch_disable = liquiddsp.agc_rrrf_squelch_disable
agc_rrrf_squelch_disable.restype = ctypes.c_int32
agc_rrrf_squelch_disable.argtypes = [agc_rrrf]
agc_rrrf_squelch_is_enabled = liquiddsp.agc_rrrf_squelch_is_enabled
agc_rrrf_squelch_is_enabled.restype = ctypes.c_int32
agc_rrrf_squelch_is_enabled.argtypes = [agc_rrrf]
agc_rrrf_squelch_set_threshold = liquiddsp.agc_rrrf_squelch_set_threshold
agc_rrrf_squelch_set_threshold.restype = ctypes.c_int32
agc_rrrf_squelch_set_threshold.argtypes = [agc_rrrf, ctypes.c_float]
agc_rrrf_squelch_get_threshold = liquiddsp.agc_rrrf_squelch_get_threshold
agc_rrrf_squelch_get_threshold.restype = ctypes.c_float
agc_rrrf_squelch_get_threshold.argtypes = [agc_rrrf]
agc_rrrf_squelch_set_timeout = liquiddsp.agc_rrrf_squelch_set_timeout
agc_rrrf_squelch_set_timeout.restype = ctypes.c_int32
agc_rrrf_squelch_set_timeout.argtypes = [agc_rrrf, ctypes.c_uint32]
agc_rrrf_squelch_get_timeout = liquiddsp.agc_rrrf_squelch_get_timeout
agc_rrrf_squelch_get_timeout.restype = ctypes.c_uint32
agc_rrrf_squelch_get_timeout.argtypes = [agc_rrrf]
agc_rrrf_squelch_get_status = liquiddsp.agc_rrrf_squelch_get_status
agc_rrrf_squelch_get_status.restype = ctypes.c_int32
agc_rrrf_squelch_get_status.argtypes = [agc_rrrf]
class struct_cvsd_s(Structure):
    pass

cvsd = ctypes.POINTER(struct_cvsd_s)
cvsd_create = liquiddsp.cvsd_create
cvsd_create.restype = cvsd
cvsd_create.argtypes = [ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
cvsd_destroy = liquiddsp.cvsd_destroy
cvsd_destroy.restype = None
cvsd_destroy.argtypes = [cvsd]
cvsd_print = liquiddsp.cvsd_print
cvsd_print.restype = None
cvsd_print.argtypes = [cvsd]
cvsd_encode = liquiddsp.cvsd_encode
cvsd_encode.restype = ctypes.c_ubyte
cvsd_encode.argtypes = [cvsd, ctypes.c_float]
cvsd_decode = liquiddsp.cvsd_decode
cvsd_decode.restype = ctypes.c_float
cvsd_decode.argtypes = [cvsd, ctypes.c_ubyte]
cvsd_encode8 = liquiddsp.cvsd_encode8
cvsd_encode8.restype = None
cvsd_encode8.argtypes = [cvsd, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_ubyte)]
cvsd_decode8 = liquiddsp.cvsd_decode8
cvsd_decode8.restype = None
cvsd_decode8.argtypes = [cvsd, ctypes.c_ubyte, ctypes.POINTER(ctypes.c_float)]
class struct_cbufferf_s(Structure):
    pass

cbufferf = ctypes.POINTER(struct_cbufferf_s)
cbufferf_create = liquiddsp.cbufferf_create
cbufferf_create.restype = cbufferf
cbufferf_create.argtypes = [ctypes.c_uint32]
cbufferf_create_max = liquiddsp.cbufferf_create_max
cbufferf_create_max.restype = cbufferf
cbufferf_create_max.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
cbufferf_destroy = liquiddsp.cbufferf_destroy
cbufferf_destroy.restype = None
cbufferf_destroy.argtypes = [cbufferf]
cbufferf_print = liquiddsp.cbufferf_print
cbufferf_print.restype = None
cbufferf_print.argtypes = [cbufferf]
cbufferf_debug_print = liquiddsp.cbufferf_debug_print
cbufferf_debug_print.restype = None
cbufferf_debug_print.argtypes = [cbufferf]
cbufferf_reset = liquiddsp.cbufferf_reset
cbufferf_reset.restype = None
cbufferf_reset.argtypes = [cbufferf]
cbufferf_size = liquiddsp.cbufferf_size
cbufferf_size.restype = ctypes.c_uint32
cbufferf_size.argtypes = [cbufferf]
cbufferf_max_size = liquiddsp.cbufferf_max_size
cbufferf_max_size.restype = ctypes.c_uint32
cbufferf_max_size.argtypes = [cbufferf]
cbufferf_max_read = liquiddsp.cbufferf_max_read
cbufferf_max_read.restype = ctypes.c_uint32
cbufferf_max_read.argtypes = [cbufferf]
cbufferf_space_available = liquiddsp.cbufferf_space_available
cbufferf_space_available.restype = ctypes.c_uint32
cbufferf_space_available.argtypes = [cbufferf]
cbufferf_is_full = liquiddsp.cbufferf_is_full
cbufferf_is_full.restype = ctypes.c_int32
cbufferf_is_full.argtypes = [cbufferf]
cbufferf_push = liquiddsp.cbufferf_push
cbufferf_push.restype = None
cbufferf_push.argtypes = [cbufferf, ctypes.c_float]
cbufferf_write = liquiddsp.cbufferf_write
cbufferf_write.restype = None
cbufferf_write.argtypes = [cbufferf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
cbufferf_pop = liquiddsp.cbufferf_pop
cbufferf_pop.restype = None
cbufferf_pop.argtypes = [cbufferf, ctypes.POINTER(ctypes.c_float)]
cbufferf_read = liquiddsp.cbufferf_read
cbufferf_read.restype = None
cbufferf_read.argtypes = [cbufferf, ctypes.c_uint32, ctypes.POINTER(ctypes.POINTER(ctypes.c_float)), ctypes.POINTER(ctypes.c_uint32)]
cbufferf_release = liquiddsp.cbufferf_release
cbufferf_release.restype = None
cbufferf_release.argtypes = [cbufferf, ctypes.c_uint32]
class struct_cbuffercf_s(Structure):
    pass

cbuffercf = ctypes.POINTER(struct_cbuffercf_s)
cbuffercf_create = liquiddsp.cbuffercf_create
cbuffercf_create.restype = cbuffercf
cbuffercf_create.argtypes = [ctypes.c_uint32]
cbuffercf_create_max = liquiddsp.cbuffercf_create_max
cbuffercf_create_max.restype = cbuffercf
cbuffercf_create_max.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
cbuffercf_destroy = liquiddsp.cbuffercf_destroy
cbuffercf_destroy.restype = None
cbuffercf_destroy.argtypes = [cbuffercf]
cbuffercf_print = liquiddsp.cbuffercf_print
cbuffercf_print.restype = None
cbuffercf_print.argtypes = [cbuffercf]
cbuffercf_debug_print = liquiddsp.cbuffercf_debug_print
cbuffercf_debug_print.restype = None
cbuffercf_debug_print.argtypes = [cbuffercf]
cbuffercf_reset = liquiddsp.cbuffercf_reset
cbuffercf_reset.restype = None
cbuffercf_reset.argtypes = [cbuffercf]
cbuffercf_size = liquiddsp.cbuffercf_size
cbuffercf_size.restype = ctypes.c_uint32
cbuffercf_size.argtypes = [cbuffercf]
cbuffercf_max_size = liquiddsp.cbuffercf_max_size
cbuffercf_max_size.restype = ctypes.c_uint32
cbuffercf_max_size.argtypes = [cbuffercf]
cbuffercf_max_read = liquiddsp.cbuffercf_max_read
cbuffercf_max_read.restype = ctypes.c_uint32
cbuffercf_max_read.argtypes = [cbuffercf]
cbuffercf_space_available = liquiddsp.cbuffercf_space_available
cbuffercf_space_available.restype = ctypes.c_uint32
cbuffercf_space_available.argtypes = [cbuffercf]
cbuffercf_is_full = liquiddsp.cbuffercf_is_full
cbuffercf_is_full.restype = ctypes.c_int32
cbuffercf_is_full.argtypes = [cbuffercf]
cbuffercf_push = liquiddsp.cbuffercf_push
cbuffercf_push.restype = None
cbuffercf_push.argtypes = [cbuffercf, liquid_float_complex]
cbuffercf_write = liquiddsp.cbuffercf_write
cbuffercf_write.restype = None
cbuffercf_write.argtypes = [cbuffercf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
cbuffercf_pop = liquiddsp.cbuffercf_pop
cbuffercf_pop.restype = None
cbuffercf_pop.argtypes = [cbuffercf, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
cbuffercf_read = liquiddsp.cbuffercf_read
cbuffercf_read.restype = None
cbuffercf_read.argtypes = [cbuffercf, ctypes.c_uint32, ctypes.POINTER(ctypes.POINTER(struct_c__SA_liquid_float_complex)), ctypes.POINTER(ctypes.c_uint32)]
cbuffercf_release = liquiddsp.cbuffercf_release
cbuffercf_release.restype = None
cbuffercf_release.argtypes = [cbuffercf, ctypes.c_uint32]
class struct_windowf_s(Structure):
    pass

windowf = ctypes.POINTER(struct_windowf_s)
windowf_create = liquiddsp.windowf_create
windowf_create.restype = windowf
windowf_create.argtypes = [ctypes.c_uint32]
windowf_recreate = liquiddsp.windowf_recreate
windowf_recreate.restype = windowf
windowf_recreate.argtypes = [windowf, ctypes.c_uint32]
windowf_destroy = liquiddsp.windowf_destroy
windowf_destroy.restype = ctypes.c_int32
windowf_destroy.argtypes = [windowf]
windowf_print = liquiddsp.windowf_print
windowf_print.restype = ctypes.c_int32
windowf_print.argtypes = [windowf]
windowf_debug_print = liquiddsp.windowf_debug_print
windowf_debug_print.restype = ctypes.c_int32
windowf_debug_print.argtypes = [windowf]
windowf_reset = liquiddsp.windowf_reset
windowf_reset.restype = ctypes.c_int32
windowf_reset.argtypes = [windowf]
windowf_read = liquiddsp.windowf_read
windowf_read.restype = ctypes.c_int32
windowf_read.argtypes = [windowf, ctypes.POINTER(ctypes.POINTER(ctypes.c_float))]
windowf_index = liquiddsp.windowf_index
windowf_index.restype = ctypes.c_int32
windowf_index.argtypes = [windowf, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
windowf_push = liquiddsp.windowf_push
windowf_push.restype = ctypes.c_int32
windowf_push.argtypes = [windowf, ctypes.c_float]
windowf_write = liquiddsp.windowf_write
windowf_write.restype = ctypes.c_int32
windowf_write.argtypes = [windowf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
class struct_windowcf_s(Structure):
    pass

windowcf = ctypes.POINTER(struct_windowcf_s)
windowcf_create = liquiddsp.windowcf_create
windowcf_create.restype = windowcf
windowcf_create.argtypes = [ctypes.c_uint32]
windowcf_recreate = liquiddsp.windowcf_recreate
windowcf_recreate.restype = windowcf
windowcf_recreate.argtypes = [windowcf, ctypes.c_uint32]
windowcf_destroy = liquiddsp.windowcf_destroy
windowcf_destroy.restype = ctypes.c_int32
windowcf_destroy.argtypes = [windowcf]
windowcf_print = liquiddsp.windowcf_print
windowcf_print.restype = ctypes.c_int32
windowcf_print.argtypes = [windowcf]
windowcf_debug_print = liquiddsp.windowcf_debug_print
windowcf_debug_print.restype = ctypes.c_int32
windowcf_debug_print.argtypes = [windowcf]
windowcf_reset = liquiddsp.windowcf_reset
windowcf_reset.restype = ctypes.c_int32
windowcf_reset.argtypes = [windowcf]
windowcf_read = liquiddsp.windowcf_read
windowcf_read.restype = ctypes.c_int32
windowcf_read.argtypes = [windowcf, ctypes.POINTER(ctypes.POINTER(struct_c__SA_liquid_float_complex))]
windowcf_index = liquiddsp.windowcf_index
windowcf_index.restype = ctypes.c_int32
windowcf_index.argtypes = [windowcf, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
windowcf_push = liquiddsp.windowcf_push
windowcf_push.restype = ctypes.c_int32
windowcf_push.argtypes = [windowcf, liquid_float_complex]
windowcf_write = liquiddsp.windowcf_write
windowcf_write.restype = ctypes.c_int32
windowcf_write.argtypes = [windowcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
class struct_wdelayf_s(Structure):
    pass

wdelayf = ctypes.POINTER(struct_wdelayf_s)
wdelayf_create = liquiddsp.wdelayf_create
wdelayf_create.restype = wdelayf
wdelayf_create.argtypes = [ctypes.c_uint32]
wdelayf_recreate = liquiddsp.wdelayf_recreate
wdelayf_recreate.restype = wdelayf
wdelayf_recreate.argtypes = [wdelayf, ctypes.c_uint32]
wdelayf_destroy = liquiddsp.wdelayf_destroy
wdelayf_destroy.restype = None
wdelayf_destroy.argtypes = [wdelayf]
wdelayf_print = liquiddsp.wdelayf_print
wdelayf_print.restype = None
wdelayf_print.argtypes = [wdelayf]
wdelayf_reset = liquiddsp.wdelayf_reset
wdelayf_reset.restype = None
wdelayf_reset.argtypes = [wdelayf]
wdelayf_read = liquiddsp.wdelayf_read
wdelayf_read.restype = None
wdelayf_read.argtypes = [wdelayf, ctypes.POINTER(ctypes.c_float)]
wdelayf_push = liquiddsp.wdelayf_push
wdelayf_push.restype = None
wdelayf_push.argtypes = [wdelayf, ctypes.c_float]
class struct_wdelaycf_s(Structure):
    pass

wdelaycf = ctypes.POINTER(struct_wdelaycf_s)
wdelaycf_create = liquiddsp.wdelaycf_create
wdelaycf_create.restype = wdelaycf
wdelaycf_create.argtypes = [ctypes.c_uint32]
wdelaycf_recreate = liquiddsp.wdelaycf_recreate
wdelaycf_recreate.restype = wdelaycf
wdelaycf_recreate.argtypes = [wdelaycf, ctypes.c_uint32]
wdelaycf_destroy = liquiddsp.wdelaycf_destroy
wdelaycf_destroy.restype = None
wdelaycf_destroy.argtypes = [wdelaycf]
wdelaycf_print = liquiddsp.wdelaycf_print
wdelaycf_print.restype = None
wdelaycf_print.argtypes = [wdelaycf]
wdelaycf_reset = liquiddsp.wdelaycf_reset
wdelaycf_reset.restype = None
wdelaycf_reset.argtypes = [wdelaycf]
wdelaycf_read = liquiddsp.wdelaycf_read
wdelaycf_read.restype = None
wdelaycf_read.argtypes = [wdelaycf, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
wdelaycf_push = liquiddsp.wdelaycf_push
wdelaycf_push.restype = None
wdelaycf_push.argtypes = [wdelaycf, liquid_float_complex]
class struct_channel_cccf_s(Structure):
    pass

channel_cccf = ctypes.POINTER(struct_channel_cccf_s)
channel_cccf_create = liquiddsp.channel_cccf_create
channel_cccf_create.restype = channel_cccf
channel_cccf_create.argtypes = []
channel_cccf_destroy = liquiddsp.channel_cccf_destroy
channel_cccf_destroy.restype = ctypes.c_int32
channel_cccf_destroy.argtypes = [channel_cccf]
channel_cccf_print = liquiddsp.channel_cccf_print
channel_cccf_print.restype = ctypes.c_int32
channel_cccf_print.argtypes = [channel_cccf]
channel_cccf_add_awgn = liquiddsp.channel_cccf_add_awgn
channel_cccf_add_awgn.restype = ctypes.c_int32
channel_cccf_add_awgn.argtypes = [channel_cccf, ctypes.c_float, ctypes.c_float]
channel_cccf_add_carrier_offset = liquiddsp.channel_cccf_add_carrier_offset
channel_cccf_add_carrier_offset.restype = ctypes.c_int32
channel_cccf_add_carrier_offset.argtypes = [channel_cccf, ctypes.c_float, ctypes.c_float]
channel_cccf_add_multipath = liquiddsp.channel_cccf_add_multipath
channel_cccf_add_multipath.restype = ctypes.c_int32
channel_cccf_add_multipath.argtypes = [channel_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
channel_cccf_add_shadowing = liquiddsp.channel_cccf_add_shadowing
channel_cccf_add_shadowing.restype = ctypes.c_int32
channel_cccf_add_shadowing.argtypes = [channel_cccf, ctypes.c_float, ctypes.c_float]
channel_cccf_execute = liquiddsp.channel_cccf_execute
channel_cccf_execute.restype = ctypes.c_int32
channel_cccf_execute.argtypes = [channel_cccf, liquid_float_complex, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
channel_cccf_execute_block = liquiddsp.channel_cccf_execute_block
channel_cccf_execute_block.restype = ctypes.c_int32
channel_cccf_execute_block.argtypes = [channel_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
class struct_tvmpch_cccf_s(Structure):
    pass

tvmpch_cccf = ctypes.POINTER(struct_tvmpch_cccf_s)
tvmpch_cccf_create = liquiddsp.tvmpch_cccf_create
tvmpch_cccf_create.restype = tvmpch_cccf
tvmpch_cccf_create.argtypes = [ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
tvmpch_cccf_destroy = liquiddsp.tvmpch_cccf_destroy
tvmpch_cccf_destroy.restype = ctypes.c_int32
tvmpch_cccf_destroy.argtypes = [tvmpch_cccf]
tvmpch_cccf_reset = liquiddsp.tvmpch_cccf_reset
tvmpch_cccf_reset.restype = ctypes.c_int32
tvmpch_cccf_reset.argtypes = [tvmpch_cccf]
tvmpch_cccf_print = liquiddsp.tvmpch_cccf_print
tvmpch_cccf_print.restype = ctypes.c_int32
tvmpch_cccf_print.argtypes = [tvmpch_cccf]
tvmpch_cccf_push = liquiddsp.tvmpch_cccf_push
tvmpch_cccf_push.restype = ctypes.c_int32
tvmpch_cccf_push.argtypes = [tvmpch_cccf, liquid_float_complex]
tvmpch_cccf_execute = liquiddsp.tvmpch_cccf_execute
tvmpch_cccf_execute.restype = ctypes.c_int32
tvmpch_cccf_execute.argtypes = [tvmpch_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
tvmpch_cccf_execute_block = liquiddsp.tvmpch_cccf_execute_block
tvmpch_cccf_execute_block.restype = ctypes.c_int32
tvmpch_cccf_execute_block.argtypes = [tvmpch_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
class struct_dotprod_rrrf_s(Structure):
    pass

dotprod_rrrf = ctypes.POINTER(struct_dotprod_rrrf_s)
dotprod_rrrf_run = liquiddsp.dotprod_rrrf_run
dotprod_rrrf_run.restype = None
dotprod_rrrf_run.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
dotprod_rrrf_run4 = liquiddsp.dotprod_rrrf_run4
dotprod_rrrf_run4.restype = None
dotprod_rrrf_run4.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
dotprod_rrrf_create = liquiddsp.dotprod_rrrf_create
dotprod_rrrf_create.restype = dotprod_rrrf
dotprod_rrrf_create.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
dotprod_rrrf_recreate = liquiddsp.dotprod_rrrf_recreate
dotprod_rrrf_recreate.restype = dotprod_rrrf
dotprod_rrrf_recreate.argtypes = [dotprod_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
dotprod_rrrf_destroy = liquiddsp.dotprod_rrrf_destroy
dotprod_rrrf_destroy.restype = None
dotprod_rrrf_destroy.argtypes = [dotprod_rrrf]
dotprod_rrrf_print = liquiddsp.dotprod_rrrf_print
dotprod_rrrf_print.restype = None
dotprod_rrrf_print.argtypes = [dotprod_rrrf]
dotprod_rrrf_execute = liquiddsp.dotprod_rrrf_execute
dotprod_rrrf_execute.restype = None
dotprod_rrrf_execute.argtypes = [dotprod_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
class struct_dotprod_cccf_s(Structure):
    pass

dotprod_cccf = ctypes.POINTER(struct_dotprod_cccf_s)
dotprod_cccf_run = liquiddsp.dotprod_cccf_run
dotprod_cccf_run.restype = None
dotprod_cccf_run.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
dotprod_cccf_run4 = liquiddsp.dotprod_cccf_run4
dotprod_cccf_run4.restype = None
dotprod_cccf_run4.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
dotprod_cccf_create = liquiddsp.dotprod_cccf_create
dotprod_cccf_create.restype = dotprod_cccf
dotprod_cccf_create.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
dotprod_cccf_recreate = liquiddsp.dotprod_cccf_recreate
dotprod_cccf_recreate.restype = dotprod_cccf
dotprod_cccf_recreate.argtypes = [dotprod_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
dotprod_cccf_destroy = liquiddsp.dotprod_cccf_destroy
dotprod_cccf_destroy.restype = None
dotprod_cccf_destroy.argtypes = [dotprod_cccf]
dotprod_cccf_print = liquiddsp.dotprod_cccf_print
dotprod_cccf_print.restype = None
dotprod_cccf_print.argtypes = [dotprod_cccf]
dotprod_cccf_execute = liquiddsp.dotprod_cccf_execute
dotprod_cccf_execute.restype = None
dotprod_cccf_execute.argtypes = [dotprod_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
class struct_dotprod_crcf_s(Structure):
    pass

dotprod_crcf = ctypes.POINTER(struct_dotprod_crcf_s)
dotprod_crcf_run = liquiddsp.dotprod_crcf_run
dotprod_crcf_run.restype = None
dotprod_crcf_run.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
dotprod_crcf_run4 = liquiddsp.dotprod_crcf_run4
dotprod_crcf_run4.restype = None
dotprod_crcf_run4.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
dotprod_crcf_create = liquiddsp.dotprod_crcf_create
dotprod_crcf_create.restype = dotprod_crcf
dotprod_crcf_create.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
dotprod_crcf_recreate = liquiddsp.dotprod_crcf_recreate
dotprod_crcf_recreate.restype = dotprod_crcf
dotprod_crcf_recreate.argtypes = [dotprod_crcf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
dotprod_crcf_destroy = liquiddsp.dotprod_crcf_destroy
dotprod_crcf_destroy.restype = None
dotprod_crcf_destroy.argtypes = [dotprod_crcf]
dotprod_crcf_print = liquiddsp.dotprod_crcf_print
dotprod_crcf_print.restype = None
dotprod_crcf_print.argtypes = [dotprod_crcf]
dotprod_crcf_execute = liquiddsp.dotprod_crcf_execute
dotprod_crcf_execute.restype = None
dotprod_crcf_execute.argtypes = [dotprod_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
liquid_sumsqf = liquiddsp.liquid_sumsqf
liquid_sumsqf.restype = ctypes.c_float
liquid_sumsqf.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
liquid_sumsqcf = liquiddsp.liquid_sumsqcf
liquid_sumsqcf.restype = ctypes.c_float
liquid_sumsqcf.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
class struct_eqlms_rrrf_s(Structure):
    pass

eqlms_rrrf = ctypes.POINTER(struct_eqlms_rrrf_s)
eqlms_rrrf_create = liquiddsp.eqlms_rrrf_create
eqlms_rrrf_create.restype = eqlms_rrrf
eqlms_rrrf_create.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
eqlms_rrrf_create_rnyquist = liquiddsp.eqlms_rrrf_create_rnyquist
eqlms_rrrf_create_rnyquist.restype = eqlms_rrrf
eqlms_rrrf_create_rnyquist.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
eqlms_rrrf_create_lowpass = liquiddsp.eqlms_rrrf_create_lowpass
eqlms_rrrf_create_lowpass.restype = eqlms_rrrf
eqlms_rrrf_create_lowpass.argtypes = [ctypes.c_uint32, ctypes.c_float]
eqlms_rrrf_recreate = liquiddsp.eqlms_rrrf_recreate
eqlms_rrrf_recreate.restype = eqlms_rrrf
eqlms_rrrf_recreate.argtypes = [eqlms_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
eqlms_rrrf_destroy = liquiddsp.eqlms_rrrf_destroy
eqlms_rrrf_destroy.restype = ctypes.c_int32
eqlms_rrrf_destroy.argtypes = [eqlms_rrrf]
eqlms_rrrf_reset = liquiddsp.eqlms_rrrf_reset
eqlms_rrrf_reset.restype = ctypes.c_int32
eqlms_rrrf_reset.argtypes = [eqlms_rrrf]
eqlms_rrrf_print = liquiddsp.eqlms_rrrf_print
eqlms_rrrf_print.restype = ctypes.c_int32
eqlms_rrrf_print.argtypes = [eqlms_rrrf]
eqlms_rrrf_get_bw = liquiddsp.eqlms_rrrf_get_bw
eqlms_rrrf_get_bw.restype = ctypes.c_float
eqlms_rrrf_get_bw.argtypes = [eqlms_rrrf]
eqlms_rrrf_set_bw = liquiddsp.eqlms_rrrf_set_bw
eqlms_rrrf_set_bw.restype = ctypes.c_int32
eqlms_rrrf_set_bw.argtypes = [eqlms_rrrf, ctypes.c_float]
eqlms_rrrf_push = liquiddsp.eqlms_rrrf_push
eqlms_rrrf_push.restype = ctypes.c_int32
eqlms_rrrf_push.argtypes = [eqlms_rrrf, ctypes.c_float]
eqlms_rrrf_push_block = liquiddsp.eqlms_rrrf_push_block
eqlms_rrrf_push_block.restype = ctypes.c_int32
eqlms_rrrf_push_block.argtypes = [eqlms_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
eqlms_rrrf_execute = liquiddsp.eqlms_rrrf_execute
eqlms_rrrf_execute.restype = ctypes.c_int32
eqlms_rrrf_execute.argtypes = [eqlms_rrrf, ctypes.POINTER(ctypes.c_float)]
eqlms_rrrf_execute_block = liquiddsp.eqlms_rrrf_execute_block
eqlms_rrrf_execute_block.restype = ctypes.c_int32
eqlms_rrrf_execute_block.argtypes = [eqlms_rrrf, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
eqlms_rrrf_step = liquiddsp.eqlms_rrrf_step
eqlms_rrrf_step.restype = ctypes.c_int32
eqlms_rrrf_step.argtypes = [eqlms_rrrf, ctypes.c_float, ctypes.c_float]
eqlms_rrrf_step_blind = liquiddsp.eqlms_rrrf_step_blind
eqlms_rrrf_step_blind.restype = ctypes.c_int32
eqlms_rrrf_step_blind.argtypes = [eqlms_rrrf, ctypes.c_float]
eqlms_rrrf_get_weights = liquiddsp.eqlms_rrrf_get_weights
eqlms_rrrf_get_weights.restype = ctypes.c_int32
eqlms_rrrf_get_weights.argtypes = [eqlms_rrrf, ctypes.POINTER(ctypes.c_float)]
eqlms_rrrf_train = liquiddsp.eqlms_rrrf_train
eqlms_rrrf_train.restype = ctypes.c_int32
eqlms_rrrf_train.argtypes = [eqlms_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
class struct_eqlms_cccf_s(Structure):
    pass

eqlms_cccf = ctypes.POINTER(struct_eqlms_cccf_s)
eqlms_cccf_create = liquiddsp.eqlms_cccf_create
eqlms_cccf_create.restype = eqlms_cccf
eqlms_cccf_create.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
eqlms_cccf_create_rnyquist = liquiddsp.eqlms_cccf_create_rnyquist
eqlms_cccf_create_rnyquist.restype = eqlms_cccf
eqlms_cccf_create_rnyquist.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
eqlms_cccf_create_lowpass = liquiddsp.eqlms_cccf_create_lowpass
eqlms_cccf_create_lowpass.restype = eqlms_cccf
eqlms_cccf_create_lowpass.argtypes = [ctypes.c_uint32, ctypes.c_float]
eqlms_cccf_recreate = liquiddsp.eqlms_cccf_recreate
eqlms_cccf_recreate.restype = eqlms_cccf
eqlms_cccf_recreate.argtypes = [eqlms_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
eqlms_cccf_destroy = liquiddsp.eqlms_cccf_destroy
eqlms_cccf_destroy.restype = ctypes.c_int32
eqlms_cccf_destroy.argtypes = [eqlms_cccf]
eqlms_cccf_reset = liquiddsp.eqlms_cccf_reset
eqlms_cccf_reset.restype = ctypes.c_int32
eqlms_cccf_reset.argtypes = [eqlms_cccf]
eqlms_cccf_print = liquiddsp.eqlms_cccf_print
eqlms_cccf_print.restype = ctypes.c_int32
eqlms_cccf_print.argtypes = [eqlms_cccf]
eqlms_cccf_get_bw = liquiddsp.eqlms_cccf_get_bw
eqlms_cccf_get_bw.restype = ctypes.c_float
eqlms_cccf_get_bw.argtypes = [eqlms_cccf]
eqlms_cccf_set_bw = liquiddsp.eqlms_cccf_set_bw
eqlms_cccf_set_bw.restype = ctypes.c_int32
eqlms_cccf_set_bw.argtypes = [eqlms_cccf, ctypes.c_float]
eqlms_cccf_push = liquiddsp.eqlms_cccf_push
eqlms_cccf_push.restype = ctypes.c_int32
eqlms_cccf_push.argtypes = [eqlms_cccf, liquid_float_complex]
eqlms_cccf_push_block = liquiddsp.eqlms_cccf_push_block
eqlms_cccf_push_block.restype = ctypes.c_int32
eqlms_cccf_push_block.argtypes = [eqlms_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
eqlms_cccf_execute = liquiddsp.eqlms_cccf_execute
eqlms_cccf_execute.restype = ctypes.c_int32
eqlms_cccf_execute.argtypes = [eqlms_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
eqlms_cccf_execute_block = liquiddsp.eqlms_cccf_execute_block
eqlms_cccf_execute_block.restype = ctypes.c_int32
eqlms_cccf_execute_block.argtypes = [eqlms_cccf, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
eqlms_cccf_step = liquiddsp.eqlms_cccf_step
eqlms_cccf_step.restype = ctypes.c_int32
eqlms_cccf_step.argtypes = [eqlms_cccf, liquid_float_complex, liquid_float_complex]
eqlms_cccf_step_blind = liquiddsp.eqlms_cccf_step_blind
eqlms_cccf_step_blind.restype = ctypes.c_int32
eqlms_cccf_step_blind.argtypes = [eqlms_cccf, liquid_float_complex]
eqlms_cccf_get_weights = liquiddsp.eqlms_cccf_get_weights
eqlms_cccf_get_weights.restype = ctypes.c_int32
eqlms_cccf_get_weights.argtypes = [eqlms_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
eqlms_cccf_train = liquiddsp.eqlms_cccf_train
eqlms_cccf_train.restype = ctypes.c_int32
eqlms_cccf_train.argtypes = [eqlms_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
class struct_eqrls_rrrf_s(Structure):
    pass

eqrls_rrrf = ctypes.POINTER(struct_eqrls_rrrf_s)
eqrls_rrrf_create = liquiddsp.eqrls_rrrf_create
eqrls_rrrf_create.restype = eqrls_rrrf
eqrls_rrrf_create.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
eqrls_rrrf_recreate = liquiddsp.eqrls_rrrf_recreate
eqrls_rrrf_recreate.restype = eqrls_rrrf
eqrls_rrrf_recreate.argtypes = [eqrls_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
eqrls_rrrf_destroy = liquiddsp.eqrls_rrrf_destroy
eqrls_rrrf_destroy.restype = ctypes.c_int32
eqrls_rrrf_destroy.argtypes = [eqrls_rrrf]
eqrls_rrrf_reset = liquiddsp.eqrls_rrrf_reset
eqrls_rrrf_reset.restype = ctypes.c_int32
eqrls_rrrf_reset.argtypes = [eqrls_rrrf]
eqrls_rrrf_print = liquiddsp.eqrls_rrrf_print
eqrls_rrrf_print.restype = ctypes.c_int32
eqrls_rrrf_print.argtypes = [eqrls_rrrf]
eqrls_rrrf_get_bw = liquiddsp.eqrls_rrrf_get_bw
eqrls_rrrf_get_bw.restype = ctypes.c_float
eqrls_rrrf_get_bw.argtypes = [eqrls_rrrf]
eqrls_rrrf_set_bw = liquiddsp.eqrls_rrrf_set_bw
eqrls_rrrf_set_bw.restype = ctypes.c_int32
eqrls_rrrf_set_bw.argtypes = [eqrls_rrrf, ctypes.c_float]
eqrls_rrrf_push = liquiddsp.eqrls_rrrf_push
eqrls_rrrf_push.restype = ctypes.c_int32
eqrls_rrrf_push.argtypes = [eqrls_rrrf, ctypes.c_float]
eqrls_rrrf_execute = liquiddsp.eqrls_rrrf_execute
eqrls_rrrf_execute.restype = ctypes.c_int32
eqrls_rrrf_execute.argtypes = [eqrls_rrrf, ctypes.POINTER(ctypes.c_float)]
eqrls_rrrf_step = liquiddsp.eqrls_rrrf_step
eqrls_rrrf_step.restype = ctypes.c_int32
eqrls_rrrf_step.argtypes = [eqrls_rrrf, ctypes.c_float, ctypes.c_float]
eqrls_rrrf_get_weights = liquiddsp.eqrls_rrrf_get_weights
eqrls_rrrf_get_weights.restype = ctypes.c_int32
eqrls_rrrf_get_weights.argtypes = [eqrls_rrrf, ctypes.POINTER(ctypes.c_float)]
eqrls_rrrf_train = liquiddsp.eqrls_rrrf_train
eqrls_rrrf_train.restype = ctypes.c_int32
eqrls_rrrf_train.argtypes = [eqrls_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
class struct_eqrls_cccf_s(Structure):
    pass

eqrls_cccf = ctypes.POINTER(struct_eqrls_cccf_s)
eqrls_cccf_create = liquiddsp.eqrls_cccf_create
eqrls_cccf_create.restype = eqrls_cccf
eqrls_cccf_create.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
eqrls_cccf_recreate = liquiddsp.eqrls_cccf_recreate
eqrls_cccf_recreate.restype = eqrls_cccf
eqrls_cccf_recreate.argtypes = [eqrls_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
eqrls_cccf_destroy = liquiddsp.eqrls_cccf_destroy
eqrls_cccf_destroy.restype = ctypes.c_int32
eqrls_cccf_destroy.argtypes = [eqrls_cccf]
eqrls_cccf_reset = liquiddsp.eqrls_cccf_reset
eqrls_cccf_reset.restype = ctypes.c_int32
eqrls_cccf_reset.argtypes = [eqrls_cccf]
eqrls_cccf_print = liquiddsp.eqrls_cccf_print
eqrls_cccf_print.restype = ctypes.c_int32
eqrls_cccf_print.argtypes = [eqrls_cccf]
eqrls_cccf_get_bw = liquiddsp.eqrls_cccf_get_bw
eqrls_cccf_get_bw.restype = ctypes.c_float
eqrls_cccf_get_bw.argtypes = [eqrls_cccf]
eqrls_cccf_set_bw = liquiddsp.eqrls_cccf_set_bw
eqrls_cccf_set_bw.restype = ctypes.c_int32
eqrls_cccf_set_bw.argtypes = [eqrls_cccf, ctypes.c_float]
eqrls_cccf_push = liquiddsp.eqrls_cccf_push
eqrls_cccf_push.restype = ctypes.c_int32
eqrls_cccf_push.argtypes = [eqrls_cccf, liquid_float_complex]
eqrls_cccf_execute = liquiddsp.eqrls_cccf_execute
eqrls_cccf_execute.restype = ctypes.c_int32
eqrls_cccf_execute.argtypes = [eqrls_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
eqrls_cccf_step = liquiddsp.eqrls_cccf_step
eqrls_cccf_step.restype = ctypes.c_int32
eqrls_cccf_step.argtypes = [eqrls_cccf, liquid_float_complex, liquid_float_complex]
eqrls_cccf_get_weights = liquiddsp.eqrls_cccf_get_weights
eqrls_cccf_get_weights.restype = ctypes.c_int32
eqrls_cccf_get_weights.argtypes = [eqrls_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
eqrls_cccf_train = liquiddsp.eqrls_cccf_train
eqrls_cccf_train.restype = ctypes.c_int32
eqrls_cccf_train.argtypes = [eqrls_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]

# values for enumeration 'c__EA_crc_scheme'
c__EA_crc_scheme__enumvalues = {
    0: 'LIQUID_CRC_UNKNOWN',
    1: 'LIQUID_CRC_NONE',
    2: 'LIQUID_CRC_CHECKSUM',
    3: 'LIQUID_CRC_8',
    4: 'LIQUID_CRC_16',
    5: 'LIQUID_CRC_24',
    6: 'LIQUID_CRC_32',
}
LIQUID_CRC_UNKNOWN = 0
LIQUID_CRC_NONE = 1
LIQUID_CRC_CHECKSUM = 2
LIQUID_CRC_8 = 3
LIQUID_CRC_16 = 4
LIQUID_CRC_24 = 5
LIQUID_CRC_32 = 6
c__EA_crc_scheme = ctypes.c_uint32 # enum
crc_scheme = c__EA_crc_scheme
crc_scheme__enumvalues = c__EA_crc_scheme__enumvalues
crc_scheme_str = [] # Variable ctypes.POINTER(ctypes.c_char) * 2 * 7
liquid_print_crc_schemes = liquiddsp.liquid_print_crc_schemes
liquid_print_crc_schemes.restype = None
liquid_print_crc_schemes.argtypes = []
liquid_getopt_str2crc = liquiddsp.liquid_getopt_str2crc
liquid_getopt_str2crc.restype = crc_scheme
liquid_getopt_str2crc.argtypes = [ctypes.POINTER(ctypes.c_char)]
crc_get_length = liquiddsp.crc_get_length
crc_get_length.restype = ctypes.c_uint32
crc_get_length.argtypes = [crc_scheme]
crc_generate_key = liquiddsp.crc_generate_key
crc_generate_key.restype = ctypes.c_uint32
crc_generate_key.argtypes = [crc_scheme, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32]
crc_append_key = liquiddsp.crc_append_key
crc_append_key.restype = ctypes.c_int32
crc_append_key.argtypes = [crc_scheme, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32]
crc_validate_message = liquiddsp.crc_validate_message
crc_validate_message.restype = ctypes.c_int32
crc_validate_message.argtypes = [crc_scheme, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, ctypes.c_uint32]
crc_check_key = liquiddsp.crc_check_key
crc_check_key.restype = ctypes.c_int32
crc_check_key.argtypes = [crc_scheme, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32]
crc_sizeof_key = liquiddsp.crc_sizeof_key
crc_sizeof_key.restype = ctypes.c_uint32
crc_sizeof_key.argtypes = [crc_scheme]

# values for enumeration 'c__EA_fec_scheme'
c__EA_fec_scheme__enumvalues = {
    0: 'LIQUID_FEC_UNKNOWN',
    1: 'LIQUID_FEC_NONE',
    2: 'LIQUID_FEC_REP3',
    3: 'LIQUID_FEC_REP5',
    4: 'LIQUID_FEC_HAMMING74',
    5: 'LIQUID_FEC_HAMMING84',
    6: 'LIQUID_FEC_HAMMING128',
    7: 'LIQUID_FEC_GOLAY2412',
    8: 'LIQUID_FEC_SECDED2216',
    9: 'LIQUID_FEC_SECDED3932',
    10: 'LIQUID_FEC_SECDED7264',
    11: 'LIQUID_FEC_CONV_V27',
    12: 'LIQUID_FEC_CONV_V29',
    13: 'LIQUID_FEC_CONV_V39',
    14: 'LIQUID_FEC_CONV_V615',
    15: 'LIQUID_FEC_CONV_V27P23',
    16: 'LIQUID_FEC_CONV_V27P34',
    17: 'LIQUID_FEC_CONV_V27P45',
    18: 'LIQUID_FEC_CONV_V27P56',
    19: 'LIQUID_FEC_CONV_V27P67',
    20: 'LIQUID_FEC_CONV_V27P78',
    21: 'LIQUID_FEC_CONV_V29P23',
    22: 'LIQUID_FEC_CONV_V29P34',
    23: 'LIQUID_FEC_CONV_V29P45',
    24: 'LIQUID_FEC_CONV_V29P56',
    25: 'LIQUID_FEC_CONV_V29P67',
    26: 'LIQUID_FEC_CONV_V29P78',
    27: 'LIQUID_FEC_RS_M8',
}
LIQUID_FEC_UNKNOWN = 0
LIQUID_FEC_NONE = 1
LIQUID_FEC_REP3 = 2
LIQUID_FEC_REP5 = 3
LIQUID_FEC_HAMMING74 = 4
LIQUID_FEC_HAMMING84 = 5
LIQUID_FEC_HAMMING128 = 6
LIQUID_FEC_GOLAY2412 = 7
LIQUID_FEC_SECDED2216 = 8
LIQUID_FEC_SECDED3932 = 9
LIQUID_FEC_SECDED7264 = 10
LIQUID_FEC_CONV_V27 = 11
LIQUID_FEC_CONV_V29 = 12
LIQUID_FEC_CONV_V39 = 13
LIQUID_FEC_CONV_V615 = 14
LIQUID_FEC_CONV_V27P23 = 15
LIQUID_FEC_CONV_V27P34 = 16
LIQUID_FEC_CONV_V27P45 = 17
LIQUID_FEC_CONV_V27P56 = 18
LIQUID_FEC_CONV_V27P67 = 19
LIQUID_FEC_CONV_V27P78 = 20
LIQUID_FEC_CONV_V29P23 = 21
LIQUID_FEC_CONV_V29P34 = 22
LIQUID_FEC_CONV_V29P45 = 23
LIQUID_FEC_CONV_V29P56 = 24
LIQUID_FEC_CONV_V29P67 = 25
LIQUID_FEC_CONV_V29P78 = 26
LIQUID_FEC_RS_M8 = 27
c__EA_fec_scheme = ctypes.c_uint32 # enum
fec_scheme = c__EA_fec_scheme
fec_scheme__enumvalues = c__EA_fec_scheme__enumvalues
fec_scheme_str = [] # Variable ctypes.POINTER(ctypes.c_char) * 2 * 28
liquid_print_fec_schemes = liquiddsp.liquid_print_fec_schemes
liquid_print_fec_schemes.restype = None
liquid_print_fec_schemes.argtypes = []
liquid_getopt_str2fec = liquiddsp.liquid_getopt_str2fec
liquid_getopt_str2fec.restype = fec_scheme
liquid_getopt_str2fec.argtypes = [ctypes.POINTER(ctypes.c_char)]
class struct_fec_s(Structure):
    pass

fec = ctypes.POINTER(struct_fec_s)
fec_get_enc_msg_length = liquiddsp.fec_get_enc_msg_length
fec_get_enc_msg_length.restype = ctypes.c_uint32
fec_get_enc_msg_length.argtypes = [fec_scheme, ctypes.c_uint32]
fec_get_rate = liquiddsp.fec_get_rate
fec_get_rate.restype = ctypes.c_float
fec_get_rate.argtypes = [fec_scheme]
fec_create = liquiddsp.fec_create
fec_create.restype = fec
fec_create.argtypes = [fec_scheme, ctypes.POINTER(None)]
fec_recreate = liquiddsp.fec_recreate
fec_recreate.restype = fec
fec_recreate.argtypes = [fec, fec_scheme, ctypes.POINTER(None)]
fec_destroy = liquiddsp.fec_destroy
fec_destroy.restype = ctypes.c_int32
fec_destroy.argtypes = [fec]
fec_print = liquiddsp.fec_print
fec_print.restype = ctypes.c_int32
fec_print.argtypes = [fec]
fec_encode = liquiddsp.fec_encode
fec_encode.restype = ctypes.c_int32
fec_encode.argtypes = [fec, ctypes.c_uint32, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte)]
fec_decode = liquiddsp.fec_decode
fec_decode.restype = ctypes.c_int32
fec_decode.argtypes = [fec, ctypes.c_uint32, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte)]
fec_decode_soft = liquiddsp.fec_decode_soft
fec_decode_soft.restype = ctypes.c_int32
fec_decode_soft.argtypes = [fec, ctypes.c_uint32, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte)]
packetizer_compute_enc_msg_len = liquiddsp.packetizer_compute_enc_msg_len
packetizer_compute_enc_msg_len.restype = ctypes.c_uint32
packetizer_compute_enc_msg_len.argtypes = [ctypes.c_uint32, ctypes.c_int32, ctypes.c_int32, ctypes.c_int32]
packetizer_compute_dec_msg_len = liquiddsp.packetizer_compute_dec_msg_len
packetizer_compute_dec_msg_len.restype = ctypes.c_uint32
packetizer_compute_dec_msg_len.argtypes = [ctypes.c_uint32, ctypes.c_int32, ctypes.c_int32, ctypes.c_int32]
class struct_packetizer_s(Structure):
    pass

packetizer = ctypes.POINTER(struct_packetizer_s)
packetizer_create = liquiddsp.packetizer_create
packetizer_create.restype = packetizer
packetizer_create.argtypes = [ctypes.c_uint32, ctypes.c_int32, ctypes.c_int32, ctypes.c_int32]
packetizer_recreate = liquiddsp.packetizer_recreate
packetizer_recreate.restype = packetizer
packetizer_recreate.argtypes = [packetizer, ctypes.c_uint32, ctypes.c_int32, ctypes.c_int32, ctypes.c_int32]
packetizer_destroy = liquiddsp.packetizer_destroy
packetizer_destroy.restype = None
packetizer_destroy.argtypes = [packetizer]
packetizer_print = liquiddsp.packetizer_print
packetizer_print.restype = None
packetizer_print.argtypes = [packetizer]
packetizer_get_dec_msg_len = liquiddsp.packetizer_get_dec_msg_len
packetizer_get_dec_msg_len.restype = ctypes.c_uint32
packetizer_get_dec_msg_len.argtypes = [packetizer]
packetizer_get_enc_msg_len = liquiddsp.packetizer_get_enc_msg_len
packetizer_get_enc_msg_len.restype = ctypes.c_uint32
packetizer_get_enc_msg_len.argtypes = [packetizer]
packetizer_get_crc = liquiddsp.packetizer_get_crc
packetizer_get_crc.restype = crc_scheme
packetizer_get_crc.argtypes = [packetizer]
packetizer_get_fec0 = liquiddsp.packetizer_get_fec0
packetizer_get_fec0.restype = fec_scheme
packetizer_get_fec0.argtypes = [packetizer]
packetizer_get_fec1 = liquiddsp.packetizer_get_fec1
packetizer_get_fec1.restype = fec_scheme
packetizer_get_fec1.argtypes = [packetizer]
packetizer_encode = liquiddsp.packetizer_encode
packetizer_encode.restype = None
packetizer_encode.argtypes = [packetizer, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte)]
packetizer_decode = liquiddsp.packetizer_decode
packetizer_decode.restype = ctypes.c_int32
packetizer_decode.argtypes = [packetizer, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte)]
packetizer_decode_soft = liquiddsp.packetizer_decode_soft
packetizer_decode_soft.restype = ctypes.c_int32
packetizer_decode_soft.argtypes = [packetizer, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte)]
class struct_interleaver_s(Structure):
    pass

interleaver = ctypes.POINTER(struct_interleaver_s)
interleaver_create = liquiddsp.interleaver_create
interleaver_create.restype = interleaver
interleaver_create.argtypes = [ctypes.c_uint32]
interleaver_destroy = liquiddsp.interleaver_destroy
interleaver_destroy.restype = None
interleaver_destroy.argtypes = [interleaver]
interleaver_print = liquiddsp.interleaver_print
interleaver_print.restype = None
interleaver_print.argtypes = [interleaver]
interleaver_set_depth = liquiddsp.interleaver_set_depth
interleaver_set_depth.restype = None
interleaver_set_depth.argtypes = [interleaver, ctypes.c_uint32]
interleaver_encode = liquiddsp.interleaver_encode
interleaver_encode.restype = None
interleaver_encode.argtypes = [interleaver, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte)]
interleaver_encode_soft = liquiddsp.interleaver_encode_soft
interleaver_encode_soft.restype = None
interleaver_encode_soft.argtypes = [interleaver, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte)]
interleaver_decode = liquiddsp.interleaver_decode
interleaver_decode.restype = None
interleaver_decode.argtypes = [interleaver, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte)]
interleaver_decode_soft = liquiddsp.interleaver_decode_soft
interleaver_decode_soft.restype = None
interleaver_decode_soft.argtypes = [interleaver, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte)]

# values for enumeration 'c__EA_liquid_fft_type'
c__EA_liquid_fft_type__enumvalues = {
    0: 'LIQUID_FFT_UNKNOWN',
    1: 'LIQUID_FFT_FORWARD',
    -1: 'LIQUID_FFT_BACKWARD',
    10: 'LIQUID_FFT_REDFT00',
    11: 'LIQUID_FFT_REDFT10',
    12: 'LIQUID_FFT_REDFT01',
    13: 'LIQUID_FFT_REDFT11',
    20: 'LIQUID_FFT_RODFT00',
    21: 'LIQUID_FFT_RODFT10',
    22: 'LIQUID_FFT_RODFT01',
    23: 'LIQUID_FFT_RODFT11',
    30: 'LIQUID_FFT_MDCT',
    31: 'LIQUID_FFT_IMDCT',
}
LIQUID_FFT_UNKNOWN = 0
LIQUID_FFT_FORWARD = 1
LIQUID_FFT_BACKWARD = -1
LIQUID_FFT_REDFT00 = 10
LIQUID_FFT_REDFT10 = 11
LIQUID_FFT_REDFT01 = 12
LIQUID_FFT_REDFT11 = 13
LIQUID_FFT_RODFT00 = 20
LIQUID_FFT_RODFT10 = 21
LIQUID_FFT_RODFT01 = 22
LIQUID_FFT_RODFT11 = 23
LIQUID_FFT_MDCT = 30
LIQUID_FFT_IMDCT = 31
c__EA_liquid_fft_type = ctypes.c_int32 # enum
liquid_fft_type = c__EA_liquid_fft_type
liquid_fft_type__enumvalues = c__EA_liquid_fft_type__enumvalues
class struct_fftplan_s(Structure):
    pass

fftplan = ctypes.POINTER(struct_fftplan_s)
fft_create_plan = liquiddsp.fft_create_plan
fft_create_plan.restype = fftplan
fft_create_plan.argtypes = [ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_int32, ctypes.c_int32]
fft_create_plan_r2r_1d = liquiddsp.fft_create_plan_r2r_1d
fft_create_plan_r2r_1d.restype = fftplan
fft_create_plan_r2r_1d.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_int32, ctypes.c_int32]
fft_destroy_plan = liquiddsp.fft_destroy_plan
fft_destroy_plan.restype = ctypes.c_int32
fft_destroy_plan.argtypes = [fftplan]
fft_print_plan = liquiddsp.fft_print_plan
fft_print_plan.restype = ctypes.c_int32
fft_print_plan.argtypes = [fftplan]
fft_execute = liquiddsp.fft_execute
fft_execute.restype = ctypes.c_int32
fft_execute.argtypes = [fftplan]
fft_run = liquiddsp.fft_run
fft_run.restype = ctypes.c_int32
fft_run.argtypes = [ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_int32, ctypes.c_int32]
fft_r2r_1d_run = liquiddsp.fft_r2r_1d_run
fft_r2r_1d_run.restype = ctypes.c_int32
fft_r2r_1d_run.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_int32, ctypes.c_int32]
fft_shift = liquiddsp.fft_shift
fft_shift.restype = ctypes.c_int32
fft_shift.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
class struct_spgramcf_s(Structure):
    pass

spgramcf = ctypes.POINTER(struct_spgramcf_s)
spgramcf_create = liquiddsp.spgramcf_create
spgramcf_create.restype = spgramcf
spgramcf_create.argtypes = [ctypes.c_uint32, ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32]
spgramcf_create_default = liquiddsp.spgramcf_create_default
spgramcf_create_default.restype = spgramcf
spgramcf_create_default.argtypes = [ctypes.c_uint32]
spgramcf_destroy = liquiddsp.spgramcf_destroy
spgramcf_destroy.restype = ctypes.c_int32
spgramcf_destroy.argtypes = [spgramcf]
spgramcf_clear = liquiddsp.spgramcf_clear
spgramcf_clear.restype = ctypes.c_int32
spgramcf_clear.argtypes = [spgramcf]
spgramcf_reset = liquiddsp.spgramcf_reset
spgramcf_reset.restype = ctypes.c_int32
spgramcf_reset.argtypes = [spgramcf]
spgramcf_print = liquiddsp.spgramcf_print
spgramcf_print.restype = ctypes.c_int32
spgramcf_print.argtypes = [spgramcf]
spgramcf_set_alpha = liquiddsp.spgramcf_set_alpha
spgramcf_set_alpha.restype = ctypes.c_int32
spgramcf_set_alpha.argtypes = [spgramcf, ctypes.c_float]
spgramcf_get_alpha = liquiddsp.spgramcf_get_alpha
spgramcf_get_alpha.restype = ctypes.c_float
spgramcf_get_alpha.argtypes = [spgramcf]
spgramcf_set_freq = liquiddsp.spgramcf_set_freq
spgramcf_set_freq.restype = ctypes.c_int32
spgramcf_set_freq.argtypes = [spgramcf, ctypes.c_float]
spgramcf_set_rate = liquiddsp.spgramcf_set_rate
spgramcf_set_rate.restype = ctypes.c_int32
spgramcf_set_rate.argtypes = [spgramcf, ctypes.c_float]
spgramcf_get_nfft = liquiddsp.spgramcf_get_nfft
spgramcf_get_nfft.restype = ctypes.c_uint32
spgramcf_get_nfft.argtypes = [spgramcf]
spgramcf_get_window_len = liquiddsp.spgramcf_get_window_len
spgramcf_get_window_len.restype = ctypes.c_uint32
spgramcf_get_window_len.argtypes = [spgramcf]
spgramcf_get_delay = liquiddsp.spgramcf_get_delay
spgramcf_get_delay.restype = ctypes.c_uint32
spgramcf_get_delay.argtypes = [spgramcf]
spgramcf_get_wtype = liquiddsp.spgramcf_get_wtype
spgramcf_get_wtype.restype = ctypes.c_int32
spgramcf_get_wtype.argtypes = [spgramcf]
spgramcf_get_num_samples = liquiddsp.spgramcf_get_num_samples
spgramcf_get_num_samples.restype = ctypes.c_uint64
spgramcf_get_num_samples.argtypes = [spgramcf]
spgramcf_get_num_samples_total = liquiddsp.spgramcf_get_num_samples_total
spgramcf_get_num_samples_total.restype = ctypes.c_uint64
spgramcf_get_num_samples_total.argtypes = [spgramcf]
spgramcf_get_num_transforms = liquiddsp.spgramcf_get_num_transforms
spgramcf_get_num_transforms.restype = ctypes.c_uint64
spgramcf_get_num_transforms.argtypes = [spgramcf]
spgramcf_get_num_transforms_total = liquiddsp.spgramcf_get_num_transforms_total
spgramcf_get_num_transforms_total.restype = ctypes.c_uint64
spgramcf_get_num_transforms_total.argtypes = [spgramcf]
spgramcf_push = liquiddsp.spgramcf_push
spgramcf_push.restype = ctypes.c_int32
spgramcf_push.argtypes = [spgramcf, liquid_float_complex]
spgramcf_write = liquiddsp.spgramcf_write
spgramcf_write.restype = ctypes.c_int32
spgramcf_write.argtypes = [spgramcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
spgramcf_get_psd_mag = liquiddsp.spgramcf_get_psd_mag
spgramcf_get_psd_mag.restype = ctypes.c_int32
spgramcf_get_psd_mag.argtypes = [spgramcf, ctypes.POINTER(ctypes.c_float)]
spgramcf_get_psd = liquiddsp.spgramcf_get_psd
spgramcf_get_psd.restype = ctypes.c_int32
spgramcf_get_psd.argtypes = [spgramcf, ctypes.POINTER(ctypes.c_float)]
spgramcf_export_gnuplot = liquiddsp.spgramcf_export_gnuplot
spgramcf_export_gnuplot.restype = ctypes.c_int32
spgramcf_export_gnuplot.argtypes = [spgramcf, ctypes.POINTER(ctypes.c_char)]
spgramcf_estimate_psd = liquiddsp.spgramcf_estimate_psd
spgramcf_estimate_psd.restype = ctypes.c_int32
spgramcf_estimate_psd.argtypes = [ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
class struct_spgramf_s(Structure):
    pass

spgramf = ctypes.POINTER(struct_spgramf_s)
spgramf_create = liquiddsp.spgramf_create
spgramf_create.restype = spgramf
spgramf_create.argtypes = [ctypes.c_uint32, ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32]
spgramf_create_default = liquiddsp.spgramf_create_default
spgramf_create_default.restype = spgramf
spgramf_create_default.argtypes = [ctypes.c_uint32]
spgramf_destroy = liquiddsp.spgramf_destroy
spgramf_destroy.restype = ctypes.c_int32
spgramf_destroy.argtypes = [spgramf]
spgramf_clear = liquiddsp.spgramf_clear
spgramf_clear.restype = ctypes.c_int32
spgramf_clear.argtypes = [spgramf]
spgramf_reset = liquiddsp.spgramf_reset
spgramf_reset.restype = ctypes.c_int32
spgramf_reset.argtypes = [spgramf]
spgramf_print = liquiddsp.spgramf_print
spgramf_print.restype = ctypes.c_int32
spgramf_print.argtypes = [spgramf]
spgramf_set_alpha = liquiddsp.spgramf_set_alpha
spgramf_set_alpha.restype = ctypes.c_int32
spgramf_set_alpha.argtypes = [spgramf, ctypes.c_float]
spgramf_get_alpha = liquiddsp.spgramf_get_alpha
spgramf_get_alpha.restype = ctypes.c_float
spgramf_get_alpha.argtypes = [spgramf]
spgramf_set_freq = liquiddsp.spgramf_set_freq
spgramf_set_freq.restype = ctypes.c_int32
spgramf_set_freq.argtypes = [spgramf, ctypes.c_float]
spgramf_set_rate = liquiddsp.spgramf_set_rate
spgramf_set_rate.restype = ctypes.c_int32
spgramf_set_rate.argtypes = [spgramf, ctypes.c_float]
spgramf_get_nfft = liquiddsp.spgramf_get_nfft
spgramf_get_nfft.restype = ctypes.c_uint32
spgramf_get_nfft.argtypes = [spgramf]
spgramf_get_window_len = liquiddsp.spgramf_get_window_len
spgramf_get_window_len.restype = ctypes.c_uint32
spgramf_get_window_len.argtypes = [spgramf]
spgramf_get_delay = liquiddsp.spgramf_get_delay
spgramf_get_delay.restype = ctypes.c_uint32
spgramf_get_delay.argtypes = [spgramf]
spgramf_get_wtype = liquiddsp.spgramf_get_wtype
spgramf_get_wtype.restype = ctypes.c_int32
spgramf_get_wtype.argtypes = [spgramf]
spgramf_get_num_samples = liquiddsp.spgramf_get_num_samples
spgramf_get_num_samples.restype = ctypes.c_uint64
spgramf_get_num_samples.argtypes = [spgramf]
spgramf_get_num_samples_total = liquiddsp.spgramf_get_num_samples_total
spgramf_get_num_samples_total.restype = ctypes.c_uint64
spgramf_get_num_samples_total.argtypes = [spgramf]
spgramf_get_num_transforms = liquiddsp.spgramf_get_num_transforms
spgramf_get_num_transforms.restype = ctypes.c_uint64
spgramf_get_num_transforms.argtypes = [spgramf]
spgramf_get_num_transforms_total = liquiddsp.spgramf_get_num_transforms_total
spgramf_get_num_transforms_total.restype = ctypes.c_uint64
spgramf_get_num_transforms_total.argtypes = [spgramf]
spgramf_push = liquiddsp.spgramf_push
spgramf_push.restype = ctypes.c_int32
spgramf_push.argtypes = [spgramf, ctypes.c_float]
spgramf_write = liquiddsp.spgramf_write
spgramf_write.restype = ctypes.c_int32
spgramf_write.argtypes = [spgramf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
spgramf_get_psd_mag = liquiddsp.spgramf_get_psd_mag
spgramf_get_psd_mag.restype = ctypes.c_int32
spgramf_get_psd_mag.argtypes = [spgramf, ctypes.POINTER(ctypes.c_float)]
spgramf_get_psd = liquiddsp.spgramf_get_psd
spgramf_get_psd.restype = ctypes.c_int32
spgramf_get_psd.argtypes = [spgramf, ctypes.POINTER(ctypes.c_float)]
spgramf_export_gnuplot = liquiddsp.spgramf_export_gnuplot
spgramf_export_gnuplot.restype = ctypes.c_int32
spgramf_export_gnuplot.argtypes = [spgramf, ctypes.POINTER(ctypes.c_char)]
spgramf_estimate_psd = liquiddsp.spgramf_estimate_psd
spgramf_estimate_psd.restype = ctypes.c_int32
spgramf_estimate_psd.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
class struct_asgramcf_s(Structure):
    pass

asgramcf = ctypes.POINTER(struct_asgramcf_s)
asgramcf_create = liquiddsp.asgramcf_create
asgramcf_create.restype = asgramcf
asgramcf_create.argtypes = [ctypes.c_uint32]
asgramcf_destroy = liquiddsp.asgramcf_destroy
asgramcf_destroy.restype = ctypes.c_int32
asgramcf_destroy.argtypes = [asgramcf]
asgramcf_reset = liquiddsp.asgramcf_reset
asgramcf_reset.restype = ctypes.c_int32
asgramcf_reset.argtypes = [asgramcf]
asgramcf_set_scale = liquiddsp.asgramcf_set_scale
asgramcf_set_scale.restype = ctypes.c_int32
asgramcf_set_scale.argtypes = [asgramcf, ctypes.c_float, ctypes.c_float]
asgramcf_set_display = liquiddsp.asgramcf_set_display
asgramcf_set_display.restype = ctypes.c_int32
asgramcf_set_display.argtypes = [asgramcf, ctypes.POINTER(ctypes.c_char)]
asgramcf_push = liquiddsp.asgramcf_push
asgramcf_push.restype = ctypes.c_int32
asgramcf_push.argtypes = [asgramcf, liquid_float_complex]
asgramcf_write = liquiddsp.asgramcf_write
asgramcf_write.restype = ctypes.c_int32
asgramcf_write.argtypes = [asgramcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
asgramcf_execute = liquiddsp.asgramcf_execute
asgramcf_execute.restype = ctypes.c_int32
asgramcf_execute.argtypes = [asgramcf, ctypes.POINTER(ctypes.c_char), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
asgramcf_print = liquiddsp.asgramcf_print
asgramcf_print.restype = ctypes.c_int32
asgramcf_print.argtypes = [asgramcf]
class struct_asgramf_s(Structure):
    pass

asgramf = ctypes.POINTER(struct_asgramf_s)
asgramf_create = liquiddsp.asgramf_create
asgramf_create.restype = asgramf
asgramf_create.argtypes = [ctypes.c_uint32]
asgramf_destroy = liquiddsp.asgramf_destroy
asgramf_destroy.restype = ctypes.c_int32
asgramf_destroy.argtypes = [asgramf]
asgramf_reset = liquiddsp.asgramf_reset
asgramf_reset.restype = ctypes.c_int32
asgramf_reset.argtypes = [asgramf]
asgramf_set_scale = liquiddsp.asgramf_set_scale
asgramf_set_scale.restype = ctypes.c_int32
asgramf_set_scale.argtypes = [asgramf, ctypes.c_float, ctypes.c_float]
asgramf_set_display = liquiddsp.asgramf_set_display
asgramf_set_display.restype = ctypes.c_int32
asgramf_set_display.argtypes = [asgramf, ctypes.POINTER(ctypes.c_char)]
asgramf_push = liquiddsp.asgramf_push
asgramf_push.restype = ctypes.c_int32
asgramf_push.argtypes = [asgramf, ctypes.c_float]
asgramf_write = liquiddsp.asgramf_write
asgramf_write.restype = ctypes.c_int32
asgramf_write.argtypes = [asgramf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
asgramf_execute = liquiddsp.asgramf_execute
asgramf_execute.restype = ctypes.c_int32
asgramf_execute.argtypes = [asgramf, ctypes.POINTER(ctypes.c_char), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
asgramf_print = liquiddsp.asgramf_print
asgramf_print.restype = ctypes.c_int32
asgramf_print.argtypes = [asgramf]
class struct_spwaterfallcf_s(Structure):
    pass

spwaterfallcf = ctypes.POINTER(struct_spwaterfallcf_s)
spwaterfallcf_create = liquiddsp.spwaterfallcf_create
spwaterfallcf_create.restype = spwaterfallcf
spwaterfallcf_create.argtypes = [ctypes.c_uint32, ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
spwaterfallcf_create_default = liquiddsp.spwaterfallcf_create_default
spwaterfallcf_create_default.restype = spwaterfallcf
spwaterfallcf_create_default.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
spwaterfallcf_destroy = liquiddsp.spwaterfallcf_destroy
spwaterfallcf_destroy.restype = ctypes.c_int32
spwaterfallcf_destroy.argtypes = [spwaterfallcf]
spwaterfallcf_clear = liquiddsp.spwaterfallcf_clear
spwaterfallcf_clear.restype = ctypes.c_int32
spwaterfallcf_clear.argtypes = [spwaterfallcf]
spwaterfallcf_reset = liquiddsp.spwaterfallcf_reset
spwaterfallcf_reset.restype = ctypes.c_int32
spwaterfallcf_reset.argtypes = [spwaterfallcf]
spwaterfallcf_print = liquiddsp.spwaterfallcf_print
spwaterfallcf_print.restype = ctypes.c_int32
spwaterfallcf_print.argtypes = [spwaterfallcf]
uint64_t = ctypes.c_uint64
spwaterfallcf_get_num_samples_total = liquiddsp.spwaterfallcf_get_num_samples_total
spwaterfallcf_get_num_samples_total.restype = uint64_t
spwaterfallcf_get_num_samples_total.argtypes = [spwaterfallcf]
spwaterfallcf_get_num_freq = liquiddsp.spwaterfallcf_get_num_freq
spwaterfallcf_get_num_freq.restype = ctypes.c_uint32
spwaterfallcf_get_num_freq.argtypes = [spwaterfallcf]
spwaterfallcf_get_num_time = liquiddsp.spwaterfallcf_get_num_time
spwaterfallcf_get_num_time.restype = ctypes.c_uint32
spwaterfallcf_get_num_time.argtypes = [spwaterfallcf]
spwaterfallcf_get_window_len = liquiddsp.spwaterfallcf_get_window_len
spwaterfallcf_get_window_len.restype = ctypes.c_uint32
spwaterfallcf_get_window_len.argtypes = [spwaterfallcf]
spwaterfallcf_get_delay = liquiddsp.spwaterfallcf_get_delay
spwaterfallcf_get_delay.restype = ctypes.c_uint32
spwaterfallcf_get_delay.argtypes = [spwaterfallcf]
spwaterfallcf_get_wtype = liquiddsp.spwaterfallcf_get_wtype
spwaterfallcf_get_wtype.restype = ctypes.c_int32
spwaterfallcf_get_wtype.argtypes = [spwaterfallcf]
spwaterfallcf_get_psd = liquiddsp.spwaterfallcf_get_psd
spwaterfallcf_get_psd.restype = ctypes.POINTER(ctypes.c_float)
spwaterfallcf_get_psd.argtypes = [spwaterfallcf]
spwaterfallcf_set_freq = liquiddsp.spwaterfallcf_set_freq
spwaterfallcf_set_freq.restype = ctypes.c_int32
spwaterfallcf_set_freq.argtypes = [spwaterfallcf, ctypes.c_float]
spwaterfallcf_set_rate = liquiddsp.spwaterfallcf_set_rate
spwaterfallcf_set_rate.restype = ctypes.c_int32
spwaterfallcf_set_rate.argtypes = [spwaterfallcf, ctypes.c_float]
spwaterfallcf_set_dims = liquiddsp.spwaterfallcf_set_dims
spwaterfallcf_set_dims.restype = ctypes.c_int32
spwaterfallcf_set_dims.argtypes = [spwaterfallcf, ctypes.c_uint32, ctypes.c_uint32]
spwaterfallcf_set_commands = liquiddsp.spwaterfallcf_set_commands
spwaterfallcf_set_commands.restype = ctypes.c_int32
spwaterfallcf_set_commands.argtypes = [spwaterfallcf, ctypes.POINTER(ctypes.c_char)]
spwaterfallcf_push = liquiddsp.spwaterfallcf_push
spwaterfallcf_push.restype = ctypes.c_int32
spwaterfallcf_push.argtypes = [spwaterfallcf, liquid_float_complex]
spwaterfallcf_write = liquiddsp.spwaterfallcf_write
spwaterfallcf_write.restype = ctypes.c_int32
spwaterfallcf_write.argtypes = [spwaterfallcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
spwaterfallcf_export = liquiddsp.spwaterfallcf_export
spwaterfallcf_export.restype = ctypes.c_int32
spwaterfallcf_export.argtypes = [spwaterfallcf, ctypes.POINTER(ctypes.c_char)]
class struct_spwaterfallf_s(Structure):
    pass

spwaterfallf = ctypes.POINTER(struct_spwaterfallf_s)
spwaterfallf_create = liquiddsp.spwaterfallf_create
spwaterfallf_create.restype = spwaterfallf
spwaterfallf_create.argtypes = [ctypes.c_uint32, ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
spwaterfallf_create_default = liquiddsp.spwaterfallf_create_default
spwaterfallf_create_default.restype = spwaterfallf
spwaterfallf_create_default.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
spwaterfallf_destroy = liquiddsp.spwaterfallf_destroy
spwaterfallf_destroy.restype = ctypes.c_int32
spwaterfallf_destroy.argtypes = [spwaterfallf]
spwaterfallf_clear = liquiddsp.spwaterfallf_clear
spwaterfallf_clear.restype = ctypes.c_int32
spwaterfallf_clear.argtypes = [spwaterfallf]
spwaterfallf_reset = liquiddsp.spwaterfallf_reset
spwaterfallf_reset.restype = ctypes.c_int32
spwaterfallf_reset.argtypes = [spwaterfallf]
spwaterfallf_print = liquiddsp.spwaterfallf_print
spwaterfallf_print.restype = ctypes.c_int32
spwaterfallf_print.argtypes = [spwaterfallf]
spwaterfallf_get_num_samples_total = liquiddsp.spwaterfallf_get_num_samples_total
spwaterfallf_get_num_samples_total.restype = uint64_t
spwaterfallf_get_num_samples_total.argtypes = [spwaterfallf]
spwaterfallf_get_num_freq = liquiddsp.spwaterfallf_get_num_freq
spwaterfallf_get_num_freq.restype = ctypes.c_uint32
spwaterfallf_get_num_freq.argtypes = [spwaterfallf]
spwaterfallf_get_num_time = liquiddsp.spwaterfallf_get_num_time
spwaterfallf_get_num_time.restype = ctypes.c_uint32
spwaterfallf_get_num_time.argtypes = [spwaterfallf]
spwaterfallf_get_window_len = liquiddsp.spwaterfallf_get_window_len
spwaterfallf_get_window_len.restype = ctypes.c_uint32
spwaterfallf_get_window_len.argtypes = [spwaterfallf]
spwaterfallf_get_delay = liquiddsp.spwaterfallf_get_delay
spwaterfallf_get_delay.restype = ctypes.c_uint32
spwaterfallf_get_delay.argtypes = [spwaterfallf]
spwaterfallf_get_wtype = liquiddsp.spwaterfallf_get_wtype
spwaterfallf_get_wtype.restype = ctypes.c_int32
spwaterfallf_get_wtype.argtypes = [spwaterfallf]
spwaterfallf_get_psd = liquiddsp.spwaterfallf_get_psd
spwaterfallf_get_psd.restype = ctypes.POINTER(ctypes.c_float)
spwaterfallf_get_psd.argtypes = [spwaterfallf]
spwaterfallf_set_freq = liquiddsp.spwaterfallf_set_freq
spwaterfallf_set_freq.restype = ctypes.c_int32
spwaterfallf_set_freq.argtypes = [spwaterfallf, ctypes.c_float]
spwaterfallf_set_rate = liquiddsp.spwaterfallf_set_rate
spwaterfallf_set_rate.restype = ctypes.c_int32
spwaterfallf_set_rate.argtypes = [spwaterfallf, ctypes.c_float]
spwaterfallf_set_dims = liquiddsp.spwaterfallf_set_dims
spwaterfallf_set_dims.restype = ctypes.c_int32
spwaterfallf_set_dims.argtypes = [spwaterfallf, ctypes.c_uint32, ctypes.c_uint32]
spwaterfallf_set_commands = liquiddsp.spwaterfallf_set_commands
spwaterfallf_set_commands.restype = ctypes.c_int32
spwaterfallf_set_commands.argtypes = [spwaterfallf, ctypes.POINTER(ctypes.c_char)]
spwaterfallf_push = liquiddsp.spwaterfallf_push
spwaterfallf_push.restype = ctypes.c_int32
spwaterfallf_push.argtypes = [spwaterfallf, ctypes.c_float]
spwaterfallf_write = liquiddsp.spwaterfallf_write
spwaterfallf_write.restype = ctypes.c_int32
spwaterfallf_write.argtypes = [spwaterfallf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
spwaterfallf_export = liquiddsp.spwaterfallf_export
spwaterfallf_export.restype = ctypes.c_int32
spwaterfallf_export.argtypes = [spwaterfallf, ctypes.POINTER(ctypes.c_char)]

# values for enumeration 'c__EA_liquid_firfilt_type'
c__EA_liquid_firfilt_type__enumvalues = {
    0: 'LIQUID_FIRFILT_UNKNOWN',
    1: 'LIQUID_FIRFILT_KAISER',
    2: 'LIQUID_FIRFILT_PM',
    3: 'LIQUID_FIRFILT_RCOS',
    4: 'LIQUID_FIRFILT_FEXP',
    5: 'LIQUID_FIRFILT_FSECH',
    6: 'LIQUID_FIRFILT_FARCSECH',
    7: 'LIQUID_FIRFILT_ARKAISER',
    8: 'LIQUID_FIRFILT_RKAISER',
    9: 'LIQUID_FIRFILT_RRC',
    10: 'LIQUID_FIRFILT_hM3',
    11: 'LIQUID_FIRFILT_GMSKTX',
    12: 'LIQUID_FIRFILT_GMSKRX',
    13: 'LIQUID_FIRFILT_RFEXP',
    14: 'LIQUID_FIRFILT_RFSECH',
    15: 'LIQUID_FIRFILT_RFARCSECH',
}
LIQUID_FIRFILT_UNKNOWN = 0
LIQUID_FIRFILT_KAISER = 1
LIQUID_FIRFILT_PM = 2
LIQUID_FIRFILT_RCOS = 3
LIQUID_FIRFILT_FEXP = 4
LIQUID_FIRFILT_FSECH = 5
LIQUID_FIRFILT_FARCSECH = 6
LIQUID_FIRFILT_ARKAISER = 7
LIQUID_FIRFILT_RKAISER = 8
LIQUID_FIRFILT_RRC = 9
LIQUID_FIRFILT_hM3 = 10
LIQUID_FIRFILT_GMSKTX = 11
LIQUID_FIRFILT_GMSKRX = 12
LIQUID_FIRFILT_RFEXP = 13
LIQUID_FIRFILT_RFSECH = 14
LIQUID_FIRFILT_RFARCSECH = 15
c__EA_liquid_firfilt_type = ctypes.c_uint32 # enum
liquid_firfilt_type = c__EA_liquid_firfilt_type
liquid_firfilt_type__enumvalues = c__EA_liquid_firfilt_type__enumvalues
liquid_firdes_prototype = liquiddsp.liquid_firdes_prototype
liquid_firdes_prototype.restype = None
liquid_firdes_prototype.argtypes = [liquid_firfilt_type, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
liquid_firfilt_type_str = [] # Variable ctypes.POINTER(ctypes.c_char) * 2 * 16
liquid_getopt_str2firfilt = liquiddsp.liquid_getopt_str2firfilt
liquid_getopt_str2firfilt.restype = ctypes.c_int32
liquid_getopt_str2firfilt.argtypes = [ctypes.POINTER(ctypes.c_char)]
estimate_req_filter_len = liquiddsp.estimate_req_filter_len
estimate_req_filter_len.restype = ctypes.c_uint32
estimate_req_filter_len.argtypes = [ctypes.c_float, ctypes.c_float]
estimate_req_filter_As = liquiddsp.estimate_req_filter_As
estimate_req_filter_As.restype = ctypes.c_float
estimate_req_filter_As.argtypes = [ctypes.c_float, ctypes.c_uint32]
estimate_req_filter_df = liquiddsp.estimate_req_filter_df
estimate_req_filter_df.restype = ctypes.c_float
estimate_req_filter_df.argtypes = [ctypes.c_float, ctypes.c_uint32]
kaiser_beta_As = liquiddsp.kaiser_beta_As
kaiser_beta_As.restype = ctypes.c_float
kaiser_beta_As.argtypes = [ctypes.c_float]

# values for enumeration 'c__EA_liquid_firdespm_btype'
c__EA_liquid_firdespm_btype__enumvalues = {
    0: 'LIQUID_FIRDESPM_BANDPASS',
    1: 'LIQUID_FIRDESPM_DIFFERENTIATOR',
    2: 'LIQUID_FIRDESPM_HILBERT',
}
LIQUID_FIRDESPM_BANDPASS = 0
LIQUID_FIRDESPM_DIFFERENTIATOR = 1
LIQUID_FIRDESPM_HILBERT = 2
c__EA_liquid_firdespm_btype = ctypes.c_uint32 # enum
liquid_firdespm_btype = c__EA_liquid_firdespm_btype
liquid_firdespm_btype__enumvalues = c__EA_liquid_firdespm_btype__enumvalues

# values for enumeration 'c__EA_liquid_firdespm_wtype'
c__EA_liquid_firdespm_wtype__enumvalues = {
    0: 'LIQUID_FIRDESPM_FLATWEIGHT',
    1: 'LIQUID_FIRDESPM_EXPWEIGHT',
    2: 'LIQUID_FIRDESPM_LINWEIGHT',
}
LIQUID_FIRDESPM_FLATWEIGHT = 0
LIQUID_FIRDESPM_EXPWEIGHT = 1
LIQUID_FIRDESPM_LINWEIGHT = 2
c__EA_liquid_firdespm_wtype = ctypes.c_uint32 # enum
liquid_firdespm_wtype = c__EA_liquid_firdespm_wtype
liquid_firdespm_wtype__enumvalues = c__EA_liquid_firdespm_wtype__enumvalues
firdespm_run = liquiddsp.firdespm_run
firdespm_run.restype = ctypes.c_int32
firdespm_run.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(c__EA_liquid_firdespm_wtype), liquid_firdespm_btype, ctypes.POINTER(ctypes.c_float)]
firdespm_lowpass = liquiddsp.firdespm_lowpass
firdespm_lowpass.restype = ctypes.c_int32
firdespm_lowpass.argtypes = [ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
firdespm_callback = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.c_double, ctypes.POINTER(None), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double))
class struct_firdespm_s(Structure):
    pass

firdespm = ctypes.POINTER(struct_firdespm_s)
firdespm_create = liquiddsp.firdespm_create
firdespm_create.restype = firdespm
firdespm_create.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(c__EA_liquid_firdespm_wtype), liquid_firdespm_btype]
firdespm_create_callback = liquiddsp.firdespm_create_callback
firdespm_create_callback.restype = firdespm
firdespm_create_callback.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), liquid_firdespm_btype, firdespm_callback, ctypes.POINTER(None)]
firdespm_destroy = liquiddsp.firdespm_destroy
firdespm_destroy.restype = ctypes.c_int32
firdespm_destroy.argtypes = [firdespm]
firdespm_print = liquiddsp.firdespm_print
firdespm_print.restype = ctypes.c_int32
firdespm_print.argtypes = [firdespm]
firdespm_execute = liquiddsp.firdespm_execute
firdespm_execute.restype = ctypes.c_int32
firdespm_execute.argtypes = [firdespm, ctypes.POINTER(ctypes.c_float)]
liquid_firdes_kaiser = liquiddsp.liquid_firdes_kaiser
liquid_firdes_kaiser.restype = None
liquid_firdes_kaiser.argtypes = [ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
liquid_firdes_notch = liquiddsp.liquid_firdes_notch
liquid_firdes_notch.restype = None
liquid_firdes_notch.argtypes = [ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
liquid_firdes_doppler = liquiddsp.liquid_firdes_doppler
liquid_firdes_doppler.restype = None
liquid_firdes_doppler.argtypes = [ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
liquid_firdes_rcos = liquiddsp.liquid_firdes_rcos
liquid_firdes_rcos.restype = None
liquid_firdes_rcos.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
liquid_firdes_rrcos = liquiddsp.liquid_firdes_rrcos
liquid_firdes_rrcos.restype = None
liquid_firdes_rrcos.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
liquid_firdes_rkaiser = liquiddsp.liquid_firdes_rkaiser
liquid_firdes_rkaiser.restype = None
liquid_firdes_rkaiser.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
liquid_firdes_arkaiser = liquiddsp.liquid_firdes_arkaiser
liquid_firdes_arkaiser.restype = None
liquid_firdes_arkaiser.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
liquid_firdes_hM3 = liquiddsp.liquid_firdes_hM3
liquid_firdes_hM3.restype = None
liquid_firdes_hM3.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
liquid_firdes_gmsktx = liquiddsp.liquid_firdes_gmsktx
liquid_firdes_gmsktx.restype = None
liquid_firdes_gmsktx.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
liquid_firdes_gmskrx = liquiddsp.liquid_firdes_gmskrx
liquid_firdes_gmskrx.restype = None
liquid_firdes_gmskrx.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
liquid_firdes_fexp = liquiddsp.liquid_firdes_fexp
liquid_firdes_fexp.restype = None
liquid_firdes_fexp.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
liquid_firdes_rfexp = liquiddsp.liquid_firdes_rfexp
liquid_firdes_rfexp.restype = None
liquid_firdes_rfexp.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
liquid_firdes_fsech = liquiddsp.liquid_firdes_fsech
liquid_firdes_fsech.restype = None
liquid_firdes_fsech.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
liquid_firdes_rfsech = liquiddsp.liquid_firdes_rfsech
liquid_firdes_rfsech.restype = None
liquid_firdes_rfsech.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
liquid_firdes_farcsech = liquiddsp.liquid_firdes_farcsech
liquid_firdes_farcsech.restype = None
liquid_firdes_farcsech.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
liquid_firdes_rfarcsech = liquiddsp.liquid_firdes_rfarcsech
liquid_firdes_rfarcsech.restype = None
liquid_firdes_rfarcsech.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
fir_group_delay = liquiddsp.fir_group_delay
fir_group_delay.restype = ctypes.c_float
fir_group_delay.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_float]
iir_group_delay = liquiddsp.iir_group_delay
iir_group_delay.restype = ctypes.c_float
iir_group_delay.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_float]
liquid_filter_autocorr = liquiddsp.liquid_filter_autocorr
liquid_filter_autocorr.restype = ctypes.c_float
liquid_filter_autocorr.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_int32]
liquid_filter_crosscorr = liquiddsp.liquid_filter_crosscorr
liquid_filter_crosscorr.restype = ctypes.c_float
liquid_filter_crosscorr.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_int32]
liquid_filter_isi = liquiddsp.liquid_filter_isi
liquid_filter_isi.restype = None
liquid_filter_isi.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
liquid_filter_energy = liquiddsp.liquid_filter_energy
liquid_filter_energy.restype = ctypes.c_float
liquid_filter_energy.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_float, ctypes.c_uint32]

# values for enumeration 'c__EA_liquid_iirdes_filtertype'
c__EA_liquid_iirdes_filtertype__enumvalues = {
    0: 'LIQUID_IIRDES_BUTTER',
    1: 'LIQUID_IIRDES_CHEBY1',
    2: 'LIQUID_IIRDES_CHEBY2',
    3: 'LIQUID_IIRDES_ELLIP',
    4: 'LIQUID_IIRDES_BESSEL',
}
LIQUID_IIRDES_BUTTER = 0
LIQUID_IIRDES_CHEBY1 = 1
LIQUID_IIRDES_CHEBY2 = 2
LIQUID_IIRDES_ELLIP = 3
LIQUID_IIRDES_BESSEL = 4
c__EA_liquid_iirdes_filtertype = ctypes.c_uint32 # enum
liquid_iirdes_filtertype = c__EA_liquid_iirdes_filtertype
liquid_iirdes_filtertype__enumvalues = c__EA_liquid_iirdes_filtertype__enumvalues

# values for enumeration 'c__EA_liquid_iirdes_bandtype'
c__EA_liquid_iirdes_bandtype__enumvalues = {
    0: 'LIQUID_IIRDES_LOWPASS',
    1: 'LIQUID_IIRDES_HIGHPASS',
    2: 'LIQUID_IIRDES_BANDPASS',
    3: 'LIQUID_IIRDES_BANDSTOP',
}
LIQUID_IIRDES_LOWPASS = 0
LIQUID_IIRDES_HIGHPASS = 1
LIQUID_IIRDES_BANDPASS = 2
LIQUID_IIRDES_BANDSTOP = 3
c__EA_liquid_iirdes_bandtype = ctypes.c_uint32 # enum
liquid_iirdes_bandtype = c__EA_liquid_iirdes_bandtype
liquid_iirdes_bandtype__enumvalues = c__EA_liquid_iirdes_bandtype__enumvalues

# values for enumeration 'c__EA_liquid_iirdes_format'
c__EA_liquid_iirdes_format__enumvalues = {
    0: 'LIQUID_IIRDES_SOS',
    1: 'LIQUID_IIRDES_TF',
}
LIQUID_IIRDES_SOS = 0
LIQUID_IIRDES_TF = 1
c__EA_liquid_iirdes_format = ctypes.c_uint32 # enum
liquid_iirdes_format = c__EA_liquid_iirdes_format
liquid_iirdes_format__enumvalues = c__EA_liquid_iirdes_format__enumvalues
liquid_iirdes = liquiddsp.liquid_iirdes
liquid_iirdes.restype = None
liquid_iirdes.argtypes = [liquid_iirdes_filtertype, liquid_iirdes_bandtype, liquid_iirdes_format, ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
butter_azpkf = liquiddsp.butter_azpkf
butter_azpkf.restype = None
butter_azpkf.argtypes = [ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
cheby1_azpkf = liquiddsp.cheby1_azpkf
cheby1_azpkf.restype = None
cheby1_azpkf.argtypes = [ctypes.c_uint32, ctypes.c_float, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
cheby2_azpkf = liquiddsp.cheby2_azpkf
cheby2_azpkf.restype = None
cheby2_azpkf.argtypes = [ctypes.c_uint32, ctypes.c_float, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
ellip_azpkf = liquiddsp.ellip_azpkf
ellip_azpkf.restype = None
ellip_azpkf.argtypes = [ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
bessel_azpkf = liquiddsp.bessel_azpkf
bessel_azpkf.restype = None
bessel_azpkf.argtypes = [ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
iirdes_freqprewarp = liquiddsp.iirdes_freqprewarp
iirdes_freqprewarp.restype = ctypes.c_float
iirdes_freqprewarp.argtypes = [liquid_iirdes_bandtype, ctypes.c_float, ctypes.c_float]
bilinear_zpkf = liquiddsp.bilinear_zpkf
bilinear_zpkf.restype = None
bilinear_zpkf.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, liquid_float_complex, ctypes.c_float, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
iirdes_dzpk_lp2hp = liquiddsp.iirdes_dzpk_lp2hp
iirdes_dzpk_lp2hp.restype = None
iirdes_dzpk_lp2hp.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
iirdes_dzpk_lp2bp = liquiddsp.iirdes_dzpk_lp2bp
iirdes_dzpk_lp2bp.restype = None
iirdes_dzpk_lp2bp.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_float, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
iirdes_dzpk2tff = liquiddsp.iirdes_dzpk2tff
iirdes_dzpk2tff.restype = None
iirdes_dzpk2tff.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, liquid_float_complex, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
iirdes_dzpk2sosf = liquiddsp.iirdes_dzpk2sosf
iirdes_dzpk2sosf.restype = None
iirdes_dzpk2sosf.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, liquid_float_complex, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
iirdes_pll_active_lag = liquiddsp.iirdes_pll_active_lag
iirdes_pll_active_lag.restype = None
iirdes_pll_active_lag.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
iirdes_pll_active_PI = liquiddsp.iirdes_pll_active_PI
iirdes_pll_active_PI.restype = None
iirdes_pll_active_PI.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
iirdes_isstable = liquiddsp.iirdes_isstable
iirdes_isstable.restype = ctypes.c_int32
iirdes_isstable.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
liquid_lpc = liquiddsp.liquid_lpc
liquid_lpc.restype = None
liquid_lpc.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
liquid_levinson = liquiddsp.liquid_levinson
liquid_levinson.restype = None
liquid_levinson.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
class struct_autocorr_cccf_s(Structure):
    pass

autocorr_cccf = ctypes.POINTER(struct_autocorr_cccf_s)
autocorr_cccf_create = liquiddsp.autocorr_cccf_create
autocorr_cccf_create.restype = autocorr_cccf
autocorr_cccf_create.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
autocorr_cccf_destroy = liquiddsp.autocorr_cccf_destroy
autocorr_cccf_destroy.restype = None
autocorr_cccf_destroy.argtypes = [autocorr_cccf]
autocorr_cccf_reset = liquiddsp.autocorr_cccf_reset
autocorr_cccf_reset.restype = None
autocorr_cccf_reset.argtypes = [autocorr_cccf]
autocorr_cccf_print = liquiddsp.autocorr_cccf_print
autocorr_cccf_print.restype = None
autocorr_cccf_print.argtypes = [autocorr_cccf]
autocorr_cccf_push = liquiddsp.autocorr_cccf_push
autocorr_cccf_push.restype = None
autocorr_cccf_push.argtypes = [autocorr_cccf, liquid_float_complex]
autocorr_cccf_write = liquiddsp.autocorr_cccf_write
autocorr_cccf_write.restype = None
autocorr_cccf_write.argtypes = [autocorr_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
autocorr_cccf_execute = liquiddsp.autocorr_cccf_execute
autocorr_cccf_execute.restype = None
autocorr_cccf_execute.argtypes = [autocorr_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
autocorr_cccf_execute_block = liquiddsp.autocorr_cccf_execute_block
autocorr_cccf_execute_block.restype = None
autocorr_cccf_execute_block.argtypes = [autocorr_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
autocorr_cccf_get_energy = liquiddsp.autocorr_cccf_get_energy
autocorr_cccf_get_energy.restype = ctypes.c_float
autocorr_cccf_get_energy.argtypes = [autocorr_cccf]
class struct_autocorr_rrrf_s(Structure):
    pass

autocorr_rrrf = ctypes.POINTER(struct_autocorr_rrrf_s)
autocorr_rrrf_create = liquiddsp.autocorr_rrrf_create
autocorr_rrrf_create.restype = autocorr_rrrf
autocorr_rrrf_create.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
autocorr_rrrf_destroy = liquiddsp.autocorr_rrrf_destroy
autocorr_rrrf_destroy.restype = None
autocorr_rrrf_destroy.argtypes = [autocorr_rrrf]
autocorr_rrrf_reset = liquiddsp.autocorr_rrrf_reset
autocorr_rrrf_reset.restype = None
autocorr_rrrf_reset.argtypes = [autocorr_rrrf]
autocorr_rrrf_print = liquiddsp.autocorr_rrrf_print
autocorr_rrrf_print.restype = None
autocorr_rrrf_print.argtypes = [autocorr_rrrf]
autocorr_rrrf_push = liquiddsp.autocorr_rrrf_push
autocorr_rrrf_push.restype = None
autocorr_rrrf_push.argtypes = [autocorr_rrrf, ctypes.c_float]
autocorr_rrrf_write = liquiddsp.autocorr_rrrf_write
autocorr_rrrf_write.restype = None
autocorr_rrrf_write.argtypes = [autocorr_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
autocorr_rrrf_execute = liquiddsp.autocorr_rrrf_execute
autocorr_rrrf_execute.restype = None
autocorr_rrrf_execute.argtypes = [autocorr_rrrf, ctypes.POINTER(ctypes.c_float)]
autocorr_rrrf_execute_block = liquiddsp.autocorr_rrrf_execute_block
autocorr_rrrf_execute_block.restype = None
autocorr_rrrf_execute_block.argtypes = [autocorr_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
autocorr_rrrf_get_energy = liquiddsp.autocorr_rrrf_get_energy
autocorr_rrrf_get_energy.restype = ctypes.c_float
autocorr_rrrf_get_energy.argtypes = [autocorr_rrrf]
class struct_firfilt_rrrf_s(Structure):
    pass

firfilt_rrrf = ctypes.POINTER(struct_firfilt_rrrf_s)
firfilt_rrrf_create = liquiddsp.firfilt_rrrf_create
firfilt_rrrf_create.restype = firfilt_rrrf
firfilt_rrrf_create.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
firfilt_rrrf_create_kaiser = liquiddsp.firfilt_rrrf_create_kaiser
firfilt_rrrf_create_kaiser.restype = firfilt_rrrf
firfilt_rrrf_create_kaiser.argtypes = [ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.c_float]
firfilt_rrrf_create_rnyquist = liquiddsp.firfilt_rrrf_create_rnyquist
firfilt_rrrf_create_rnyquist.restype = firfilt_rrrf
firfilt_rrrf_create_rnyquist.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
firfilt_rrrf_create_firdespm = liquiddsp.firfilt_rrrf_create_firdespm
firfilt_rrrf_create_firdespm.restype = firfilt_rrrf
firfilt_rrrf_create_firdespm.argtypes = [ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
firfilt_rrrf_create_rect = liquiddsp.firfilt_rrrf_create_rect
firfilt_rrrf_create_rect.restype = firfilt_rrrf
firfilt_rrrf_create_rect.argtypes = [ctypes.c_uint32]
firfilt_rrrf_create_dc_blocker = liquiddsp.firfilt_rrrf_create_dc_blocker
firfilt_rrrf_create_dc_blocker.restype = firfilt_rrrf
firfilt_rrrf_create_dc_blocker.argtypes = [ctypes.c_uint32, ctypes.c_float]
firfilt_rrrf_create_notch = liquiddsp.firfilt_rrrf_create_notch
firfilt_rrrf_create_notch.restype = firfilt_rrrf
firfilt_rrrf_create_notch.argtypes = [ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
firfilt_rrrf_recreate = liquiddsp.firfilt_rrrf_recreate
firfilt_rrrf_recreate.restype = firfilt_rrrf
firfilt_rrrf_recreate.argtypes = [firfilt_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
firfilt_rrrf_destroy = liquiddsp.firfilt_rrrf_destroy
firfilt_rrrf_destroy.restype = None
firfilt_rrrf_destroy.argtypes = [firfilt_rrrf]
firfilt_rrrf_reset = liquiddsp.firfilt_rrrf_reset
firfilt_rrrf_reset.restype = None
firfilt_rrrf_reset.argtypes = [firfilt_rrrf]
firfilt_rrrf_print = liquiddsp.firfilt_rrrf_print
firfilt_rrrf_print.restype = None
firfilt_rrrf_print.argtypes = [firfilt_rrrf]
firfilt_rrrf_set_scale = liquiddsp.firfilt_rrrf_set_scale
firfilt_rrrf_set_scale.restype = None
firfilt_rrrf_set_scale.argtypes = [firfilt_rrrf, ctypes.c_float]
firfilt_rrrf_get_scale = liquiddsp.firfilt_rrrf_get_scale
firfilt_rrrf_get_scale.restype = None
firfilt_rrrf_get_scale.argtypes = [firfilt_rrrf, ctypes.POINTER(ctypes.c_float)]
firfilt_rrrf_push = liquiddsp.firfilt_rrrf_push
firfilt_rrrf_push.restype = None
firfilt_rrrf_push.argtypes = [firfilt_rrrf, ctypes.c_float]
firfilt_rrrf_write = liquiddsp.firfilt_rrrf_write
firfilt_rrrf_write.restype = None
firfilt_rrrf_write.argtypes = [firfilt_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
firfilt_rrrf_execute = liquiddsp.firfilt_rrrf_execute
firfilt_rrrf_execute.restype = None
firfilt_rrrf_execute.argtypes = [firfilt_rrrf, ctypes.POINTER(ctypes.c_float)]
firfilt_rrrf_execute_block = liquiddsp.firfilt_rrrf_execute_block
firfilt_rrrf_execute_block.restype = None
firfilt_rrrf_execute_block.argtypes = [firfilt_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
firfilt_rrrf_get_length = liquiddsp.firfilt_rrrf_get_length
firfilt_rrrf_get_length.restype = ctypes.c_uint32
firfilt_rrrf_get_length.argtypes = [firfilt_rrrf]
firfilt_rrrf_get_coefficients = liquiddsp.firfilt_rrrf_get_coefficients
firfilt_rrrf_get_coefficients.restype = ctypes.c_int32
firfilt_rrrf_get_coefficients.argtypes = [firfilt_rrrf, ctypes.POINTER(ctypes.c_float)]
firfilt_rrrf_freqresponse = liquiddsp.firfilt_rrrf_freqresponse
firfilt_rrrf_freqresponse.restype = None
firfilt_rrrf_freqresponse.argtypes = [firfilt_rrrf, ctypes.c_float, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
firfilt_rrrf_groupdelay = liquiddsp.firfilt_rrrf_groupdelay
firfilt_rrrf_groupdelay.restype = ctypes.c_float
firfilt_rrrf_groupdelay.argtypes = [firfilt_rrrf, ctypes.c_float]
class struct_firfilt_crcf_s(Structure):
    pass

firfilt_crcf = ctypes.POINTER(struct_firfilt_crcf_s)
firfilt_crcf_create = liquiddsp.firfilt_crcf_create
firfilt_crcf_create.restype = firfilt_crcf
firfilt_crcf_create.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
firfilt_crcf_create_kaiser = liquiddsp.firfilt_crcf_create_kaiser
firfilt_crcf_create_kaiser.restype = firfilt_crcf
firfilt_crcf_create_kaiser.argtypes = [ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.c_float]
firfilt_crcf_create_rnyquist = liquiddsp.firfilt_crcf_create_rnyquist
firfilt_crcf_create_rnyquist.restype = firfilt_crcf
firfilt_crcf_create_rnyquist.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
firfilt_crcf_create_firdespm = liquiddsp.firfilt_crcf_create_firdespm
firfilt_crcf_create_firdespm.restype = firfilt_crcf
firfilt_crcf_create_firdespm.argtypes = [ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
firfilt_crcf_create_rect = liquiddsp.firfilt_crcf_create_rect
firfilt_crcf_create_rect.restype = firfilt_crcf
firfilt_crcf_create_rect.argtypes = [ctypes.c_uint32]
firfilt_crcf_create_dc_blocker = liquiddsp.firfilt_crcf_create_dc_blocker
firfilt_crcf_create_dc_blocker.restype = firfilt_crcf
firfilt_crcf_create_dc_blocker.argtypes = [ctypes.c_uint32, ctypes.c_float]
firfilt_crcf_create_notch = liquiddsp.firfilt_crcf_create_notch
firfilt_crcf_create_notch.restype = firfilt_crcf
firfilt_crcf_create_notch.argtypes = [ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
firfilt_crcf_recreate = liquiddsp.firfilt_crcf_recreate
firfilt_crcf_recreate.restype = firfilt_crcf
firfilt_crcf_recreate.argtypes = [firfilt_crcf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
firfilt_crcf_destroy = liquiddsp.firfilt_crcf_destroy
firfilt_crcf_destroy.restype = None
firfilt_crcf_destroy.argtypes = [firfilt_crcf]
firfilt_crcf_reset = liquiddsp.firfilt_crcf_reset
firfilt_crcf_reset.restype = None
firfilt_crcf_reset.argtypes = [firfilt_crcf]
firfilt_crcf_print = liquiddsp.firfilt_crcf_print
firfilt_crcf_print.restype = None
firfilt_crcf_print.argtypes = [firfilt_crcf]
firfilt_crcf_set_scale = liquiddsp.firfilt_crcf_set_scale
firfilt_crcf_set_scale.restype = None
firfilt_crcf_set_scale.argtypes = [firfilt_crcf, ctypes.c_float]
firfilt_crcf_get_scale = liquiddsp.firfilt_crcf_get_scale
firfilt_crcf_get_scale.restype = None
firfilt_crcf_get_scale.argtypes = [firfilt_crcf, ctypes.POINTER(ctypes.c_float)]
firfilt_crcf_push = liquiddsp.firfilt_crcf_push
firfilt_crcf_push.restype = None
firfilt_crcf_push.argtypes = [firfilt_crcf, liquid_float_complex]
firfilt_crcf_write = liquiddsp.firfilt_crcf_write
firfilt_crcf_write.restype = None
firfilt_crcf_write.argtypes = [firfilt_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
firfilt_crcf_execute = liquiddsp.firfilt_crcf_execute
firfilt_crcf_execute.restype = None
firfilt_crcf_execute.argtypes = [firfilt_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
firfilt_crcf_execute_block = liquiddsp.firfilt_crcf_execute_block
firfilt_crcf_execute_block.restype = None
firfilt_crcf_execute_block.argtypes = [firfilt_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
firfilt_crcf_get_length = liquiddsp.firfilt_crcf_get_length
firfilt_crcf_get_length.restype = ctypes.c_uint32
firfilt_crcf_get_length.argtypes = [firfilt_crcf]
firfilt_crcf_get_coefficients = liquiddsp.firfilt_crcf_get_coefficients
firfilt_crcf_get_coefficients.restype = ctypes.c_int32
firfilt_crcf_get_coefficients.argtypes = [firfilt_crcf, ctypes.POINTER(ctypes.c_float)]
firfilt_crcf_freqresponse = liquiddsp.firfilt_crcf_freqresponse
firfilt_crcf_freqresponse.restype = None
firfilt_crcf_freqresponse.argtypes = [firfilt_crcf, ctypes.c_float, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
firfilt_crcf_groupdelay = liquiddsp.firfilt_crcf_groupdelay
firfilt_crcf_groupdelay.restype = ctypes.c_float
firfilt_crcf_groupdelay.argtypes = [firfilt_crcf, ctypes.c_float]
class struct_firfilt_cccf_s(Structure):
    pass

firfilt_cccf = ctypes.POINTER(struct_firfilt_cccf_s)
firfilt_cccf_create = liquiddsp.firfilt_cccf_create
firfilt_cccf_create.restype = firfilt_cccf
firfilt_cccf_create.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
firfilt_cccf_create_kaiser = liquiddsp.firfilt_cccf_create_kaiser
firfilt_cccf_create_kaiser.restype = firfilt_cccf
firfilt_cccf_create_kaiser.argtypes = [ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.c_float]
firfilt_cccf_create_rnyquist = liquiddsp.firfilt_cccf_create_rnyquist
firfilt_cccf_create_rnyquist.restype = firfilt_cccf
firfilt_cccf_create_rnyquist.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
firfilt_cccf_create_firdespm = liquiddsp.firfilt_cccf_create_firdespm
firfilt_cccf_create_firdespm.restype = firfilt_cccf
firfilt_cccf_create_firdespm.argtypes = [ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
firfilt_cccf_create_rect = liquiddsp.firfilt_cccf_create_rect
firfilt_cccf_create_rect.restype = firfilt_cccf
firfilt_cccf_create_rect.argtypes = [ctypes.c_uint32]
firfilt_cccf_create_dc_blocker = liquiddsp.firfilt_cccf_create_dc_blocker
firfilt_cccf_create_dc_blocker.restype = firfilt_cccf
firfilt_cccf_create_dc_blocker.argtypes = [ctypes.c_uint32, ctypes.c_float]
firfilt_cccf_create_notch = liquiddsp.firfilt_cccf_create_notch
firfilt_cccf_create_notch.restype = firfilt_cccf
firfilt_cccf_create_notch.argtypes = [ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
firfilt_cccf_recreate = liquiddsp.firfilt_cccf_recreate
firfilt_cccf_recreate.restype = firfilt_cccf
firfilt_cccf_recreate.argtypes = [firfilt_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
firfilt_cccf_destroy = liquiddsp.firfilt_cccf_destroy
firfilt_cccf_destroy.restype = None
firfilt_cccf_destroy.argtypes = [firfilt_cccf]
firfilt_cccf_reset = liquiddsp.firfilt_cccf_reset
firfilt_cccf_reset.restype = None
firfilt_cccf_reset.argtypes = [firfilt_cccf]
firfilt_cccf_print = liquiddsp.firfilt_cccf_print
firfilt_cccf_print.restype = None
firfilt_cccf_print.argtypes = [firfilt_cccf]
firfilt_cccf_set_scale = liquiddsp.firfilt_cccf_set_scale
firfilt_cccf_set_scale.restype = None
firfilt_cccf_set_scale.argtypes = [firfilt_cccf, liquid_float_complex]
firfilt_cccf_get_scale = liquiddsp.firfilt_cccf_get_scale
firfilt_cccf_get_scale.restype = None
firfilt_cccf_get_scale.argtypes = [firfilt_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
firfilt_cccf_push = liquiddsp.firfilt_cccf_push
firfilt_cccf_push.restype = None
firfilt_cccf_push.argtypes = [firfilt_cccf, liquid_float_complex]
firfilt_cccf_write = liquiddsp.firfilt_cccf_write
firfilt_cccf_write.restype = None
firfilt_cccf_write.argtypes = [firfilt_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
firfilt_cccf_execute = liquiddsp.firfilt_cccf_execute
firfilt_cccf_execute.restype = None
firfilt_cccf_execute.argtypes = [firfilt_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
firfilt_cccf_execute_block = liquiddsp.firfilt_cccf_execute_block
firfilt_cccf_execute_block.restype = None
firfilt_cccf_execute_block.argtypes = [firfilt_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
firfilt_cccf_get_length = liquiddsp.firfilt_cccf_get_length
firfilt_cccf_get_length.restype = ctypes.c_uint32
firfilt_cccf_get_length.argtypes = [firfilt_cccf]
firfilt_cccf_get_coefficients = liquiddsp.firfilt_cccf_get_coefficients
firfilt_cccf_get_coefficients.restype = ctypes.c_int32
firfilt_cccf_get_coefficients.argtypes = [firfilt_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
firfilt_cccf_freqresponse = liquiddsp.firfilt_cccf_freqresponse
firfilt_cccf_freqresponse.restype = None
firfilt_cccf_freqresponse.argtypes = [firfilt_cccf, ctypes.c_float, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
firfilt_cccf_groupdelay = liquiddsp.firfilt_cccf_groupdelay
firfilt_cccf_groupdelay.restype = ctypes.c_float
firfilt_cccf_groupdelay.argtypes = [firfilt_cccf, ctypes.c_float]
class struct_firhilbf_s(Structure):
    pass

firhilbf = ctypes.POINTER(struct_firhilbf_s)
firhilbf_create = liquiddsp.firhilbf_create
firhilbf_create.restype = firhilbf
firhilbf_create.argtypes = [ctypes.c_uint32, ctypes.c_float]
firhilbf_destroy = liquiddsp.firhilbf_destroy
firhilbf_destroy.restype = None
firhilbf_destroy.argtypes = [firhilbf]
firhilbf_print = liquiddsp.firhilbf_print
firhilbf_print.restype = None
firhilbf_print.argtypes = [firhilbf]
firhilbf_reset = liquiddsp.firhilbf_reset
firhilbf_reset.restype = None
firhilbf_reset.argtypes = [firhilbf]
firhilbf_r2c_execute = liquiddsp.firhilbf_r2c_execute
firhilbf_r2c_execute.restype = None
firhilbf_r2c_execute.argtypes = [firhilbf, ctypes.c_float, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
firhilbf_c2r_execute = liquiddsp.firhilbf_c2r_execute
firhilbf_c2r_execute.restype = None
firhilbf_c2r_execute.argtypes = [firhilbf, liquid_float_complex, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
firhilbf_decim_execute = liquiddsp.firhilbf_decim_execute
firhilbf_decim_execute.restype = None
firhilbf_decim_execute.argtypes = [firhilbf, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
firhilbf_decim_execute_block = liquiddsp.firhilbf_decim_execute_block
firhilbf_decim_execute_block.restype = None
firhilbf_decim_execute_block.argtypes = [firhilbf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
firhilbf_interp_execute = liquiddsp.firhilbf_interp_execute
firhilbf_interp_execute.restype = None
firhilbf_interp_execute.argtypes = [firhilbf, liquid_float_complex, ctypes.POINTER(ctypes.c_float)]
firhilbf_interp_execute_block = liquiddsp.firhilbf_interp_execute_block
firhilbf_interp_execute_block.restype = None
firhilbf_interp_execute_block.argtypes = [firhilbf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
class struct_iirhilbf_s(Structure):
    pass

iirhilbf = ctypes.POINTER(struct_iirhilbf_s)
iirhilbf_create = liquiddsp.iirhilbf_create
iirhilbf_create.restype = iirhilbf
iirhilbf_create.argtypes = [liquid_iirdes_filtertype, ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
iirhilbf_create_default = liquiddsp.iirhilbf_create_default
iirhilbf_create_default.restype = iirhilbf
iirhilbf_create_default.argtypes = [ctypes.c_uint32]
iirhilbf_destroy = liquiddsp.iirhilbf_destroy
iirhilbf_destroy.restype = None
iirhilbf_destroy.argtypes = [iirhilbf]
iirhilbf_print = liquiddsp.iirhilbf_print
iirhilbf_print.restype = None
iirhilbf_print.argtypes = [iirhilbf]
iirhilbf_reset = liquiddsp.iirhilbf_reset
iirhilbf_reset.restype = None
iirhilbf_reset.argtypes = [iirhilbf]
iirhilbf_r2c_execute = liquiddsp.iirhilbf_r2c_execute
iirhilbf_r2c_execute.restype = None
iirhilbf_r2c_execute.argtypes = [iirhilbf, ctypes.c_float, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
iirhilbf_c2r_execute = liquiddsp.iirhilbf_c2r_execute
iirhilbf_c2r_execute.restype = None
iirhilbf_c2r_execute.argtypes = [iirhilbf, liquid_float_complex, ctypes.POINTER(ctypes.c_float)]
iirhilbf_decim_execute = liquiddsp.iirhilbf_decim_execute
iirhilbf_decim_execute.restype = None
iirhilbf_decim_execute.argtypes = [iirhilbf, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
iirhilbf_decim_execute_block = liquiddsp.iirhilbf_decim_execute_block
iirhilbf_decim_execute_block.restype = None
iirhilbf_decim_execute_block.argtypes = [iirhilbf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
iirhilbf_interp_execute = liquiddsp.iirhilbf_interp_execute
iirhilbf_interp_execute.restype = None
iirhilbf_interp_execute.argtypes = [iirhilbf, liquid_float_complex, ctypes.POINTER(ctypes.c_float)]
iirhilbf_interp_execute_block = liquiddsp.iirhilbf_interp_execute_block
iirhilbf_interp_execute_block.restype = None
iirhilbf_interp_execute_block.argtypes = [iirhilbf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
class struct_fftfilt_rrrf_s(Structure):
    pass

fftfilt_rrrf = ctypes.POINTER(struct_fftfilt_rrrf_s)
fftfilt_rrrf_create = liquiddsp.fftfilt_rrrf_create
fftfilt_rrrf_create.restype = fftfilt_rrrf
fftfilt_rrrf_create.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32]
fftfilt_rrrf_destroy = liquiddsp.fftfilt_rrrf_destroy
fftfilt_rrrf_destroy.restype = None
fftfilt_rrrf_destroy.argtypes = [fftfilt_rrrf]
fftfilt_rrrf_reset = liquiddsp.fftfilt_rrrf_reset
fftfilt_rrrf_reset.restype = None
fftfilt_rrrf_reset.argtypes = [fftfilt_rrrf]
fftfilt_rrrf_print = liquiddsp.fftfilt_rrrf_print
fftfilt_rrrf_print.restype = None
fftfilt_rrrf_print.argtypes = [fftfilt_rrrf]
fftfilt_rrrf_set_scale = liquiddsp.fftfilt_rrrf_set_scale
fftfilt_rrrf_set_scale.restype = None
fftfilt_rrrf_set_scale.argtypes = [fftfilt_rrrf, ctypes.c_float]
fftfilt_rrrf_get_scale = liquiddsp.fftfilt_rrrf_get_scale
fftfilt_rrrf_get_scale.restype = None
fftfilt_rrrf_get_scale.argtypes = [fftfilt_rrrf, ctypes.POINTER(ctypes.c_float)]
fftfilt_rrrf_execute = liquiddsp.fftfilt_rrrf_execute
fftfilt_rrrf_execute.restype = None
fftfilt_rrrf_execute.argtypes = [fftfilt_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
fftfilt_rrrf_get_length = liquiddsp.fftfilt_rrrf_get_length
fftfilt_rrrf_get_length.restype = ctypes.c_uint32
fftfilt_rrrf_get_length.argtypes = [fftfilt_rrrf]
class struct_fftfilt_crcf_s(Structure):
    pass

fftfilt_crcf = ctypes.POINTER(struct_fftfilt_crcf_s)
fftfilt_crcf_create = liquiddsp.fftfilt_crcf_create
fftfilt_crcf_create.restype = fftfilt_crcf
fftfilt_crcf_create.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32]
fftfilt_crcf_destroy = liquiddsp.fftfilt_crcf_destroy
fftfilt_crcf_destroy.restype = None
fftfilt_crcf_destroy.argtypes = [fftfilt_crcf]
fftfilt_crcf_reset = liquiddsp.fftfilt_crcf_reset
fftfilt_crcf_reset.restype = None
fftfilt_crcf_reset.argtypes = [fftfilt_crcf]
fftfilt_crcf_print = liquiddsp.fftfilt_crcf_print
fftfilt_crcf_print.restype = None
fftfilt_crcf_print.argtypes = [fftfilt_crcf]
fftfilt_crcf_set_scale = liquiddsp.fftfilt_crcf_set_scale
fftfilt_crcf_set_scale.restype = None
fftfilt_crcf_set_scale.argtypes = [fftfilt_crcf, ctypes.c_float]
fftfilt_crcf_get_scale = liquiddsp.fftfilt_crcf_get_scale
fftfilt_crcf_get_scale.restype = None
fftfilt_crcf_get_scale.argtypes = [fftfilt_crcf, ctypes.POINTER(ctypes.c_float)]
fftfilt_crcf_execute = liquiddsp.fftfilt_crcf_execute
fftfilt_crcf_execute.restype = None
fftfilt_crcf_execute.argtypes = [fftfilt_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
fftfilt_crcf_get_length = liquiddsp.fftfilt_crcf_get_length
fftfilt_crcf_get_length.restype = ctypes.c_uint32
fftfilt_crcf_get_length.argtypes = [fftfilt_crcf]
class struct_fftfilt_cccf_s(Structure):
    pass

fftfilt_cccf = ctypes.POINTER(struct_fftfilt_cccf_s)
fftfilt_cccf_create = liquiddsp.fftfilt_cccf_create
fftfilt_cccf_create.restype = fftfilt_cccf
fftfilt_cccf_create.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_uint32]
fftfilt_cccf_destroy = liquiddsp.fftfilt_cccf_destroy
fftfilt_cccf_destroy.restype = None
fftfilt_cccf_destroy.argtypes = [fftfilt_cccf]
fftfilt_cccf_reset = liquiddsp.fftfilt_cccf_reset
fftfilt_cccf_reset.restype = None
fftfilt_cccf_reset.argtypes = [fftfilt_cccf]
fftfilt_cccf_print = liquiddsp.fftfilt_cccf_print
fftfilt_cccf_print.restype = None
fftfilt_cccf_print.argtypes = [fftfilt_cccf]
fftfilt_cccf_set_scale = liquiddsp.fftfilt_cccf_set_scale
fftfilt_cccf_set_scale.restype = None
fftfilt_cccf_set_scale.argtypes = [fftfilt_cccf, liquid_float_complex]
fftfilt_cccf_get_scale = liquiddsp.fftfilt_cccf_get_scale
fftfilt_cccf_get_scale.restype = None
fftfilt_cccf_get_scale.argtypes = [fftfilt_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
fftfilt_cccf_execute = liquiddsp.fftfilt_cccf_execute
fftfilt_cccf_execute.restype = None
fftfilt_cccf_execute.argtypes = [fftfilt_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
fftfilt_cccf_get_length = liquiddsp.fftfilt_cccf_get_length
fftfilt_cccf_get_length.restype = ctypes.c_uint32
fftfilt_cccf_get_length.argtypes = [fftfilt_cccf]
class struct_iirfilt_rrrf_s(Structure):
    pass

iirfilt_rrrf = ctypes.POINTER(struct_iirfilt_rrrf_s)
iirfilt_rrrf_create = liquiddsp.iirfilt_rrrf_create
iirfilt_rrrf_create.restype = iirfilt_rrrf
iirfilt_rrrf_create.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
iirfilt_rrrf_create_sos = liquiddsp.iirfilt_rrrf_create_sos
iirfilt_rrrf_create_sos.restype = iirfilt_rrrf
iirfilt_rrrf_create_sos.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
iirfilt_rrrf_create_prototype = liquiddsp.iirfilt_rrrf_create_prototype
iirfilt_rrrf_create_prototype.restype = iirfilt_rrrf
iirfilt_rrrf_create_prototype.argtypes = [liquid_iirdes_filtertype, liquid_iirdes_bandtype, liquid_iirdes_format, ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
iirfilt_rrrf_create_lowpass = liquiddsp.iirfilt_rrrf_create_lowpass
iirfilt_rrrf_create_lowpass.restype = iirfilt_rrrf
iirfilt_rrrf_create_lowpass.argtypes = [ctypes.c_uint32, ctypes.c_float]
iirfilt_rrrf_create_integrator = liquiddsp.iirfilt_rrrf_create_integrator
iirfilt_rrrf_create_integrator.restype = iirfilt_rrrf
iirfilt_rrrf_create_integrator.argtypes = []
iirfilt_rrrf_create_differentiator = liquiddsp.iirfilt_rrrf_create_differentiator
iirfilt_rrrf_create_differentiator.restype = iirfilt_rrrf
iirfilt_rrrf_create_differentiator.argtypes = []
iirfilt_rrrf_create_dc_blocker = liquiddsp.iirfilt_rrrf_create_dc_blocker
iirfilt_rrrf_create_dc_blocker.restype = iirfilt_rrrf
iirfilt_rrrf_create_dc_blocker.argtypes = [ctypes.c_float]
iirfilt_rrrf_create_pll = liquiddsp.iirfilt_rrrf_create_pll
iirfilt_rrrf_create_pll.restype = iirfilt_rrrf
iirfilt_rrrf_create_pll.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float]
iirfilt_rrrf_destroy = liquiddsp.iirfilt_rrrf_destroy
iirfilt_rrrf_destroy.restype = None
iirfilt_rrrf_destroy.argtypes = [iirfilt_rrrf]
iirfilt_rrrf_print = liquiddsp.iirfilt_rrrf_print
iirfilt_rrrf_print.restype = None
iirfilt_rrrf_print.argtypes = [iirfilt_rrrf]
iirfilt_rrrf_reset = liquiddsp.iirfilt_rrrf_reset
iirfilt_rrrf_reset.restype = None
iirfilt_rrrf_reset.argtypes = [iirfilt_rrrf]
iirfilt_rrrf_execute = liquiddsp.iirfilt_rrrf_execute
iirfilt_rrrf_execute.restype = None
iirfilt_rrrf_execute.argtypes = [iirfilt_rrrf, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
iirfilt_rrrf_execute_block = liquiddsp.iirfilt_rrrf_execute_block
iirfilt_rrrf_execute_block.restype = None
iirfilt_rrrf_execute_block.argtypes = [iirfilt_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
iirfilt_rrrf_get_length = liquiddsp.iirfilt_rrrf_get_length
iirfilt_rrrf_get_length.restype = ctypes.c_uint32
iirfilt_rrrf_get_length.argtypes = [iirfilt_rrrf]
iirfilt_rrrf_freqresponse = liquiddsp.iirfilt_rrrf_freqresponse
iirfilt_rrrf_freqresponse.restype = None
iirfilt_rrrf_freqresponse.argtypes = [iirfilt_rrrf, ctypes.c_float, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
iirfilt_rrrf_groupdelay = liquiddsp.iirfilt_rrrf_groupdelay
iirfilt_rrrf_groupdelay.restype = ctypes.c_float
iirfilt_rrrf_groupdelay.argtypes = [iirfilt_rrrf, ctypes.c_float]
class struct_iirfilt_crcf_s(Structure):
    pass

iirfilt_crcf = ctypes.POINTER(struct_iirfilt_crcf_s)
iirfilt_crcf_create = liquiddsp.iirfilt_crcf_create
iirfilt_crcf_create.restype = iirfilt_crcf
iirfilt_crcf_create.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
iirfilt_crcf_create_sos = liquiddsp.iirfilt_crcf_create_sos
iirfilt_crcf_create_sos.restype = iirfilt_crcf
iirfilt_crcf_create_sos.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
iirfilt_crcf_create_prototype = liquiddsp.iirfilt_crcf_create_prototype
iirfilt_crcf_create_prototype.restype = iirfilt_crcf
iirfilt_crcf_create_prototype.argtypes = [liquid_iirdes_filtertype, liquid_iirdes_bandtype, liquid_iirdes_format, ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
iirfilt_crcf_create_lowpass = liquiddsp.iirfilt_crcf_create_lowpass
iirfilt_crcf_create_lowpass.restype = iirfilt_crcf
iirfilt_crcf_create_lowpass.argtypes = [ctypes.c_uint32, ctypes.c_float]
iirfilt_crcf_create_integrator = liquiddsp.iirfilt_crcf_create_integrator
iirfilt_crcf_create_integrator.restype = iirfilt_crcf
iirfilt_crcf_create_integrator.argtypes = []
iirfilt_crcf_create_differentiator = liquiddsp.iirfilt_crcf_create_differentiator
iirfilt_crcf_create_differentiator.restype = iirfilt_crcf
iirfilt_crcf_create_differentiator.argtypes = []
iirfilt_crcf_create_dc_blocker = liquiddsp.iirfilt_crcf_create_dc_blocker
iirfilt_crcf_create_dc_blocker.restype = iirfilt_crcf
iirfilt_crcf_create_dc_blocker.argtypes = [ctypes.c_float]
iirfilt_crcf_create_pll = liquiddsp.iirfilt_crcf_create_pll
iirfilt_crcf_create_pll.restype = iirfilt_crcf
iirfilt_crcf_create_pll.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float]
iirfilt_crcf_destroy = liquiddsp.iirfilt_crcf_destroy
iirfilt_crcf_destroy.restype = None
iirfilt_crcf_destroy.argtypes = [iirfilt_crcf]
iirfilt_crcf_print = liquiddsp.iirfilt_crcf_print
iirfilt_crcf_print.restype = None
iirfilt_crcf_print.argtypes = [iirfilt_crcf]
iirfilt_crcf_reset = liquiddsp.iirfilt_crcf_reset
iirfilt_crcf_reset.restype = None
iirfilt_crcf_reset.argtypes = [iirfilt_crcf]
iirfilt_crcf_execute = liquiddsp.iirfilt_crcf_execute
iirfilt_crcf_execute.restype = None
iirfilt_crcf_execute.argtypes = [iirfilt_crcf, liquid_float_complex, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
iirfilt_crcf_execute_block = liquiddsp.iirfilt_crcf_execute_block
iirfilt_crcf_execute_block.restype = None
iirfilt_crcf_execute_block.argtypes = [iirfilt_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
iirfilt_crcf_get_length = liquiddsp.iirfilt_crcf_get_length
iirfilt_crcf_get_length.restype = ctypes.c_uint32
iirfilt_crcf_get_length.argtypes = [iirfilt_crcf]
iirfilt_crcf_freqresponse = liquiddsp.iirfilt_crcf_freqresponse
iirfilt_crcf_freqresponse.restype = None
iirfilt_crcf_freqresponse.argtypes = [iirfilt_crcf, ctypes.c_float, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
iirfilt_crcf_groupdelay = liquiddsp.iirfilt_crcf_groupdelay
iirfilt_crcf_groupdelay.restype = ctypes.c_float
iirfilt_crcf_groupdelay.argtypes = [iirfilt_crcf, ctypes.c_float]
class struct_iirfilt_cccf_s(Structure):
    pass

iirfilt_cccf = ctypes.POINTER(struct_iirfilt_cccf_s)
iirfilt_cccf_create = liquiddsp.iirfilt_cccf_create
iirfilt_cccf_create.restype = iirfilt_cccf
iirfilt_cccf_create.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
iirfilt_cccf_create_sos = liquiddsp.iirfilt_cccf_create_sos
iirfilt_cccf_create_sos.restype = iirfilt_cccf
iirfilt_cccf_create_sos.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
iirfilt_cccf_create_prototype = liquiddsp.iirfilt_cccf_create_prototype
iirfilt_cccf_create_prototype.restype = iirfilt_cccf
iirfilt_cccf_create_prototype.argtypes = [liquid_iirdes_filtertype, liquid_iirdes_bandtype, liquid_iirdes_format, ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
iirfilt_cccf_create_lowpass = liquiddsp.iirfilt_cccf_create_lowpass
iirfilt_cccf_create_lowpass.restype = iirfilt_cccf
iirfilt_cccf_create_lowpass.argtypes = [ctypes.c_uint32, ctypes.c_float]
iirfilt_cccf_create_integrator = liquiddsp.iirfilt_cccf_create_integrator
iirfilt_cccf_create_integrator.restype = iirfilt_cccf
iirfilt_cccf_create_integrator.argtypes = []
iirfilt_cccf_create_differentiator = liquiddsp.iirfilt_cccf_create_differentiator
iirfilt_cccf_create_differentiator.restype = iirfilt_cccf
iirfilt_cccf_create_differentiator.argtypes = []
iirfilt_cccf_create_dc_blocker = liquiddsp.iirfilt_cccf_create_dc_blocker
iirfilt_cccf_create_dc_blocker.restype = iirfilt_cccf
iirfilt_cccf_create_dc_blocker.argtypes = [ctypes.c_float]
iirfilt_cccf_create_pll = liquiddsp.iirfilt_cccf_create_pll
iirfilt_cccf_create_pll.restype = iirfilt_cccf
iirfilt_cccf_create_pll.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float]
iirfilt_cccf_destroy = liquiddsp.iirfilt_cccf_destroy
iirfilt_cccf_destroy.restype = None
iirfilt_cccf_destroy.argtypes = [iirfilt_cccf]
iirfilt_cccf_print = liquiddsp.iirfilt_cccf_print
iirfilt_cccf_print.restype = None
iirfilt_cccf_print.argtypes = [iirfilt_cccf]
iirfilt_cccf_reset = liquiddsp.iirfilt_cccf_reset
iirfilt_cccf_reset.restype = None
iirfilt_cccf_reset.argtypes = [iirfilt_cccf]
iirfilt_cccf_execute = liquiddsp.iirfilt_cccf_execute
iirfilt_cccf_execute.restype = None
iirfilt_cccf_execute.argtypes = [iirfilt_cccf, liquid_float_complex, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
iirfilt_cccf_execute_block = liquiddsp.iirfilt_cccf_execute_block
iirfilt_cccf_execute_block.restype = None
iirfilt_cccf_execute_block.argtypes = [iirfilt_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
iirfilt_cccf_get_length = liquiddsp.iirfilt_cccf_get_length
iirfilt_cccf_get_length.restype = ctypes.c_uint32
iirfilt_cccf_get_length.argtypes = [iirfilt_cccf]
iirfilt_cccf_freqresponse = liquiddsp.iirfilt_cccf_freqresponse
iirfilt_cccf_freqresponse.restype = None
iirfilt_cccf_freqresponse.argtypes = [iirfilt_cccf, ctypes.c_float, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
iirfilt_cccf_groupdelay = liquiddsp.iirfilt_cccf_groupdelay
iirfilt_cccf_groupdelay.restype = ctypes.c_float
iirfilt_cccf_groupdelay.argtypes = [iirfilt_cccf, ctypes.c_float]
class struct_iirfiltsos_rrrf_s(Structure):
    pass

iirfiltsos_rrrf = ctypes.POINTER(struct_iirfiltsos_rrrf_s)
iirfiltsos_rrrf_create = liquiddsp.iirfiltsos_rrrf_create
iirfiltsos_rrrf_create.restype = iirfiltsos_rrrf
iirfiltsos_rrrf_create.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
iirfiltsos_rrrf_set_coefficients = liquiddsp.iirfiltsos_rrrf_set_coefficients
iirfiltsos_rrrf_set_coefficients.restype = None
iirfiltsos_rrrf_set_coefficients.argtypes = [iirfiltsos_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
iirfiltsos_rrrf_destroy = liquiddsp.iirfiltsos_rrrf_destroy
iirfiltsos_rrrf_destroy.restype = None
iirfiltsos_rrrf_destroy.argtypes = [iirfiltsos_rrrf]
iirfiltsos_rrrf_print = liquiddsp.iirfiltsos_rrrf_print
iirfiltsos_rrrf_print.restype = None
iirfiltsos_rrrf_print.argtypes = [iirfiltsos_rrrf]
iirfiltsos_rrrf_reset = liquiddsp.iirfiltsos_rrrf_reset
iirfiltsos_rrrf_reset.restype = None
iirfiltsos_rrrf_reset.argtypes = [iirfiltsos_rrrf]
iirfiltsos_rrrf_execute = liquiddsp.iirfiltsos_rrrf_execute
iirfiltsos_rrrf_execute.restype = None
iirfiltsos_rrrf_execute.argtypes = [iirfiltsos_rrrf, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
iirfiltsos_rrrf_execute_df1 = liquiddsp.iirfiltsos_rrrf_execute_df1
iirfiltsos_rrrf_execute_df1.restype = None
iirfiltsos_rrrf_execute_df1.argtypes = [iirfiltsos_rrrf, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
iirfiltsos_rrrf_execute_df2 = liquiddsp.iirfiltsos_rrrf_execute_df2
iirfiltsos_rrrf_execute_df2.restype = None
iirfiltsos_rrrf_execute_df2.argtypes = [iirfiltsos_rrrf, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
iirfiltsos_rrrf_groupdelay = liquiddsp.iirfiltsos_rrrf_groupdelay
iirfiltsos_rrrf_groupdelay.restype = ctypes.c_float
iirfiltsos_rrrf_groupdelay.argtypes = [iirfiltsos_rrrf, ctypes.c_float]
class struct_iirfiltsos_crcf_s(Structure):
    pass

iirfiltsos_crcf = ctypes.POINTER(struct_iirfiltsos_crcf_s)
iirfiltsos_crcf_create = liquiddsp.iirfiltsos_crcf_create
iirfiltsos_crcf_create.restype = iirfiltsos_crcf
iirfiltsos_crcf_create.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
iirfiltsos_crcf_set_coefficients = liquiddsp.iirfiltsos_crcf_set_coefficients
iirfiltsos_crcf_set_coefficients.restype = None
iirfiltsos_crcf_set_coefficients.argtypes = [iirfiltsos_crcf, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
iirfiltsos_crcf_destroy = liquiddsp.iirfiltsos_crcf_destroy
iirfiltsos_crcf_destroy.restype = None
iirfiltsos_crcf_destroy.argtypes = [iirfiltsos_crcf]
iirfiltsos_crcf_print = liquiddsp.iirfiltsos_crcf_print
iirfiltsos_crcf_print.restype = None
iirfiltsos_crcf_print.argtypes = [iirfiltsos_crcf]
iirfiltsos_crcf_reset = liquiddsp.iirfiltsos_crcf_reset
iirfiltsos_crcf_reset.restype = None
iirfiltsos_crcf_reset.argtypes = [iirfiltsos_crcf]
iirfiltsos_crcf_execute = liquiddsp.iirfiltsos_crcf_execute
iirfiltsos_crcf_execute.restype = None
iirfiltsos_crcf_execute.argtypes = [iirfiltsos_crcf, liquid_float_complex, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
iirfiltsos_crcf_execute_df1 = liquiddsp.iirfiltsos_crcf_execute_df1
iirfiltsos_crcf_execute_df1.restype = None
iirfiltsos_crcf_execute_df1.argtypes = [iirfiltsos_crcf, liquid_float_complex, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
iirfiltsos_crcf_execute_df2 = liquiddsp.iirfiltsos_crcf_execute_df2
iirfiltsos_crcf_execute_df2.restype = None
iirfiltsos_crcf_execute_df2.argtypes = [iirfiltsos_crcf, liquid_float_complex, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
iirfiltsos_crcf_groupdelay = liquiddsp.iirfiltsos_crcf_groupdelay
iirfiltsos_crcf_groupdelay.restype = ctypes.c_float
iirfiltsos_crcf_groupdelay.argtypes = [iirfiltsos_crcf, ctypes.c_float]
class struct_iirfiltsos_cccf_s(Structure):
    pass

iirfiltsos_cccf = ctypes.POINTER(struct_iirfiltsos_cccf_s)
iirfiltsos_cccf_create = liquiddsp.iirfiltsos_cccf_create
iirfiltsos_cccf_create.restype = iirfiltsos_cccf
iirfiltsos_cccf_create.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
iirfiltsos_cccf_set_coefficients = liquiddsp.iirfiltsos_cccf_set_coefficients
iirfiltsos_cccf_set_coefficients.restype = None
iirfiltsos_cccf_set_coefficients.argtypes = [iirfiltsos_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
iirfiltsos_cccf_destroy = liquiddsp.iirfiltsos_cccf_destroy
iirfiltsos_cccf_destroy.restype = None
iirfiltsos_cccf_destroy.argtypes = [iirfiltsos_cccf]
iirfiltsos_cccf_print = liquiddsp.iirfiltsos_cccf_print
iirfiltsos_cccf_print.restype = None
iirfiltsos_cccf_print.argtypes = [iirfiltsos_cccf]
iirfiltsos_cccf_reset = liquiddsp.iirfiltsos_cccf_reset
iirfiltsos_cccf_reset.restype = None
iirfiltsos_cccf_reset.argtypes = [iirfiltsos_cccf]
iirfiltsos_cccf_execute = liquiddsp.iirfiltsos_cccf_execute
iirfiltsos_cccf_execute.restype = None
iirfiltsos_cccf_execute.argtypes = [iirfiltsos_cccf, liquid_float_complex, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
iirfiltsos_cccf_execute_df1 = liquiddsp.iirfiltsos_cccf_execute_df1
iirfiltsos_cccf_execute_df1.restype = None
iirfiltsos_cccf_execute_df1.argtypes = [iirfiltsos_cccf, liquid_float_complex, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
iirfiltsos_cccf_execute_df2 = liquiddsp.iirfiltsos_cccf_execute_df2
iirfiltsos_cccf_execute_df2.restype = None
iirfiltsos_cccf_execute_df2.argtypes = [iirfiltsos_cccf, liquid_float_complex, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
iirfiltsos_cccf_groupdelay = liquiddsp.iirfiltsos_cccf_groupdelay
iirfiltsos_cccf_groupdelay.restype = ctypes.c_float
iirfiltsos_cccf_groupdelay.argtypes = [iirfiltsos_cccf, ctypes.c_float]
class struct_firpfb_rrrf_s(Structure):
    pass

firpfb_rrrf = ctypes.POINTER(struct_firpfb_rrrf_s)
firpfb_rrrf_create = liquiddsp.firpfb_rrrf_create
firpfb_rrrf_create.restype = firpfb_rrrf
firpfb_rrrf_create.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
firpfb_rrrf_create_default = liquiddsp.firpfb_rrrf_create_default
firpfb_rrrf_create_default.restype = firpfb_rrrf
firpfb_rrrf_create_default.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
firpfb_rrrf_create_kaiser = liquiddsp.firpfb_rrrf_create_kaiser
firpfb_rrrf_create_kaiser.restype = firpfb_rrrf
firpfb_rrrf_create_kaiser.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
firpfb_rrrf_create_rnyquist = liquiddsp.firpfb_rrrf_create_rnyquist
firpfb_rrrf_create_rnyquist.restype = firpfb_rrrf
firpfb_rrrf_create_rnyquist.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float]
firpfb_rrrf_create_drnyquist = liquiddsp.firpfb_rrrf_create_drnyquist
firpfb_rrrf_create_drnyquist.restype = firpfb_rrrf
firpfb_rrrf_create_drnyquist.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float]
firpfb_rrrf_recreate = liquiddsp.firpfb_rrrf_recreate
firpfb_rrrf_recreate.restype = firpfb_rrrf
firpfb_rrrf_recreate.argtypes = [firpfb_rrrf, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
firpfb_rrrf_destroy = liquiddsp.firpfb_rrrf_destroy
firpfb_rrrf_destroy.restype = None
firpfb_rrrf_destroy.argtypes = [firpfb_rrrf]
firpfb_rrrf_print = liquiddsp.firpfb_rrrf_print
firpfb_rrrf_print.restype = None
firpfb_rrrf_print.argtypes = [firpfb_rrrf]
firpfb_rrrf_set_scale = liquiddsp.firpfb_rrrf_set_scale
firpfb_rrrf_set_scale.restype = None
firpfb_rrrf_set_scale.argtypes = [firpfb_rrrf, ctypes.c_float]
firpfb_rrrf_get_scale = liquiddsp.firpfb_rrrf_get_scale
firpfb_rrrf_get_scale.restype = None
firpfb_rrrf_get_scale.argtypes = [firpfb_rrrf, ctypes.POINTER(ctypes.c_float)]
firpfb_rrrf_reset = liquiddsp.firpfb_rrrf_reset
firpfb_rrrf_reset.restype = None
firpfb_rrrf_reset.argtypes = [firpfb_rrrf]
firpfb_rrrf_push = liquiddsp.firpfb_rrrf_push
firpfb_rrrf_push.restype = None
firpfb_rrrf_push.argtypes = [firpfb_rrrf, ctypes.c_float]
firpfb_rrrf_write = liquiddsp.firpfb_rrrf_write
firpfb_rrrf_write.restype = None
firpfb_rrrf_write.argtypes = [firpfb_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
firpfb_rrrf_execute = liquiddsp.firpfb_rrrf_execute
firpfb_rrrf_execute.restype = None
firpfb_rrrf_execute.argtypes = [firpfb_rrrf, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
firpfb_rrrf_execute_block = liquiddsp.firpfb_rrrf_execute_block
firpfb_rrrf_execute_block.restype = None
firpfb_rrrf_execute_block.argtypes = [firpfb_rrrf, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
class struct_firpfb_crcf_s(Structure):
    pass

firpfb_crcf = ctypes.POINTER(struct_firpfb_crcf_s)
firpfb_crcf_create = liquiddsp.firpfb_crcf_create
firpfb_crcf_create.restype = firpfb_crcf
firpfb_crcf_create.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
firpfb_crcf_create_default = liquiddsp.firpfb_crcf_create_default
firpfb_crcf_create_default.restype = firpfb_crcf
firpfb_crcf_create_default.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
firpfb_crcf_create_kaiser = liquiddsp.firpfb_crcf_create_kaiser
firpfb_crcf_create_kaiser.restype = firpfb_crcf
firpfb_crcf_create_kaiser.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
firpfb_crcf_create_rnyquist = liquiddsp.firpfb_crcf_create_rnyquist
firpfb_crcf_create_rnyquist.restype = firpfb_crcf
firpfb_crcf_create_rnyquist.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float]
firpfb_crcf_create_drnyquist = liquiddsp.firpfb_crcf_create_drnyquist
firpfb_crcf_create_drnyquist.restype = firpfb_crcf
firpfb_crcf_create_drnyquist.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float]
firpfb_crcf_recreate = liquiddsp.firpfb_crcf_recreate
firpfb_crcf_recreate.restype = firpfb_crcf
firpfb_crcf_recreate.argtypes = [firpfb_crcf, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
firpfb_crcf_destroy = liquiddsp.firpfb_crcf_destroy
firpfb_crcf_destroy.restype = None
firpfb_crcf_destroy.argtypes = [firpfb_crcf]
firpfb_crcf_print = liquiddsp.firpfb_crcf_print
firpfb_crcf_print.restype = None
firpfb_crcf_print.argtypes = [firpfb_crcf]
firpfb_crcf_set_scale = liquiddsp.firpfb_crcf_set_scale
firpfb_crcf_set_scale.restype = None
firpfb_crcf_set_scale.argtypes = [firpfb_crcf, ctypes.c_float]
firpfb_crcf_get_scale = liquiddsp.firpfb_crcf_get_scale
firpfb_crcf_get_scale.restype = None
firpfb_crcf_get_scale.argtypes = [firpfb_crcf, ctypes.POINTER(ctypes.c_float)]
firpfb_crcf_reset = liquiddsp.firpfb_crcf_reset
firpfb_crcf_reset.restype = None
firpfb_crcf_reset.argtypes = [firpfb_crcf]
firpfb_crcf_push = liquiddsp.firpfb_crcf_push
firpfb_crcf_push.restype = None
firpfb_crcf_push.argtypes = [firpfb_crcf, liquid_float_complex]
firpfb_crcf_write = liquiddsp.firpfb_crcf_write
firpfb_crcf_write.restype = None
firpfb_crcf_write.argtypes = [firpfb_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
firpfb_crcf_execute = liquiddsp.firpfb_crcf_execute
firpfb_crcf_execute.restype = None
firpfb_crcf_execute.argtypes = [firpfb_crcf, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
firpfb_crcf_execute_block = liquiddsp.firpfb_crcf_execute_block
firpfb_crcf_execute_block.restype = None
firpfb_crcf_execute_block.argtypes = [firpfb_crcf, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
class struct_firpfb_cccf_s(Structure):
    pass

firpfb_cccf = ctypes.POINTER(struct_firpfb_cccf_s)
firpfb_cccf_create = liquiddsp.firpfb_cccf_create
firpfb_cccf_create.restype = firpfb_cccf
firpfb_cccf_create.argtypes = [ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
firpfb_cccf_create_default = liquiddsp.firpfb_cccf_create_default
firpfb_cccf_create_default.restype = firpfb_cccf
firpfb_cccf_create_default.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
firpfb_cccf_create_kaiser = liquiddsp.firpfb_cccf_create_kaiser
firpfb_cccf_create_kaiser.restype = firpfb_cccf
firpfb_cccf_create_kaiser.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
firpfb_cccf_create_rnyquist = liquiddsp.firpfb_cccf_create_rnyquist
firpfb_cccf_create_rnyquist.restype = firpfb_cccf
firpfb_cccf_create_rnyquist.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float]
firpfb_cccf_create_drnyquist = liquiddsp.firpfb_cccf_create_drnyquist
firpfb_cccf_create_drnyquist.restype = firpfb_cccf
firpfb_cccf_create_drnyquist.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float]
firpfb_cccf_recreate = liquiddsp.firpfb_cccf_recreate
firpfb_cccf_recreate.restype = firpfb_cccf
firpfb_cccf_recreate.argtypes = [firpfb_cccf, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
firpfb_cccf_destroy = liquiddsp.firpfb_cccf_destroy
firpfb_cccf_destroy.restype = None
firpfb_cccf_destroy.argtypes = [firpfb_cccf]
firpfb_cccf_print = liquiddsp.firpfb_cccf_print
firpfb_cccf_print.restype = None
firpfb_cccf_print.argtypes = [firpfb_cccf]
firpfb_cccf_set_scale = liquiddsp.firpfb_cccf_set_scale
firpfb_cccf_set_scale.restype = None
firpfb_cccf_set_scale.argtypes = [firpfb_cccf, liquid_float_complex]
firpfb_cccf_get_scale = liquiddsp.firpfb_cccf_get_scale
firpfb_cccf_get_scale.restype = None
firpfb_cccf_get_scale.argtypes = [firpfb_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
firpfb_cccf_reset = liquiddsp.firpfb_cccf_reset
firpfb_cccf_reset.restype = None
firpfb_cccf_reset.argtypes = [firpfb_cccf]
firpfb_cccf_push = liquiddsp.firpfb_cccf_push
firpfb_cccf_push.restype = None
firpfb_cccf_push.argtypes = [firpfb_cccf, liquid_float_complex]
firpfb_cccf_write = liquiddsp.firpfb_cccf_write
firpfb_cccf_write.restype = None
firpfb_cccf_write.argtypes = [firpfb_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
firpfb_cccf_execute = liquiddsp.firpfb_cccf_execute
firpfb_cccf_execute.restype = None
firpfb_cccf_execute.argtypes = [firpfb_cccf, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
firpfb_cccf_execute_block = liquiddsp.firpfb_cccf_execute_block
firpfb_cccf_execute_block.restype = None
firpfb_cccf_execute_block.argtypes = [firpfb_cccf, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
class struct_firinterp_rrrf_s(Structure):
    pass

firinterp_rrrf = ctypes.POINTER(struct_firinterp_rrrf_s)
firinterp_rrrf_create = liquiddsp.firinterp_rrrf_create
firinterp_rrrf_create.restype = firinterp_rrrf
firinterp_rrrf_create.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
firinterp_rrrf_create_kaiser = liquiddsp.firinterp_rrrf_create_kaiser
firinterp_rrrf_create_kaiser.restype = firinterp_rrrf
firinterp_rrrf_create_kaiser.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float]
firinterp_rrrf_create_prototype = liquiddsp.firinterp_rrrf_create_prototype
firinterp_rrrf_create_prototype.restype = firinterp_rrrf
firinterp_rrrf_create_prototype.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
firinterp_rrrf_create_linear = liquiddsp.firinterp_rrrf_create_linear
firinterp_rrrf_create_linear.restype = firinterp_rrrf
firinterp_rrrf_create_linear.argtypes = [ctypes.c_uint32]
firinterp_rrrf_create_window = liquiddsp.firinterp_rrrf_create_window
firinterp_rrrf_create_window.restype = firinterp_rrrf
firinterp_rrrf_create_window.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
firinterp_rrrf_destroy = liquiddsp.firinterp_rrrf_destroy
firinterp_rrrf_destroy.restype = None
firinterp_rrrf_destroy.argtypes = [firinterp_rrrf]
firinterp_rrrf_print = liquiddsp.firinterp_rrrf_print
firinterp_rrrf_print.restype = None
firinterp_rrrf_print.argtypes = [firinterp_rrrf]
firinterp_rrrf_reset = liquiddsp.firinterp_rrrf_reset
firinterp_rrrf_reset.restype = None
firinterp_rrrf_reset.argtypes = [firinterp_rrrf]
firinterp_rrrf_get_interp_rate = liquiddsp.firinterp_rrrf_get_interp_rate
firinterp_rrrf_get_interp_rate.restype = ctypes.c_uint32
firinterp_rrrf_get_interp_rate.argtypes = [firinterp_rrrf]
firinterp_rrrf_get_sub_len = liquiddsp.firinterp_rrrf_get_sub_len
firinterp_rrrf_get_sub_len.restype = ctypes.c_uint32
firinterp_rrrf_get_sub_len.argtypes = [firinterp_rrrf]
firinterp_rrrf_set_scale = liquiddsp.firinterp_rrrf_set_scale
firinterp_rrrf_set_scale.restype = None
firinterp_rrrf_set_scale.argtypes = [firinterp_rrrf, ctypes.c_float]
firinterp_rrrf_get_scale = liquiddsp.firinterp_rrrf_get_scale
firinterp_rrrf_get_scale.restype = None
firinterp_rrrf_get_scale.argtypes = [firinterp_rrrf, ctypes.POINTER(ctypes.c_float)]
firinterp_rrrf_execute = liquiddsp.firinterp_rrrf_execute
firinterp_rrrf_execute.restype = None
firinterp_rrrf_execute.argtypes = [firinterp_rrrf, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
firinterp_rrrf_execute_block = liquiddsp.firinterp_rrrf_execute_block
firinterp_rrrf_execute_block.restype = None
firinterp_rrrf_execute_block.argtypes = [firinterp_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
class struct_firinterp_crcf_s(Structure):
    pass

firinterp_crcf = ctypes.POINTER(struct_firinterp_crcf_s)
firinterp_crcf_create = liquiddsp.firinterp_crcf_create
firinterp_crcf_create.restype = firinterp_crcf
firinterp_crcf_create.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
firinterp_crcf_create_kaiser = liquiddsp.firinterp_crcf_create_kaiser
firinterp_crcf_create_kaiser.restype = firinterp_crcf
firinterp_crcf_create_kaiser.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float]
firinterp_crcf_create_prototype = liquiddsp.firinterp_crcf_create_prototype
firinterp_crcf_create_prototype.restype = firinterp_crcf
firinterp_crcf_create_prototype.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
firinterp_crcf_create_linear = liquiddsp.firinterp_crcf_create_linear
firinterp_crcf_create_linear.restype = firinterp_crcf
firinterp_crcf_create_linear.argtypes = [ctypes.c_uint32]
firinterp_crcf_create_window = liquiddsp.firinterp_crcf_create_window
firinterp_crcf_create_window.restype = firinterp_crcf
firinterp_crcf_create_window.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
firinterp_crcf_destroy = liquiddsp.firinterp_crcf_destroy
firinterp_crcf_destroy.restype = None
firinterp_crcf_destroy.argtypes = [firinterp_crcf]
firinterp_crcf_print = liquiddsp.firinterp_crcf_print
firinterp_crcf_print.restype = None
firinterp_crcf_print.argtypes = [firinterp_crcf]
firinterp_crcf_reset = liquiddsp.firinterp_crcf_reset
firinterp_crcf_reset.restype = None
firinterp_crcf_reset.argtypes = [firinterp_crcf]
firinterp_crcf_get_interp_rate = liquiddsp.firinterp_crcf_get_interp_rate
firinterp_crcf_get_interp_rate.restype = ctypes.c_uint32
firinterp_crcf_get_interp_rate.argtypes = [firinterp_crcf]
firinterp_crcf_get_sub_len = liquiddsp.firinterp_crcf_get_sub_len
firinterp_crcf_get_sub_len.restype = ctypes.c_uint32
firinterp_crcf_get_sub_len.argtypes = [firinterp_crcf]
firinterp_crcf_set_scale = liquiddsp.firinterp_crcf_set_scale
firinterp_crcf_set_scale.restype = None
firinterp_crcf_set_scale.argtypes = [firinterp_crcf, ctypes.c_float]
firinterp_crcf_get_scale = liquiddsp.firinterp_crcf_get_scale
firinterp_crcf_get_scale.restype = None
firinterp_crcf_get_scale.argtypes = [firinterp_crcf, ctypes.POINTER(ctypes.c_float)]
firinterp_crcf_execute = liquiddsp.firinterp_crcf_execute
firinterp_crcf_execute.restype = None
firinterp_crcf_execute.argtypes = [firinterp_crcf, liquid_float_complex, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
firinterp_crcf_execute_block = liquiddsp.firinterp_crcf_execute_block
firinterp_crcf_execute_block.restype = None
firinterp_crcf_execute_block.argtypes = [firinterp_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
class struct_firinterp_cccf_s(Structure):
    pass

firinterp_cccf = ctypes.POINTER(struct_firinterp_cccf_s)
firinterp_cccf_create = liquiddsp.firinterp_cccf_create
firinterp_cccf_create.restype = firinterp_cccf
firinterp_cccf_create.argtypes = [ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
firinterp_cccf_create_kaiser = liquiddsp.firinterp_cccf_create_kaiser
firinterp_cccf_create_kaiser.restype = firinterp_cccf
firinterp_cccf_create_kaiser.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float]
firinterp_cccf_create_prototype = liquiddsp.firinterp_cccf_create_prototype
firinterp_cccf_create_prototype.restype = firinterp_cccf
firinterp_cccf_create_prototype.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
firinterp_cccf_create_linear = liquiddsp.firinterp_cccf_create_linear
firinterp_cccf_create_linear.restype = firinterp_cccf
firinterp_cccf_create_linear.argtypes = [ctypes.c_uint32]
firinterp_cccf_create_window = liquiddsp.firinterp_cccf_create_window
firinterp_cccf_create_window.restype = firinterp_cccf
firinterp_cccf_create_window.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
firinterp_cccf_destroy = liquiddsp.firinterp_cccf_destroy
firinterp_cccf_destroy.restype = None
firinterp_cccf_destroy.argtypes = [firinterp_cccf]
firinterp_cccf_print = liquiddsp.firinterp_cccf_print
firinterp_cccf_print.restype = None
firinterp_cccf_print.argtypes = [firinterp_cccf]
firinterp_cccf_reset = liquiddsp.firinterp_cccf_reset
firinterp_cccf_reset.restype = None
firinterp_cccf_reset.argtypes = [firinterp_cccf]
firinterp_cccf_get_interp_rate = liquiddsp.firinterp_cccf_get_interp_rate
firinterp_cccf_get_interp_rate.restype = ctypes.c_uint32
firinterp_cccf_get_interp_rate.argtypes = [firinterp_cccf]
firinterp_cccf_get_sub_len = liquiddsp.firinterp_cccf_get_sub_len
firinterp_cccf_get_sub_len.restype = ctypes.c_uint32
firinterp_cccf_get_sub_len.argtypes = [firinterp_cccf]
firinterp_cccf_set_scale = liquiddsp.firinterp_cccf_set_scale
firinterp_cccf_set_scale.restype = None
firinterp_cccf_set_scale.argtypes = [firinterp_cccf, liquid_float_complex]
firinterp_cccf_get_scale = liquiddsp.firinterp_cccf_get_scale
firinterp_cccf_get_scale.restype = None
firinterp_cccf_get_scale.argtypes = [firinterp_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
firinterp_cccf_execute = liquiddsp.firinterp_cccf_execute
firinterp_cccf_execute.restype = None
firinterp_cccf_execute.argtypes = [firinterp_cccf, liquid_float_complex, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
firinterp_cccf_execute_block = liquiddsp.firinterp_cccf_execute_block
firinterp_cccf_execute_block.restype = None
firinterp_cccf_execute_block.argtypes = [firinterp_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
class struct_iirinterp_rrrf_s(Structure):
    pass

iirinterp_rrrf = ctypes.POINTER(struct_iirinterp_rrrf_s)
iirinterp_rrrf_create = liquiddsp.iirinterp_rrrf_create
iirinterp_rrrf_create.restype = iirinterp_rrrf
iirinterp_rrrf_create.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
iirinterp_rrrf_create_default = liquiddsp.iirinterp_rrrf_create_default
iirinterp_rrrf_create_default.restype = iirinterp_rrrf
iirinterp_rrrf_create_default.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
iirinterp_rrrf_create_prototype = liquiddsp.iirinterp_rrrf_create_prototype
iirinterp_rrrf_create_prototype.restype = iirinterp_rrrf
iirinterp_rrrf_create_prototype.argtypes = [ctypes.c_uint32, liquid_iirdes_filtertype, liquid_iirdes_bandtype, liquid_iirdes_format, ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
iirinterp_rrrf_destroy = liquiddsp.iirinterp_rrrf_destroy
iirinterp_rrrf_destroy.restype = None
iirinterp_rrrf_destroy.argtypes = [iirinterp_rrrf]
iirinterp_rrrf_print = liquiddsp.iirinterp_rrrf_print
iirinterp_rrrf_print.restype = None
iirinterp_rrrf_print.argtypes = [iirinterp_rrrf]
iirinterp_rrrf_reset = liquiddsp.iirinterp_rrrf_reset
iirinterp_rrrf_reset.restype = None
iirinterp_rrrf_reset.argtypes = [iirinterp_rrrf]
iirinterp_rrrf_execute = liquiddsp.iirinterp_rrrf_execute
iirinterp_rrrf_execute.restype = None
iirinterp_rrrf_execute.argtypes = [iirinterp_rrrf, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
iirinterp_rrrf_execute_block = liquiddsp.iirinterp_rrrf_execute_block
iirinterp_rrrf_execute_block.restype = None
iirinterp_rrrf_execute_block.argtypes = [iirinterp_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
iirinterp_rrrf_groupdelay = liquiddsp.iirinterp_rrrf_groupdelay
iirinterp_rrrf_groupdelay.restype = ctypes.c_float
iirinterp_rrrf_groupdelay.argtypes = [iirinterp_rrrf, ctypes.c_float]
class struct_iirinterp_crcf_s(Structure):
    pass

iirinterp_crcf = ctypes.POINTER(struct_iirinterp_crcf_s)
iirinterp_crcf_create = liquiddsp.iirinterp_crcf_create
iirinterp_crcf_create.restype = iirinterp_crcf
iirinterp_crcf_create.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
iirinterp_crcf_create_default = liquiddsp.iirinterp_crcf_create_default
iirinterp_crcf_create_default.restype = iirinterp_crcf
iirinterp_crcf_create_default.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
iirinterp_crcf_create_prototype = liquiddsp.iirinterp_crcf_create_prototype
iirinterp_crcf_create_prototype.restype = iirinterp_crcf
iirinterp_crcf_create_prototype.argtypes = [ctypes.c_uint32, liquid_iirdes_filtertype, liquid_iirdes_bandtype, liquid_iirdes_format, ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
iirinterp_crcf_destroy = liquiddsp.iirinterp_crcf_destroy
iirinterp_crcf_destroy.restype = None
iirinterp_crcf_destroy.argtypes = [iirinterp_crcf]
iirinterp_crcf_print = liquiddsp.iirinterp_crcf_print
iirinterp_crcf_print.restype = None
iirinterp_crcf_print.argtypes = [iirinterp_crcf]
iirinterp_crcf_reset = liquiddsp.iirinterp_crcf_reset
iirinterp_crcf_reset.restype = None
iirinterp_crcf_reset.argtypes = [iirinterp_crcf]
iirinterp_crcf_execute = liquiddsp.iirinterp_crcf_execute
iirinterp_crcf_execute.restype = None
iirinterp_crcf_execute.argtypes = [iirinterp_crcf, liquid_float_complex, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
iirinterp_crcf_execute_block = liquiddsp.iirinterp_crcf_execute_block
iirinterp_crcf_execute_block.restype = None
iirinterp_crcf_execute_block.argtypes = [iirinterp_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
iirinterp_crcf_groupdelay = liquiddsp.iirinterp_crcf_groupdelay
iirinterp_crcf_groupdelay.restype = ctypes.c_float
iirinterp_crcf_groupdelay.argtypes = [iirinterp_crcf, ctypes.c_float]
class struct_iirinterp_cccf_s(Structure):
    pass

iirinterp_cccf = ctypes.POINTER(struct_iirinterp_cccf_s)
iirinterp_cccf_create = liquiddsp.iirinterp_cccf_create
iirinterp_cccf_create.restype = iirinterp_cccf
iirinterp_cccf_create.argtypes = [ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
iirinterp_cccf_create_default = liquiddsp.iirinterp_cccf_create_default
iirinterp_cccf_create_default.restype = iirinterp_cccf
iirinterp_cccf_create_default.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
iirinterp_cccf_create_prototype = liquiddsp.iirinterp_cccf_create_prototype
iirinterp_cccf_create_prototype.restype = iirinterp_cccf
iirinterp_cccf_create_prototype.argtypes = [ctypes.c_uint32, liquid_iirdes_filtertype, liquid_iirdes_bandtype, liquid_iirdes_format, ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
iirinterp_cccf_destroy = liquiddsp.iirinterp_cccf_destroy
iirinterp_cccf_destroy.restype = None
iirinterp_cccf_destroy.argtypes = [iirinterp_cccf]
iirinterp_cccf_print = liquiddsp.iirinterp_cccf_print
iirinterp_cccf_print.restype = None
iirinterp_cccf_print.argtypes = [iirinterp_cccf]
iirinterp_cccf_reset = liquiddsp.iirinterp_cccf_reset
iirinterp_cccf_reset.restype = None
iirinterp_cccf_reset.argtypes = [iirinterp_cccf]
iirinterp_cccf_execute = liquiddsp.iirinterp_cccf_execute
iirinterp_cccf_execute.restype = None
iirinterp_cccf_execute.argtypes = [iirinterp_cccf, liquid_float_complex, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
iirinterp_cccf_execute_block = liquiddsp.iirinterp_cccf_execute_block
iirinterp_cccf_execute_block.restype = None
iirinterp_cccf_execute_block.argtypes = [iirinterp_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
iirinterp_cccf_groupdelay = liquiddsp.iirinterp_cccf_groupdelay
iirinterp_cccf_groupdelay.restype = ctypes.c_float
iirinterp_cccf_groupdelay.argtypes = [iirinterp_cccf, ctypes.c_float]
class struct_firdecim_rrrf_s(Structure):
    pass

firdecim_rrrf = ctypes.POINTER(struct_firdecim_rrrf_s)
firdecim_rrrf_create = liquiddsp.firdecim_rrrf_create
firdecim_rrrf_create.restype = firdecim_rrrf
firdecim_rrrf_create.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
firdecim_rrrf_create_kaiser = liquiddsp.firdecim_rrrf_create_kaiser
firdecim_rrrf_create_kaiser.restype = firdecim_rrrf
firdecim_rrrf_create_kaiser.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float]
firdecim_rrrf_create_prototype = liquiddsp.firdecim_rrrf_create_prototype
firdecim_rrrf_create_prototype.restype = firdecim_rrrf
firdecim_rrrf_create_prototype.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
firdecim_rrrf_destroy = liquiddsp.firdecim_rrrf_destroy
firdecim_rrrf_destroy.restype = None
firdecim_rrrf_destroy.argtypes = [firdecim_rrrf]
firdecim_rrrf_print = liquiddsp.firdecim_rrrf_print
firdecim_rrrf_print.restype = None
firdecim_rrrf_print.argtypes = [firdecim_rrrf]
firdecim_rrrf_reset = liquiddsp.firdecim_rrrf_reset
firdecim_rrrf_reset.restype = None
firdecim_rrrf_reset.argtypes = [firdecim_rrrf]
firdecim_rrrf_get_decim_rate = liquiddsp.firdecim_rrrf_get_decim_rate
firdecim_rrrf_get_decim_rate.restype = ctypes.c_uint32
firdecim_rrrf_get_decim_rate.argtypes = [firdecim_rrrf]
firdecim_rrrf_set_scale = liquiddsp.firdecim_rrrf_set_scale
firdecim_rrrf_set_scale.restype = None
firdecim_rrrf_set_scale.argtypes = [firdecim_rrrf, ctypes.c_float]
firdecim_rrrf_get_scale = liquiddsp.firdecim_rrrf_get_scale
firdecim_rrrf_get_scale.restype = None
firdecim_rrrf_get_scale.argtypes = [firdecim_rrrf, ctypes.POINTER(ctypes.c_float)]
firdecim_rrrf_execute = liquiddsp.firdecim_rrrf_execute
firdecim_rrrf_execute.restype = None
firdecim_rrrf_execute.argtypes = [firdecim_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
firdecim_rrrf_execute_block = liquiddsp.firdecim_rrrf_execute_block
firdecim_rrrf_execute_block.restype = None
firdecim_rrrf_execute_block.argtypes = [firdecim_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
class struct_firdecim_crcf_s(Structure):
    pass

firdecim_crcf = ctypes.POINTER(struct_firdecim_crcf_s)
firdecim_crcf_create = liquiddsp.firdecim_crcf_create
firdecim_crcf_create.restype = firdecim_crcf
firdecim_crcf_create.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
firdecim_crcf_create_kaiser = liquiddsp.firdecim_crcf_create_kaiser
firdecim_crcf_create_kaiser.restype = firdecim_crcf
firdecim_crcf_create_kaiser.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float]
firdecim_crcf_create_prototype = liquiddsp.firdecim_crcf_create_prototype
firdecim_crcf_create_prototype.restype = firdecim_crcf
firdecim_crcf_create_prototype.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
firdecim_crcf_destroy = liquiddsp.firdecim_crcf_destroy
firdecim_crcf_destroy.restype = None
firdecim_crcf_destroy.argtypes = [firdecim_crcf]
firdecim_crcf_print = liquiddsp.firdecim_crcf_print
firdecim_crcf_print.restype = None
firdecim_crcf_print.argtypes = [firdecim_crcf]
firdecim_crcf_reset = liquiddsp.firdecim_crcf_reset
firdecim_crcf_reset.restype = None
firdecim_crcf_reset.argtypes = [firdecim_crcf]
firdecim_crcf_get_decim_rate = liquiddsp.firdecim_crcf_get_decim_rate
firdecim_crcf_get_decim_rate.restype = ctypes.c_uint32
firdecim_crcf_get_decim_rate.argtypes = [firdecim_crcf]
firdecim_crcf_set_scale = liquiddsp.firdecim_crcf_set_scale
firdecim_crcf_set_scale.restype = None
firdecim_crcf_set_scale.argtypes = [firdecim_crcf, ctypes.c_float]
firdecim_crcf_get_scale = liquiddsp.firdecim_crcf_get_scale
firdecim_crcf_get_scale.restype = None
firdecim_crcf_get_scale.argtypes = [firdecim_crcf, ctypes.POINTER(ctypes.c_float)]
firdecim_crcf_execute = liquiddsp.firdecim_crcf_execute
firdecim_crcf_execute.restype = None
firdecim_crcf_execute.argtypes = [firdecim_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
firdecim_crcf_execute_block = liquiddsp.firdecim_crcf_execute_block
firdecim_crcf_execute_block.restype = None
firdecim_crcf_execute_block.argtypes = [firdecim_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
class struct_firdecim_cccf_s(Structure):
    pass

firdecim_cccf = ctypes.POINTER(struct_firdecim_cccf_s)
firdecim_cccf_create = liquiddsp.firdecim_cccf_create
firdecim_cccf_create.restype = firdecim_cccf
firdecim_cccf_create.argtypes = [ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
firdecim_cccf_create_kaiser = liquiddsp.firdecim_cccf_create_kaiser
firdecim_cccf_create_kaiser.restype = firdecim_cccf
firdecim_cccf_create_kaiser.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float]
firdecim_cccf_create_prototype = liquiddsp.firdecim_cccf_create_prototype
firdecim_cccf_create_prototype.restype = firdecim_cccf
firdecim_cccf_create_prototype.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
firdecim_cccf_destroy = liquiddsp.firdecim_cccf_destroy
firdecim_cccf_destroy.restype = None
firdecim_cccf_destroy.argtypes = [firdecim_cccf]
firdecim_cccf_print = liquiddsp.firdecim_cccf_print
firdecim_cccf_print.restype = None
firdecim_cccf_print.argtypes = [firdecim_cccf]
firdecim_cccf_reset = liquiddsp.firdecim_cccf_reset
firdecim_cccf_reset.restype = None
firdecim_cccf_reset.argtypes = [firdecim_cccf]
firdecim_cccf_get_decim_rate = liquiddsp.firdecim_cccf_get_decim_rate
firdecim_cccf_get_decim_rate.restype = ctypes.c_uint32
firdecim_cccf_get_decim_rate.argtypes = [firdecim_cccf]
firdecim_cccf_set_scale = liquiddsp.firdecim_cccf_set_scale
firdecim_cccf_set_scale.restype = None
firdecim_cccf_set_scale.argtypes = [firdecim_cccf, liquid_float_complex]
firdecim_cccf_get_scale = liquiddsp.firdecim_cccf_get_scale
firdecim_cccf_get_scale.restype = None
firdecim_cccf_get_scale.argtypes = [firdecim_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
firdecim_cccf_execute = liquiddsp.firdecim_cccf_execute
firdecim_cccf_execute.restype = None
firdecim_cccf_execute.argtypes = [firdecim_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
firdecim_cccf_execute_block = liquiddsp.firdecim_cccf_execute_block
firdecim_cccf_execute_block.restype = None
firdecim_cccf_execute_block.argtypes = [firdecim_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
class struct_iirdecim_rrrf_s(Structure):
    pass

iirdecim_rrrf = ctypes.POINTER(struct_iirdecim_rrrf_s)
iirdecim_rrrf_create = liquiddsp.iirdecim_rrrf_create
iirdecim_rrrf_create.restype = iirdecim_rrrf
iirdecim_rrrf_create.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
iirdecim_rrrf_create_default = liquiddsp.iirdecim_rrrf_create_default
iirdecim_rrrf_create_default.restype = iirdecim_rrrf
iirdecim_rrrf_create_default.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
iirdecim_rrrf_create_prototype = liquiddsp.iirdecim_rrrf_create_prototype
iirdecim_rrrf_create_prototype.restype = iirdecim_rrrf
iirdecim_rrrf_create_prototype.argtypes = [ctypes.c_uint32, liquid_iirdes_filtertype, liquid_iirdes_bandtype, liquid_iirdes_format, ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
iirdecim_rrrf_destroy = liquiddsp.iirdecim_rrrf_destroy
iirdecim_rrrf_destroy.restype = None
iirdecim_rrrf_destroy.argtypes = [iirdecim_rrrf]
iirdecim_rrrf_print = liquiddsp.iirdecim_rrrf_print
iirdecim_rrrf_print.restype = None
iirdecim_rrrf_print.argtypes = [iirdecim_rrrf]
iirdecim_rrrf_reset = liquiddsp.iirdecim_rrrf_reset
iirdecim_rrrf_reset.restype = None
iirdecim_rrrf_reset.argtypes = [iirdecim_rrrf]
iirdecim_rrrf_execute = liquiddsp.iirdecim_rrrf_execute
iirdecim_rrrf_execute.restype = None
iirdecim_rrrf_execute.argtypes = [iirdecim_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
iirdecim_rrrf_execute_block = liquiddsp.iirdecim_rrrf_execute_block
iirdecim_rrrf_execute_block.restype = None
iirdecim_rrrf_execute_block.argtypes = [iirdecim_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
iirdecim_rrrf_groupdelay = liquiddsp.iirdecim_rrrf_groupdelay
iirdecim_rrrf_groupdelay.restype = ctypes.c_float
iirdecim_rrrf_groupdelay.argtypes = [iirdecim_rrrf, ctypes.c_float]
class struct_iirdecim_crcf_s(Structure):
    pass

iirdecim_crcf = ctypes.POINTER(struct_iirdecim_crcf_s)
iirdecim_crcf_create = liquiddsp.iirdecim_crcf_create
iirdecim_crcf_create.restype = iirdecim_crcf
iirdecim_crcf_create.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
iirdecim_crcf_create_default = liquiddsp.iirdecim_crcf_create_default
iirdecim_crcf_create_default.restype = iirdecim_crcf
iirdecim_crcf_create_default.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
iirdecim_crcf_create_prototype = liquiddsp.iirdecim_crcf_create_prototype
iirdecim_crcf_create_prototype.restype = iirdecim_crcf
iirdecim_crcf_create_prototype.argtypes = [ctypes.c_uint32, liquid_iirdes_filtertype, liquid_iirdes_bandtype, liquid_iirdes_format, ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
iirdecim_crcf_destroy = liquiddsp.iirdecim_crcf_destroy
iirdecim_crcf_destroy.restype = None
iirdecim_crcf_destroy.argtypes = [iirdecim_crcf]
iirdecim_crcf_print = liquiddsp.iirdecim_crcf_print
iirdecim_crcf_print.restype = None
iirdecim_crcf_print.argtypes = [iirdecim_crcf]
iirdecim_crcf_reset = liquiddsp.iirdecim_crcf_reset
iirdecim_crcf_reset.restype = None
iirdecim_crcf_reset.argtypes = [iirdecim_crcf]
iirdecim_crcf_execute = liquiddsp.iirdecim_crcf_execute
iirdecim_crcf_execute.restype = None
iirdecim_crcf_execute.argtypes = [iirdecim_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
iirdecim_crcf_execute_block = liquiddsp.iirdecim_crcf_execute_block
iirdecim_crcf_execute_block.restype = None
iirdecim_crcf_execute_block.argtypes = [iirdecim_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
iirdecim_crcf_groupdelay = liquiddsp.iirdecim_crcf_groupdelay
iirdecim_crcf_groupdelay.restype = ctypes.c_float
iirdecim_crcf_groupdelay.argtypes = [iirdecim_crcf, ctypes.c_float]
class struct_iirdecim_cccf_s(Structure):
    pass

iirdecim_cccf = ctypes.POINTER(struct_iirdecim_cccf_s)
iirdecim_cccf_create = liquiddsp.iirdecim_cccf_create
iirdecim_cccf_create.restype = iirdecim_cccf
iirdecim_cccf_create.argtypes = [ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
iirdecim_cccf_create_default = liquiddsp.iirdecim_cccf_create_default
iirdecim_cccf_create_default.restype = iirdecim_cccf
iirdecim_cccf_create_default.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
iirdecim_cccf_create_prototype = liquiddsp.iirdecim_cccf_create_prototype
iirdecim_cccf_create_prototype.restype = iirdecim_cccf
iirdecim_cccf_create_prototype.argtypes = [ctypes.c_uint32, liquid_iirdes_filtertype, liquid_iirdes_bandtype, liquid_iirdes_format, ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
iirdecim_cccf_destroy = liquiddsp.iirdecim_cccf_destroy
iirdecim_cccf_destroy.restype = None
iirdecim_cccf_destroy.argtypes = [iirdecim_cccf]
iirdecim_cccf_print = liquiddsp.iirdecim_cccf_print
iirdecim_cccf_print.restype = None
iirdecim_cccf_print.argtypes = [iirdecim_cccf]
iirdecim_cccf_reset = liquiddsp.iirdecim_cccf_reset
iirdecim_cccf_reset.restype = None
iirdecim_cccf_reset.argtypes = [iirdecim_cccf]
iirdecim_cccf_execute = liquiddsp.iirdecim_cccf_execute
iirdecim_cccf_execute.restype = None
iirdecim_cccf_execute.argtypes = [iirdecim_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
iirdecim_cccf_execute_block = liquiddsp.iirdecim_cccf_execute_block
iirdecim_cccf_execute_block.restype = None
iirdecim_cccf_execute_block.argtypes = [iirdecim_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
iirdecim_cccf_groupdelay = liquiddsp.iirdecim_cccf_groupdelay
iirdecim_cccf_groupdelay.restype = ctypes.c_float
iirdecim_cccf_groupdelay.argtypes = [iirdecim_cccf, ctypes.c_float]
class struct_resamp2_rrrf_s(Structure):
    pass

resamp2_rrrf = ctypes.POINTER(struct_resamp2_rrrf_s)
resamp2_rrrf_create = liquiddsp.resamp2_rrrf_create
resamp2_rrrf_create.restype = resamp2_rrrf
resamp2_rrrf_create.argtypes = [ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
resamp2_rrrf_recreate = liquiddsp.resamp2_rrrf_recreate
resamp2_rrrf_recreate.restype = resamp2_rrrf
resamp2_rrrf_recreate.argtypes = [resamp2_rrrf, ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
resamp2_rrrf_destroy = liquiddsp.resamp2_rrrf_destroy
resamp2_rrrf_destroy.restype = None
resamp2_rrrf_destroy.argtypes = [resamp2_rrrf]
resamp2_rrrf_print = liquiddsp.resamp2_rrrf_print
resamp2_rrrf_print.restype = None
resamp2_rrrf_print.argtypes = [resamp2_rrrf]
resamp2_rrrf_reset = liquiddsp.resamp2_rrrf_reset
resamp2_rrrf_reset.restype = None
resamp2_rrrf_reset.argtypes = [resamp2_rrrf]
resamp2_rrrf_get_delay = liquiddsp.resamp2_rrrf_get_delay
resamp2_rrrf_get_delay.restype = ctypes.c_uint32
resamp2_rrrf_get_delay.argtypes = [resamp2_rrrf]
resamp2_rrrf_filter_execute = liquiddsp.resamp2_rrrf_filter_execute
resamp2_rrrf_filter_execute.restype = None
resamp2_rrrf_filter_execute.argtypes = [resamp2_rrrf, ctypes.c_float, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
resamp2_rrrf_analyzer_execute = liquiddsp.resamp2_rrrf_analyzer_execute
resamp2_rrrf_analyzer_execute.restype = None
resamp2_rrrf_analyzer_execute.argtypes = [resamp2_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
resamp2_rrrf_synthesizer_execute = liquiddsp.resamp2_rrrf_synthesizer_execute
resamp2_rrrf_synthesizer_execute.restype = None
resamp2_rrrf_synthesizer_execute.argtypes = [resamp2_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
resamp2_rrrf_decim_execute = liquiddsp.resamp2_rrrf_decim_execute
resamp2_rrrf_decim_execute.restype = None
resamp2_rrrf_decim_execute.argtypes = [resamp2_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
resamp2_rrrf_interp_execute = liquiddsp.resamp2_rrrf_interp_execute
resamp2_rrrf_interp_execute.restype = None
resamp2_rrrf_interp_execute.argtypes = [resamp2_rrrf, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
class struct_resamp2_crcf_s(Structure):
    pass

resamp2_crcf = ctypes.POINTER(struct_resamp2_crcf_s)
resamp2_crcf_create = liquiddsp.resamp2_crcf_create
resamp2_crcf_create.restype = resamp2_crcf
resamp2_crcf_create.argtypes = [ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
resamp2_crcf_recreate = liquiddsp.resamp2_crcf_recreate
resamp2_crcf_recreate.restype = resamp2_crcf
resamp2_crcf_recreate.argtypes = [resamp2_crcf, ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
resamp2_crcf_destroy = liquiddsp.resamp2_crcf_destroy
resamp2_crcf_destroy.restype = None
resamp2_crcf_destroy.argtypes = [resamp2_crcf]
resamp2_crcf_print = liquiddsp.resamp2_crcf_print
resamp2_crcf_print.restype = None
resamp2_crcf_print.argtypes = [resamp2_crcf]
resamp2_crcf_reset = liquiddsp.resamp2_crcf_reset
resamp2_crcf_reset.restype = None
resamp2_crcf_reset.argtypes = [resamp2_crcf]
resamp2_crcf_get_delay = liquiddsp.resamp2_crcf_get_delay
resamp2_crcf_get_delay.restype = ctypes.c_uint32
resamp2_crcf_get_delay.argtypes = [resamp2_crcf]
resamp2_crcf_filter_execute = liquiddsp.resamp2_crcf_filter_execute
resamp2_crcf_filter_execute.restype = None
resamp2_crcf_filter_execute.argtypes = [resamp2_crcf, liquid_float_complex, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
resamp2_crcf_analyzer_execute = liquiddsp.resamp2_crcf_analyzer_execute
resamp2_crcf_analyzer_execute.restype = None
resamp2_crcf_analyzer_execute.argtypes = [resamp2_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
resamp2_crcf_synthesizer_execute = liquiddsp.resamp2_crcf_synthesizer_execute
resamp2_crcf_synthesizer_execute.restype = None
resamp2_crcf_synthesizer_execute.argtypes = [resamp2_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
resamp2_crcf_decim_execute = liquiddsp.resamp2_crcf_decim_execute
resamp2_crcf_decim_execute.restype = None
resamp2_crcf_decim_execute.argtypes = [resamp2_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
resamp2_crcf_interp_execute = liquiddsp.resamp2_crcf_interp_execute
resamp2_crcf_interp_execute.restype = None
resamp2_crcf_interp_execute.argtypes = [resamp2_crcf, liquid_float_complex, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
class struct_resamp2_cccf_s(Structure):
    pass

resamp2_cccf = ctypes.POINTER(struct_resamp2_cccf_s)
resamp2_cccf_create = liquiddsp.resamp2_cccf_create
resamp2_cccf_create.restype = resamp2_cccf
resamp2_cccf_create.argtypes = [ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
resamp2_cccf_recreate = liquiddsp.resamp2_cccf_recreate
resamp2_cccf_recreate.restype = resamp2_cccf
resamp2_cccf_recreate.argtypes = [resamp2_cccf, ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
resamp2_cccf_destroy = liquiddsp.resamp2_cccf_destroy
resamp2_cccf_destroy.restype = None
resamp2_cccf_destroy.argtypes = [resamp2_cccf]
resamp2_cccf_print = liquiddsp.resamp2_cccf_print
resamp2_cccf_print.restype = None
resamp2_cccf_print.argtypes = [resamp2_cccf]
resamp2_cccf_reset = liquiddsp.resamp2_cccf_reset
resamp2_cccf_reset.restype = None
resamp2_cccf_reset.argtypes = [resamp2_cccf]
resamp2_cccf_get_delay = liquiddsp.resamp2_cccf_get_delay
resamp2_cccf_get_delay.restype = ctypes.c_uint32
resamp2_cccf_get_delay.argtypes = [resamp2_cccf]
resamp2_cccf_filter_execute = liquiddsp.resamp2_cccf_filter_execute
resamp2_cccf_filter_execute.restype = None
resamp2_cccf_filter_execute.argtypes = [resamp2_cccf, liquid_float_complex, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
resamp2_cccf_analyzer_execute = liquiddsp.resamp2_cccf_analyzer_execute
resamp2_cccf_analyzer_execute.restype = None
resamp2_cccf_analyzer_execute.argtypes = [resamp2_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
resamp2_cccf_synthesizer_execute = liquiddsp.resamp2_cccf_synthesizer_execute
resamp2_cccf_synthesizer_execute.restype = None
resamp2_cccf_synthesizer_execute.argtypes = [resamp2_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
resamp2_cccf_decim_execute = liquiddsp.resamp2_cccf_decim_execute
resamp2_cccf_decim_execute.restype = None
resamp2_cccf_decim_execute.argtypes = [resamp2_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
resamp2_cccf_interp_execute = liquiddsp.resamp2_cccf_interp_execute
resamp2_cccf_interp_execute.restype = None
resamp2_cccf_interp_execute.argtypes = [resamp2_cccf, liquid_float_complex, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
class struct_rresamp_rrrf_s(Structure):
    pass

rresamp_rrrf = ctypes.POINTER(struct_rresamp_rrrf_s)
rresamp_rrrf_create = liquiddsp.rresamp_rrrf_create
rresamp_rrrf_create.restype = rresamp_rrrf
rresamp_rrrf_create.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
rresamp_rrrf_create_kaiser = liquiddsp.rresamp_rrrf_create_kaiser
rresamp_rrrf_create_kaiser.restype = rresamp_rrrf
rresamp_rrrf_create_kaiser.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
rresamp_rrrf_create_prototype = liquiddsp.rresamp_rrrf_create_prototype
rresamp_rrrf_create_prototype.restype = rresamp_rrrf
rresamp_rrrf_create_prototype.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float]
rresamp_rrrf_create_default = liquiddsp.rresamp_rrrf_create_default
rresamp_rrrf_create_default.restype = rresamp_rrrf
rresamp_rrrf_create_default.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
rresamp_rrrf_destroy = liquiddsp.rresamp_rrrf_destroy
rresamp_rrrf_destroy.restype = None
rresamp_rrrf_destroy.argtypes = [rresamp_rrrf]
rresamp_rrrf_print = liquiddsp.rresamp_rrrf_print
rresamp_rrrf_print.restype = None
rresamp_rrrf_print.argtypes = [rresamp_rrrf]
rresamp_rrrf_reset = liquiddsp.rresamp_rrrf_reset
rresamp_rrrf_reset.restype = None
rresamp_rrrf_reset.argtypes = [rresamp_rrrf]
rresamp_rrrf_set_scale = liquiddsp.rresamp_rrrf_set_scale
rresamp_rrrf_set_scale.restype = None
rresamp_rrrf_set_scale.argtypes = [rresamp_rrrf, ctypes.c_float]
rresamp_rrrf_get_scale = liquiddsp.rresamp_rrrf_get_scale
rresamp_rrrf_get_scale.restype = None
rresamp_rrrf_get_scale.argtypes = [rresamp_rrrf, ctypes.POINTER(ctypes.c_float)]
rresamp_rrrf_get_delay = liquiddsp.rresamp_rrrf_get_delay
rresamp_rrrf_get_delay.restype = ctypes.c_uint32
rresamp_rrrf_get_delay.argtypes = [rresamp_rrrf]
rresamp_rrrf_get_P = liquiddsp.rresamp_rrrf_get_P
rresamp_rrrf_get_P.restype = ctypes.c_uint32
rresamp_rrrf_get_P.argtypes = [rresamp_rrrf]
rresamp_rrrf_get_interp = liquiddsp.rresamp_rrrf_get_interp
rresamp_rrrf_get_interp.restype = ctypes.c_uint32
rresamp_rrrf_get_interp.argtypes = [rresamp_rrrf]
rresamp_rrrf_get_Q = liquiddsp.rresamp_rrrf_get_Q
rresamp_rrrf_get_Q.restype = ctypes.c_uint32
rresamp_rrrf_get_Q.argtypes = [rresamp_rrrf]
rresamp_rrrf_get_decim = liquiddsp.rresamp_rrrf_get_decim
rresamp_rrrf_get_decim.restype = ctypes.c_uint32
rresamp_rrrf_get_decim.argtypes = [rresamp_rrrf]
rresamp_rrrf_get_block_len = liquiddsp.rresamp_rrrf_get_block_len
rresamp_rrrf_get_block_len.restype = ctypes.c_uint32
rresamp_rrrf_get_block_len.argtypes = [rresamp_rrrf]
rresamp_rrrf_get_rate = liquiddsp.rresamp_rrrf_get_rate
rresamp_rrrf_get_rate.restype = ctypes.c_float
rresamp_rrrf_get_rate.argtypes = [rresamp_rrrf]
rresamp_rrrf_write = liquiddsp.rresamp_rrrf_write
rresamp_rrrf_write.restype = None
rresamp_rrrf_write.argtypes = [rresamp_rrrf, ctypes.POINTER(ctypes.c_float)]
rresamp_rrrf_execute = liquiddsp.rresamp_rrrf_execute
rresamp_rrrf_execute.restype = None
rresamp_rrrf_execute.argtypes = [rresamp_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
rresamp_rrrf_execute_block = liquiddsp.rresamp_rrrf_execute_block
rresamp_rrrf_execute_block.restype = None
rresamp_rrrf_execute_block.argtypes = [rresamp_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
class struct_rresamp_crcf_s(Structure):
    pass

rresamp_crcf = ctypes.POINTER(struct_rresamp_crcf_s)
rresamp_crcf_create = liquiddsp.rresamp_crcf_create
rresamp_crcf_create.restype = rresamp_crcf
rresamp_crcf_create.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
rresamp_crcf_create_kaiser = liquiddsp.rresamp_crcf_create_kaiser
rresamp_crcf_create_kaiser.restype = rresamp_crcf
rresamp_crcf_create_kaiser.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
rresamp_crcf_create_prototype = liquiddsp.rresamp_crcf_create_prototype
rresamp_crcf_create_prototype.restype = rresamp_crcf
rresamp_crcf_create_prototype.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float]
rresamp_crcf_create_default = liquiddsp.rresamp_crcf_create_default
rresamp_crcf_create_default.restype = rresamp_crcf
rresamp_crcf_create_default.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
rresamp_crcf_destroy = liquiddsp.rresamp_crcf_destroy
rresamp_crcf_destroy.restype = None
rresamp_crcf_destroy.argtypes = [rresamp_crcf]
rresamp_crcf_print = liquiddsp.rresamp_crcf_print
rresamp_crcf_print.restype = None
rresamp_crcf_print.argtypes = [rresamp_crcf]
rresamp_crcf_reset = liquiddsp.rresamp_crcf_reset
rresamp_crcf_reset.restype = None
rresamp_crcf_reset.argtypes = [rresamp_crcf]
rresamp_crcf_set_scale = liquiddsp.rresamp_crcf_set_scale
rresamp_crcf_set_scale.restype = None
rresamp_crcf_set_scale.argtypes = [rresamp_crcf, ctypes.c_float]
rresamp_crcf_get_scale = liquiddsp.rresamp_crcf_get_scale
rresamp_crcf_get_scale.restype = None
rresamp_crcf_get_scale.argtypes = [rresamp_crcf, ctypes.POINTER(ctypes.c_float)]
rresamp_crcf_get_delay = liquiddsp.rresamp_crcf_get_delay
rresamp_crcf_get_delay.restype = ctypes.c_uint32
rresamp_crcf_get_delay.argtypes = [rresamp_crcf]
rresamp_crcf_get_P = liquiddsp.rresamp_crcf_get_P
rresamp_crcf_get_P.restype = ctypes.c_uint32
rresamp_crcf_get_P.argtypes = [rresamp_crcf]
rresamp_crcf_get_interp = liquiddsp.rresamp_crcf_get_interp
rresamp_crcf_get_interp.restype = ctypes.c_uint32
rresamp_crcf_get_interp.argtypes = [rresamp_crcf]
rresamp_crcf_get_Q = liquiddsp.rresamp_crcf_get_Q
rresamp_crcf_get_Q.restype = ctypes.c_uint32
rresamp_crcf_get_Q.argtypes = [rresamp_crcf]
rresamp_crcf_get_decim = liquiddsp.rresamp_crcf_get_decim
rresamp_crcf_get_decim.restype = ctypes.c_uint32
rresamp_crcf_get_decim.argtypes = [rresamp_crcf]
rresamp_crcf_get_block_len = liquiddsp.rresamp_crcf_get_block_len
rresamp_crcf_get_block_len.restype = ctypes.c_uint32
rresamp_crcf_get_block_len.argtypes = [rresamp_crcf]
rresamp_crcf_get_rate = liquiddsp.rresamp_crcf_get_rate
rresamp_crcf_get_rate.restype = ctypes.c_float
rresamp_crcf_get_rate.argtypes = [rresamp_crcf]
rresamp_crcf_write = liquiddsp.rresamp_crcf_write
rresamp_crcf_write.restype = None
rresamp_crcf_write.argtypes = [rresamp_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
rresamp_crcf_execute = liquiddsp.rresamp_crcf_execute
rresamp_crcf_execute.restype = None
rresamp_crcf_execute.argtypes = [rresamp_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
rresamp_crcf_execute_block = liquiddsp.rresamp_crcf_execute_block
rresamp_crcf_execute_block.restype = None
rresamp_crcf_execute_block.argtypes = [rresamp_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
class struct_rresamp_cccf_s(Structure):
    pass

rresamp_cccf = ctypes.POINTER(struct_rresamp_cccf_s)
rresamp_cccf_create = liquiddsp.rresamp_cccf_create
rresamp_cccf_create.restype = rresamp_cccf
rresamp_cccf_create.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
rresamp_cccf_create_kaiser = liquiddsp.rresamp_cccf_create_kaiser
rresamp_cccf_create_kaiser.restype = rresamp_cccf
rresamp_cccf_create_kaiser.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
rresamp_cccf_create_prototype = liquiddsp.rresamp_cccf_create_prototype
rresamp_cccf_create_prototype.restype = rresamp_cccf
rresamp_cccf_create_prototype.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float]
rresamp_cccf_create_default = liquiddsp.rresamp_cccf_create_default
rresamp_cccf_create_default.restype = rresamp_cccf
rresamp_cccf_create_default.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
rresamp_cccf_destroy = liquiddsp.rresamp_cccf_destroy
rresamp_cccf_destroy.restype = None
rresamp_cccf_destroy.argtypes = [rresamp_cccf]
rresamp_cccf_print = liquiddsp.rresamp_cccf_print
rresamp_cccf_print.restype = None
rresamp_cccf_print.argtypes = [rresamp_cccf]
rresamp_cccf_reset = liquiddsp.rresamp_cccf_reset
rresamp_cccf_reset.restype = None
rresamp_cccf_reset.argtypes = [rresamp_cccf]
rresamp_cccf_set_scale = liquiddsp.rresamp_cccf_set_scale
rresamp_cccf_set_scale.restype = None
rresamp_cccf_set_scale.argtypes = [rresamp_cccf, liquid_float_complex]
rresamp_cccf_get_scale = liquiddsp.rresamp_cccf_get_scale
rresamp_cccf_get_scale.restype = None
rresamp_cccf_get_scale.argtypes = [rresamp_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
rresamp_cccf_get_delay = liquiddsp.rresamp_cccf_get_delay
rresamp_cccf_get_delay.restype = ctypes.c_uint32
rresamp_cccf_get_delay.argtypes = [rresamp_cccf]
rresamp_cccf_get_P = liquiddsp.rresamp_cccf_get_P
rresamp_cccf_get_P.restype = ctypes.c_uint32
rresamp_cccf_get_P.argtypes = [rresamp_cccf]
rresamp_cccf_get_interp = liquiddsp.rresamp_cccf_get_interp
rresamp_cccf_get_interp.restype = ctypes.c_uint32
rresamp_cccf_get_interp.argtypes = [rresamp_cccf]
rresamp_cccf_get_Q = liquiddsp.rresamp_cccf_get_Q
rresamp_cccf_get_Q.restype = ctypes.c_uint32
rresamp_cccf_get_Q.argtypes = [rresamp_cccf]
rresamp_cccf_get_decim = liquiddsp.rresamp_cccf_get_decim
rresamp_cccf_get_decim.restype = ctypes.c_uint32
rresamp_cccf_get_decim.argtypes = [rresamp_cccf]
rresamp_cccf_get_block_len = liquiddsp.rresamp_cccf_get_block_len
rresamp_cccf_get_block_len.restype = ctypes.c_uint32
rresamp_cccf_get_block_len.argtypes = [rresamp_cccf]
rresamp_cccf_get_rate = liquiddsp.rresamp_cccf_get_rate
rresamp_cccf_get_rate.restype = ctypes.c_float
rresamp_cccf_get_rate.argtypes = [rresamp_cccf]
rresamp_cccf_write = liquiddsp.rresamp_cccf_write
rresamp_cccf_write.restype = None
rresamp_cccf_write.argtypes = [rresamp_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
rresamp_cccf_execute = liquiddsp.rresamp_cccf_execute
rresamp_cccf_execute.restype = None
rresamp_cccf_execute.argtypes = [rresamp_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
rresamp_cccf_execute_block = liquiddsp.rresamp_cccf_execute_block
rresamp_cccf_execute_block.restype = None
rresamp_cccf_execute_block.argtypes = [rresamp_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
class struct_resamp_rrrf_s(Structure):
    pass

resamp_rrrf = ctypes.POINTER(struct_resamp_rrrf_s)
resamp_rrrf_create = liquiddsp.resamp_rrrf_create
resamp_rrrf_create.restype = resamp_rrrf
resamp_rrrf_create.argtypes = [ctypes.c_float, ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.c_uint32]
resamp_rrrf_create_default = liquiddsp.resamp_rrrf_create_default
resamp_rrrf_create_default.restype = resamp_rrrf
resamp_rrrf_create_default.argtypes = [ctypes.c_float]
resamp_rrrf_destroy = liquiddsp.resamp_rrrf_destroy
resamp_rrrf_destroy.restype = None
resamp_rrrf_destroy.argtypes = [resamp_rrrf]
resamp_rrrf_print = liquiddsp.resamp_rrrf_print
resamp_rrrf_print.restype = None
resamp_rrrf_print.argtypes = [resamp_rrrf]
resamp_rrrf_reset = liquiddsp.resamp_rrrf_reset
resamp_rrrf_reset.restype = None
resamp_rrrf_reset.argtypes = [resamp_rrrf]
resamp_rrrf_get_delay = liquiddsp.resamp_rrrf_get_delay
resamp_rrrf_get_delay.restype = ctypes.c_uint32
resamp_rrrf_get_delay.argtypes = [resamp_rrrf]
resamp_rrrf_set_rate = liquiddsp.resamp_rrrf_set_rate
resamp_rrrf_set_rate.restype = None
resamp_rrrf_set_rate.argtypes = [resamp_rrrf, ctypes.c_float]
resamp_rrrf_get_rate = liquiddsp.resamp_rrrf_get_rate
resamp_rrrf_get_rate.restype = ctypes.c_float
resamp_rrrf_get_rate.argtypes = [resamp_rrrf]
resamp_rrrf_adjust_rate = liquiddsp.resamp_rrrf_adjust_rate
resamp_rrrf_adjust_rate.restype = None
resamp_rrrf_adjust_rate.argtypes = [resamp_rrrf, ctypes.c_float]
resamp_rrrf_set_timing_phase = liquiddsp.resamp_rrrf_set_timing_phase
resamp_rrrf_set_timing_phase.restype = None
resamp_rrrf_set_timing_phase.argtypes = [resamp_rrrf, ctypes.c_float]
resamp_rrrf_adjust_timing_phase = liquiddsp.resamp_rrrf_adjust_timing_phase
resamp_rrrf_adjust_timing_phase.restype = None
resamp_rrrf_adjust_timing_phase.argtypes = [resamp_rrrf, ctypes.c_float]
resamp_rrrf_execute = liquiddsp.resamp_rrrf_execute
resamp_rrrf_execute.restype = None
resamp_rrrf_execute.argtypes = [resamp_rrrf, ctypes.c_float, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_uint32)]
resamp_rrrf_execute_block = liquiddsp.resamp_rrrf_execute_block
resamp_rrrf_execute_block.restype = None
resamp_rrrf_execute_block.argtypes = [resamp_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_uint32)]
class struct_resamp_crcf_s(Structure):
    pass

resamp_crcf = ctypes.POINTER(struct_resamp_crcf_s)
resamp_crcf_create = liquiddsp.resamp_crcf_create
resamp_crcf_create.restype = resamp_crcf
resamp_crcf_create.argtypes = [ctypes.c_float, ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.c_uint32]
resamp_crcf_create_default = liquiddsp.resamp_crcf_create_default
resamp_crcf_create_default.restype = resamp_crcf
resamp_crcf_create_default.argtypes = [ctypes.c_float]
resamp_crcf_destroy = liquiddsp.resamp_crcf_destroy
resamp_crcf_destroy.restype = None
resamp_crcf_destroy.argtypes = [resamp_crcf]
resamp_crcf_print = liquiddsp.resamp_crcf_print
resamp_crcf_print.restype = None
resamp_crcf_print.argtypes = [resamp_crcf]
resamp_crcf_reset = liquiddsp.resamp_crcf_reset
resamp_crcf_reset.restype = None
resamp_crcf_reset.argtypes = [resamp_crcf]
resamp_crcf_get_delay = liquiddsp.resamp_crcf_get_delay
resamp_crcf_get_delay.restype = ctypes.c_uint32
resamp_crcf_get_delay.argtypes = [resamp_crcf]
resamp_crcf_set_rate = liquiddsp.resamp_crcf_set_rate
resamp_crcf_set_rate.restype = None
resamp_crcf_set_rate.argtypes = [resamp_crcf, ctypes.c_float]
resamp_crcf_get_rate = liquiddsp.resamp_crcf_get_rate
resamp_crcf_get_rate.restype = ctypes.c_float
resamp_crcf_get_rate.argtypes = [resamp_crcf]
resamp_crcf_adjust_rate = liquiddsp.resamp_crcf_adjust_rate
resamp_crcf_adjust_rate.restype = None
resamp_crcf_adjust_rate.argtypes = [resamp_crcf, ctypes.c_float]
resamp_crcf_set_timing_phase = liquiddsp.resamp_crcf_set_timing_phase
resamp_crcf_set_timing_phase.restype = None
resamp_crcf_set_timing_phase.argtypes = [resamp_crcf, ctypes.c_float]
resamp_crcf_adjust_timing_phase = liquiddsp.resamp_crcf_adjust_timing_phase
resamp_crcf_adjust_timing_phase.restype = None
resamp_crcf_adjust_timing_phase.argtypes = [resamp_crcf, ctypes.c_float]
resamp_crcf_execute = liquiddsp.resamp_crcf_execute
resamp_crcf_execute.restype = None
resamp_crcf_execute.argtypes = [resamp_crcf, liquid_float_complex, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(ctypes.c_uint32)]
resamp_crcf_execute_block = liquiddsp.resamp_crcf_execute_block
resamp_crcf_execute_block.restype = None
resamp_crcf_execute_block.argtypes = [resamp_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(ctypes.c_uint32)]
class struct_resamp_cccf_s(Structure):
    pass

resamp_cccf = ctypes.POINTER(struct_resamp_cccf_s)
resamp_cccf_create = liquiddsp.resamp_cccf_create
resamp_cccf_create.restype = resamp_cccf
resamp_cccf_create.argtypes = [ctypes.c_float, ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.c_uint32]
resamp_cccf_create_default = liquiddsp.resamp_cccf_create_default
resamp_cccf_create_default.restype = resamp_cccf
resamp_cccf_create_default.argtypes = [ctypes.c_float]
resamp_cccf_destroy = liquiddsp.resamp_cccf_destroy
resamp_cccf_destroy.restype = None
resamp_cccf_destroy.argtypes = [resamp_cccf]
resamp_cccf_print = liquiddsp.resamp_cccf_print
resamp_cccf_print.restype = None
resamp_cccf_print.argtypes = [resamp_cccf]
resamp_cccf_reset = liquiddsp.resamp_cccf_reset
resamp_cccf_reset.restype = None
resamp_cccf_reset.argtypes = [resamp_cccf]
resamp_cccf_get_delay = liquiddsp.resamp_cccf_get_delay
resamp_cccf_get_delay.restype = ctypes.c_uint32
resamp_cccf_get_delay.argtypes = [resamp_cccf]
resamp_cccf_set_rate = liquiddsp.resamp_cccf_set_rate
resamp_cccf_set_rate.restype = None
resamp_cccf_set_rate.argtypes = [resamp_cccf, ctypes.c_float]
resamp_cccf_get_rate = liquiddsp.resamp_cccf_get_rate
resamp_cccf_get_rate.restype = ctypes.c_float
resamp_cccf_get_rate.argtypes = [resamp_cccf]
resamp_cccf_adjust_rate = liquiddsp.resamp_cccf_adjust_rate
resamp_cccf_adjust_rate.restype = None
resamp_cccf_adjust_rate.argtypes = [resamp_cccf, ctypes.c_float]
resamp_cccf_set_timing_phase = liquiddsp.resamp_cccf_set_timing_phase
resamp_cccf_set_timing_phase.restype = None
resamp_cccf_set_timing_phase.argtypes = [resamp_cccf, ctypes.c_float]
resamp_cccf_adjust_timing_phase = liquiddsp.resamp_cccf_adjust_timing_phase
resamp_cccf_adjust_timing_phase.restype = None
resamp_cccf_adjust_timing_phase.argtypes = [resamp_cccf, ctypes.c_float]
resamp_cccf_execute = liquiddsp.resamp_cccf_execute
resamp_cccf_execute.restype = None
resamp_cccf_execute.argtypes = [resamp_cccf, liquid_float_complex, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(ctypes.c_uint32)]
resamp_cccf_execute_block = liquiddsp.resamp_cccf_execute_block
resamp_cccf_execute_block.restype = None
resamp_cccf_execute_block.argtypes = [resamp_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(ctypes.c_uint32)]

# values for enumeration 'c__EA_liquid_resamp_type'
c__EA_liquid_resamp_type__enumvalues = {
    0: 'LIQUID_RESAMP_INTERP',
    1: 'LIQUID_RESAMP_DECIM',
}
LIQUID_RESAMP_INTERP = 0
LIQUID_RESAMP_DECIM = 1
c__EA_liquid_resamp_type = ctypes.c_uint32 # enum
liquid_resamp_type = c__EA_liquid_resamp_type
liquid_resamp_type__enumvalues = c__EA_liquid_resamp_type__enumvalues
class struct_msresamp2_rrrf_s(Structure):
    pass

msresamp2_rrrf = ctypes.POINTER(struct_msresamp2_rrrf_s)
msresamp2_rrrf_create = liquiddsp.msresamp2_rrrf_create
msresamp2_rrrf_create.restype = msresamp2_rrrf
msresamp2_rrrf_create.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.c_float]
msresamp2_rrrf_destroy = liquiddsp.msresamp2_rrrf_destroy
msresamp2_rrrf_destroy.restype = None
msresamp2_rrrf_destroy.argtypes = [msresamp2_rrrf]
msresamp2_rrrf_print = liquiddsp.msresamp2_rrrf_print
msresamp2_rrrf_print.restype = None
msresamp2_rrrf_print.argtypes = [msresamp2_rrrf]
msresamp2_rrrf_reset = liquiddsp.msresamp2_rrrf_reset
msresamp2_rrrf_reset.restype = None
msresamp2_rrrf_reset.argtypes = [msresamp2_rrrf]
msresamp2_rrrf_get_rate = liquiddsp.msresamp2_rrrf_get_rate
msresamp2_rrrf_get_rate.restype = ctypes.c_float
msresamp2_rrrf_get_rate.argtypes = [msresamp2_rrrf]
msresamp2_rrrf_get_num_stages = liquiddsp.msresamp2_rrrf_get_num_stages
msresamp2_rrrf_get_num_stages.restype = ctypes.c_uint32
msresamp2_rrrf_get_num_stages.argtypes = [msresamp2_rrrf]
msresamp2_rrrf_get_type = liquiddsp.msresamp2_rrrf_get_type
msresamp2_rrrf_get_type.restype = ctypes.c_int32
msresamp2_rrrf_get_type.argtypes = [msresamp2_rrrf]
msresamp2_rrrf_get_delay = liquiddsp.msresamp2_rrrf_get_delay
msresamp2_rrrf_get_delay.restype = ctypes.c_float
msresamp2_rrrf_get_delay.argtypes = [msresamp2_rrrf]
msresamp2_rrrf_execute = liquiddsp.msresamp2_rrrf_execute
msresamp2_rrrf_execute.restype = None
msresamp2_rrrf_execute.argtypes = [msresamp2_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
class struct_msresamp2_crcf_s(Structure):
    pass

msresamp2_crcf = ctypes.POINTER(struct_msresamp2_crcf_s)
msresamp2_crcf_create = liquiddsp.msresamp2_crcf_create
msresamp2_crcf_create.restype = msresamp2_crcf
msresamp2_crcf_create.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.c_float]
msresamp2_crcf_destroy = liquiddsp.msresamp2_crcf_destroy
msresamp2_crcf_destroy.restype = None
msresamp2_crcf_destroy.argtypes = [msresamp2_crcf]
msresamp2_crcf_print = liquiddsp.msresamp2_crcf_print
msresamp2_crcf_print.restype = None
msresamp2_crcf_print.argtypes = [msresamp2_crcf]
msresamp2_crcf_reset = liquiddsp.msresamp2_crcf_reset
msresamp2_crcf_reset.restype = None
msresamp2_crcf_reset.argtypes = [msresamp2_crcf]
msresamp2_crcf_get_rate = liquiddsp.msresamp2_crcf_get_rate
msresamp2_crcf_get_rate.restype = ctypes.c_float
msresamp2_crcf_get_rate.argtypes = [msresamp2_crcf]
msresamp2_crcf_get_num_stages = liquiddsp.msresamp2_crcf_get_num_stages
msresamp2_crcf_get_num_stages.restype = ctypes.c_uint32
msresamp2_crcf_get_num_stages.argtypes = [msresamp2_crcf]
msresamp2_crcf_get_type = liquiddsp.msresamp2_crcf_get_type
msresamp2_crcf_get_type.restype = ctypes.c_int32
msresamp2_crcf_get_type.argtypes = [msresamp2_crcf]
msresamp2_crcf_get_delay = liquiddsp.msresamp2_crcf_get_delay
msresamp2_crcf_get_delay.restype = ctypes.c_float
msresamp2_crcf_get_delay.argtypes = [msresamp2_crcf]
msresamp2_crcf_execute = liquiddsp.msresamp2_crcf_execute
msresamp2_crcf_execute.restype = None
msresamp2_crcf_execute.argtypes = [msresamp2_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
class struct_msresamp2_cccf_s(Structure):
    pass

msresamp2_cccf = ctypes.POINTER(struct_msresamp2_cccf_s)
msresamp2_cccf_create = liquiddsp.msresamp2_cccf_create
msresamp2_cccf_create.restype = msresamp2_cccf
msresamp2_cccf_create.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.c_float]
msresamp2_cccf_destroy = liquiddsp.msresamp2_cccf_destroy
msresamp2_cccf_destroy.restype = None
msresamp2_cccf_destroy.argtypes = [msresamp2_cccf]
msresamp2_cccf_print = liquiddsp.msresamp2_cccf_print
msresamp2_cccf_print.restype = None
msresamp2_cccf_print.argtypes = [msresamp2_cccf]
msresamp2_cccf_reset = liquiddsp.msresamp2_cccf_reset
msresamp2_cccf_reset.restype = None
msresamp2_cccf_reset.argtypes = [msresamp2_cccf]
msresamp2_cccf_get_rate = liquiddsp.msresamp2_cccf_get_rate
msresamp2_cccf_get_rate.restype = ctypes.c_float
msresamp2_cccf_get_rate.argtypes = [msresamp2_cccf]
msresamp2_cccf_get_num_stages = liquiddsp.msresamp2_cccf_get_num_stages
msresamp2_cccf_get_num_stages.restype = ctypes.c_uint32
msresamp2_cccf_get_num_stages.argtypes = [msresamp2_cccf]
msresamp2_cccf_get_type = liquiddsp.msresamp2_cccf_get_type
msresamp2_cccf_get_type.restype = ctypes.c_int32
msresamp2_cccf_get_type.argtypes = [msresamp2_cccf]
msresamp2_cccf_get_delay = liquiddsp.msresamp2_cccf_get_delay
msresamp2_cccf_get_delay.restype = ctypes.c_float
msresamp2_cccf_get_delay.argtypes = [msresamp2_cccf]
msresamp2_cccf_execute = liquiddsp.msresamp2_cccf_execute
msresamp2_cccf_execute.restype = None
msresamp2_cccf_execute.argtypes = [msresamp2_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
class struct_msresamp_rrrf_s(Structure):
    pass

msresamp_rrrf = ctypes.POINTER(struct_msresamp_rrrf_s)
msresamp_rrrf_create = liquiddsp.msresamp_rrrf_create
msresamp_rrrf_create.restype = msresamp_rrrf
msresamp_rrrf_create.argtypes = [ctypes.c_float, ctypes.c_float]
msresamp_rrrf_destroy = liquiddsp.msresamp_rrrf_destroy
msresamp_rrrf_destroy.restype = None
msresamp_rrrf_destroy.argtypes = [msresamp_rrrf]
msresamp_rrrf_print = liquiddsp.msresamp_rrrf_print
msresamp_rrrf_print.restype = None
msresamp_rrrf_print.argtypes = [msresamp_rrrf]
msresamp_rrrf_reset = liquiddsp.msresamp_rrrf_reset
msresamp_rrrf_reset.restype = None
msresamp_rrrf_reset.argtypes = [msresamp_rrrf]
msresamp_rrrf_get_delay = liquiddsp.msresamp_rrrf_get_delay
msresamp_rrrf_get_delay.restype = ctypes.c_float
msresamp_rrrf_get_delay.argtypes = [msresamp_rrrf]
msresamp_rrrf_get_rate = liquiddsp.msresamp_rrrf_get_rate
msresamp_rrrf_get_rate.restype = ctypes.c_float
msresamp_rrrf_get_rate.argtypes = [msresamp_rrrf]
msresamp_rrrf_execute = liquiddsp.msresamp_rrrf_execute
msresamp_rrrf_execute.restype = None
msresamp_rrrf_execute.argtypes = [msresamp_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_uint32)]
class struct_msresamp_crcf_s(Structure):
    pass

msresamp_crcf = ctypes.POINTER(struct_msresamp_crcf_s)
msresamp_crcf_create = liquiddsp.msresamp_crcf_create
msresamp_crcf_create.restype = msresamp_crcf
msresamp_crcf_create.argtypes = [ctypes.c_float, ctypes.c_float]
msresamp_crcf_destroy = liquiddsp.msresamp_crcf_destroy
msresamp_crcf_destroy.restype = None
msresamp_crcf_destroy.argtypes = [msresamp_crcf]
msresamp_crcf_print = liquiddsp.msresamp_crcf_print
msresamp_crcf_print.restype = None
msresamp_crcf_print.argtypes = [msresamp_crcf]
msresamp_crcf_reset = liquiddsp.msresamp_crcf_reset
msresamp_crcf_reset.restype = None
msresamp_crcf_reset.argtypes = [msresamp_crcf]
msresamp_crcf_get_delay = liquiddsp.msresamp_crcf_get_delay
msresamp_crcf_get_delay.restype = ctypes.c_float
msresamp_crcf_get_delay.argtypes = [msresamp_crcf]
msresamp_crcf_get_rate = liquiddsp.msresamp_crcf_get_rate
msresamp_crcf_get_rate.restype = ctypes.c_float
msresamp_crcf_get_rate.argtypes = [msresamp_crcf]
msresamp_crcf_execute = liquiddsp.msresamp_crcf_execute
msresamp_crcf_execute.restype = None
msresamp_crcf_execute.argtypes = [msresamp_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(ctypes.c_uint32)]
class struct_msresamp_cccf_s(Structure):
    pass

msresamp_cccf = ctypes.POINTER(struct_msresamp_cccf_s)
msresamp_cccf_create = liquiddsp.msresamp_cccf_create
msresamp_cccf_create.restype = msresamp_cccf
msresamp_cccf_create.argtypes = [ctypes.c_float, ctypes.c_float]
msresamp_cccf_destroy = liquiddsp.msresamp_cccf_destroy
msresamp_cccf_destroy.restype = None
msresamp_cccf_destroy.argtypes = [msresamp_cccf]
msresamp_cccf_print = liquiddsp.msresamp_cccf_print
msresamp_cccf_print.restype = None
msresamp_cccf_print.argtypes = [msresamp_cccf]
msresamp_cccf_reset = liquiddsp.msresamp_cccf_reset
msresamp_cccf_reset.restype = None
msresamp_cccf_reset.argtypes = [msresamp_cccf]
msresamp_cccf_get_delay = liquiddsp.msresamp_cccf_get_delay
msresamp_cccf_get_delay.restype = ctypes.c_float
msresamp_cccf_get_delay.argtypes = [msresamp_cccf]
msresamp_cccf_get_rate = liquiddsp.msresamp_cccf_get_rate
msresamp_cccf_get_rate.restype = ctypes.c_float
msresamp_cccf_get_rate.argtypes = [msresamp_cccf]
msresamp_cccf_execute = liquiddsp.msresamp_cccf_execute
msresamp_cccf_execute.restype = None
msresamp_cccf_execute.argtypes = [msresamp_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(ctypes.c_uint32)]
class struct_dds_cccf_s(Structure):
    pass

dds_cccf = ctypes.POINTER(struct_dds_cccf_s)
dds_cccf_create = liquiddsp.dds_cccf_create
dds_cccf_create.restype = dds_cccf
dds_cccf_create.argtypes = [ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.c_float]
dds_cccf_destroy = liquiddsp.dds_cccf_destroy
dds_cccf_destroy.restype = None
dds_cccf_destroy.argtypes = [dds_cccf]
dds_cccf_print = liquiddsp.dds_cccf_print
dds_cccf_print.restype = None
dds_cccf_print.argtypes = [dds_cccf]
dds_cccf_reset = liquiddsp.dds_cccf_reset
dds_cccf_reset.restype = None
dds_cccf_reset.argtypes = [dds_cccf]
dds_cccf_decim_execute = liquiddsp.dds_cccf_decim_execute
dds_cccf_decim_execute.restype = None
dds_cccf_decim_execute.argtypes = [dds_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
dds_cccf_interp_execute = liquiddsp.dds_cccf_interp_execute
dds_cccf_interp_execute.restype = None
dds_cccf_interp_execute.argtypes = [dds_cccf, liquid_float_complex, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
class struct_symsync_rrrf_s(Structure):
    pass

symsync_rrrf = ctypes.POINTER(struct_symsync_rrrf_s)
symsync_rrrf_create = liquiddsp.symsync_rrrf_create
symsync_rrrf_create.restype = symsync_rrrf
symsync_rrrf_create.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
symsync_rrrf_create_rnyquist = liquiddsp.symsync_rrrf_create_rnyquist
symsync_rrrf_create_rnyquist.restype = symsync_rrrf
symsync_rrrf_create_rnyquist.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_uint32]
symsync_rrrf_create_kaiser = liquiddsp.symsync_rrrf_create_kaiser
symsync_rrrf_create_kaiser.restype = symsync_rrrf
symsync_rrrf_create_kaiser.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_uint32]
symsync_rrrf_destroy = liquiddsp.symsync_rrrf_destroy
symsync_rrrf_destroy.restype = None
symsync_rrrf_destroy.argtypes = [symsync_rrrf]
symsync_rrrf_print = liquiddsp.symsync_rrrf_print
symsync_rrrf_print.restype = None
symsync_rrrf_print.argtypes = [symsync_rrrf]
symsync_rrrf_reset = liquiddsp.symsync_rrrf_reset
symsync_rrrf_reset.restype = None
symsync_rrrf_reset.argtypes = [symsync_rrrf]
symsync_rrrf_lock = liquiddsp.symsync_rrrf_lock
symsync_rrrf_lock.restype = None
symsync_rrrf_lock.argtypes = [symsync_rrrf]
symsync_rrrf_unlock = liquiddsp.symsync_rrrf_unlock
symsync_rrrf_unlock.restype = None
symsync_rrrf_unlock.argtypes = [symsync_rrrf]
symsync_rrrf_set_output_rate = liquiddsp.symsync_rrrf_set_output_rate
symsync_rrrf_set_output_rate.restype = None
symsync_rrrf_set_output_rate.argtypes = [symsync_rrrf, ctypes.c_uint32]
symsync_rrrf_set_lf_bw = liquiddsp.symsync_rrrf_set_lf_bw
symsync_rrrf_set_lf_bw.restype = None
symsync_rrrf_set_lf_bw.argtypes = [symsync_rrrf, ctypes.c_float]
symsync_rrrf_get_tau = liquiddsp.symsync_rrrf_get_tau
symsync_rrrf_get_tau.restype = ctypes.c_float
symsync_rrrf_get_tau.argtypes = [symsync_rrrf]
symsync_rrrf_execute = liquiddsp.symsync_rrrf_execute
symsync_rrrf_execute.restype = None
symsync_rrrf_execute.argtypes = [symsync_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_uint32)]
class struct_symsync_crcf_s(Structure):
    pass

symsync_crcf = ctypes.POINTER(struct_symsync_crcf_s)
symsync_crcf_create = liquiddsp.symsync_crcf_create
symsync_crcf_create.restype = symsync_crcf
symsync_crcf_create.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
symsync_crcf_create_rnyquist = liquiddsp.symsync_crcf_create_rnyquist
symsync_crcf_create_rnyquist.restype = symsync_crcf
symsync_crcf_create_rnyquist.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_uint32]
symsync_crcf_create_kaiser = liquiddsp.symsync_crcf_create_kaiser
symsync_crcf_create_kaiser.restype = symsync_crcf
symsync_crcf_create_kaiser.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_uint32]
symsync_crcf_destroy = liquiddsp.symsync_crcf_destroy
symsync_crcf_destroy.restype = None
symsync_crcf_destroy.argtypes = [symsync_crcf]
symsync_crcf_print = liquiddsp.symsync_crcf_print
symsync_crcf_print.restype = None
symsync_crcf_print.argtypes = [symsync_crcf]
symsync_crcf_reset = liquiddsp.symsync_crcf_reset
symsync_crcf_reset.restype = None
symsync_crcf_reset.argtypes = [symsync_crcf]
symsync_crcf_lock = liquiddsp.symsync_crcf_lock
symsync_crcf_lock.restype = None
symsync_crcf_lock.argtypes = [symsync_crcf]
symsync_crcf_unlock = liquiddsp.symsync_crcf_unlock
symsync_crcf_unlock.restype = None
symsync_crcf_unlock.argtypes = [symsync_crcf]
symsync_crcf_set_output_rate = liquiddsp.symsync_crcf_set_output_rate
symsync_crcf_set_output_rate.restype = None
symsync_crcf_set_output_rate.argtypes = [symsync_crcf, ctypes.c_uint32]
symsync_crcf_set_lf_bw = liquiddsp.symsync_crcf_set_lf_bw
symsync_crcf_set_lf_bw.restype = None
symsync_crcf_set_lf_bw.argtypes = [symsync_crcf, ctypes.c_float]
symsync_crcf_get_tau = liquiddsp.symsync_crcf_get_tau
symsync_crcf_get_tau.restype = ctypes.c_float
symsync_crcf_get_tau.argtypes = [symsync_crcf]
symsync_crcf_execute = liquiddsp.symsync_crcf_execute
symsync_crcf_execute.restype = None
symsync_crcf_execute.argtypes = [symsync_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(ctypes.c_uint32)]
class struct_firfarrow_rrrf_s(Structure):
    pass

firfarrow_rrrf = ctypes.POINTER(struct_firfarrow_rrrf_s)
firfarrow_rrrf_create = liquiddsp.firfarrow_rrrf_create
firfarrow_rrrf_create.restype = firfarrow_rrrf
firfarrow_rrrf_create.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
firfarrow_rrrf_destroy = liquiddsp.firfarrow_rrrf_destroy
firfarrow_rrrf_destroy.restype = None
firfarrow_rrrf_destroy.argtypes = [firfarrow_rrrf]
firfarrow_rrrf_print = liquiddsp.firfarrow_rrrf_print
firfarrow_rrrf_print.restype = None
firfarrow_rrrf_print.argtypes = [firfarrow_rrrf]
firfarrow_rrrf_reset = liquiddsp.firfarrow_rrrf_reset
firfarrow_rrrf_reset.restype = None
firfarrow_rrrf_reset.argtypes = [firfarrow_rrrf]
firfarrow_rrrf_push = liquiddsp.firfarrow_rrrf_push
firfarrow_rrrf_push.restype = None
firfarrow_rrrf_push.argtypes = [firfarrow_rrrf, ctypes.c_float]
firfarrow_rrrf_set_delay = liquiddsp.firfarrow_rrrf_set_delay
firfarrow_rrrf_set_delay.restype = None
firfarrow_rrrf_set_delay.argtypes = [firfarrow_rrrf, ctypes.c_float]
firfarrow_rrrf_execute = liquiddsp.firfarrow_rrrf_execute
firfarrow_rrrf_execute.restype = None
firfarrow_rrrf_execute.argtypes = [firfarrow_rrrf, ctypes.POINTER(ctypes.c_float)]
firfarrow_rrrf_execute_block = liquiddsp.firfarrow_rrrf_execute_block
firfarrow_rrrf_execute_block.restype = None
firfarrow_rrrf_execute_block.argtypes = [firfarrow_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
firfarrow_rrrf_get_length = liquiddsp.firfarrow_rrrf_get_length
firfarrow_rrrf_get_length.restype = ctypes.c_uint32
firfarrow_rrrf_get_length.argtypes = [firfarrow_rrrf]
firfarrow_rrrf_get_coefficients = liquiddsp.firfarrow_rrrf_get_coefficients
firfarrow_rrrf_get_coefficients.restype = None
firfarrow_rrrf_get_coefficients.argtypes = [firfarrow_rrrf, ctypes.POINTER(ctypes.c_float)]
firfarrow_rrrf_freqresponse = liquiddsp.firfarrow_rrrf_freqresponse
firfarrow_rrrf_freqresponse.restype = None
firfarrow_rrrf_freqresponse.argtypes = [firfarrow_rrrf, ctypes.c_float, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
firfarrow_rrrf_groupdelay = liquiddsp.firfarrow_rrrf_groupdelay
firfarrow_rrrf_groupdelay.restype = ctypes.c_float
firfarrow_rrrf_groupdelay.argtypes = [firfarrow_rrrf, ctypes.c_float]
class struct_firfarrow_crcf_s(Structure):
    pass

firfarrow_crcf = ctypes.POINTER(struct_firfarrow_crcf_s)
firfarrow_crcf_create = liquiddsp.firfarrow_crcf_create
firfarrow_crcf_create.restype = firfarrow_crcf
firfarrow_crcf_create.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
firfarrow_crcf_destroy = liquiddsp.firfarrow_crcf_destroy
firfarrow_crcf_destroy.restype = None
firfarrow_crcf_destroy.argtypes = [firfarrow_crcf]
firfarrow_crcf_print = liquiddsp.firfarrow_crcf_print
firfarrow_crcf_print.restype = None
firfarrow_crcf_print.argtypes = [firfarrow_crcf]
firfarrow_crcf_reset = liquiddsp.firfarrow_crcf_reset
firfarrow_crcf_reset.restype = None
firfarrow_crcf_reset.argtypes = [firfarrow_crcf]
firfarrow_crcf_push = liquiddsp.firfarrow_crcf_push
firfarrow_crcf_push.restype = None
firfarrow_crcf_push.argtypes = [firfarrow_crcf, liquid_float_complex]
firfarrow_crcf_set_delay = liquiddsp.firfarrow_crcf_set_delay
firfarrow_crcf_set_delay.restype = None
firfarrow_crcf_set_delay.argtypes = [firfarrow_crcf, ctypes.c_float]
firfarrow_crcf_execute = liquiddsp.firfarrow_crcf_execute
firfarrow_crcf_execute.restype = None
firfarrow_crcf_execute.argtypes = [firfarrow_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
firfarrow_crcf_execute_block = liquiddsp.firfarrow_crcf_execute_block
firfarrow_crcf_execute_block.restype = None
firfarrow_crcf_execute_block.argtypes = [firfarrow_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
firfarrow_crcf_get_length = liquiddsp.firfarrow_crcf_get_length
firfarrow_crcf_get_length.restype = ctypes.c_uint32
firfarrow_crcf_get_length.argtypes = [firfarrow_crcf]
firfarrow_crcf_get_coefficients = liquiddsp.firfarrow_crcf_get_coefficients
firfarrow_crcf_get_coefficients.restype = None
firfarrow_crcf_get_coefficients.argtypes = [firfarrow_crcf, ctypes.POINTER(ctypes.c_float)]
firfarrow_crcf_freqresponse = liquiddsp.firfarrow_crcf_freqresponse
firfarrow_crcf_freqresponse.restype = None
firfarrow_crcf_freqresponse.argtypes = [firfarrow_crcf, ctypes.c_float, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
firfarrow_crcf_groupdelay = liquiddsp.firfarrow_crcf_groupdelay
firfarrow_crcf_groupdelay.restype = ctypes.c_float
firfarrow_crcf_groupdelay.argtypes = [firfarrow_crcf, ctypes.c_float]
class struct_ordfilt_rrrf_s(Structure):
    pass

ordfilt_rrrf = ctypes.POINTER(struct_ordfilt_rrrf_s)
ordfilt_rrrf_create = liquiddsp.ordfilt_rrrf_create
ordfilt_rrrf_create.restype = ordfilt_rrrf
ordfilt_rrrf_create.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
ordfilt_rrrf_create_medfilt = liquiddsp.ordfilt_rrrf_create_medfilt
ordfilt_rrrf_create_medfilt.restype = ordfilt_rrrf
ordfilt_rrrf_create_medfilt.argtypes = [ctypes.c_uint32]
ordfilt_rrrf_destroy = liquiddsp.ordfilt_rrrf_destroy
ordfilt_rrrf_destroy.restype = None
ordfilt_rrrf_destroy.argtypes = [ordfilt_rrrf]
ordfilt_rrrf_reset = liquiddsp.ordfilt_rrrf_reset
ordfilt_rrrf_reset.restype = None
ordfilt_rrrf_reset.argtypes = [ordfilt_rrrf]
ordfilt_rrrf_print = liquiddsp.ordfilt_rrrf_print
ordfilt_rrrf_print.restype = None
ordfilt_rrrf_print.argtypes = [ordfilt_rrrf]
ordfilt_rrrf_push = liquiddsp.ordfilt_rrrf_push
ordfilt_rrrf_push.restype = None
ordfilt_rrrf_push.argtypes = [ordfilt_rrrf, ctypes.c_float]
ordfilt_rrrf_write = liquiddsp.ordfilt_rrrf_write
ordfilt_rrrf_write.restype = None
ordfilt_rrrf_write.argtypes = [ordfilt_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
ordfilt_rrrf_execute = liquiddsp.ordfilt_rrrf_execute
ordfilt_rrrf_execute.restype = None
ordfilt_rrrf_execute.argtypes = [ordfilt_rrrf, ctypes.POINTER(ctypes.c_float)]
ordfilt_rrrf_execute_block = liquiddsp.ordfilt_rrrf_execute_block
ordfilt_rrrf_execute_block.restype = None
ordfilt_rrrf_execute_block.argtypes = [ordfilt_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
class struct_c__SA_framesyncstats_s(Structure):
    pass

struct_c__SA_framesyncstats_s._pack_ = 1 # source:False
struct_c__SA_framesyncstats_s._fields_ = [
    ('evm', ctypes.c_float),
    ('rssi', ctypes.c_float),
    ('cfo', ctypes.c_float),
    ('PADDING_0', ctypes.c_ubyte * 4),
    ('framesyms', ctypes.POINTER(struct_c__SA_liquid_float_complex)),
    ('num_framesyms', ctypes.c_uint32),
    ('mod_scheme', ctypes.c_uint32),
    ('mod_bps', ctypes.c_uint32),
    ('check', ctypes.c_uint32),
    ('fec0', ctypes.c_uint32),
    ('fec1', ctypes.c_uint32),
]

framesyncstats_s = struct_c__SA_framesyncstats_s
framesyncstats_default = struct_c__SA_framesyncstats_s # Variable struct_c__SA_framesyncstats_s
framesyncstats_init_default = liquiddsp.framesyncstats_init_default
framesyncstats_init_default.restype = ctypes.c_int32
framesyncstats_init_default.argtypes = [ctypes.POINTER(struct_c__SA_framesyncstats_s)]
framesyncstats_print = liquiddsp.framesyncstats_print
framesyncstats_print.restype = ctypes.c_int32
framesyncstats_print.argtypes = [ctypes.POINTER(struct_c__SA_framesyncstats_s)]
class struct_c__SA_framedatastats_s(Structure):
    pass

struct_c__SA_framedatastats_s._pack_ = 1 # source:False
struct_c__SA_framedatastats_s._fields_ = [
    ('num_frames_detected', ctypes.c_uint32),
    ('num_headers_valid', ctypes.c_uint32),
    ('num_payloads_valid', ctypes.c_uint32),
    ('PADDING_0', ctypes.c_ubyte * 4),
    ('num_bytes_received', ctypes.c_uint64),
]

framedatastats_s = struct_c__SA_framedatastats_s
framedatastats_reset = liquiddsp.framedatastats_reset
framedatastats_reset.restype = ctypes.c_int32
framedatastats_reset.argtypes = [ctypes.POINTER(struct_c__SA_framedatastats_s)]
framedatastats_print = liquiddsp.framedatastats_print
framedatastats_print.restype = ctypes.c_int32
framedatastats_print.argtypes = [ctypes.POINTER(struct_c__SA_framedatastats_s)]
framesync_callback = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int32, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, ctypes.c_int32, struct_c__SA_framesyncstats_s, ctypes.POINTER(None))
framesync_csma_callback = ctypes.CFUNCTYPE(None, ctypes.POINTER(None))
class struct_qpacketmodem_s(Structure):
    pass

qpacketmodem = ctypes.POINTER(struct_qpacketmodem_s)
qpacketmodem_create = liquiddsp.qpacketmodem_create
qpacketmodem_create.restype = qpacketmodem
qpacketmodem_create.argtypes = []
qpacketmodem_destroy = liquiddsp.qpacketmodem_destroy
qpacketmodem_destroy.restype = ctypes.c_int32
qpacketmodem_destroy.argtypes = [qpacketmodem]
qpacketmodem_reset = liquiddsp.qpacketmodem_reset
qpacketmodem_reset.restype = ctypes.c_int32
qpacketmodem_reset.argtypes = [qpacketmodem]
qpacketmodem_print = liquiddsp.qpacketmodem_print
qpacketmodem_print.restype = ctypes.c_int32
qpacketmodem_print.argtypes = [qpacketmodem]
qpacketmodem_configure = liquiddsp.qpacketmodem_configure
qpacketmodem_configure.restype = ctypes.c_int32
qpacketmodem_configure.argtypes = [qpacketmodem, ctypes.c_uint32, crc_scheme, fec_scheme, fec_scheme, ctypes.c_int32]
qpacketmodem_get_frame_len = liquiddsp.qpacketmodem_get_frame_len
qpacketmodem_get_frame_len.restype = ctypes.c_uint32
qpacketmodem_get_frame_len.argtypes = [qpacketmodem]
qpacketmodem_get_payload_len = liquiddsp.qpacketmodem_get_payload_len
qpacketmodem_get_payload_len.restype = ctypes.c_uint32
qpacketmodem_get_payload_len.argtypes = [qpacketmodem]
qpacketmodem_get_crc = liquiddsp.qpacketmodem_get_crc
qpacketmodem_get_crc.restype = ctypes.c_uint32
qpacketmodem_get_crc.argtypes = [qpacketmodem]
qpacketmodem_get_fec0 = liquiddsp.qpacketmodem_get_fec0
qpacketmodem_get_fec0.restype = ctypes.c_uint32
qpacketmodem_get_fec0.argtypes = [qpacketmodem]
qpacketmodem_get_fec1 = liquiddsp.qpacketmodem_get_fec1
qpacketmodem_get_fec1.restype = ctypes.c_uint32
qpacketmodem_get_fec1.argtypes = [qpacketmodem]
qpacketmodem_get_modscheme = liquiddsp.qpacketmodem_get_modscheme
qpacketmodem_get_modscheme.restype = ctypes.c_uint32
qpacketmodem_get_modscheme.argtypes = [qpacketmodem]
qpacketmodem_get_demodulator_phase_error = liquiddsp.qpacketmodem_get_demodulator_phase_error
qpacketmodem_get_demodulator_phase_error.restype = ctypes.c_float
qpacketmodem_get_demodulator_phase_error.argtypes = [qpacketmodem]
qpacketmodem_get_demodulator_evm = liquiddsp.qpacketmodem_get_demodulator_evm
qpacketmodem_get_demodulator_evm.restype = ctypes.c_float
qpacketmodem_get_demodulator_evm.argtypes = [qpacketmodem]
qpacketmodem_encode_syms = liquiddsp.qpacketmodem_encode_syms
qpacketmodem_encode_syms.restype = ctypes.c_int32
qpacketmodem_encode_syms.argtypes = [qpacketmodem, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte)]
qpacketmodem_decode_syms = liquiddsp.qpacketmodem_decode_syms
qpacketmodem_decode_syms.restype = ctypes.c_int32
qpacketmodem_decode_syms.argtypes = [qpacketmodem, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte)]
qpacketmodem_decode_bits = liquiddsp.qpacketmodem_decode_bits
qpacketmodem_decode_bits.restype = ctypes.c_int32
qpacketmodem_decode_bits.argtypes = [qpacketmodem, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte)]
qpacketmodem_encode = liquiddsp.qpacketmodem_encode
qpacketmodem_encode.restype = ctypes.c_int32
qpacketmodem_encode.argtypes = [qpacketmodem, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
qpacketmodem_decode = liquiddsp.qpacketmodem_decode
qpacketmodem_decode.restype = ctypes.c_int32
qpacketmodem_decode.argtypes = [qpacketmodem, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(ctypes.c_ubyte)]
qpacketmodem_decode_soft = liquiddsp.qpacketmodem_decode_soft
qpacketmodem_decode_soft.restype = ctypes.c_int32
qpacketmodem_decode_soft.argtypes = [qpacketmodem, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(ctypes.c_ubyte)]
qpacketmodem_decode_soft_sym = liquiddsp.qpacketmodem_decode_soft_sym
qpacketmodem_decode_soft_sym.restype = ctypes.c_int32
qpacketmodem_decode_soft_sym.argtypes = [qpacketmodem, liquid_float_complex]
qpacketmodem_decode_soft_payload = liquiddsp.qpacketmodem_decode_soft_payload
qpacketmodem_decode_soft_payload.restype = ctypes.c_int32
qpacketmodem_decode_soft_payload.argtypes = [qpacketmodem, ctypes.POINTER(ctypes.c_ubyte)]
qpilot_num_pilots = liquiddsp.qpilot_num_pilots
qpilot_num_pilots.restype = ctypes.c_uint32
qpilot_num_pilots.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
qpilot_frame_len = liquiddsp.qpilot_frame_len
qpilot_frame_len.restype = ctypes.c_uint32
qpilot_frame_len.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
class struct_qpilotgen_s(Structure):
    pass

qpilotgen = ctypes.POINTER(struct_qpilotgen_s)
qpilotgen_create = liquiddsp.qpilotgen_create
qpilotgen_create.restype = qpilotgen
qpilotgen_create.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
qpilotgen_recreate = liquiddsp.qpilotgen_recreate
qpilotgen_recreate.restype = qpilotgen
qpilotgen_recreate.argtypes = [qpilotgen, ctypes.c_uint32, ctypes.c_uint32]
qpilotgen_destroy = liquiddsp.qpilotgen_destroy
qpilotgen_destroy.restype = ctypes.c_int32
qpilotgen_destroy.argtypes = [qpilotgen]
qpilotgen_reset = liquiddsp.qpilotgen_reset
qpilotgen_reset.restype = ctypes.c_int32
qpilotgen_reset.argtypes = [qpilotgen]
qpilotgen_print = liquiddsp.qpilotgen_print
qpilotgen_print.restype = ctypes.c_int32
qpilotgen_print.argtypes = [qpilotgen]
qpilotgen_get_frame_len = liquiddsp.qpilotgen_get_frame_len
qpilotgen_get_frame_len.restype = ctypes.c_uint32
qpilotgen_get_frame_len.argtypes = [qpilotgen]
qpilotgen_execute = liquiddsp.qpilotgen_execute
qpilotgen_execute.restype = ctypes.c_int32
qpilotgen_execute.argtypes = [qpilotgen, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
class struct_qpilotsync_s(Structure):
    pass

qpilotsync = ctypes.POINTER(struct_qpilotsync_s)
qpilotsync_create = liquiddsp.qpilotsync_create
qpilotsync_create.restype = qpilotsync
qpilotsync_create.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
qpilotsync_recreate = liquiddsp.qpilotsync_recreate
qpilotsync_recreate.restype = qpilotsync
qpilotsync_recreate.argtypes = [qpilotsync, ctypes.c_uint32, ctypes.c_uint32]
qpilotsync_destroy = liquiddsp.qpilotsync_destroy
qpilotsync_destroy.restype = ctypes.c_int32
qpilotsync_destroy.argtypes = [qpilotsync]
qpilotsync_reset = liquiddsp.qpilotsync_reset
qpilotsync_reset.restype = ctypes.c_int32
qpilotsync_reset.argtypes = [qpilotsync]
qpilotsync_print = liquiddsp.qpilotsync_print
qpilotsync_print.restype = ctypes.c_int32
qpilotsync_print.argtypes = [qpilotsync]
qpilotsync_get_frame_len = liquiddsp.qpilotsync_get_frame_len
qpilotsync_get_frame_len.restype = ctypes.c_uint32
qpilotsync_get_frame_len.argtypes = [qpilotsync]
qpilotsync_execute = liquiddsp.qpilotsync_execute
qpilotsync_execute.restype = ctypes.c_int32
qpilotsync_execute.argtypes = [qpilotsync, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
qpilotsync_get_dphi = liquiddsp.qpilotsync_get_dphi
qpilotsync_get_dphi.restype = ctypes.c_float
qpilotsync_get_dphi.argtypes = [qpilotsync]
qpilotsync_get_phi = liquiddsp.qpilotsync_get_phi
qpilotsync_get_phi.restype = ctypes.c_float
qpilotsync_get_phi.argtypes = [qpilotsync]
qpilotsync_get_gain = liquiddsp.qpilotsync_get_gain
qpilotsync_get_gain.restype = ctypes.c_float
qpilotsync_get_gain.argtypes = [qpilotsync]
qpilotsync_get_evm = liquiddsp.qpilotsync_get_evm
qpilotsync_get_evm.restype = ctypes.c_float
qpilotsync_get_evm.argtypes = [qpilotsync]
class struct_framegen64_s(Structure):
    pass

framegen64 = ctypes.POINTER(struct_framegen64_s)
framegen64_create = liquiddsp.framegen64_create
framegen64_create.restype = framegen64
framegen64_create.argtypes = []
framegen64_destroy = liquiddsp.framegen64_destroy
framegen64_destroy.restype = ctypes.c_int32
framegen64_destroy.argtypes = [framegen64]
framegen64_print = liquiddsp.framegen64_print
framegen64_print.restype = ctypes.c_int32
framegen64_print.argtypes = [framegen64]
framegen64_execute = liquiddsp.framegen64_execute
framegen64_execute.restype = ctypes.c_int32
framegen64_execute.argtypes = [framegen64, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
class struct_framesync64_s(Structure):
    pass

framesync64 = ctypes.POINTER(struct_framesync64_s)
framesync64_create = liquiddsp.framesync64_create
framesync64_create.restype = framesync64
framesync64_create.argtypes = [framesync_callback, ctypes.POINTER(None)]
framesync64_destroy = liquiddsp.framesync64_destroy
framesync64_destroy.restype = ctypes.c_int32
framesync64_destroy.argtypes = [framesync64]
framesync64_print = liquiddsp.framesync64_print
framesync64_print.restype = ctypes.c_int32
framesync64_print.argtypes = [framesync64]
framesync64_reset = liquiddsp.framesync64_reset
framesync64_reset.restype = ctypes.c_int32
framesync64_reset.argtypes = [framesync64]
framesync64_execute = liquiddsp.framesync64_execute
framesync64_execute.restype = ctypes.c_int32
framesync64_execute.argtypes = [framesync64, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
framesync64_debug_enable = liquiddsp.framesync64_debug_enable
framesync64_debug_enable.restype = ctypes.c_int32
framesync64_debug_enable.argtypes = [framesync64]
framesync64_debug_disable = liquiddsp.framesync64_debug_disable
framesync64_debug_disable.restype = ctypes.c_int32
framesync64_debug_disable.argtypes = [framesync64]
framesync64_debug_print = liquiddsp.framesync64_debug_print
framesync64_debug_print.restype = ctypes.c_int32
framesync64_debug_print.argtypes = [framesync64, ctypes.POINTER(ctypes.c_char)]
framesync64_reset_framedatastats = liquiddsp.framesync64_reset_framedatastats
framesync64_reset_framedatastats.restype = ctypes.c_int32
framesync64_reset_framedatastats.argtypes = [framesync64]
framesync64_get_framedatastats = liquiddsp.framesync64_get_framedatastats
framesync64_get_framedatastats.restype = framedatastats_s
framesync64_get_framedatastats.argtypes = [framesync64]
class struct_c__SA_flexframegenprops_s(Structure):
    pass

struct_c__SA_flexframegenprops_s._pack_ = 1 # source:False
struct_c__SA_flexframegenprops_s._fields_ = [
    ('check', ctypes.c_uint32),
    ('fec0', ctypes.c_uint32),
    ('fec1', ctypes.c_uint32),
    ('mod_scheme', ctypes.c_uint32),
]

flexframegenprops_s = struct_c__SA_flexframegenprops_s
flexframegenprops_init_default = liquiddsp.flexframegenprops_init_default
flexframegenprops_init_default.restype = ctypes.c_int32
flexframegenprops_init_default.argtypes = [ctypes.POINTER(struct_c__SA_flexframegenprops_s)]
class struct_flexframegen_s(Structure):
    pass

flexframegen = ctypes.POINTER(struct_flexframegen_s)
flexframegen_create = liquiddsp.flexframegen_create
flexframegen_create.restype = flexframegen
flexframegen_create.argtypes = [ctypes.POINTER(struct_c__SA_flexframegenprops_s)]
flexframegen_destroy = liquiddsp.flexframegen_destroy
flexframegen_destroy.restype = ctypes.c_int32
flexframegen_destroy.argtypes = [flexframegen]
flexframegen_print = liquiddsp.flexframegen_print
flexframegen_print.restype = ctypes.c_int32
flexframegen_print.argtypes = [flexframegen]
flexframegen_reset = liquiddsp.flexframegen_reset
flexframegen_reset.restype = ctypes.c_int32
flexframegen_reset.argtypes = [flexframegen]
flexframegen_is_assembled = liquiddsp.flexframegen_is_assembled
flexframegen_is_assembled.restype = ctypes.c_int32
flexframegen_is_assembled.argtypes = [flexframegen]
flexframegen_getprops = liquiddsp.flexframegen_getprops
flexframegen_getprops.restype = ctypes.c_int32
flexframegen_getprops.argtypes = [flexframegen, ctypes.POINTER(struct_c__SA_flexframegenprops_s)]
flexframegen_setprops = liquiddsp.flexframegen_setprops
flexframegen_setprops.restype = ctypes.c_int32
flexframegen_setprops.argtypes = [flexframegen, ctypes.POINTER(struct_c__SA_flexframegenprops_s)]
flexframegen_set_header_len = liquiddsp.flexframegen_set_header_len
flexframegen_set_header_len.restype = ctypes.c_int32
flexframegen_set_header_len.argtypes = [flexframegen, ctypes.c_uint32]
flexframegen_set_header_props = liquiddsp.flexframegen_set_header_props
flexframegen_set_header_props.restype = ctypes.c_int32
flexframegen_set_header_props.argtypes = [flexframegen, ctypes.POINTER(struct_c__SA_flexframegenprops_s)]
flexframegen_getframelen = liquiddsp.flexframegen_getframelen
flexframegen_getframelen.restype = ctypes.c_uint32
flexframegen_getframelen.argtypes = [flexframegen]
flexframegen_assemble = liquiddsp.flexframegen_assemble
flexframegen_assemble.restype = ctypes.c_int32
flexframegen_assemble.argtypes = [flexframegen, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32]
flexframegen_write_samples = liquiddsp.flexframegen_write_samples
flexframegen_write_samples.restype = ctypes.c_int32
flexframegen_write_samples.argtypes = [flexframegen, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
class struct_flexframesync_s(Structure):
    pass

flexframesync = ctypes.POINTER(struct_flexframesync_s)
flexframesync_create = liquiddsp.flexframesync_create
flexframesync_create.restype = flexframesync
flexframesync_create.argtypes = [framesync_callback, ctypes.POINTER(None)]
flexframesync_destroy = liquiddsp.flexframesync_destroy
flexframesync_destroy.restype = ctypes.c_int32
flexframesync_destroy.argtypes = [flexframesync]
flexframesync_print = liquiddsp.flexframesync_print
flexframesync_print.restype = ctypes.c_int32
flexframesync_print.argtypes = [flexframesync]
flexframesync_reset = liquiddsp.flexframesync_reset
flexframesync_reset.restype = ctypes.c_int32
flexframesync_reset.argtypes = [flexframesync]
flexframesync_is_frame_open = liquiddsp.flexframesync_is_frame_open
flexframesync_is_frame_open.restype = ctypes.c_int32
flexframesync_is_frame_open.argtypes = [flexframesync]
flexframesync_set_header_len = liquiddsp.flexframesync_set_header_len
flexframesync_set_header_len.restype = ctypes.c_int32
flexframesync_set_header_len.argtypes = [flexframesync, ctypes.c_uint32]
flexframesync_decode_header_soft = liquiddsp.flexframesync_decode_header_soft
flexframesync_decode_header_soft.restype = ctypes.c_int32
flexframesync_decode_header_soft.argtypes = [flexframesync, ctypes.c_int32]
flexframesync_decode_payload_soft = liquiddsp.flexframesync_decode_payload_soft
flexframesync_decode_payload_soft.restype = ctypes.c_int32
flexframesync_decode_payload_soft.argtypes = [flexframesync, ctypes.c_int32]
flexframesync_set_header_props = liquiddsp.flexframesync_set_header_props
flexframesync_set_header_props.restype = ctypes.c_int32
flexframesync_set_header_props.argtypes = [flexframesync, ctypes.POINTER(struct_c__SA_flexframegenprops_s)]
flexframesync_execute = liquiddsp.flexframesync_execute
flexframesync_execute.restype = ctypes.c_int32
flexframesync_execute.argtypes = [flexframesync, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
flexframesync_reset_framedatastats = liquiddsp.flexframesync_reset_framedatastats
flexframesync_reset_framedatastats.restype = ctypes.c_int32
flexframesync_reset_framedatastats.argtypes = [flexframesync]
flexframesync_get_framedatastats = liquiddsp.flexframesync_get_framedatastats
flexframesync_get_framedatastats.restype = framedatastats_s
flexframesync_get_framedatastats.argtypes = [flexframesync]
flexframesync_debug_enable = liquiddsp.flexframesync_debug_enable
flexframesync_debug_enable.restype = ctypes.c_int32
flexframesync_debug_enable.argtypes = [flexframesync]
flexframesync_debug_disable = liquiddsp.flexframesync_debug_disable
flexframesync_debug_disable.restype = ctypes.c_int32
flexframesync_debug_disable.argtypes = [flexframesync]
flexframesync_debug_print = liquiddsp.flexframesync_debug_print
flexframesync_debug_print.restype = ctypes.c_int32
flexframesync_debug_print.argtypes = [flexframesync, ctypes.POINTER(ctypes.c_char)]
class struct_bpacketgen_s(Structure):
    pass

bpacketgen = ctypes.POINTER(struct_bpacketgen_s)
bpacketgen_create = liquiddsp.bpacketgen_create
bpacketgen_create.restype = bpacketgen
bpacketgen_create.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_int32, ctypes.c_int32, ctypes.c_int32]
bpacketgen_recreate = liquiddsp.bpacketgen_recreate
bpacketgen_recreate.restype = bpacketgen
bpacketgen_recreate.argtypes = [bpacketgen, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_int32, ctypes.c_int32, ctypes.c_int32]
bpacketgen_destroy = liquiddsp.bpacketgen_destroy
bpacketgen_destroy.restype = None
bpacketgen_destroy.argtypes = [bpacketgen]
bpacketgen_print = liquiddsp.bpacketgen_print
bpacketgen_print.restype = None
bpacketgen_print.argtypes = [bpacketgen]
bpacketgen_get_packet_len = liquiddsp.bpacketgen_get_packet_len
bpacketgen_get_packet_len.restype = ctypes.c_uint32
bpacketgen_get_packet_len.argtypes = [bpacketgen]
bpacketgen_encode = liquiddsp.bpacketgen_encode
bpacketgen_encode.restype = None
bpacketgen_encode.argtypes = [bpacketgen, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte)]
class struct_bpacketsync_s(Structure):
    pass

bpacketsync = ctypes.POINTER(struct_bpacketsync_s)
bpacketsync_callback = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int32, ctypes.c_uint32, struct_c__SA_framesyncstats_s, ctypes.POINTER(None))
bpacketsync_create = liquiddsp.bpacketsync_create
bpacketsync_create.restype = bpacketsync
bpacketsync_create.argtypes = [ctypes.c_uint32, bpacketsync_callback, ctypes.POINTER(None)]
bpacketsync_destroy = liquiddsp.bpacketsync_destroy
bpacketsync_destroy.restype = ctypes.c_int32
bpacketsync_destroy.argtypes = [bpacketsync]
bpacketsync_print = liquiddsp.bpacketsync_print
bpacketsync_print.restype = ctypes.c_int32
bpacketsync_print.argtypes = [bpacketsync]
bpacketsync_reset = liquiddsp.bpacketsync_reset
bpacketsync_reset.restype = ctypes.c_int32
bpacketsync_reset.argtypes = [bpacketsync]
bpacketsync_execute = liquiddsp.bpacketsync_execute
bpacketsync_execute.restype = ctypes.c_int32
bpacketsync_execute.argtypes = [bpacketsync, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32]
bpacketsync_execute_byte = liquiddsp.bpacketsync_execute_byte
bpacketsync_execute_byte.restype = ctypes.c_int32
bpacketsync_execute_byte.argtypes = [bpacketsync, ctypes.c_ubyte]
bpacketsync_execute_sym = liquiddsp.bpacketsync_execute_sym
bpacketsync_execute_sym.restype = ctypes.c_int32
bpacketsync_execute_sym.argtypes = [bpacketsync, ctypes.c_ubyte, ctypes.c_uint32]
bpacketsync_execute_bit = liquiddsp.bpacketsync_execute_bit
bpacketsync_execute_bit.restype = ctypes.c_int32
bpacketsync_execute_bit.argtypes = [bpacketsync, ctypes.c_ubyte]
class struct_fskframegen_s(Structure):
    pass

fskframegen = ctypes.POINTER(struct_fskframegen_s)
fskframegen_create = liquiddsp.fskframegen_create
fskframegen_create.restype = fskframegen
fskframegen_create.argtypes = []
fskframegen_destroy = liquiddsp.fskframegen_destroy
fskframegen_destroy.restype = ctypes.c_int32
fskframegen_destroy.argtypes = [fskframegen]
fskframegen_print = liquiddsp.fskframegen_print
fskframegen_print.restype = ctypes.c_int32
fskframegen_print.argtypes = [fskframegen]
fskframegen_reset = liquiddsp.fskframegen_reset
fskframegen_reset.restype = ctypes.c_int32
fskframegen_reset.argtypes = [fskframegen]
fskframegen_assemble = liquiddsp.fskframegen_assemble
fskframegen_assemble.restype = ctypes.c_int32
fskframegen_assemble.argtypes = [fskframegen, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, crc_scheme, fec_scheme, fec_scheme]
fskframegen_getframelen = liquiddsp.fskframegen_getframelen
fskframegen_getframelen.restype = ctypes.c_uint32
fskframegen_getframelen.argtypes = [fskframegen]
fskframegen_write_samples = liquiddsp.fskframegen_write_samples
fskframegen_write_samples.restype = ctypes.c_int32
fskframegen_write_samples.argtypes = [fskframegen, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
class struct_fskframesync_s(Structure):
    pass

fskframesync = ctypes.POINTER(struct_fskframesync_s)
fskframesync_create = liquiddsp.fskframesync_create
fskframesync_create.restype = fskframesync
fskframesync_create.argtypes = [framesync_callback, ctypes.POINTER(None)]
fskframesync_destroy = liquiddsp.fskframesync_destroy
fskframesync_destroy.restype = ctypes.c_int32
fskframesync_destroy.argtypes = [fskframesync]
fskframesync_print = liquiddsp.fskframesync_print
fskframesync_print.restype = ctypes.c_int32
fskframesync_print.argtypes = [fskframesync]
fskframesync_reset = liquiddsp.fskframesync_reset
fskframesync_reset.restype = ctypes.c_int32
fskframesync_reset.argtypes = [fskframesync]
fskframesync_execute = liquiddsp.fskframesync_execute
fskframesync_execute.restype = ctypes.c_int32
fskframesync_execute.argtypes = [fskframesync, liquid_float_complex]
fskframesync_execute_block = liquiddsp.fskframesync_execute_block
fskframesync_execute_block.restype = ctypes.c_int32
fskframesync_execute_block.argtypes = [fskframesync, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
fskframesync_debug_enable = liquiddsp.fskframesync_debug_enable
fskframesync_debug_enable.restype = ctypes.c_int32
fskframesync_debug_enable.argtypes = [fskframesync]
fskframesync_debug_disable = liquiddsp.fskframesync_debug_disable
fskframesync_debug_disable.restype = ctypes.c_int32
fskframesync_debug_disable.argtypes = [fskframesync]
fskframesync_debug_export = liquiddsp.fskframesync_debug_export
fskframesync_debug_export.restype = ctypes.c_int32
fskframesync_debug_export.argtypes = [fskframesync, ctypes.POINTER(ctypes.c_char)]
class struct_gmskframegen_s(Structure):
    pass

gmskframegen = ctypes.POINTER(struct_gmskframegen_s)
gmskframegen_create = liquiddsp.gmskframegen_create
gmskframegen_create.restype = gmskframegen
gmskframegen_create.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float]
gmskframegen_destroy = liquiddsp.gmskframegen_destroy
gmskframegen_destroy.restype = ctypes.c_int32
gmskframegen_destroy.argtypes = [gmskframegen]
gmskframegen_is_assembled = liquiddsp.gmskframegen_is_assembled
gmskframegen_is_assembled.restype = ctypes.c_int32
gmskframegen_is_assembled.argtypes = [gmskframegen]
gmskframegen_print = liquiddsp.gmskframegen_print
gmskframegen_print.restype = ctypes.c_int32
gmskframegen_print.argtypes = [gmskframegen]
gmskframegen_set_header_len = liquiddsp.gmskframegen_set_header_len
gmskframegen_set_header_len.restype = ctypes.c_int32
gmskframegen_set_header_len.argtypes = [gmskframegen, ctypes.c_uint32]
gmskframegen_reset = liquiddsp.gmskframegen_reset
gmskframegen_reset.restype = ctypes.c_int32
gmskframegen_reset.argtypes = [gmskframegen]
gmskframegen_assemble = liquiddsp.gmskframegen_assemble
gmskframegen_assemble.restype = ctypes.c_int32
gmskframegen_assemble.argtypes = [gmskframegen, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, crc_scheme, fec_scheme, fec_scheme]
gmskframegen_getframelen = liquiddsp.gmskframegen_getframelen
gmskframegen_getframelen.restype = ctypes.c_uint32
gmskframegen_getframelen.argtypes = [gmskframegen]
gmskframegen_write_samples = liquiddsp.gmskframegen_write_samples
gmskframegen_write_samples.restype = ctypes.c_int32
gmskframegen_write_samples.argtypes = [gmskframegen, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
gmskframegen_write = liquiddsp.gmskframegen_write
gmskframegen_write.restype = ctypes.c_int32
gmskframegen_write.argtypes = [gmskframegen, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
class struct_gmskframesync_s(Structure):
    pass

gmskframesync = ctypes.POINTER(struct_gmskframesync_s)
gmskframesync_create = liquiddsp.gmskframesync_create
gmskframesync_create.restype = gmskframesync
gmskframesync_create.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, framesync_callback, ctypes.POINTER(None)]
gmskframesync_destroy = liquiddsp.gmskframesync_destroy
gmskframesync_destroy.restype = ctypes.c_int32
gmskframesync_destroy.argtypes = [gmskframesync]
gmskframesync_print = liquiddsp.gmskframesync_print
gmskframesync_print.restype = ctypes.c_int32
gmskframesync_print.argtypes = [gmskframesync]
gmskframesync_set_header_len = liquiddsp.gmskframesync_set_header_len
gmskframesync_set_header_len.restype = ctypes.c_int32
gmskframesync_set_header_len.argtypes = [gmskframesync, ctypes.c_uint32]
gmskframesync_reset = liquiddsp.gmskframesync_reset
gmskframesync_reset.restype = ctypes.c_int32
gmskframesync_reset.argtypes = [gmskframesync]
gmskframesync_is_frame_open = liquiddsp.gmskframesync_is_frame_open
gmskframesync_is_frame_open.restype = ctypes.c_int32
gmskframesync_is_frame_open.argtypes = [gmskframesync]
gmskframesync_execute = liquiddsp.gmskframesync_execute
gmskframesync_execute.restype = ctypes.c_int32
gmskframesync_execute.argtypes = [gmskframesync, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
gmskframesync_reset_framedatastats = liquiddsp.gmskframesync_reset_framedatastats
gmskframesync_reset_framedatastats.restype = ctypes.c_int32
gmskframesync_reset_framedatastats.argtypes = [gmskframesync]
gmskframesync_get_framedatastats = liquiddsp.gmskframesync_get_framedatastats
gmskframesync_get_framedatastats.restype = framedatastats_s
gmskframesync_get_framedatastats.argtypes = [gmskframesync]
gmskframesync_debug_enable = liquiddsp.gmskframesync_debug_enable
gmskframesync_debug_enable.restype = ctypes.c_int32
gmskframesync_debug_enable.argtypes = [gmskframesync]
gmskframesync_debug_disable = liquiddsp.gmskframesync_debug_disable
gmskframesync_debug_disable.restype = ctypes.c_int32
gmskframesync_debug_disable.argtypes = [gmskframesync]
gmskframesync_debug_print = liquiddsp.gmskframesync_debug_print
gmskframesync_debug_print.restype = ctypes.c_int32
gmskframesync_debug_print.argtypes = [gmskframesync, ctypes.POINTER(ctypes.c_char)]
class struct_c__SA_dsssframegenprops_s(Structure):
    pass

struct_c__SA_dsssframegenprops_s._pack_ = 1 # source:False
struct_c__SA_dsssframegenprops_s._fields_ = [
    ('check', ctypes.c_uint32),
    ('fec0', ctypes.c_uint32),
    ('fec1', ctypes.c_uint32),
]

dsssframegenprops_s = struct_c__SA_dsssframegenprops_s
class struct_dsssframegen_s(Structure):
    pass

dsssframegen = ctypes.POINTER(struct_dsssframegen_s)
dsssframegen_create = liquiddsp.dsssframegen_create
dsssframegen_create.restype = dsssframegen
dsssframegen_create.argtypes = [ctypes.POINTER(struct_c__SA_dsssframegenprops_s)]
dsssframegen_destroy = liquiddsp.dsssframegen_destroy
dsssframegen_destroy.restype = ctypes.c_int32
dsssframegen_destroy.argtypes = [dsssframegen]
dsssframegen_reset = liquiddsp.dsssframegen_reset
dsssframegen_reset.restype = ctypes.c_int32
dsssframegen_reset.argtypes = [dsssframegen]
dsssframegen_is_assembled = liquiddsp.dsssframegen_is_assembled
dsssframegen_is_assembled.restype = ctypes.c_int32
dsssframegen_is_assembled.argtypes = [dsssframegen]
dsssframegen_getprops = liquiddsp.dsssframegen_getprops
dsssframegen_getprops.restype = ctypes.c_int32
dsssframegen_getprops.argtypes = [dsssframegen, ctypes.POINTER(struct_c__SA_dsssframegenprops_s)]
dsssframegen_setprops = liquiddsp.dsssframegen_setprops
dsssframegen_setprops.restype = ctypes.c_int32
dsssframegen_setprops.argtypes = [dsssframegen, ctypes.POINTER(struct_c__SA_dsssframegenprops_s)]
dsssframegen_set_header_len = liquiddsp.dsssframegen_set_header_len
dsssframegen_set_header_len.restype = ctypes.c_int32
dsssframegen_set_header_len.argtypes = [dsssframegen, ctypes.c_uint32]
dsssframegen_set_header_props = liquiddsp.dsssframegen_set_header_props
dsssframegen_set_header_props.restype = ctypes.c_int32
dsssframegen_set_header_props.argtypes = [dsssframegen, ctypes.POINTER(struct_c__SA_dsssframegenprops_s)]
dsssframegen_getframelen = liquiddsp.dsssframegen_getframelen
dsssframegen_getframelen.restype = ctypes.c_uint32
dsssframegen_getframelen.argtypes = [dsssframegen]
dsssframegen_assemble = liquiddsp.dsssframegen_assemble
dsssframegen_assemble.restype = ctypes.c_int32
dsssframegen_assemble.argtypes = [dsssframegen, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32]
dsssframegen_write_samples = liquiddsp.dsssframegen_write_samples
dsssframegen_write_samples.restype = ctypes.c_int32
dsssframegen_write_samples.argtypes = [dsssframegen, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
class struct_dsssframesync_s(Structure):
    pass

dsssframesync = ctypes.POINTER(struct_dsssframesync_s)
dsssframesync_create = liquiddsp.dsssframesync_create
dsssframesync_create.restype = dsssframesync
dsssframesync_create.argtypes = [framesync_callback, ctypes.POINTER(None)]
dsssframesync_destroy = liquiddsp.dsssframesync_destroy
dsssframesync_destroy.restype = ctypes.c_int32
dsssframesync_destroy.argtypes = [dsssframesync]
dsssframesync_print = liquiddsp.dsssframesync_print
dsssframesync_print.restype = ctypes.c_int32
dsssframesync_print.argtypes = [dsssframesync]
dsssframesync_reset = liquiddsp.dsssframesync_reset
dsssframesync_reset.restype = ctypes.c_int32
dsssframesync_reset.argtypes = [dsssframesync]
dsssframesync_is_frame_open = liquiddsp.dsssframesync_is_frame_open
dsssframesync_is_frame_open.restype = ctypes.c_int32
dsssframesync_is_frame_open.argtypes = [dsssframesync]
dsssframesync_set_header_len = liquiddsp.dsssframesync_set_header_len
dsssframesync_set_header_len.restype = ctypes.c_int32
dsssframesync_set_header_len.argtypes = [dsssframesync, ctypes.c_uint32]
dsssframesync_decode_header_soft = liquiddsp.dsssframesync_decode_header_soft
dsssframesync_decode_header_soft.restype = ctypes.c_int32
dsssframesync_decode_header_soft.argtypes = [dsssframesync, ctypes.c_int32]
dsssframesync_decode_payload_soft = liquiddsp.dsssframesync_decode_payload_soft
dsssframesync_decode_payload_soft.restype = ctypes.c_int32
dsssframesync_decode_payload_soft.argtypes = [dsssframesync, ctypes.c_int32]
dsssframesync_set_header_props = liquiddsp.dsssframesync_set_header_props
dsssframesync_set_header_props.restype = ctypes.c_int32
dsssframesync_set_header_props.argtypes = [dsssframesync, ctypes.POINTER(struct_c__SA_dsssframegenprops_s)]
dsssframesync_execute = liquiddsp.dsssframesync_execute
dsssframesync_execute.restype = ctypes.c_int32
dsssframesync_execute.argtypes = [dsssframesync, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
dsssframesync_reset_framedatastats = liquiddsp.dsssframesync_reset_framedatastats
dsssframesync_reset_framedatastats.restype = ctypes.c_int32
dsssframesync_reset_framedatastats.argtypes = [dsssframesync]
dsssframesync_debug_enable = liquiddsp.dsssframesync_debug_enable
dsssframesync_debug_enable.restype = ctypes.c_int32
dsssframesync_debug_enable.argtypes = [dsssframesync]
dsssframesync_debug_disable = liquiddsp.dsssframesync_debug_disable
dsssframesync_debug_disable.restype = ctypes.c_int32
dsssframesync_debug_disable.argtypes = [dsssframesync]
dsssframesync_debug_print = liquiddsp.dsssframesync_debug_print
dsssframesync_debug_print.restype = ctypes.c_int32
dsssframesync_debug_print.argtypes = [dsssframesync, ctypes.POINTER(ctypes.c_char)]
dsssframesync_get_framedatastats = liquiddsp.dsssframesync_get_framedatastats
dsssframesync_get_framedatastats.restype = framedatastats_s
dsssframesync_get_framedatastats.argtypes = [dsssframesync]
class struct_c__SA_ofdmflexframegenprops_s(Structure):
    pass

struct_c__SA_ofdmflexframegenprops_s._pack_ = 1 # source:False
struct_c__SA_ofdmflexframegenprops_s._fields_ = [
    ('check', ctypes.c_uint32),
    ('fec0', ctypes.c_uint32),
    ('fec1', ctypes.c_uint32),
    ('mod_scheme', ctypes.c_uint32),
]

ofdmflexframegenprops_s = struct_c__SA_ofdmflexframegenprops_s
ofdmflexframegenprops_init_default = liquiddsp.ofdmflexframegenprops_init_default
ofdmflexframegenprops_init_default.restype = ctypes.c_int32
ofdmflexframegenprops_init_default.argtypes = [ctypes.POINTER(struct_c__SA_ofdmflexframegenprops_s)]
class struct_ofdmflexframegen_s(Structure):
    pass
struct_ofdmflexframegen_s._pack_ = 1
struct_ofdmflexframegen_s._fields_ = [
    ('M', ctypes.c_uint32),
    ('cp_len', ctypes.c_uint32),
    ('taper_len', ctypes.c_uint32),
]

ofdmflexframegen = ctypes.POINTER(struct_ofdmflexframegen_s)
ofdmflexframegen_create = liquiddsp.ofdmflexframegen_create
ofdmflexframegen_create.restype = ofdmflexframegen
ofdmflexframegen_create.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(struct_c__SA_ofdmflexframegenprops_s)]
ofdmflexframegen_destroy = liquiddsp.ofdmflexframegen_destroy
ofdmflexframegen_destroy.restype = ctypes.c_int32
ofdmflexframegen_destroy.argtypes = [ofdmflexframegen]
ofdmflexframegen_print = liquiddsp.ofdmflexframegen_print
ofdmflexframegen_print.restype = ctypes.c_int32
ofdmflexframegen_print.argtypes = [ofdmflexframegen]
ofdmflexframegen_reset = liquiddsp.ofdmflexframegen_reset
ofdmflexframegen_reset.restype = ctypes.c_int32
ofdmflexframegen_reset.argtypes = [ofdmflexframegen]
ofdmflexframegen_is_assembled = liquiddsp.ofdmflexframegen_is_assembled
ofdmflexframegen_is_assembled.restype = ctypes.c_int32
ofdmflexframegen_is_assembled.argtypes = [ofdmflexframegen]
ofdmflexframegen_getprops = liquiddsp.ofdmflexframegen_getprops
ofdmflexframegen_getprops.restype = ctypes.c_int32
ofdmflexframegen_getprops.argtypes = [ofdmflexframegen, ctypes.POINTER(struct_c__SA_ofdmflexframegenprops_s)]
ofdmflexframegen_setprops = liquiddsp.ofdmflexframegen_setprops
ofdmflexframegen_setprops.restype = ctypes.c_int32
ofdmflexframegen_setprops.argtypes = [ofdmflexframegen, ctypes.POINTER(struct_c__SA_ofdmflexframegenprops_s)]
ofdmflexframegen_set_header_len = liquiddsp.ofdmflexframegen_set_header_len
ofdmflexframegen_set_header_len.restype = ctypes.c_int32
ofdmflexframegen_set_header_len.argtypes = [ofdmflexframegen, ctypes.c_uint32]
ofdmflexframegen_set_header_props = liquiddsp.ofdmflexframegen_set_header_props
ofdmflexframegen_set_header_props.restype = ctypes.c_int32
ofdmflexframegen_set_header_props.argtypes = [ofdmflexframegen, ctypes.POINTER(struct_c__SA_ofdmflexframegenprops_s)]
ofdmflexframegen_getframelen = liquiddsp.ofdmflexframegen_getframelen
ofdmflexframegen_getframelen.restype = ctypes.c_uint32
ofdmflexframegen_getframelen.argtypes = [ofdmflexframegen]
ofdmflexframegen_assemble = liquiddsp.ofdmflexframegen_assemble
ofdmflexframegen_assemble.restype = ctypes.c_int32
ofdmflexframegen_assemble.argtypes = [ofdmflexframegen, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32]
ofdmflexframegen_write = liquiddsp.ofdmflexframegen_write
ofdmflexframegen_write.restype = ctypes.c_int32
ofdmflexframegen_write.argtypes = [ofdmflexframegen, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
class struct_ofdmflexframesync_s(Structure):
    pass

ofdmflexframesync = ctypes.POINTER(struct_ofdmflexframesync_s)
ofdmflexframesync_create = liquiddsp.ofdmflexframesync_create
ofdmflexframesync_create.restype = ofdmflexframesync
ofdmflexframesync_create.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_ubyte), framesync_callback, ctypes.POINTER(None)]
ofdmflexframesync_destroy = liquiddsp.ofdmflexframesync_destroy
ofdmflexframesync_destroy.restype = ctypes.c_int32
ofdmflexframesync_destroy.argtypes = [ofdmflexframesync]
ofdmflexframesync_print = liquiddsp.ofdmflexframesync_print
ofdmflexframesync_print.restype = ctypes.c_int32
ofdmflexframesync_print.argtypes = [ofdmflexframesync]
ofdmflexframesync_set_header_len = liquiddsp.ofdmflexframesync_set_header_len
ofdmflexframesync_set_header_len.restype = ctypes.c_int32
ofdmflexframesync_set_header_len.argtypes = [ofdmflexframesync, ctypes.c_uint32]
ofdmflexframesync_decode_header_soft = liquiddsp.ofdmflexframesync_decode_header_soft
ofdmflexframesync_decode_header_soft.restype = ctypes.c_int32
ofdmflexframesync_decode_header_soft.argtypes = [ofdmflexframesync, ctypes.c_int32]
ofdmflexframesync_decode_payload_soft = liquiddsp.ofdmflexframesync_decode_payload_soft
ofdmflexframesync_decode_payload_soft.restype = ctypes.c_int32
ofdmflexframesync_decode_payload_soft.argtypes = [ofdmflexframesync, ctypes.c_int32]
ofdmflexframesync_set_header_props = liquiddsp.ofdmflexframesync_set_header_props
ofdmflexframesync_set_header_props.restype = ctypes.c_int32
ofdmflexframesync_set_header_props.argtypes = [ofdmflexframesync, ctypes.POINTER(struct_c__SA_ofdmflexframegenprops_s)]
ofdmflexframesync_reset = liquiddsp.ofdmflexframesync_reset
ofdmflexframesync_reset.restype = ctypes.c_int32
ofdmflexframesync_reset.argtypes = [ofdmflexframesync]
ofdmflexframesync_is_frame_open = liquiddsp.ofdmflexframesync_is_frame_open
ofdmflexframesync_is_frame_open.restype = ctypes.c_int32
ofdmflexframesync_is_frame_open.argtypes = [ofdmflexframesync]
ofdmflexframesync_execute = liquiddsp.ofdmflexframesync_execute
ofdmflexframesync_execute.restype = ctypes.c_int32
ofdmflexframesync_execute.argtypes = [ofdmflexframesync, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
ofdmflexframesync_get_rssi = liquiddsp.ofdmflexframesync_get_rssi
ofdmflexframesync_get_rssi.restype = ctypes.c_float
ofdmflexframesync_get_rssi.argtypes = [ofdmflexframesync]
ofdmflexframesync_get_cfo = liquiddsp.ofdmflexframesync_get_cfo
ofdmflexframesync_get_cfo.restype = ctypes.c_float
ofdmflexframesync_get_cfo.argtypes = [ofdmflexframesync]
ofdmflexframesync_reset_framedatastats = liquiddsp.ofdmflexframesync_reset_framedatastats
ofdmflexframesync_reset_framedatastats.restype = ctypes.c_int32
ofdmflexframesync_reset_framedatastats.argtypes = [ofdmflexframesync]
ofdmflexframesync_get_framedatastats = liquiddsp.ofdmflexframesync_get_framedatastats
ofdmflexframesync_get_framedatastats.restype = framedatastats_s
ofdmflexframesync_get_framedatastats.argtypes = [ofdmflexframesync]
ofdmflexframesync_set_cfo = liquiddsp.ofdmflexframesync_set_cfo
ofdmflexframesync_set_cfo.restype = ctypes.c_int32
ofdmflexframesync_set_cfo.argtypes = [ofdmflexframesync, ctypes.c_float]
ofdmflexframesync_debug_enable = liquiddsp.ofdmflexframesync_debug_enable
ofdmflexframesync_debug_enable.restype = ctypes.c_int32
ofdmflexframesync_debug_enable.argtypes = [ofdmflexframesync]
ofdmflexframesync_debug_disable = liquiddsp.ofdmflexframesync_debug_disable
ofdmflexframesync_debug_disable.restype = ctypes.c_int32
ofdmflexframesync_debug_disable.argtypes = [ofdmflexframesync]
ofdmflexframesync_debug_print = liquiddsp.ofdmflexframesync_debug_print
ofdmflexframesync_debug_print.restype = ctypes.c_int32
ofdmflexframesync_debug_print.argtypes = [ofdmflexframesync, ctypes.POINTER(ctypes.c_char)]
class struct_bsync_rrrf_s(Structure):
    pass

bsync_rrrf = ctypes.POINTER(struct_bsync_rrrf_s)
bsync_rrrf_create = liquiddsp.bsync_rrrf_create
bsync_rrrf_create.restype = bsync_rrrf
bsync_rrrf_create.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
bsync_rrrf_create_msequence = liquiddsp.bsync_rrrf_create_msequence
bsync_rrrf_create_msequence.restype = bsync_rrrf
bsync_rrrf_create_msequence.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
bsync_rrrf_destroy = liquiddsp.bsync_rrrf_destroy
bsync_rrrf_destroy.restype = None
bsync_rrrf_destroy.argtypes = [bsync_rrrf]
bsync_rrrf_print = liquiddsp.bsync_rrrf_print
bsync_rrrf_print.restype = None
bsync_rrrf_print.argtypes = [bsync_rrrf]
bsync_rrrf_correlate = liquiddsp.bsync_rrrf_correlate
bsync_rrrf_correlate.restype = None
bsync_rrrf_correlate.argtypes = [bsync_rrrf, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
class struct_bsync_crcf_s(Structure):
    pass

bsync_crcf = ctypes.POINTER(struct_bsync_crcf_s)
bsync_crcf_create = liquiddsp.bsync_crcf_create
bsync_crcf_create.restype = bsync_crcf
bsync_crcf_create.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
bsync_crcf_create_msequence = liquiddsp.bsync_crcf_create_msequence
bsync_crcf_create_msequence.restype = bsync_crcf
bsync_crcf_create_msequence.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
bsync_crcf_destroy = liquiddsp.bsync_crcf_destroy
bsync_crcf_destroy.restype = None
bsync_crcf_destroy.argtypes = [bsync_crcf]
bsync_crcf_print = liquiddsp.bsync_crcf_print
bsync_crcf_print.restype = None
bsync_crcf_print.argtypes = [bsync_crcf]
bsync_crcf_correlate = liquiddsp.bsync_crcf_correlate
bsync_crcf_correlate.restype = None
bsync_crcf_correlate.argtypes = [bsync_crcf, liquid_float_complex, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
class struct_bsync_cccf_s(Structure):
    pass

bsync_cccf = ctypes.POINTER(struct_bsync_cccf_s)
bsync_cccf_create = liquiddsp.bsync_cccf_create
bsync_cccf_create.restype = bsync_cccf
bsync_cccf_create.argtypes = [ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
bsync_cccf_create_msequence = liquiddsp.bsync_cccf_create_msequence
bsync_cccf_create_msequence.restype = bsync_cccf
bsync_cccf_create_msequence.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
bsync_cccf_destroy = liquiddsp.bsync_cccf_destroy
bsync_cccf_destroy.restype = None
bsync_cccf_destroy.argtypes = [bsync_cccf]
bsync_cccf_print = liquiddsp.bsync_cccf_print
bsync_cccf_print.restype = None
bsync_cccf_print.argtypes = [bsync_cccf]
bsync_cccf_correlate = liquiddsp.bsync_cccf_correlate
bsync_cccf_correlate.restype = None
bsync_cccf_correlate.argtypes = [bsync_cccf, liquid_float_complex, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
class struct_presync_cccf_s(Structure):
    pass

presync_cccf = ctypes.POINTER(struct_presync_cccf_s)
presync_cccf_create = liquiddsp.presync_cccf_create
presync_cccf_create.restype = presync_cccf
presync_cccf_create.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_float, ctypes.c_uint32]
presync_cccf_destroy = liquiddsp.presync_cccf_destroy
presync_cccf_destroy.restype = ctypes.c_int32
presync_cccf_destroy.argtypes = [presync_cccf]
presync_cccf_print = liquiddsp.presync_cccf_print
presync_cccf_print.restype = ctypes.c_int32
presync_cccf_print.argtypes = [presync_cccf]
presync_cccf_reset = liquiddsp.presync_cccf_reset
presync_cccf_reset.restype = ctypes.c_int32
presync_cccf_reset.argtypes = [presync_cccf]
presync_cccf_push = liquiddsp.presync_cccf_push
presync_cccf_push.restype = ctypes.c_int32
presync_cccf_push.argtypes = [presync_cccf, liquid_float_complex]
presync_cccf_execute = liquiddsp.presync_cccf_execute
presync_cccf_execute.restype = ctypes.c_int32
presync_cccf_execute.argtypes = [presync_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(ctypes.c_float)]
class struct_bpresync_cccf_s(Structure):
    pass

bpresync_cccf = ctypes.POINTER(struct_bpresync_cccf_s)
bpresync_cccf_create = liquiddsp.bpresync_cccf_create
bpresync_cccf_create.restype = bpresync_cccf
bpresync_cccf_create.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_float, ctypes.c_uint32]
bpresync_cccf_destroy = liquiddsp.bpresync_cccf_destroy
bpresync_cccf_destroy.restype = ctypes.c_int32
bpresync_cccf_destroy.argtypes = [bpresync_cccf]
bpresync_cccf_print = liquiddsp.bpresync_cccf_print
bpresync_cccf_print.restype = ctypes.c_int32
bpresync_cccf_print.argtypes = [bpresync_cccf]
bpresync_cccf_reset = liquiddsp.bpresync_cccf_reset
bpresync_cccf_reset.restype = ctypes.c_int32
bpresync_cccf_reset.argtypes = [bpresync_cccf]
bpresync_cccf_push = liquiddsp.bpresync_cccf_push
bpresync_cccf_push.restype = ctypes.c_int32
bpresync_cccf_push.argtypes = [bpresync_cccf, liquid_float_complex]
bpresync_cccf_execute = liquiddsp.bpresync_cccf_execute
bpresync_cccf_execute.restype = ctypes.c_int32
bpresync_cccf_execute.argtypes = [bpresync_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(ctypes.c_float)]
class struct_qdetector_cccf_s(Structure):
    pass

qdetector_cccf = ctypes.POINTER(struct_qdetector_cccf_s)
qdetector_cccf_create = liquiddsp.qdetector_cccf_create
qdetector_cccf_create.restype = qdetector_cccf
qdetector_cccf_create.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
qdetector_cccf_create_linear = liquiddsp.qdetector_cccf_create_linear
qdetector_cccf_create_linear.restype = qdetector_cccf
qdetector_cccf_create_linear.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float]
qdetector_cccf_create_gmsk = liquiddsp.qdetector_cccf_create_gmsk
qdetector_cccf_create_gmsk.restype = qdetector_cccf
qdetector_cccf_create_gmsk.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float]
qdetector_cccf_create_cpfsk = liquiddsp.qdetector_cccf_create_cpfsk
qdetector_cccf_create_cpfsk.restype = qdetector_cccf
qdetector_cccf_create_cpfsk.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_int32]
qdetector_cccf_destroy = liquiddsp.qdetector_cccf_destroy
qdetector_cccf_destroy.restype = ctypes.c_int32
qdetector_cccf_destroy.argtypes = [qdetector_cccf]
qdetector_cccf_print = liquiddsp.qdetector_cccf_print
qdetector_cccf_print.restype = ctypes.c_int32
qdetector_cccf_print.argtypes = [qdetector_cccf]
qdetector_cccf_reset = liquiddsp.qdetector_cccf_reset
qdetector_cccf_reset.restype = ctypes.c_int32
qdetector_cccf_reset.argtypes = [qdetector_cccf]
qdetector_cccf_execute = liquiddsp.qdetector_cccf_execute
qdetector_cccf_execute.restype = ctypes.POINTER(None)
qdetector_cccf_execute.argtypes = [qdetector_cccf, liquid_float_complex]
qdetector_cccf_set_threshold = liquiddsp.qdetector_cccf_set_threshold
qdetector_cccf_set_threshold.restype = ctypes.c_int32
qdetector_cccf_set_threshold.argtypes = [qdetector_cccf, ctypes.c_float]
qdetector_cccf_set_range = liquiddsp.qdetector_cccf_set_range
qdetector_cccf_set_range.restype = ctypes.c_int32
qdetector_cccf_set_range.argtypes = [qdetector_cccf, ctypes.c_float]
qdetector_cccf_get_seq_len = liquiddsp.qdetector_cccf_get_seq_len
qdetector_cccf_get_seq_len.restype = ctypes.c_uint32
qdetector_cccf_get_seq_len.argtypes = [qdetector_cccf]
qdetector_cccf_get_sequence = liquiddsp.qdetector_cccf_get_sequence
qdetector_cccf_get_sequence.restype = ctypes.POINTER(None)
qdetector_cccf_get_sequence.argtypes = [qdetector_cccf]
qdetector_cccf_get_buf_len = liquiddsp.qdetector_cccf_get_buf_len
qdetector_cccf_get_buf_len.restype = ctypes.c_uint32
qdetector_cccf_get_buf_len.argtypes = [qdetector_cccf]
qdetector_cccf_get_rxy = liquiddsp.qdetector_cccf_get_rxy
qdetector_cccf_get_rxy.restype = ctypes.c_float
qdetector_cccf_get_rxy.argtypes = [qdetector_cccf]
qdetector_cccf_get_tau = liquiddsp.qdetector_cccf_get_tau
qdetector_cccf_get_tau.restype = ctypes.c_float
qdetector_cccf_get_tau.argtypes = [qdetector_cccf]
qdetector_cccf_get_gamma = liquiddsp.qdetector_cccf_get_gamma
qdetector_cccf_get_gamma.restype = ctypes.c_float
qdetector_cccf_get_gamma.argtypes = [qdetector_cccf]
qdetector_cccf_get_dphi = liquiddsp.qdetector_cccf_get_dphi
qdetector_cccf_get_dphi.restype = ctypes.c_float
qdetector_cccf_get_dphi.argtypes = [qdetector_cccf]
qdetector_cccf_get_phi = liquiddsp.qdetector_cccf_get_phi
qdetector_cccf_get_phi.restype = ctypes.c_float
qdetector_cccf_get_phi.argtypes = [qdetector_cccf]
class struct_detector_cccf_s(Structure):
    pass

detector_cccf = ctypes.POINTER(struct_detector_cccf_s)
detector_cccf_create = liquiddsp.detector_cccf_create
detector_cccf_create.restype = detector_cccf
detector_cccf_create.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_float, ctypes.c_float]
detector_cccf_destroy = liquiddsp.detector_cccf_destroy
detector_cccf_destroy.restype = None
detector_cccf_destroy.argtypes = [detector_cccf]
detector_cccf_print = liquiddsp.detector_cccf_print
detector_cccf_print.restype = None
detector_cccf_print.argtypes = [detector_cccf]
detector_cccf_reset = liquiddsp.detector_cccf_reset
detector_cccf_reset.restype = None
detector_cccf_reset.argtypes = [detector_cccf]
detector_cccf_correlate = liquiddsp.detector_cccf_correlate
detector_cccf_correlate.restype = ctypes.c_int32
detector_cccf_correlate.argtypes = [detector_cccf, liquid_float_complex, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
class struct_symstreamcf_s(Structure):
    pass

symstreamcf = ctypes.POINTER(struct_symstreamcf_s)
symstreamcf_create = liquiddsp.symstreamcf_create
symstreamcf_create.restype = symstreamcf
symstreamcf_create.argtypes = []
symstreamcf_create_linear = liquiddsp.symstreamcf_create_linear
symstreamcf_create_linear.restype = symstreamcf
symstreamcf_create_linear.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_int32]
symstreamcf_destroy = liquiddsp.symstreamcf_destroy
symstreamcf_destroy.restype = ctypes.c_int32
symstreamcf_destroy.argtypes = [symstreamcf]
symstreamcf_print = liquiddsp.symstreamcf_print
symstreamcf_print.restype = ctypes.c_int32
symstreamcf_print.argtypes = [symstreamcf]
symstreamcf_reset = liquiddsp.symstreamcf_reset
symstreamcf_reset.restype = ctypes.c_int32
symstreamcf_reset.argtypes = [symstreamcf]
symstreamcf_set_scheme = liquiddsp.symstreamcf_set_scheme
symstreamcf_set_scheme.restype = ctypes.c_int32
symstreamcf_set_scheme.argtypes = [symstreamcf, ctypes.c_int32]
symstreamcf_get_scheme = liquiddsp.symstreamcf_get_scheme
symstreamcf_get_scheme.restype = ctypes.c_int32
symstreamcf_get_scheme.argtypes = [symstreamcf]
symstreamcf_set_gain = liquiddsp.symstreamcf_set_gain
symstreamcf_set_gain.restype = ctypes.c_int32
symstreamcf_set_gain.argtypes = [symstreamcf, ctypes.c_float]
symstreamcf_get_gain = liquiddsp.symstreamcf_get_gain
symstreamcf_get_gain.restype = ctypes.c_float
symstreamcf_get_gain.argtypes = [symstreamcf]
symstreamcf_write_samples = liquiddsp.symstreamcf_write_samples
symstreamcf_write_samples.restype = ctypes.c_int32
symstreamcf_write_samples.argtypes = [symstreamcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
class struct_symstreamrcf_s(Structure):
    pass

symstreamrcf = ctypes.POINTER(struct_symstreamrcf_s)
symstreamrcf_create = liquiddsp.symstreamrcf_create
symstreamrcf_create.restype = symstreamrcf
symstreamrcf_create.argtypes = []
symstreamrcf_create_linear = liquiddsp.symstreamrcf_create_linear
symstreamrcf_create_linear.restype = symstreamrcf
symstreamrcf_create_linear.argtypes = [ctypes.c_int32, ctypes.c_float, ctypes.c_uint32, ctypes.c_float, ctypes.c_int32]
symstreamrcf_destroy = liquiddsp.symstreamrcf_destroy
symstreamrcf_destroy.restype = ctypes.c_int32
symstreamrcf_destroy.argtypes = [symstreamrcf]
symstreamrcf_print = liquiddsp.symstreamrcf_print
symstreamrcf_print.restype = ctypes.c_int32
symstreamrcf_print.argtypes = [symstreamrcf]
symstreamrcf_reset = liquiddsp.symstreamrcf_reset
symstreamrcf_reset.restype = ctypes.c_int32
symstreamrcf_reset.argtypes = [symstreamrcf]
symstreamrcf_set_scheme = liquiddsp.symstreamrcf_set_scheme
symstreamrcf_set_scheme.restype = ctypes.c_int32
symstreamrcf_set_scheme.argtypes = [symstreamrcf, ctypes.c_int32]
symstreamrcf_get_scheme = liquiddsp.symstreamrcf_get_scheme
symstreamrcf_get_scheme.restype = ctypes.c_int32
symstreamrcf_get_scheme.argtypes = [symstreamrcf]
symstreamrcf_set_gain = liquiddsp.symstreamrcf_set_gain
symstreamrcf_set_gain.restype = ctypes.c_int32
symstreamrcf_set_gain.argtypes = [symstreamrcf, ctypes.c_float]
symstreamrcf_get_gain = liquiddsp.symstreamrcf_get_gain
symstreamrcf_get_gain.restype = ctypes.c_float
symstreamrcf_get_gain.argtypes = [symstreamrcf]
symstreamrcf_write_samples = liquiddsp.symstreamrcf_write_samples
symstreamrcf_write_samples.restype = ctypes.c_int32
symstreamrcf_write_samples.argtypes = [symstreamrcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
class struct_msourcecf_s(Structure):
    pass

msourcecf = ctypes.POINTER(struct_msourcecf_s)
msourcecf_create = liquiddsp.msourcecf_create
msourcecf_create.restype = msourcecf
msourcecf_create.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float]
msourcecf_create_default = liquiddsp.msourcecf_create_default
msourcecf_create_default.restype = msourcecf
msourcecf_create_default.argtypes = []
msourcecf_destroy = liquiddsp.msourcecf_destroy
msourcecf_destroy.restype = ctypes.c_int32
msourcecf_destroy.argtypes = [msourcecf]
msourcecf_print = liquiddsp.msourcecf_print
msourcecf_print.restype = ctypes.c_int32
msourcecf_print.argtypes = [msourcecf]
msourcecf_reset = liquiddsp.msourcecf_reset
msourcecf_reset.restype = ctypes.c_int32
msourcecf_reset.argtypes = [msourcecf]
msourcecf_callback = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.POINTER(None), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32)
msourcecf_add_user = liquiddsp.msourcecf_add_user
msourcecf_add_user.restype = ctypes.c_int32
msourcecf_add_user.argtypes = [msourcecf, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.POINTER(None), msourcecf_callback]
msourcecf_add_tone = liquiddsp.msourcecf_add_tone
msourcecf_add_tone.restype = ctypes.c_int32
msourcecf_add_tone.argtypes = [msourcecf, ctypes.c_float, ctypes.c_float, ctypes.c_float]
msourcecf_add_chirp = liquiddsp.msourcecf_add_chirp
msourcecf_add_chirp.restype = ctypes.c_int32
msourcecf_add_chirp.argtypes = [msourcecf, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_int32, ctypes.c_int32]
msourcecf_add_noise = liquiddsp.msourcecf_add_noise
msourcecf_add_noise.restype = ctypes.c_int32
msourcecf_add_noise.argtypes = [msourcecf, ctypes.c_float, ctypes.c_float, ctypes.c_float]
msourcecf_add_modem = liquiddsp.msourcecf_add_modem
msourcecf_add_modem.restype = ctypes.c_int32
msourcecf_add_modem.argtypes = [msourcecf, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_int32, ctypes.c_uint32, ctypes.c_float]
msourcecf_add_fsk = liquiddsp.msourcecf_add_fsk
msourcecf_add_fsk.restype = ctypes.c_int32
msourcecf_add_fsk.argtypes = [msourcecf, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_uint32, ctypes.c_uint32]
msourcecf_add_gmsk = liquiddsp.msourcecf_add_gmsk
msourcecf_add_gmsk.restype = ctypes.c_int32
msourcecf_add_gmsk.argtypes = [msourcecf, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_uint32, ctypes.c_float]
msourcecf_remove = liquiddsp.msourcecf_remove
msourcecf_remove.restype = ctypes.c_int32
msourcecf_remove.argtypes = [msourcecf, ctypes.c_int32]
msourcecf_enable = liquiddsp.msourcecf_enable
msourcecf_enable.restype = ctypes.c_int32
msourcecf_enable.argtypes = [msourcecf, ctypes.c_int32]
msourcecf_disable = liquiddsp.msourcecf_disable
msourcecf_disable.restype = ctypes.c_int32
msourcecf_disable.argtypes = [msourcecf, ctypes.c_int32]
msourcecf_set_gain = liquiddsp.msourcecf_set_gain
msourcecf_set_gain.restype = ctypes.c_int32
msourcecf_set_gain.argtypes = [msourcecf, ctypes.c_int32, ctypes.c_float]
msourcecf_get_gain = liquiddsp.msourcecf_get_gain
msourcecf_get_gain.restype = ctypes.c_int32
msourcecf_get_gain.argtypes = [msourcecf, ctypes.c_int32, ctypes.POINTER(ctypes.c_float)]
msourcecf_get_num_samples = liquiddsp.msourcecf_get_num_samples
msourcecf_get_num_samples.restype = ctypes.c_uint64
msourcecf_get_num_samples.argtypes = [msourcecf]
msourcecf_set_frequency = liquiddsp.msourcecf_set_frequency
msourcecf_set_frequency.restype = ctypes.c_int32
msourcecf_set_frequency.argtypes = [msourcecf, ctypes.c_int32, ctypes.c_float]
msourcecf_get_frequency = liquiddsp.msourcecf_get_frequency
msourcecf_get_frequency.restype = ctypes.c_int32
msourcecf_get_frequency.argtypes = [msourcecf, ctypes.c_int32, ctypes.POINTER(ctypes.c_float)]
msourcecf_write_samples = liquiddsp.msourcecf_write_samples
msourcecf_write_samples.restype = ctypes.c_int32
msourcecf_write_samples.argtypes = [msourcecf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]

# class struct_symtrack_rrrf_s(Structure):
#     pass
#
# symtrack_rrrf = ctypes.POINTER(struct_symtrack_rrrf_s)
# symtrack_rrrf_create = liquiddsp.symtrack_rrrf_create
# symtrack_rrrf_create.restype = symtrack_rrrf
# symtrack_rrrf_create.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_int32]
# symtrack_rrrf_create_default = liquiddsp.symtrack_rrrf_create_default
# symtrack_rrrf_create_default.restype = symtrack_rrrf
# symtrack_rrrf_create_default.argtypes = []
# symtrack_rrrf_destroy = liquiddsp.symtrack_rrrf_destroy
# symtrack_rrrf_destroy.restype = ctypes.c_int32
# symtrack_rrrf_destroy.argtypes = [symtrack_rrrf]
# symtrack_rrrf_print = liquiddsp.symtrack_rrrf_print
# symtrack_rrrf_print.restype = ctypes.c_int32
# symtrack_rrrf_print.argtypes = [symtrack_rrrf]
# symtrack_rrrf_reset = liquiddsp.symtrack_rrrf_reset
# symtrack_rrrf_reset.restype = ctypes.c_int32
# symtrack_rrrf_reset.argtypes = [symtrack_rrrf]
# symtrack_rrrf_set_modscheme = liquiddsp.symtrack_rrrf_set_modscheme
# symtrack_rrrf_set_modscheme.restype = ctypes.c_int32
# symtrack_rrrf_set_modscheme.argtypes = [symtrack_rrrf, ctypes.c_int32]
# symtrack_rrrf_set_bandwidth = liquiddsp.symtrack_rrrf_set_bandwidth
# symtrack_rrrf_set_bandwidth.restype = ctypes.c_int32
# symtrack_rrrf_set_bandwidth.argtypes = [symtrack_rrrf, ctypes.c_float]
# symtrack_rrrf_adjust_phase = liquiddsp.symtrack_rrrf_adjust_phase
# symtrack_rrrf_adjust_phase.restype = ctypes.c_int32
# symtrack_rrrf_adjust_phase.argtypes = [symtrack_rrrf, ctypes.c_float]
# symtrack_rrrf_set_eq_cm = liquiddsp.symtrack_rrrf_set_eq_cm
# symtrack_rrrf_set_eq_cm.restype = ctypes.c_int32
# symtrack_rrrf_set_eq_cm.argtypes = [symtrack_rrrf]
# symtrack_rrrf_set_eq_dd = liquiddsp.symtrack_rrrf_set_eq_dd
# symtrack_rrrf_set_eq_dd.restype = ctypes.c_int32
# symtrack_rrrf_set_eq_dd.argtypes = [symtrack_rrrf]
# symtrack_rrrf_set_eq_off = liquiddsp.symtrack_rrrf_set_eq_off
# symtrack_rrrf_set_eq_off.restype = ctypes.c_int32
# symtrack_rrrf_set_eq_off.argtypes = [symtrack_rrrf]
# symtrack_rrrf_execute = liquiddsp.symtrack_rrrf_execute
# symtrack_rrrf_execute.restype = ctypes.c_int32
# symtrack_rrrf_execute.argtypes = [symtrack_rrrf, ctypes.c_float, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_uint32)]
# symtrack_rrrf_execute_block = liquiddsp.symtrack_rrrf_execute_block
# symtrack_rrrf_execute_block.restype = ctypes.c_int32
# symtrack_rrrf_execute_block.argtypes = [symtrack_rrrf, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_uint32)]

class struct_symtrack_cccf_s(Structure):
    pass

symtrack_cccf = ctypes.POINTER(struct_symtrack_cccf_s)
symtrack_cccf_create = liquiddsp.symtrack_cccf_create
symtrack_cccf_create.restype = symtrack_cccf
symtrack_cccf_create.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_int32]
symtrack_cccf_create_default = liquiddsp.symtrack_cccf_create_default
symtrack_cccf_create_default.restype = symtrack_cccf
symtrack_cccf_create_default.argtypes = []
symtrack_cccf_destroy = liquiddsp.symtrack_cccf_destroy
symtrack_cccf_destroy.restype = ctypes.c_int32
symtrack_cccf_destroy.argtypes = [symtrack_cccf]
symtrack_cccf_print = liquiddsp.symtrack_cccf_print
symtrack_cccf_print.restype = ctypes.c_int32
symtrack_cccf_print.argtypes = [symtrack_cccf]
symtrack_cccf_reset = liquiddsp.symtrack_cccf_reset
symtrack_cccf_reset.restype = ctypes.c_int32
symtrack_cccf_reset.argtypes = [symtrack_cccf]
symtrack_cccf_set_modscheme = liquiddsp.symtrack_cccf_set_modscheme
symtrack_cccf_set_modscheme.restype = ctypes.c_int32
symtrack_cccf_set_modscheme.argtypes = [symtrack_cccf, ctypes.c_int32]
symtrack_cccf_set_bandwidth = liquiddsp.symtrack_cccf_set_bandwidth
symtrack_cccf_set_bandwidth.restype = ctypes.c_int32
symtrack_cccf_set_bandwidth.argtypes = [symtrack_cccf, ctypes.c_float]
symtrack_cccf_adjust_phase = liquiddsp.symtrack_cccf_adjust_phase
symtrack_cccf_adjust_phase.restype = ctypes.c_int32
symtrack_cccf_adjust_phase.argtypes = [symtrack_cccf, ctypes.c_float]
symtrack_cccf_set_eq_cm = liquiddsp.symtrack_cccf_set_eq_cm
symtrack_cccf_set_eq_cm.restype = ctypes.c_int32
symtrack_cccf_set_eq_cm.argtypes = [symtrack_cccf]
symtrack_cccf_set_eq_dd = liquiddsp.symtrack_cccf_set_eq_dd
symtrack_cccf_set_eq_dd.restype = ctypes.c_int32
symtrack_cccf_set_eq_dd.argtypes = [symtrack_cccf]
symtrack_cccf_set_eq_off = liquiddsp.symtrack_cccf_set_eq_off
symtrack_cccf_set_eq_off.restype = ctypes.c_int32
symtrack_cccf_set_eq_off.argtypes = [symtrack_cccf]
symtrack_cccf_execute = liquiddsp.symtrack_cccf_execute
symtrack_cccf_execute.restype = ctypes.c_int32
symtrack_cccf_execute.argtypes = [symtrack_cccf, liquid_float_complex, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(ctypes.c_uint32)]
symtrack_cccf_execute_block = liquiddsp.symtrack_cccf_execute_block
symtrack_cccf_execute_block.restype = ctypes.c_int32
symtrack_cccf_execute_block.argtypes = [symtrack_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(ctypes.c_uint32)]
liquid_lngammaf = liquiddsp.liquid_lngammaf
liquid_lngammaf.restype = ctypes.c_float
liquid_lngammaf.argtypes = [ctypes.c_float]
liquid_gammaf = liquiddsp.liquid_gammaf
liquid_gammaf.restype = ctypes.c_float
liquid_gammaf.argtypes = [ctypes.c_float]
liquid_lnlowergammaf = liquiddsp.liquid_lnlowergammaf
liquid_lnlowergammaf.restype = ctypes.c_float
liquid_lnlowergammaf.argtypes = [ctypes.c_float, ctypes.c_float]
liquid_lnuppergammaf = liquiddsp.liquid_lnuppergammaf
liquid_lnuppergammaf.restype = ctypes.c_float
liquid_lnuppergammaf.argtypes = [ctypes.c_float, ctypes.c_float]
liquid_lowergammaf = liquiddsp.liquid_lowergammaf
liquid_lowergammaf.restype = ctypes.c_float
liquid_lowergammaf.argtypes = [ctypes.c_float, ctypes.c_float]
liquid_uppergammaf = liquiddsp.liquid_uppergammaf
liquid_uppergammaf.restype = ctypes.c_float
liquid_uppergammaf.argtypes = [ctypes.c_float, ctypes.c_float]
liquid_factorialf = liquiddsp.liquid_factorialf
liquid_factorialf.restype = ctypes.c_float
liquid_factorialf.argtypes = [ctypes.c_uint32]
liquid_lnbesselif = liquiddsp.liquid_lnbesselif
liquid_lnbesselif.restype = ctypes.c_float
liquid_lnbesselif.argtypes = [ctypes.c_float, ctypes.c_float]
liquid_besselif = liquiddsp.liquid_besselif
liquid_besselif.restype = ctypes.c_float
liquid_besselif.argtypes = [ctypes.c_float, ctypes.c_float]
liquid_besseli0f = liquiddsp.liquid_besseli0f
liquid_besseli0f.restype = ctypes.c_float
liquid_besseli0f.argtypes = [ctypes.c_float]
liquid_besseljf = liquiddsp.liquid_besseljf
liquid_besseljf.restype = ctypes.c_float
liquid_besseljf.argtypes = [ctypes.c_float, ctypes.c_float]
liquid_besselj0f = liquiddsp.liquid_besselj0f
liquid_besselj0f.restype = ctypes.c_float
liquid_besselj0f.argtypes = [ctypes.c_float]
liquid_Qf = liquiddsp.liquid_Qf
liquid_Qf.restype = ctypes.c_float
liquid_Qf.argtypes = [ctypes.c_float]
liquid_MarcumQf = liquiddsp.liquid_MarcumQf
liquid_MarcumQf.restype = ctypes.c_float
liquid_MarcumQf.argtypes = [ctypes.c_int32, ctypes.c_float, ctypes.c_float]
liquid_MarcumQ1f = liquiddsp.liquid_MarcumQ1f
liquid_MarcumQ1f.restype = ctypes.c_float
liquid_MarcumQ1f.argtypes = [ctypes.c_float, ctypes.c_float]
sincf = liquiddsp.sincf
sincf.restype = ctypes.c_float
sincf.argtypes = [ctypes.c_float]
liquid_nextpow2 = liquiddsp.liquid_nextpow2
liquid_nextpow2.restype = ctypes.c_uint32
liquid_nextpow2.argtypes = [ctypes.c_uint32]
liquid_nchoosek = liquiddsp.liquid_nchoosek
liquid_nchoosek.restype = ctypes.c_float
liquid_nchoosek.argtypes = [ctypes.c_uint32, ctypes.c_uint32]

# values for enumeration 'c__EA_liquid_window_type'
c__EA_liquid_window_type__enumvalues = {
    0: 'LIQUID_WINDOW_UNKNOWN',
    1: 'LIQUID_WINDOW_HAMMING',
    2: 'LIQUID_WINDOW_HANN',
    3: 'LIQUID_WINDOW_BLACKMANHARRIS',
    4: 'LIQUID_WINDOW_BLACKMANHARRIS7',
    5: 'LIQUID_WINDOW_KAISER',
    6: 'LIQUID_WINDOW_FLATTOP',
    7: 'LIQUID_WINDOW_TRIANGULAR',
    8: 'LIQUID_WINDOW_RCOSTAPER',
    9: 'LIQUID_WINDOW_KBD',
}
LIQUID_WINDOW_UNKNOWN = 0
LIQUID_WINDOW_HAMMING = 1
LIQUID_WINDOW_HANN = 2
LIQUID_WINDOW_BLACKMANHARRIS = 3
LIQUID_WINDOW_BLACKMANHARRIS7 = 4
LIQUID_WINDOW_KAISER = 5
LIQUID_WINDOW_FLATTOP = 6
LIQUID_WINDOW_TRIANGULAR = 7
LIQUID_WINDOW_RCOSTAPER = 8
LIQUID_WINDOW_KBD = 9
c__EA_liquid_window_type = ctypes.c_uint32 # enum
liquid_window_type = c__EA_liquid_window_type
liquid_window_type__enumvalues = c__EA_liquid_window_type__enumvalues
liquid_window_str = [] # Variable ctypes.POINTER(ctypes.c_char) * 2 * 10
liquid_print_windows = liquiddsp.liquid_print_windows
liquid_print_windows.restype = None
liquid_print_windows.argtypes = []
liquid_getopt_str2window = liquiddsp.liquid_getopt_str2window
liquid_getopt_str2window.restype = liquid_window_type
liquid_getopt_str2window.argtypes = [ctypes.POINTER(ctypes.c_char)]
liquid_windowf = liquiddsp.liquid_windowf
liquid_windowf.restype = ctypes.c_float
liquid_windowf.argtypes = [liquid_window_type, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float]
liquid_kaiser = liquiddsp.liquid_kaiser
liquid_kaiser.restype = ctypes.c_float
liquid_kaiser.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float]
liquid_hamming = liquiddsp.liquid_hamming
liquid_hamming.restype = ctypes.c_float
liquid_hamming.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
liquid_hann = liquiddsp.liquid_hann
liquid_hann.restype = ctypes.c_float
liquid_hann.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
liquid_blackmanharris = liquiddsp.liquid_blackmanharris
liquid_blackmanharris.restype = ctypes.c_float
liquid_blackmanharris.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
liquid_blackmanharris7 = liquiddsp.liquid_blackmanharris7
liquid_blackmanharris7.restype = ctypes.c_float
liquid_blackmanharris7.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
liquid_flattop = liquiddsp.liquid_flattop
liquid_flattop.restype = ctypes.c_float
liquid_flattop.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
liquid_triangular = liquiddsp.liquid_triangular
liquid_triangular.restype = ctypes.c_float
liquid_triangular.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
liquid_rcostaper_window = liquiddsp.liquid_rcostaper_window
liquid_rcostaper_window.restype = ctypes.c_float
liquid_rcostaper_window.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
liquid_kbd = liquiddsp.liquid_kbd
liquid_kbd.restype = ctypes.c_float
liquid_kbd.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float]
liquid_kbd_window = liquiddsp.liquid_kbd_window
liquid_kbd_window.restype = ctypes.c_int32
liquid_kbd_window.argtypes = [ctypes.c_uint32, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
poly_val = liquiddsp.poly_val
poly_val.restype = ctypes.c_double
poly_val.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.c_double]
poly_fit = liquiddsp.poly_fit
poly_fit.restype = ctypes.c_int32
poly_fit.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.POINTER(ctypes.c_double), ctypes.c_uint32]
poly_fit_lagrange = liquiddsp.poly_fit_lagrange
poly_fit_lagrange.restype = ctypes.c_int32
poly_fit_lagrange.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.POINTER(ctypes.c_double)]
poly_interp_lagrange = liquiddsp.poly_interp_lagrange
poly_interp_lagrange.restype = ctypes.c_double
poly_interp_lagrange.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.c_double]
poly_fit_lagrange_barycentric = liquiddsp.poly_fit_lagrange_barycentric
poly_fit_lagrange_barycentric.restype = ctypes.c_int32
poly_fit_lagrange_barycentric.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.POINTER(ctypes.c_double)]
poly_val_lagrange_barycentric = liquiddsp.poly_val_lagrange_barycentric
poly_val_lagrange_barycentric.restype = ctypes.c_double
poly_val_lagrange_barycentric.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_double, ctypes.c_uint32]
poly_expandbinomial = liquiddsp.poly_expandbinomial
poly_expandbinomial.restype = ctypes.c_int32
poly_expandbinomial.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_double)]
poly_expandbinomial_pm = liquiddsp.poly_expandbinomial_pm
poly_expandbinomial_pm.restype = ctypes.c_int32
poly_expandbinomial_pm.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_double)]
poly_expandroots = liquiddsp.poly_expandroots
poly_expandroots.restype = ctypes.c_int32
poly_expandroots.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.POINTER(ctypes.c_double)]
poly_expandroots2 = liquiddsp.poly_expandroots2
poly_expandroots2.restype = ctypes.c_int32
poly_expandroots2.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.POINTER(ctypes.c_double)]
poly_findroots = liquiddsp.poly_findroots
poly_findroots.restype = ctypes.c_int32
poly_findroots.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_double_complex)]
#poly_findroots_durandkerner = liquiddsp.poly_findroots_durandkerner
#poly_findroots_durandkerner.restype = ctypes.c_int32
#poly_findroots_durandkerner.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_double_complex)]
#poly_findroots_bairstow = liquiddsp.poly_findroots_bairstow
#poly_findroots_bairstow.restype = ctypes.c_int32
#poly_findroots_bairstow.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_double_complex)]
poly_mul = liquiddsp.poly_mul
poly_mul.restype = ctypes.c_int32
poly_mul.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.POINTER(ctypes.c_double)]
polyf_val = liquiddsp.polyf_val
polyf_val.restype = ctypes.c_float
polyf_val.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_float]
polyf_fit = liquiddsp.polyf_fit
polyf_fit.restype = ctypes.c_int32
polyf_fit.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
polyf_fit_lagrange = liquiddsp.polyf_fit_lagrange
polyf_fit_lagrange.restype = ctypes.c_int32
polyf_fit_lagrange.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
polyf_interp_lagrange = liquiddsp.polyf_interp_lagrange
polyf_interp_lagrange.restype = ctypes.c_float
polyf_interp_lagrange.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_float]
polyf_fit_lagrange_barycentric = liquiddsp.polyf_fit_lagrange_barycentric
polyf_fit_lagrange_barycentric.restype = ctypes.c_int32
polyf_fit_lagrange_barycentric.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
polyf_val_lagrange_barycentric = liquiddsp.polyf_val_lagrange_barycentric
polyf_val_lagrange_barycentric.restype = ctypes.c_float
polyf_val_lagrange_barycentric.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_float, ctypes.c_uint32]
polyf_expandbinomial = liquiddsp.polyf_expandbinomial
polyf_expandbinomial.restype = ctypes.c_int32
polyf_expandbinomial.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
polyf_expandbinomial_pm = liquiddsp.polyf_expandbinomial_pm
polyf_expandbinomial_pm.restype = ctypes.c_int32
polyf_expandbinomial_pm.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
polyf_expandroots = liquiddsp.polyf_expandroots
polyf_expandroots.restype = ctypes.c_int32
polyf_expandroots.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
polyf_expandroots2 = liquiddsp.polyf_expandroots2
polyf_expandroots2.restype = ctypes.c_int32
polyf_expandroots2.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
polyf_findroots = liquiddsp.polyf_findroots
polyf_findroots.restype = ctypes.c_int32
polyf_findroots.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
#polyf_findroots_durandkerner = liquiddsp.polyf_findroots_durandkerner
#polyf_findroots_durandkerner.restype = ctypes.c_int32
#polyf_findroots_durandkerner.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
#polyf_findroots_bairstow = liquiddsp.polyf_findroots_bairstow
#polyf_findroots_bairstow.restype = ctypes.c_int32
#polyf_findroots_bairstow.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
polyf_mul = liquiddsp.polyf_mul
polyf_mul.restype = ctypes.c_int32
polyf_mul.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
polyc_val = liquiddsp.polyc_val
polyc_val.restype = liquid_double_complex
polyc_val.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, liquid_double_complex]
polyc_fit = liquiddsp.polyc_fit
polyc_fit.restype = ctypes.c_int32
polyc_fit.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32]
polyc_fit_lagrange = liquiddsp.polyc_fit_lagrange
polyc_fit_lagrange.restype = ctypes.c_int32
polyc_fit_lagrange.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_double_complex)]
polyc_interp_lagrange = liquiddsp.polyc_interp_lagrange
polyc_interp_lagrange.restype = liquid_double_complex
polyc_interp_lagrange.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, liquid_double_complex]
polyc_fit_lagrange_barycentric = liquiddsp.polyc_fit_lagrange_barycentric
polyc_fit_lagrange_barycentric.restype = ctypes.c_int32
polyc_fit_lagrange_barycentric.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_double_complex)]
polyc_val_lagrange_barycentric = liquiddsp.polyc_val_lagrange_barycentric
polyc_val_lagrange_barycentric.restype = liquid_double_complex
polyc_val_lagrange_barycentric.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.POINTER(struct_c__SA_liquid_double_complex), liquid_double_complex, ctypes.c_uint32]
polyc_expandbinomial = liquiddsp.polyc_expandbinomial
polyc_expandbinomial.restype = ctypes.c_int32
polyc_expandbinomial.argtypes = [ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_double_complex)]
polyc_expandbinomial_pm = liquiddsp.polyc_expandbinomial_pm
polyc_expandbinomial_pm.restype = ctypes.c_int32
polyc_expandbinomial_pm.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_double_complex)]
polyc_expandroots = liquiddsp.polyc_expandroots
polyc_expandroots.restype = ctypes.c_int32
polyc_expandroots.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_double_complex)]
polyc_expandroots2 = liquiddsp.polyc_expandroots2
polyc_expandroots2.restype = ctypes.c_int32
polyc_expandroots2.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_double_complex)]
polyc_findroots = liquiddsp.polyc_findroots
polyc_findroots.restype = ctypes.c_int32
polyc_findroots.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_double_complex)]
#polyc_findroots_durandkerner = liquiddsp.polyc_findroots_durandkerner
#polyc_findroots_durandkerner.restype = ctypes.c_int32
#polyc_findroots_durandkerner.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_double_complex)]
#polyc_findroots_bairstow = liquiddsp.polyc_findroots_bairstow
#polyc_findroots_bairstow.restype = ctypes.c_int32
#polyc_findroots_bairstow.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_double_complex)]
polyc_mul = liquiddsp.polyc_mul
polyc_mul.restype = ctypes.c_int32
polyc_mul.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_double_complex)]
polycf_val = liquiddsp.polycf_val
polycf_val.restype = liquid_float_complex
polycf_val.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, liquid_float_complex]
polycf_fit = liquiddsp.polycf_fit
polycf_fit.restype = ctypes.c_int32
polycf_fit.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
polycf_fit_lagrange = liquiddsp.polycf_fit_lagrange
polycf_fit_lagrange.restype = ctypes.c_int32
polycf_fit_lagrange.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
polycf_interp_lagrange = liquiddsp.polycf_interp_lagrange
polycf_interp_lagrange.restype = liquid_float_complex
polycf_interp_lagrange.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, liquid_float_complex]
polycf_fit_lagrange_barycentric = liquiddsp.polycf_fit_lagrange_barycentric
polycf_fit_lagrange_barycentric.restype = ctypes.c_int32
polycf_fit_lagrange_barycentric.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
polycf_val_lagrange_barycentric = liquiddsp.polycf_val_lagrange_barycentric
polycf_val_lagrange_barycentric.restype = liquid_float_complex
polycf_val_lagrange_barycentric.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), liquid_float_complex, ctypes.c_uint32]
polycf_expandbinomial = liquiddsp.polycf_expandbinomial
polycf_expandbinomial.restype = ctypes.c_int32
polycf_expandbinomial.argtypes = [ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
polycf_expandbinomial_pm = liquiddsp.polycf_expandbinomial_pm
polycf_expandbinomial_pm.restype = ctypes.c_int32
polycf_expandbinomial_pm.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
polycf_expandroots = liquiddsp.polycf_expandroots
polycf_expandroots.restype = ctypes.c_int32
polycf_expandroots.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
polycf_expandroots2 = liquiddsp.polycf_expandroots2
polycf_expandroots2.restype = ctypes.c_int32
polycf_expandroots2.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
polycf_findroots = liquiddsp.polycf_findroots
polycf_findroots.restype = ctypes.c_int32
polycf_findroots.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
#polycf_findroots_durandkerner = liquiddsp.polycf_findroots_durandkerner
#polycf_findroots_durandkerner.restype = ctypes.c_int32
#polycf_findroots_durandkerner.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
#polycf_findroots_bairstow = liquiddsp.polycf_findroots_bairstow
#polycf_findroots_bairstow.restype = ctypes.c_int32
#polycf_findroots_bairstow.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
polycf_mul = liquiddsp.polycf_mul
polycf_mul.restype = ctypes.c_int32
polycf_mul.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
liquid_is_prime = liquiddsp.liquid_is_prime
liquid_is_prime.restype = ctypes.c_int32
liquid_is_prime.argtypes = [ctypes.c_uint32]
liquid_factor = liquiddsp.liquid_factor
liquid_factor.restype = ctypes.c_int32
liquid_factor.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32)]
liquid_unique_factor = liquiddsp.liquid_unique_factor
liquid_unique_factor.restype = ctypes.c_int32
liquid_unique_factor.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32)]
liquid_gcd = liquiddsp.liquid_gcd
liquid_gcd.restype = ctypes.c_uint32
liquid_gcd.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
liquid_modpow = liquiddsp.liquid_modpow
liquid_modpow.restype = ctypes.c_uint32
liquid_modpow.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
liquid_primitive_root = liquiddsp.liquid_primitive_root
liquid_primitive_root.restype = ctypes.c_uint32
liquid_primitive_root.argtypes = [ctypes.c_uint32]
liquid_primitive_root_prime = liquiddsp.liquid_primitive_root_prime
liquid_primitive_root_prime.restype = ctypes.c_uint32
liquid_primitive_root_prime.argtypes = [ctypes.c_uint32]
liquid_totient = liquiddsp.liquid_totient
liquid_totient.restype = ctypes.c_uint32
liquid_totient.argtypes = [ctypes.c_uint32]
matrixf_print = liquiddsp.matrixf_print
matrixf_print.restype = ctypes.c_int32
matrixf_print.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32]
matrixf_add = liquiddsp.matrixf_add
matrixf_add.restype = ctypes.c_int32
matrixf_add.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32]
matrixf_sub = liquiddsp.matrixf_sub
matrixf_sub.restype = ctypes.c_int32
matrixf_sub.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32]
matrixf_pmul = liquiddsp.matrixf_pmul
matrixf_pmul.restype = ctypes.c_int32
matrixf_pmul.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32]
matrixf_pdiv = liquiddsp.matrixf_pdiv
matrixf_pdiv.restype = ctypes.c_int32
matrixf_pdiv.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32]
matrixf_mul = liquiddsp.matrixf_mul
matrixf_mul.restype = ctypes.c_int32
matrixf_mul.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32]
matrixf_div = liquiddsp.matrixf_div
matrixf_div.restype = ctypes.c_int32
matrixf_div.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
matrixf_det = liquiddsp.matrixf_det
matrixf_det.restype = ctypes.c_float
matrixf_det.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32]
matrixf_trans = liquiddsp.matrixf_trans
matrixf_trans.restype = ctypes.c_int32
matrixf_trans.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32]
matrixf_hermitian = liquiddsp.matrixf_hermitian
matrixf_hermitian.restype = ctypes.c_int32
matrixf_hermitian.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32]
matrixf_mul_transpose = liquiddsp.matrixf_mul_transpose
matrixf_mul_transpose.restype = ctypes.c_int32
matrixf_mul_transpose.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
matrixf_transpose_mul = liquiddsp.matrixf_transpose_mul
matrixf_transpose_mul.restype = ctypes.c_int32
matrixf_transpose_mul.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
matrixf_mul_hermitian = liquiddsp.matrixf_mul_hermitian
matrixf_mul_hermitian.restype = ctypes.c_int32
matrixf_mul_hermitian.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
matrixf_hermitian_mul = liquiddsp.matrixf_hermitian_mul
matrixf_hermitian_mul.restype = ctypes.c_int32
matrixf_hermitian_mul.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
matrixf_aug = liquiddsp.matrixf_aug
matrixf_aug.restype = ctypes.c_int32
matrixf_aug.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32]
matrixf_inv = liquiddsp.matrixf_inv
matrixf_inv.restype = ctypes.c_int32
matrixf_inv.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32]
matrixf_eye = liquiddsp.matrixf_eye
matrixf_eye.restype = ctypes.c_int32
matrixf_eye.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
matrixf_ones = liquiddsp.matrixf_ones
matrixf_ones.restype = ctypes.c_int32
matrixf_ones.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32]
matrixf_zeros = liquiddsp.matrixf_zeros
matrixf_zeros.restype = ctypes.c_int32
matrixf_zeros.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32]
matrixf_gjelim = liquiddsp.matrixf_gjelim
matrixf_gjelim.restype = ctypes.c_int32
matrixf_gjelim.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32]
matrixf_pivot = liquiddsp.matrixf_pivot
matrixf_pivot.restype = ctypes.c_int32
matrixf_pivot.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
matrixf_swaprows = liquiddsp.matrixf_swaprows
matrixf_swaprows.restype = ctypes.c_int32
matrixf_swaprows.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
matrixf_linsolve = liquiddsp.matrixf_linsolve
matrixf_linsolve.restype = ctypes.c_int32
matrixf_linsolve.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(None)]
matrixf_cgsolve = liquiddsp.matrixf_cgsolve
matrixf_cgsolve.restype = ctypes.c_int32
matrixf_cgsolve.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(None)]
matrixf_ludecomp_crout = liquiddsp.matrixf_ludecomp_crout
matrixf_ludecomp_crout.restype = ctypes.c_int32
matrixf_ludecomp_crout.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
matrixf_ludecomp_doolittle = liquiddsp.matrixf_ludecomp_doolittle
matrixf_ludecomp_doolittle.restype = ctypes.c_int32
matrixf_ludecomp_doolittle.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
matrixf_gramschmidt = liquiddsp.matrixf_gramschmidt
matrixf_gramschmidt.restype = ctypes.c_int32
matrixf_gramschmidt.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
matrixf_qrdecomp_gramschmidt = liquiddsp.matrixf_qrdecomp_gramschmidt
matrixf_qrdecomp_gramschmidt.restype = ctypes.c_int32
matrixf_qrdecomp_gramschmidt.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
matrixf_chol = liquiddsp.matrixf_chol
matrixf_chol.restype = ctypes.c_int32
matrixf_chol.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
matrix_print = liquiddsp.matrix_print
matrix_print.restype = ctypes.c_int32
matrix_print.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.c_uint32]
matrix_add = liquiddsp.matrix_add
matrix_add.restype = ctypes.c_int32
matrix_add.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.c_uint32]
matrix_sub = liquiddsp.matrix_sub
matrix_sub.restype = ctypes.c_int32
matrix_sub.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.c_uint32]
matrix_pmul = liquiddsp.matrix_pmul
matrix_pmul.restype = ctypes.c_int32
matrix_pmul.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.c_uint32]
matrix_pdiv = liquiddsp.matrix_pdiv
matrix_pdiv.restype = ctypes.c_int32
matrix_pdiv.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.c_uint32]
matrix_mul = liquiddsp.matrix_mul
matrix_mul.restype = ctypes.c_int32
matrix_mul.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.c_uint32]
matrix_div = liquiddsp.matrix_div
matrix_div.restype = ctypes.c_int32
matrix_div.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_uint32]
matrix_det = liquiddsp.matrix_det
matrix_det.restype = ctypes.c_double
matrix_det.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.c_uint32]
matrix_trans = liquiddsp.matrix_trans
matrix_trans.restype = ctypes.c_int32
matrix_trans.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.c_uint32]
matrix_hermitian = liquiddsp.matrix_hermitian
matrix_hermitian.restype = ctypes.c_int32
matrix_hermitian.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.c_uint32]
matrix_mul_transpose = liquiddsp.matrix_mul_transpose
matrix_mul_transpose.restype = ctypes.c_int32
matrix_mul_transpose.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_double)]
matrix_transpose_mul = liquiddsp.matrix_transpose_mul
matrix_transpose_mul.restype = ctypes.c_int32
matrix_transpose_mul.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_double)]
matrix_mul_hermitian = liquiddsp.matrix_mul_hermitian
matrix_mul_hermitian.restype = ctypes.c_int32
matrix_mul_hermitian.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_double)]
matrix_hermitian_mul = liquiddsp.matrix_hermitian_mul
matrix_hermitian_mul.restype = ctypes.c_int32
matrix_hermitian_mul.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_double)]
matrix_aug = liquiddsp.matrix_aug
matrix_aug.restype = ctypes.c_int32
matrix_aug.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.c_uint32]
matrix_inv = liquiddsp.matrix_inv
matrix_inv.restype = ctypes.c_int32
matrix_inv.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.c_uint32]
matrix_eye = liquiddsp.matrix_eye
matrix_eye.restype = ctypes.c_int32
matrix_eye.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_uint32]
matrix_ones = liquiddsp.matrix_ones
matrix_ones.restype = ctypes.c_int32
matrix_ones.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.c_uint32]
matrix_zeros = liquiddsp.matrix_zeros
matrix_zeros.restype = ctypes.c_int32
matrix_zeros.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.c_uint32]
matrix_gjelim = liquiddsp.matrix_gjelim
matrix_gjelim.restype = ctypes.c_int32
matrix_gjelim.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.c_uint32]
matrix_pivot = liquiddsp.matrix_pivot
matrix_pivot.restype = ctypes.c_int32
matrix_pivot.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
matrix_swaprows = liquiddsp.matrix_swaprows
matrix_swaprows.restype = ctypes.c_int32
matrix_swaprows.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
matrix_linsolve = liquiddsp.matrix_linsolve
matrix_linsolve.restype = ctypes.c_int32
matrix_linsolve.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(None)]
matrix_cgsolve = liquiddsp.matrix_cgsolve
matrix_cgsolve.restype = ctypes.c_int32
matrix_cgsolve.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(None)]
matrix_ludecomp_crout = liquiddsp.matrix_ludecomp_crout
matrix_ludecomp_crout.restype = ctypes.c_int32
matrix_ludecomp_crout.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)]
matrix_ludecomp_doolittle = liquiddsp.matrix_ludecomp_doolittle
matrix_ludecomp_doolittle.restype = ctypes.c_int32
matrix_ludecomp_doolittle.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)]
matrix_gramschmidt = liquiddsp.matrix_gramschmidt
matrix_gramschmidt.restype = ctypes.c_int32
matrix_gramschmidt.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_double)]
matrix_qrdecomp_gramschmidt = liquiddsp.matrix_qrdecomp_gramschmidt
matrix_qrdecomp_gramschmidt.restype = ctypes.c_int32
matrix_qrdecomp_gramschmidt.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)]
matrix_chol = liquiddsp.matrix_chol
matrix_chol.restype = ctypes.c_int32
matrix_chol.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.POINTER(ctypes.c_double)]
matrixcf_print = liquiddsp.matrixcf_print
matrixcf_print.restype = ctypes.c_int32
matrixcf_print.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_uint32]
matrixcf_add = liquiddsp.matrixcf_add
matrixcf_add.restype = ctypes.c_int32
matrixcf_add.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_uint32]
matrixcf_sub = liquiddsp.matrixcf_sub
matrixcf_sub.restype = ctypes.c_int32
matrixcf_sub.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_uint32]
matrixcf_pmul = liquiddsp.matrixcf_pmul
matrixcf_pmul.restype = ctypes.c_int32
matrixcf_pmul.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_uint32]
matrixcf_pdiv = liquiddsp.matrixcf_pdiv
matrixcf_pdiv.restype = ctypes.c_int32
matrixcf_pdiv.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_uint32]
matrixcf_mul = liquiddsp.matrixcf_mul
matrixcf_mul.restype = ctypes.c_int32
matrixcf_mul.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_uint32]
matrixcf_div = liquiddsp.matrixcf_div
matrixcf_div.restype = ctypes.c_int32
matrixcf_div.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
matrixcf_det = liquiddsp.matrixcf_det
matrixcf_det.restype = liquid_float_complex
matrixcf_det.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_uint32]
matrixcf_trans = liquiddsp.matrixcf_trans
matrixcf_trans.restype = ctypes.c_int32
matrixcf_trans.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_uint32]
matrixcf_hermitian = liquiddsp.matrixcf_hermitian
matrixcf_hermitian.restype = ctypes.c_int32
matrixcf_hermitian.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_uint32]
matrixcf_mul_transpose = liquiddsp.matrixcf_mul_transpose
matrixcf_mul_transpose.restype = ctypes.c_int32
matrixcf_mul_transpose.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
matrixcf_transpose_mul = liquiddsp.matrixcf_transpose_mul
matrixcf_transpose_mul.restype = ctypes.c_int32
matrixcf_transpose_mul.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
matrixcf_mul_hermitian = liquiddsp.matrixcf_mul_hermitian
matrixcf_mul_hermitian.restype = ctypes.c_int32
matrixcf_mul_hermitian.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
matrixcf_hermitian_mul = liquiddsp.matrixcf_hermitian_mul
matrixcf_hermitian_mul.restype = ctypes.c_int32
matrixcf_hermitian_mul.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
matrixcf_aug = liquiddsp.matrixcf_aug
matrixcf_aug.restype = ctypes.c_int32
matrixcf_aug.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_uint32]
matrixcf_inv = liquiddsp.matrixcf_inv
matrixcf_inv.restype = ctypes.c_int32
matrixcf_inv.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_uint32]
matrixcf_eye = liquiddsp.matrixcf_eye
matrixcf_eye.restype = ctypes.c_int32
matrixcf_eye.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
matrixcf_ones = liquiddsp.matrixcf_ones
matrixcf_ones.restype = ctypes.c_int32
matrixcf_ones.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_uint32]
matrixcf_zeros = liquiddsp.matrixcf_zeros
matrixcf_zeros.restype = ctypes.c_int32
matrixcf_zeros.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_uint32]
matrixcf_gjelim = liquiddsp.matrixcf_gjelim
matrixcf_gjelim.restype = ctypes.c_int32
matrixcf_gjelim.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_uint32]
matrixcf_pivot = liquiddsp.matrixcf_pivot
matrixcf_pivot.restype = ctypes.c_int32
matrixcf_pivot.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
matrixcf_swaprows = liquiddsp.matrixcf_swaprows
matrixcf_swaprows.restype = ctypes.c_int32
matrixcf_swaprows.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
matrixcf_linsolve = liquiddsp.matrixcf_linsolve
matrixcf_linsolve.restype = ctypes.c_int32
matrixcf_linsolve.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(None)]
matrixcf_cgsolve = liquiddsp.matrixcf_cgsolve
matrixcf_cgsolve.restype = ctypes.c_int32
matrixcf_cgsolve.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(None)]
matrixcf_ludecomp_crout = liquiddsp.matrixcf_ludecomp_crout
matrixcf_ludecomp_crout.restype = ctypes.c_int32
matrixcf_ludecomp_crout.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
matrixcf_ludecomp_doolittle = liquiddsp.matrixcf_ludecomp_doolittle
matrixcf_ludecomp_doolittle.restype = ctypes.c_int32
matrixcf_ludecomp_doolittle.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
matrixcf_gramschmidt = liquiddsp.matrixcf_gramschmidt
matrixcf_gramschmidt.restype = ctypes.c_int32
matrixcf_gramschmidt.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
matrixcf_qrdecomp_gramschmidt = liquiddsp.matrixcf_qrdecomp_gramschmidt
matrixcf_qrdecomp_gramschmidt.restype = ctypes.c_int32
matrixcf_qrdecomp_gramschmidt.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
matrixcf_chol = liquiddsp.matrixcf_chol
matrixcf_chol.restype = ctypes.c_int32
matrixcf_chol.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
matrixc_print = liquiddsp.matrixc_print
matrixc_print.restype = ctypes.c_int32
matrixc_print.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.c_uint32]
matrixc_add = liquiddsp.matrixc_add
matrixc_add.restype = ctypes.c_int32
matrixc_add.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.c_uint32]
matrixc_sub = liquiddsp.matrixc_sub
matrixc_sub.restype = ctypes.c_int32
matrixc_sub.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.c_uint32]
matrixc_pmul = liquiddsp.matrixc_pmul
matrixc_pmul.restype = ctypes.c_int32
matrixc_pmul.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.c_uint32]
matrixc_pdiv = liquiddsp.matrixc_pdiv
matrixc_pdiv.restype = ctypes.c_int32
matrixc_pdiv.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.c_uint32]
matrixc_mul = liquiddsp.matrixc_mul
matrixc_mul.restype = ctypes.c_int32
matrixc_mul.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.c_uint32]
matrixc_div = liquiddsp.matrixc_div
matrixc_div.restype = ctypes.c_int32
matrixc_div.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32]
matrixc_det = liquiddsp.matrixc_det
matrixc_det.restype = liquid_double_complex
matrixc_det.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.c_uint32]
matrixc_trans = liquiddsp.matrixc_trans
matrixc_trans.restype = ctypes.c_int32
matrixc_trans.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.c_uint32]
matrixc_hermitian = liquiddsp.matrixc_hermitian
matrixc_hermitian.restype = ctypes.c_int32
matrixc_hermitian.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.c_uint32]
matrixc_mul_transpose = liquiddsp.matrixc_mul_transpose
matrixc_mul_transpose.restype = ctypes.c_int32
matrixc_mul_transpose.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_double_complex)]
matrixc_transpose_mul = liquiddsp.matrixc_transpose_mul
matrixc_transpose_mul.restype = ctypes.c_int32
matrixc_transpose_mul.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_double_complex)]
matrixc_mul_hermitian = liquiddsp.matrixc_mul_hermitian
matrixc_mul_hermitian.restype = ctypes.c_int32
matrixc_mul_hermitian.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_double_complex)]
matrixc_hermitian_mul = liquiddsp.matrixc_hermitian_mul
matrixc_hermitian_mul.restype = ctypes.c_int32
matrixc_hermitian_mul.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_double_complex)]
matrixc_aug = liquiddsp.matrixc_aug
matrixc_aug.restype = ctypes.c_int32
matrixc_aug.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.c_uint32]
matrixc_inv = liquiddsp.matrixc_inv
matrixc_inv.restype = ctypes.c_int32
matrixc_inv.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.c_uint32]
matrixc_eye = liquiddsp.matrixc_eye
matrixc_eye.restype = ctypes.c_int32
matrixc_eye.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32]
matrixc_ones = liquiddsp.matrixc_ones
matrixc_ones.restype = ctypes.c_int32
matrixc_ones.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.c_uint32]
matrixc_zeros = liquiddsp.matrixc_zeros
matrixc_zeros.restype = ctypes.c_int32
matrixc_zeros.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.c_uint32]
matrixc_gjelim = liquiddsp.matrixc_gjelim
matrixc_gjelim.restype = ctypes.c_int32
matrixc_gjelim.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.c_uint32]
matrixc_pivot = liquiddsp.matrixc_pivot
matrixc_pivot.restype = ctypes.c_int32
matrixc_pivot.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
matrixc_swaprows = liquiddsp.matrixc_swaprows
matrixc_swaprows.restype = ctypes.c_int32
matrixc_swaprows.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
matrixc_linsolve = liquiddsp.matrixc_linsolve
matrixc_linsolve.restype = ctypes.c_int32
matrixc_linsolve.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.POINTER(None)]
matrixc_cgsolve = liquiddsp.matrixc_cgsolve
matrixc_cgsolve.restype = ctypes.c_int32
matrixc_cgsolve.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.POINTER(None)]
matrixc_ludecomp_crout = liquiddsp.matrixc_ludecomp_crout
matrixc_ludecomp_crout.restype = ctypes.c_int32
matrixc_ludecomp_crout.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.POINTER(struct_c__SA_liquid_double_complex)]
matrixc_ludecomp_doolittle = liquiddsp.matrixc_ludecomp_doolittle
matrixc_ludecomp_doolittle.restype = ctypes.c_int32
matrixc_ludecomp_doolittle.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.POINTER(struct_c__SA_liquid_double_complex)]
matrixc_gramschmidt = liquiddsp.matrixc_gramschmidt
matrixc_gramschmidt.restype = ctypes.c_int32
matrixc_gramschmidt.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_double_complex)]
matrixc_qrdecomp_gramschmidt = liquiddsp.matrixc_qrdecomp_gramschmidt
matrixc_qrdecomp_gramschmidt.restype = ctypes.c_int32
matrixc_qrdecomp_gramschmidt.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.POINTER(struct_c__SA_liquid_double_complex)]
matrixc_chol = liquiddsp.matrixc_chol
matrixc_chol.restype = ctypes.c_int32
matrixc_chol.argtypes = [ctypes.POINTER(struct_c__SA_liquid_double_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_double_complex)]
class struct_smatrixb_s(Structure):
    pass

smatrixb = ctypes.POINTER(struct_smatrixb_s)
smatrixb_create = liquiddsp.smatrixb_create
smatrixb_create.restype = smatrixb
smatrixb_create.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
smatrixb_create_array = liquiddsp.smatrixb_create_array
smatrixb_create_array.restype = smatrixb
smatrixb_create_array.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, ctypes.c_uint32]
smatrixb_destroy = liquiddsp.smatrixb_destroy
smatrixb_destroy.restype = ctypes.c_int32
smatrixb_destroy.argtypes = [smatrixb]
smatrixb_print = liquiddsp.smatrixb_print
smatrixb_print.restype = ctypes.c_int32
smatrixb_print.argtypes = [smatrixb]
smatrixb_print_expanded = liquiddsp.smatrixb_print_expanded
smatrixb_print_expanded.restype = ctypes.c_int32
smatrixb_print_expanded.argtypes = [smatrixb]
smatrixb_size = liquiddsp.smatrixb_size
smatrixb_size.restype = ctypes.c_int32
smatrixb_size.argtypes = [smatrixb, ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32)]
smatrixb_clear = liquiddsp.smatrixb_clear
smatrixb_clear.restype = ctypes.c_int32
smatrixb_clear.argtypes = [smatrixb]
smatrixb_reset = liquiddsp.smatrixb_reset
smatrixb_reset.restype = ctypes.c_int32
smatrixb_reset.argtypes = [smatrixb]
smatrixb_isset = liquiddsp.smatrixb_isset
smatrixb_isset.restype = ctypes.c_int32
smatrixb_isset.argtypes = [smatrixb, ctypes.c_uint32, ctypes.c_uint32]
smatrixb_insert = liquiddsp.smatrixb_insert
smatrixb_insert.restype = ctypes.c_int32
smatrixb_insert.argtypes = [smatrixb, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_ubyte]
smatrixb_delete = liquiddsp.smatrixb_delete
smatrixb_delete.restype = ctypes.c_int32
smatrixb_delete.argtypes = [smatrixb, ctypes.c_uint32, ctypes.c_uint32]
smatrixb_set = liquiddsp.smatrixb_set
smatrixb_set.restype = ctypes.c_int32
smatrixb_set.argtypes = [smatrixb, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_ubyte]
smatrixb_get = liquiddsp.smatrixb_get
smatrixb_get.restype = ctypes.c_ubyte
smatrixb_get.argtypes = [smatrixb, ctypes.c_uint32, ctypes.c_uint32]
smatrixb_eye = liquiddsp.smatrixb_eye
smatrixb_eye.restype = ctypes.c_int32
smatrixb_eye.argtypes = [smatrixb]
smatrixb_mul = liquiddsp.smatrixb_mul
smatrixb_mul.restype = ctypes.c_int32
smatrixb_mul.argtypes = [smatrixb, smatrixb, smatrixb]
smatrixb_vmul = liquiddsp.smatrixb_vmul
smatrixb_vmul.restype = ctypes.c_int32
smatrixb_vmul.argtypes = [smatrixb, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte)]
class struct_smatrixf_s(Structure):
    pass

smatrixf = ctypes.POINTER(struct_smatrixf_s)
smatrixf_create = liquiddsp.smatrixf_create
smatrixf_create.restype = smatrixf
smatrixf_create.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
smatrixf_create_array = liquiddsp.smatrixf_create_array
smatrixf_create_array.restype = smatrixf
smatrixf_create_array.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32]
smatrixf_destroy = liquiddsp.smatrixf_destroy
smatrixf_destroy.restype = ctypes.c_int32
smatrixf_destroy.argtypes = [smatrixf]
smatrixf_print = liquiddsp.smatrixf_print
smatrixf_print.restype = ctypes.c_int32
smatrixf_print.argtypes = [smatrixf]
smatrixf_print_expanded = liquiddsp.smatrixf_print_expanded
smatrixf_print_expanded.restype = ctypes.c_int32
smatrixf_print_expanded.argtypes = [smatrixf]
smatrixf_size = liquiddsp.smatrixf_size
smatrixf_size.restype = ctypes.c_int32
smatrixf_size.argtypes = [smatrixf, ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32)]
smatrixf_clear = liquiddsp.smatrixf_clear
smatrixf_clear.restype = ctypes.c_int32
smatrixf_clear.argtypes = [smatrixf]
smatrixf_reset = liquiddsp.smatrixf_reset
smatrixf_reset.restype = ctypes.c_int32
smatrixf_reset.argtypes = [smatrixf]
smatrixf_isset = liquiddsp.smatrixf_isset
smatrixf_isset.restype = ctypes.c_int32
smatrixf_isset.argtypes = [smatrixf, ctypes.c_uint32, ctypes.c_uint32]
smatrixf_insert = liquiddsp.smatrixf_insert
smatrixf_insert.restype = ctypes.c_int32
smatrixf_insert.argtypes = [smatrixf, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float]
smatrixf_delete = liquiddsp.smatrixf_delete
smatrixf_delete.restype = ctypes.c_int32
smatrixf_delete.argtypes = [smatrixf, ctypes.c_uint32, ctypes.c_uint32]
smatrixf_set = liquiddsp.smatrixf_set
smatrixf_set.restype = ctypes.c_int32
smatrixf_set.argtypes = [smatrixf, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float]
smatrixf_get = liquiddsp.smatrixf_get
smatrixf_get.restype = ctypes.c_float
smatrixf_get.argtypes = [smatrixf, ctypes.c_uint32, ctypes.c_uint32]
smatrixf_eye = liquiddsp.smatrixf_eye
smatrixf_eye.restype = ctypes.c_int32
smatrixf_eye.argtypes = [smatrixf]
smatrixf_mul = liquiddsp.smatrixf_mul
smatrixf_mul.restype = ctypes.c_int32
smatrixf_mul.argtypes = [smatrixf, smatrixf, smatrixf]
smatrixf_vmul = liquiddsp.smatrixf_vmul
smatrixf_vmul.restype = ctypes.c_int32
smatrixf_vmul.argtypes = [smatrixf, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
class struct_smatrixi_s(Structure):
    pass

smatrixi = ctypes.POINTER(struct_smatrixi_s)
smatrixi_create = liquiddsp.smatrixi_create
smatrixi_create.restype = smatrixi
smatrixi_create.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
smatrixi_create_array = liquiddsp.smatrixi_create_array
smatrixi_create_array.restype = smatrixi
smatrixi_create_array.argtypes = [ctypes.POINTER(ctypes.c_int16), ctypes.c_uint32, ctypes.c_uint32]
smatrixi_destroy = liquiddsp.smatrixi_destroy
smatrixi_destroy.restype = ctypes.c_int32
smatrixi_destroy.argtypes = [smatrixi]
smatrixi_print = liquiddsp.smatrixi_print
smatrixi_print.restype = ctypes.c_int32
smatrixi_print.argtypes = [smatrixi]
smatrixi_print_expanded = liquiddsp.smatrixi_print_expanded
smatrixi_print_expanded.restype = ctypes.c_int32
smatrixi_print_expanded.argtypes = [smatrixi]
smatrixi_size = liquiddsp.smatrixi_size
smatrixi_size.restype = ctypes.c_int32
smatrixi_size.argtypes = [smatrixi, ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32)]
smatrixi_clear = liquiddsp.smatrixi_clear
smatrixi_clear.restype = ctypes.c_int32
smatrixi_clear.argtypes = [smatrixi]
smatrixi_reset = liquiddsp.smatrixi_reset
smatrixi_reset.restype = ctypes.c_int32
smatrixi_reset.argtypes = [smatrixi]
smatrixi_isset = liquiddsp.smatrixi_isset
smatrixi_isset.restype = ctypes.c_int32
smatrixi_isset.argtypes = [smatrixi, ctypes.c_uint32, ctypes.c_uint32]
smatrixi_insert = liquiddsp.smatrixi_insert
smatrixi_insert.restype = ctypes.c_int32
smatrixi_insert.argtypes = [smatrixi, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_int16]
smatrixi_delete = liquiddsp.smatrixi_delete
smatrixi_delete.restype = ctypes.c_int32
smatrixi_delete.argtypes = [smatrixi, ctypes.c_uint32, ctypes.c_uint32]
smatrixi_set = liquiddsp.smatrixi_set
smatrixi_set.restype = ctypes.c_int32
smatrixi_set.argtypes = [smatrixi, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_int16]
smatrixi_get = liquiddsp.smatrixi_get
smatrixi_get.restype = ctypes.c_int16
smatrixi_get.argtypes = [smatrixi, ctypes.c_uint32, ctypes.c_uint32]
smatrixi_eye = liquiddsp.smatrixi_eye
smatrixi_eye.restype = ctypes.c_int32
smatrixi_eye.argtypes = [smatrixi]
smatrixi_mul = liquiddsp.smatrixi_mul
smatrixi_mul.restype = ctypes.c_int32
smatrixi_mul.argtypes = [smatrixi, smatrixi, smatrixi]
smatrixi_vmul = liquiddsp.smatrixi_vmul
smatrixi_vmul.restype = ctypes.c_int32
smatrixi_vmul.argtypes = [smatrixi, ctypes.POINTER(ctypes.c_int16), ctypes.POINTER(ctypes.c_int16)]
smatrixb_mulf = liquiddsp.smatrixb_mulf
smatrixb_mulf.restype = ctypes.c_int32
smatrixb_mulf.argtypes = [smatrixb, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_uint32]
smatrixb_vmulf = liquiddsp.smatrixb_vmulf
smatrixb_vmulf.restype = ctypes.c_int32
smatrixb_vmulf.argtypes = [smatrixb, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]

# values for enumeration 'c__EA_modulation_scheme'
c__EA_modulation_scheme__enumvalues = {
    0: 'LIQUID_MODEM_UNKNOWN',
    1: 'LIQUID_MODEM_PSK2',
    2: 'LIQUID_MODEM_PSK4',
    3: 'LIQUID_MODEM_PSK8',
    4: 'LIQUID_MODEM_PSK16',
    5: 'LIQUID_MODEM_PSK32',
    6: 'LIQUID_MODEM_PSK64',
    7: 'LIQUID_MODEM_PSK128',
    8: 'LIQUID_MODEM_PSK256',
    9: 'LIQUID_MODEM_DPSK2',
    10: 'LIQUID_MODEM_DPSK4',
    11: 'LIQUID_MODEM_DPSK8',
    12: 'LIQUID_MODEM_DPSK16',
    13: 'LIQUID_MODEM_DPSK32',
    14: 'LIQUID_MODEM_DPSK64',
    15: 'LIQUID_MODEM_DPSK128',
    16: 'LIQUID_MODEM_DPSK256',
    17: 'LIQUID_MODEM_ASK2',
    18: 'LIQUID_MODEM_ASK4',
    19: 'LIQUID_MODEM_ASK8',
    20: 'LIQUID_MODEM_ASK16',
    21: 'LIQUID_MODEM_ASK32',
    22: 'LIQUID_MODEM_ASK64',
    23: 'LIQUID_MODEM_ASK128',
    24: 'LIQUID_MODEM_ASK256',
    25: 'LIQUID_MODEM_QAM4',
    26: 'LIQUID_MODEM_QAM8',
    27: 'LIQUID_MODEM_QAM16',
    28: 'LIQUID_MODEM_QAM32',
    29: 'LIQUID_MODEM_QAM64',
    30: 'LIQUID_MODEM_QAM128',
    31: 'LIQUID_MODEM_QAM256',
    32: 'LIQUID_MODEM_APSK4',
    33: 'LIQUID_MODEM_APSK8',
    34: 'LIQUID_MODEM_APSK16',
    35: 'LIQUID_MODEM_APSK32',
    36: 'LIQUID_MODEM_APSK64',
    37: 'LIQUID_MODEM_APSK128',
    38: 'LIQUID_MODEM_APSK256',
    39: 'LIQUID_MODEM_BPSK',
    40: 'LIQUID_MODEM_QPSK',
    41: 'LIQUID_MODEM_OOK',
    42: 'LIQUID_MODEM_SQAM32',
    43: 'LIQUID_MODEM_SQAM128',
    44: 'LIQUID_MODEM_V29',
    45: 'LIQUID_MODEM_ARB16OPT',
    46: 'LIQUID_MODEM_ARB32OPT',
    47: 'LIQUID_MODEM_ARB64OPT',
    48: 'LIQUID_MODEM_ARB128OPT',
    49: 'LIQUID_MODEM_ARB256OPT',
    50: 'LIQUID_MODEM_ARB64VT',
    51: 'LIQUID_MODEM_ARB',
}
LIQUID_MODEM_UNKNOWN = 0
LIQUID_MODEM_PSK2 = 1
LIQUID_MODEM_PSK4 = 2
LIQUID_MODEM_PSK8 = 3
LIQUID_MODEM_PSK16 = 4
LIQUID_MODEM_PSK32 = 5
LIQUID_MODEM_PSK64 = 6
LIQUID_MODEM_PSK128 = 7
LIQUID_MODEM_PSK256 = 8
LIQUID_MODEM_DPSK2 = 9
LIQUID_MODEM_DPSK4 = 10
LIQUID_MODEM_DPSK8 = 11
LIQUID_MODEM_DPSK16 = 12
LIQUID_MODEM_DPSK32 = 13
LIQUID_MODEM_DPSK64 = 14
LIQUID_MODEM_DPSK128 = 15
LIQUID_MODEM_DPSK256 = 16
LIQUID_MODEM_ASK2 = 17
LIQUID_MODEM_ASK4 = 18
LIQUID_MODEM_ASK8 = 19
LIQUID_MODEM_ASK16 = 20
LIQUID_MODEM_ASK32 = 21
LIQUID_MODEM_ASK64 = 22
LIQUID_MODEM_ASK128 = 23
LIQUID_MODEM_ASK256 = 24
LIQUID_MODEM_QAM4 = 25
LIQUID_MODEM_QAM8 = 26
LIQUID_MODEM_QAM16 = 27
LIQUID_MODEM_QAM32 = 28
LIQUID_MODEM_QAM64 = 29
LIQUID_MODEM_QAM128 = 30
LIQUID_MODEM_QAM256 = 31
LIQUID_MODEM_APSK4 = 32
LIQUID_MODEM_APSK8 = 33
LIQUID_MODEM_APSK16 = 34
LIQUID_MODEM_APSK32 = 35
LIQUID_MODEM_APSK64 = 36
LIQUID_MODEM_APSK128 = 37
LIQUID_MODEM_APSK256 = 38
LIQUID_MODEM_BPSK = 39
LIQUID_MODEM_QPSK = 40
LIQUID_MODEM_OOK = 41
LIQUID_MODEM_SQAM32 = 42
LIQUID_MODEM_SQAM128 = 43
LIQUID_MODEM_V29 = 44
LIQUID_MODEM_ARB16OPT = 45
LIQUID_MODEM_ARB32OPT = 46
LIQUID_MODEM_ARB64OPT = 47
LIQUID_MODEM_ARB128OPT = 48
LIQUID_MODEM_ARB256OPT = 49
LIQUID_MODEM_ARB64VT = 50
LIQUID_MODEM_ARB = 51
c__EA_modulation_scheme = ctypes.c_uint32 # enum
modulation_scheme = c__EA_modulation_scheme
modulation_scheme__enumvalues = c__EA_modulation_scheme__enumvalues
class struct_modulation_type_s(Structure):
    pass

struct_modulation_type_s._pack_ = 1 # source:False
struct_modulation_type_s._fields_ = [
    ('name', ctypes.POINTER(ctypes.c_char)),
    ('fullname', ctypes.POINTER(ctypes.c_char)),
    ('scheme', modulation_scheme),
    ('bps', ctypes.c_uint32),
]

modulation_types = struct_modulation_type_s * 52 # Variable struct_modulation_type_s * 52
liquid_print_modulation_schemes = liquiddsp.liquid_print_modulation_schemes
liquid_print_modulation_schemes.restype = ctypes.c_int32
liquid_print_modulation_schemes.argtypes = []
liquid_getopt_str2mod = liquiddsp.liquid_getopt_str2mod
liquid_getopt_str2mod.restype = modulation_scheme
liquid_getopt_str2mod.argtypes = [ctypes.POINTER(ctypes.c_char)]
liquid_modem_is_psk = liquiddsp.liquid_modem_is_psk
liquid_modem_is_psk.restype = ctypes.c_int32
liquid_modem_is_psk.argtypes = [modulation_scheme]
liquid_modem_is_dpsk = liquiddsp.liquid_modem_is_dpsk
liquid_modem_is_dpsk.restype = ctypes.c_int32
liquid_modem_is_dpsk.argtypes = [modulation_scheme]
liquid_modem_is_ask = liquiddsp.liquid_modem_is_ask
liquid_modem_is_ask.restype = ctypes.c_int32
liquid_modem_is_ask.argtypes = [modulation_scheme]
liquid_modem_is_qam = liquiddsp.liquid_modem_is_qam
liquid_modem_is_qam.restype = ctypes.c_int32
liquid_modem_is_qam.argtypes = [modulation_scheme]
liquid_modem_is_apsk = liquiddsp.liquid_modem_is_apsk
liquid_modem_is_apsk.restype = ctypes.c_int32
liquid_modem_is_apsk.argtypes = [modulation_scheme]
count_bit_errors = liquiddsp.count_bit_errors
count_bit_errors.restype = ctypes.c_uint32
count_bit_errors.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
count_bit_errors_array = liquiddsp.count_bit_errors_array
count_bit_errors_array.restype = ctypes.c_uint32
count_bit_errors_array.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32]
gray_encode = liquiddsp.gray_encode
gray_encode.restype = ctypes.c_uint32
gray_encode.argtypes = [ctypes.c_uint32]
gray_decode = liquiddsp.gray_decode
gray_decode.restype = ctypes.c_uint32
gray_decode.argtypes = [ctypes.c_uint32]
liquid_pack_soft_bits = liquiddsp.liquid_pack_soft_bits
liquid_pack_soft_bits.restype = ctypes.c_int32
liquid_pack_soft_bits.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)]
liquid_unpack_soft_bits = liquiddsp.liquid_unpack_soft_bits
liquid_unpack_soft_bits.restype = ctypes.c_int32
liquid_unpack_soft_bits.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_ubyte)]
class struct_modem_s(Structure):
    pass

modem = ctypes.POINTER(struct_modem_s)
modem_create = liquiddsp.modem_create
modem_create.restype = modem
modem_create.argtypes = [modulation_scheme]
modem_create_arbitrary = liquiddsp.modem_create_arbitrary
modem_create_arbitrary.restype = modem
modem_create_arbitrary.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
modem_recreate = liquiddsp.modem_recreate
modem_recreate.restype = modem
modem_recreate.argtypes = [modem, modulation_scheme]
modem_destroy = liquiddsp.modem_destroy
modem_destroy.restype = ctypes.c_int32
modem_destroy.argtypes = [modem]
modem_print = liquiddsp.modem_print
modem_print.restype = ctypes.c_int32
modem_print.argtypes = [modem]
modem_reset = liquiddsp.modem_reset
modem_reset.restype = ctypes.c_int32
modem_reset.argtypes = [modem]
modem_gen_rand_sym = liquiddsp.modem_gen_rand_sym
modem_gen_rand_sym.restype = ctypes.c_uint32
modem_gen_rand_sym.argtypes = [modem]
modem_get_bps = liquiddsp.modem_get_bps
modem_get_bps.restype = ctypes.c_uint32
modem_get_bps.argtypes = [modem]
modem_get_scheme = liquiddsp.modem_get_scheme
modem_get_scheme.restype = modulation_scheme
modem_get_scheme.argtypes = [modem]
modem_modulate = liquiddsp.modem_modulate
modem_modulate.restype = ctypes.c_int32
modem_modulate.argtypes = [modem, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
modem_demodulate = liquiddsp.modem_demodulate
modem_demodulate.restype = ctypes.c_int32
modem_demodulate.argtypes = [modem, liquid_float_complex, ctypes.POINTER(ctypes.c_uint32)]
modem_demodulate_soft = liquiddsp.modem_demodulate_soft
modem_demodulate_soft.restype = ctypes.c_int32
modem_demodulate_soft.argtypes = [modem, liquid_float_complex, ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_ubyte)]
modem_get_demodulator_sample = liquiddsp.modem_get_demodulator_sample
modem_get_demodulator_sample.restype = ctypes.c_int32
modem_get_demodulator_sample.argtypes = [modem, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
modem_get_demodulator_phase_error = liquiddsp.modem_get_demodulator_phase_error
modem_get_demodulator_phase_error.restype = ctypes.c_float
modem_get_demodulator_phase_error.argtypes = [modem]
modem_get_demodulator_evm = liquiddsp.modem_get_demodulator_evm
modem_get_demodulator_evm.restype = ctypes.c_float
modem_get_demodulator_evm.argtypes = [modem]
class struct_gmskmod_s(Structure):
    pass

gmskmod = ctypes.POINTER(struct_gmskmod_s)
gmskmod_create = liquiddsp.gmskmod_create
gmskmod_create.restype = gmskmod
gmskmod_create.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float]
gmskmod_destroy = liquiddsp.gmskmod_destroy
gmskmod_destroy.restype = ctypes.c_int32
gmskmod_destroy.argtypes = [gmskmod]
gmskmod_print = liquiddsp.gmskmod_print
gmskmod_print.restype = ctypes.c_int32
gmskmod_print.argtypes = [gmskmod]
gmskmod_reset = liquiddsp.gmskmod_reset
gmskmod_reset.restype = ctypes.c_int32
gmskmod_reset.argtypes = [gmskmod]
gmskmod_modulate = liquiddsp.gmskmod_modulate
gmskmod_modulate.restype = ctypes.c_int32
gmskmod_modulate.argtypes = [gmskmod, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
class struct_gmskdem_s(Structure):
    pass

gmskdem = ctypes.POINTER(struct_gmskdem_s)
gmskdem_create = liquiddsp.gmskdem_create
gmskdem_create.restype = gmskdem
gmskdem_create.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float]
gmskdem_destroy = liquiddsp.gmskdem_destroy
gmskdem_destroy.restype = ctypes.c_int32
gmskdem_destroy.argtypes = [gmskdem]
gmskdem_print = liquiddsp.gmskdem_print
gmskdem_print.restype = ctypes.c_int32
gmskdem_print.argtypes = [gmskdem]
gmskdem_reset = liquiddsp.gmskdem_reset
gmskdem_reset.restype = ctypes.c_int32
gmskdem_reset.argtypes = [gmskdem]
gmskdem_set_eq_bw = liquiddsp.gmskdem_set_eq_bw
gmskdem_set_eq_bw.restype = ctypes.c_int32
gmskdem_set_eq_bw.argtypes = [gmskdem, ctypes.c_float]
gmskdem_demodulate = liquiddsp.gmskdem_demodulate
gmskdem_demodulate.restype = ctypes.c_int32
gmskdem_demodulate.argtypes = [gmskdem, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(ctypes.c_uint32)]

# values for enumeration 'c__EA_liquid_cpfsk_filter'
c__EA_liquid_cpfsk_filter__enumvalues = {
    0: 'LIQUID_CPFSK_SQUARE',
    1: 'LIQUID_CPFSK_RCOS_FULL',
    2: 'LIQUID_CPFSK_RCOS_PARTIAL',
    3: 'LIQUID_CPFSK_GMSK',
}
LIQUID_CPFSK_SQUARE = 0
LIQUID_CPFSK_RCOS_FULL = 1
LIQUID_CPFSK_RCOS_PARTIAL = 2
LIQUID_CPFSK_GMSK = 3
c__EA_liquid_cpfsk_filter = ctypes.c_uint32 # enum
liquid_cpfsk_filter = c__EA_liquid_cpfsk_filter
liquid_cpfsk_filter__enumvalues = c__EA_liquid_cpfsk_filter__enumvalues
class struct_cpfskmod_s(Structure):
    pass

cpfskmod = ctypes.POINTER(struct_cpfskmod_s)
cpfskmod_create = liquiddsp.cpfskmod_create
cpfskmod_create.restype = cpfskmod
cpfskmod_create.argtypes = [ctypes.c_uint32, ctypes.c_float, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_int32]
cpfskmod_destroy = liquiddsp.cpfskmod_destroy
cpfskmod_destroy.restype = ctypes.c_int32
cpfskmod_destroy.argtypes = [cpfskmod]
cpfskmod_print = liquiddsp.cpfskmod_print
cpfskmod_print.restype = ctypes.c_int32
cpfskmod_print.argtypes = [cpfskmod]
cpfskmod_reset = liquiddsp.cpfskmod_reset
cpfskmod_reset.restype = ctypes.c_int32
cpfskmod_reset.argtypes = [cpfskmod]
cpfskmod_get_delay = liquiddsp.cpfskmod_get_delay
cpfskmod_get_delay.restype = ctypes.c_uint32
cpfskmod_get_delay.argtypes = [cpfskmod]
cpfskmod_modulate = liquiddsp.cpfskmod_modulate
cpfskmod_modulate.restype = ctypes.c_int32
cpfskmod_modulate.argtypes = [cpfskmod, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
class struct_cpfskdem_s(Structure):
    pass

cpfskdem = ctypes.POINTER(struct_cpfskdem_s)
cpfskdem_create = liquiddsp.cpfskdem_create
cpfskdem_create.restype = cpfskdem
cpfskdem_create.argtypes = [ctypes.c_uint32, ctypes.c_float, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_int32]
cpfskdem_destroy = liquiddsp.cpfskdem_destroy
cpfskdem_destroy.restype = ctypes.c_int32
cpfskdem_destroy.argtypes = [cpfskdem]
cpfskdem_print = liquiddsp.cpfskdem_print
cpfskdem_print.restype = ctypes.c_int32
cpfskdem_print.argtypes = [cpfskdem]
cpfskdem_reset = liquiddsp.cpfskdem_reset
cpfskdem_reset.restype = ctypes.c_int32
cpfskdem_reset.argtypes = [cpfskdem]
cpfskdem_get_delay = liquiddsp.cpfskdem_get_delay
cpfskdem_get_delay.restype = ctypes.c_uint32
cpfskdem_get_delay.argtypes = [cpfskdem]
cpfskdem_demodulate = liquiddsp.cpfskdem_demodulate
cpfskdem_demodulate.restype = ctypes.c_uint32
cpfskdem_demodulate.argtypes = [cpfskdem, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
class struct_fskmod_s(Structure):
    pass

fskmod = ctypes.POINTER(struct_fskmod_s)
fskmod_create = liquiddsp.fskmod_create
fskmod_create.restype = fskmod
fskmod_create.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float]
fskmod_destroy = liquiddsp.fskmod_destroy
fskmod_destroy.restype = ctypes.c_int32
fskmod_destroy.argtypes = [fskmod]
fskmod_print = liquiddsp.fskmod_print
fskmod_print.restype = ctypes.c_int32
fskmod_print.argtypes = [fskmod]
fskmod_reset = liquiddsp.fskmod_reset
fskmod_reset.restype = ctypes.c_int32
fskmod_reset.argtypes = [fskmod]
fskmod_modulate = liquiddsp.fskmod_modulate
fskmod_modulate.restype = ctypes.c_int32
fskmod_modulate.argtypes = [fskmod, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
class struct_fskdem_s(Structure):
    pass

fskdem = ctypes.POINTER(struct_fskdem_s)
fskdem_create = liquiddsp.fskdem_create
fskdem_create.restype = fskdem
fskdem_create.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float]
fskdem_destroy = liquiddsp.fskdem_destroy
fskdem_destroy.restype = ctypes.c_int32
fskdem_destroy.argtypes = [fskdem]
fskdem_print = liquiddsp.fskdem_print
fskdem_print.restype = ctypes.c_int32
fskdem_print.argtypes = [fskdem]
fskdem_reset = liquiddsp.fskdem_reset
fskdem_reset.restype = ctypes.c_int32
fskdem_reset.argtypes = [fskdem]
fskdem_demodulate = liquiddsp.fskdem_demodulate
fskdem_demodulate.restype = ctypes.c_uint32
fskdem_demodulate.argtypes = [fskdem, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
fskdem_get_frequency_error = liquiddsp.fskdem_get_frequency_error
fskdem_get_frequency_error.restype = ctypes.c_float
fskdem_get_frequency_error.argtypes = [fskdem]
fskdem_get_symbol_energy = liquiddsp.fskdem_get_symbol_energy
fskdem_get_symbol_energy.restype = ctypes.c_float
fskdem_get_symbol_energy.argtypes = [fskdem, ctypes.c_uint32, ctypes.c_uint32]
class struct_freqmod_s(Structure):
    pass

freqmod = ctypes.POINTER(struct_freqmod_s)
freqmod_create = liquiddsp.freqmod_create
freqmod_create.restype = freqmod
freqmod_create.argtypes = [ctypes.c_float]
freqmod_destroy = liquiddsp.freqmod_destroy
freqmod_destroy.restype = ctypes.c_int32
freqmod_destroy.argtypes = [freqmod]
freqmod_print = liquiddsp.freqmod_print
freqmod_print.restype = ctypes.c_int32
freqmod_print.argtypes = [freqmod]
freqmod_reset = liquiddsp.freqmod_reset
freqmod_reset.restype = ctypes.c_int32
freqmod_reset.argtypes = [freqmod]
freqmod_modulate = liquiddsp.freqmod_modulate
freqmod_modulate.restype = ctypes.c_int32
freqmod_modulate.argtypes = [freqmod, ctypes.c_float, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
freqmod_modulate_block = liquiddsp.freqmod_modulate_block
freqmod_modulate_block.restype = ctypes.c_int32
freqmod_modulate_block.argtypes = [freqmod, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
class struct_freqdem_s(Structure):
    pass

freqdem = ctypes.POINTER(struct_freqdem_s)
freqdem_create = liquiddsp.freqdem_create
freqdem_create.restype = freqdem
freqdem_create.argtypes = [ctypes.c_float]
freqdem_destroy = liquiddsp.freqdem_destroy
freqdem_destroy.restype = ctypes.c_int32
freqdem_destroy.argtypes = [freqdem]
freqdem_print = liquiddsp.freqdem_print
freqdem_print.restype = ctypes.c_int32
freqdem_print.argtypes = [freqdem]
freqdem_reset = liquiddsp.freqdem_reset
freqdem_reset.restype = ctypes.c_int32
freqdem_reset.argtypes = [freqdem]
freqdem_demodulate = liquiddsp.freqdem_demodulate
freqdem_demodulate.restype = ctypes.c_int32
freqdem_demodulate.argtypes = [freqdem, liquid_float_complex, ctypes.POINTER(ctypes.c_float)]
freqdem_demodulate_block = liquiddsp.freqdem_demodulate_block
freqdem_demodulate_block.restype = ctypes.c_int32
freqdem_demodulate_block.argtypes = [freqdem, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]

# values for enumeration 'c__EA_liquid_ampmodem_type'
c__EA_liquid_ampmodem_type__enumvalues = {
    0: 'LIQUID_AMPMODEM_DSB',
    1: 'LIQUID_AMPMODEM_USB',
    2: 'LIQUID_AMPMODEM_LSB',
}
LIQUID_AMPMODEM_DSB = 0
LIQUID_AMPMODEM_USB = 1
LIQUID_AMPMODEM_LSB = 2
c__EA_liquid_ampmodem_type = ctypes.c_uint32 # enum
liquid_ampmodem_type = c__EA_liquid_ampmodem_type
liquid_ampmodem_type__enumvalues = c__EA_liquid_ampmodem_type__enumvalues
class struct_ampmodem_s(Structure):
    pass

ampmodem = ctypes.POINTER(struct_ampmodem_s)
ampmodem_create = liquiddsp.ampmodem_create
ampmodem_create.restype = ampmodem
ampmodem_create.argtypes = [ctypes.c_float, liquid_ampmodem_type, ctypes.c_int32]
ampmodem_destroy = liquiddsp.ampmodem_destroy
ampmodem_destroy.restype = ctypes.c_int32
ampmodem_destroy.argtypes = [ampmodem]
ampmodem_print = liquiddsp.ampmodem_print
ampmodem_print.restype = ctypes.c_int32
ampmodem_print.argtypes = [ampmodem]
ampmodem_reset = liquiddsp.ampmodem_reset
ampmodem_reset.restype = ctypes.c_int32
ampmodem_reset.argtypes = [ampmodem]
ampmodem_get_delay_mod = liquiddsp.ampmodem_get_delay_mod
ampmodem_get_delay_mod.restype = ctypes.c_uint32
ampmodem_get_delay_mod.argtypes = [ampmodem]
ampmodem_get_delay_demod = liquiddsp.ampmodem_get_delay_demod
ampmodem_get_delay_demod.restype = ctypes.c_uint32
ampmodem_get_delay_demod.argtypes = [ampmodem]
ampmodem_modulate = liquiddsp.ampmodem_modulate
ampmodem_modulate.restype = ctypes.c_int32
ampmodem_modulate.argtypes = [ampmodem, ctypes.c_float, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
ampmodem_modulate_block = liquiddsp.ampmodem_modulate_block
ampmodem_modulate_block.restype = ctypes.c_int32
ampmodem_modulate_block.argtypes = [ampmodem, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
ampmodem_demodulate = liquiddsp.ampmodem_demodulate
ampmodem_demodulate.restype = ctypes.c_int32
ampmodem_demodulate.argtypes = [ampmodem, liquid_float_complex, ctypes.POINTER(ctypes.c_float)]
ampmodem_demodulate_block = liquiddsp.ampmodem_demodulate_block
ampmodem_demodulate_block.restype = ctypes.c_int32
ampmodem_demodulate_block.argtypes = [ampmodem, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
class struct_firpfbch_crcf_s(Structure):
    pass

firpfbch_crcf = ctypes.POINTER(struct_firpfbch_crcf_s)
firpfbch_crcf_create = liquiddsp.firpfbch_crcf_create
firpfbch_crcf_create.restype = firpfbch_crcf
firpfbch_crcf_create.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
firpfbch_crcf_create_kaiser = liquiddsp.firpfbch_crcf_create_kaiser
firpfbch_crcf_create_kaiser.restype = firpfbch_crcf
firpfbch_crcf_create_kaiser.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float]
firpfbch_crcf_create_rnyquist = liquiddsp.firpfbch_crcf_create_rnyquist
firpfbch_crcf_create_rnyquist.restype = firpfbch_crcf
firpfbch_crcf_create_rnyquist.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_int32]
firpfbch_crcf_destroy = liquiddsp.firpfbch_crcf_destroy
firpfbch_crcf_destroy.restype = ctypes.c_int32
firpfbch_crcf_destroy.argtypes = [firpfbch_crcf]
firpfbch_crcf_reset = liquiddsp.firpfbch_crcf_reset
firpfbch_crcf_reset.restype = ctypes.c_int32
firpfbch_crcf_reset.argtypes = [firpfbch_crcf]
firpfbch_crcf_print = liquiddsp.firpfbch_crcf_print
firpfbch_crcf_print.restype = ctypes.c_int32
firpfbch_crcf_print.argtypes = [firpfbch_crcf]
firpfbch_crcf_synthesizer_execute = liquiddsp.firpfbch_crcf_synthesizer_execute
firpfbch_crcf_synthesizer_execute.restype = ctypes.c_int32
firpfbch_crcf_synthesizer_execute.argtypes = [firpfbch_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
firpfbch_crcf_analyzer_execute = liquiddsp.firpfbch_crcf_analyzer_execute
firpfbch_crcf_analyzer_execute.restype = ctypes.c_int32
firpfbch_crcf_analyzer_execute.argtypes = [firpfbch_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
class struct_firpfbch_cccf_s(Structure):
    pass

firpfbch_cccf = ctypes.POINTER(struct_firpfbch_cccf_s)
firpfbch_cccf_create = liquiddsp.firpfbch_cccf_create
firpfbch_cccf_create.restype = firpfbch_cccf
firpfbch_cccf_create.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
firpfbch_cccf_create_kaiser = liquiddsp.firpfbch_cccf_create_kaiser
firpfbch_cccf_create_kaiser.restype = firpfbch_cccf
firpfbch_cccf_create_kaiser.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float]
firpfbch_cccf_create_rnyquist = liquiddsp.firpfbch_cccf_create_rnyquist
firpfbch_cccf_create_rnyquist.restype = firpfbch_cccf
firpfbch_cccf_create_rnyquist.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float, ctypes.c_int32]
firpfbch_cccf_destroy = liquiddsp.firpfbch_cccf_destroy
firpfbch_cccf_destroy.restype = ctypes.c_int32
firpfbch_cccf_destroy.argtypes = [firpfbch_cccf]
firpfbch_cccf_reset = liquiddsp.firpfbch_cccf_reset
firpfbch_cccf_reset.restype = ctypes.c_int32
firpfbch_cccf_reset.argtypes = [firpfbch_cccf]
firpfbch_cccf_print = liquiddsp.firpfbch_cccf_print
firpfbch_cccf_print.restype = ctypes.c_int32
firpfbch_cccf_print.argtypes = [firpfbch_cccf]
firpfbch_cccf_synthesizer_execute = liquiddsp.firpfbch_cccf_synthesizer_execute
firpfbch_cccf_synthesizer_execute.restype = ctypes.c_int32
firpfbch_cccf_synthesizer_execute.argtypes = [firpfbch_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
firpfbch_cccf_analyzer_execute = liquiddsp.firpfbch_cccf_analyzer_execute
firpfbch_cccf_analyzer_execute.restype = ctypes.c_int32
firpfbch_cccf_analyzer_execute.argtypes = [firpfbch_cccf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
class struct_firpfbch2_crcf_s(Structure):
    pass

firpfbch2_crcf = ctypes.POINTER(struct_firpfbch2_crcf_s)
firpfbch2_crcf_create = liquiddsp.firpfbch2_crcf_create
firpfbch2_crcf_create.restype = firpfbch2_crcf
firpfbch2_crcf_create.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
firpfbch2_crcf_create_kaiser = liquiddsp.firpfbch2_crcf_create_kaiser
firpfbch2_crcf_create_kaiser.restype = firpfbch2_crcf
firpfbch2_crcf_create_kaiser.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float]
firpfbch2_crcf_destroy = liquiddsp.firpfbch2_crcf_destroy
firpfbch2_crcf_destroy.restype = ctypes.c_int32
firpfbch2_crcf_destroy.argtypes = [firpfbch2_crcf]
firpfbch2_crcf_reset = liquiddsp.firpfbch2_crcf_reset
firpfbch2_crcf_reset.restype = ctypes.c_int32
firpfbch2_crcf_reset.argtypes = [firpfbch2_crcf]
firpfbch2_crcf_print = liquiddsp.firpfbch2_crcf_print
firpfbch2_crcf_print.restype = ctypes.c_int32
firpfbch2_crcf_print.argtypes = [firpfbch2_crcf]
firpfbch2_crcf_get_type = liquiddsp.firpfbch2_crcf_get_type
firpfbch2_crcf_get_type.restype = ctypes.c_int32
firpfbch2_crcf_get_type.argtypes = [firpfbch2_crcf]
firpfbch2_crcf_get_M = liquiddsp.firpfbch2_crcf_get_M
firpfbch2_crcf_get_M.restype = ctypes.c_uint32
firpfbch2_crcf_get_M.argtypes = [firpfbch2_crcf]
firpfbch2_crcf_get_m = liquiddsp.firpfbch2_crcf_get_m
firpfbch2_crcf_get_m.restype = ctypes.c_uint32
firpfbch2_crcf_get_m.argtypes = [firpfbch2_crcf]
firpfbch2_crcf_execute = liquiddsp.firpfbch2_crcf_execute
firpfbch2_crcf_execute.restype = ctypes.c_int32
firpfbch2_crcf_execute.argtypes = [firpfbch2_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
class struct_firpfbchr_crcf_s(Structure):
    pass

firpfbchr_crcf = ctypes.POINTER(struct_firpfbchr_crcf_s)
firpfbchr_crcf_create = liquiddsp.firpfbchr_crcf_create
firpfbchr_crcf_create.restype = firpfbchr_crcf
firpfbchr_crcf_create.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
firpfbchr_crcf_create_kaiser = liquiddsp.firpfbchr_crcf_create_kaiser
firpfbchr_crcf_create_kaiser.restype = firpfbchr_crcf
firpfbchr_crcf_create_kaiser.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_float]
firpfbchr_crcf_destroy = liquiddsp.firpfbchr_crcf_destroy
firpfbchr_crcf_destroy.restype = ctypes.c_int32
firpfbchr_crcf_destroy.argtypes = [firpfbchr_crcf]
firpfbchr_crcf_reset = liquiddsp.firpfbchr_crcf_reset
firpfbchr_crcf_reset.restype = ctypes.c_int32
firpfbchr_crcf_reset.argtypes = [firpfbchr_crcf]
firpfbchr_crcf_print = liquiddsp.firpfbchr_crcf_print
firpfbchr_crcf_print.restype = ctypes.c_int32
firpfbchr_crcf_print.argtypes = [firpfbchr_crcf]
firpfbchr_crcf_get_M = liquiddsp.firpfbchr_crcf_get_M
firpfbchr_crcf_get_M.restype = ctypes.c_uint32
firpfbchr_crcf_get_M.argtypes = [firpfbchr_crcf]
firpfbchr_crcf_get_P = liquiddsp.firpfbchr_crcf_get_P
firpfbchr_crcf_get_P.restype = ctypes.c_uint32
firpfbchr_crcf_get_P.argtypes = [firpfbchr_crcf]
firpfbchr_crcf_get_m = liquiddsp.firpfbchr_crcf_get_m
firpfbchr_crcf_get_m.restype = ctypes.c_uint32
firpfbchr_crcf_get_m.argtypes = [firpfbchr_crcf]
firpfbchr_crcf_push = liquiddsp.firpfbchr_crcf_push
firpfbchr_crcf_push.restype = ctypes.c_int32
firpfbchr_crcf_push.argtypes = [firpfbchr_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
firpfbchr_crcf_execute = liquiddsp.firpfbchr_crcf_execute
firpfbchr_crcf_execute.restype = ctypes.c_int32
firpfbchr_crcf_execute.argtypes = [firpfbchr_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
ofdmframe_init_default_sctype = liquiddsp.ofdmframe_init_default_sctype
ofdmframe_init_default_sctype.restype = ctypes.c_int32
ofdmframe_init_default_sctype.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_ubyte)]
ofdmframe_init_sctype_range = liquiddsp.ofdmframe_init_sctype_range
ofdmframe_init_sctype_range.restype = ctypes.c_int32
ofdmframe_init_sctype_range.argtypes = [ctypes.c_uint32, ctypes.c_float, ctypes.c_float, ctypes.POINTER(ctypes.c_ubyte)]
ofdmframe_validate_sctype = liquiddsp.ofdmframe_validate_sctype
ofdmframe_validate_sctype.restype = ctypes.c_int32
ofdmframe_validate_sctype.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32)]
ofdmframe_print_sctype = liquiddsp.ofdmframe_print_sctype
ofdmframe_print_sctype.restype = ctypes.c_int32
ofdmframe_print_sctype.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32]
class struct_ofdmframegen_s(Structure):
    pass

ofdmframegen = ctypes.POINTER(struct_ofdmframegen_s)
ofdmframegen_create = liquiddsp.ofdmframegen_create
ofdmframegen_create.restype = ofdmframegen
ofdmframegen_create.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_ubyte)]
ofdmframegen_destroy = liquiddsp.ofdmframegen_destroy
ofdmframegen_destroy.restype = ctypes.c_int32
ofdmframegen_destroy.argtypes = [ofdmframegen]
ofdmframegen_print = liquiddsp.ofdmframegen_print
ofdmframegen_print.restype = ctypes.c_int32
ofdmframegen_print.argtypes = [ofdmframegen]
ofdmframegen_reset = liquiddsp.ofdmframegen_reset
ofdmframegen_reset.restype = ctypes.c_int32
ofdmframegen_reset.argtypes = [ofdmframegen]
ofdmframegen_write_S0a = liquiddsp.ofdmframegen_write_S0a
ofdmframegen_write_S0a.restype = ctypes.c_int32
ofdmframegen_write_S0a.argtypes = [ofdmframegen, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
ofdmframegen_write_S0b = liquiddsp.ofdmframegen_write_S0b
ofdmframegen_write_S0b.restype = ctypes.c_int32
ofdmframegen_write_S0b.argtypes = [ofdmframegen, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
ofdmframegen_write_S1 = liquiddsp.ofdmframegen_write_S1
ofdmframegen_write_S1.restype = ctypes.c_int32
ofdmframegen_write_S1.argtypes = [ofdmframegen, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
ofdmframegen_writesymbol = liquiddsp.ofdmframegen_writesymbol
ofdmframegen_writesymbol.restype = ctypes.c_int32
ofdmframegen_writesymbol.argtypes = [ofdmframegen, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
ofdmframegen_writetail = liquiddsp.ofdmframegen_writetail
ofdmframegen_writetail.restype = ctypes.c_int32
ofdmframegen_writetail.argtypes = [ofdmframegen, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
ofdmframesync_callback = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, ctypes.POINTER(None))
class struct_ofdmframesync_s(Structure):
    pass

ofdmframesync = ctypes.POINTER(struct_ofdmframesync_s)
ofdmframesync_create = liquiddsp.ofdmframesync_create
ofdmframesync_create.restype = ofdmframesync
ofdmframesync_create.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_ubyte), ofdmframesync_callback, ctypes.POINTER(None)]
ofdmframesync_destroy = liquiddsp.ofdmframesync_destroy
ofdmframesync_destroy.restype = ctypes.c_int32
ofdmframesync_destroy.argtypes = [ofdmframesync]
ofdmframesync_print = liquiddsp.ofdmframesync_print
ofdmframesync_print.restype = ctypes.c_int32
ofdmframesync_print.argtypes = [ofdmframesync]
ofdmframesync_reset = liquiddsp.ofdmframesync_reset
ofdmframesync_reset.restype = ctypes.c_int32
ofdmframesync_reset.argtypes = [ofdmframesync]
ofdmframesync_is_frame_open = liquiddsp.ofdmframesync_is_frame_open
ofdmframesync_is_frame_open.restype = ctypes.c_int32
ofdmframesync_is_frame_open.argtypes = [ofdmframesync]
ofdmframesync_execute = liquiddsp.ofdmframesync_execute
ofdmframesync_execute.restype = ctypes.c_int32
ofdmframesync_execute.argtypes = [ofdmframesync, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
ofdmframesync_get_rssi = liquiddsp.ofdmframesync_get_rssi
ofdmframesync_get_rssi.restype = ctypes.c_float
ofdmframesync_get_rssi.argtypes = [ofdmframesync]
ofdmframesync_get_cfo = liquiddsp.ofdmframesync_get_cfo
ofdmframesync_get_cfo.restype = ctypes.c_float
ofdmframesync_get_cfo.argtypes = [ofdmframesync]
ofdmframesync_set_cfo = liquiddsp.ofdmframesync_set_cfo
ofdmframesync_set_cfo.restype = ctypes.c_int32
ofdmframesync_set_cfo.argtypes = [ofdmframesync, ctypes.c_float]
ofdmframesync_debug_enable = liquiddsp.ofdmframesync_debug_enable
ofdmframesync_debug_enable.restype = ctypes.c_int32
ofdmframesync_debug_enable.argtypes = [ofdmframesync]
ofdmframesync_debug_disable = liquiddsp.ofdmframesync_debug_disable
ofdmframesync_debug_disable.restype = ctypes.c_int32
ofdmframesync_debug_disable.argtypes = [ofdmframesync]
ofdmframesync_debug_print = liquiddsp.ofdmframesync_debug_print
ofdmframesync_debug_print.restype = ctypes.c_int32
ofdmframesync_debug_print.argtypes = [ofdmframesync, ctypes.POINTER(ctypes.c_char)]

# values for enumeration 'c__EA_liquid_ncotype'
c__EA_liquid_ncotype__enumvalues = {
    0: 'LIQUID_NCO',
    1: 'LIQUID_VCO',
}
LIQUID_NCO = 0
LIQUID_VCO = 1
c__EA_liquid_ncotype = ctypes.c_uint32 # enum
liquid_ncotype = c__EA_liquid_ncotype
liquid_ncotype__enumvalues = c__EA_liquid_ncotype__enumvalues
class struct_nco_crcf_s(Structure):
    pass

nco_crcf = ctypes.POINTER(struct_nco_crcf_s)
nco_crcf_create = liquiddsp.nco_crcf_create
nco_crcf_create.restype = nco_crcf
nco_crcf_create.argtypes = [liquid_ncotype]
nco_crcf_destroy = liquiddsp.nco_crcf_destroy
nco_crcf_destroy.restype = ctypes.c_int32
nco_crcf_destroy.argtypes = [nco_crcf]
nco_crcf_print = liquiddsp.nco_crcf_print
nco_crcf_print.restype = ctypes.c_int32
nco_crcf_print.argtypes = [nco_crcf]
nco_crcf_reset = liquiddsp.nco_crcf_reset
nco_crcf_reset.restype = ctypes.c_int32
nco_crcf_reset.argtypes = [nco_crcf]
nco_crcf_get_frequency = liquiddsp.nco_crcf_get_frequency
nco_crcf_get_frequency.restype = ctypes.c_float
nco_crcf_get_frequency.argtypes = [nco_crcf]
nco_crcf_set_frequency = liquiddsp.nco_crcf_set_frequency
nco_crcf_set_frequency.restype = ctypes.c_int32
nco_crcf_set_frequency.argtypes = [nco_crcf, ctypes.c_float]
nco_crcf_adjust_frequency = liquiddsp.nco_crcf_adjust_frequency
nco_crcf_adjust_frequency.restype = ctypes.c_int32
nco_crcf_adjust_frequency.argtypes = [nco_crcf, ctypes.c_float]
nco_crcf_get_phase = liquiddsp.nco_crcf_get_phase
nco_crcf_get_phase.restype = ctypes.c_float
nco_crcf_get_phase.argtypes = [nco_crcf]
nco_crcf_set_phase = liquiddsp.nco_crcf_set_phase
nco_crcf_set_phase.restype = ctypes.c_int32
nco_crcf_set_phase.argtypes = [nco_crcf, ctypes.c_float]
nco_crcf_adjust_phase = liquiddsp.nco_crcf_adjust_phase
nco_crcf_adjust_phase.restype = ctypes.c_int32
nco_crcf_adjust_phase.argtypes = [nco_crcf, ctypes.c_float]
nco_crcf_step = liquiddsp.nco_crcf_step
nco_crcf_step.restype = ctypes.c_int32
nco_crcf_step.argtypes = [nco_crcf]
nco_crcf_sin = liquiddsp.nco_crcf_sin
nco_crcf_sin.restype = ctypes.c_float
nco_crcf_sin.argtypes = [nco_crcf]
nco_crcf_cos = liquiddsp.nco_crcf_cos
nco_crcf_cos.restype = ctypes.c_float
nco_crcf_cos.argtypes = [nco_crcf]
nco_crcf_sincos = liquiddsp.nco_crcf_sincos
nco_crcf_sincos.restype = ctypes.c_int32
nco_crcf_sincos.argtypes = [nco_crcf, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
nco_crcf_cexpf = liquiddsp.nco_crcf_cexpf
nco_crcf_cexpf.restype = ctypes.c_int32
nco_crcf_cexpf.argtypes = [nco_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
nco_crcf_pll_set_bandwidth = liquiddsp.nco_crcf_pll_set_bandwidth
nco_crcf_pll_set_bandwidth.restype = ctypes.c_int32
nco_crcf_pll_set_bandwidth.argtypes = [nco_crcf, ctypes.c_float]
nco_crcf_pll_step = liquiddsp.nco_crcf_pll_step
nco_crcf_pll_step.restype = ctypes.c_int32
nco_crcf_pll_step.argtypes = [nco_crcf, ctypes.c_float]
nco_crcf_mix_up = liquiddsp.nco_crcf_mix_up
nco_crcf_mix_up.restype = ctypes.c_int32
nco_crcf_mix_up.argtypes = [nco_crcf, liquid_float_complex, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
nco_crcf_mix_down = liquiddsp.nco_crcf_mix_down
nco_crcf_mix_down.restype = ctypes.c_int32
nco_crcf_mix_down.argtypes = [nco_crcf, liquid_float_complex, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
nco_crcf_mix_block_up = liquiddsp.nco_crcf_mix_block_up
nco_crcf_mix_block_up.restype = ctypes.c_int32
nco_crcf_mix_block_up.argtypes = [nco_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
nco_crcf_mix_block_down = liquiddsp.nco_crcf_mix_block_down
nco_crcf_mix_block_down.restype = ctypes.c_int32
nco_crcf_mix_block_down.argtypes = [nco_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
liquid_unwrap_phase = liquiddsp.liquid_unwrap_phase
liquid_unwrap_phase.restype = None
liquid_unwrap_phase.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
liquid_unwrap_phase2 = liquiddsp.liquid_unwrap_phase2
liquid_unwrap_phase2.restype = None
liquid_unwrap_phase2.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
class struct_synth_crcf_s(Structure):
    pass

synth_crcf = ctypes.POINTER(struct_synth_crcf_s)
synth_crcf_create = liquiddsp.synth_crcf_create
synth_crcf_create.restype = synth_crcf
synth_crcf_create.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
synth_crcf_destroy = liquiddsp.synth_crcf_destroy
synth_crcf_destroy.restype = None
synth_crcf_destroy.argtypes = [synth_crcf]
synth_crcf_reset = liquiddsp.synth_crcf_reset
synth_crcf_reset.restype = None
synth_crcf_reset.argtypes = [synth_crcf]
synth_crcf_get_frequency = liquiddsp.synth_crcf_get_frequency
synth_crcf_get_frequency.restype = ctypes.c_float
synth_crcf_get_frequency.argtypes = [synth_crcf]
synth_crcf_set_frequency = liquiddsp.synth_crcf_set_frequency
synth_crcf_set_frequency.restype = None
synth_crcf_set_frequency.argtypes = [synth_crcf, ctypes.c_float]
synth_crcf_adjust_frequency = liquiddsp.synth_crcf_adjust_frequency
synth_crcf_adjust_frequency.restype = None
synth_crcf_adjust_frequency.argtypes = [synth_crcf, ctypes.c_float]
synth_crcf_get_phase = liquiddsp.synth_crcf_get_phase
synth_crcf_get_phase.restype = ctypes.c_float
synth_crcf_get_phase.argtypes = [synth_crcf]
synth_crcf_set_phase = liquiddsp.synth_crcf_set_phase
synth_crcf_set_phase.restype = None
synth_crcf_set_phase.argtypes = [synth_crcf, ctypes.c_float]
synth_crcf_adjust_phase = liquiddsp.synth_crcf_adjust_phase
synth_crcf_adjust_phase.restype = None
synth_crcf_adjust_phase.argtypes = [synth_crcf, ctypes.c_float]
synth_crcf_get_length = liquiddsp.synth_crcf_get_length
synth_crcf_get_length.restype = ctypes.c_uint32
synth_crcf_get_length.argtypes = [synth_crcf]
synth_crcf_get_current = liquiddsp.synth_crcf_get_current
synth_crcf_get_current.restype = liquid_float_complex
synth_crcf_get_current.argtypes = [synth_crcf]
synth_crcf_get_half_previous = liquiddsp.synth_crcf_get_half_previous
synth_crcf_get_half_previous.restype = liquid_float_complex
synth_crcf_get_half_previous.argtypes = [synth_crcf]
synth_crcf_get_half_next = liquiddsp.synth_crcf_get_half_next
synth_crcf_get_half_next.restype = liquid_float_complex
synth_crcf_get_half_next.argtypes = [synth_crcf]
synth_crcf_step = liquiddsp.synth_crcf_step
synth_crcf_step.restype = None
synth_crcf_step.argtypes = [synth_crcf]
synth_crcf_pll_set_bandwidth = liquiddsp.synth_crcf_pll_set_bandwidth
synth_crcf_pll_set_bandwidth.restype = None
synth_crcf_pll_set_bandwidth.argtypes = [synth_crcf, ctypes.c_float]
synth_crcf_pll_step = liquiddsp.synth_crcf_pll_step
synth_crcf_pll_step.restype = None
synth_crcf_pll_step.argtypes = [synth_crcf, ctypes.c_float]
synth_crcf_mix_up = liquiddsp.synth_crcf_mix_up
synth_crcf_mix_up.restype = None
synth_crcf_mix_up.argtypes = [synth_crcf, liquid_float_complex, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
synth_crcf_mix_down = liquiddsp.synth_crcf_mix_down
synth_crcf_mix_down.restype = None
synth_crcf_mix_down.argtypes = [synth_crcf, liquid_float_complex, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
synth_crcf_mix_block_up = liquiddsp.synth_crcf_mix_block_up
synth_crcf_mix_block_up.restype = None
synth_crcf_mix_block_up.argtypes = [synth_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
synth_crcf_mix_block_down = liquiddsp.synth_crcf_mix_block_down
synth_crcf_mix_block_down.restype = None
synth_crcf_mix_block_down.argtypes = [synth_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
synth_crcf_spread = liquiddsp.synth_crcf_spread
synth_crcf_spread.restype = None
synth_crcf_spread.argtypes = [synth_crcf, liquid_float_complex, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
synth_crcf_despread = liquiddsp.synth_crcf_despread
synth_crcf_despread.restype = None
synth_crcf_despread.argtypes = [synth_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
synth_crcf_despread_triple = liquiddsp.synth_crcf_despread_triple
synth_crcf_despread_triple.restype = None
synth_crcf_despread_triple.argtypes = [synth_crcf, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex)]
utility_function = ctypes.CFUNCTYPE(ctypes.c_float, ctypes.POINTER(None), ctypes.POINTER(ctypes.c_float), ctypes.c_uint32)
liquid_rosenbrock = liquiddsp.liquid_rosenbrock
liquid_rosenbrock.restype = ctypes.c_float
liquid_rosenbrock.argtypes = [ctypes.POINTER(None), ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
liquid_invgauss = liquiddsp.liquid_invgauss
liquid_invgauss.restype = ctypes.c_float
liquid_invgauss.argtypes = [ctypes.POINTER(None), ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
liquid_multimodal = liquiddsp.liquid_multimodal
liquid_multimodal.restype = ctypes.c_float
liquid_multimodal.argtypes = [ctypes.POINTER(None), ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
liquid_spiral = liquiddsp.liquid_spiral
liquid_spiral.restype = ctypes.c_float
liquid_spiral.argtypes = [ctypes.POINTER(None), ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
class struct_gradsearch_s(Structure):
    pass

gradsearch = ctypes.POINTER(struct_gradsearch_s)
gradsearch_create = liquiddsp.gradsearch_create
gradsearch_create.restype = gradsearch
gradsearch_create.argtypes = [ctypes.POINTER(None), ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, utility_function, ctypes.c_int32]
gradsearch_destroy = liquiddsp.gradsearch_destroy
gradsearch_destroy.restype = None
gradsearch_destroy.argtypes = [gradsearch]
gradsearch_print = liquiddsp.gradsearch_print
gradsearch_print.restype = None
gradsearch_print.argtypes = [gradsearch]
gradsearch_step = liquiddsp.gradsearch_step
gradsearch_step.restype = ctypes.c_float
gradsearch_step.argtypes = [gradsearch]
gradsearch_execute = liquiddsp.gradsearch_execute
gradsearch_execute.restype = ctypes.c_float
gradsearch_execute.argtypes = [gradsearch, ctypes.c_uint32, ctypes.c_float]
# class struct_qnsearch_s(Structure):
#     pass
#
# qnsearch = ctypes.POINTER(struct_qnsearch_s)
# qnsearch_create = liquiddsp.qnsearch_create
# qnsearch_create.restype = qnsearch
# qnsearch_create.argtypes = [ctypes.POINTER(None), ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, utility_function, ctypes.c_int32]
# qnsearch_destroy = liquiddsp.qnsearch_destroy
# qnsearch_destroy.restype = ctypes.c_int32
# qnsearch_destroy.argtypes = [qnsearch]
# qnsearch_print = liquiddsp.qnsearch_print
# qnsearch_print.restype = ctypes.c_int32
# qnsearch_print.argtypes = [qnsearch]
# qnsearch_reset = liquiddsp.qnsearch_reset
# qnsearch_reset.restype = ctypes.c_int32
# qnsearch_reset.argtypes = [qnsearch]
# qnsearch_step = liquiddsp.qnsearch_step
# qnsearch_step.restype = ctypes.c_int32
# qnsearch_step.argtypes = [qnsearch]
# qnsearch_execute = liquiddsp.qnsearch_execute
# qnsearch_execute.restype = ctypes.c_float
# qnsearch_execute.argtypes = [qnsearch, ctypes.c_uint32, ctypes.c_float]

class struct_chromosome_s(Structure):
    pass

chromosome = ctypes.POINTER(struct_chromosome_s)
chromosome_create = liquiddsp.chromosome_create
chromosome_create.restype = chromosome
chromosome_create.argtypes = [ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32]
chromosome_create_basic = liquiddsp.chromosome_create_basic
chromosome_create_basic.restype = chromosome
chromosome_create_basic.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
chromosome_create_clone = liquiddsp.chromosome_create_clone
chromosome_create_clone.restype = chromosome
chromosome_create_clone.argtypes = [chromosome]
chromosome_copy = liquiddsp.chromosome_copy
chromosome_copy.restype = ctypes.c_int32
chromosome_copy.argtypes = [chromosome, chromosome]
chromosome_destroy = liquiddsp.chromosome_destroy
chromosome_destroy.restype = ctypes.c_int32
chromosome_destroy.argtypes = [chromosome]
chromosome_get_num_traits = liquiddsp.chromosome_get_num_traits
chromosome_get_num_traits.restype = ctypes.c_uint32
chromosome_get_num_traits.argtypes = [chromosome]
chromosome_print = liquiddsp.chromosome_print
chromosome_print.restype = ctypes.c_int32
chromosome_print.argtypes = [chromosome]
chromosome_printf = liquiddsp.chromosome_printf
chromosome_printf.restype = ctypes.c_int32
chromosome_printf.argtypes = [chromosome]
chromosome_reset = liquiddsp.chromosome_reset
chromosome_reset.restype = ctypes.c_int32
chromosome_reset.argtypes = [chromosome]
chromosome_init = liquiddsp.chromosome_init
chromosome_init.restype = ctypes.c_int32
chromosome_init.argtypes = [chromosome, ctypes.POINTER(ctypes.c_uint32)]
chromosome_initf = liquiddsp.chromosome_initf
chromosome_initf.restype = ctypes.c_int32
chromosome_initf.argtypes = [chromosome, ctypes.POINTER(ctypes.c_float)]
chromosome_mutate = liquiddsp.chromosome_mutate
chromosome_mutate.restype = ctypes.c_int32
chromosome_mutate.argtypes = [chromosome, ctypes.c_uint32]
chromosome_crossover = liquiddsp.chromosome_crossover
chromosome_crossover.restype = ctypes.c_int32
chromosome_crossover.argtypes = [chromosome, chromosome, chromosome, ctypes.c_uint32]
chromosome_init_random = liquiddsp.chromosome_init_random
chromosome_init_random.restype = ctypes.c_int32
chromosome_init_random.argtypes = [chromosome]
chromosome_value = liquiddsp.chromosome_value
chromosome_value.restype = ctypes.c_uint32
chromosome_value.argtypes = [chromosome, ctypes.c_uint32]
chromosome_valuef = liquiddsp.chromosome_valuef
chromosome_valuef.restype = ctypes.c_float
chromosome_valuef.argtypes = [chromosome, ctypes.c_uint32]
class struct_gasearch_s(Structure):
    pass

gasearch = ctypes.POINTER(struct_gasearch_s)
gasearch_utility = ctypes.CFUNCTYPE(ctypes.c_float, ctypes.POINTER(None), ctypes.POINTER(struct_chromosome_s))
gasearch_create = liquiddsp.gasearch_create
gasearch_create.restype = gasearch
gasearch_create.argtypes = [gasearch_utility, ctypes.POINTER(None), chromosome, ctypes.c_int32]
gasearch_create_advanced = liquiddsp.gasearch_create_advanced
gasearch_create_advanced.restype = gasearch
gasearch_create_advanced.argtypes = [gasearch_utility, ctypes.POINTER(None), chromosome, ctypes.c_int32, ctypes.c_uint32, ctypes.c_float]
gasearch_destroy = liquiddsp.gasearch_destroy
gasearch_destroy.restype = ctypes.c_int32
gasearch_destroy.argtypes = [gasearch]
gasearch_print = liquiddsp.gasearch_print
gasearch_print.restype = ctypes.c_int32
gasearch_print.argtypes = [gasearch]
gasearch_set_mutation_rate = liquiddsp.gasearch_set_mutation_rate
gasearch_set_mutation_rate.restype = ctypes.c_int32
gasearch_set_mutation_rate.argtypes = [gasearch, ctypes.c_float]
gasearch_set_population_size = liquiddsp.gasearch_set_population_size
gasearch_set_population_size.restype = ctypes.c_int32
gasearch_set_population_size.argtypes = [gasearch, ctypes.c_uint32, ctypes.c_uint32]
gasearch_run = liquiddsp.gasearch_run
gasearch_run.restype = ctypes.c_float
gasearch_run.argtypes = [gasearch, ctypes.c_uint32, ctypes.c_float]
gasearch_evolve = liquiddsp.gasearch_evolve
gasearch_evolve.restype = ctypes.c_int32
gasearch_evolve.argtypes = [gasearch]
gasearch_getopt = liquiddsp.gasearch_getopt
gasearch_getopt.restype = ctypes.c_int32
gasearch_getopt.argtypes = [gasearch, chromosome, ctypes.POINTER(ctypes.c_float)]
compress_mulaw = liquiddsp.compress_mulaw
compress_mulaw.restype = ctypes.c_float
compress_mulaw.argtypes = [ctypes.c_float, ctypes.c_float]
expand_mulaw = liquiddsp.expand_mulaw
expand_mulaw.restype = ctypes.c_float
expand_mulaw.argtypes = [ctypes.c_float, ctypes.c_float]
compress_cf_mulaw = liquiddsp.compress_cf_mulaw
compress_cf_mulaw.restype = ctypes.c_int32
compress_cf_mulaw.argtypes = [liquid_float_complex, ctypes.c_float, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
expand_cf_mulaw = liquiddsp.expand_cf_mulaw
expand_cf_mulaw.restype = ctypes.c_int32
expand_cf_mulaw.argtypes = [liquid_float_complex, ctypes.c_float, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
quantize_adc = liquiddsp.quantize_adc
quantize_adc.restype = ctypes.c_uint32
quantize_adc.argtypes = [ctypes.c_float, ctypes.c_uint32]
quantize_dac = liquiddsp.quantize_dac
quantize_dac.restype = ctypes.c_float
quantize_dac.argtypes = [ctypes.c_uint32, ctypes.c_uint32]

# values for enumeration 'c__EA_liquid_compander_type'
c__EA_liquid_compander_type__enumvalues = {
    0: 'LIQUID_COMPANDER_NONE',
    1: 'LIQUID_COMPANDER_LINEAR',
    2: 'LIQUID_COMPANDER_MULAW',
    3: 'LIQUID_COMPANDER_ALAW',
}
LIQUID_COMPANDER_NONE = 0
LIQUID_COMPANDER_LINEAR = 1
LIQUID_COMPANDER_MULAW = 2
LIQUID_COMPANDER_ALAW = 3
c__EA_liquid_compander_type = ctypes.c_uint32 # enum
liquid_compander_type = c__EA_liquid_compander_type
liquid_compander_type__enumvalues = c__EA_liquid_compander_type__enumvalues
class struct_quantizerf_s(Structure):
    pass

quantizerf = ctypes.POINTER(struct_quantizerf_s)
quantizerf_create = liquiddsp.quantizerf_create
quantizerf_create.restype = quantizerf
quantizerf_create.argtypes = [liquid_compander_type, ctypes.c_float, ctypes.c_uint32]
quantizerf_destroy = liquiddsp.quantizerf_destroy
quantizerf_destroy.restype = ctypes.c_int32
quantizerf_destroy.argtypes = [quantizerf]
quantizerf_print = liquiddsp.quantizerf_print
quantizerf_print.restype = ctypes.c_int32
quantizerf_print.argtypes = [quantizerf]
quantizerf_execute_adc = liquiddsp.quantizerf_execute_adc
quantizerf_execute_adc.restype = ctypes.c_int32
quantizerf_execute_adc.argtypes = [quantizerf, ctypes.c_float, ctypes.POINTER(ctypes.c_uint32)]
quantizerf_execute_dac = liquiddsp.quantizerf_execute_dac
quantizerf_execute_dac.restype = ctypes.c_int32
quantizerf_execute_dac.argtypes = [quantizerf, ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
class struct_quantizercf_s(Structure):
    pass

quantizercf = ctypes.POINTER(struct_quantizercf_s)
quantizercf_create = liquiddsp.quantizercf_create
quantizercf_create.restype = quantizercf
quantizercf_create.argtypes = [liquid_compander_type, ctypes.c_float, ctypes.c_uint32]
quantizercf_destroy = liquiddsp.quantizercf_destroy
quantizercf_destroy.restype = ctypes.c_int32
quantizercf_destroy.argtypes = [quantizercf]
quantizercf_print = liquiddsp.quantizercf_print
quantizercf_print.restype = ctypes.c_int32
quantizercf_print.argtypes = [quantizercf]
quantizercf_execute_adc = liquiddsp.quantizercf_execute_adc
quantizercf_execute_adc.restype = ctypes.c_int32
quantizercf_execute_adc.argtypes = [quantizercf, liquid_float_complex, ctypes.POINTER(ctypes.c_uint32)]
quantizercf_execute_dac = liquiddsp.quantizercf_execute_dac
quantizercf_execute_dac.restype = ctypes.c_int32
quantizercf_execute_dac.argtypes = [quantizercf, ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
randf = liquiddsp.randf
randf.restype = ctypes.c_float
randf.argtypes = []
randf_pdf = liquiddsp.randf_pdf
randf_pdf.restype = ctypes.c_float
randf_pdf.argtypes = [ctypes.c_float]
randf_cdf = liquiddsp.randf_cdf
randf_cdf.restype = ctypes.c_float
randf_cdf.argtypes = [ctypes.c_float]
randuf = liquiddsp.randuf
randuf.restype = ctypes.c_float
randuf.argtypes = [ctypes.c_float, ctypes.c_float]
randuf_pdf = liquiddsp.randuf_pdf
randuf_pdf.restype = ctypes.c_float
randuf_pdf.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float]
randuf_cdf = liquiddsp.randuf_cdf
randuf_cdf.restype = ctypes.c_float
randuf_cdf.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float]
randnf = liquiddsp.randnf
randnf.restype = ctypes.c_float
randnf.argtypes = []
awgn = liquiddsp.awgn
awgn.restype = None
awgn.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_float]
crandnf = liquiddsp.crandnf
crandnf.restype = None
crandnf.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex)]
cawgn = liquiddsp.cawgn
cawgn.restype = None
cawgn.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_float]
randnf_pdf = liquiddsp.randnf_pdf
randnf_pdf.restype = ctypes.c_float
randnf_pdf.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float]
randnf_cdf = liquiddsp.randnf_cdf
randnf_cdf.restype = ctypes.c_float
randnf_cdf.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float]
randexpf = liquiddsp.randexpf
randexpf.restype = ctypes.c_float
randexpf.argtypes = [ctypes.c_float]
randexpf_pdf = liquiddsp.randexpf_pdf
randexpf_pdf.restype = ctypes.c_float
randexpf_pdf.argtypes = [ctypes.c_float, ctypes.c_float]
randexpf_cdf = liquiddsp.randexpf_cdf
randexpf_cdf.restype = ctypes.c_float
randexpf_cdf.argtypes = [ctypes.c_float, ctypes.c_float]
randweibf = liquiddsp.randweibf
randweibf.restype = ctypes.c_float
randweibf.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float]
randweibf_pdf = liquiddsp.randweibf_pdf
randweibf_pdf.restype = ctypes.c_float
randweibf_pdf.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
randweibf_cdf = liquiddsp.randweibf_cdf
randweibf_cdf.restype = ctypes.c_float
randweibf_cdf.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
randgammaf = liquiddsp.randgammaf
randgammaf.restype = ctypes.c_float
randgammaf.argtypes = [ctypes.c_float, ctypes.c_float]
randgammaf_pdf = liquiddsp.randgammaf_pdf
randgammaf_pdf.restype = ctypes.c_float
randgammaf_pdf.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float]
randgammaf_cdf = liquiddsp.randgammaf_cdf
randgammaf_cdf.restype = ctypes.c_float
randgammaf_cdf.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float]
randnakmf = liquiddsp.randnakmf
randnakmf.restype = ctypes.c_float
randnakmf.argtypes = [ctypes.c_float, ctypes.c_float]
randnakmf_pdf = liquiddsp.randnakmf_pdf
randnakmf_pdf.restype = ctypes.c_float
randnakmf_pdf.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float]
randnakmf_cdf = liquiddsp.randnakmf_cdf
randnakmf_cdf.restype = ctypes.c_float
randnakmf_cdf.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float]
randricekf = liquiddsp.randricekf
randricekf.restype = ctypes.c_float
randricekf.argtypes = [ctypes.c_float, ctypes.c_float]
randricekf_cdf = liquiddsp.randricekf_cdf
randricekf_cdf.restype = ctypes.c_float
randricekf_cdf.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float]
randricekf_pdf = liquiddsp.randricekf_pdf
randricekf_pdf.restype = ctypes.c_float
randricekf_pdf.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float]
scramble_data = liquiddsp.scramble_data
scramble_data.restype = None
scramble_data.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32]
unscramble_data = liquiddsp.unscramble_data
unscramble_data.restype = None
unscramble_data.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32]
unscramble_data_soft = liquiddsp.unscramble_data_soft
unscramble_data_soft.restype = None
unscramble_data_soft.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32]
class struct_bsequence_s(Structure):
    pass

bsequence = ctypes.POINTER(struct_bsequence_s)
bsequence_create = liquiddsp.bsequence_create
bsequence_create.restype = bsequence
bsequence_create.argtypes = [ctypes.c_uint32]
bsequence_destroy = liquiddsp.bsequence_destroy
bsequence_destroy.restype = ctypes.c_int32
bsequence_destroy.argtypes = [bsequence]
bsequence_reset = liquiddsp.bsequence_reset
bsequence_reset.restype = ctypes.c_int32
bsequence_reset.argtypes = [bsequence]
bsequence_init = liquiddsp.bsequence_init
bsequence_init.restype = ctypes.c_int32
bsequence_init.argtypes = [bsequence, ctypes.POINTER(ctypes.c_ubyte)]
bsequence_print = liquiddsp.bsequence_print
bsequence_print.restype = ctypes.c_int32
bsequence_print.argtypes = [bsequence]
bsequence_push = liquiddsp.bsequence_push
bsequence_push.restype = ctypes.c_int32
bsequence_push.argtypes = [bsequence, ctypes.c_uint32]
bsequence_circshift = liquiddsp.bsequence_circshift
bsequence_circshift.restype = ctypes.c_int32
bsequence_circshift.argtypes = [bsequence]
bsequence_correlate = liquiddsp.bsequence_correlate
bsequence_correlate.restype = ctypes.c_int32
bsequence_correlate.argtypes = [bsequence, bsequence]
bsequence_add = liquiddsp.bsequence_add
bsequence_add.restype = ctypes.c_int32
bsequence_add.argtypes = [bsequence, bsequence, bsequence]
bsequence_mul = liquiddsp.bsequence_mul
bsequence_mul.restype = ctypes.c_int32
bsequence_mul.argtypes = [bsequence, bsequence, bsequence]
bsequence_accumulate = liquiddsp.bsequence_accumulate
bsequence_accumulate.restype = ctypes.c_uint32
bsequence_accumulate.argtypes = [bsequence]
bsequence_get_length = liquiddsp.bsequence_get_length
bsequence_get_length.restype = ctypes.c_uint32
bsequence_get_length.argtypes = [bsequence]
bsequence_index = liquiddsp.bsequence_index
bsequence_index.restype = ctypes.c_uint32
bsequence_index.argtypes = [bsequence, ctypes.c_uint32]
bsequence_create_ccodes = liquiddsp.bsequence_create_ccodes
bsequence_create_ccodes.restype = ctypes.c_int32
bsequence_create_ccodes.argtypes = [bsequence, bsequence]
class struct_msequence_s(Structure):
    pass

msequence = ctypes.POINTER(struct_msequence_s)
msequence_create = liquiddsp.msequence_create
msequence_create.restype = msequence
msequence_create.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
msequence_create_genpoly = liquiddsp.msequence_create_genpoly
msequence_create_genpoly.restype = msequence
msequence_create_genpoly.argtypes = [ctypes.c_uint32]
msequence_create_default = liquiddsp.msequence_create_default
msequence_create_default.restype = msequence
msequence_create_default.argtypes = [ctypes.c_uint32]
msequence_destroy = liquiddsp.msequence_destroy
msequence_destroy.restype = ctypes.c_int32
msequence_destroy.argtypes = [msequence]
msequence_print = liquiddsp.msequence_print
msequence_print.restype = ctypes.c_int32
msequence_print.argtypes = [msequence]
msequence_advance = liquiddsp.msequence_advance
msequence_advance.restype = ctypes.c_uint32
msequence_advance.argtypes = [msequence]
msequence_generate_symbol = liquiddsp.msequence_generate_symbol
msequence_generate_symbol.restype = ctypes.c_uint32
msequence_generate_symbol.argtypes = [msequence, ctypes.c_uint32]
msequence_reset = liquiddsp.msequence_reset
msequence_reset.restype = ctypes.c_int32
msequence_reset.argtypes = [msequence]
bsequence_init_msequence = liquiddsp.bsequence_init_msequence
bsequence_init_msequence.restype = ctypes.c_int32
bsequence_init_msequence.argtypes = [bsequence, msequence]
msequence_get_length = liquiddsp.msequence_get_length
msequence_get_length.restype = ctypes.c_uint32
msequence_get_length.argtypes = [msequence]
msequence_get_state = liquiddsp.msequence_get_state
msequence_get_state.restype = ctypes.c_uint32
msequence_get_state.argtypes = [msequence]
msequence_set_state = liquiddsp.msequence_set_state
msequence_set_state.restype = ctypes.c_int32
msequence_set_state.argtypes = [msequence, ctypes.c_uint32]
liquid_pack_array = liquiddsp.liquid_pack_array
liquid_pack_array.restype = ctypes.c_int32
liquid_pack_array.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_ubyte]
liquid_unpack_array = liquiddsp.liquid_unpack_array
liquid_unpack_array.restype = ctypes.c_int32
liquid_unpack_array.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_ubyte)]
liquid_pack_bytes = liquiddsp.liquid_pack_bytes
liquid_pack_bytes.restype = ctypes.c_int32
liquid_pack_bytes.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)]
liquid_unpack_bytes = liquiddsp.liquid_unpack_bytes
liquid_unpack_bytes.restype = ctypes.c_int32
liquid_unpack_bytes.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)]
liquid_repack_bytes = liquiddsp.liquid_repack_bytes
liquid_repack_bytes.restype = ctypes.c_int32
liquid_repack_bytes.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)]
liquid_lbshift = liquiddsp.liquid_lbshift
liquid_lbshift.restype = ctypes.c_int32
liquid_lbshift.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, ctypes.c_uint32]
liquid_rbshift = liquiddsp.liquid_rbshift
liquid_rbshift.restype = ctypes.c_int32
liquid_rbshift.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, ctypes.c_uint32]
liquid_lbcircshift = liquiddsp.liquid_lbcircshift
liquid_lbcircshift.restype = ctypes.c_int32
liquid_lbcircshift.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, ctypes.c_uint32]
liquid_rbcircshift = liquiddsp.liquid_rbcircshift
liquid_rbcircshift.restype = ctypes.c_int32
liquid_rbcircshift.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, ctypes.c_uint32]
liquid_lshift = liquiddsp.liquid_lshift
liquid_lshift.restype = ctypes.c_int32
liquid_lshift.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, ctypes.c_uint32]
liquid_rshift = liquiddsp.liquid_rshift
liquid_rshift.restype = ctypes.c_int32
liquid_rshift.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, ctypes.c_uint32]
liquid_lcircshift = liquiddsp.liquid_lcircshift
liquid_lcircshift.restype = ctypes.c_int32
liquid_lcircshift.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, ctypes.c_uint32]
liquid_rcircshift = liquiddsp.liquid_rcircshift
liquid_rcircshift.restype = ctypes.c_int32
liquid_rcircshift.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, ctypes.c_uint32]
liquid_count_ones = liquiddsp.liquid_count_ones
liquid_count_ones.restype = ctypes.c_uint32
liquid_count_ones.argtypes = [ctypes.c_uint32]
liquid_count_ones_mod2 = liquiddsp.liquid_count_ones_mod2
liquid_count_ones_mod2.restype = ctypes.c_uint32
liquid_count_ones_mod2.argtypes = [ctypes.c_uint32]
liquid_bdotprod = liquiddsp.liquid_bdotprod
liquid_bdotprod.restype = ctypes.c_uint32
liquid_bdotprod.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
liquid_count_leading_zeros = liquiddsp.liquid_count_leading_zeros
liquid_count_leading_zeros.restype = ctypes.c_uint32
liquid_count_leading_zeros.argtypes = [ctypes.c_uint32]
liquid_msb_index = liquiddsp.liquid_msb_index
liquid_msb_index.restype = ctypes.c_uint32
liquid_msb_index.argtypes = [ctypes.c_uint32]
liquid_print_bitstring = liquiddsp.liquid_print_bitstring
liquid_print_bitstring.restype = ctypes.c_int32
liquid_print_bitstring.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
liquid_reverse_byte = liquiddsp.liquid_reverse_byte
liquid_reverse_byte.restype = ctypes.c_ubyte
liquid_reverse_byte.argtypes = [ctypes.c_ubyte]
liquid_reverse_uint16 = liquiddsp.liquid_reverse_uint16
liquid_reverse_uint16.restype = ctypes.c_uint32
liquid_reverse_uint16.argtypes = [ctypes.c_uint32]
liquid_reverse_uint24 = liquiddsp.liquid_reverse_uint24
liquid_reverse_uint24.restype = ctypes.c_uint32
liquid_reverse_uint24.argtypes = [ctypes.c_uint32]
liquid_reverse_uint32 = liquiddsp.liquid_reverse_uint32
liquid_reverse_uint32.restype = ctypes.c_uint32
liquid_reverse_uint32.argtypes = [ctypes.c_uint32]
liquid_get_scale = liquiddsp.liquid_get_scale
liquid_get_scale.restype = ctypes.c_int32
liquid_get_scale.argtypes = [ctypes.c_float, ctypes.POINTER(ctypes.c_char), ctypes.POINTER(ctypes.c_float)]
#liquid_vectorf_init = liquiddsp.liquid_vectorf_init
#liquid_vectorf_init.restype = None
#liquid_vectorf_init.argtypes = [ctypes.c_float, ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
liquid_vectorf_add = liquiddsp.liquid_vectorf_add
liquid_vectorf_add.restype = None
liquid_vectorf_add.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
liquid_vectorf_addscalar = liquiddsp.liquid_vectorf_addscalar
liquid_vectorf_addscalar.restype = None
liquid_vectorf_addscalar.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
liquid_vectorf_mul = liquiddsp.liquid_vectorf_mul
liquid_vectorf_mul.restype = None
liquid_vectorf_mul.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
liquid_vectorf_mulscalar = liquiddsp.liquid_vectorf_mulscalar
liquid_vectorf_mulscalar.restype = None
liquid_vectorf_mulscalar.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
liquid_vectorf_cexpj = liquiddsp.liquid_vectorf_cexpj
liquid_vectorf_cexpj.restype = None
liquid_vectorf_cexpj.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
liquid_vectorf_carg = liquiddsp.liquid_vectorf_carg
liquid_vectorf_carg.restype = None
liquid_vectorf_carg.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
liquid_vectorf_abs = liquiddsp.liquid_vectorf_abs
liquid_vectorf_abs.restype = None
liquid_vectorf_abs.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
#liquid_vectorf_sumsq = liquiddsp.liquid_vectorf_sumsq
#liquid_vectorf_sumsq.restype = ctypes.c_float
#liquid_vectorf_sumsq.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
liquid_vectorf_norm = liquiddsp.liquid_vectorf_norm
liquid_vectorf_norm.restype = ctypes.c_float
liquid_vectorf_norm.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32]
#liquid_vectorf_pnorm = liquiddsp.liquid_vectorf_pnorm
#liquid_vectorf_pnorm.restype = ctypes.c_float
#liquid_vectorf_pnorm.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.c_float]
liquid_vectorf_normalize = liquiddsp.liquid_vectorf_normalize
liquid_vectorf_normalize.restype = None
liquid_vectorf_normalize.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
#liquid_vectorcf_init = liquiddsp.liquid_vectorcf_init
#liquid_vectorcf_init.restype = None
#liquid_vectorcf_init.argtypes = [liquid_float_complex, ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
liquid_vectorcf_add = liquiddsp.liquid_vectorcf_add
liquid_vectorcf_add.restype = None
liquid_vectorcf_add.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
liquid_vectorcf_addscalar = liquiddsp.liquid_vectorcf_addscalar
liquid_vectorcf_addscalar.restype = None
liquid_vectorcf_addscalar.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, liquid_float_complex, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
liquid_vectorcf_mul = liquiddsp.liquid_vectorcf_mul
liquid_vectorcf_mul.restype = None
liquid_vectorcf_mul.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
liquid_vectorcf_mulscalar = liquiddsp.liquid_vectorcf_mulscalar
liquid_vectorcf_mulscalar.restype = None
liquid_vectorcf_mulscalar.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, liquid_float_complex, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
liquid_vectorcf_cexpj = liquiddsp.liquid_vectorcf_cexpj
liquid_vectorcf_cexpj.restype = None
liquid_vectorcf_cexpj.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
liquid_vectorcf_carg = liquiddsp.liquid_vectorcf_carg
liquid_vectorcf_carg.restype = None
liquid_vectorcf_carg.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
liquid_vectorcf_abs = liquiddsp.liquid_vectorcf_abs
liquid_vectorcf_abs.restype = None
liquid_vectorcf_abs.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(ctypes.c_float)]
#liquid_vectorcf_sumsq = liquiddsp.liquid_vectorcf_sumsq
#liquid_vectorcf_sumsq.restype = ctypes.c_float
#liquid_vectorcf_sumsq.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
liquid_vectorcf_norm = liquiddsp.liquid_vectorcf_norm
liquid_vectorcf_norm.restype = ctypes.c_float
liquid_vectorcf_norm.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32]
#liquid_vectorcf_pnorm = liquiddsp.liquid_vectorcf_pnorm
#liquid_vectorcf_pnorm.restype = ctypes.c_float
#liquid_vectorcf_pnorm.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.c_float]
liquid_vectorcf_normalize = liquiddsp.liquid_vectorcf_normalize
liquid_vectorcf_normalize.restype = None
liquid_vectorcf_normalize.argtypes = [ctypes.POINTER(struct_c__SA_liquid_float_complex), ctypes.c_uint32, ctypes.POINTER(struct_c__SA_liquid_float_complex)]
__all__ = \
    ['LIQUID_AGC_SQUELCH_DISABLED', 'LIQUID_AGC_SQUELCH_ENABLED',
    'LIQUID_AGC_SQUELCH_FALL', 'LIQUID_AGC_SQUELCH_RISE',
    'LIQUID_AGC_SQUELCH_SIGNALHI', 'LIQUID_AGC_SQUELCH_SIGNALLO',
    'LIQUID_AGC_SQUELCH_TIMEOUT', 'LIQUID_AGC_SQUELCH_UNKNOWN',
    'LIQUID_AMPMODEM_DSB', 'LIQUID_AMPMODEM_LSB',
    'LIQUID_AMPMODEM_USB', 'LIQUID_COMPANDER_ALAW',
    'LIQUID_COMPANDER_LINEAR', 'LIQUID_COMPANDER_MULAW',
    'LIQUID_COMPANDER_NONE', 'LIQUID_CPFSK_GMSK',
    'LIQUID_CPFSK_RCOS_FULL', 'LIQUID_CPFSK_RCOS_PARTIAL',
    'LIQUID_CPFSK_SQUARE', 'LIQUID_CRC_16', 'LIQUID_CRC_24',
    'LIQUID_CRC_32', 'LIQUID_CRC_8', 'LIQUID_CRC_CHECKSUM',
    'LIQUID_CRC_NONE', 'LIQUID_CRC_UNKNOWN', 'LIQUID_EICONFIG',
    'LIQUID_EIMEM', 'LIQUID_EIMODE', 'LIQUID_EINT', 'LIQUID_EIO',
    'LIQUID_EIOBJ', 'LIQUID_EIRANGE', 'LIQUID_EIVAL',
    'LIQUID_ENOINIT', 'LIQUID_EUMODE', 'LIQUID_FEC_CONV_V27',
    'LIQUID_FEC_CONV_V27P23', 'LIQUID_FEC_CONV_V27P34',
    'LIQUID_FEC_CONV_V27P45', 'LIQUID_FEC_CONV_V27P56',
    'LIQUID_FEC_CONV_V27P67', 'LIQUID_FEC_CONV_V27P78',
    'LIQUID_FEC_CONV_V29', 'LIQUID_FEC_CONV_V29P23',
    'LIQUID_FEC_CONV_V29P34', 'LIQUID_FEC_CONV_V29P45',
    'LIQUID_FEC_CONV_V29P56', 'LIQUID_FEC_CONV_V29P67',
    'LIQUID_FEC_CONV_V29P78', 'LIQUID_FEC_CONV_V39',
    'LIQUID_FEC_CONV_V615', 'LIQUID_FEC_GOLAY2412',
    'LIQUID_FEC_HAMMING128', 'LIQUID_FEC_HAMMING74',
    'LIQUID_FEC_HAMMING84', 'LIQUID_FEC_NONE', 'LIQUID_FEC_REP3',
    'LIQUID_FEC_REP5', 'LIQUID_FEC_RS_M8', 'LIQUID_FEC_SECDED2216',
    'LIQUID_FEC_SECDED3932', 'LIQUID_FEC_SECDED7264',
    'LIQUID_FEC_UNKNOWN', 'LIQUID_FFT_BACKWARD', 'LIQUID_FFT_FORWARD',
    'LIQUID_FFT_IMDCT', 'LIQUID_FFT_MDCT', 'LIQUID_FFT_REDFT00',
    'LIQUID_FFT_REDFT01', 'LIQUID_FFT_REDFT10', 'LIQUID_FFT_REDFT11',
    'LIQUID_FFT_RODFT00', 'LIQUID_FFT_RODFT01', 'LIQUID_FFT_RODFT10',
    'LIQUID_FFT_RODFT11', 'LIQUID_FFT_UNKNOWN',
    'LIQUID_FIRDESPM_BANDPASS', 'LIQUID_FIRDESPM_DIFFERENTIATOR',
    'LIQUID_FIRDESPM_EXPWEIGHT', 'LIQUID_FIRDESPM_FLATWEIGHT',
    'LIQUID_FIRDESPM_HILBERT', 'LIQUID_FIRDESPM_LINWEIGHT',
    'LIQUID_FIRFILT_ARKAISER', 'LIQUID_FIRFILT_FARCSECH',
    'LIQUID_FIRFILT_FEXP', 'LIQUID_FIRFILT_FSECH',
    'LIQUID_FIRFILT_GMSKRX', 'LIQUID_FIRFILT_GMSKTX',
    'LIQUID_FIRFILT_KAISER', 'LIQUID_FIRFILT_PM',
    'LIQUID_FIRFILT_RCOS', 'LIQUID_FIRFILT_RFARCSECH',
    'LIQUID_FIRFILT_RFEXP', 'LIQUID_FIRFILT_RFSECH',
    'LIQUID_FIRFILT_RKAISER', 'LIQUID_FIRFILT_RRC',
    'LIQUID_FIRFILT_UNKNOWN', 'LIQUID_FIRFILT_hM3',
    'LIQUID_IIRDES_BANDPASS', 'LIQUID_IIRDES_BANDSTOP',
    'LIQUID_IIRDES_BESSEL', 'LIQUID_IIRDES_BUTTER',
    'LIQUID_IIRDES_CHEBY1', 'LIQUID_IIRDES_CHEBY2',
    'LIQUID_IIRDES_ELLIP', 'LIQUID_IIRDES_HIGHPASS',
    'LIQUID_IIRDES_LOWPASS', 'LIQUID_IIRDES_SOS', 'LIQUID_IIRDES_TF',
    'LIQUID_MODEM_APSK128', 'LIQUID_MODEM_APSK16',
    'LIQUID_MODEM_APSK256', 'LIQUID_MODEM_APSK32',
    'LIQUID_MODEM_APSK4', 'LIQUID_MODEM_APSK64', 'LIQUID_MODEM_APSK8',
    'LIQUID_MODEM_ARB', 'LIQUID_MODEM_ARB128OPT',
    'LIQUID_MODEM_ARB16OPT', 'LIQUID_MODEM_ARB256OPT',
    'LIQUID_MODEM_ARB32OPT', 'LIQUID_MODEM_ARB64OPT',
    'LIQUID_MODEM_ARB64VT', 'LIQUID_MODEM_ASK128',
    'LIQUID_MODEM_ASK16', 'LIQUID_MODEM_ASK2', 'LIQUID_MODEM_ASK256',
    'LIQUID_MODEM_ASK32', 'LIQUID_MODEM_ASK4', 'LIQUID_MODEM_ASK64',
    'LIQUID_MODEM_ASK8', 'LIQUID_MODEM_BPSK', 'LIQUID_MODEM_DPSK128',
    'LIQUID_MODEM_DPSK16', 'LIQUID_MODEM_DPSK2',
    'LIQUID_MODEM_DPSK256', 'LIQUID_MODEM_DPSK32',
    'LIQUID_MODEM_DPSK4', 'LIQUID_MODEM_DPSK64', 'LIQUID_MODEM_DPSK8',
    'LIQUID_MODEM_OOK', 'LIQUID_MODEM_PSK128', 'LIQUID_MODEM_PSK16',
    'LIQUID_MODEM_PSK2', 'LIQUID_MODEM_PSK256', 'LIQUID_MODEM_PSK32',
    'LIQUID_MODEM_PSK4', 'LIQUID_MODEM_PSK64', 'LIQUID_MODEM_PSK8',
    'LIQUID_MODEM_QAM128', 'LIQUID_MODEM_QAM16',
    'LIQUID_MODEM_QAM256', 'LIQUID_MODEM_QAM32', 'LIQUID_MODEM_QAM4',
    'LIQUID_MODEM_QAM64', 'LIQUID_MODEM_QAM8', 'LIQUID_MODEM_QPSK',
    'LIQUID_MODEM_SQAM128', 'LIQUID_MODEM_SQAM32',
    'LIQUID_MODEM_UNKNOWN', 'LIQUID_MODEM_V29', 'LIQUID_NCO',
    'LIQUID_OK', 'LIQUID_RESAMP_DECIM', 'LIQUID_RESAMP_INTERP',
    'LIQUID_VCO', 'LIQUID_WINDOW_BLACKMANHARRIS',
    'LIQUID_WINDOW_BLACKMANHARRIS7', 'LIQUID_WINDOW_FLATTOP',
    'LIQUID_WINDOW_HAMMING', 'LIQUID_WINDOW_HANN',
    'LIQUID_WINDOW_KAISER', 'LIQUID_WINDOW_KBD',
    'LIQUID_WINDOW_RCOSTAPER', 'LIQUID_WINDOW_TRIANGULAR',
    'LIQUID_WINDOW_UNKNOWN', 'agc_crcf', 'agc_crcf_create',
    'agc_crcf_destroy', 'agc_crcf_execute', 'agc_crcf_execute_block',
    'agc_crcf_get_bandwidth', 'agc_crcf_get_gain',
    'agc_crcf_get_rssi', 'agc_crcf_get_scale',
    'agc_crcf_get_signal_level', 'agc_crcf_init', 'agc_crcf_lock',
    'agc_crcf_print', 'agc_crcf_reset', 'agc_crcf_set_bandwidth',
    'agc_crcf_set_gain', 'agc_crcf_set_rssi', 'agc_crcf_set_scale',
    'agc_crcf_set_signal_level', 'agc_crcf_squelch_disable',
    'agc_crcf_squelch_enable', 'agc_crcf_squelch_get_status',
    'agc_crcf_squelch_get_threshold', 'agc_crcf_squelch_get_timeout',
    'agc_crcf_squelch_is_enabled', 'agc_crcf_squelch_set_threshold',
    'agc_crcf_squelch_set_timeout', 'agc_crcf_unlock', 'agc_rrrf',
    'agc_rrrf_create', 'agc_rrrf_destroy', 'agc_rrrf_execute',
    'agc_rrrf_execute_block', 'agc_rrrf_get_bandwidth',
    'agc_rrrf_get_gain', 'agc_rrrf_get_rssi', 'agc_rrrf_get_scale',
    'agc_rrrf_get_signal_level', 'agc_rrrf_init', 'agc_rrrf_lock',
    'agc_rrrf_print', 'agc_rrrf_reset', 'agc_rrrf_set_bandwidth',
    'agc_rrrf_set_gain', 'agc_rrrf_set_rssi', 'agc_rrrf_set_scale',
    'agc_rrrf_set_signal_level', 'agc_rrrf_squelch_disable',
    'agc_rrrf_squelch_enable', 'agc_rrrf_squelch_get_status',
    'agc_rrrf_squelch_get_threshold', 'agc_rrrf_squelch_get_timeout',
    'agc_rrrf_squelch_is_enabled', 'agc_rrrf_squelch_set_threshold',
    'agc_rrrf_squelch_set_timeout', 'agc_rrrf_unlock',
    'agc_squelch_mode', 'agc_squelch_mode__enumvalues', 'ampmodem',
    'ampmodem_create', 'ampmodem_demodulate',
    'ampmodem_demodulate_block', 'ampmodem_destroy',
    'ampmodem_get_delay_demod', 'ampmodem_get_delay_mod',
    'ampmodem_modulate', 'ampmodem_modulate_block', 'ampmodem_print',
    'ampmodem_reset', 'asgramcf', 'asgramcf_create',
    'asgramcf_destroy', 'asgramcf_execute', 'asgramcf_print',
    'asgramcf_push', 'asgramcf_reset', 'asgramcf_set_display',
    'asgramcf_set_scale', 'asgramcf_write', 'asgramf',
    'asgramf_create', 'asgramf_destroy', 'asgramf_execute',
    'asgramf_print', 'asgramf_push', 'asgramf_reset',
    'asgramf_set_display', 'asgramf_set_scale', 'asgramf_write',
    'autocorr_cccf', 'autocorr_cccf_create', 'autocorr_cccf_destroy',
    'autocorr_cccf_execute', 'autocorr_cccf_execute_block',
    'autocorr_cccf_get_energy', 'autocorr_cccf_print',
    'autocorr_cccf_push', 'autocorr_cccf_reset',
    'autocorr_cccf_write', 'autocorr_rrrf', 'autocorr_rrrf_create',
    'autocorr_rrrf_destroy', 'autocorr_rrrf_execute',
    'autocorr_rrrf_execute_block', 'autocorr_rrrf_get_energy',
    'autocorr_rrrf_print', 'autocorr_rrrf_push',
    'autocorr_rrrf_reset', 'autocorr_rrrf_write', 'awgn',
    'bessel_azpkf', 'bilinear_zpkf', 'bpacketgen',
    'bpacketgen_create', 'bpacketgen_destroy', 'bpacketgen_encode',
    'bpacketgen_get_packet_len', 'bpacketgen_print',
    'bpacketgen_recreate', 'bpacketsync', 'bpacketsync_callback',
    'bpacketsync_create', 'bpacketsync_destroy',
    'bpacketsync_execute', 'bpacketsync_execute_bit',
    'bpacketsync_execute_byte', 'bpacketsync_execute_sym',
    'bpacketsync_print', 'bpacketsync_reset', 'bpresync_cccf',
    'bpresync_cccf_create', 'bpresync_cccf_destroy',
    'bpresync_cccf_execute', 'bpresync_cccf_print',
    'bpresync_cccf_push', 'bpresync_cccf_reset', 'bsequence',
    'bsequence_accumulate', 'bsequence_add', 'bsequence_circshift',
    'bsequence_correlate', 'bsequence_create',
    'bsequence_create_ccodes', 'bsequence_destroy',
    'bsequence_get_length', 'bsequence_index', 'bsequence_init',
    'bsequence_init_msequence', 'bsequence_mul', 'bsequence_print',
    'bsequence_push', 'bsequence_reset', 'bsync_cccf',
    'bsync_cccf_correlate', 'bsync_cccf_create',
    'bsync_cccf_create_msequence', 'bsync_cccf_destroy',
    'bsync_cccf_print', 'bsync_crcf', 'bsync_crcf_correlate',
    'bsync_crcf_create', 'bsync_crcf_create_msequence',
    'bsync_crcf_destroy', 'bsync_crcf_print', 'bsync_rrrf',
    'bsync_rrrf_correlate', 'bsync_rrrf_create',
    'bsync_rrrf_create_msequence', 'bsync_rrrf_destroy',
    'bsync_rrrf_print', 'butter_azpkf', 'c__EA_agc_squelch_mode',
    'c__EA_crc_scheme', 'c__EA_fec_scheme',
    'c__EA_liquid_ampmodem_type', 'c__EA_liquid_compander_type',
    'c__EA_liquid_cpfsk_filter', 'c__EA_liquid_error_code',
    'c__EA_liquid_fft_type', 'c__EA_liquid_firdespm_btype',
    'c__EA_liquid_firdespm_wtype', 'c__EA_liquid_firfilt_type',
    'c__EA_liquid_iirdes_bandtype', 'c__EA_liquid_iirdes_filtertype',
    'c__EA_liquid_iirdes_format', 'c__EA_liquid_ncotype',
    'c__EA_liquid_resamp_type', 'c__EA_liquid_window_type',
    'c__EA_modulation_scheme', 'cawgn', 'cbuffercf',
    'cbuffercf_create', 'cbuffercf_create_max',
    'cbuffercf_debug_print', 'cbuffercf_destroy', 'cbuffercf_is_full',
    'cbuffercf_max_read', 'cbuffercf_max_size', 'cbuffercf_pop',
    'cbuffercf_print', 'cbuffercf_push', 'cbuffercf_read',
    'cbuffercf_release', 'cbuffercf_reset', 'cbuffercf_size',
    'cbuffercf_space_available', 'cbuffercf_write', 'cbufferf',
    'cbufferf_create', 'cbufferf_create_max', 'cbufferf_debug_print',
    'cbufferf_destroy', 'cbufferf_is_full', 'cbufferf_max_read',
    'cbufferf_max_size', 'cbufferf_pop', 'cbufferf_print',
    'cbufferf_push', 'cbufferf_read', 'cbufferf_release',
    'cbufferf_reset', 'cbufferf_size', 'cbufferf_space_available',
    'cbufferf_write', 'channel_cccf', 'channel_cccf_add_awgn',
    'channel_cccf_add_carrier_offset', 'channel_cccf_add_multipath',
    'channel_cccf_add_shadowing', 'channel_cccf_create',
    'channel_cccf_destroy', 'channel_cccf_execute',
    'channel_cccf_execute_block', 'channel_cccf_print',
    'cheby1_azpkf', 'cheby2_azpkf', 'chromosome', 'chromosome_copy',
    'chromosome_create', 'chromosome_create_basic',
    'chromosome_create_clone', 'chromosome_crossover',
    'chromosome_destroy', 'chromosome_get_num_traits',
    'chromosome_init', 'chromosome_init_random', 'chromosome_initf',
    'chromosome_mutate', 'chromosome_print', 'chromosome_printf',
    'chromosome_reset', 'chromosome_value', 'chromosome_valuef',
    'compress_cf_mulaw', 'compress_mulaw', 'count_bit_errors',
    'count_bit_errors_array', 'cpfskdem', 'cpfskdem_create',
    'cpfskdem_demodulate', 'cpfskdem_destroy', 'cpfskdem_get_delay',
    'cpfskdem_print', 'cpfskdem_reset', 'cpfskmod', 'cpfskmod_create',
    'cpfskmod_destroy', 'cpfskmod_get_delay', 'cpfskmod_modulate',
    'cpfskmod_print', 'cpfskmod_reset', 'crandnf', 'crc_append_key',
    'crc_check_key', 'crc_generate_key', 'crc_get_length',
    'crc_scheme', 'crc_scheme__enumvalues', 'crc_scheme_str',
    'crc_sizeof_key', 'crc_validate_message', 'cvsd', 'cvsd_create',
    'cvsd_decode', 'cvsd_decode8', 'cvsd_destroy', 'cvsd_encode',
    'cvsd_encode8', 'cvsd_print', 'dds_cccf', 'dds_cccf_create',
    'dds_cccf_decim_execute', 'dds_cccf_destroy',
    'dds_cccf_interp_execute', 'dds_cccf_print', 'dds_cccf_reset',
    'detector_cccf', 'detector_cccf_correlate',
    'detector_cccf_create', 'detector_cccf_destroy',
    'detector_cccf_print', 'detector_cccf_reset', 'dotprod_cccf',
    'dotprod_cccf_create', 'dotprod_cccf_destroy',
    'dotprod_cccf_execute', 'dotprod_cccf_print',
    'dotprod_cccf_recreate', 'dotprod_cccf_run', 'dotprod_cccf_run4',
    'dotprod_crcf', 'dotprod_crcf_create', 'dotprod_crcf_destroy',
    'dotprod_crcf_execute', 'dotprod_crcf_print',
    'dotprod_crcf_recreate', 'dotprod_crcf_run', 'dotprod_crcf_run4',
    'dotprod_rrrf', 'dotprod_rrrf_create', 'dotprod_rrrf_destroy',
    'dotprod_rrrf_execute', 'dotprod_rrrf_print',
    'dotprod_rrrf_recreate', 'dotprod_rrrf_run', 'dotprod_rrrf_run4',
    'dsssframegen', 'dsssframegen_assemble', 'dsssframegen_create',
    'dsssframegen_destroy', 'dsssframegen_getframelen',
    'dsssframegen_getprops', 'dsssframegen_is_assembled',
    'dsssframegen_reset', 'dsssframegen_set_header_len',
    'dsssframegen_set_header_props', 'dsssframegen_setprops',
    'dsssframegen_write_samples', 'dsssframegenprops_s',
    'dsssframesync', 'dsssframesync_create',
    'dsssframesync_debug_disable', 'dsssframesync_debug_enable',
    'dsssframesync_debug_print', 'dsssframesync_decode_header_soft',
    'dsssframesync_decode_payload_soft', 'dsssframesync_destroy',
    'dsssframesync_execute', 'dsssframesync_get_framedatastats',
    'dsssframesync_is_frame_open', 'dsssframesync_print',
    'dsssframesync_reset', 'dsssframesync_reset_framedatastats',
    'dsssframesync_set_header_len', 'dsssframesync_set_header_props',
    'ellip_azpkf', 'eqlms_cccf', 'eqlms_cccf_create',
    'eqlms_cccf_create_lowpass', 'eqlms_cccf_create_rnyquist',
    'eqlms_cccf_destroy', 'eqlms_cccf_execute',
    'eqlms_cccf_execute_block', 'eqlms_cccf_get_bw',
    'eqlms_cccf_get_weights', 'eqlms_cccf_print', 'eqlms_cccf_push',
    'eqlms_cccf_push_block', 'eqlms_cccf_recreate',
    'eqlms_cccf_reset', 'eqlms_cccf_set_bw', 'eqlms_cccf_step',
    'eqlms_cccf_step_blind', 'eqlms_cccf_train', 'eqlms_rrrf',
    'eqlms_rrrf_create', 'eqlms_rrrf_create_lowpass',
    'eqlms_rrrf_create_rnyquist', 'eqlms_rrrf_destroy',
    'eqlms_rrrf_execute', 'eqlms_rrrf_execute_block',
    'eqlms_rrrf_get_bw', 'eqlms_rrrf_get_weights', 'eqlms_rrrf_print',
    'eqlms_rrrf_push', 'eqlms_rrrf_push_block', 'eqlms_rrrf_recreate',
    'eqlms_rrrf_reset', 'eqlms_rrrf_set_bw', 'eqlms_rrrf_step',
    'eqlms_rrrf_step_blind', 'eqlms_rrrf_train', 'eqrls_cccf',
    'eqrls_cccf_create', 'eqrls_cccf_destroy', 'eqrls_cccf_execute',
    'eqrls_cccf_get_bw', 'eqrls_cccf_get_weights', 'eqrls_cccf_print',
    'eqrls_cccf_push', 'eqrls_cccf_recreate', 'eqrls_cccf_reset',
    'eqrls_cccf_set_bw', 'eqrls_cccf_step', 'eqrls_cccf_train',
    'eqrls_rrrf', 'eqrls_rrrf_create', 'eqrls_rrrf_destroy',
    'eqrls_rrrf_execute', 'eqrls_rrrf_get_bw',
    'eqrls_rrrf_get_weights', 'eqrls_rrrf_print', 'eqrls_rrrf_push',
    'eqrls_rrrf_recreate', 'eqrls_rrrf_reset', 'eqrls_rrrf_set_bw',
    'eqrls_rrrf_step', 'eqrls_rrrf_train', 'estimate_req_filter_As',
    'estimate_req_filter_df', 'estimate_req_filter_len',
    'expand_cf_mulaw', 'expand_mulaw', 'fec', 'fec_create',
    'fec_decode', 'fec_decode_soft', 'fec_destroy', 'fec_encode',
    'fec_get_enc_msg_length', 'fec_get_rate', 'fec_print',
    'fec_recreate', 'fec_scheme', 'fec_scheme__enumvalues',
    'fec_scheme_str', 'fft_create_plan', 'fft_create_plan_r2r_1d',
    'fft_destroy_plan', 'fft_execute', 'fft_print_plan',
    'fft_r2r_1d_run', 'fft_run', 'fft_shift', 'fftfilt_cccf',
    'fftfilt_cccf_create', 'fftfilt_cccf_destroy',
    'fftfilt_cccf_execute', 'fftfilt_cccf_get_length',
    'fftfilt_cccf_get_scale', 'fftfilt_cccf_print',
    'fftfilt_cccf_reset', 'fftfilt_cccf_set_scale', 'fftfilt_crcf',
    'fftfilt_crcf_create', 'fftfilt_crcf_destroy',
    'fftfilt_crcf_execute', 'fftfilt_crcf_get_length',
    'fftfilt_crcf_get_scale', 'fftfilt_crcf_print',
    'fftfilt_crcf_reset', 'fftfilt_crcf_set_scale', 'fftfilt_rrrf',
    'fftfilt_rrrf_create', 'fftfilt_rrrf_destroy',
    'fftfilt_rrrf_execute', 'fftfilt_rrrf_get_length',
    'fftfilt_rrrf_get_scale', 'fftfilt_rrrf_print',
    'fftfilt_rrrf_reset', 'fftfilt_rrrf_set_scale', 'fftplan',
    'fir_group_delay', 'firdecim_cccf', 'firdecim_cccf_create',
    'firdecim_cccf_create_kaiser', 'firdecim_cccf_create_prototype',
    'firdecim_cccf_destroy', 'firdecim_cccf_execute',
    'firdecim_cccf_execute_block', 'firdecim_cccf_get_decim_rate',
    'firdecim_cccf_get_scale', 'firdecim_cccf_print',
    'firdecim_cccf_reset', 'firdecim_cccf_set_scale', 'firdecim_crcf',
    'firdecim_crcf_create', 'firdecim_crcf_create_kaiser',
    'firdecim_crcf_create_prototype', 'firdecim_crcf_destroy',
    'firdecim_crcf_execute', 'firdecim_crcf_execute_block',
    'firdecim_crcf_get_decim_rate', 'firdecim_crcf_get_scale',
    'firdecim_crcf_print', 'firdecim_crcf_reset',
    'firdecim_crcf_set_scale', 'firdecim_rrrf',
    'firdecim_rrrf_create', 'firdecim_rrrf_create_kaiser',
    'firdecim_rrrf_create_prototype', 'firdecim_rrrf_destroy',
    'firdecim_rrrf_execute', 'firdecim_rrrf_execute_block',
    'firdecim_rrrf_get_decim_rate', 'firdecim_rrrf_get_scale',
    'firdecim_rrrf_print', 'firdecim_rrrf_reset',
    'firdecim_rrrf_set_scale', 'firdespm', 'firdespm_callback',
    'firdespm_create', 'firdespm_create_callback', 'firdespm_destroy',
    'firdespm_execute', 'firdespm_lowpass', 'firdespm_print',
    'firdespm_run', 'firfarrow_crcf', 'firfarrow_crcf_create',
    'firfarrow_crcf_destroy', 'firfarrow_crcf_execute',
    'firfarrow_crcf_execute_block', 'firfarrow_crcf_freqresponse',
    'firfarrow_crcf_get_coefficients', 'firfarrow_crcf_get_length',
    'firfarrow_crcf_groupdelay', 'firfarrow_crcf_print',
    'firfarrow_crcf_push', 'firfarrow_crcf_reset',
    'firfarrow_crcf_set_delay', 'firfarrow_rrrf',
    'firfarrow_rrrf_create', 'firfarrow_rrrf_destroy',
    'firfarrow_rrrf_execute', 'firfarrow_rrrf_execute_block',
    'firfarrow_rrrf_freqresponse', 'firfarrow_rrrf_get_coefficients',
    'firfarrow_rrrf_get_length', 'firfarrow_rrrf_groupdelay',
    'firfarrow_rrrf_print', 'firfarrow_rrrf_push',
    'firfarrow_rrrf_reset', 'firfarrow_rrrf_set_delay',
    'firfilt_cccf', 'firfilt_cccf_create',
    'firfilt_cccf_create_dc_blocker', 'firfilt_cccf_create_firdespm',
    'firfilt_cccf_create_kaiser', 'firfilt_cccf_create_notch',
    'firfilt_cccf_create_rect', 'firfilt_cccf_create_rnyquist',
    'firfilt_cccf_destroy', 'firfilt_cccf_execute',
    'firfilt_cccf_execute_block', 'firfilt_cccf_freqresponse',
    'firfilt_cccf_get_coefficients', 'firfilt_cccf_get_length',
    'firfilt_cccf_get_scale', 'firfilt_cccf_groupdelay',
    'firfilt_cccf_print', 'firfilt_cccf_push',
    'firfilt_cccf_recreate', 'firfilt_cccf_reset',
    'firfilt_cccf_set_scale', 'firfilt_cccf_write', 'firfilt_crcf',
    'firfilt_crcf_create', 'firfilt_crcf_create_dc_blocker',
    'firfilt_crcf_create_firdespm', 'firfilt_crcf_create_kaiser',
    'firfilt_crcf_create_notch', 'firfilt_crcf_create_rect',
    'firfilt_crcf_create_rnyquist', 'firfilt_crcf_destroy',
    'firfilt_crcf_execute', 'firfilt_crcf_execute_block',
    'firfilt_crcf_freqresponse', 'firfilt_crcf_get_coefficients',
    'firfilt_crcf_get_length', 'firfilt_crcf_get_scale',
    'firfilt_crcf_groupdelay', 'firfilt_crcf_print',
    'firfilt_crcf_push', 'firfilt_crcf_recreate',
    'firfilt_crcf_reset', 'firfilt_crcf_set_scale',
    'firfilt_crcf_write', 'firfilt_rrrf', 'firfilt_rrrf_create',
    'firfilt_rrrf_create_dc_blocker', 'firfilt_rrrf_create_firdespm',
    'firfilt_rrrf_create_kaiser', 'firfilt_rrrf_create_notch',
    'firfilt_rrrf_create_rect', 'firfilt_rrrf_create_rnyquist',
    'firfilt_rrrf_destroy', 'firfilt_rrrf_execute',
    'firfilt_rrrf_execute_block', 'firfilt_rrrf_freqresponse',
    'firfilt_rrrf_get_coefficients', 'firfilt_rrrf_get_length',
    'firfilt_rrrf_get_scale', 'firfilt_rrrf_groupdelay',
    'firfilt_rrrf_print', 'firfilt_rrrf_push',
    'firfilt_rrrf_recreate', 'firfilt_rrrf_reset',
    'firfilt_rrrf_set_scale', 'firfilt_rrrf_write', 'firhilbf',
    'firhilbf_c2r_execute', 'firhilbf_create',
    'firhilbf_decim_execute', 'firhilbf_decim_execute_block',
    'firhilbf_destroy', 'firhilbf_interp_execute',
    'firhilbf_interp_execute_block', 'firhilbf_print',
    'firhilbf_r2c_execute', 'firhilbf_reset', 'firinterp_cccf',
    'firinterp_cccf_create', 'firinterp_cccf_create_kaiser',
    'firinterp_cccf_create_linear', 'firinterp_cccf_create_prototype',
    'firinterp_cccf_create_window', 'firinterp_cccf_destroy',
    'firinterp_cccf_execute', 'firinterp_cccf_execute_block',
    'firinterp_cccf_get_interp_rate', 'firinterp_cccf_get_scale',
    'firinterp_cccf_get_sub_len', 'firinterp_cccf_print',
    'firinterp_cccf_reset', 'firinterp_cccf_set_scale',
    'firinterp_crcf', 'firinterp_crcf_create',
    'firinterp_crcf_create_kaiser', 'firinterp_crcf_create_linear',
    'firinterp_crcf_create_prototype', 'firinterp_crcf_create_window',
    'firinterp_crcf_destroy', 'firinterp_crcf_execute',
    'firinterp_crcf_execute_block', 'firinterp_crcf_get_interp_rate',
    'firinterp_crcf_get_scale', 'firinterp_crcf_get_sub_len',
    'firinterp_crcf_print', 'firinterp_crcf_reset',
    'firinterp_crcf_set_scale', 'firinterp_rrrf',
    'firinterp_rrrf_create', 'firinterp_rrrf_create_kaiser',
    'firinterp_rrrf_create_linear', 'firinterp_rrrf_create_prototype',
    'firinterp_rrrf_create_window', 'firinterp_rrrf_destroy',
    'firinterp_rrrf_execute', 'firinterp_rrrf_execute_block',
    'firinterp_rrrf_get_interp_rate', 'firinterp_rrrf_get_scale',
    'firinterp_rrrf_get_sub_len', 'firinterp_rrrf_print',
    'firinterp_rrrf_reset', 'firinterp_rrrf_set_scale', 'firpfb_cccf',
    'firpfb_cccf_create', 'firpfb_cccf_create_default',
    'firpfb_cccf_create_drnyquist', 'firpfb_cccf_create_kaiser',
    'firpfb_cccf_create_rnyquist', 'firpfb_cccf_destroy',
    'firpfb_cccf_execute', 'firpfb_cccf_execute_block',
    'firpfb_cccf_get_scale', 'firpfb_cccf_print', 'firpfb_cccf_push',
    'firpfb_cccf_recreate', 'firpfb_cccf_reset',
    'firpfb_cccf_set_scale', 'firpfb_cccf_write', 'firpfb_crcf',
    'firpfb_crcf_create', 'firpfb_crcf_create_default',
    'firpfb_crcf_create_drnyquist', 'firpfb_crcf_create_kaiser',
    'firpfb_crcf_create_rnyquist', 'firpfb_crcf_destroy',
    'firpfb_crcf_execute', 'firpfb_crcf_execute_block',
    'firpfb_crcf_get_scale', 'firpfb_crcf_print', 'firpfb_crcf_push',
    'firpfb_crcf_recreate', 'firpfb_crcf_reset',
    'firpfb_crcf_set_scale', 'firpfb_crcf_write', 'firpfb_rrrf',
    'firpfb_rrrf_create', 'firpfb_rrrf_create_default',
    'firpfb_rrrf_create_drnyquist', 'firpfb_rrrf_create_kaiser',
    'firpfb_rrrf_create_rnyquist', 'firpfb_rrrf_destroy',
    'firpfb_rrrf_execute', 'firpfb_rrrf_execute_block',
    'firpfb_rrrf_get_scale', 'firpfb_rrrf_print', 'firpfb_rrrf_push',
    'firpfb_rrrf_recreate', 'firpfb_rrrf_reset',
    'firpfb_rrrf_set_scale', 'firpfb_rrrf_write', 'firpfbch2_crcf',
    'firpfbch2_crcf_create', 'firpfbch2_crcf_create_kaiser',
    'firpfbch2_crcf_destroy', 'firpfbch2_crcf_execute',
    'firpfbch2_crcf_get_M', 'firpfbch2_crcf_get_m',
    'firpfbch2_crcf_get_type', 'firpfbch2_crcf_print',
    'firpfbch2_crcf_reset', 'firpfbch_cccf',
    'firpfbch_cccf_analyzer_execute', 'firpfbch_cccf_create',
    'firpfbch_cccf_create_kaiser', 'firpfbch_cccf_create_rnyquist',
    'firpfbch_cccf_destroy', 'firpfbch_cccf_print',
    'firpfbch_cccf_reset', 'firpfbch_cccf_synthesizer_execute',
    'firpfbch_crcf', 'firpfbch_crcf_analyzer_execute',
    'firpfbch_crcf_create', 'firpfbch_crcf_create_kaiser',
    'firpfbch_crcf_create_rnyquist', 'firpfbch_crcf_destroy',
    'firpfbch_crcf_print', 'firpfbch_crcf_reset',
    'firpfbch_crcf_synthesizer_execute', 'firpfbchr_crcf',
    'firpfbchr_crcf_create', 'firpfbchr_crcf_create_kaiser',
    'firpfbchr_crcf_destroy', 'firpfbchr_crcf_execute',
    'firpfbchr_crcf_get_M', 'firpfbchr_crcf_get_P',
    'firpfbchr_crcf_get_m', 'firpfbchr_crcf_print',
    'firpfbchr_crcf_push', 'firpfbchr_crcf_reset', 'flexframegen',
    'flexframegen_assemble', 'flexframegen_create',
    'flexframegen_destroy', 'flexframegen_getframelen',
    'flexframegen_getprops', 'flexframegen_is_assembled',
    'flexframegen_print', 'flexframegen_reset',
    'flexframegen_set_header_len', 'flexframegen_set_header_props',
    'flexframegen_setprops', 'flexframegen_write_samples',
    'flexframegenprops_init_default', 'flexframegenprops_s',
    'flexframesync', 'flexframesync_create',
    'flexframesync_debug_disable', 'flexframesync_debug_enable',
    'flexframesync_debug_print', 'flexframesync_decode_header_soft',
    'flexframesync_decode_payload_soft', 'flexframesync_destroy',
    'flexframesync_execute', 'flexframesync_get_framedatastats',
    'flexframesync_is_frame_open', 'flexframesync_print',
    'flexframesync_reset', 'flexframesync_reset_framedatastats',
    'flexframesync_set_header_len', 'flexframesync_set_header_props',
    'framedatastats_print', 'framedatastats_reset',
    'framedatastats_s', 'framegen64', 'framegen64_create',
    'framegen64_destroy', 'framegen64_execute', 'framegen64_print',
    'framesync64', 'framesync64_create', 'framesync64_debug_disable',
    'framesync64_debug_enable', 'framesync64_debug_print',
    'framesync64_destroy', 'framesync64_execute',
    'framesync64_get_framedatastats', 'framesync64_print',
    'framesync64_reset', 'framesync64_reset_framedatastats',
    'framesync_callback', 'framesync_csma_callback',
    'framesyncstats_default', 'framesyncstats_init_default',
    'framesyncstats_print', 'framesyncstats_s', 'freqdem',
    'freqdem_create', 'freqdem_demodulate',
    'freqdem_demodulate_block', 'freqdem_destroy', 'freqdem_print',
    'freqdem_reset', 'freqmod', 'freqmod_create', 'freqmod_destroy',
    'freqmod_modulate', 'freqmod_modulate_block', 'freqmod_print',
    'freqmod_reset', 'fskdem', 'fskdem_create', 'fskdem_demodulate',
    'fskdem_destroy', 'fskdem_get_frequency_error',
    'fskdem_get_symbol_energy', 'fskdem_print', 'fskdem_reset',
    'fskframegen', 'fskframegen_assemble', 'fskframegen_create',
    'fskframegen_destroy', 'fskframegen_getframelen',
    'fskframegen_print', 'fskframegen_reset',
    'fskframegen_write_samples', 'fskframesync',
    'fskframesync_create', 'fskframesync_debug_disable',
    'fskframesync_debug_enable', 'fskframesync_debug_export',
    'fskframesync_destroy', 'fskframesync_execute',
    'fskframesync_execute_block', 'fskframesync_print',
    'fskframesync_reset', 'fskmod', 'fskmod_create', 'fskmod_destroy',
    'fskmod_modulate', 'fskmod_print', 'fskmod_reset', 'gasearch',
    'gasearch_create', 'gasearch_create_advanced', 'gasearch_destroy',
    'gasearch_evolve', 'gasearch_getopt', 'gasearch_print',
    'gasearch_run', 'gasearch_set_mutation_rate',
    'gasearch_set_population_size', 'gasearch_utility', 'gmskdem',
    'gmskdem_create', 'gmskdem_demodulate', 'gmskdem_destroy',
    'gmskdem_print', 'gmskdem_reset', 'gmskdem_set_eq_bw',
    'gmskframegen', 'gmskframegen_assemble', 'gmskframegen_create',
    'gmskframegen_destroy', 'gmskframegen_getframelen',
    'gmskframegen_is_assembled', 'gmskframegen_print',
    'gmskframegen_reset', 'gmskframegen_set_header_len',
    'gmskframegen_write', 'gmskframegen_write_samples',
    'gmskframesync', 'gmskframesync_create',
    'gmskframesync_debug_disable', 'gmskframesync_debug_enable',
    'gmskframesync_debug_print', 'gmskframesync_destroy',
    'gmskframesync_execute', 'gmskframesync_get_framedatastats',
    'gmskframesync_is_frame_open', 'gmskframesync_print',
    'gmskframesync_reset', 'gmskframesync_reset_framedatastats',
    'gmskframesync_set_header_len', 'gmskmod', 'gmskmod_create',
    'gmskmod_destroy', 'gmskmod_modulate', 'gmskmod_print',
    'gmskmod_reset', 'gradsearch', 'gradsearch_create',
    'gradsearch_destroy', 'gradsearch_execute', 'gradsearch_print',
    'gradsearch_step', 'gray_decode', 'gray_encode',
    'iir_group_delay', 'iirdecim_cccf', 'iirdecim_cccf_create',
    'iirdecim_cccf_create_default', 'iirdecim_cccf_create_prototype',
    'iirdecim_cccf_destroy', 'iirdecim_cccf_execute',
    'iirdecim_cccf_execute_block', 'iirdecim_cccf_groupdelay',
    'iirdecim_cccf_print', 'iirdecim_cccf_reset', 'iirdecim_crcf',
    'iirdecim_crcf_create', 'iirdecim_crcf_create_default',
    'iirdecim_crcf_create_prototype', 'iirdecim_crcf_destroy',
    'iirdecim_crcf_execute', 'iirdecim_crcf_execute_block',
    'iirdecim_crcf_groupdelay', 'iirdecim_crcf_print',
    'iirdecim_crcf_reset', 'iirdecim_rrrf', 'iirdecim_rrrf_create',
    'iirdecim_rrrf_create_default', 'iirdecim_rrrf_create_prototype',
    'iirdecim_rrrf_destroy', 'iirdecim_rrrf_execute',
    'iirdecim_rrrf_execute_block', 'iirdecim_rrrf_groupdelay',
    'iirdecim_rrrf_print', 'iirdecim_rrrf_reset', 'iirdes_dzpk2sosf',
    'iirdes_dzpk2tff', 'iirdes_dzpk_lp2bp', 'iirdes_dzpk_lp2hp',
    'iirdes_freqprewarp', 'iirdes_isstable', 'iirdes_pll_active_PI',
    'iirdes_pll_active_lag', 'iirfilt_cccf', 'iirfilt_cccf_create',
    'iirfilt_cccf_create_dc_blocker',
    'iirfilt_cccf_create_differentiator',
    'iirfilt_cccf_create_integrator', 'iirfilt_cccf_create_lowpass',
    'iirfilt_cccf_create_pll', 'iirfilt_cccf_create_prototype',
    'iirfilt_cccf_create_sos', 'iirfilt_cccf_destroy',
    'iirfilt_cccf_execute', 'iirfilt_cccf_execute_block',
    'iirfilt_cccf_freqresponse', 'iirfilt_cccf_get_length',
    'iirfilt_cccf_groupdelay', 'iirfilt_cccf_print',
    'iirfilt_cccf_reset', 'iirfilt_crcf', 'iirfilt_crcf_create',
    'iirfilt_crcf_create_dc_blocker',
    'iirfilt_crcf_create_differentiator',
    'iirfilt_crcf_create_integrator', 'iirfilt_crcf_create_lowpass',
    'iirfilt_crcf_create_pll', 'iirfilt_crcf_create_prototype',
    'iirfilt_crcf_create_sos', 'iirfilt_crcf_destroy',
    'iirfilt_crcf_execute', 'iirfilt_crcf_execute_block',
    'iirfilt_crcf_freqresponse', 'iirfilt_crcf_get_length',
    'iirfilt_crcf_groupdelay', 'iirfilt_crcf_print',
    'iirfilt_crcf_reset', 'iirfilt_rrrf', 'iirfilt_rrrf_create',
    'iirfilt_rrrf_create_dc_blocker',
    'iirfilt_rrrf_create_differentiator',
    'iirfilt_rrrf_create_integrator', 'iirfilt_rrrf_create_lowpass',
    'iirfilt_rrrf_create_pll', 'iirfilt_rrrf_create_prototype',
    'iirfilt_rrrf_create_sos', 'iirfilt_rrrf_destroy',
    'iirfilt_rrrf_execute', 'iirfilt_rrrf_execute_block',
    'iirfilt_rrrf_freqresponse', 'iirfilt_rrrf_get_length',
    'iirfilt_rrrf_groupdelay', 'iirfilt_rrrf_print',
    'iirfilt_rrrf_reset', 'iirfiltsos_cccf', 'iirfiltsos_cccf_create',
    'iirfiltsos_cccf_destroy', 'iirfiltsos_cccf_execute',
    'iirfiltsos_cccf_execute_df1', 'iirfiltsos_cccf_execute_df2',
    'iirfiltsos_cccf_groupdelay', 'iirfiltsos_cccf_print',
    'iirfiltsos_cccf_reset', 'iirfiltsos_cccf_set_coefficients',
    'iirfiltsos_crcf', 'iirfiltsos_crcf_create',
    'iirfiltsos_crcf_destroy', 'iirfiltsos_crcf_execute',
    'iirfiltsos_crcf_execute_df1', 'iirfiltsos_crcf_execute_df2',
    'iirfiltsos_crcf_groupdelay', 'iirfiltsos_crcf_print',
    'iirfiltsos_crcf_reset', 'iirfiltsos_crcf_set_coefficients',
    'iirfiltsos_rrrf', 'iirfiltsos_rrrf_create',
    'iirfiltsos_rrrf_destroy', 'iirfiltsos_rrrf_execute',
    'iirfiltsos_rrrf_execute_df1', 'iirfiltsos_rrrf_execute_df2',
    'iirfiltsos_rrrf_groupdelay', 'iirfiltsos_rrrf_print',
    'iirfiltsos_rrrf_reset', 'iirfiltsos_rrrf_set_coefficients',
    'iirhilbf', 'iirhilbf_c2r_execute', 'iirhilbf_create',
    'iirhilbf_create_default', 'iirhilbf_decim_execute',
    'iirhilbf_decim_execute_block', 'iirhilbf_destroy',
    'iirhilbf_interp_execute', 'iirhilbf_interp_execute_block',
    'iirhilbf_print', 'iirhilbf_r2c_execute', 'iirhilbf_reset',
    'iirinterp_cccf', 'iirinterp_cccf_create',
    'iirinterp_cccf_create_default',
    'iirinterp_cccf_create_prototype', 'iirinterp_cccf_destroy',
    'iirinterp_cccf_execute', 'iirinterp_cccf_execute_block',
    'iirinterp_cccf_groupdelay', 'iirinterp_cccf_print',
    'iirinterp_cccf_reset', 'iirinterp_crcf', 'iirinterp_crcf_create',
    'iirinterp_crcf_create_default',
    'iirinterp_crcf_create_prototype', 'iirinterp_crcf_destroy',
    'iirinterp_crcf_execute', 'iirinterp_crcf_execute_block',
    'iirinterp_crcf_groupdelay', 'iirinterp_crcf_print',
    'iirinterp_crcf_reset', 'iirinterp_rrrf', 'iirinterp_rrrf_create',
    'iirinterp_rrrf_create_default',
    'iirinterp_rrrf_create_prototype', 'iirinterp_rrrf_destroy',
    'iirinterp_rrrf_execute', 'iirinterp_rrrf_execute_block',
    'iirinterp_rrrf_groupdelay', 'iirinterp_rrrf_print',
    'iirinterp_rrrf_reset', 'interleaver', 'interleaver_create',
    'interleaver_decode', 'interleaver_decode_soft',
    'interleaver_destroy', 'interleaver_encode',
    'interleaver_encode_soft', 'interleaver_print',
    'interleaver_set_depth', 'kaiser_beta_As', 'liquid_MarcumQ1f',
    'liquid_MarcumQf', 'liquid_Qf', 'liquid_ampmodem_type',
    'liquid_ampmodem_type__enumvalues', 'liquid_bdotprod',
    'liquid_besseli0f', 'liquid_besselif', 'liquid_besselj0f',
    'liquid_besseljf', 'liquid_blackmanharris',
    'liquid_blackmanharris7', 'liquid_compander_type',
    'liquid_compander_type__enumvalues', 'liquid_count_leading_zeros',
    'liquid_count_ones', 'liquid_count_ones_mod2',
    'liquid_cpfsk_filter', 'liquid_cpfsk_filter__enumvalues',
    'liquid_double_complex', 'liquid_error_code',
    'liquid_error_code__enumvalues', 'liquid_error_info',
    'liquid_error_str', 'liquid_factor', 'liquid_factorialf',
    'liquid_fft_type', 'liquid_fft_type__enumvalues',
    'liquid_filter_autocorr', 'liquid_filter_crosscorr',
    'liquid_filter_energy', 'liquid_filter_isi',
    'liquid_firdes_arkaiser', 'liquid_firdes_doppler',
    'liquid_firdes_farcsech', 'liquid_firdes_fexp',
    'liquid_firdes_fsech', 'liquid_firdes_gmskrx',
    'liquid_firdes_gmsktx', 'liquid_firdes_hM3',
    'liquid_firdes_kaiser', 'liquid_firdes_notch',
    'liquid_firdes_prototype', 'liquid_firdes_rcos',
    'liquid_firdes_rfarcsech', 'liquid_firdes_rfexp',
    'liquid_firdes_rfsech', 'liquid_firdes_rkaiser',
    'liquid_firdes_rrcos', 'liquid_firdespm_btype',
    'liquid_firdespm_btype__enumvalues', 'liquid_firdespm_wtype',
    'liquid_firdespm_wtype__enumvalues', 'liquid_firfilt_type',
    'liquid_firfilt_type__enumvalues', 'liquid_firfilt_type_str',
    'liquid_flattop', 'liquid_float_complex', 'liquid_gammaf',
    'liquid_gcd', 'liquid_get_scale', 'liquid_getopt_str2crc',
    'liquid_getopt_str2fec', 'liquid_getopt_str2firfilt',
    'liquid_getopt_str2mod', 'liquid_getopt_str2window',
    'liquid_hamming', 'liquid_hann', 'liquid_iirdes',
    'liquid_iirdes_bandtype', 'liquid_iirdes_bandtype__enumvalues',
    'liquid_iirdes_filtertype',
    'liquid_iirdes_filtertype__enumvalues', 'liquid_iirdes_format',
    'liquid_iirdes_format__enumvalues', 'liquid_invgauss',
    'liquid_is_prime', 'liquid_kaiser', 'liquid_kbd',
    'liquid_kbd_window', 'liquid_lbcircshift', 'liquid_lbshift',
    'liquid_lcircshift', 'liquid_levinson', 'liquid_libversion',
    'liquid_libversion_number', 'liquid_lnbesselif',
    'liquid_lngammaf', 'liquid_lnlowergammaf', 'liquid_lnuppergammaf',
    'liquid_lowergammaf', 'liquid_lpc', 'liquid_lshift',
    'liquid_modem_is_apsk', 'liquid_modem_is_ask',
    'liquid_modem_is_dpsk', 'liquid_modem_is_psk',
    'liquid_modem_is_qam', 'liquid_modpow', 'liquid_msb_index',
    'liquid_multimodal', 'liquid_nchoosek', 'liquid_ncotype',
    'liquid_ncotype__enumvalues', 'liquid_nextpow2',
    'liquid_pack_array', 'liquid_pack_bytes', 'liquid_pack_soft_bits',
    'liquid_primitive_root', 'liquid_primitive_root_prime',
    'liquid_print_bitstring', 'liquid_print_crc_schemes',
    'liquid_print_fec_schemes', 'liquid_print_modulation_schemes',
    'liquid_print_windows', 'liquid_rbcircshift', 'liquid_rbshift',
    'liquid_rcircshift', 'liquid_rcostaper_window',
    'liquid_repack_bytes', 'liquid_resamp_type',
    'liquid_resamp_type__enumvalues', 'liquid_reverse_byte',
    'liquid_reverse_uint16', 'liquid_reverse_uint24',
    'liquid_reverse_uint32', 'liquid_rosenbrock', 'liquid_rshift',
    'liquid_spiral', 'liquid_sumsqcf', 'liquid_sumsqf',
    'liquid_totient', 'liquid_triangular', 'liquid_unique_factor',
    'liquid_unpack_array', 'liquid_unpack_bytes',
    'liquid_unpack_soft_bits', 'liquid_unwrap_phase',
    'liquid_unwrap_phase2', 'liquid_uppergammaf',
    'liquid_vectorcf_abs', 'liquid_vectorcf_add',
    'liquid_vectorcf_addscalar', 'liquid_vectorcf_carg',
    'liquid_vectorcf_cexpj', #'liquid_vectorcf_init',
    'liquid_vectorcf_mul', 'liquid_vectorcf_mulscalar',
    'liquid_vectorcf_norm', 'liquid_vectorcf_normalize',
    #'liquid_vectorcf_pnorm', 
    #'liquid_vectorcf_sumsq',
    'liquid_vectorf_abs', 'liquid_vectorf_add',
    'liquid_vectorf_addscalar', 'liquid_vectorf_carg',
    'liquid_vectorf_cexpj', #'liquid_vectorf_init',
    'liquid_vectorf_mul', 'liquid_vectorf_mulscalar',
    'liquid_vectorf_norm', 'liquid_vectorf_normalize',
    #'liquid_vectorf_pnorm', 'liquid_vectorf_sumsq', 
    'liquid_version',
    'liquid_window_str', 'liquid_window_type',
    'liquid_window_type__enumvalues', 'liquid_windowf', 'matrix_add',
    'matrix_aug', 'matrix_cgsolve', 'matrix_chol', 'matrix_det',
    'matrix_div', 'matrix_eye', 'matrix_gjelim', 'matrix_gramschmidt',
    'matrix_hermitian', 'matrix_hermitian_mul', 'matrix_inv',
    'matrix_linsolve', 'matrix_ludecomp_crout',
    'matrix_ludecomp_doolittle', 'matrix_mul', 'matrix_mul_hermitian',
    'matrix_mul_transpose', 'matrix_ones', 'matrix_pdiv',
    'matrix_pivot', 'matrix_pmul', 'matrix_print',
    'matrix_qrdecomp_gramschmidt', 'matrix_sub', 'matrix_swaprows',
    'matrix_trans', 'matrix_transpose_mul', 'matrix_zeros',
    'matrixc_add', 'matrixc_aug', 'matrixc_cgsolve', 'matrixc_chol',
    'matrixc_det', 'matrixc_div', 'matrixc_eye', 'matrixc_gjelim',
    'matrixc_gramschmidt', 'matrixc_hermitian',
    'matrixc_hermitian_mul', 'matrixc_inv', 'matrixc_linsolve',
    'matrixc_ludecomp_crout', 'matrixc_ludecomp_doolittle',
    'matrixc_mul', 'matrixc_mul_hermitian', 'matrixc_mul_transpose',
    'matrixc_ones', 'matrixc_pdiv', 'matrixc_pivot', 'matrixc_pmul',
    'matrixc_print', 'matrixc_qrdecomp_gramschmidt', 'matrixc_sub',
    'matrixc_swaprows', 'matrixc_trans', 'matrixc_transpose_mul',
    'matrixc_zeros', 'matrixcf_add', 'matrixcf_aug',
    'matrixcf_cgsolve', 'matrixcf_chol', 'matrixcf_det',
    'matrixcf_div', 'matrixcf_eye', 'matrixcf_gjelim',
    'matrixcf_gramschmidt', 'matrixcf_hermitian',
    'matrixcf_hermitian_mul', 'matrixcf_inv', 'matrixcf_linsolve',
    'matrixcf_ludecomp_crout', 'matrixcf_ludecomp_doolittle',
    'matrixcf_mul', 'matrixcf_mul_hermitian',
    'matrixcf_mul_transpose', 'matrixcf_ones', 'matrixcf_pdiv',
    'matrixcf_pivot', 'matrixcf_pmul', 'matrixcf_print',
    'matrixcf_qrdecomp_gramschmidt', 'matrixcf_sub',
    'matrixcf_swaprows', 'matrixcf_trans', 'matrixcf_transpose_mul',
    'matrixcf_zeros', 'matrixf_add', 'matrixf_aug', 'matrixf_cgsolve',
    'matrixf_chol', 'matrixf_det', 'matrixf_div', 'matrixf_eye',
    'matrixf_gjelim', 'matrixf_gramschmidt', 'matrixf_hermitian',
    'matrixf_hermitian_mul', 'matrixf_inv', 'matrixf_linsolve',
    'matrixf_ludecomp_crout', 'matrixf_ludecomp_doolittle',
    'matrixf_mul', 'matrixf_mul_hermitian', 'matrixf_mul_transpose',
    'matrixf_ones', 'matrixf_pdiv', 'matrixf_pivot', 'matrixf_pmul',
    'matrixf_print', 'matrixf_qrdecomp_gramschmidt', 'matrixf_sub',
    'matrixf_swaprows', 'matrixf_trans', 'matrixf_transpose_mul',
    'matrixf_zeros', 'modem', 'modem_create',
    'modem_create_arbitrary', 'modem_demodulate',
    'modem_demodulate_soft', 'modem_destroy', 'modem_gen_rand_sym',
    'modem_get_bps', 'modem_get_demodulator_evm',
    'modem_get_demodulator_phase_error',
    'modem_get_demodulator_sample', 'modem_get_scheme',
    'modem_modulate', 'modem_print', 'modem_recreate', 'modem_reset',
    'modulation_scheme', 'modulation_scheme__enumvalues',
    'modulation_types', 'msequence', 'msequence_advance',
    'msequence_create', 'msequence_create_default',
    'msequence_create_genpoly', 'msequence_destroy',
    'msequence_generate_symbol', 'msequence_get_length',
    'msequence_get_state', 'msequence_print', 'msequence_reset',
    'msequence_set_state', 'msourcecf', 'msourcecf_add_chirp',
    'msourcecf_add_fsk', 'msourcecf_add_gmsk', 'msourcecf_add_modem',
    'msourcecf_add_noise', 'msourcecf_add_tone', 'msourcecf_add_user',
    'msourcecf_callback', 'msourcecf_create',
    'msourcecf_create_default', 'msourcecf_destroy',
    'msourcecf_disable', 'msourcecf_enable',
    'msourcecf_get_frequency', 'msourcecf_get_gain',
    'msourcecf_get_num_samples', 'msourcecf_print',
    'msourcecf_remove', 'msourcecf_reset', 'msourcecf_set_frequency',
    'msourcecf_set_gain', 'msourcecf_write_samples', 'msresamp2_cccf',
    'msresamp2_cccf_create', 'msresamp2_cccf_destroy',
    'msresamp2_cccf_execute', 'msresamp2_cccf_get_delay',
    'msresamp2_cccf_get_num_stages', 'msresamp2_cccf_get_rate',
    'msresamp2_cccf_get_type', 'msresamp2_cccf_print',
    'msresamp2_cccf_reset', 'msresamp2_crcf', 'msresamp2_crcf_create',
    'msresamp2_crcf_destroy', 'msresamp2_crcf_execute',
    'msresamp2_crcf_get_delay', 'msresamp2_crcf_get_num_stages',
    'msresamp2_crcf_get_rate', 'msresamp2_crcf_get_type',
    'msresamp2_crcf_print', 'msresamp2_crcf_reset', 'msresamp2_rrrf',
    'msresamp2_rrrf_create', 'msresamp2_rrrf_destroy',
    'msresamp2_rrrf_execute', 'msresamp2_rrrf_get_delay',
    'msresamp2_rrrf_get_num_stages', 'msresamp2_rrrf_get_rate',
    'msresamp2_rrrf_get_type', 'msresamp2_rrrf_print',
    'msresamp2_rrrf_reset', 'msresamp_cccf', 'msresamp_cccf_create',
    'msresamp_cccf_destroy', 'msresamp_cccf_execute',
    'msresamp_cccf_get_delay', 'msresamp_cccf_get_rate',
    'msresamp_cccf_print', 'msresamp_cccf_reset', 'msresamp_crcf',
    'msresamp_crcf_create', 'msresamp_crcf_destroy',
    'msresamp_crcf_execute', 'msresamp_crcf_get_delay',
    'msresamp_crcf_get_rate', 'msresamp_crcf_print',
    'msresamp_crcf_reset', 'msresamp_rrrf', 'msresamp_rrrf_create',
    'msresamp_rrrf_destroy', 'msresamp_rrrf_execute',
    'msresamp_rrrf_get_delay', 'msresamp_rrrf_get_rate',
    'msresamp_rrrf_print', 'msresamp_rrrf_reset', 'nco_crcf',
    'nco_crcf_adjust_frequency', 'nco_crcf_adjust_phase',
    'nco_crcf_cexpf', 'nco_crcf_cos', 'nco_crcf_create',
    'nco_crcf_destroy', 'nco_crcf_get_frequency',
    'nco_crcf_get_phase', 'nco_crcf_mix_block_down',
    'nco_crcf_mix_block_up', 'nco_crcf_mix_down', 'nco_crcf_mix_up',
    'nco_crcf_pll_set_bandwidth', 'nco_crcf_pll_step',
    'nco_crcf_print', 'nco_crcf_reset', 'nco_crcf_set_frequency',
    'nco_crcf_set_phase', 'nco_crcf_sin', 'nco_crcf_sincos',
    'nco_crcf_step', 'ofdmflexframegen', 'ofdmflexframegen_assemble',
    'ofdmflexframegen_create', 'ofdmflexframegen_destroy',
    'ofdmflexframegen_getframelen', 'ofdmflexframegen_getprops',
    'ofdmflexframegen_is_assembled', 'ofdmflexframegen_print',
    'ofdmflexframegen_reset', 'ofdmflexframegen_set_header_len',
    'ofdmflexframegen_set_header_props', 'ofdmflexframegen_setprops',
    'ofdmflexframegen_write', 'ofdmflexframegenprops_init_default',
    'ofdmflexframegenprops_s', 'ofdmflexframesync',
    'ofdmflexframesync_create', 'ofdmflexframesync_debug_disable',
    'ofdmflexframesync_debug_enable', 'ofdmflexframesync_debug_print',
    'ofdmflexframesync_decode_header_soft',
    'ofdmflexframesync_decode_payload_soft',
    'ofdmflexframesync_destroy', 'ofdmflexframesync_execute',
    'ofdmflexframesync_get_cfo',
    'ofdmflexframesync_get_framedatastats',
    'ofdmflexframesync_get_rssi', 'ofdmflexframesync_is_frame_open',
    'ofdmflexframesync_print', 'ofdmflexframesync_reset',
    'ofdmflexframesync_reset_framedatastats',
    'ofdmflexframesync_set_cfo', 'ofdmflexframesync_set_header_len',
    'ofdmflexframesync_set_header_props',
    'ofdmframe_init_default_sctype', 'ofdmframe_init_sctype_range',
    'ofdmframe_print_sctype', 'ofdmframe_validate_sctype',
    'ofdmframegen', 'ofdmframegen_create', 'ofdmframegen_destroy',
    'ofdmframegen_print', 'ofdmframegen_reset',
    'ofdmframegen_write_S0a', 'ofdmframegen_write_S0b',
    'ofdmframegen_write_S1', 'ofdmframegen_writesymbol',
    'ofdmframegen_writetail', 'ofdmframesync',
    'ofdmframesync_callback', 'ofdmframesync_create',
    'ofdmframesync_debug_disable', 'ofdmframesync_debug_enable',
    'ofdmframesync_debug_print', 'ofdmframesync_destroy',
    'ofdmframesync_execute', 'ofdmframesync_get_cfo',
    'ofdmframesync_get_rssi', 'ofdmframesync_is_frame_open',
    'ofdmframesync_print', 'ofdmframesync_reset',
    'ofdmframesync_set_cfo', 'ordfilt_rrrf', 'ordfilt_rrrf_create',
    'ordfilt_rrrf_create_medfilt', 'ordfilt_rrrf_destroy',
    'ordfilt_rrrf_execute', 'ordfilt_rrrf_execute_block',
    'ordfilt_rrrf_print', 'ordfilt_rrrf_push', 'ordfilt_rrrf_reset',
    'ordfilt_rrrf_write', 'packetizer',
    'packetizer_compute_dec_msg_len',
    'packetizer_compute_enc_msg_len', 'packetizer_create',
    'packetizer_decode', 'packetizer_decode_soft',
    'packetizer_destroy', 'packetizer_encode', 'packetizer_get_crc',
    'packetizer_get_dec_msg_len', 'packetizer_get_enc_msg_len',
    'packetizer_get_fec0', 'packetizer_get_fec1', 'packetizer_print',
    'packetizer_recreate', 'poly_expandbinomial',
    'poly_expandbinomial_pm', 'poly_expandroots', 'poly_expandroots2',
    'poly_findroots', #'poly_findroots_bairstow',
    #'poly_findroots_durandkerner', 
    'poly_fit', 'poly_fit_lagrange',
    'poly_fit_lagrange_barycentric', 'poly_interp_lagrange',
    'poly_mul', 'poly_val', 'poly_val_lagrange_barycentric',
    'polyc_expandbinomial', 'polyc_expandbinomial_pm',
    'polyc_expandroots', 'polyc_expandroots2', 'polyc_findroots',
    #'polyc_findroots_bairstow', 'polyc_findroots_durandkerner',
    'polyc_fit', 'polyc_fit_lagrange',
    'polyc_fit_lagrange_barycentric', 'polyc_interp_lagrange',
    'polyc_mul', 'polyc_val', 'polyc_val_lagrange_barycentric',
    'polycf_expandbinomial', 'polycf_expandbinomial_pm',
    'polycf_expandroots', 'polycf_expandroots2', 'polycf_findroots',
    #'polycf_findroots_bairstow', 'polycf_findroots_durandkerner',
    'polycf_fit', 'polycf_fit_lagrange',
    'polycf_fit_lagrange_barycentric', 'polycf_interp_lagrange',
    'polycf_mul', 'polycf_val', 'polycf_val_lagrange_barycentric',
    'polyf_expandbinomial', 'polyf_expandbinomial_pm',
    'polyf_expandroots', 'polyf_expandroots2', 'polyf_findroots',
    #'polyf_findroots_bairstow', 'polyf_findroots_durandkerner',
    'polyf_fit', 'polyf_fit_lagrange',
    'polyf_fit_lagrange_barycentric', 'polyf_interp_lagrange',
    'polyf_mul', 'polyf_val', 'polyf_val_lagrange_barycentric',
    'presync_cccf', 'presync_cccf_create', 'presync_cccf_destroy',
    'presync_cccf_execute', 'presync_cccf_print', 'presync_cccf_push',
    'presync_cccf_reset', 'qdetector_cccf', 'qdetector_cccf_create',
    'qdetector_cccf_create_cpfsk', 'qdetector_cccf_create_gmsk',
    'qdetector_cccf_create_linear', 'qdetector_cccf_destroy',
    'qdetector_cccf_execute', 'qdetector_cccf_get_buf_len',
    'qdetector_cccf_get_dphi', 'qdetector_cccf_get_gamma',
    'qdetector_cccf_get_phi', 'qdetector_cccf_get_rxy',
    'qdetector_cccf_get_seq_len', 'qdetector_cccf_get_sequence',
    'qdetector_cccf_get_tau', 'qdetector_cccf_print',
    'qdetector_cccf_reset', 'qdetector_cccf_set_range',
    'qdetector_cccf_set_threshold', 
    #'qnsearch', 'qnsearch_create',
    #'qnsearch_destroy', 'qnsearch_execute', 'qnsearch_print',
    #'qnsearch_reset', 'qnsearch_step', 
    'qpacketmodem',
    'qpacketmodem_configure', 'qpacketmodem_create',
    'qpacketmodem_decode', 'qpacketmodem_decode_bits',
    'qpacketmodem_decode_soft', 'qpacketmodem_decode_soft_payload',
    'qpacketmodem_decode_soft_sym', 'qpacketmodem_decode_syms',
    'qpacketmodem_destroy', 'qpacketmodem_encode',
    'qpacketmodem_encode_syms', 'qpacketmodem_get_crc',
    'qpacketmodem_get_demodulator_evm',
    'qpacketmodem_get_demodulator_phase_error',
    'qpacketmodem_get_fec0', 'qpacketmodem_get_fec1',
    'qpacketmodem_get_frame_len', 'qpacketmodem_get_modscheme',
    'qpacketmodem_get_payload_len', 'qpacketmodem_print',
    'qpacketmodem_reset', 'qpilot_frame_len', 'qpilot_num_pilots',
    'qpilotgen', 'qpilotgen_create', 'qpilotgen_destroy',
    'qpilotgen_execute', 'qpilotgen_get_frame_len', 'qpilotgen_print',
    'qpilotgen_recreate', 'qpilotgen_reset', 'qpilotsync',
    'qpilotsync_create', 'qpilotsync_destroy', 'qpilotsync_execute',
    'qpilotsync_get_dphi', 'qpilotsync_get_evm',
    'qpilotsync_get_frame_len', 'qpilotsync_get_gain',
    'qpilotsync_get_phi', 'qpilotsync_print', 'qpilotsync_recreate',
    'qpilotsync_reset', 'quantize_adc', 'quantize_dac', 'quantizercf',
    'quantizercf_create', 'quantizercf_destroy',
    'quantizercf_execute_adc', 'quantizercf_execute_dac',
    'quantizercf_print', 'quantizerf', 'quantizerf_create',
    'quantizerf_destroy', 'quantizerf_execute_adc',
    'quantizerf_execute_dac', 'quantizerf_print', 'randexpf',
    'randexpf_cdf', 'randexpf_pdf', 'randf', 'randf_cdf', 'randf_pdf',
    'randgammaf', 'randgammaf_cdf', 'randgammaf_pdf', 'randnakmf',
    'randnakmf_cdf', 'randnakmf_pdf', 'randnf', 'randnf_cdf',
    'randnf_pdf', 'randricekf', 'randricekf_cdf', 'randricekf_pdf',
    'randuf', 'randuf_cdf', 'randuf_pdf', 'randweibf',
    'randweibf_cdf', 'randweibf_pdf', 'resamp2_cccf',
    'resamp2_cccf_analyzer_execute', 'resamp2_cccf_create',
    'resamp2_cccf_decim_execute', 'resamp2_cccf_destroy',
    'resamp2_cccf_filter_execute', 'resamp2_cccf_get_delay',
    'resamp2_cccf_interp_execute', 'resamp2_cccf_print',
    'resamp2_cccf_recreate', 'resamp2_cccf_reset',
    'resamp2_cccf_synthesizer_execute', 'resamp2_crcf',
    'resamp2_crcf_analyzer_execute', 'resamp2_crcf_create',
    'resamp2_crcf_decim_execute', 'resamp2_crcf_destroy',
    'resamp2_crcf_filter_execute', 'resamp2_crcf_get_delay',
    'resamp2_crcf_interp_execute', 'resamp2_crcf_print',
    'resamp2_crcf_recreate', 'resamp2_crcf_reset',
    'resamp2_crcf_synthesizer_execute', 'resamp2_rrrf',
    'resamp2_rrrf_analyzer_execute', 'resamp2_rrrf_create',
    'resamp2_rrrf_decim_execute', 'resamp2_rrrf_destroy',
    'resamp2_rrrf_filter_execute', 'resamp2_rrrf_get_delay',
    'resamp2_rrrf_interp_execute', 'resamp2_rrrf_print',
    'resamp2_rrrf_recreate', 'resamp2_rrrf_reset',
    'resamp2_rrrf_synthesizer_execute', 'resamp_cccf',
    'resamp_cccf_adjust_rate', 'resamp_cccf_adjust_timing_phase',
    'resamp_cccf_create', 'resamp_cccf_create_default',
    'resamp_cccf_destroy', 'resamp_cccf_execute',
    'resamp_cccf_execute_block', 'resamp_cccf_get_delay',
    'resamp_cccf_get_rate', 'resamp_cccf_print', 'resamp_cccf_reset',
    'resamp_cccf_set_rate', 'resamp_cccf_set_timing_phase',
    'resamp_crcf', 'resamp_crcf_adjust_rate',
    'resamp_crcf_adjust_timing_phase', 'resamp_crcf_create',
    'resamp_crcf_create_default', 'resamp_crcf_destroy',
    'resamp_crcf_execute', 'resamp_crcf_execute_block',
    'resamp_crcf_get_delay', 'resamp_crcf_get_rate',
    'resamp_crcf_print', 'resamp_crcf_reset', 'resamp_crcf_set_rate',
    'resamp_crcf_set_timing_phase', 'resamp_rrrf',
    'resamp_rrrf_adjust_rate', 'resamp_rrrf_adjust_timing_phase',
    'resamp_rrrf_create', 'resamp_rrrf_create_default',
    'resamp_rrrf_destroy', 'resamp_rrrf_execute',
    'resamp_rrrf_execute_block', 'resamp_rrrf_get_delay',
    'resamp_rrrf_get_rate', 'resamp_rrrf_print', 'resamp_rrrf_reset',
    'resamp_rrrf_set_rate', 'resamp_rrrf_set_timing_phase',
    'rresamp_cccf', 'rresamp_cccf_create',
    'rresamp_cccf_create_default', 'rresamp_cccf_create_kaiser',
    'rresamp_cccf_create_prototype', 'rresamp_cccf_destroy',
    'rresamp_cccf_execute', 'rresamp_cccf_execute_block',
    'rresamp_cccf_get_P', 'rresamp_cccf_get_Q',
    'rresamp_cccf_get_block_len', 'rresamp_cccf_get_decim',
    'rresamp_cccf_get_delay', 'rresamp_cccf_get_interp',
    'rresamp_cccf_get_rate', 'rresamp_cccf_get_scale',
    'rresamp_cccf_print', 'rresamp_cccf_reset',
    'rresamp_cccf_set_scale', 'rresamp_cccf_write', 'rresamp_crcf',
    'rresamp_crcf_create', 'rresamp_crcf_create_default',
    'rresamp_crcf_create_kaiser', 'rresamp_crcf_create_prototype',
    'rresamp_crcf_destroy', 'rresamp_crcf_execute',
    'rresamp_crcf_execute_block', 'rresamp_crcf_get_P',
    'rresamp_crcf_get_Q', 'rresamp_crcf_get_block_len',
    'rresamp_crcf_get_decim', 'rresamp_crcf_get_delay',
    'rresamp_crcf_get_interp', 'rresamp_crcf_get_rate',
    'rresamp_crcf_get_scale', 'rresamp_crcf_print',
    'rresamp_crcf_reset', 'rresamp_crcf_set_scale',
    'rresamp_crcf_write', 'rresamp_rrrf', 'rresamp_rrrf_create',
    'rresamp_rrrf_create_default', 'rresamp_rrrf_create_kaiser',
    'rresamp_rrrf_create_prototype', 'rresamp_rrrf_destroy',
    'rresamp_rrrf_execute', 'rresamp_rrrf_execute_block',
    'rresamp_rrrf_get_P', 'rresamp_rrrf_get_Q',
    'rresamp_rrrf_get_block_len', 'rresamp_rrrf_get_decim',
    'rresamp_rrrf_get_delay', 'rresamp_rrrf_get_interp',
    'rresamp_rrrf_get_rate', 'rresamp_rrrf_get_scale',
    'rresamp_rrrf_print', 'rresamp_rrrf_reset',
    'rresamp_rrrf_set_scale', 'rresamp_rrrf_write', 'scramble_data',
    'sincf', 'smatrixb', 'smatrixb_clear', 'smatrixb_create',
    'smatrixb_create_array', 'smatrixb_delete', 'smatrixb_destroy',
    'smatrixb_eye', 'smatrixb_get', 'smatrixb_insert',
    'smatrixb_isset', 'smatrixb_mul', 'smatrixb_mulf',
    'smatrixb_print', 'smatrixb_print_expanded', 'smatrixb_reset',
    'smatrixb_set', 'smatrixb_size', 'smatrixb_vmul',
    'smatrixb_vmulf', 'smatrixf', 'smatrixf_clear', 'smatrixf_create',
    'smatrixf_create_array', 'smatrixf_delete', 'smatrixf_destroy',
    'smatrixf_eye', 'smatrixf_get', 'smatrixf_insert',
    'smatrixf_isset', 'smatrixf_mul', 'smatrixf_print',
    'smatrixf_print_expanded', 'smatrixf_reset', 'smatrixf_set',
    'smatrixf_size', 'smatrixf_vmul', 'smatrixi', 'smatrixi_clear',
    'smatrixi_create', 'smatrixi_create_array', 'smatrixi_delete',
    'smatrixi_destroy', 'smatrixi_eye', 'smatrixi_get',
    'smatrixi_insert', 'smatrixi_isset', 'smatrixi_mul',
    'smatrixi_print', 'smatrixi_print_expanded', 'smatrixi_reset',
    'smatrixi_set', 'smatrixi_size', 'smatrixi_vmul', 'spgramcf',
    'spgramcf_clear', 'spgramcf_create', 'spgramcf_create_default',
    'spgramcf_destroy', 'spgramcf_estimate_psd',
    'spgramcf_export_gnuplot', 'spgramcf_get_alpha',
    'spgramcf_get_delay', 'spgramcf_get_nfft',
    'spgramcf_get_num_samples', 'spgramcf_get_num_samples_total',
    'spgramcf_get_num_transforms',
    'spgramcf_get_num_transforms_total', 'spgramcf_get_psd',
    'spgramcf_get_psd_mag', 'spgramcf_get_window_len',
    'spgramcf_get_wtype', 'spgramcf_print', 'spgramcf_push',
    'spgramcf_reset', 'spgramcf_set_alpha', 'spgramcf_set_freq',
    'spgramcf_set_rate', 'spgramcf_write', 'spgramf', 'spgramf_clear',
    'spgramf_create', 'spgramf_create_default', 'spgramf_destroy',
    'spgramf_estimate_psd', 'spgramf_export_gnuplot',
    'spgramf_get_alpha', 'spgramf_get_delay', 'spgramf_get_nfft',
    'spgramf_get_num_samples', 'spgramf_get_num_samples_total',
    'spgramf_get_num_transforms', 'spgramf_get_num_transforms_total',
    'spgramf_get_psd', 'spgramf_get_psd_mag',
    'spgramf_get_window_len', 'spgramf_get_wtype', 'spgramf_print',
    'spgramf_push', 'spgramf_reset', 'spgramf_set_alpha',
    'spgramf_set_freq', 'spgramf_set_rate', 'spgramf_write',
    'spwaterfallcf', 'spwaterfallcf_clear', 'spwaterfallcf_create',
    'spwaterfallcf_create_default', 'spwaterfallcf_destroy',
    'spwaterfallcf_export', 'spwaterfallcf_get_delay',
    'spwaterfallcf_get_num_freq',
    'spwaterfallcf_get_num_samples_total',
    'spwaterfallcf_get_num_time', 'spwaterfallcf_get_psd',
    'spwaterfallcf_get_window_len', 'spwaterfallcf_get_wtype',
    'spwaterfallcf_print', 'spwaterfallcf_push',
    'spwaterfallcf_reset', 'spwaterfallcf_set_commands',
    'spwaterfallcf_set_dims', 'spwaterfallcf_set_freq',
    'spwaterfallcf_set_rate', 'spwaterfallcf_write', 'spwaterfallf',
    'spwaterfallf_clear', 'spwaterfallf_create',
    'spwaterfallf_create_default', 'spwaterfallf_destroy',
    'spwaterfallf_export', 'spwaterfallf_get_delay',
    'spwaterfallf_get_num_freq', 'spwaterfallf_get_num_samples_total',
    'spwaterfallf_get_num_time', 'spwaterfallf_get_psd',
    'spwaterfallf_get_window_len', 'spwaterfallf_get_wtype',
    'spwaterfallf_print', 'spwaterfallf_push', 'spwaterfallf_reset',
    'spwaterfallf_set_commands', 'spwaterfallf_set_dims',
    'spwaterfallf_set_freq', 'spwaterfallf_set_rate',
    'spwaterfallf_write', 'struct_agc_crcf_s', 'struct_agc_rrrf_s',
    'struct_ampmodem_s', 'struct_asgramcf_s', 'struct_asgramf_s',
    'struct_autocorr_cccf_s', 'struct_autocorr_rrrf_s',
    'struct_bpacketgen_s', 'struct_bpacketsync_s',
    'struct_bpresync_cccf_s', 'struct_bsequence_s',
    'struct_bsync_cccf_s', 'struct_bsync_crcf_s',
    'struct_bsync_rrrf_s', 'struct_c__SA_dsssframegenprops_s',
    'struct_c__SA_flexframegenprops_s',
    'struct_c__SA_framedatastats_s', 'struct_c__SA_framesyncstats_s',
    'struct_c__SA_liquid_double_complex',
    'struct_c__SA_liquid_float_complex',
    'struct_c__SA_ofdmflexframegenprops_s', 'struct_cbuffercf_s',
    'struct_cbufferf_s', 'struct_channel_cccf_s',
    'struct_chromosome_s', 'struct_cpfskdem_s', 'struct_cpfskmod_s',
    'struct_cvsd_s', 'struct_dds_cccf_s', 'struct_detector_cccf_s',
    'struct_dotprod_cccf_s', 'struct_dotprod_crcf_s',
    'struct_dotprod_rrrf_s', 'struct_dsssframegen_s',
    'struct_dsssframesync_s', 'struct_eqlms_cccf_s',
    'struct_eqlms_rrrf_s', 'struct_eqrls_cccf_s',
    'struct_eqrls_rrrf_s', 'struct_fec_s', 'struct_fftfilt_cccf_s',
    'struct_fftfilt_crcf_s', 'struct_fftfilt_rrrf_s',
    'struct_fftplan_s', 'struct_firdecim_cccf_s',
    'struct_firdecim_crcf_s', 'struct_firdecim_rrrf_s',
    'struct_firdespm_s', 'struct_firfarrow_crcf_s',
    'struct_firfarrow_rrrf_s', 'struct_firfilt_cccf_s',
    'struct_firfilt_crcf_s', 'struct_firfilt_rrrf_s',
    'struct_firhilbf_s', 'struct_firinterp_cccf_s',
    'struct_firinterp_crcf_s', 'struct_firinterp_rrrf_s',
    'struct_firpfb_cccf_s', 'struct_firpfb_crcf_s',
    'struct_firpfb_rrrf_s', 'struct_firpfbch2_crcf_s',
    'struct_firpfbch_cccf_s', 'struct_firpfbch_crcf_s',
    'struct_firpfbchr_crcf_s', 'struct_flexframegen_s',
    'struct_flexframesync_s', 'struct_framegen64_s',
    'struct_framesync64_s', 'struct_freqdem_s', 'struct_freqmod_s',
    'struct_fskdem_s', 'struct_fskframegen_s',
    'struct_fskframesync_s', 'struct_fskmod_s', 'struct_gasearch_s',
    'struct_gmskdem_s', 'struct_gmskframegen_s',
    'struct_gmskframesync_s', 'struct_gmskmod_s',
    'struct_gradsearch_s', 'struct_iirdecim_cccf_s',
    'struct_iirdecim_crcf_s', 'struct_iirdecim_rrrf_s',
    'struct_iirfilt_cccf_s', 'struct_iirfilt_crcf_s',
    'struct_iirfilt_rrrf_s', 'struct_iirfiltsos_cccf_s',
    'struct_iirfiltsos_crcf_s', 'struct_iirfiltsos_rrrf_s',
    'struct_iirhilbf_s', 'struct_iirinterp_cccf_s',
    'struct_iirinterp_crcf_s', 'struct_iirinterp_rrrf_s',
    'struct_interleaver_s', 'struct_modem_s',
    'struct_modulation_type_s', 'struct_msequence_s',
    'struct_msourcecf_s', 'struct_msresamp2_cccf_s',
    'struct_msresamp2_crcf_s', 'struct_msresamp2_rrrf_s',
    'struct_msresamp_cccf_s', 'struct_msresamp_crcf_s',
    'struct_msresamp_rrrf_s', 'struct_nco_crcf_s',
    'struct_ofdmflexframegen_s', 'struct_ofdmflexframesync_s',
    'struct_ofdmframegen_s', 'struct_ofdmframesync_s',
    'struct_ordfilt_rrrf_s', 'struct_packetizer_s',
    'struct_presync_cccf_s', 'struct_qdetector_cccf_s',
    #'struct_qnsearch_s', 
    'struct_qpacketmodem_s',
    'struct_qpilotgen_s', 'struct_qpilotsync_s',
    'struct_quantizercf_s', 'struct_quantizerf_s',
    'struct_resamp2_cccf_s', 'struct_resamp2_crcf_s',
    'struct_resamp2_rrrf_s', 'struct_resamp_cccf_s',
    'struct_resamp_crcf_s', 'struct_resamp_rrrf_s',
    'struct_rresamp_cccf_s', 'struct_rresamp_crcf_s',
    'struct_rresamp_rrrf_s', 'struct_smatrixb_s', 'struct_smatrixf_s',
    'struct_smatrixi_s', 'struct_spgramcf_s', 'struct_spgramf_s',
    'struct_spwaterfallcf_s', 'struct_spwaterfallf_s',
    'struct_symstreamcf_s', 'struct_symstreamrcf_s',
    'struct_symsync_crcf_s', 'struct_symsync_rrrf_s',
    'struct_symtrack_cccf_s', #'struct_symtrack_rrrf_s',
    'struct_synth_crcf_s', 'struct_tvmpch_cccf_s',
    'struct_wdelaycf_s', 'struct_wdelayf_s', 'struct_windowcf_s',
    'struct_windowf_s', 'symstreamcf', 'symstreamcf_create',
    'symstreamcf_create_linear', 'symstreamcf_destroy',
    'symstreamcf_get_gain', 'symstreamcf_get_scheme',
    'symstreamcf_print', 'symstreamcf_reset', 'symstreamcf_set_gain',
    'symstreamcf_set_scheme', 'symstreamcf_write_samples',
    'symstreamrcf', 'symstreamrcf_create',
    'symstreamrcf_create_linear', 'symstreamrcf_destroy',
    'symstreamrcf_get_gain', 'symstreamrcf_get_scheme',
    'symstreamrcf_print', 'symstreamrcf_reset',
    'symstreamrcf_set_gain', 'symstreamrcf_set_scheme',
    'symstreamrcf_write_samples', 'symsync_crcf',
    'symsync_crcf_create', 'symsync_crcf_create_kaiser',
    'symsync_crcf_create_rnyquist', 'symsync_crcf_destroy',
    'symsync_crcf_execute', 'symsync_crcf_get_tau',
    'symsync_crcf_lock', 'symsync_crcf_print', 'symsync_crcf_reset',
    'symsync_crcf_set_lf_bw', 'symsync_crcf_set_output_rate',
    'symsync_crcf_unlock', 'symsync_rrrf', 'symsync_rrrf_create',
    'symsync_rrrf_create_kaiser', 'symsync_rrrf_create_rnyquist',
    'symsync_rrrf_destroy', 'symsync_rrrf_execute',
    'symsync_rrrf_get_tau', 'symsync_rrrf_lock', 'symsync_rrrf_print',
    'symsync_rrrf_reset', 'symsync_rrrf_set_lf_bw',
    'symsync_rrrf_set_output_rate', 'symsync_rrrf_unlock',
    'symtrack_cccf', 'symtrack_cccf_adjust_phase',
    'symtrack_cccf_create', 'symtrack_cccf_create_default',
    'symtrack_cccf_destroy', 'symtrack_cccf_execute',
    'symtrack_cccf_execute_block', 'symtrack_cccf_print',
    'symtrack_cccf_reset', 'symtrack_cccf_set_bandwidth',
    'symtrack_cccf_set_eq_cm', 'symtrack_cccf_set_eq_dd',
    'symtrack_cccf_set_eq_off', 'symtrack_cccf_set_modscheme',
    #'symtrack_rrrf', 'symtrack_rrrf_adjust_phase',
    #'symtrack_rrrf_create', 'symtrack_rrrf_create_default',
    #'symtrack_rrrf_destroy', 'symtrack_rrrf_execute',
    #'symtrack_rrrf_execute_block', 'symtrack_rrrf_print',
    #'symtrack_rrrf_reset', 'symtrack_rrrf_set_bandwidth',
    #'symtrack_rrrf_set_eq_cm', 'symtrack_rrrf_set_eq_dd',
    #'symtrack_rrrf_set_eq_off', 'symtrack_rrrf_set_modscheme',
    'synth_crcf', 'synth_crcf_adjust_frequency',
    'synth_crcf_adjust_phase', 'synth_crcf_create',
    'synth_crcf_despread', 'synth_crcf_despread_triple',
    'synth_crcf_destroy', 'synth_crcf_get_current',
    'synth_crcf_get_frequency', 'synth_crcf_get_half_next',
    'synth_crcf_get_half_previous', 'synth_crcf_get_length',
    'synth_crcf_get_phase', 'synth_crcf_mix_block_down',
    'synth_crcf_mix_block_up', 'synth_crcf_mix_down',
    'synth_crcf_mix_up', 'synth_crcf_pll_set_bandwidth',
    'synth_crcf_pll_step', 'synth_crcf_reset',
    'synth_crcf_set_frequency', 'synth_crcf_set_phase',
    'synth_crcf_spread', 'synth_crcf_step', 'tvmpch_cccf',
    'tvmpch_cccf_create', 'tvmpch_cccf_destroy',
    'tvmpch_cccf_execute', 'tvmpch_cccf_execute_block',
    'tvmpch_cccf_print', 'tvmpch_cccf_push', 'tvmpch_cccf_reset',
    'uint64_t', 'unscramble_data', 'unscramble_data_soft',
    'utility_function', 'wdelaycf', 'wdelaycf_create',
    'wdelaycf_destroy', 'wdelaycf_print', 'wdelaycf_push',
    'wdelaycf_read', 'wdelaycf_recreate', 'wdelaycf_reset', 'wdelayf',
    'wdelayf_create', 'wdelayf_destroy', 'wdelayf_print',
    'wdelayf_push', 'wdelayf_read', 'wdelayf_recreate',
    'wdelayf_reset', 'windowcf', 'windowcf_create',
    'windowcf_debug_print', 'windowcf_destroy', 'windowcf_index',
    'windowcf_print', 'windowcf_push', 'windowcf_read',
    'windowcf_recreate', 'windowcf_reset', 'windowcf_write',
    'windowf', 'windowf_create', 'windowf_debug_print',
    'windowf_destroy', 'windowf_index', 'windowf_print',
    'windowf_push', 'windowf_read', 'windowf_recreate',
    'windowf_reset', 'windowf_write']
