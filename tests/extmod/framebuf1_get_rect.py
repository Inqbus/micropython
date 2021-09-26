# test if framebuffer module is compiled in
try:
    import framebuf
except ImportError:
    print("SKIP")
    raise SystemExit

# test if framebuf is compiled with the get_rect function
if not 'get_rect' in dir(framebuf.FrameBuffer):
    print("SKIP")
    raise SystemExit

DEBUG = True

# Maximal dimension for the framebuffer used
WIDTH = 23
HEIGHT = 29

# Bad assumed values for x and y coordinates and width/height
BAD_X = [-8, -7, -1]
BAD_Y = [-8, -7, -1]
BAD_RANGE_WH = [-8, -7, -1, 0]

# Good assumed range for width/height
GOOD_WIDTH_RANGE = [1, 7, 8, 11, WIDTH - 1, WIDTH]
GOOD_HEIGHT_RANGE = [1, 7, 8, 11, HEIGHT - 1, HEIGHT]

# Good assumed range for x/y coordinates
GOOD_X_RANGE = [0] + GOOD_WIDTH_RANGE
GOOD_Y_RANGE = [0] + GOOD_HEIGHT_RANGE

# Choosen good index to test for
GOOD_POINT_IDX = 1

# test strides
GOOD_STRIDE_OFFSET = [0, 1, 7 ,8]

# test strides
BAD_STRIDE_OFFSET = [-1, -7, -8]



# The mappings tested
MAPS = {
    framebuf.MONO_VLSB: "MONO_VLSB",
    framebuf.MONO_HLSB: "MONO_HLSB",
    framebuf.MONO_HMSB: "MONO_HMSB",
}


# debug print wrapper
def dprint(str):
    if DEBUG:
        print(str)


# Subclass of framebuff to access the dimensions and mapping
class FrameBufferTest(framebuf.FrameBuffer):
    def __init__(self, width, height, map_key, stride=None):
        self.width = width
        self.height = height
        self.map_key = map_key
        self.stride = self.calc_stride(stride)
        self.buf = self.calc_buf()
        
        if stride is None: # ToDo: Cannot be None : Fix inconsitent stride calculation
            sys.exit(1)
            super(FrameBufferTest, self).__init__(self.buf, width, height, map_key) 
        else:
            super(FrameBufferTest, self).__init__(self.buf, width, height, map_key, self.stride)
            
        self.draw()

    def calc_stride(self, stride):

        if stride is None:
            stride = self.width

        if stride < self.width :
            stride = self.width
            
        if self.map_key != framebuf.MONO_VLSB:
            stride = (stride + 7) & ~7
            
        return stride

    def calc_buf(self):

        if self.map_key == framebuf.MONO_VLSB:
            buffer_size = self.stride * (self.height // 8 + 1)
        else:
            buffer_size = (self.stride // 8 + 1) * self.height

        return bytearray(buffer_size)

    def draw(self):
        self.line(0, 0, self.width, self.height, 1)

    def __str__(self):
        msg = ''
        msg += 'Frambuffer w:{} h:{} stride:{}'.format(self.width, self.height, self.stride)
        msg += v_bytes2bin(self.buf, self.width, self.height)
        return msg
        
def h_get_rect(framebuffer, x, y, w, h):
    """
    Reimplementation of FrameBufferTest.get_rect for mono horizontal in Python.
    """

    stride = framebuffer.stride
    buffer = framebuffer.buf
    dprint('py_h_get_rect init x:{} y:{} w:{} h:{} stride:{}'.format(x, y, w, h, stride))

    if (h < 1) or (w < 1) or (x + w <= 0) or (y + h <= 0) or (x >= framebuffer.width) or (y >= framebuffer.height):
        return None

    dprint('py_h_get_rect buffer:{}'.format(buffer))
    xend = min(framebuffer.width, x + w)
    yend = min(framebuffer.height, y + h)
    x = max(x, 0)
    y = max(y, 0)

    w = xend - x
    h = yend - y

    dprint('py_h_get_rect clipped x:{} y:{} w:{} h:{}'.format(x, y, w, h))
    dprint('py_h_get_rect stride:{}'.format(stride))

    if stride is None:
        stride = (framebuffer.width + 7) & ~7  # Rounding up to byte boundary
    dprint('py_h_get_rect new_stride:{}'.format(stride))
    # get the width of the returned rect in bytes, including the partial striven bytes at the left/right border
    w_bytes = ((x + w - 1) >> 3) - (x >> 3) + 1
    dprint('py_h_get_rect w_bytes:{}'.format(w_bytes))

    # advance is the offest to the next line
    advance = stride >> 3
    dprint('py_h_get_rect advance:{}'.format(advance))

    start_byte = (x >> 3) + y * advance
    dprint('py_h_get_rect start_byte:{}'.format(start_byte))
    # The output buffer
    vstr = bytearray()
    for n in range(h):
        vstr += buffer[start_byte: start_byte + w_bytes]
        start_byte += advance
    return vstr


def v_get_rect(framebuffer, x, y, w, h):
    """
    Reimplementation of FrameBufferTest.get_rect for mono vertical in Python.
    """
    stride = framebuffer.stride
    buffer = framebuffer.buf
    dprint('py_v_get_rect init x:{} y:{} w:{} h:{} stride:{}'.format(x, y, w, h, stride))

    if (h < 1) or (w < 1) or (x + w <= 0) or (y + h <= 0) or (x >= framebuffer.width) or (y >= framebuffer.height):
        return None

    dprint('py_v_get_rect buffer:{}'.format(buffer))
    xend = min(framebuffer.width, x + w)
    yend = min(framebuffer.height, y + h)
    x = max(x, 0)
    y = max(y, 0)

    w = xend - x
    h = yend - y

    dprint('py_v_get_rect clipped x:{} y:{} w:{} h:{}'.format(x, y, w, h))
    dprint('py_v_get_rect stride:{}'.format(stride))

    if framebuffer.stride is None:
        stride = framebuffer.width
    dprint('py_v_get_rect new_stride:{}'.format(stride))
    # get the height of the returned rect in bytes, including the partial striven bytes at the top/bottom border
    h_bytes = ((y + h - 1) >> 3) - (y >> 3) + 1
    dprint('py_v_get_rect h_bytes:{}'.format(h_bytes))

    # advance is the offest to the next line
    advance = stride
    dprint('py_v_get_rect advance:{}'.format(advance))

    start_byte = (y >> 3) * advance + x
    dprint('py_v_get_rect start_byte:{}'.format(start_byte))
    # The output buffer
    vstr = bytearray()
    for n in range(h_bytes):
        vstr += buffer[start_byte : start_byte + w]
        start_byte += advance
    return vstr


# check the shortcuts to dismiss a get_rect request since the rectangle requested is outside the frame buffer
def check_range_overflow(map_key):

    framebuffer = FrameBufferTest(WIDTH, HEIGHT, map_key)
    buffer = framebuffer.buf
    get_rect_func = get_get_rect_func(framebuffer.map_key)

    # These have to be clipped and should return a valid result
    for x in BAD_X:
        c_res = framebuffer.get_rect(x, GOOD_Y_RANGE[GOOD_POINT_IDX], GOOD_WIDTH_RANGE[GOOD_POINT_IDX], GOOD_HEIGHT_RANGE[GOOD_POINT_IDX])
        py_res = get_rect_func(framebuffer, buffer, x, GOOD_Y_RANGE[GOOD_POINT_IDX], GOOD_WIDTH_RANGE[GOOD_POINT_IDX], GOOD_HEIGHT_RANGE[GOOD_POINT_IDX])
        assert c_res == py_res

    # These have to be clipped and should return a valid result
    for y in BAD_Y:
        c_res = framebuffer.get_rect(GOOD_X_RANGE[GOOD_POINT_IDX], y, GOOD_WIDTH_RANGE[GOOD_POINT_IDX], GOOD_HEIGHT_RANGE[GOOD_POINT_IDX])
        py_res = get_rect_func(framebuffer, buffer, GOOD_X_RANGE[GOOD_POINT_IDX], y, GOOD_WIDTH_RANGE[GOOD_POINT_IDX], GOOD_HEIGHT_RANGE[GOOD_POINT_IDX])
        assert c_res == py_res

    # These have to return None
    for w in BAD_RANGE_WH:
        c_res = framebuffer.get_rect(GOOD_X_RANGE[GOOD_POINT_IDX], GOOD_Y_RANGE[GOOD_POINT_IDX], w, GOOD_HEIGHT_RANGE[GOOD_POINT_IDX])
        py_res = get_rect_func(framebuffer, buffer, GOOD_X_RANGE[GOOD_POINT_IDX], GOOD_Y_RANGE[GOOD_POINT_IDX], w, GOOD_HEIGHT_RANGE[GOOD_POINT_IDX])
        assert c_res == py_res == None

    # These have to return None
    for h in BAD_RANGE_WH:
        c_res = framebuffer.get_rect(GOOD_X_RANGE[GOOD_POINT_IDX], GOOD_Y_RANGE[GOOD_POINT_IDX], GOOD_WIDTH_RANGE[GOOD_POINT_IDX], h)
        py_res = get_rect_func(framebuffer, buffer, GOOD_X_RANGE[GOOD_POINT_IDX], GOOD_Y_RANGE[GOOD_POINT_IDX], GOOD_WIDTH_RANGE[GOOD_POINT_IDX], h)
        assert c_res == py_res == None


def check_stride(map_key):

#    print('Good stride')
#    for stride_offset in GOOD_STRIDE_OFFSET:
#        stride = WIDTH + stride_offset
#        framebuffer = FrameBufferTest(WIDTH, HEIGHT, map_key, stride=stride)
#        check_rect_combinations(framebuffer)

    for stride_offset in BAD_STRIDE_OFFSET:
        stride = WIDTH + stride_offset
        print('Bad map_key:{} stride:{}'.format(map_key, stride))
        framebuffer = FrameBufferTest(WIDTH, HEIGHT, map_key, stride=stride)
        check_rect_combinations(framebuffer)


def check_rect_combinations(framebuffer):
    test_name = 'check_rect_combinations'
    print('='*50)
    print(MAPS[map_key] + ' ' + test_name)
    print('='*50)
    print()

    for x in GOOD_WIDTH_RANGE:
        check_get_rect('x varying', framebuffer, x, GOOD_Y_RANGE[GOOD_POINT_IDX], GOOD_WIDTH_RANGE[GOOD_POINT_IDX], GOOD_HEIGHT_RANGE[GOOD_POINT_IDX])

    for y in GOOD_Y_RANGE:
        check_get_rect('y varying', framebuffer, GOOD_X_RANGE[GOOD_POINT_IDX], y, GOOD_WIDTH_RANGE[GOOD_POINT_IDX], GOOD_HEIGHT_RANGE[GOOD_POINT_IDX])

    for x, y in zip(GOOD_WIDTH_RANGE, GOOD_Y_RANGE):
        check_get_rect('diagonal varying', framebuffer, x, y, GOOD_WIDTH_RANGE[GOOD_POINT_IDX], GOOD_HEIGHT_RANGE[GOOD_POINT_IDX])


def get_get_rect_func(map_key):
    if map_key == framebuf.MONO_VLSB:
        return v_get_rect
    else:
        return h_get_rect

                    
def check_get_rect(test_name, framebuffer, x, y, w, h,):
    print('frame_buf: w:{} h:{}'.format(framebuffer.width, framebuffer.height))
    print('check_rect: x:{} y:{} w:{} h:{} stride:{}'.format(x,y,w,h, framebuffer.stride))
    get_rect_res = framebuffer.get_rect(x, y, w, h)
    py_get_rect_res = get_get_rect_func(framebuffer.map_key)(framebuffer, x, y, w, h)
    print(MAPS[map_key] + ' ' + test_name + ' C : {}'.format(get_rect_res))
    print(MAPS[map_key] + ' ' + test_name + ' Py: {}'.format(py_get_rect_res))
    
    if get_rect_res != py_get_rect_res:
        print('Error!')
        print('Framebuffer:')
        print(v_bytes2bin(framebuffer.buf, framebuffer.width, framebuffer.height, framebuffer.stride))
        print('Rect C')
        print(v_bytes2bin(get_rect_res, w, h))
        print('Rect Py')
        print(v_bytes2bin(py_get_rect_res, w, h))
        print()
        sys.exit(1)
        

def check_buf_size(map_key):
    for w in GOOD_WIDTH_RANGE:
        for h in GOOD_HEIGHT_RANGE:
            fbuf = FrameBufferTest(w, h, map_key)
            check_rect_combinations(fbuf)


def v_bytes2bin(byts, width, height, stride=None):
    if stride is None:
        stride = width
    print('w:{} h:{} stride:{}'.format(width, height, stride))
    h_bytes = (((len(byts) * 8) // stride - 1) >> 3) + 1
    offset = 0
    msg = '\n'
    for line8 in range(h_bytes):
        for line in range(8):
            mask = 0x1 << line
            for i in byts[offset:offset + stride]:
                if mask & i == mask:
                    msg += '1'
                else:
                    msg += '0'
            msg += '\n'
        offset += stride
    return msg

#framebuffer = FrameBufferTest(23, 29, framebuf.MONO_VLSB, stride=22)
#print(v_bytes2bin(framebuffer.buf, 23, 29))

#sys.exit(1)

for map_key in MAPS:
    print('#'*50)
    print(MAPS[map_key])
    print('#'*50)
    print()

    # Check stride problems
    check_stride(map_key)

    # Testing impossible coordinates
#    check_range_overflow(map_key)
    
    # test for different buffer sizes        
#    check_buf_size(map_key)