from basemod import BaseModule
from subprocess import run
import os, pty
from select import select



class CmdRunner(BaseModule):
    def __init__(self, *, args:list[str], pipe_stdout=True, pipe_stderr=True, wraplines=False, **kwargs):
        self.args=args
        self.master_fd, self.slave_fd = pty.openpty()
        self.stdout_pipe=self.slave_fd if pipe_stdout else None
        self.stderr_pipe=self.slave_fd if pipe_stderr else None
        super().__init__(**kwargs)
        if wraplines:
            self.inner.styles.width = self.content_width
            
        self._screen = ''
    
    def __post_init__(self):
        env = os.environ
        env['COLUMNS']= str(self.content_width)
        env['LINES']= str(self.content_height)
        
        proc = run(args=self.args, env=env, stdout=self.stdout_pipe, stderr=self.stderr_pipe)
        
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

            # if proc.poll() is not None and not ready:
            if not ready:
                break

    def __call__(self):
        # output = ''
        # while os.re:
        #     o:=os.read(self.master_fd, 1024)
        #     output += o.decode()
        return self._screen
        # thread = Thread(target = self.run_task)
        # thread.run()

    
widget = CmdRunner