# -*- coding: utf-8 -*-
import os
import json
import PySimpleGUI as sg

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
    except (json.JSONDecodeError, IOError) as e:
        sg.popup_error(f'加载配置文件失败: {e}\n将使用默认设置。')
        return {}

def save_config(cfg):
    """
    将配置字典保存到 config.json。
    """
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=4)
        return True
    except IOError as e:
        sg.popup_error(f'保存配置文件失败: {e}')
        return False