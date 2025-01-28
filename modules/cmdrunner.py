import os
import pty
from select import select
from shlex import split
from subprocess import run

from containers import BaseModule


class CmdRunner(BaseModule):
    def __init__(self, *, args:str|list[str], pipe_stdout=True, pipe_stderr=True, wraplines=False, shell=False, **kwargs):
        super().__init__(**kwargs)
        self.args=args if shell or isinstance(args, list) else split(args)
        self.shell=shell
        self.master_fd, self.slave_fd = pty.openpty()
        self.stdout_pipe=self.slave_fd if pipe_stdout else None
        self.stderr_pipe=self.slave_fd if pipe_stderr else None
        self.wraplines=wraplines
        self._screen = ''
    
    def __post_init__(self):
        if self.wraplines:
            self.inner.styles.width = self.content_size.width
    
    def run(self):
        env = os.environ
        env['COLUMNS']= str(self.content_size.width)
        env['LINES']= str(self.content_size.height)
        
        proc = run(args=self.args, env=env, stdout=self.stdout_pipe, stderr=self.stderr_pipe, shell=self.shell)
        
        self._screen = ''
        
        while True:
            ready, _, _ = select((self.master_fd,), (), (), .1)

            if self.master_fd in ready:
                next_line_to_process = os.read(self.master_fd, 1024)
                if next_line_to_process:
                    # process the output
                    self._screen += next_line_to_process.decode()
                elif proc.returncode is not None:
                    # The program has exited, and we have read everything written to stdout
                    ready = filter(lambda x: x is not self.master_fd, ready)

            if not ready:
                break

    def __call__(self):
        self.run()
        return self._screen

    
widget = CmdRunner