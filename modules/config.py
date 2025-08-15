# -*- coding: utf-8 -*-
import os
import json

CONFIG_FILE = 'config.json'

def load_config():
    """
    从 config.json 加载配置。
    如果文件不存在或内容无效，则返回一个空字典。
    """
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        # 加载失败时，静默返回空字典，让UI层决定如何处理
        return {}

def save_config(cfg):
    """
    将配置字典保存到 config.json。
    成功返回True，失败则引发异常。
    """
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=4)
        return True
    except IOError as e:
        raise e # 将异常传递给调用者