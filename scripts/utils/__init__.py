#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
2FStore 公共工具模块

使用方法:
    from utils import GitHubAPI, validate_app_info, auto_classify_app
    from utils.data_store import AppsStore, AppDetailsStore
"""

from .github_api import GitHubAPI, fetch_github_api
from .validators import (
    validate_app_info,
    validate_app_key,
    validate_github_url,
    parse_github_url,
    validate_version
)
from .classifier import auto_classify_app, get_all_categories, get_category_display_name
from .config import (
    get_project_root,
    get_scripts_dir,
    get_data_path,
    get_apps_json_path,
    get_fnpacks_json_path,
    get_app_details_path,
    get_fnpack_details_path,
    ensure_data_dir
)
from .data_store import (
    DataStore,
    AppsStore,
    FnpacksStore,
    AppDetailsStore,
    FnpackDetailsStore
)

__all__ = [
    # GitHub API
    'GitHubAPI',
    'fetch_github_api',
    # 验证器
    'validate_app_info',
    'validate_app_key',
    'validate_github_url',
    'parse_github_url',
    'validate_version',
    # 分类器
    'auto_classify_app',
    'get_all_categories',
    'get_category_display_name',
    # 配置
    'get_project_root',
    'get_scripts_dir',
    'get_data_path',
    'get_apps_json_path',
    'get_fnpacks_json_path',
    'get_app_details_path',
    'get_fnpack_details_path',
    'ensure_data_dir',
    # 数据存储
    'DataStore',
    'AppsStore',
    'FnpacksStore',
    'AppDetailsStore',
    'FnpackDetailsStore',
]
