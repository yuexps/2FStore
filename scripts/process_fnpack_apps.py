#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FnDepot 应用管理工具
管理使用 fnpack.json 格式的应用
"""

import json
import os
import sys
import re
import argparse

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import FnpacksStore, parse_github_url
from fetch_fnpack_info import fetch_fnpack_info, update_apps_from_fnpack


def add_fnpack_app(repo_url, app_key=None, github_token=None):
    """
    添加一个使用 fnpack.json 格式的应用（只需要 GitHub 仓库 URL）
    将应用信息从 fnpack.json 获取并存储到 data/fnpack_details.json
    """
    # 如果没有提供 token，尝试从环境变量获取
    if not github_token:
        github_token = os.environ.get('GITHUB_TOKEN') or os.environ.get('PERSONAL_TOKEN')
    
    try:
        print(f"正在从 {repo_url} 的fnpack.json获取应用信息...")
        app_info = fetch_fnpack_info(repo_url, app_key, github_token)
        
        if not app_info:
            print("未找到有效的fnpack.json或解析失败")
            return False
        
        # 获取仓库所有者作为 key
        parsed = parse_github_url(repo_url)
        owner = parsed['owner'] if parsed else None
        
        if not owner:
            print("无法解析仓库URL")
            return False
        
        # 检查 fnpack 是否已存在
        store = FnpacksStore()
        if store.find_fnpack_by_repo(repo_url):
            print(f"fnpack仓库 {repo_url} 已存在于列表中")
            return False
        
        # 添加到 fnpacks 列表
        store.add_or_update_fnpack(owner, repo_url)
        
        # 更新到 fnpack_details.json
        update_apps_from_fnpack(owner, owner, repo_url, app_key, github_token)
        
        # 根据 fnpack_info 类型确定显示信息
        if isinstance(app_info, dict) and 'name' in app_info:
            app_name = app_info.get('name', '未知应用')
            app_id = f"{owner}_{app_key or 'main'}"
            print(f"成功添加应用: {app_name} (ID: {app_id})")
        else:
            app_count = len(app_info) if isinstance(app_info, dict) else 1
            print(f"成功添加 {app_count} 个应用")
            print(f"应用ID格式: {owner}_[app_key]")
        
        print(f"应用信息已存储到 data/fnpack_details.json")
        return True
        
    except Exception as e:
        print(f"添加应用时出错: {str(e)}")
        return False


def update_fnpack_app(app_id=None, repo_url=None, app_key=None, github_token=None):
    """
    更新应用信息，使用 fnpack.json
    将应用信息存储到 data/fnpack_details.json
    可以通过 app_id（从应用列表中查找）或直接提供 repo_url 来更新
    """
    # 如果没有提供 token，尝试从环境变量获取
    if not github_token:
        github_token = os.environ.get('GITHUB_TOKEN') or os.environ.get('PERSONAL_TOKEN')
    
    try:
        if repo_url:
            print(f"正在从 {repo_url} 的fnpack.json获取应用信息...")
            app_info = fetch_fnpack_info(repo_url, app_key, github_token)
            
            if not app_info:
                print("未找到有效的fnpack.json或解析失败")
                return False
            
            current_app_id = app_info.get('fnpack_app_key')
            display_name = app_info.get('name')
            
            # 获取仓库所有者作为 key
            parsed = parse_github_url(repo_url)
            if parsed:
                owner = parsed['owner']
                store = FnpacksStore()
                store.add_or_update_fnpack(owner, repo_url)
            
            # 更新到 fnpack_details.json
            success = update_apps_from_fnpack(current_app_id, display_name, repo_url, app_key, github_token)
            
            if success:
                print(f"成功更新应用: {display_name} (ID: {current_app_id})")
                print(f"更新后的信息已存储到 data/fnpack_details.json")
                return True
            else:
                print("更新失败，请检查fnpack.json是否存在且格式正确")
                return False
        else:
            # 从应用列表中查找
            store = FnpacksStore()
            fnpacks = store.get_fnpacks()
            
            # 在 fnpacks 中查找匹配的 key
            repo_url = None
            for fnpack in fnpacks:
                if fnpack.get('key') == app_id:
                    repo_url = fnpack.get('repo')
                    break
            
            if not repo_url:
                print(f"错误: 未找到key为 {app_id} 的fnpack仓库")
                return False
            
            current_app_key = app_key  # 使用传入的 app_key
            
            print(f"正在更新 {app_id} 的应用信息，从 {repo_url} 的fnpack.json获取...")
            
            # 更新应用信息
            success = update_apps_from_fnpack(
                app_id, 
                app_id,
                repo_url, 
                current_app_key,
                github_token
            )
            
            if success:
                print(f"成功使用fnpack.json更新仓库信息并存储到fnpack_details.json: {app_id} ({repo_url})")
                return True
            else:
                print(f"使用fnpack.json更新仓库信息失败: {app_id} ({repo_url})")
                return False
    except Exception as e:
        print(f"更新应用时出错: {str(e)}")
        return False


from concurrent.futures import ThreadPoolExecutor, as_completed

def process_repo_for_batch(fnpack, existing_apps_map, github_token):
    """
    处理单个仓库的更新（供并发调用）
    返回: list of app_details
    """
    repo_key = fnpack.get('key')
    repo_url = fnpack.get('repo')
    
    try:
        # 获取此仓库的现有应用数据，用于增量检查
        repo_existing_apps = existing_apps_map.get(repo_url, [])
        
        # 获取应用信息 (支持增量)
        app_info_map = fetch_fnpack_info(repo_url, None, github_token, repo_existing_apps)
        
        if not app_info_map:
            return []
            
        processed_apps = []
        
        # 统一处理返回结果（可能是单个字典或字典的字典）
        # fetch_fnpack_info 如果没指定 app_key，返回的是 {app_key: info}
        # 如果返回的是跳过的结果 (复用了 existing_apps 且更新了 star/fork)，结构是一样的
        
        if isinstance(app_info_map, dict):
             for app_key, single_app_info in app_info_map.items():
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
                    'author_url': single_app_info.get('author_url', ''),
                    'bug_report_url': single_app_info.get('bug_report_url', ''),
                    'history': single_app_info.get('history', {}),
                    'stars': single_app_info.get('stars', 0),
                    'forks': single_app_info.get('forks', 0),
                    'category': single_app_info.get('category', 'uncategorized'),
                    'lastUpdate': single_app_info.get('lastUpdate', ''),
                    'fnpack_app_key': app_key,
                    'fnpack_repo_key': repo_key,
                    'install_type': single_app_info.get('install_type', ''),
                    'size': single_app_info.get('size', '')
                }
                processed_apps.append(new_app_detail)
        
        return processed_apps
        
    except Exception as e:
        print(f"处理仓库 {repo_key} 失败: {str(e)}")
        return []

def batch_update_fnpack_apps(github_token=None):
    """
    批量更新所有使用 fnpack.json 格式的应用 (并发版)
    """
    if not github_token:
        github_token = os.environ.get('GITHUB_TOKEN')
    
    try:
        from utils.data_store import FnpacksStore, FnpackDetailsStore
        
        store = FnpacksStore()
        fnpacks = store.get_fnpacks()
        
        if not fnpacks:
            print("fnpack仓库列表为空")
            return False
            
        details_store = FnpackDetailsStore()
        # 加载所有现有应用，用于增量更新
        all_existing_data = details_store.load()
        existing_apps_list = all_existing_data.get('apps', [])
        
        # 按仓库URL分组现有应用，以便传递给 worker
        existing_apps_map = {}
        for app in existing_apps_list:
            repo_url = app.get('repository')
            if repo_url:
                if repo_url not in existing_apps_map:
                    existing_apps_map[repo_url] = []
                existing_apps_map[repo_url].append(app)

        print(f"开始批量更新 {len(fnpacks)} 个fnpack仓库 (并发)...")
        
        all_new_apps = []
        valid_app_ids = set()
        repo_success_count = 0
        repo_fail_count = 0
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_fnpack = {
                executor.submit(process_repo_for_batch, fnpack, existing_apps_map, github_token): fnpack 
                for fnpack in fnpacks
            }
            
            for future in as_completed(future_to_fnpack):
                fnpack = future_to_fnpack[future]
                repo_key = fnpack.get('key')
                
                try:
                    repo_apps = future.result()
                    if repo_apps:
                        repo_success_count += 1
                        all_new_apps.extend(repo_apps)
                        for app in repo_apps:
                            valid_app_ids.add(app['id'])
                        print(f"✓ 成功更新: {repo_key} ({len(repo_apps)} 个应用)")
                    else:
                        # 可能是空仓库或失败
                        # 如果没有返回数据，就不计入成功，但也不一定是严重错误
                        print(f"⚠ 仓库 {repo_key} 未返回应用数据或更新失败")
                        
                except Exception as exc:
                    repo_fail_count += 1
                    print(f"✗ 更新仓库 {repo_key} 发生异常: {exc}")

        # 批量保存
        if all_new_apps:
            print(f"正在保存 {len(all_new_apps)} 个应用的数据...")
            details_store.upsert_apps_batch(all_new_apps)
        
        # 清理已删除的应用
        cleaned_count = _cleanup_deleted_fnpack_apps(valid_app_ids)
        
        print(f"\n批量更新完成!")
        print(f"成功获取应用总数: {len(all_new_apps)}")
        if cleaned_count > 0:
            print(f"清理删除: {cleaned_count} 个应用")
            
        return True
        
    except Exception as e:
        print(f"批量更新过程中出现错误: {str(e)}")
        return False


def _cleanup_deleted_fnpack_apps(valid_app_ids):
    """
    清理已从 fnpacks.json 或仓库 fnpack.json 中移除的应用
    """
    try:
        from utils.data_store import FnpackDetailsStore
        store = FnpackDetailsStore()
        
        # 获取当前存储的数据
        fnpack_details_data = store.load()
        
        if 'apps' not in fnpack_details_data:
            return 0
        
        original_count = len(fnpack_details_data['apps'])
        
        # 过滤掉不在有效列表中的应用
        fnpack_details_data['apps'] = [
            app for app in fnpack_details_data['apps']
            if app.get('id') in valid_app_ids
        ]
        
        cleaned_count = original_count - len(fnpack_details_data['apps'])
        
        if cleaned_count > 0:
            # 使用store.save()方法保存，这样会检查数据是否真正变化
            store.save(fnpack_details_data)
            print(f"已清理 {cleaned_count} 个已删除的应用")
        
        return cleaned_count
    except Exception as e:
        print(f"清理已删除应用时出错: {str(e)}")
        return 0


def preview_fnpack_app(repo_url, app_key=None, github_token=None):
    """
    预览从 fnpack.json 获取的应用信息，格式将与 fnpack_details.json 保持一致
    """
    # 如果没有提供 token，尝试从环境变量获取
    if not github_token:
        github_token = os.environ.get('GITHUB_TOKEN') or os.environ.get('PERSONAL_TOKEN')
    
    try:
        print(f"正在从 {repo_url} 的fnpack.json获取应用信息...")
        print(f"格式将与fnpack_details.json保持一致，供网页端读取")
        app_info = fetch_fnpack_info(repo_url, app_key, github_token)
        
        if app_info:
            # 判断是单个应用还是多个应用
            if 'name' in app_info and 'description' in app_info:
                # 单个应用情况
                print("\n从fnpack.json获取到的应用信息 (将以网页端兼容格式存储):")
                print("-" * 50)
                for key, value in app_info.items():
                    if key == 'screenshots':
                        print(f"{key}: {len(value)} 张截图")
                    else:
                        print(f"{key}: {value}")
                print("-" * 50)
            else:
                # 多个应用情况
                print(f"\n从fnpack.json获取到 {len(app_info)} 个应用信息 (将以网页端兼容格式存储):")
                for idx, (app_key, app_data) in enumerate(app_info.items(), 1):
                    print(f"\n{idx}. 应用: {app_data.get('name', app_key)}")
                    print("-" * 50)
                    for key, value in app_data.items():
                        if key == 'screenshots':
                            print(f"  {key}: {len(value)} 张截图")
                        else:
                            print(f"  {key}: {value}")
                    print("-" * 50)
            
            print(f"\n注: 添加到系统后，此信息将以网页端兼容格式存储在 data/fnpack_details.json")
            print(f"注: 应用ID将以 '仓库key_应用key' 格式生成，确保唯一性")
            return app_info
        else:
            print("未找到有效的fnpack.json或解析失败")
            return None
    except Exception as e:
        print(f"获取fnpack信息时出错: {str(e)}")
        return None


def main():
    parser = argparse.ArgumentParser(description="FN-Free-Store fnpack.json 处理工具")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 添加全局参数支持token
    parser.add_argument('--token', help='GitHub API token，用于提高API调用限制')
    
    # 添加使用fnpack.json的应用命令
    add_parser = subparsers.add_parser('add', help='添加使用fnpack.json的新应用')
    add_parser.add_argument('repo', help='仓库URL')
    add_parser.add_argument('--app-key', help='fnpack.json中的应用键名（可选，如果有多个应用）')
    
    # 更新使用fnpack.json的应用命令
    update_parser = subparsers.add_parser('update', help='更新应用信息，使用fnpack.json')
    update_parser.add_argument('target', help='应用ID或仓库URL')
    update_parser.add_argument('--app-key', help='fnpack.json中的应用键名（可选）')
    update_parser.add_argument('--url', action='store_true', help='指定target为URL而不是应用ID')
    
    # 批量更新命令
    batch_parser = subparsers.add_parser('batch-update', help='批量更新所有应用，尝试使用fnpack.json')
    
    # 预览fnpack应用命令
    preview_parser = subparsers.add_parser('preview', help='预览从fnpack.json获取的应用信息')
    preview_parser.add_argument('repo', help='仓库URL')
    preview_parser.add_argument('--app-key', help='fnpack.json中的应用键名（可选）')
    

    
    args = parser.parse_args()
    
    if args.command == 'add':
        add_fnpack_app(args.repo, args.app_key, args.token)
    elif args.command == 'update':
        if args.url or args.target.startswith(('http://', 'https://')):
            update_fnpack_app(repo_url=args.target, app_key=args.app_key, github_token=args.token)
        else:
            update_fnpack_app(app_id=args.target, app_key=args.app_key, github_token=args.token)
    elif args.command == 'batch-update':
        batch_update_fnpack_apps(github_token=args.token)
    elif args.command == 'preview':
        preview_fnpack_app(args.repo, args.app_key, args.token)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()