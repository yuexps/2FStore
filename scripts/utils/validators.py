#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
验证器模块
统一处理应用信息验证
"""

import re


def validate_app_info(app_id, app_name, repo_url):
    """
    验证应用信息
    
    参数:
    - app_id: 应用ID
    - app_name: 应用名称
    - repo_url: GitHub仓库URL
    
    返回:
    - {'is_valid': bool, 'errors': list}
    """
    errors = []
    
    # 验证应用ID
    if not app_id or not isinstance(app_id, str) or app_id.strip() == '':
        errors.append('应用ID不能为空')
    elif not validate_app_key(app_id):
        errors.append('应用ID只能包含小写字母、数字和连字符')
    
    # 验证应用名称
    if not app_name or not isinstance(app_name, str) or app_name.strip() == '':
        errors.append('应用名称不能为空')
    elif len(app_name) > 100:
        errors.append('应用名称长度不能超过100个字符')
    
    # 验证GitHub仓库URL
    if not repo_url or not isinstance(repo_url, str) or repo_url.strip() == '':
        errors.append('GitHub仓库URL不能为空')
    elif not validate_github_url(repo_url):
        errors.append('请提供有效的GitHub仓库URL')
    
    return {
        'is_valid': len(errors) == 0,
        'errors': errors
    }


def validate_app_key(app_key):
    """
    验证应用唯一标识是否符合规范
    规范要求: 仅允许使用小写字母(a-z)、数字(0-9)和连字符(-)
    
    参数:
    - app_key: 应用唯一标识
    
    返回:
    - bool: 是否符合规范
    """
    if not app_key or not isinstance(app_key, str):
        return False
    return bool(re.match(r'^[a-z0-9-]+$', app_key))


def validate_github_url(url):
    """
    验证是否为有效的GitHub仓库URL
    
    参数:
    - url: URL字符串
    
    返回:
    - bool: 是否为有效的GitHub仓库URL
    """
    if not url or not isinstance(url, str):
        return False
    return bool(re.match(r'^https://github\.com/[^/]+/[^/]+/?$', url))


def parse_github_url(url):
    """
    解析GitHub仓库URL，提取owner和repo
    
    参数:
    - url: GitHub仓库URL
    
    返回:
    - (owner, repo) 元组，解析失败返回 (None, None)
    """
    if not url:
        return None, None
    
    match = re.search(r'github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$', url)
    if match:
        return match.group(1), match.group(2)
    return None, None


def validate_version(version):
    """
    验证版本号格式
    支持: x.y.z, x.y, x, x.y.z-beta 等格式
    
    参数:
    - version: 版本号字符串
    
    返回:
    - bool: 是否为有效版本号
    """
    if not version or not isinstance(version, str):
        return False
    return bool(re.match(r'^\d+(\.\d+)*(-[\w]+)?$', version))
