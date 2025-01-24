import psutil as ps
from psutil._common import shwtemp


def get_cpu_data(cpuCombined):
    bars = []
    
    if cpuCombined:
        perc = ps.cpu_percent()
        temp = combine_temps([t for t in ps.sensors_temperatures()['coretemp'] if t.label.startswith('Package')])
        freq = round(ps.cpu_freq().current) 
        
        text = f'{round(perc, int(perc < 100))}% {freq:>4}MHz {temp}°C'
        bars.append([perc, text, 'CPU', 'red'])
    else:
        perc = ps.cpu_percent(percpu=True)
        temp = {int(t.label.removeprefix('Core ')):round(t.current) for t in ps.sensors_temperatures()['coretemp'] if t.label.startswith('Core')}
        freq = [round(f.current) for f in ps.cpu_freq(percpu=True)]
        
        for i, (p, f) in enumerate(zip(perc, freq)):
            text = f'{round(p, int(p < 100))}% {f:>4}MHz'
            t = temp.get(i)
            if t is not None: text += f' {t}°C'
            else: text += '  N/A'
            bars.append([p, text, str(i), 'red'])
            
    return bars




def combine_temps(temperatures:list[shwtemp]):
    combine_fn = max #max or average
    return round(combine_fn([t.current for t in temperatures]))