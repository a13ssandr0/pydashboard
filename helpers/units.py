from datetime import datetime, timedelta


def sizeof_fmt(num, suffix="B", div=1024.0):  # psutil._common.bytes2human
    for unit in ("", "K", "M", "G", "T", "P", "E", "Z"):
        if abs(num) < div:
            return f"{num:3.1f}{unit}{suffix}"
        num /= div
    return f"{num:.1f}Y{suffix}"

def speedof_fmt(num, suffix="B/s"):
    if num < 0: return ''
    return sizeof_fmt(num, suffix)

def duration_fmt(seconds):
    return str(timedelta(seconds=seconds))

def time_fmt(seconds):
    return datetime.fromtimestamp(seconds).isoformat()

def perc_fmt(percentage):
    percentage *= 100
    if percentage < 10:
        return f"{percentage:.2f}%"
    elif percentage < 100:
        return f"{percentage:.1f}%"
    return f"{round(percentage):}%"