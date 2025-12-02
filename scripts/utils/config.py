#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
项目配置和路径管理
"""

import os

def get_project_root():
    """获取项目根目录"""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_scripts_dir():
    """获取scripts目录"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_data_path(filename=''):
    """获取data目录路径，可选择性拼接文件名"""
    data_dir = os.path.join(get_project_root(), 'data')
    if filename:
        return os.path.join(data_dir, filename)
    return data_dir

def get_apps_json_path():
    """获取apps.json文件路径"""
    return os.path.join(get_project_root(), 'apps.json')

def get_fnpacks_json_path():
    """获取fnpacks.json文件路径"""
    return os.path.join(get_project_root(), 'fnpacks.json')

def get_app_details_path():
    """获取app_details.json文件路径"""
    return get_data_path('app_details.json')

def get_fnpack_details_path():
    """获取fnpack_details.json文件路径"""
    return get_data_path('fnpack_details.json')

def ensure_data_dir():
    """确保data目录存在"""
    data_dir = get_data_path()
    os.makedirs(data_dir, exist_ok=True)
    return data_dir
