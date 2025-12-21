#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
从 GitHub 仓库获取应用信息
"""

import sys
import os
import re
import base64
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import (
    fetch_github_api,
    auto_classify_app,
    parse_github_url
)
from utils.data_store import AppDetailsStore


def parse_manifest(content):
    """
    解析 manifest 文件内容（key=value 格式）
    支持多行字符串（使用三引号 \"\"\" 包裹）
    
    参数:
    - content: manifest 文件内容
    
    返回:
    - dict: 解析后的键值对
    """
    manifest_data = {}
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # 跳过空行和注释
        if not line or line.startswith('#'):
            i += 1
            continue
        
        # 匹配 key = value 格式
        match = re.match(r'^([a-zA-Z0-9_]+)\s*=\s*(.*)$', line)
        if match:
            key = match.group(1)
            value = match.group(2).strip()
            
            # 检查是否是多行字符串开始（三引号）
            if value.startswith('"""'):
                # 移除开头的三引号
                value = value[3:]
                
                # 检查是否在同一行结束
                if value.endswith('"""'):
                    value = value[:-3]
                else:
                    # 收集多行内容直到找到结束的三引号
                    multiline_parts = [value] if value else []
                    i += 1
                    while i < len(lines):
                        next_line = lines[i]
                        if '"""' in next_line:
                            # 找到结束的三引号
                            end_part = next_line.split('"""')[0]
                            if end_part.strip():
                                multiline_parts.append(end_part)
                            break
                        else:
                            multiline_parts.append(next_line)
                        i += 1
                    value = '\n'.join(multiline_parts).strip()
            
            manifest_data[key] = value
        
        i += 1
    
    return manifest_data



def fetch_app_info(repo_url, github_token=None, existing_app=None):
    """
    从 GitHub 获取应用信息 (支持增量更新)
    
    参数:
    - repo_url: GitHub 仓库 URL
    - github_token: GitHub API token
    - existing_app: 已存在的应用信息（用于对比更新时间）
    
    返回:
    - dict: 应用信息字典 (如果无需更新且提供了 existing_app，可能返回 existing_app)
    """
    owner, repo = parse_github_url(repo_url)
    if not owner or not repo:
        raise ValueError('无效的 GitHub 仓库 URL')
    
    # 1. 获取仓库基础信息 (轻量请求)
    repo_info = fetch_github_api(f'https://api.github.com/repos/{owner}/{repo}', github_token)
    if not repo_info:
        raise ValueError('无法获取仓库信息')
    
    # 2. 获取 manifest 文件的提交信息和 Releases 信息 (用于判断是否需要更新)
    manifest_commits = fetch_github_api(
        f'https://api.github.com/repos/{owner}/{repo}/commits?path=manifest&per_page=1',
        github_token
    )
    releases = fetch_github_api(
        f'https://api.github.com/repos/{owner}/{repo}/releases',
        github_token
    ) or []

    manifest_update = None
    if manifest_commits and isinstance(manifest_commits, list) and len(manifest_commits) > 0:
        manifest_update = manifest_commits[0].get('commit', {}).get('committer', {}).get('date')

    release_update = None
    if releases:
        release_update = releases[0].get('published_at') or releases[0].get('created_at')

    # 取 manifest 和 release 的最大时间
    update_times = [t for t in [manifest_update, release_update] if t]
    if update_times:
        current_last_update = max(update_times)
    else:
        current_last_update = repo_info.get('updated_at')

    # 3. 增量更新检查
    if existing_app:
        cached_last_update = existing_app.get('lastUpdate')
        
        # 如果时间戳一致，且数据完整
        if cached_last_update == current_last_update:
             if existing_app.get('version') and existing_app.get('description'):
                print(f"应用 {repo} Manifest 无变更 (Last update: {current_last_update})，更新动态数据")
                # 仅更新 Star 和 Fork
                existing_app['stars'] = repo_info.get('stargazers_count', 0)
                existing_app['forks'] = repo_info.get('forks_count', 0)
                # 依然返回现有对象
                return existing_app

    # 4. 详细抓取 (Manifest, README, Icon, Releases) - 只有检测到变更才执行
    # 获取 manifest 文件
    manifest_data = {}
    try:
        manifest_res = fetch_github_api(
            f'https://api.github.com/repos/{owner}/{repo}/contents/manifest',
            github_token
        )
        if manifest_res and 'content' in manifest_res:
            manifest_content = base64.b64decode(manifest_res['content']).decode('utf-8')
            manifest_data = parse_manifest(manifest_content)
    except Exception as e:
        print(f"获取 manifest 文件失败: {str(e)}")
    
    # 获取 README 内容
    readme_content = ''
    try:
        readme_res = fetch_github_api(
            f'https://api.github.com/repos/{owner}/{repo}/readme',
            github_token
        )
        if readme_res and 'content' in readme_res:
            readme_content = base64.b64decode(readme_res['content']).decode('utf-8')
    except Exception as e:
        print(f"获取 README 失败: {str(e)}")
    icon_url = ''
    icon_variants = [
        'ICON_256.PNG', 'ICON_256.png', 'icon_256.png',
        'ICON.PNG', 'ICON.png', 'icon.png', 'Icon.png'
    ]
    default_branch = repo_info.get('default_branch', 'main')
    for icon_name in icon_variants:
        icon_res = fetch_github_api(
            f'https://api.github.com/repos/{owner}/{repo}/contents/{icon_name}',
            github_token,
            max_retries=1,
            silent=True
        )
        if icon_res:
            icon_url = f'https://raw.githubusercontent.com/{owner}/{repo}/{default_branch}/{icon_name}'
            print(f"找到图标: {icon_url}")
            break
            
    # 获取 Release 信息
    releases = fetch_github_api(
        f'https://api.github.com/repos/{owner}/{repo}/releases',
        github_token
    ) or []
    
    app_info = {
        'description': manifest_data.get('desc') or repo_info.get('description', '') or '暂无描述',
        'version': manifest_data.get('version') or (releases[0].get('tag_name') if releases else None) or '1.0.0',
        'iconUrl': icon_url,
        'downloadUrl': '',
        'screenshots': [],
        'author': repo_info.get('owner', {}).get('login', ''),
        'stars': repo_info.get('stargazers_count', 0),
        'forks': repo_info.get('forks_count', 0),
        'category': manifest_data.get('category', 'uncategorized'),
        'lastUpdate': current_last_update
    }
    
    # 从 README 补充版本号
    if app_info['version'] == '1.0.0' and readme_content:
        version_match = re.search(r'version[:\s]+v?([\d.]+)', readme_content, re.IGNORECASE)
        if version_match:
            app_info['version'] = version_match.group(1)
    
    # 智能分类
    if app_info['category'] == 'uncategorized':
        category_match = re.search(r'category[:\s]+([\w]+)', readme_content, re.IGNORECASE)
        if category_match:
            app_info['category'] = category_match.group(1)
        else:
            app_info['category'] = auto_classify_app(repo, app_info['description'])
            print(f"为应用 {repo} 自动分类为: {app_info['category']}")
    
    # 提取 README 中的截图
    screenshot_matches = re.findall(r'!\[[^\]]*\]\((https?://[^)]+)\)', readme_content)
    if screenshot_matches:
        app_info['screenshots'] = screenshot_matches
    
    # 获取下载链接（.fpk 文件）
    if releases:
        latest_release = releases[0]
        assets = latest_release.get('assets', [])
        fpk_assets = [a for a in assets if a.get('name', '').endswith('.fpk')]
        if fpk_assets:
            app_info['downloadUrl'] = fpk_assets[0].get('browser_download_url', '')
            print(f"从 GitHub Release 获取到 {len(fpk_assets)} 个 .fpk 下载资产")
        else:
            print(f"GitHub Release 中未找到 .fpk 文件: {owner}/{repo}")
    
    return app_info


def fetch_and_process_app(app_data, store, github_token):
    """
    处理单个应用的获取和更新（供并发调用）
    
    返回:
    - dict: 更新后的应用详情，失败返回 None
    """
    app_id = app_data.get('id')
    app_name = app_data.get('name')
    repo_url = app_data.get('repository')
    
    if not app_id or not repo_url:
        return None
        
    try:
        existing_app = store.find_app(app_id)
        
        # 传入 existing_app 触发增量检查
        app_info = fetch_app_info(repo_url, github_token, existing_app)
        
        app_detail = {
            'id': app_id,
            'name': app_name,
            'repository': repo_url,
            **app_info
        }
        return app_detail
    except Exception as e:
        print(f"处理应用 {app_name} ({app_id}) 失败: {str(e)}")
        return None


def update_apps(app_id=None, app_name=None, repo_url=None, active_app_ids=None, github_token=None):
    """
    更新应用列表 (保留用于单应用更新的入口)
    """
    if not github_token:
        github_token = os.environ.get('GITHUB_TOKEN') or os.environ.get('PERSONAL_TOKEN')
    
    store = AppDetailsStore()
    
    if active_app_ids is not None:
        store.sync_with_apps_list(active_app_ids)
    
    if app_id and app_name and repo_url:
        print(f"开始获取应用 {app_id} 的详细信息...")
        try:
            # 单应用更新也复用 fetch_app_info
            existing_app = store.find_app(app_id)
            app_info = fetch_app_info(repo_url, github_token, existing_app)
            
            app_detail = {
                'id': app_id,
                'name': app_name,
                'repository': repo_url,
                **app_info
            }
            store.upsert_app(app_detail)
            print(f"应用详细信息更新成功: {app_id}")
        except Exception as e:
            print(f"获取应用信息失败: {str(e)}")
            raise


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print('用法: python fetch_app_info.py <appId> <appName> <repoUrl>')
        sys.exit(1)
    
    app_id, app_name, repo_url = sys.argv[1], sys.argv[2], sys.argv[3]
    update_apps(app_id, app_name, repo_url)