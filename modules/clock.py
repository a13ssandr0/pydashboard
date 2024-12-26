from datetime import datetime

from basemod import BaseModule

class Clock(BaseModule):
    def __init__(self, *, format:str, **kwargs):
        self.format=format
        super().__init__(**kwargs)
        
    def __call__(self):
        return datetime.now().strftime(self.format)
    
widget = Clock