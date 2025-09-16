import paramiko
import os
import threading

_ssh_client = None
_ssh_lock = threading.Lock()

def get_ssh_client(alias="localhost", keepalive=30):
    """
    Return a persistent SSH client based on an alias in ~/.ssh/config.
    If the client already exists and is alive, reuse it.
    """
    global _ssh_client

    with _ssh_lock:
        # Reuse existing connection if active
        if _ssh_client is not None:
            transport = _ssh_client.get_transport()
            if transport is not None and transport.is_active():
                return _ssh_client

        # Parse ~/.ssh/config
        ssh_config = paramiko.SSHConfig()
        config_path = os.path.expanduser("~/.ssh/config")
        with open(config_path) as f:
            ssh_config.parse(f)

        host_config = ssh_config.lookup(alias)

        # Extract config details
        hostname = host_config.get("hostname", alias)
        username = host_config.get("user")
        key_filename = host_config.get("identityfile", [None])[0]
        port = int(host_config.get("port", 22))

        # Create new SSH client
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname,
            port=port,
            username=username,
            key_filename=key_filename,
            look_for_keys=True,
            allow_agent=True,
        )

        # Keep alive
        transport = client.get_transport()
        if transport is not None and keepalive > 0:
            transport.set_keepalive(keepalive)

        _ssh_client = client
        return _ssh_client
