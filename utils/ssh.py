from functools import cache

from plumbum import SshMachine


class SSHMachine(SshMachine):
    @cache
    def __new__(cls, host, user=None, port=None, keyfile=None, ssh_command=None, scp_command=None, ssh_opts=(),
                scp_opts=(), password=None, encoding="utf8", connect_timeout=10, new_session=False):
        return super().__new__(cls)

    @cache
    def tunnel(self, lport, dport, lhost="localhost", dhost="localhost", connect_timeout=5, reverse=False):
        return super().tunnel(lport, dport, lhost, dhost, connect_timeout, reverse)

    def __del__(self):
        print("closing ssh connection")
        self.close()

