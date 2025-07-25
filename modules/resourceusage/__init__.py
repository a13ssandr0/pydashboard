import psutil as ps
from psutil._common import bytes2human as b2h

from containers import BaseModule
from utils.types import Coordinates, Size
from modules.resourceusage.nvidia import get_gpu_data
from utils.bars import create_bar
from .cpu import get_cpu_data


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
            bars.extend(get_cpu_data(self.cpuCombined))

        if self.showMem:
            vmem = ps.virtual_memory()
            bars.append([vmem.percent, f'{b2h(vmem.used)}/{b2h(vmem.total)}', 'Mem', 'green'])

        if self.showSwp:
            smem = ps.swap_memory()
            bars.append([smem.percent, f'{b2h(smem.used)}/{b2h(smem.total)}', 'Swp', 'green'])

        if self.showGPU:
            bars.extend(get_gpu_data())

        return '\n'.join([create_bar(max_w=content_size[1],
                                     perc=perc, text=text,
                                     pre_txt=pre_txt, color=color) for perc, text, pre_txt, color in bars])


widget = ResourceUsage
