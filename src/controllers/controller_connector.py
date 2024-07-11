import paramiko
import yaml
import os
import src.utils.file_utils


def load_controller_config():
    config_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../config/controller_config.yaml'))
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    return config

def connect_to_controller():
    config = load_controller_config()
    try:
        # 建立 SSH 连接
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(config['host'], username=config['username'], password=config['password'])
        print("成功连接到控制器。")
        # 返回 SSH 连接对象
        return ssh

    except paramiko.AuthenticationException:
        print("身份验证失败，请检查您的凭据。")
        return None

    except paramiko.SSHException as e:
        print(f"SSH 连接失败：{e}")
        return None

    except Exception as e:
        print(f"发生错误：{e}")
        return None

def get_controller_files():
    try:
        ssh = connect_to_controller()
        if not ssh:
            return {}
        paths_config = src.utils.file_utils.load_paths_config()
        all_json_files = {}
        for path_info in paths_config:
            path = path_info['path']
            json_files = src.utils.file_utils.load_json_files(ssh, path)
            all_json_files.update(json_files)
        ssh.close()
        return all_json_files
    except Exception as e:
        print(f"发生错误：{e}")
        return {}
