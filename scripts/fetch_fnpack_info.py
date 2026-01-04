#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
从 FnDepot 仓库获取 fnpack.json 应用信息
支持解析 fnpack.json 规范格式的应用信息
"""

import json
import sys
import os
import re
import base64
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import fetch_github_api, auto_classify_app, validate_app_key, parse_github_url


def fetch_fnpack_info(repo_url, app_name_in_fnpack=None, github_token=None, existing_apps=None):
    """
    从GitHub仓库读取fnpack.json文件并提取应用信息
    严格按照fnpack.json规范解析数据
    
    参数:
    - repo_url: GitHub仓库URL
    - app_name_in_fnpack: fnpack.json中应用的键名，如果不提供则返回所有应用
    - github_token: GitHub API token，用于提高API调用限制
    - existing_apps: 已存在的应用列表（用于增量更新检查），列表中的元素为已存储的应用详情字典
    
    返回:
    - 如果指定了app_name_in_fnpack: 返回单个应用信息字典
    - 如果未指定app_name_in_fnpack: 返回所有应用信息的字典，键为app_key，值为应用信息
    """
    try:
        # 解析GitHub仓库信息
        match = re.search(r'github\.com\/([^\/]+)\/([^\/]+)', repo_url)
        if not match:
            raise ValueError('无效的GitHub仓库URL')
        
        owner = match.group(1)
        repo = match.group(2)
        
        # 验证仓库名称是否符合规范（必须为FnDepot，大小写敏感）
        if repo != 'FnDepot':
            print(f"警告: 仓库名称 '{repo}' 不符合规范，推荐使用 'FnDepot'")
        
        # 获取仓库基本信息
        repo_info = fetch_github_api(f'https://api.github.com/repos/{owner}/{repo}', github_token)
        if not repo_info:
            raise ValueError('无法获取仓库信息')

        # 增量更新检查：获取 fnpack.json 的最后提交时间
        fnpack_commits = fetch_github_api(
            f'https://api.github.com/repos/{owner}/{repo}/commits?path=fnpack.json&per_page=1',
            github_token
        )
        
        current_last_update = repo_info.get('updated_at')
        if fnpack_commits and isinstance(fnpack_commits, list) and len(fnpack_commits) > 0:
            current_last_update = fnpack_commits[0].get('commit', {}).get('committer', {}).get('date')

        # 检查是否可以跳过更新
        # 只要现有的应用中有一个记录的 lastUpdate 与 fnpack.json 的 commit 时间一致，就可以认为没变
        if existing_apps:
            # 找到任意一个来自此仓库的有效应用
            sample_app = None
            for app in existing_apps:
                # 简单验证一下 app 是否属于当前仓库 (通过 id 或 url)
                if app.get('repository', '').lower() == repo_url.lower():
                    sample_app = app
                    break
            
            if sample_app:
                cached_last_update = sample_app.get('lastUpdate')
                if cached_last_update == current_last_update:
                    print(f"Fnpack仓库 {repo} 无变更 (Last update: {current_last_update})，更新动态数据")
                    
                    # 构建返回结果，直接复用 existing_apps，但更新 Stars/Forks
                    result_apps = {}
                    
                    # 重新映射 existing_apps 为 {app_key: app_info} 格式
                    relevant_apps = [a for a in existing_apps if a.get('repository', '').lower() == repo_url.lower()]
                    
                    for app in relevant_apps:
                        app_key = app.get('fnpack_app_key')
                        if not app_key:
                             continue # 跳过没有 key 的旧数据
                        
                        # 更新动态数据
                        app['stars'] = repo_info.get('stargazers_count', 0)
                        app['forks'] = repo_info.get('forks_count', 0)
                        
                        # 如果指定了只获取特定应用
                        if app_name_in_fnpack and app_key != app_name_in_fnpack:
                            continue

                        result_apps[app_key] = app
                    
                    if app_name_in_fnpack:
                        return result_apps.get(app_name_in_fnpack)
                    return result_apps

        # 获取fnpack.json文件内容
        fnpack_content = ''
        fnpack_data = {}
        try:
            fnpack_res = fetch_github_api(f'https://api.github.com/repos/{owner}/{repo}/contents/fnpack.json', github_token)
            if fnpack_res and 'content' in fnpack_res:
                fnpack_content = base64.b64decode(fnpack_res['content']).decode('utf-8')
                fnpack_data = json.loads(fnpack_content)
                print(f"成功获取fnpack.json文件内容")
            else:
                print(f"仓库中未找到fnpack.json文件: {owner}/{repo}")
                return None
        except Exception as e:
            print(f"获取或解析fnpack.json失败: {str(e)}")
            return None
        
        # 传递 current_last_update 给 _process_single_app 以便使用统一的 commit 时间
        repo_info['fnpack_commit_date'] = current_last_update

        # 如果指定了应用键名，只返回单个应用
        if app_name_in_fnpack:
            if app_name_in_fnpack not in fnpack_data:
                print(f"应用键 '{app_name_in_fnpack}' 不存在于fnpack.json中")
                return None
            return _process_single_app(fnpack_data[app_name_in_fnpack], app_name_in_fnpack, owner, repo, repo_info, github_token)
        
        # 如果未指定应用键名，返回所有应用
        if not fnpack_data:
            print("fnpack.json中没有应用信息")
            return None
        
        all_apps = {}
        for app_key, app_config in fnpack_data.items():
            print(f"处理应用: {app_key}")
            app_info = _process_single_app(app_config, app_key, owner, repo, repo_info, github_token)
            if app_info:
                all_apps[app_key] = app_info
        
        print(f"成功解析fnpack.json，获取到 {len(all_apps)} 个应用信息")
        return all_apps
        
    except Exception as error:
        print(f"获取fnpack信息失败: {str(error)}")
        return None

def _process_single_app(app_config, app_key, owner, repo, repo_info, github_token=None):
    """
    处理单个应用配置，提取应用信息
    """
    try:
        # 验证应用唯一标识是否符合规范
        if not validate_app_key(app_key):
            print(f"警告: 应用键 '{app_key}' 不符合规范，仅允许使用小写字母(a-z)、数字(0-9)和连字符(-)")
        
        # 获取图标URL，支持多种大小写变体
        icon_url = ''
        icon_variants = ['ICON.PNG', 'ICON.png', 'icon.png', 'Icon.png', 'icon.PNG']
        try:
            for icon_name in icon_variants:
                icon_res = fetch_github_api(f'https://api.github.com/repos/{owner}/{repo}/contents/{app_key}/{icon_name}', github_token)
                if icon_res:
                    icon_url = f'https://raw.githubusercontent.com/{owner}/{repo}/main/{app_key}/{icon_name}'
                    print(f"找到图标: {icon_url}")
                    break
            if not icon_url:
                print(f"警告: 未找到图标文件 /{app_key}/ICON.PNG (尝试了多种大小写变体)")
        except Exception as e:
            print(f"获取图标失败: {str(e)}")
        
        # 按照规范获取安装包URL
        # 优先使用 fnpack.json 中配置的 download_url
        # 如果没有配置，则按照规范在 /{app_key}/目录下查找 {app_key}.fpk
        download_url = ''
        if app_config.get('download_url'):
            # 使用配置中指定的下载URL
            download_url = app_config.get('download_url')
            print(f"使用配置的下载URL: {download_url}")
        else:
            try:
                # 严格按照规范在/{app_key}/目录下查找{app_key}.fpk
                download_url = f'https://raw.githubusercontent.com/{owner}/{repo}/main/{app_key}/{app_key}.fpk'
                # 验证安装包是否存在
                fpk_res = fetch_github_api(f'https://api.github.com/repos/{owner}/{repo}/contents/{app_key}/{app_key}.fpk', github_token)
                if fpk_res:
                    print(f"找到安装包: {download_url}")
                else:
                    print(f"警告: 未找到规范的安装包文件 /{app_key}/{app_key}.fpk")
            except Exception as e:
                print(f"获取安装包失败: {str(e)}")
        
        # 尝试获取预览图
        screenshots = []
        try:
            # 检查Preview目录是否存在
            preview_res = fetch_github_api(f'https://api.github.com/repos/{owner}/{repo}/contents/{app_key}/Preview', github_token)
            if preview_res and isinstance(preview_res, list):
                # 筛选支持的图片格式
                image_extensions = ['.png', '.jpg', '.jpeg', '.webp']
                for item in preview_res:
                    if any(item.get('name', '').lower().endswith(ext) for ext in image_extensions):
                        img_url = f'https://raw.githubusercontent.com/{owner}/{repo}/main/{app_key}/Preview/{item.get("name")}'
                        screenshots.append(img_url)
                # 限制最多 9 张预览图
                screenshots = screenshots[:9]
                print(f"找到 {len(screenshots)} 张预览图")
        except Exception as e:
            print(f"获取预览图失败: {str(e)}")
        
        # 提取标签作为分类
        category = 'uncategorized'
        labels = app_config.get('labels', '')
        if labels:
            # 将标签按逗号分割，取第一个作为分类
            first_label = labels.split(',')[0].strip().lower()
            # 标签到系统分类的映射
            label_to_category = {
                '工具': 'utility',
                '终端': 'system',
                '开发': 'development',
                '游戏': 'games',
                '媒体': 'media',
                '网络': 'network',
                '办公': 'productivity',
                '系统': 'system',
                '教育': 'productivity',
                '社交': 'network',
                '娱乐': 'games'
            }
            category = label_to_category.get(first_label, 'utility')
        else:
            # 使用智能分类
            display_name = app_config.get('display_name', '')
            desc = app_config.get('desc', '')
            category = auto_classify_app(display_name, desc)
            print(f"为应用 {display_name} 自动分类为: {category}")
        
        # 构建应用信息字典，格式与fetch_app_info.py保持一致
        # 根据规范要求包含所有必填字段
        app_info = {
            'name': app_config.get('display_name', app_key),  # 使用display_name作为应用名称
            'description': app_config.get('desc', '') or '暂无描述',
            'version': app_config.get('version', '1.0.0'),
            'iconUrl': icon_url,
            'downloadUrl': download_url,
            'screenshots': screenshots,
            'author': app_config.get('author', '') or repo_info.get('owner', {}).get('login', ''),
            'author_url': app_config.get('author_url', ''),  # 规范要求的作者主页
            'bug_report_url': app_config.get('bug_report_url', ''),  # 规范要求的问题反馈链接
            'history': app_config.get('history', {}),  # 规范要求的版本更新记录
            'stars': repo_info.get('stargazers_count', 0),
            'forks': repo_info.get('forks_count', 0),
            'category': category,
            'lastUpdate': repo_info.get('fnpack_commit_date') or repo_info.get('updated_at', datetime.utcnow().isoformat() + 'Z'),
            # 额外存储规范要求的字段
            'app_key': app_key,
            'install_type': app_config.get('install_type', ''),
            'size': app_config.get('size', '')
        }
        
        print(f"成功解析应用信息: {app_info}")
        return app_info
        
    except Exception as error:
        print(f"处理应用 {app_key} 时出错: {str(error)}")
        return None

def update_apps_from_fnpack(app_id, app_name, repo_url, app_name_in_fnpack=None, github_token=None):
    """
    从fnpack.json更新应用信息到独立的fnpack_details.json文件
    严格按照fnpack.json规范处理数据，使用与app_details.json相同的格式供网页端读取
    
    根据规范：
    - 应用唯一标识(app_key)必须与应用文件夹名称完全一致
    - 使用display_name作为应用显示名称
    - 图标路径：/{app_name}/ICON.PNG
    - 安装包路径：/{app_name}/{app_name}.fpk
    """
    # 从URL提取仓库key（用户名或组织名）
    import re
    match = re.search(r'github\.com/([^/]+)/', repo_url)
    repo_key = match.group(1) if match else repo_url.replace('https://github.com/', '').split('/')[0]
    
    try:
        # 使用FnpackDetailsStore管理数据存储
        from utils.data_store import FnpackDetailsStore
        store = FnpackDetailsStore()
        
        # 获取当前存储的数据
        fnpack_details_data = store.load()
        apps_list = fnpack_details_data.get('apps', [])
        
        # 获取应用详细信息（从fnpack.json）
        print(f"开始获取仓库 {repo_url} 的fnpack详细信息...")
        app_info = fetch_fnpack_info(repo_url, app_name_in_fnpack, github_token)
        
        # 处理获取到的应用信息
        updated_count = 0
        
        if isinstance(app_info, dict):
            # 检查是否是单个应用还是多个应用
            if 'name' in app_info and 'description' in app_info:
                # 单个应用情况
                display_name = app_info.get('name', app_name)
                app_key = app_info.get('app_key', app_name_in_fnpack)
                
                # 构建应用唯一ID: repo_key + '_' + app_key
                final_app_id = f"{repo_key}_{app_key}"
                
                new_app_detail = {
                    'id': final_app_id,
                    'name': display_name,
                    'repository': repo_url,
                    'description': app_info.get('description', ''),
                    'version': app_info.get('version', '1.0.0'),
                    'iconUrl': app_info.get('iconUrl', ''),
                    'downloadUrl': app_info.get('downloadUrl', ''),
                    'screenshots': app_info.get('screenshots', []),
                    'author': app_info.get('author', ''),
                    'author_url': app_info.get('author_url', ''),  # 规范要求的作者主页
                    'bug_report_url': app_info.get('bug_report_url', ''),  # 规范要求的问题反馈链接
                    'history': app_info.get('history', {}),  # 规范要求的版本更新记录
                    'stars': app_info.get('stars', 0),
                    'forks': app_info.get('forks', 0),
                    'category': app_info.get('category', 'uncategorized'),
                    'lastUpdate': app_info.get('lastUpdate', datetime.utcnow().isoformat() + 'Z'),
                    'fnpack_app_key': app_key,
                    'fnpack_repo_key': repo_key,  # 使用仓库key作为标识
                    'install_type': app_info.get('install_type', ''),
                    'size': app_info.get('size', '')
                }
                
                store.upsert_app(new_app_detail)
                print(f"更新fnpack应用详细信息: {final_app_id} ({display_name})")
                updated_count = 1
            else:
                # 多个应用情况（从仓库获取所有应用）
                print(f"开始处理仓库中的 {len(app_info)} 个应用...")
                for app_key, single_app_info in app_info.items():
                    display_name = single_app_info.get('name', app_key)
                    
                    # 构建应用唯一ID: repo_key + '_' + app_key
                    final_app_id = f"{repo_key}_{app_key}"
                    
                    new_app_detail = {
                        'id': final_app_id,
                        'name': display_name,
                        'repository': repo_url,
                        'description': single_app_info.get('description', ''),
                        'version': single_app_info.get('version', '1.0.0'),
                        'iconUrl': single_app_info.get('iconUrl', ''),
                        'downloadUrl': single_app_info.get('downloadUrl', ''),
                        'screenshots': single_app_info.get('screenshots', []),
                        'author': single_app_info.get('author', ''),
                        'author_url': single_app_info.get('author_url', ''),  # 规范要求的作者主页
                        'bug_report_url': single_app_info.get('bug_report_url', ''),  # 规范要求的问题反馈链接
                        'history': single_app_info.get('history', {}),  # 规范要求的版本更新记录
                        'stars': single_app_info.get('stars', 0),
                        'forks': single_app_info.get('forks', 0),
                        'category': single_app_info.get('category', 'uncategorized'),
                        'lastUpdate': single_app_info.get('lastUpdate', datetime.utcnow().isoformat() + 'Z'),
                        'fnpack_app_key': app_key,
                        'fnpack_repo_key': repo_key,  # 使用仓库key作为标识
                        'install_type': single_app_info.get('install_type', ''),
                        'size': single_app_info.get('size', '')
                    }
                    
                    store.upsert_app(new_app_detail)
                    print(f"更新fnpack应用详细信息: {final_app_id} ({display_name})")
                    updated_count += 1
        
        if updated_count > 0:
            print(f'fnpack应用详细元数据更新成功，共处理 {updated_count} 个应用')
            return True
        else:
            print(f"无法获取应用信息或没有需要更新的应用")
            return False
    
    except Exception as error:
        print(f"更新fnpack应用详细元数据失败: {str(error)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print('用法: python fetch_fnpack_info.py <appId> <appName> <repoUrl> [appNameInFnpack]')
        print('appNameInFnpack为可选参数，指定fnpack.json中的应用键名')
        sys.exit(1)
    
    app_id = sys.argv[1]
    app_name = sys.argv[2]
    repo_url = sys.argv[3]
    app_name_in_fnpack = sys.argv[4] if len(sys.argv) > 4 else None
    github_token = sys.argv[5] if len(sys.argv) > 5 else None
    
    update_apps_from_fnpack(app_id, app_name, repo_url, app_name_in_fnpack, github_token)