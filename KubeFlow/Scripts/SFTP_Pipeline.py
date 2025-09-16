import os
import paramiko
import json 

def upload_dir(sftp, local_dir, remote_dir):
    """Recursively upload a folder"""
    try:
        sftp.chdir(remote_dir)
    except IOError:
        sftp.mkdir(remote_dir)
        sftp.chdir(remote_dir)

    for item in os.listdir(local_dir):
        local_path = os.path.join(local_dir, item)
        remote_path = f"{remote_dir}/{item}"
        if os.path.isfile(local_path):
            sftp.put(local_path, remote_path)
            print(f"Uploaded {local_path} → {remote_path}")
        else:
            upload_dir(sftp, local_path, remote_path)

def download_dir(sftp, remote_dir, local_dir):
    """Recursively download a folder"""
    print(f"Downloading {remote_dir} to {local_dir}")
    os.makedirs(local_dir, exist_ok=True)
    sftp.chdir(remote_dir)

    for item in sftp.listdir():
        remote_path = f"{remote_dir}/{item}"
        local_path = os.path.join(local_dir, item)
        if is_sftp_dir(sftp, remote_path):
            download_dir(sftp, remote_path, local_path)
        else:
            sftp.get(remote_path, local_path)
            print(f"Downloaded {remote_path} → {local_path}")

def is_sftp_dir(sftp, path):
    try:
        return paramiko.SFTPAttributes.from_stat(sftp.stat(path)).st_mode & 0o40000 == 0o40000
    except IOError:
        return False
    
def upload_to_remote(alias, local_folder, remote_folder, ssh_folder="~/.ssh"):
    ssh = paramiko.SSHClient()
    ssh_config = paramiko.SSHConfig()
    with open(os.path.expanduser(ssh_folder+"/config")) as f:
        ssh_config.parse(f)
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    cfg = ssh_config.lookup(alias)

    hostname = cfg.get("hostname")
    username = cfg.get("user")
    port = int(cfg.get("port", 22))
    key_filename = os.path.expanduser(cfg.get("identityfile", [f"{ssh_folder}/id_rsa"])[0])

    # Connect using parsed config
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh.connect(
        hostname=hostname,
        port=port,
        username=username,
        key_filename=key_filename,
    )

    with open(os.path.expanduser("~/.maia-hpc/server_configs/{}.json".format(alias))) as f:
        config = json.load(f)

    project_dir = config.get("project_dir", "")
    sftp = ssh.open_sftp()
    upload_dir(sftp, local_folder, os.path.join(project_dir, remote_folder))
    sftp.close()
    ssh.close()


def download_from_remote(alias, remote_folder, local_folder, ssh_folder="~/.ssh"):
    ssh = paramiko.SSHClient()
    ssh_config = paramiko.SSHConfig()
    with open(os.path.expanduser(ssh_folder+"/config")) as f:
        ssh_config.parse(f)
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    cfg = ssh_config.lookup(alias)

    hostname = cfg.get("hostname")
    username = cfg.get("user")
    port = int(cfg.get("port", 22))
    key_filename = os.path.expanduser(cfg.get("identityfile", [f"{ssh_folder}/id_rsa"])[0])

    # Connect using parsed config
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh.connect(
        hostname=hostname,
        port=port,
        username=username,
        key_filename=key_filename,
    )

    with open(os.path.expanduser("~/.maia-hpc/server_configs/{}.json".format(alias))) as f:
        config = json.load(f)

    project_dir = config.get("project_dir", "")
    sftp = ssh.open_sftp()
    download_dir(sftp, os.path.join(project_dir, remote_folder), local_folder)
    sftp.close()
    ssh.close()
    
    
#upload_to_remote("pdc","/home/maia-user/shared/nnUNet/","Data/nnUNet/")
#upload_to_remote("pdc","/home/maia-user/shared/MONet_Bundle/","Data/MONet_Bundle/")

#download_from_remote("pdc","Data/MONet_Bundle/Task09/MONetBundle/models/fold_0/","/home/maia-user/shared/MONet_Bundle/PL/Task09/fold_0/")