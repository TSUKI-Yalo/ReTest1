# -*- coding: utf-8 -*-
import os
import yaml
import json
import re


# 获取路径配置
def load_paths_config():
    config_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../config/paths_config.yaml'))
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    return config.get('paths', {})


# 加载 JSON 文件
def load_json_files(ssh_client, directory):
    json_files = {}
    print("查找路径:", directory)

    # 查找所有符合条件的 JSON 文件
    command = f"shopt -s globstar && ls {directory}/**/*.json"
    stdin, stdout, stderr = ssh_client.exec_command(command)
    files = stdout.read().decode().splitlines()
    print("匹配到的文件:", files)

    for file_path in files:
        print("正在加载 JSON 文件:", file_path)
        stdin, stdout, stderr = ssh_client.exec_command(f"cat {file_path}")
        try:
            file_content = stdout.read().decode()
            # 替换内容中的单引号为双引号，以符合 JSON 标准
            file_content = re.sub(r"'", '"', file_content)
            file_name_without_ext = os.path.splitext(os.path.basename(file_path))[0]
            # 后缀替换逻辑
            file_name_modified = re.sub(r'(_[A-Z])$', lambda x: str(ord(x.group(1)[1]) - ord('A') + 1),
                                            file_name_without_ext)
            json_files[file_name_modified] = file_content
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON file {file_path}: {e}")
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")

    return json_files
