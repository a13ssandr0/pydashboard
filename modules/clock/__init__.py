from datetime import datetime

from basemod import BaseModule

class Clock(BaseModule):
    def __init__(self, *, format:str, **kwargs):
        super().__init__(**kwargs)
        self.format=format
        
    def __run__(self):
        return datetime.now().strftime(self.format)
    
widget = Clock