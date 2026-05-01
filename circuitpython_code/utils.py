def interpolate(x, curve):

  
    x = x >> 7         # map to 0-511, this should be faster than using map.
    # clamp
    if x <= curve[0][0]:
        return curve[0][1]

    if x >= curve[-1][0]:
        return curve[-1][1]

    # find segment
    for i in range(len(curve) - 1):
        x0, y0 = curve[i]
        x1, y1 = curve[i + 1]

        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0)
            return int(y0 + t * (y1 - y0))
        
def get_current_position(x):
    return x >> 7   