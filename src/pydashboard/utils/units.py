import math
from datetime import datetime, timedelta


def sizeof_fmt(suffix="B", div=1024.0):  # psutil._common.bytes2human
    # noinspection PyShadowingNames
    def sizeof_fmt(num):
        if num == '': return ''
        for unit in ("", "K", "M", "G", "T", "P", "E", "Z"):
            if abs(num) < div:
                return f"{num:.1f}{unit}{suffix}"
            num /= div
        return f"{num:.1f}Y{suffix}"
    return sizeof_fmt

def speedof_fmt(suffix="B/s", div=1024.0):
    return sizeof_fmt(suffix, div)

def duration_fmt(seconds):
    if seconds == '': return ''
    return str(timedelta(seconds=seconds))

def time_fmt(seconds):
    if seconds == '': return ''
    return datetime.fromtimestamp(seconds).isoformat()

def perc_fmt(scale: float = None):
    # noinspection PyShadowingNames
    def perc_fmt(percentage):
        if percentage == '' or math.isnan(percentage):
            return ''
        if scale:
            percentage *= scale
        if percentage < 10:
            return f"{percentage:.2f}%"
        elif percentage < 100:
            return f"{percentage:.1f}%"
        else:
            return f"{percentage:.0f}%"
    return perc_fmt