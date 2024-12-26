from basemod import BaseModule
from subprocess import run, PIPE, STDOUT

class CmdRunner(BaseModule):
    def __init__(self, *, args:list[str], pipe_stdout=True, pipe_stderr=True, **kwargs):
        self.args=args
        self.stdout_pipe=PIPE if pipe_stdout else None
        self.stderr_pipe=STDOUT if pipe_stderr else None
        super().__init__(**kwargs)
        
    def __call__(self):
        return run(args=self.args, stdout=self.stdout_pipe, stderr=self.stderr_pipe).stdout.decode()
    
widget = CmdRunner