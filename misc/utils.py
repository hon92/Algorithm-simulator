
def hex_to_rgb(value):
    value = value.lstrip("#")
    l = len(value)
    return tuple(int(value[i:i + l // 3], 16) for i in range(0, l, l // 3))