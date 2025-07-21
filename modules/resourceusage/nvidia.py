"""
Extracted from GPUtil https://github.com/anderskm/gputil/tree/master
"""

from subprocess import PIPE, run

from loguru import logger


def safe_float_cast(str_number):
    try:
        number = float(str_number)
    except ValueError:
        number = float('nan')
    return number


def get_gpu_data():
    # Get ID, processing and memory utilization for all GPUs
    try:
        p = run(["nvidia-smi", "--query-gpu=index,utilization.gpu,memory.total,memory.used,temperature.gpu",
                 "--format=csv,noheader,nounits"], stdout=PIPE).stdout.decode()
    except FileNotFoundError as e:
        raise e
    except:
        return []

    if 'Failed to initialize NVML' in p:
        logger.error(p)
        return [[None, '', 'GPU: NVML Error', 'red']]

    bars = []
    for n, line in enumerate(p.splitlines()):
        vals = line.split(', ')
        try:
            gpu_id = int(vals[0])
        except ValueError:
            gpu_id = n
        gpu_util = safe_float_cast(vals[1])
        mem_total = safe_float_cast(vals[2])
        mem_used = safe_float_cast(vals[3])
        memory_util = (mem_used / mem_total) * 100
        temp_gpu = safe_float_cast(vals[4])
        bars.append([gpu_util, f'{round(gpu_util, int(gpu_util < 100))}% {temp_gpu}°C', f'GPU{gpu_id}', 'red'])
        bars.append([memory_util, f'{(round(mem_used / 1024, 1))}G/{round(mem_total / 1024, 1)}G', f'Mem{gpu_id}', 'green'])
    return bars
