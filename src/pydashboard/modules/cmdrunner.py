import os
import pty
from select import select
from shlex import split
from subprocess import run
from typing import Any

from pydashboard.containers import BaseModule
from pydashboard.utils.types import Size


class CmdRunner(BaseModule):
    def __init__(self, *, args: str | list[str], pipe_stdout: bool = True, pipe_stderr: bool = True,
                 wraplines: bool = False, shell: bool = False, **kwargs: Any):
        """
        Run a terminal command, if any of pipe_stdout or pipe_stderr are set, command will be run in a pseudo-terminal (pty).

        Args:
            args:
            pipe_stdout: Capture output from stdout
            pipe_stderr: Capture output from stderr
            wraplines: Wrap lines longer than widget width
            shell: Run command in a shell (allows glob expansion, piping and redirection)
            **kwargs: See [BaseModule](../containers/basemodule.md)
        """
        super().__init__(args=args, pipe_stdout=pipe_stdout, pipe_stderr=pipe_stderr, wraplines=wraplines, shell=shell,
                         **kwargs)
        self.args = args if shell or isinstance(args, list) else split(args)
        self.shell = shell
        self.master_fd, self.slave_fd = pty.openpty()
        self.stdout_pipe = self.slave_fd if pipe_stdout else None
        self.stderr_pipe = self.slave_fd if pipe_stderr else None
        self.wraplines = wraplines
        self._screen = ''

    def __post_init__(self):
        if self.wraplines and not self.remote_root:
            self.inner.styles.width = self.content_size.width

    def run(self, content_size: Size):
        env = os.environ | {
            'LINES'  : str(content_size[0]),
            'COLUMNS': str(content_size[1]),
        }

        proc = run(args=self.args, env=env, stdout=self.stdout_pipe, stderr=self.stderr_pipe, shell=self.shell)
        self.logger.debug('Running {}', self.args if isinstance(self.args, str) else ' '.join(self.args))

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

    def __call__(self, content_size: Size):
        self.run(content_size=content_size)
        return self._screen


widget = CmdRunner
