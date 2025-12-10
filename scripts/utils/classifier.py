#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
应用分类模块
根据应用名称和描述自动确定分类
"""


# 分类关键词映射
CATEGORY_KEYWORDS = {
    'games': [
        '游戏', 'game', 'gaming', '休闲', 'entertainment', '娱乐',
        'play', 'player', 'arcade', 'puzzle', 'rpg', 'strategy'
    ],
    'media': [
        '视频', '音乐', 'video', 'music', 'player', '播放', 'audio',
        'image', '图片', 'photo', 'gallery', 'stream', '流媒体',
        'emby', 'jellyfin', 'plex', 'movie', '电影', 'tv', '电视'
    ],
    'network': [
        '网络', 'net', 'browser', '浏览器', 'vpn', '代理', 'proxy',
        '连接', 'connect', 'wifi', 'v2ray', 'clash', 'trojan',
        'shadowsocks', 'wireguard', 'frp', 'ddns', 'dns',
        '网盘', 'drive', 'cloud', '云', 'nas', 'webdav', 'alist', 'cloudreve'  # Storage merged here
    ],
    'development': [
        '开发', 'dev', 'code', '编程', 'program', 'ide', 'editor',
        '开发工具', 'developer', 'git', 'docker', 'container',
        '容器', 'kubernetes', 'k8s', 'ci', 'cd', 'jenkins'
    ],
    'system': [
        '系统', 'system', '设置', 'setting', '优化', 'optimize',
        '管理', 'manager', '监控', 'monitor', 'terminal', '终端',
        'shell', 'ssh', 'admin', '管理员', 'backup', '备份',
        '安全', 'security', '密码', 'password', '加密', 'encrypt',  # Security merged here
        'vault', 'auth', '认证', 'firewall', '防火墙', 'antivirus',
        '存储', 'storage', 'file', '文件'  # Local storage merged here
    ],
    'productivity': [
        '办公', 'office', '文档', 'document', '效率', 'productivity',
        '笔记', 'note', 'todo', 'task', 'calendar', '日历',
        'markdown', 'wiki', 'knowledge', '知识库'
    ],
    'utility': [
        '工具', 'utility', '计算器', 'calculator', '转换', 'convert',
        '下载', 'download', '搜索', 'search', '助手', 'helper',
        'tool', 'toolkit', '同步', 'sync', 'transfer', '传输'
    ]
}


import re

def auto_classify_app(name, description=''):
    """
    智能分类函数 - 根据应用名称和描述自动确定分类
    
    参数:
    - name: 应用名称
    - description: 应用描述
    
    返回:
    - str: 分类名称，默认为 'uncategorized'
    """
    if not name:
        return 'uncategorized'
    
    # 预处理文本
    name_lower = name.lower()
    desc_lower = (description or '').lower()
    
    # 计算每个分类的匹配分数
    best_category = 'uncategorized'
    highest_score = 0
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            # 判断关键词是否为纯英文（用于区分匹配模式）
            is_english = all(ord(c) < 128 for c in keyword)
            
            # 定义匹配加分函数
            def check_match(text, weight):
                if not text: return 0
                count = 0
                if is_english:
                    # 英文使用正则全词匹配，避免 "net" 匹配 "planet"
                    # \b 是单词边界
                    if re.search(r'\b' + re.escape(keyword) + r'\b', text):
                        count += weight
                else:
                    # 中文使用子串匹配
                    if keyword in text:
                        count += weight
                return count

            # 标题权重 x3
            score += check_match(name_lower, 3)
            # 描述权重 x1
            score += check_match(desc_lower, 1)
        
        if score > highest_score:
            highest_score = score
            best_category = category
            
    return best_category if highest_score > 0 else 'uncategorized'


def get_all_categories():
    """
    获取所有可用分类
    
    返回:
    - list: 分类名称列表
    """
    return list(CATEGORY_KEYWORDS.keys()) + ['uncategorized']


def get_category_display_name(category):
    """
    获取分类的中文显示名称
    
    参数:
    - category: 分类英文名
    
    返回:
    - str: 中文显示名称
    """
    display_names = {
        'games': '游戏',
        'media': '媒体',
        'network': '网络',
        'development': '开发',
        'system': '系统',
        'productivity': '效率',
        'utility': '工具',
        'uncategorized': '未分类'
    }
    return display_names.get(category, category)
