from threading import Thread
from basemod import BaseModule
from subprocess import run, PIPE, STDOUT
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
        
    def run_task(self):
        env = os.environ
        env['COLUMNS']= str(self.content_width)
        env['LINES']= str(self.content_height)
        
        proc = run(args=self.args, env=env, stdout=self.stdout_pipe, stderr=self.stderr_pipe)
        
        while True:
            [ready, *_], _, _ = select((self.master_fd,), (), (), .1)

            if proc.stdout in ready:
                next_line_to_process = os.read
                if next_line_to_process:
                    # process the output
                    self.inner.update(next_line_to_process)
                elif proc.returncode is not None:
                    # The program has exited, and we have read everything written to stdout
                    ready = filter(lambda x: x is not proc.stdout, ready)

            if proc.poll() is not None and not ready:
                break

    def __call__(self):
        # output = ''
        # while os.re:
        #     o:=os.read(self.master_fd, 1024)
        #     output += o.decode()
        self.inner.update('Testing')
        # thread = Thread(target = self.run_task)
        # thread.run()

    
widget = CmdRunner