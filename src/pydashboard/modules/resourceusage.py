from subprocess import PIPE, run

import psutil as ps
from psutil._common import bytes2human as b2h, shwtemp

from pydashboard.containers import BaseModule
from pydashboard.utils.bars import create_bar
from pydashboard.utils.numbers import safe_float_cast
from pydashboard.utils.types import Size


# noinspection PyPep8Naming
class ResourceUsage(BaseModule):
    def __init__(self, *, cpuCombined=True, showCPU=True, showMem=True, showSwp=True, showGPU=True, **kwargs):
        super().__init__(cpuCombined=cpuCombined, showCPU=showCPU, showMem=showMem, showSwp=showSwp, showGPU=showGPU,
                         **kwargs)
        self.cpuCombined = cpuCombined
        self.showCPU = showCPU
        self.showMem = showMem
        self.showSwp = showSwp
        self.showGPU = showGPU

    def __call__(self, content_size: Size):
        bars = []

        if self.showCPU:
            bars.extend(self.get_cpu_data(self.cpuCombined))

        if self.showMem:
            vmem = ps.virtual_memory()
            bars.append([vmem.percent, f'{b2h(vmem.used)}/{b2h(vmem.total)}', 'Mem', 'green'])

        if self.showSwp:
            smem = ps.swap_memory()
            bars.append([smem.percent, f'{b2h(smem.used)}/{b2h(smem.total)}', 'Swp', 'green'])

        if self.showGPU:
            bars.extend(self.get_gpu_data())

        return '\n'.join([create_bar(max_w=content_size[1],
                                     perc=perc, text=text,
                                     pre_txt=pre_txt, color=color) for perc, text, pre_txt, color in bars])

    @staticmethod
    def get_cpu_data(cpu_combined):
        bars = []

        if cpu_combined:
            perc = ps.cpu_percent()
            temp = combine_temps([t for t in ps.sensors_temperatures()['coretemp'] if t.label.startswith('Package')])
            freq = round(ps.cpu_freq().current)

            text = f'{round(perc, int(perc < 100))}% {freq:>4}MHz {temp}°C'
            bars.append([perc, text, 'CPU', 'red'])
        else:
            perc = ps.cpu_percent(percpu=True)
            temp = {int(t.label.removeprefix('Core ')): round(t.current) for t in ps.sensors_temperatures()['coretemp']
                    if
                    t.label.startswith('Core')}
            freq = [round(f.current) for f in ps.cpu_freq(percpu=True)]

            for i, (p, f) in enumerate(zip(perc, freq)):
                text = f'{round(p, int(p < 100))}% {f:>4}MHz'
                t = temp.get(i)
                if t is not None:
                    text += f' {t}°C'
                else:
                    text += '  N/A'
                bars.append([p, text, str(i), 'red'])

        return bars


    def get_gpu_data(self):
        """Extracted from GPUtil https://github.com/anderskm/gputil/tree/master"""

        # Get ID, processing and memory utilization for all GPUs
        try:
            p = run(["nvidia-smi", "--query-gpu=index,utilization.gpu,memory.total,memory.used,temperature.gpu",
                     "--format=csv,noheader,nounits"], stdout=PIPE).stdout.decode()
        except FileNotFoundError:
            return [[None, '', 'nvidia-smi not found', 'red']]
        except Exception as e:
            return [[None, '', str(e), 'red']]

        if 'Failed to initialize NVML' in p:
            self.logger.error(p)
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
            bars.append([memory_util, f'{(round(mem_used / 1024, 1))}G/{round(mem_total / 1024, 1)}G', f'Mem{gpu_id}',
                         'green'])
        return bars


def combine_temps(temperatures: list[shwtemp]):
    combine_fn = max  # max or average
    return round(combine_fn([t.current for t in temperatures]))


widget = ResourceUsage
