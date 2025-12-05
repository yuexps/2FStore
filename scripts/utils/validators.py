#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
验证器模块
统一处理应用信息验证
"""

import re
import base64

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


def _process_word_list(word_list):
    """
    处理词汇列表
    
    参数:
    - word_list: 词汇列表
    
    返回:
    - list: 处理后的词汇列表
    """
    processed = []
    for item in word_list:
        try:
            processed_item = base64.b64decode(item).decode('utf-8')
            processed.append(processed_item)
        except:
            continue
    return processed

# 合规检查参考词汇（编码存储）
_LEGAL_REFERENCE_WORDS = [
    '6Imy5oOF', '6LWM5Y2a', '5Y2a5b2p', '5b2p56Wo', '6LWM55CD', '6ICB6JmO5py6', '5qOL54mM5ri45oiP', '6LWM5Zy6',
    '5q+S5ZOB', '5aSn6bq7', '5rW35rSb5Zug', '5Y+v5Y2h5Zug', '5Yaw5q+S', '5pGH5aS05Li4', 'UysreSQ==',
    '6K+I6aqX', '5qy66K+I', '5Lyg6ZSA', '6Z2e5rOV6ZuG6LWE', '5rSX6ZKx', '5YG356iO5ryP56iO',
    '55uX54mI', '56C06Kej', '5L615p2D', '6Z2e5rOV5LiL6L29', '57+75aKZ', 'VlBO', '5Luj55CG5pyN5Yqh5Zmo',
    '5pq05Yqb', '5oGQ5oCW', '5p2A5Lq6', '6Ieq5p2A', '6Ieq5q6L', '6KGA6IWl', '6YW35YiR',
    '5pS/5rK75pWP5oSf', '5Y+N5YWx', '5Y+N5pS/5bqc', '5YiG6KOC', '6YKq5pWZ', '5p6B56uv5Li75LmJ',
    '6buR5a6i', '5YWl5L61', '5pyo6ams', '5oG25oSP6L2v5Lu2', '6ZKT6bG8', '55uX56qD', '5pyq5oiQ5bm05Lq65LiN5a6c',
    '6KO46Zyy', '5oCn6KGM5Li6', '5oCn5pqX56S6', '6buE6Imy', '5rer56e9', '5L2O5L+X'
]

# 英文参考词汇（编码存储）
_ENGLISH_REFERENCE_WORDS = [
    'cG9ybg==', 'Z2FtYmxpbmc=', 'Y2FzaW5v', 'ZHJ1Zw==', 'aGVyb2lu', 'Y29jYWluZQ==', 'bWV0aA==', 'ZnJhdWQ==',
    'c2NhbQ==', 'cGlyYWN5', 'Y3JhY2s=', 'aGFjaw==', 'dHJvamFu', 'bWFsd2FyZQ==', 'cGhpc2hpbmc=',
    'dmlvbGVuY2U=', 'dGVycm9y', 'c3Vpc2lkZQ==', 'bnVkZQ==', 'c2V4', 'b2JzY2VuZQ==', 'dnVsZ2Fy'
]

# 加载参考词汇
LEGAL_SENSITIVE_WORDS = _process_word_list(_LEGAL_REFERENCE_WORDS)
ENGLISH_SENSITIVE_WORDS = _process_word_list(_ENGLISH_REFERENCE_WORDS)


def check_content_guidelines(text):
    """
    检查文本是否符合内容指南
    
    参数:
    - text: 要检查的文本内容
    
    返回:
    - tuple: (is_acceptable: bool, flagged_items: list)
        - is_acceptable: 是否符合内容指南
        - flagged_items: 标记的项目列表
    """
    if not text or not isinstance(text, str):
        return True, []
    
    flagged_items = []
    lower_text = text.lower()
    
    # 检查中文参考词汇
    for word in LEGAL_SENSITIVE_WORDS:
        if word in text:
            flagged_items.append(word)
    
    # 检查英文参考词汇
    for word in ENGLISH_SENSITIVE_WORDS:
        if word in lower_text:
            flagged_items.append(word)
    
    return len(flagged_items) == 0, flagged_items


def validate_content(app_name, app_description):
    """
    验证应用名称和描述的内容
    
    参数:
    - app_name: 应用名称
    - app_description: 应用描述
    
    返回:
    - {'is_valid': bool, 'errors': list}
    """
    errors = []
    
    # 检查应用名称
    if app_name:
        is_acceptable, flagged_items = check_content_guidelines(app_name)
        if not is_acceptable:
            errors.append(f'应用名称包含不当内容: {"、".join(flagged_items)}')
    
    # 检查应用描述
    if app_description:
        is_acceptable, flagged_items = check_content_guidelines(app_description)
        if not is_acceptable:
            errors.append(f'应用描述包含不当内容: {"、".join(flagged_items)}')
    
    return {
        'is_valid': len(errors) == 0,
        'errors': errors
    }