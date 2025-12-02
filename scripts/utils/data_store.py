#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据存储模块
统一处理 JSON 数据文件的读写操作
"""

import json
import os
from datetime import datetime
from .config import (
    get_apps_json_path,
    get_fnpacks_json_path,
    get_data_path,
    ensure_data_dir
)


class DataStore:
    """数据存储类，处理 JSON 文件读写"""
    
    @staticmethod
    def load_json(file_path, default=None):
        """
        加载 JSON 文件
        
        参数:
        - file_path: 文件路径
        - default: 文件不存在或解析失败时返回的默认值
        
        返回:
        - 解析后的数据或默认值
        """
        if default is None:
            default = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return default
        except json.JSONDecodeError as e:
            print(f"JSON 解析错误 ({file_path}): {str(e)}")
            return default
        except Exception as e:
            print(f"读取文件错误 ({file_path}): {str(e)}")
            return default
    
    @staticmethod
    def save_json(file_path, data, indent=2):
        """
        保存数据到 JSON 文件
        
        参数:
        - file_path: 文件路径
        - data: 要保存的数据
        - indent: 缩进空格数
        
        返回:
        - bool: 是否成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)
            return True
        except Exception as e:
            print(f"保存文件错误 ({file_path}): {str(e)}")
            return False


class AppsStore:
    """apps.json 数据操作类"""
    
    def __init__(self):
        self.file_path = get_apps_json_path()
    
    def load(self):
        """加载应用列表"""
        return DataStore.load_json(self.file_path, {'apps': []})
    
    def save(self, data):
        """保存应用列表"""
        return DataStore.save_json(self.file_path, data)
    
    def get_apps(self):
        """获取所有应用"""
        data = self.load()
        return data.get('apps', [])
    
    def get_all_apps(self):
        """获取所有应用（别名方法）"""
        return self.get_apps()
    
    def get_app_ids(self):
        """获取所有应用ID集合"""
        return {app.get('id') for app in self.get_apps() if app.get('id')}
    
    def find_app(self, app_id):
        """根据ID查找应用"""
        for app in self.get_apps():
            if app.get('id') == app_id:
                return app
        return None
    
    def add_app(self, app_id, app_name, repo_url):
        """
        添加新应用
        
        返回:
        - bool: 是否成功（如果已存在返回False）
        """
        data = self.load()
        
        # 检查是否已存在
        for app in data['apps']:
            if app.get('id') == app_id:
                print(f"应用 {app_id} 已存在")
                return False
        
        data['apps'].append({
            'id': app_id,
            'name': app_name,
            'repository': repo_url
        })
        
        return self.save(data)
    
    def add_or_update_app(self, app_id, app_name, repo_url):
        """
        添加或更新应用
        
        返回:
        - bool: 是否成功
        """
        data = self.load()
        
        # 检查是否已存在
        for app in data['apps']:
            if app.get('id') == app_id:
                app['name'] = app_name
                app['repository'] = repo_url
                return self.save(data)
        
        # 不存在则添加
        data['apps'].append({
            'id': app_id,
            'name': app_name,
            'repository': repo_url
        })
        
        return self.save(data)
    
    def update_app(self, app_id, app_name=None, repo_url=None):
        """
        更新应用信息
        
        返回:
        - bool: 是否成功
        """
        data = self.load()
        
        for app in data['apps']:
            if app.get('id') == app_id:
                if app_name:
                    app['name'] = app_name
                if repo_url:
                    app['repository'] = repo_url
                return self.save(data)
        
        print(f"未找到应用 {app_id}")
        return False
    
    def remove_app(self, app_id):
        """
        移除应用
        
        返回:
        - bool: 是否成功
        """
        data = self.load()
        original_length = len(data['apps'])
        data['apps'] = [app for app in data['apps'] if app.get('id') != app_id]
        
        if len(data['apps']) < original_length:
            return self.save(data)
        
        print(f"未找到应用 {app_id}")
        return False


class FnpacksStore:
    """fnpacks.json 数据操作类"""
    
    def __init__(self):
        self.file_path = get_fnpacks_json_path()
    
    def load(self):
        """加载 fnpack 仓库列表"""
        return DataStore.load_json(self.file_path, {'fnpacks': []})
    
    def save(self, data):
        """保存 fnpack 仓库列表"""
        return DataStore.save_json(self.file_path, data)
    
    def get_fnpacks(self):
        """获取所有 fnpack 仓库"""
        data = self.load()
        return data.get('fnpacks', [])
    
    def find_fnpack(self, key=None, repo_url=None):
        """根据 key 或 repo_url 查找 fnpack"""
        for fnpack in self.get_fnpacks():
            if key and fnpack.get('key') == key:
                return fnpack
            if repo_url and fnpack.get('repo') == repo_url:
                return fnpack
        return None
    
    def find_fnpack_by_repo(self, repo_url):
        """根据仓库 URL 查找 fnpack"""
        return self.find_fnpack(repo_url=repo_url)
    
    def add_fnpack(self, key, repo_url):
        """
        添加 fnpack 仓库
        
        返回:
        - bool: 是否成功
        """
        data = self.load()
        
        # 检查是否已存在
        if self.find_fnpack(key=key) or self.find_fnpack(repo_url=repo_url):
            print(f"fnpack 仓库已存在: {key}")
            return False
        
        data['fnpacks'].append({
            'key': key,
            'repo': repo_url
        })
        
        return self.save(data)
    
    def add_or_update_fnpack(self, key, repo_url):
        """
        添加或更新 fnpack 仓库
        
        返回:
        - bool: 是否成功
        """
        data = self.load()
        
        # 检查是否已存在
        for i, fnpack in enumerate(data['fnpacks']):
            if fnpack.get('repo') == repo_url:
                data['fnpacks'][i]['key'] = key
                return self.save(data)
        
        # 不存在则添加
        data['fnpacks'].append({
            'key': key,
            'repo': repo_url
        })
        
        return self.save(data)
    
    def remove_fnpack(self, key):
        """
        移除 fnpack 仓库
        
        返回:
        - bool: 是否成功
        """
        data = self.load()
        original_length = len(data['fnpacks'])
        data['fnpacks'] = [f for f in data['fnpacks'] if f.get('key') != key]
        
        if len(data['fnpacks']) < original_length:
            return self.save(data)
        
        print(f"未找到 fnpack 仓库: {key}")
        return False


class AppDetailsStore:
    """app_details.json 数据操作类"""
    
    def __init__(self):
        ensure_data_dir()
        self.file_path = get_data_path('app_details.json')
    
    def load(self):
        """加载应用详情"""
        return DataStore.load_json(self.file_path, {
            'apps': [],
            'lastUpdated': ''
        })
    
    def save(self, data):
        """保存应用详情"""
        data['lastUpdated'] = datetime.utcnow().isoformat() + 'Z'
        return DataStore.save_json(self.file_path, data)
    
    def get_apps(self):
        """获取所有应用详情"""
        return self.load().get('apps', [])
    
    def find_app(self, app_id):
        """根据ID查找应用详情"""
        for app in self.get_apps():
            if app.get('id') == app_id:
                return app
        return None
    
    def upsert_app(self, app_detail):
        """
        更新或插入应用详情
        
        参数:
        - app_detail: 包含 id 的应用详情字典
        
        返回:
        - bool: 是否成功
        """
        if not app_detail.get('id'):
            print("应用详情必须包含 id")
            return False
        
        data = self.load()
        app_id = app_detail['id']
        
        # 查找并更新或插入
        found = False
        for i, app in enumerate(data['apps']):
            if app.get('id') == app_id:
                data['apps'][i] = app_detail
                found = True
                break
        
        if not found:
            data['apps'].append(app_detail)
        
        return self.save(data)
    
    def remove_app(self, app_id):
        """移除应用详情"""
        data = self.load()
        original_length = len(data['apps'])
        data['apps'] = [app for app in data['apps'] if app.get('id') != app_id]
        
        if len(data['apps']) < original_length:
            return self.save(data)
        return False
    
    def sync_with_apps_list(self, active_app_ids):
        """
        与 apps.json 同步，移除不存在的应用
        
        参数:
        - active_app_ids: 当前活跃的应用ID集合
        
        返回:
        - int: 移除的应用数量
        """
        data = self.load()
        original_length = len(data['apps'])
        data['apps'] = [app for app in data['apps'] if app.get('id') in active_app_ids]
        removed_count = original_length - len(data['apps'])
        
        if removed_count > 0:
            self.save(data)
            print(f"清理了 {removed_count} 个已删除应用的详细信息")
        
        return removed_count


class FnpackDetailsStore:
    """fnpack_details.json 数据操作类"""
    
    def __init__(self):
        ensure_data_dir()
        self.file_path = get_data_path('fnpack_details.json')
    
    def load(self):
        """加载 fnpack 应用详情"""
        return DataStore.load_json(self.file_path, {
            'apps': [],
            'lastUpdated': ''
        })
    
    def save(self, data):
        """保存 fnpack 应用详情"""
        data['lastUpdated'] = datetime.utcnow().isoformat() + 'Z'
        return DataStore.save_json(self.file_path, data)
    
    def get_apps(self):
        """获取所有应用详情"""
        return self.load().get('apps', [])
    
    def upsert_app(self, app_detail):
        """更新或插入应用详情"""
        if not app_detail.get('id'):
            print("应用详情必须包含 id")
            return False
        
        data = self.load()
        app_id = app_detail['id']
        
        found = False
        for i, app in enumerate(data['apps']):
            if app.get('id') == app_id:
                data['apps'][i] = app_detail
                found = True
                break
        
        if not found:
            data['apps'].append(app_detail)
        
        return self.save(data)
    
    def upsert_apps_batch(self, apps_list):
        """
        批量更新或插入应用详情
        
        参数:
        - apps_list: 应用详情列表
        
        返回:
        - int: 更新的应用数量
        """
        data = self.load()
        existing_ids = {app.get('id'): i for i, app in enumerate(data['apps'])}
        
        count = 0
        for app_detail in apps_list:
            app_id = app_detail.get('id')
            if not app_id:
                continue
            
            if app_id in existing_ids:
                data['apps'][existing_ids[app_id]] = app_detail
            else:
                data['apps'].append(app_detail)
                existing_ids[app_id] = len(data['apps']) - 1
            count += 1
        
        self.save(data)
        return count
