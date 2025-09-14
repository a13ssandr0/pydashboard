from collections import defaultdict
from multiprocessing import Lock

import rpyc
from loguru import logger
from plumbum import SshMachine
from plumbum.machines.ssh_machine import SshTunnel
from rpyc import Connection
rpyc.core.protocol.DEFAULT_CONFIG['allow_pickle'] = True


class SessionManager:
    active_ssh: dict[str, SshMachine] = {}
    active_tunnels: dict[str, SshTunnel] = {}
    active_sessions: dict[str, Connection] = {}
    active_sessions_count: dict[str, int] = defaultdict(lambda: 0)
    lock = Lock()
    logger = logger.bind(module="SSHSessionManager")

    @classmethod
    def create_connection(cls, host, user=None, port=None, keyfile=None, password=None,
                          ssh_strict_host_key_checking=None, ssh_ignore_known_hosts_file=None):
        with cls.lock:
            cls.logger.info('Connecting to {}', host)
            conn_id = f'{user}@{host}:{port}'
            if conn_id not in cls.active_ssh:
                ssh_opts = []
                if ssh_strict_host_key_checking is not None:
                    if ssh_strict_host_key_checking is True:
                        ssh_opts.append('-oStrictHostKeyChecking=yes')
                    elif ssh_strict_host_key_checking is False:
                        ssh_opts.append('-oStrictHostKeyChecking=no')
                    elif ssh_strict_host_key_checking == 'accept-new':
                        ssh_opts.append('-oStrictHostKeyChecking=accept-new')

                if ssh_ignore_known_hosts_file:
                    ssh_opts.append('-oUserKnownHostsFile=/dev/null')

                cls.active_ssh[conn_id] = SshMachine(host=host, user=user, port=port, keyfile=keyfile,
                                                     password=password, ssh_opts=ssh_opts)
                cls.logger.debug("Opened connection to {}", cls.active_ssh[conn_id])
            if conn_id not in cls.active_tunnels:
                cls.active_tunnels[conn_id] = cls.active_ssh[conn_id].tunnel(0, 60001)
                cls.logger.debug("Opened tunnel {}", cls.active_tunnels[conn_id])

        return conn_id

    @classmethod
    def create_session(cls, conn_id, module_name, setter_function=None):
        sess_id = f'{conn_id};{module_name}'
        if sess_id not in cls.active_sessions:
            cls.active_sessions[sess_id] = rpyc.connect('127.0.0.1', cls.active_tunnels[conn_id].lport, config=rpyc.core.protocol.DEFAULT_CONFIG)
            cls.logger.debug("Opened connection to {}", cls.active_sessions[sess_id])
            cls.active_sessions[sess_id].root.import_module(module_name, setter_function)

        cls.active_sessions_count[conn_id] += 1

        cls.logger.success('Opened connection to {}:{} via SSH tunnel', cls.active_ssh[conn_id].host,
                       cls.active_tunnels[conn_id].lport)
        return cls.active_sessions[sess_id].root, sess_id

    @classmethod
    def close(cls, *, sess_id=None, conn_id=None):
        with cls.lock:
            if conn_id and conn_id in cls.active_ssh:
                for act_sess in cls.active_sessions.copy():
                    if act_sess.split(';')[0] == conn_id:
                        cls.__close_session(act_sess)
                cls.active_sessions_count[conn_id] = 0
                if conn_id in cls.active_tunnels:
                    cls.__close_tunnel(conn_id)
                if conn_id in cls.active_ssh:
                    cls.__close_ssh(conn_id)
                return

            if sess_id and sess_id in cls.active_sessions_count:
                cls.active_sessions_count[sess_id] -= 1
                if cls.active_sessions_count[sess_id] < 1:
                    if sess_id in cls.active_sessions:
                        cls.__close_session(sess_id)

                    conn_id = sess_id.split(';')[0]
                    if conn_id in cls.active_tunnels:
                        cls.__close_tunnel(conn_id)
                    if conn_id in cls.active_ssh:
                        cls.__close_ssh(conn_id)

    @classmethod
    def __close_session(cls, sess_id):
        session = cls.active_sessions.pop(sess_id)
        cls.logger.debug("Closing session {}", session)
        session.close()

    @classmethod
    def __close_tunnel(cls, conn_id):
        tunnel = cls.active_tunnels.pop(conn_id)
        cls.logger.debug("Closing tunnel {}", tunnel)
        tunnel.close()

    @classmethod
    def __close_ssh(cls, conn_id):
        ssh = cls.active_ssh.pop(conn_id)
        cls.logger.debug("Closing SSH connection", ssh)
        ssh.close()

    @classmethod
    def close_all(cls):
        with cls.lock:
            for conn in cls.active_sessions.values():
                conn.close()

            for tunnel in cls.active_tunnels.values():
                tunnel.close()

            for ssh in cls.active_ssh.values():
                ssh.close()

    def __new__(cls):
        raise TypeError('Static classes cannot be instantiated')
