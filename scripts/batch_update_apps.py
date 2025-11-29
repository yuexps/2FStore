#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from fetch_app_info import update_apps
except ImportError:
    # 如果作为模块运行，使用相对导入
    from .fetch_app_info import update_apps

# 修改batch_update_apps函数
def batch_update_apps():
    """
    批量更新所有应用信息
    """
    # 应用列表文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    apps_list_file_path = os.path.join(script_dir, '..', 'apps.json')
    
    try:
        # 读取应用列表
        with open(apps_list_file_path, 'r', encoding='utf-8') as f:
            apps_data = json.load(f)
        
        apps = apps_data.get('apps', [])
        if not apps:
            print("应用列表为空")
            return
        
        # 获取当前活跃的应用ID集合
        active_app_ids = {app.get('id') for app in apps if app.get('id')}
        
        # 首先清理已删除的应用
        update_apps(active_app_ids=active_app_ids)
        
        # 然后遍历并更新每个应用
        for app in apps:
            app_id = app.get('id')
            app_name = app.get('name')
            repo_url = app.get('repository')
            
            if not app_id or not app_name or not repo_url:
                print(f"跳过无效的应用条目: {app}")
                continue
            
            try:
                print(f"正在处理应用: {app_name} ({app_id})")
                update_apps(app_id, app_name, repo_url)
            except Exception as e:
                print(f"处理应用 {app_name} 时出错: {str(e)}")
                # 继续处理下一个应用，不中断整个流程
        
        print("批量更新完成")
        
    except FileNotFoundError:
        print(f"应用列表文件不存在: {apps_list_file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"解析应用列表文件失败: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"批量更新过程中出现错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    batch_update_apps()