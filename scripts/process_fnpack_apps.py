#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys
import argparse
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def load_apps_list():
    """
    从fnpacks.json加载fnpack仓库列表
    返回格式: {"fnpacks": [...]}  
    fnpacks: 包含fnpack仓库的数组
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    fnpacks_file_path = os.path.join(script_dir, '..', 'fnpacks.json')
    
    try:
        with open(fnpacks_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 直接返回fnpacks数据
            return {
                'fnpacks': data.get('fnpacks', [])
            }
    except FileNotFoundError:
        print(f"fnpacks.json文件不存在，将创建空列表")
        return {"fnpacks": []}
    except Exception as e:
        print(f"加载fnpacks.json时出错: {str(e)}")
        return {"fnpacks": []}


def save_apps_list(apps_list):
    """
    保存fnpack仓库列表到fnpacks.json
    apps_list格式: {"fnpacks": [...]}  
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    fnpacks_file_path = os.path.join(script_dir, '..', 'fnpacks.json')
    
    try:
        os.makedirs(os.path.dirname(fnpacks_file_path), exist_ok=True)
        
        # 构建要保存的数据结构
        save_data = {
            'fnpacks': apps_list.get('fnpacks', [])
        }
        
        # 写回文件
        with open(fnpacks_file_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        print(f"fnpacks数据已保存到: {fnpacks_file_path}")
        return True
    except Exception as e:
        print(f"保存fnpacks.json时出错: {str(e)}")
        return False


def add_fnpack_app(repo_url, app_key=None, github_token=None):
    """
    添加一个使用fnpack.json格式的应用（只需要GitHub仓库URL）
    将应用信息从fnpack.json获取并存储到 data/fnpack_details.json
    """
    try:
        # 确保导入路径正确
        import importlib.util
        script_dir = os.path.dirname(os.path.abspath(__file__))
        spec = importlib.util.spec_from_file_location("fetch_fnpack_info", 
                                                     os.path.join(script_dir, "fetch_fnpack_info.py"))
        fetch_fnpack_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fetch_fnpack_module)
        
        print(f"正在从 {repo_url} 的fnpack.json获取应用信息...")
        app_info = fetch_fnpack_module.fetch_fnpack_info(repo_url, app_key, github_token)
        
        if app_info:
            # 获取仓库所有者作为key
            import re
            match = re.search(r'github\.com\/([^\/]+)\/([^\/]+)', repo_url)
            owner = match.group(1) if match else None
            
            # 添加到应用列表
            apps_list = load_apps_list()
            
            # 检查fnpack是否已存在
            fnpack_exists = False
            for fnpack in apps_list['fnpacks']:
                if fnpack.get('repo') == repo_url:
                    fnpack_exists = True
                    print(f"fnpack仓库 {repo_url} 已存在于列表中")
                    return False
            
            # 添加到fnpacks数组
            if owner:
                apps_list['fnpacks'].append({
                    "key": owner,
                    "repo": repo_url
                })
            
            if save_apps_list(apps_list):
                # 更新到fnpack_details.json
                fetch_fnpack_module.update_apps_from_fnpack(owner, owner, repo_url, app_key, github_token)
                
                # 根据fnpack_info类型确定显示信息
                if isinstance(app_info, dict) and 'name' in app_info:
                    # 单个应用
                    app_name = app_info.get('name', '未知应用')
                    app_id = f"{owner}_{app_key or 'main'}"
                    print(f"成功添加应用: {app_name} (ID: {app_id})")
                else:
                    # 多个应用
                    app_count = len(app_info) if isinstance(app_info, dict) else 1
                    print(f"成功添加 {app_count} 个应用")
                    print(f"应用ID格式: {owner}_[app_key]")
                    
                print(f"应用信息已存储到 data/fnpack_details.json")
                return True
            else:
                print("保存应用列表失败")
                return False
        else:
            print("未找到有效的fnpack.json或解析失败")
            return False
    except Exception as e:
        print(f"添加应用时出错: {str(e)}")
        return False


def update_fnpack_app(app_id=None, repo_url=None, app_key=None, github_token=None):
    """
    更新应用信息，使用fnpack.json
    将应用信息存储到 data/fnpack_details.json
    可以通过app_id（从应用列表中查找）或直接提供repo_url来更新
    """
    try:
        # 确保导入路径正确
        import importlib.util
        script_dir = os.path.dirname(os.path.abspath(__file__))
        spec = importlib.util.spec_from_file_location("fetch_fnpack_info", 
                                                     os.path.join(script_dir, "fetch_fnpack_info.py"))
        fetch_fnpack_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fetch_fnpack_module)
        
        if repo_url:
            # 直接从repo_url更新
            print(f"正在从 {repo_url} 的fnpack.json获取应用信息...")
            app_info = fetch_fnpack_module.fetch_fnpack_info(repo_url, app_key, github_token)
            
            if app_info:
                current_app_id = app_info.get('fnpack_app_key')
                display_name = app_info.get('name')
                
                # 更新或添加到应用列表
                apps_list = load_apps_list()
                
                # 获取仓库所有者作为key
                import re
                match = re.search(r'github\.com\/([^\/]+)\/([^\/]+)', repo_url)
                if match:
                    owner = match.group(1)
                    
                    # 检查是否已存在
                    fnpack_index = -1
                    for i, fnpack in enumerate(apps_list['fnpacks']):
                        if fnpack.get('repo') == repo_url:
                            fnpack_index = i
                            break
                    
                    if fnpack_index >= 0:
                        # 更新现有fnpack
                        apps_list['fnpacks'][fnpack_index]['key'] = owner
                    else:
                        # 添加新fnpack
                        apps_list['fnpacks'].append({
                            "key": owner,
                            "repo": repo_url
                        })
                    
                    save_apps_list(apps_list)
                
                # 更新到fnpack_details.json
                success = fetch_fnpack_module.update_apps_from_fnpack(current_app_id, display_name, repo_url, app_key, github_token)
                
                if success:
                    print(f"成功更新应用: {display_name} (ID: {current_app_id})")
                    print(f"更新后的信息已存储到 data/fnpack_details.json")
                    return True
                else:
                    print("更新失败，请检查fnpack.json是否存在且格式正确")
                    return False
            else:
                print("未找到有效的fnpack.json或解析失败")
                return False
        else:
            # 从应用列表中查找
            apps_list = load_apps_list()
            
            # 在fnpacks中查找匹配的key
            repo_url = None
            for fnpack in apps_list['fnpacks']:
                if fnpack.get('key') == app_id:
                    repo_url = fnpack.get('repo')
                    break
            
            if not repo_url:
                print(f"错误: 未找到key为 {app_id} 的fnpack仓库")
                return False
            
            app_key_from_list = None  # fnpacks格式中不存储app_key，每个仓库可能有多个应用
            
            # 使用传入的app_key或从列表中获取
            current_app_key = app_key if app_key is not None else app_key_from_list
            
            print(f"正在更新 {app_id} 的应用信息，从 {repo_url} 的fnpack.json获取...")
            
            # 更新应用信息
            success = fetch_fnpack_module.update_apps_from_fnpack(
                app_id, 
                app_id,  # 使用app_id作为app_name参数，因为我们只需要从fnpack.json获取显示名称
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


def batch_update_fnpack_apps(github_token=None):
    """
    批量更新所有使用fnpack.json格式的应用
    将应用信息存储到 data/fnpack_details.json
    """
    try:
        # 确保导入路径正确
        import importlib.util
        script_dir = os.path.dirname(os.path.abspath(__file__))
        spec = importlib.util.spec_from_file_location("fetch_fnpack_info", 
                                                     os.path.join(script_dir, "fetch_fnpack_info.py"))
        fetch_fnpack_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fetch_fnpack_module)
        
        # 加载应用列表
        apps_list = load_apps_list()
        
        if not apps_list['fnpacks']:
            print("fnpack仓库列表为空")
            return False
        
        repo_success_count = 0
        repo_fail_count = 0
        total_app_success_count = 0
        
        print(f"开始批量更新 {len(apps_list['fnpacks'])} 个fnpack仓库...")
        
        for fnpack in apps_list['fnpacks']:
            app_id = fnpack.get('key')
            repo_url = fnpack.get('repo')
            app_key = None  # 不指定具体app_key，获取所有应用
            
            print(f"\n正在更新仓库: {app_id} ({repo_url})")
            print(f"从fnpack.json获取所有应用信息...")
            
            # 首先获取仓库中的应用数量
            app_info = fetch_fnpack_module.fetch_fnpack_info(repo_url, app_key, github_token)
            if app_info and isinstance(app_info, dict) and 'name' not in app_info:
                # 多个应用的情况
                repo_app_count = len(app_info)
                print(f"仓库中找到 {repo_app_count} 个应用")
            else:
                repo_app_count = 1 if app_info else 0
            
            # 调用fnpack更新函数
            success = fetch_fnpack_module.update_apps_from_fnpack(
                app_id, 
                app_id,  # 使用app_id作为app_name参数
                repo_url,
                app_key,  # 不指定具体app_key
                github_token
            )
            
            if success:
                repo_success_count += 1
                total_app_success_count += repo_app_count
                print(f"✓ 成功更新: {app_id}")
            else:
                repo_fail_count += 1
                print(f"✗ 更新失败: {app_id}")
        
        print(f"\n批量更新完成!")
        print(f"成功: {total_app_success_count} 个应用")
        print(f"失败或不适用: 0 个应用")
        print(f"  所有fnpack应用信息已存储到 data/fnpack_details.json")
        return True
    except Exception as e:
        print(f"批量更新过程中出现错误: {str(e)}")
        return False

def preview_fnpack_app(repo_url, app_key=None, github_token=None):
    """
    预览从fnpack.json获取的应用信息，格式将与fnpack_details.json保持一致
    """
    try:
        # 确保导入路径正确
        import importlib.util
        script_dir = os.path.dirname(os.path.abspath(__file__))
        spec = importlib.util.spec_from_file_location("fetch_fnpack_info", 
                                                     os.path.join(script_dir, "fetch_fnpack_info.py"))
        fetch_fnpack_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fetch_fnpack_module)
        
        print(f"正在从 {repo_url} 的fnpack.json获取应用信息...")
        print(f"格式将与fnpack_details.json保持一致，供网页端读取")
        app_info = fetch_fnpack_module.fetch_fnpack_info(repo_url, app_key, github_token)
        
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