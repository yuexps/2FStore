#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FN-Free-Store 应用管理工具
提供添加、移除、列出、预览和批量更新应用的命令行功能
"""

import os
import sys
import argparse

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import AppsStore
from fetch_app_info import fetch_app_info, update_apps


def add_app(app_id, app_name, repo_url):
    """
    添加新应用到列表
    """
    store = AppsStore()
    
    if store.find_app(app_id):
        print(f"应用 {app_id} 已存在于列表中")
        return False
    
    store.add_or_update_app(app_id, app_name, repo_url)
    print(f"成功添加应用: {app_name} ({app_id})")
    return True


def remove_app(app_id):
    """
    从列表中移除应用
    """
    store = AppsStore()
    
    if store.remove_app(app_id):
        print(f"成功移除应用: {app_id}")
        return True
    else:
        print(f"未找到应用: {app_id}")
        return False


def list_apps():
    """
    列出所有应用
    """
    store = AppsStore()
    apps = store.get_all_apps()
    
    if not apps:
        print("应用列表为空")
        return
    
    print("应用列表:")
    for i, app in enumerate(apps, 1):
        print(f"{i}. {app['name']} ({app['id']}) - {app['repository']}")


def preview_app(repo_url):
    """
    预览从仓库获取的应用信息
    """
    try:
        print(f"正在从 {repo_url} 获取应用信息...")
        app_info = fetch_app_info(repo_url)
        
        print("\n获取到的应用信息:")
        print("-" * 40)
        for key, value in app_info.items():
            if key == 'screenshots':
                print(f"{key}: {len(value)} 张截图")
            else:
                print(f"{key}: {value}")
        print("-" * 40)
        
        return app_info
    except Exception as e:
        print(f"获取应用信息时出错: {str(e)}")
        return None


def batch_update_apps():
    """
    批量更新所有应用信息
    """
    apps_store = AppsStore()
    apps = apps_store.get_apps()
    
    if not apps:
        print("应用列表为空")
        return
    
    # 获取当前活跃的应用ID集合
    active_app_ids = apps_store.get_app_ids()
    
    # 首先清理已删除的应用
    update_apps(active_app_ids=active_app_ids)
    
    # 遍历并更新每个应用
    success_count = 0
    fail_count = 0
    
    for app in apps:
        app_id = app.get('id')
        app_name = app.get('name')
        repo_url = app.get('repository')
        
        if not app_id or not app_name or not repo_url:
            print(f"跳过无效的应用条目: {app}")
            continue
        
        try:
            print(f"\n正在处理应用: {app_name} ({app_id})")
            update_apps(app_id, app_name, repo_url)
            success_count += 1
        except Exception as e:
            print(f"处理应用 {app_name} 时出错: {str(e)}")
            fail_count += 1
    
    print(f"\n批量更新完成: 成功 {success_count} 个，失败 {fail_count} 个")


def main():
    parser = argparse.ArgumentParser(description="FN-Free-Store 应用管理工具")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 添加应用命令
    add_parser = subparsers.add_parser('add', help='添加新应用')
    add_parser.add_argument('id', help='应用ID')
    add_parser.add_argument('name', help='应用名称')
    add_parser.add_argument('repo', help='仓库URL')
    
    # 移除应用命令
    remove_parser = subparsers.add_parser('remove', help='移除应用')
    remove_parser.add_argument('id', help='应用ID')
    
    # 列出应用命令
    subparsers.add_parser('list', help='列出所有应用')
    
    # 预览应用命令
    preview_parser = subparsers.add_parser('preview', help='预览应用信息')
    preview_parser.add_argument('repo', help='仓库URL')
    
    # 批量更新命令
    subparsers.add_parser('batch-update', help='批量更新所有应用元数据')
    
    args = parser.parse_args()
    
    if args.command == 'add':
        add_app(args.id, args.name, args.repo)
    elif args.command == 'remove':
        remove_app(args.id)
    elif args.command == 'list':
        list_apps()
    elif args.command == 'preview':
        preview_app(args.repo)
    elif args.command == 'batch-update':
        batch_update_apps()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()