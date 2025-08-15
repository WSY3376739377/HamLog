# -*- coding: utf-8 -*-
import datetime
import sys
import os

def get_resource_path(relative_path):
    """ 获取资源的绝对路径，兼容开发环境和PyInstaller打包环境 """
    if getattr(sys, 'frozen', False):
        # 如果是打包状态 (运行 .exe)
        base_path = os.path.dirname(sys.executable)
    else:
        # 如果是开发状态 (运行 .py)
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def now_str():
    """获取当前本地时间字符串，格式为 YYYY-MM-DD HH:MM"""
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

def get_beijing_time():
    """获取北京时间字符串"""
    return (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')

def get_utc_time():
    """获取UTC时间字符串"""
    return datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')