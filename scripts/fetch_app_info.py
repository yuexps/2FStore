#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
import urllib.request
import re
from datetime import datetime
import base64
import os

def auto_classify_app(name, description):
    """
    智能分类函数 - 根据应用名称和描述自动确定分类
    """
    # 组合名称和描述用于分析
    text = (name + ' ' + description).lower()
    
    # 定义分类关键词映射
    category_keywords = {
        'games': ['游戏', 'game', 'gaming', '休闲', 'entertainment', '娱乐', 'play', 'player', 'arcade', 'puzzle'],
        'media': ['视频', '音乐', 'video', 'music', 'player', '播放', 'audio', 'image', '图片', 'photo', 'gallery'],
        'network': ['网络', 'net', 'browser', '浏览器', 'vpn', '代理', 'proxy', '连接', 'connect', 'wifi', 'v2ray', 'clash'],
        'development': ['开发', 'dev', 'code', '编程', 'program', 'ide', 'editor', '开发工具', 'developer'],
        'system': ['系统', 'system', '设置', 'setting', '优化', 'optimize', '管理', 'manager', '监控', 'monitor', 'terminal', '终端'],
        'productivity': ['办公', 'office', '文档', 'document', '效率', 'productivity', '笔记', 'note', 'todo', 'task', 'calendar', '日历'],
        'utility': ['工具', 'utility', '计算器', 'calculator', '转换', 'convert', '下载', 'download', '搜索', 'search', '助手', 'helper']
    }
    
    # 计算每个分类的匹配分数
    best_category = 'uncategorized'
    highest_score = 0
    
    for category, keywords in category_keywords.items():
        score = 0
        for keyword in keywords:
            if keyword in text:
                score += 1
        
        if score > highest_score:
            highest_score = score
            best_category = category
    
    # 只有当找到至少一个匹配时才分类，否则保持未分类
    return best_category if highest_score > 0 else 'uncategorized'


def fetch_github_api(url):
    """
    从GitHub API获取数据
    """
    req = urllib.request.Request(url)
    req.add_header('User-Agent', '2FStore-App/1.0')
    try:
        response = urllib.request.urlopen(req)
        data = response.read()
        return json.loads(data)
    except Exception as e:
        print(f"Error fetching {url}: {str(e)}")
        return None


def fetch_app_info(repo_url):
    """
    从GitHub获取应用信息
    """
    try:
        match = re.search(r'github\.com\/([^\/]+)\/([^\/]+)', repo_url)
        if not match:
            raise ValueError('无效的GitHub仓库URL')
        
        owner = match.group(1)
        repo = match.group(2)
        
        # 获取仓库信息
        repo_info = fetch_github_api(f'https://api.github.com/repos/{owner}/{repo}')
        if not repo_info:
            raise ValueError('无法获取仓库信息')
        
        # 优先尝试获取 manifest 文件
        manifest_content = ''
        manifest_data = {}
        try:
            manifest_res = fetch_github_api(f'https://api.github.com/repos/{owner}/{repo}/contents/manifest')
            if manifest_res and 'content' in manifest_res:
                manifest_content = base64.b64decode(manifest_res['content']).decode('utf-8')
                # 解析 key = value 格式
                for line in manifest_content.split('\n'):
                    m = re.match(r'^([a-zA-Z0-9_]+)\s*=\s*(.*)$', line)
                    if m:
                        manifest_data[m.group(1)] = m.group(2)
        except Exception as e:
            print(f"获取manifest文件失败: {str(e)}")
        
        # 获取README内容
        readme_content = ''
        try:
            readme_res = fetch_github_api(f'https://api.github.com/repos/{owner}/{repo}/readme')
            if readme_res and 'content' in readme_res:
                readme_content = base64.b64decode(readme_res['content']).decode('utf-8')
        except Exception as e:
            print(f"获取README失败: {str(e)}")
        
        # 获取 Release 信息
        releases = []
        try:
            releases = fetch_github_api(f'https://api.github.com/repos/{owner}/{repo}/releases')
            if not releases:
                releases = []
        except Exception as e:
            print(f"获取Release信息失败: {str(e)}")
            releases = []
        
        # 获取 ICON 文件（优先 ICON_256.PNG, 其次 ICON.PNG）
        icon_url = ''
        try:
            icon256_res = fetch_github_api(f'https://api.github.com/repos/{owner}/{repo}/contents/ICON_256.PNG')
            if icon256_res:
                icon_url = f'https://raw.githubusercontent.com/{owner}/{repo}/main/ICON_256.PNG'
            else:
                icon_res = fetch_github_api(f'https://api.github.com/repos/{owner}/{repo}/contents/ICON.PNG')
                if icon_res:
                    icon_url = f'https://raw.githubusercontent.com/{owner}/{repo}/main/ICON.PNG'
        except Exception as e:
            print(f"获取图标失败: {str(e)}")
        
        # 创建应用基本信息，优先 manifest，其次 repo/README
        app_info = {
            'description': manifest_data.get('desc') or repo_info.get('description', '') or '暂无描述',
            'version': manifest_data.get('version') or (releases[0].get('tag_name') if releases else None) or '1.0.0',
            'iconUrl': icon_url,
            'downloadUrl': '',
            'screenshots': [],
            'author': repo_info.get('owner', {}).get('login', '') if repo_info.get('owner') else '',
            'stars': repo_info.get('stargazers_count', 0),
            'forks': repo_info.get('forks_count', 0),
            'category': manifest_data.get('category', 'uncategorized'),
            'lastUpdate': repo_info.get('updated_at', datetime.utcnow().isoformat() + 'Z')
        }
        
        # 补充 README 解析（如 manifest 缺失字段）
        if not app_info['version'] or app_info['version'] == '1.0.0':
            version_match = re.search(r'version:\s*([\d.]+)', readme_content, re.IGNORECASE)
            if version_match:
                app_info['version'] = version_match.group(1)
        
        if not app_info['iconUrl']:
            icon_match = re.search(r'icon:\s*(https?:\/\/[^\s]+)', readme_content, re.IGNORECASE)
            if icon_match:
                app_info['iconUrl'] = icon_match.group(1)
        
        # 提取分类信息
        if not app_info['category'] or app_info['category'] == 'uncategorized':
            category_match = re.search(r'category:\s*([\w]+)', readme_content, re.IGNORECASE)
            if category_match:
                app_info['category'] = category_match.group(1)
            else:
                # 实现智能自动分类
                repo_name_for_classification = repo
                app_info['category'] = auto_classify_app(repo_name_for_classification, app_info['description'])
                print(f"为应用 {repo_name_for_classification} 自动分类为: {app_info['category']}")
        
        # 尝试提取 README 中的截图（markdown 图片链接）
        screenshot_matches = re.findall(r'!\[[^\]]*\]\((https?:\/\/[^)]+)\)', readme_content)
        if screenshot_matches:
            app_info['screenshots'] = screenshot_matches
        
        # 遍历 Release 资产，收集所有下载链接
        if isinstance(releases, list) and len(releases) > 0:
            latest_release = releases[0]
            if 'assets' in latest_release and isinstance(latest_release['assets'], list) and len(latest_release['assets']) > 0:
                # 只保留 .fpk 资产
                fpk_assets = [asset for asset in latest_release['assets'] if asset.get('name', '').endswith('.fpk')]
                if fpk_assets:
                    app_info['downloadUrl'] = fpk_assets[0].get('browser_download_url', '')
                else:
                    app_info['downloadUrl'] = ''
                print(f"从GitHub Release获取到 {len(fpk_assets)} 个 .fpk 下载资产")
            else:
                print(f"GitHub Release中未找到资产文件: {owner}/{repo}")
        
        return app_info
    except Exception as error:
        print(f"获取应用信息失败: {str(error)}")
        raise error


# 修改update_apps函数，增加参数和删除逻辑
def update_apps(app_id=None, app_name=None, repo_url=None, active_app_ids=None):
    """
    更新应用列表或清理已删除的应用
    
    参数:
    - app_id, app_name, repo_url: 单个应用的信息（用于更新单个应用）
    - active_app_ids: 当前活跃的应用ID集合（用于清理已删除的应用）
    """
    # 详细元数据文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_details_file_path = os.path.join(script_dir, '..', 'data', 'app_details.json')
    
    try:
        # 读取现有详细元数据
        app_details_data = {'apps': [], 'lastUpdated': ''}
        try:
            with open(app_details_file_path, 'r', encoding='utf-8') as f:
                app_details_data = json.load(f)
        except FileNotFoundError:
            # 如果文件不存在，创建新的数据结构
            app_details_data = {'apps': [], 'lastUpdated': datetime.utcnow().isoformat() + 'Z'}
        except Exception as err:
            print(f"读取app_details.json出错: {str(err)}")
            app_details_data = {'apps': [], 'lastUpdated': datetime.utcnow().isoformat() + 'Z'}
        
        # 确保app_details_data是有效的数据结构
        if not isinstance(app_details_data, dict):
            app_details_data = {'apps': [], 'lastUpdated': datetime.utcnow().isoformat() + 'Z'}
        
        if 'apps' not in app_details_data or not isinstance(app_details_data['apps'], list):
            app_details_data['apps'] = []
        
        # 清理已删除的应用（如果提供了active_app_ids）
        if active_app_ids is not None:
            initial_count = len(app_details_data['apps'])
            app_details_data['apps'] = [app for app in app_details_data['apps'] 
                                      if app.get('id') in active_app_ids]
            removed_count = initial_count - len(app_details_data['apps'])
            if removed_count > 0:
                print(f"清理了 {removed_count} 个已删除应用的详细信息")
        
        # 如果提供了单个应用信息，则更新该应用
        if app_id and app_name and repo_url:
            # 获取应用详细信息
            print(f"开始获取应用 {app_id} 的详细信息...")
            app_info = fetch_app_info(repo_url)
            
            # 合并用户提供的信息和从GitHub获取的信息
            new_app_detail = {
                'id': app_id,
                'name': app_name,
                'repository': repo_url,
                **app_info
            }
            
            # 检查应用是否已存在
            existing_app_index = -1
            for i, app in enumerate(app_details_data['apps']):
                if app.get('id') == app_id:
                    existing_app_index = i
                    break
            
            if existing_app_index >= 0:
                # 更新现有应用
                app_details_data['apps'][existing_app_index] = new_app_detail
                print(f"更新应用详细信息: {app_id}")
            else:
                # 添加新应用
                app_details_data['apps'].append(new_app_detail)
                print(f"添加新应用详细信息: {app_id}")
        
        # 更新最后更新时间
        app_details_data['lastUpdated'] = datetime.utcnow().isoformat() + 'Z'
        
        # 确保目录存在
        os.makedirs(os.path.dirname(app_details_file_path), exist_ok=True)
        
        # 保存更新后的详细元数据
        with open(app_details_file_path, 'w', encoding='utf-8') as f:
            json.dump(app_details_data, f, ensure_ascii=False, indent=2)
        print('应用详细元数据更新成功')
        
    except Exception as error:
        print(f"更新应用详细元数据失败: {str(error)}")
        raise error


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print('用法: python fetch_app_info.py <appId> <appName> <repoUrl>')
        sys.exit(1)
    
    app_id, app_name, repo_url = sys.argv[1], sys.argv[2], sys.argv[3]
    update_apps(app_id, app_name, repo_url)