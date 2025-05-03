import psutil as ps
from psutil._common import bytes2human as b2h

from containers import BaseModule
from modules.resourceusage.nvidia import get_gpu_data

from .cpu import get_cpu_data


class ResourceUsage(BaseModule):
    def __init__(self, *, cpuCombined, showCPU, showMem, showSwp, showGPU, **kwargs):
        super().__init__(**kwargs)
        self.cpuCombined = cpuCombined
        self.showCPU = showCPU
        self.showMem = showMem
        self.showSwp = showSwp
        self.showGPU = showGPU
        
    def __call__(self):
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
            try:
                bars.extend(get_gpu_data())
            except RuntimeError as e:
                self.notify(str(e), title='Error while running nvidia-smi', severity='warning')
        
        return '\n'.join([createBar(max_w=self.content_size.width, 
                                    perc=perc, text=text, 
                                    pre_txt=pre_txt, color=color) for perc, text, pre_txt, color in bars])
    
widget = ResourceUsage





def createBar(max_w:int, perc:int|float, text:str='', pre_txt='', color='red'):
    if perc is None:
        # percentage can be None in case of errors and pre_txt will display
        # the associated message
        return f"[{color}]{pre_txt}[/{color}]"
    
    max_w -= len(pre_txt)
    
    if max_w <= 0:
        # preceding text takes precedence and can take all the available space
        return pre_txt
    
    max_w -= 2 #square brackets at both ends
    text = text[:max_w] # cut text if too long to prevent overflow
    
    color_width = round((perc/100)*(max_w))
    
    bar = '|' * color_width # fill the row
    bar = bar[:(max_w-len(text))] # making room for the text
    
    bar = f"{bar}{' '*(max_w-len(bar)-len(text))}{text}"
    
    bar = f"[{color}]{bar[:color_width]}[/{color}]{bar[color_width:]}"
    
    return f'{pre_txt}[{bar}]'