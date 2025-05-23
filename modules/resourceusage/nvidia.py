"""
Extracted from GPUtil https://github.com/anderskm/gputil/tree/master
"""



from subprocess import PIPE, run

from loguru import logger


def safeFloatCast(strNumber):
    try:
        number = float(strNumber)
    except ValueError:
        number = float('nan')
    return number

def get_gpu_data():	
    # Get ID, processing and memory utilization for all GPUs
    try:
        p = run(["nvidia-smi", "--query-gpu=index,utilization.gpu,memory.total,memory.used,temperature.gpu", "--format=csv,noheader,nounits"], stdout=PIPE).stdout.decode()
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
            ID = int(vals[0])
        except ValueError:
            ID = n
        gpuUtil = safeFloatCast(vals[1])
        memTotal = safeFloatCast(vals[2])
        memUsed = safeFloatCast(vals[3])
        memoryUtil = (memUsed/memTotal)*100
        temp_gpu = safeFloatCast(vals[4]);
        bars.append([gpuUtil, f'{round(gpuUtil, int(gpuUtil < 100))}% {temp_gpu}°C', f'GPU{ID}', 'red'])
        bars.append([memoryUtil, f'{(round(memUsed/1024,1))}G/{round(memTotal/1024,1)}G', f'Mem{ID}', 'green'])
    return bars
