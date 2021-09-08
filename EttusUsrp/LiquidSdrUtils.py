import ctypes
import ctypeslib

# typedef struct {
#     unsigned int check;         // data validity check
#     unsigned int fec0;          // forward error-correction scheme (inner)
#     unsigned int fec1;          // forward error-correction scheme (outer)
#     unsigned int mod_scheme;    // modulation scheme
#     //unsigned int block_size;  // framing block size
# } ofdmflexframegenprops_s;

class ofdmflexframegenprops_s(ctypes.Structure):
  """ creates a struct to match ofdmflexframegenprops_s """

  _fields_ = [('check', ctypes.c_uint),
              ('fec0', ctypes.c_uint),
              ('fec1', ctypes.c_uint),
              ('mod_scheme', ctypes.c_uint)
              ]
