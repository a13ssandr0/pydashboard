from collections import defaultdict
from functools import cache
from multiprocessing import Lock

import rpyc
from loguru import logger
from plumbum import SshMachine
from plumbum.machines.ssh_machine import SshTunnel
from rpyc import Connection


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


class SSHManager:
    active_ssh: dict[str, SshMachine] = {}
    active_tunnels: dict[str, SshTunnel] = {}
    active_sessions: dict[str, Connection] = {}
    active_connections: dict[str, int] = defaultdict(lambda: 0)
    lock = Lock()

    @classmethod
    def create_session(cls, host, user=None, port=None, keyfile=None, password=None):
        with cls.lock:
            logger.info('Connecting to {}', host)
            sess_id = f'{user}@{host}:{port}'
            if sess_id not in cls.active_ssh:
                cls.active_ssh[sess_id] = SshMachine(host=host, user=user, port=port, keyfile=keyfile,
                                                     password=password)
                logger.debug("Opened connection to {}", cls.active_ssh[sess_id])
            if sess_id not in cls.active_tunnels:
                cls.active_tunnels[sess_id] = cls.active_ssh[sess_id].tunnel(0, 60001)
                logger.debug("Opened tunnel {}", cls.active_tunnels[sess_id])
            if sess_id not in cls.active_sessions:
                cls.active_sessions[sess_id] = rpyc.connect('127.0.0.1', cls.active_tunnels[sess_id].lport)
                logger.debug("Opened connection to {}", cls.active_sessions[sess_id])

            cls.active_connections[sess_id] += 1

            logger.success('Opened connection to {}:{} via SSH tunnel', host, cls.active_tunnels[sess_id].lport)
            return cls.active_sessions[sess_id].root, sess_id

    @classmethod
    def close_session(cls, sess_id):
        with cls.lock:
            cls.active_connections[sess_id] -= 1
            if cls.active_connections[sess_id] < 1:
                if sess_id in cls.active_sessions:
                    session = cls.active_sessions.pop(sess_id)
                    logger.debug("Closing session {}", session)
                    session.close()
                if sess_id in cls.active_tunnels:
                    tunnel = cls.active_tunnels.pop(sess_id)
                    logger.debug("Closing tunnel {}", tunnel)
                    tunnel.close()
                if sess_id in cls.active_ssh:
                    ssh = cls.active_ssh.pop(sess_id)
                    logger.debug("Closing SSH connection", ssh)
                    ssh.close()

    def __new__(cls):
        raise TypeError('Static classes cannot be instantiated')
