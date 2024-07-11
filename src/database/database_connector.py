# -*- coding: utf-8 -*-
import json
import redis
import os
import yaml

def load_controller_config():
    config_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../config/database_config.yaml'))
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    return config

def connect_to_redis():
    config = load_controller_config()
    try:
        # 连接到 Redis
        redis_client = redis.StrictRedis(
            host=config['redis_host'],
            port=config['redis_port'],
            db=config['redis_db'],
            username=config['redis_username'],
            password=config['redis_password'],
            decode_responses=True  # 确保返回的键和值都是字符串类型
        )
        print("成功连接到 Redis。")
        return redis_client

    except Exception as e:
        print(f"Redis 连接失败：{e}")
        return None

def get_redis_data(redis_client, key):
    try:
        value = redis_client.execute_command("JSON.GET", key)
        if value:
            value = value.replace(" ", "").replace("\n", "")
            return value  # 返回 JSON 字符串值
        return None
    except Exception as e:
        print(f"获取 Redis 数据失败：{e}")
        return None

def main():
    redis_client = connect_to_redis()
    if not redis_client:
        return

    # 获取所有键
    keys = redis_client.keys('*')
    print(f"Redis 中的所有键: {keys}")

    # 获取每个键对应的数据
    for key in keys:
        data = get_redis_data(redis_client, key)
        print(f"键: {key}, 数据: {data}")


if __name__ == "__main__":
    main()