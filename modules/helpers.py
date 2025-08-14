# -*- coding: utf-8 -*-
import datetime

def now_str():
    """获取当前本地时间字符串，格式为 YYYY-MM-DD HH:MM"""
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

def get_beijing_time():
    """获取北京时间字符串"""
    return (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')

def get_utc_time():
    """获取UTC时间字符串"""
    return datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')