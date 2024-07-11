# -*- coding: utf-8 -*-
from src.database.database_connector import connect_to_redis
from src.controllers.controller_connector import connect_to_controller
import json
import time
import random
import string
import threading

# 连接redis
r = connect_to_redis()

# 随机生成字符串
def random_string(length=8):
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))

# 随机生成整数、浮点数和字符串
def random_int():
    return random.randint(1, 1000)

def random_float():
    return random.uniform(1.0, 1000.0)

def random_str():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

# 六级嵌套JSON生成
def nested_json(value):
    return {random_string(): {
        random_string(): {random_string(): {random_string(): {random_string(): {random_string(): value}}}}}}

# 获取Redis服务器CPU使用率
class CPUUsageMonitor:
    def __init__(self):
        self.cpu_usages = []
        self.monitoring = False
        self.thread = None

    def connect(self):
        self.ssh = connect_to_controller()
        if not self.ssh:
            raise RuntimeError("无法建立SSH连接")

    def start_monitoring(self):
        self.cpu_usages = []
        self.monitoring = True
        self.thread = threading.Thread(target=self._monitor)
        self.thread.start()

    def stop_monitoring(self):
        self.monitoring = False
        if self.thread:
            self.thread.join()

    def _monitor(self):
        command = "ps aux | grep 'redis-server *' | grep -v grep | awk '{print $3}'"
        while self.monitoring:
            stdin, stdout, stderr = self.ssh.exec_command(command)
            stdout_output = stdout.read().decode('utf-8').strip()
            cpu_usage_list = [float(cpu) for cpu in stdout_output.split('\n') if cpu]
            if cpu_usage_list:
                self.cpu_usages.append(sum(cpu_usage_list) / len(cpu_usage_list))
            time.sleep(0.1)  # 每100ms采样一次

    def get_cpu_usage_stats(self):
        if not self.cpu_usages:
            return 0.0, 0.0
        avg_cpu_usage = sum(self.cpu_usages) / len(self.cpu_usages)
        max_cpu_usage = max(self.cpu_usages)
        return avg_cpu_usage, max_cpu_usage

def measure_performance(func):
    def wrapper(*args, **kwargs):
        monitor = CPUUsageMonitor()
        monitor.connect()
        monitor.start_monitoring()
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        monitor.stop_monitoring()
        duration = end_time - start_time
        avg_cpu_usage, max_cpu_usage = monitor.get_cpu_usage_stats()
        return result, duration, avg_cpu_usage, max_cpu_usage
    return wrapper

# 执行Redis写操作
@measure_performance
def write_operation(key, value):
    existing_value = r.get(key)
    if existing_value:
        existing_value = json.loads(existing_value)
        if isinstance(existing_value, dict):
            existing_value.update(value)
            r.set(key, json.dumps(existing_value))
    else:
        r.set(key, json.dumps(value))

# 执行Redis读操作
@measure_performance
def read_operation(key):
    return json.loads(r.get(key))

# 清除所有键
def clear_all_keys():
    r.flushdb()

# 测试主节点和六级嵌套节点的性能
def test_performance():
    # 清除所有键
    clear_all_keys()
    #操作次数
    operations = 1
    #数据类型
    data_types = {
        'int': random_int,
        'float': random_float,
        'string': random_str
    }

    def execute_tests(node_type, key_prefix, value_generator):
        durations = []
        cpu_usages = []
        max_cpu_usages = []
        for _ in range(operations):
            key = f'{key_prefix}_{node_type}'
            value = value_generator() if node_type == 'root' else nested_json(value_generator())
            if node_type == 'root':
                # 主节点的数据结构是 {hhh: {value}}
                value = {random_string(): value}
            write_result, write_duration, write_cpu, write_max_cpu = write_operation(key, value)
            read_result, read_duration, read_cpu, read_max_cpu = read_operation(key)
            durations.extend([write_duration, read_duration])
            cpu_usages.extend([write_cpu, read_cpu])
            max_cpu_usages.extend([write_max_cpu, read_max_cpu])

        avg_duration = sum(durations) / len(durations)
        avg_cpu_usage = sum(cpu_usages) / len(cpu_usages)
        max_cpu_usage = max(max_cpu_usages)
        return avg_duration, avg_cpu_usage, max_cpu_usage

    for data_type, value_generator in data_types.items():
        root_avg_duration, root_avg_cpu_usage, root_max_cpu_usage = execute_tests('root', data_type, value_generator)
        print(f"Root Node - {data_type} - Average Duration: {root_avg_duration:.6f}s, "
              f"Average CPU Usage: {root_avg_cpu_usage:.2f}%, "
              f"Max CPU Usage: {root_max_cpu_usage:.2f}%")

        nested_avg_duration, nested_avg_cpu_usage, nested_max_cpu_usage = execute_tests('nested', data_type, value_generator)
        print(f"Nested Node - {data_type} - Average Duration: {nested_avg_duration:.6f}s, "
              f"Average CPU Usage: {nested_avg_cpu_usage:.2f}%, "
              f"Max CPU Usage: {nested_max_cpu_usage:.2f}%")

if __name__ == "__main__":
    test_performance()
