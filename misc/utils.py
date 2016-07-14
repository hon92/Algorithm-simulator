
def hex_to_rgb(value):
    value = value.lstrip("#")
    l = len(value)
    return tuple(int(value[i:i + l // 3], 16) for i in range(0, l, l // 3))

def rgb_to_hex(r, g, b):
    return '#%02x%02x%02x' % (r, g, b)

def get_inverted_color(color):
    hh = rgb_to_hex(*color)
    hh = hh[1:]
    ii = int(hh, 16)
    v = 0xFFFFFF ^ ii
    h = hex(v)
    h = h[2:]
    if len(h) != 6:
        for _ in range(6 - len(h)):
            h = "0" + h
    h = "#" + h
    return hex_to_rgb(h)

"""    
    r = color[0]
    g = color[1]
    b = color[2]
    
    
    
    maximum = max(r, g, b)
    minimum = min(r, g, b)
    h = 0
    s = 0
    l = (maximum + minimum) / 2.0

    if maximum == minimum:
        h = s = 0
    else:
        d = maximum - minimum
        s = 0
        if l > 0.5:
            s = d / (2.0 - maximum - minimum)
        else:
            s = d / (maximum + minimum)

        if maximum == r and g >= b:
            h = 1.0472 * (g - b) / d
        elif maximum == r and g < b:
            h = 1.0472 * (g - b) / d + 6.2832
        elif maximum == g:
            h = 1.0472 * (b - r) / d + 2.0944
        elif maximum == b:
            h = 1.0472 * (r - g) / d + 4.1888

    h = h / 6.2832 * 360.0 + 0;

    h += 180;
    if h > 360:
        h -= 360
    h /= 360;

    if s == 0:
        r = g = b = l
    else:
        def hue2rgb(p, q, t):
            if t < 0:
                t += 1
            if t > 1:
                t -= 1
            if t < 1/6:
                return p + (q - p) * 6 * t
            if t < 1/2: 
                return q
            if t < 2/3:
                return p + (q - p) * (2/3 - t) * 6
            return p

        q = 0
        if l < 0.5:
            q = l * (1 + s)
        else:
            q = l + s - l * s

        p = 2 * l - q
        r = hue2rgb(p, q, h + 1/3)
        g = hue2rgb(p, q, h)
        b = hue2rgb(p, q, h - 1/3)

    r = round(r * 255)
    g = round(g * 255) 
    b = round(b * 255)
    return (r, g, b)
"""