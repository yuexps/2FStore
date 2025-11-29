#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys
import argparse
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from fetch_app_info import fetch_app_info
except ImportError:
    # 如果作为模块运行，使用相对导入
    from .fetch_app_info import fetch_app_info

def load_apps_list():
    """
    加载应用列表
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    apps_list_file_path = os.path.join(script_dir, '..', 'apps.json')
    
    try:
        with open(apps_list_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"apps": []}
    except Exception as e:
        print(f"加载应用列表时出错: {str(e)}")
        return {"apps": []}


def save_apps_list(apps_data):
    """
    保存应用列表
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    apps_list_file_path = os.path.join(script_dir, '..', 'apps.json')
    
    try:
        os.makedirs(os.path.dirname(apps_list_file_path), exist_ok=True)
        with open(apps_list_file_path, 'w', encoding='utf-8') as f:
            json.dump(apps_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存应用列表时出错: {str(e)}")
        return False


def add_app(app_id, app_name, repo_url):
    """
    添加新应用到列表
    """
    apps_data = load_apps_list()
    
    # 检查是否已存在
    for app in apps_data["apps"]:
        if app["id"] == app_id:
            print(f"应用 {app_id} 已存在于列表中")
            return False
    
    # 添加新应用
    new_app = {
        "id": app_id,
        "name": app_name,
        "repository": repo_url
    }
    
    apps_data["apps"].append(new_app)
    
    if save_apps_list(apps_data):
        print(f"成功添加应用: {app_name} ({app_id})")
        return True
    else:
        print(f"添加应用失败: {app_name} ({app_id})")
        return False


def remove_app(app_id):
    """
    从列表中移除应用
    """
    apps_data = load_apps_list()
    
    # 查找并移除应用
    original_length = len(apps_data["apps"])
    apps_data["apps"] = [app for app in apps_data["apps"] if app["id"] != app_id]
    
    if len(apps_data["apps"]) < original_length:
        if save_apps_list(apps_data):
            print(f"成功移除应用: {app_id}")
            return True
        else:
            print(f"移除应用失败: {app_id}")
            return False
    else:
        print(f"未找到应用: {app_id}")
        return False


def list_apps():
    """
    列出所有应用
    """
    apps_data = load_apps_list()
    apps = apps_data.get("apps", [])
    
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
    
    args = parser.parse_args()
    
    if args.command == 'add':
        add_app(args.id, args.name, args.repo)
    elif args.command == 'remove':
        remove_app(args.id)
    elif args.command == 'list':
        list_apps()
    elif args.command == 'preview':
        preview_app(args.repo)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()