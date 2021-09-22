# test if framebuffer module is compiled in
try:
    import framebuf
except ImportError:
    print("SKIP")
    raise SystemExit
import sys

# test if framebuffer is compiled with the get_rect function
if not 'get_rect' in dir(framebuf.FrameBuffer):
    print("SKIP")
    raise SystemExit


import sys


DEBUG = False

# Basic maximal dimension for the framebuffer used
WIDTH = 13
HEIGHT = 19

# Bad asumed values for x and y coordinates and width/height
BAD_X = [-8, -7, -1]
BAD_Y = [-8, -7, -1]
BAD_RANGE_WH = [-8, -7, -1, 0]

# Good assumed range for width/height
GOOD_WIDTH_RANGE = [1, 7, 8, 11, WIDTH - 1, WIDTH]
GOOD_HEIGHT_RANGE = [1, 7, 8, 11, HEIGHT - 1, HEIGHT]

# Good assumed range for x/y coordinates
GOOD_X_RANGE = [0] + GOOD_WIDTH_RANGE
GOOD_Y_RANGE = [0] + GOOD_HEIGHT_RANGE

# The mappings tested
MAPS = {
    framebuf.MONO_HLSB: "MONO_HLSB",
    framebuf.MONO_HMSB: "MONO_HMSB",
}


# debug print wrapper
def dprint(str):
    if DEBUG:
        print(str)
                
# Subclass of framebuff to access the dimensions and mapping
class FrameBuffer(framebuf.FrameBuffer):
    def __init__(self, buf, width, height, map_key):
        self.buf = buf
        self.width = width
        self.height = height
        self.map_key = map_key
        super(FrameBuffer, self).__init__(buf, width, height, map_key)

# check the shortcuts to dismiss a get_rect request since the rectangle requested is outside the frame buffer
def check_range_overflow(map_key):
    
    buffer, framebuffer = get_test_buffer(WIDTH, HEIGHT, map_key)

    # These have to be clipped and should return a valid result
    for x in BAD_X:
        res = framebuffer.get_rect(x, GOOD_Y_RANGE[3], GOOD_WIDTH_RANGE[3], GOOD_HEIGHT_RANGE[3])
        if res is None:
            raise Exception
        
    # These have to be clipped and should return a valid result
    for y in BAD_Y:
        res = framebuffer.get_rect(GOOD_X_RANGE[3], y, GOOD_WIDTH_RANGE[3], GOOD_HEIGHT_RANGE[3])
        if res is None:
            raise Exception
  
    # These have to return None
    for w in BAD_RANGE_WH:
        res = framebuffer.get_rect(GOOD_X_RANGE[3], GOOD_Y_RANGE[3], w, GOOD_HEIGHT_RANGE[3])
        if res is not None:
            raise Exception
        
    # These have to return None
    for h in BAD_RANGE_WH:
        res = framebuffer.get_rect(GOOD_X_RANGE[3], GOOD_Y_RANGE[3], GOOD_WIDTH_RANGE[3], h)
        if res is not None:
            raise Exception
            

def get_rect(framebuffer, buffer, x, y, w, h, stride=None):
    """
    Reimplementation of FRameBuffer.get_rect in Python.
    """
    dprint('py_get_rect init x:{} y:{} w:{} h:{}'.format(x, y, w, h))

    if (h < 1) or (w < 1) or (x + w <= 0) or (y + h <= 0) or (x >= framebuffer.width) or (y >= framebuffer.height):
        return None

    dprint('buffer:{}'.format(buffer))
    xend = min(framebuffer.width, x + w)
    yend = min(framebuffer.height, y + h)
    x = max(x, 0)
    y = max(y, 0)

    w = xend - x
    h = yend - y

    dprint('py_get_rect clipped x:{} y:{} w:{} h:{}'.format(x, y, w, h))
    dprint('stride:{}'.format(stride))

    if stride is None:
        stride = (framebuffer.width + 7) & ~7  # Rounding up to byte boundary
    dprint('new_stride:{}'.format(stride))
    # get the width of the returned rect in bytes, including the partial striven bytes at the left/right border
    w_bytes = ((x + w - 1) >> 3) - (x >> 3) + 1
    dprint('w_bytes:{}'.format(w_bytes))

    # advance is the offest to the next line
    advance = stride >> 3
    dprint('py_get_rect advance:{}'.format(advance))

    start_byte = (x >> 3) + y * advance
    dprint('py_get_rect start_byte:{}'.format(start_byte))
    # The output buffer
    vstr = bytearray()
    for n in range(h):
        vstr += buffer[start_byte: start_byte + w_bytes]
        start_byte += advance
    return vstr


def check_rect_combinations(framebuffer, buffer):
    test_name = 'check_rect_combinations'
    print('='*50)
    print(MAPS[map_key] + ' ' + test_name)
    print('='*50)
    print()

    for x in GOOD_WIDTH_RANGE:
        check_get_rect('x varying', framebuffer, buffer, x, GOOD_Y_RANGE[3], GOOD_WIDTH_RANGE[3], GOOD_HEIGHT_RANGE[3])

    for y in GOOD_Y_RANGE:
        check_get_rect('y varying', framebuffer, buffer, GOOD_X_RANGE[3], y, GOOD_WIDTH_RANGE[3], GOOD_HEIGHT_RANGE[3])

    for x, y in zip(GOOD_WIDTH_RANGE, GOOD_Y_RANGE):
        check_get_rect('diagonal varying', framebuffer, buffer, x, y, GOOD_WIDTH_RANGE[3], GOOD_HEIGHT_RANGE[3])

                    
def check_get_rect(test_name, framebuffer, buffer, x, y, w, h, stride=None):
    print('frame_buf: w:{} h:{}'.format(framebuffer.width,framebuffer.height))
    print('check_rect: x:{} y:{} w:{} h:{} stride:{}'.format(x,y,w,h, stride))
    get_rect_res = framebuffer.get_rect(x, y, w, h)
    if stride is None:
        py_get_rect_res = get_rect(framebuffer, buffer, x, y, w, h)
    else:
        py_get_rect_res = get_rect(framebuffer, buffer, x, y, w, h, stride)
    print(MAPS[map_key] + ' ' + test_name + ' C : {}'.format(get_rect_res))
    print(MAPS[map_key] + ' ' + test_name + ' Py: {}'.format(py_get_rect_res))
    assert get_rect_res == py_get_rect_res
    print()


def get_test_buffer(width, height, map_key):
    print('test_buffer_size: w:{} h:{}'.format(width, height))
    buffer_size = (width // 8 + 1) * height
    buf = bytearray(range(buffer_size))
    print('test_buffer: {}'.format(buf))
    fbuf = FrameBuffer(buf, width, height, map_key)
    return buf, fbuf


def check_buf_size(map_key):
    for w in GOOD_WIDTH_RANGE:
        for h in GOOD_HEIGHT_RANGE:
            buf, fbuf = get_test_buffer(w, h, map_key)
            check_rect_combinations(fbuf, buf)


for map_key in MAPS:

    # Testing impossible coordinates
    check_range_overflow(map_key)
    
    
for map_key in MAPS:
    print('#'*50)
    print(MAPS[map_key])
    print('#'*50)
    print()

    check_buf_size(map_key)