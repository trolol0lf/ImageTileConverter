def good_int(var):
        if type(var) == str:
            try:
                ret = float(var)
            except:
                ret = 0
            return int(ret)
        elif type(var) == float:
            return int(round(var,0))
        elif type(var) == int:
            return var

def good_float(var):        
        if type(var) == str:
            try:
                ret = float(var)
            except:
                ret = 0.0
            return ret
        elif type(var) == float:
            return var
        elif type(var) == int:
            return float(var)
        return 0.0

def clamp_float(var, min, max):
     var = good_float(var)
     if var < min: return min
     if var > max: return max
     return var