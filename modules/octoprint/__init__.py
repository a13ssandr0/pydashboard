from sys import argv

from octorest import OctoRest

try:
    client = OctoRest(url=argv[1], apikey=argv[2])
    job_info = client.job_info()
    print('State:', job_info['state'])
    print('File:', job_info['job']['file']['name'])
    if job_info['progress']['completion'] is not None:
        print('Progress: {:.3f}%'.format(job_info['progress']['completion']))
    if job_info['progress']['printTime'] is not None:
        print('Print time: {}s'.format(job_info['progress']['printTime']))
    if job_info['progress']['printTimeLeft'] is not None:
        print('Time left: {}s'.format(job_info['progress']['printTimeLeft']))
        
    conn_info = client.connection_info()
    if conn_info['current']['port'] is not None:
        printer = client.printer()
        max_len = max([len(x) for x in printer['temperature'].keys()])
        print('Temperatures:')
        for tool, temp in printer['temperature'].items():
            if temp['target']:
                print(' ', tool.ljust(max_len), f'{temp['actual']:.1f}°C/{temp['target']:.1f}°C')
            else:
                print(' ', tool.ljust(max_len), f'{temp['actual']:.1f}°C/off')

except OSError as e:
    print('Octoprint is offline')