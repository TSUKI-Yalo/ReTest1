# -*- coding: utf-8 -*-
import os
import pytest
import redis.exceptions
import json
from src.controllers.controller_connector import get_controller_files
from src.database.database_connector import connect_to_redis, get_redis_data


def normalize_key(key):
    return key.lower().replace('_', '').replace(' ', '')

def clean_content(content):
    if isinstance(content, str):
        return content.replace(" ", "").replace("\n", "").replace("\r", "")
    return content
def generate_report(report_data, report_path):
    directory = os.path.dirname(report_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(report_path, 'w', encoding='utf-8') as report_file:
        json.dump(report_data, report_file, ensure_ascii=False, indent=4)
    print(f"报告已生成: {report_path}")

def test_compare_filenames_and_redis_keys():
    report = {"errors": []}
    try:
        controller_files = get_controller_files()
    except Exception as e:
        report["errors"].append(f"获取控制器文件时发生错误: {type(e).__name__}: {str(e)}")
    try:
        redis_client = connect_to_redis()
        if not redis_client:
            report["errors"].append("无法连接到 Redis")
    except redis.exceptions.ConnectionError as e:
        report["errors"].append(f"连接 Redis 服务器失败: {type(e).__name__}: {str(e)}")
    except OSError as e:
        report["errors"].append(f"获取 Redis 数据失败：{type(e).__name__}: {str(e)}")

    if report["errors"]:
        generate_report(report, 'report/test_report_compare.json')
        return
    # 规范化并提取控制器文件名
    normalized_controller_keys = {normalize_key(key): key for key in controller_files.keys()}
    for norm_key, original_key in normalized_controller_keys.items():
        try:
            # 检查 Redis 中是否存在对应的键
            redis_key = normalized_controller_keys[norm_key]
            redis_content = get_redis_data(redis_client, redis_key)

            if redis_content is None:
                report["errors"].append(f"Redis 中缺少键: {redis_key}")
                continue
            # 获取控制器文件的内容
            controller_content = controller_files[original_key]
            # 从 Redis 内容中提取与文件名对应的部分
            if isinstance(redis_content, dict) and redis_key in redis_content:
                redis_content = redis_content[redis_key]
            # 去除空格和回车
            cleaned_redis_content = clean_content(redis_content)
            cleaned_controller_content = clean_content(controller_content)
            # 比较内容
            if cleaned_controller_content != cleaned_redis_content:
                report["errors"].append(f"键 {original_key} 对应的内容不一致")
        except Exception as e:
            report["errors"].append(f"处理键 {original_key} 时发生错误: {type(e).__name__}: {str(e)}")
    generate_report(report, 'report/test_report_compare.json')


if __name__ == "__main__":
    pytest.main()
