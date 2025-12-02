#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PR 验证脚本
验证提交的应用信息（apps.json 和 fnpacks.json）
"""

import os
import sys
import json
import base64
import re

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import validate_app_info, GitHubAPI, validate_app_key
from fetch_app_info import fetch_app_info
from fetch_fnpack_info import fetch_fnpack_info


def check_app_id_exists(app_id, api):
    """
    检查应用ID是否已存在于主分支
    """
    repo_owner = os.environ.get('REPO_OWNER', 'yuexps')
    repo_name = os.environ.get('REPO_NAME', '2FStore')
    
    try:
        print(f"正在检查应用ID {app_id} 是否存在于主分支...")
        content = api.get_file_content(repo_owner, repo_name, 'apps.json')
        if content:
            apps_data = json.loads(content)
            exists = any(app.get('id') == app_id for app in apps_data.get('apps', []))
            print(f"应用ID {app_id} 检查结果: {'已存在' if exists else '不存在'}")
            return exists
    except Exception as e:
        print(f"检查应用ID存在性时出错: {str(e)}")
    return False


def check_fnpack_key_exists(key, api):
    """
    检查 fnpack key 是否已存在于主分支
    """
    repo_owner = os.environ.get('REPO_OWNER', 'yuexps')
    repo_name = os.environ.get('REPO_NAME', '2FStore')
    
    try:
        print(f"正在检查 fnpack key {key} 是否存在于主分支...")
        content = api.get_file_content(repo_owner, repo_name, 'fnpacks.json')
        if content:
            fnpacks_data = json.loads(content)
            exists = any(fnpack.get('key') == key for fnpack in fnpacks_data.get('fnpacks', []))
            print(f"fnpack key {key} 检查结果: {'已存在' if exists else '不存在'}")
            return exists
    except Exception as e:
        print(f"检查 fnpack key 存在性时出错: {str(e)}")
    return False


def get_apps_json_from_pr(pr_number, api, repo_owner, repo_name):
    """
    从 PR 获取 apps.json 的内容
    """
    print(f"开始从PR #{pr_number} 获取apps.json内容...")
    
    # 获取 PR 信息
    pr_result = api.get_pull_request(repo_owner, repo_name, pr_number)
    if not pr_result['success']:
        raise Exception(f"获取PR信息失败: {pr_result.get('error')}")
    
    pr_data = pr_result['data']
    head_sha = pr_data.get('head', {}).get('sha')
    head_ref = pr_data.get('head', {}).get('ref')
    
    if not head_sha:
        raise Exception('无法获取PR的head分支SHA')
    
    print(f"PR head SHA: {head_sha}, 分支: {head_ref}")
    
    # 从 head 分支获取 apps.json
    content = api.get_file_content(repo_owner, repo_name, 'apps.json', ref=head_sha)
    if content:
        print("成功从head分支获取并解码apps.json内容")
        return json.loads(content)
    
    raise Exception('PR分支中的apps.json文件内容为空')


def get_base_apps_json(base_sha, api, repo_owner, repo_name):
    """
    从 PR 的基础分支获取 apps.json 内容
    """
    try:
        content = api.get_file_content(repo_owner, repo_name, 'apps.json', ref=base_sha)
        if content:
            return json.loads(content)
    except Exception as e:
        print(f"获取基础分支apps.json失败: {str(e)}")
    return {'apps': []}


def get_fnpacks_json_from_pr(pr_number, api, repo_owner, repo_name):
    """
    从 PR 获取 fnpacks.json 的内容
    """
    print(f"开始从PR #{pr_number} 获取fnpacks.json内容...")
    
    # 获取 PR 信息
    pr_result = api.get_pull_request(repo_owner, repo_name, pr_number)
    if not pr_result['success']:
        raise Exception(f"获取PR信息失败: {pr_result.get('error')}")
    
    pr_data = pr_result['data']
    head_sha = pr_data.get('head', {}).get('sha')
    
    if not head_sha:
        raise Exception('无法获取PR的head分支SHA')
    
    # 从 head 分支获取 fnpacks.json
    content = api.get_file_content(repo_owner, repo_name, 'fnpacks.json', ref=head_sha)
    if content:
        print("成功从head分支获取并解码fnpacks.json内容")
        return json.loads(content)
    
    return None


def get_base_fnpacks_json(base_sha, api, repo_owner, repo_name):
    """
    从 PR 的基础分支获取 fnpacks.json 内容
    """
    try:
        content = api.get_file_content(repo_owner, repo_name, 'fnpacks.json', ref=base_sha)
        if content:
            return json.loads(content)
    except Exception as e:
        print(f"获取基础分支fnpacks.json失败: {str(e)}")
    return {'fnpacks': []}


def find_modified_fnpacks(pr_fnpacks_data, base_fnpacks_data):
    """
    找出PR中新增、修改或删除的 fnpack
    返回(modified_fnpacks, deleted_fnpacks)
    """
    pr_fnpacks = pr_fnpacks_data.get('fnpacks', [])
    base_fnpacks = base_fnpacks_data.get('fnpacks', [])
    
    pr_fnpack_keys = {fnpack.get('key'): fnpack for fnpack in pr_fnpacks}
    base_fnpack_keys = {fnpack.get('key'): fnpack for fnpack in base_fnpacks}
    
    modified_fnpacks = []
    deleted_fnpacks = []
    
    # 检查新增或修改的 fnpack
    for pr_fnpack in pr_fnpacks:
        pr_key = pr_fnpack.get('key')
        base_fnpack = base_fnpack_keys.get(pr_key)
        
        if not base_fnpack:
            # 新增 fnpack
            modified_fnpacks.append(pr_fnpack)
        elif base_fnpack.get('repo') != pr_fnpack.get('repo'):
            # 修改的 fnpack
            modified_fnpacks.append(pr_fnpack)
    
    # 检查删除的 fnpack
    for base_fnpack in base_fnpacks:
        base_key = base_fnpack.get('key')
        if base_key not in pr_fnpack_keys:
            # 删除的 fnpack
            deleted_fnpacks.append(base_fnpack)
    
    return modified_fnpacks, deleted_fnpacks


# 修改find_modified_apps函数
def find_modified_apps(pr_apps_data, base_apps_data):
    """
    找出PR中新增、修改或删除的应用
    返回(modified_apps, deleted_apps)
    """
    pr_apps = pr_apps_data.get('apps', [])
    base_apps = base_apps_data.get('apps', [])
    
    pr_app_ids = {app.get('id'): app for app in pr_apps}
    base_app_ids = {app.get('id'): app for app in base_apps}
    
    modified_apps = []
    deleted_apps = []
    
    # 检查新增或修改的应用
    for pr_app in pr_apps:
        pr_app_id = pr_app.get('id')
        base_app = base_app_ids.get(pr_app_id)
        
        if not base_app:
            # 新增应用
            modified_apps.append(pr_app)
        elif (base_app.get('name') != pr_app.get('name') or 
              base_app.get('repository') != pr_app.get('repository')):
            # 修改的应用
            modified_apps.append(pr_app)
    
    # 检查删除的应用
    for base_app in base_apps:
        base_app_id = base_app.get('id')
        if base_app_id not in pr_app_ids:
            # 删除的应用
            deleted_apps.append(base_app)
    
    return modified_apps, deleted_apps

def run():
    """
    GitHub Action入口函数
    """
    try:
        # 获取GitHub上下文
        github_token = os.environ.get('GITHUB_TOKEN')
        pull_request_number = os.environ.get('PR_NUMBER')
        repo_owner = os.environ.get('REPO_OWNER')
        repo_name = os.environ.get('REPO_NAME')
        
        if not github_token or not pull_request_number or not repo_owner or not repo_name:
            print('缺少必要的环境变量')
            sys.exit(1)
        
        # 创建 API 实例
        api = GitHubAPI(github_token)
        
        # 获取PR信息
        pr_result = api.get_pull_request(repo_owner, repo_name, pull_request_number)
        if not pr_result['success']:
            print(f"获取PR信息失败: {pr_result.get('error')}")
            sys.exit(1)
        pr = pr_result['data']
        
        # 获取 PR 修改的文件列表
        files_result = api.get(f'https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pull_request_number}/files')
        if not files_result['success']:
            print(f"获取PR文件列表失败: {files_result.get('error')}")
            sys.exit(1)
        
        changed_files = [f.get('filename') for f in files_result.get('data', [])]
        print(f"PR 修改的文件: {changed_files}")
        
        apps_changed = 'apps.json' in changed_files
        fnpacks_changed = 'fnpacks.json' in changed_files
        
        # 验证 fnpacks.json 的修改
        if fnpacks_changed:
            validate_fnpacks_pr(pr, api, repo_owner, repo_name, pull_request_number)
        
        # 验证 apps.json 的修改
        if apps_changed:
            validate_apps_pr(pr, api, repo_owner, repo_name, pull_request_number)
        
        if not apps_changed and not fnpacks_changed:
            print('PR 中没有检测到 apps.json 或 fnpacks.json 的修改')
            sys.exit(1)
        
    except Exception as error:
        print(f'验证PR失败: {str(error)}')
        sys.exit(1)


def validate_fnpacks_pr(pr, api, repo_owner, repo_name, pull_request_number):
    """
    验证 fnpacks.json 的 PR 修改
    """
    print('\n========== 验证 fnpacks.json ==========')
    
    # 从 PR 中获取 fnpacks.json 内容
    pr_fnpacks_data = get_fnpacks_json_from_pr(pull_request_number, api, repo_owner, repo_name)
    if not pr_fnpacks_data:
        print('无法从 PR 获取 fnpacks.json')
        return
    
    # 从基础分支获取 fnpacks.json 内容
    base_fnpacks_data = get_base_fnpacks_json(pr['base']['sha'], api, repo_owner, repo_name)
    
    # 找出修改的 fnpack
    modified_fnpacks, deleted_fnpacks = find_modified_fnpacks(pr_fnpacks_data, base_fnpacks_data)
    
    if len(modified_fnpacks) == 0 and len(deleted_fnpacks) == 0:
        print('fnpacks.json 中没有检测到新增、修改或删除的仓库')
        return
    
    # 处理删除的 fnpack
    if len(deleted_fnpacks) > 0:
        for fnpack in deleted_fnpacks:
            key = fnpack.get('key')
            repo = fnpack.get('repo')
            print(f'检测到 fnpack 删除: {key} ({repo})')
            print('⚠️ 注意: 此操作将从 fnpack 列表中永久移除该仓库')
    
    # 处理新增或修改的 fnpack
    for fnpack in modified_fnpacks:
        key = fnpack.get('key')
        repo_url = fnpack.get('repo')
        
        print(f'\n--- 验证 fnpack: {key} ---')
        
        # 验证 key 格式
        if not key or not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', key):
            print(f'❌ key 格式无效: {key}')
            print('   key 必须以字母开头，只能包含字母、数字、下划线和连字符')
            sys.exit(1)
        
        # 验证 repo URL 格式
        if not repo_url or not re.match(r'^https://github\.com/[^/]+/[^/]+$', repo_url):
            print(f'❌ 仓库 URL 格式无效: {repo_url}')
            print('   URL 必须是有效的 GitHub 仓库地址')
            sys.exit(1)
        
        # 验证仓库是否包含 fnpack.json
        try:
            print(f'正在验证仓库 {repo_url}...')
            github_token = os.environ.get('GITHUB_TOKEN')
            fnpack_info = fetch_fnpack_info(repo_url, github_token=github_token)
            
            if fnpack_info:
                app_count = len(fnpack_info) if isinstance(fnpack_info, dict) else 1
                print(f'✅ 仓库验证通过，包含 {app_count} 个应用')
                
                # 打印应用信息预览
                if isinstance(fnpack_info, dict):
                    for app_key, app_info in fnpack_info.items():
                        print(f'\n  应用: {app_info.get("name", app_key)}')
                        print(f'    版本: {app_info.get("version", "未知")}')
                        print(f'    描述: {app_info.get("description", "暂无描述")[:50]}...' if len(app_info.get("description", "")) > 50 else f'    描述: {app_info.get("description", "暂无描述")}')
                        print(f'    图标: {"✅ 有" if app_info.get("iconUrl") else "❌ 无"}')
                        print(f'    下载: {"✅ 有" if app_info.get("downloadUrl") else "❌ 无"}')
            else:
                print(f'❌ 仓库中未找到有效的 fnpack.json 或无法解析')
                sys.exit(1)
                
        except Exception as e:
            print(f'❌ 验证仓库失败: {str(e)}')
            sys.exit(1)
        
        # 检查 key 是否已存在
        if check_fnpack_key_exists(key, api):
            print(f'⚠️ 注意: fnpack key {key} 已存在，合并后将更新现有仓库')
        else:
            print(f'✅ 验证通过: 新 fnpack 仓库 {key}')
    
    print('\n========== fnpacks.json 验证完成 ==========\n')


def validate_apps_pr(pr, api, repo_owner, repo_name, pull_request_number):
    """
    验证 apps.json 的 PR 修改
    """
    print('\n========== 验证 apps.json ==========')
    
    # 从PR中获取apps.json内容
    pr_apps_data = get_apps_json_from_pr(pull_request_number, api, repo_owner, repo_name)
    
    # 从基础分支获取apps.json内容
    base_apps_data = get_base_apps_json(pr['base']['sha'], api, repo_owner, repo_name)
    
    # 找出新增或修改的应用
    modified_apps, deleted_apps = find_modified_apps(pr_apps_data, base_apps_data)
    
    if len(modified_apps) == 0 and len(deleted_apps) == 0:
        print('apps.json 中没有检测到新增、修改或删除的应用')
        return
    
    # 处理删除的应用
    if len(deleted_apps) > 0:
        for deleted_app in deleted_apps:
            app_id = deleted_app.get('id')
            app_name = deleted_app.get('name')
            print(f'检测到应用删除: {app_name} ({app_id})')
            print('⚠️ 注意: 此操作将从应用列表中永久移除该应用')
    
    # 处理新增或修改的应用
    for app in modified_apps:
        app_id = app.get('id')
        app_name = app.get('name')
        repo_url = app.get('repository')
        
        print(f'\n--- 验证应用: {app_name} ({app_id}) ---')
        
        # 验证应用信息
        validation_result = validate_app_info(app_id, app_name, repo_url)
        
        if not validation_result['is_valid']:
            print('❌ 应用信息验证失败:')
            for error in validation_result['errors']:
                print(f'  - {error}')
            sys.exit(1)
        
        # 获取GitHub上的应用信息
        try:
            print(f'正在获取GitHub上的应用信息用于预览...')
            github_app_info = fetch_app_info(repo_url)
            
            print(f'  应用描述: {github_app_info.get("description", "暂无描述")[:50]}...' if len(github_app_info.get("description", "")) > 50 else f'  应用描述: {github_app_info.get("description", "暂无描述")}')
            print(f'  版本信息: {github_app_info.get("version", "未知")}')
            print(f'  作者信息: {github_app_info.get("author", "未知")}')
            print(f'  星标数量: {github_app_info.get("stars", 0)}')
            print(f'  分类信息: {github_app_info.get("category", "未分类")}')
            
            # 检查下载链接
            download_url = github_app_info.get('downloadUrl')
            if not download_url or download_url in ['暂无下载链接', '获取失败']:
                print('  ❌ 警告：未能从GitHub仓库获取有效的下载链接')
            else:
                print(f'  ✅ 下载链接: {download_url}')
            
            # 检查应用ID是否已存在
            if check_app_id_exists(app_id, api):
                print(f'⚠️ 注意: 应用ID {app_id} 已存在，合并后将更新现有应用')
            else:
                print(f'✅ 验证通过: 新应用 {app_name} ({app_id})')
            
        except Exception as e:
            print(f'❌ 获取GitHub应用信息预览失败: {str(e)}')
            sys.exit(1)
    
    print('\n========== apps.json 验证完成 ==========\n')


if __name__ == "__main__":
    args = sys.argv[1:]
    
    if len(args) == 3:
        # 直接验证提供的参数
        app_id, app_name, repo_url = args
        validation_result = validate_app_info(app_id, app_name, repo_url)
        
        if validation_result['is_valid']:
            print('验证通过')
            # 创建 API 实例检查应用ID是否存在
            github_token = os.environ.get('GITHUB_TOKEN')
            api = GitHubAPI(github_token) if github_token else GitHubAPI()
            if check_app_id_exists(app_id, api):
                print(f'应用ID {app_id} 已存在')
        else:
            print('验证失败:')
            for error in validation_result['errors']:
                print(f'- {error}')
            sys.exit(1)
    else:
        # 作为GitHub Action运行
        run()