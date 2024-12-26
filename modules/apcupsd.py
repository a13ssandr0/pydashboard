import socket
from collections import OrderedDict
from datetime import datetime, timedelta
from basemod import BaseModule

CMD_STATUS = b"\x00\x06status"
EOF = b"  \n\x00\x00"
SEP = ":"
BUFFER_SIZE = 1024
ALL_UNITS = (
    "Minutes",
    "Seconds",
    "Percent",
    "Volts",
    "Watts",
    "Amps",
    "Hz",
    "C",
    "VA",
    "Percent Load Capacity"
)

class APCUPSd(BaseModule):
    def __init__(self, *, title=None, host="localhost", port=3551, timeout=30, **kwargs):
        self.host=host
        self.port=port
        self.timeout=timeout
        self.__model_as_title = title is None
        super().__init__(title=title, **kwargs)
        
    def __call__(self):
        status = self.get()
        
        if self.__model_as_title:
            self.border_title = status['MODEL']

        # status['STATUS']   = status['STATUS']
        status['LINEV']    = status['LINEV'].removesuffix('.0')
        status['BCHARGE']  = status['BCHARGE'].removesuffix('.0')
        status['LOADPCT']  = status['LOADPCT'].removesuffix('.0')
        status['LOADPWR']  = round(float(status['LOADPCT'])*int(status['NOMPOWER'])/100)
        status['NUMXFERS'] = f"{status.get('NUMXFERS')} transfer{'s'if status.get('NUMXFERS')!='1'else''}"
        status['XOFFBATT'] = self.human_readable_time(status.get('XOFFBATT', 'N/A'))
        status['XONBATT']  = self.human_readable_time(status.get('XONBATT', 'N/A'))

        return (
        """{STATUS:<20} {LINEV}V     {BCHARGE}%\n"""
        """LOAD: {LOADPCT:>3}% ({LOADPWR}W)  {TIMELEFT} mins left\n"""
        """LAST: {LASTXFER}\n"""
        """ONBATT:   {TONBATT}s/{CUMONBATT}s ({NUMXFERS})\n"""
        """XOFFBATT: {XOFFBATT}  XONBATT: {XONBATT}\n"""
        ).strip().format_map(status)
    
    def get(self):
        """
        Connect to the APCUPSd NIS and request its status.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        sock.connect((self.host, self.port))
        sock.send(CMD_STATUS)
        buffr = b""
        while not buffr.endswith(EOF):
            buffr += sock.recv(BUFFER_SIZE)
        sock.close()
        return self.parse(buffr.decode(), True)

    def parse(self, raw_status, strip_units=False):
        """
        Split the output from get_status() into lines, clean it up and return it as
        an OrderedDict.
        """
        # Remove the EOF string, split status on the line endings (\x00), strip the
        # length byte and newline chars off the beginning and end respectively.
        lines = [x[1:-1] for x in raw_status[:-len(EOF)].split("\x00") if x]
        if strip_units:
            lines = self.strip_units_from_lines(lines)
        # Split each line on the SEP character, strip extraneous whitespace and
        # create an OrderedDict out of the keys/values.
        return OrderedDict([[x.strip() for x in x.split(SEP, 1)] for x in lines])


    def strip_units_from_lines(self, lines):
        """
        Removes all units from the ends of the lines.
        """
        for line in lines:
            for unit in ALL_UNITS:
                if line.endswith(" %s" % unit):
                    line = line[:-1-len(unit)]
            yield line

    def human_readable_time(self, timestr):
        try:
            delta:timedelta = datetime.now() - datetime.strptime(timestr.split(' +')[0], "%Y-%m-%d %H:%M:%S")
            if delta.days:
                return f"{delta.days}d ago"
            elif delta.seconds:
                minutes, seconds = divmod(delta.seconds, 60)
                hours, minutes = divmod(minutes, 60)
                if hours:
                    return f"{hours}h ago"
                elif minutes:
                    return f"{minutes}m ago"
                else:
                    return f"{seconds}s ago"
        except:
            return timestr
    
widget = APCUPSd