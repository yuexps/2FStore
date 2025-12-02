#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
处理应用提交 Issue
从 Issue 中提取应用信息并更新 apps.json
"""

import os
import sys
import json
import re
import subprocess

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import validate_app_info, GitHubAPI, get_apps_json_path
from fetch_app_info import fetch_app_info


def run_git_command(command):
    """
    运行 git 命令并返回输出
    """
    try:
        result = subprocess.run(command, shell=True, check=True, 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                               text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Git命令执行失败: {command}")
        print(f"错误输出: {e.stderr}")
        raise


def update_apps_json(app_id, app_name, repo_url):
    """
    更新 apps.json 文件内容
    """
    apps_json_path = get_apps_json_path()
    
    try:
        # 读取现有 apps.json 内容
        try:
            with open(apps_json_path, 'r', encoding='utf-8') as f:
                apps_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            apps_data = {'apps': []}
        
        if 'apps' not in apps_data or not isinstance(apps_data['apps'], list):
            apps_data['apps'] = []
        
        # 检查应用是否已存在
        existing_app_index = -1
        for i, app in enumerate(apps_data['apps']):
            if app.get('id') == app_id:
                existing_app_index = i
                break
        
        app_info = {
            'id': app_id,
            'name': app_name,
            'repository': repo_url
        }
        
        if existing_app_index >= 0:
            apps_data['apps'][existing_app_index] = app_info
            print(f"更新apps.json中的应用: {app_id}")
        else:
            apps_data['apps'].append(app_info)
            print(f"添加新应用到apps.json: {app_id}")
        
        with open(apps_json_path, 'w', encoding='utf-8') as f:
            json.dump(apps_data, f, ensure_ascii=False, indent=2)
        print('apps.json文件已更新')
        return True
        
    except Exception as error:
        print(f"更新apps.json失败: {str(error)}")
        raise error


def process_app_issue():
    """
    处理应用提交的 Issue
    """
    try:
        github_token = os.environ.get('GITHUB_TOKEN')
        issue_number = os.environ.get('ISSUE_NUMBER')
        repo_owner = os.environ.get('REPO_OWNER')
        repo_name = os.environ.get('REPO_NAME')
        
        if not github_token or not issue_number or not repo_owner or not repo_name:
            print('缺少必要的环境变量')
            sys.exit(1)
        
        # 创建 API 实例
        api = GitHubAPI(github_token)
        
        # 获取 Issue 信息
        issue_result = api.get_issue(repo_owner, repo_name, issue_number)
        if not issue_result['success']:
            print(f"获取Issue失败: {issue_result.get('error')}")
            sys.exit(1)
        issue = issue_result['data']
        
        # 检查 Issue 是否已处理
        if 'labels' in issue:
            for label in issue['labels']:
                if label.get('name') == 'processed':
                    print('Issue已处理，跳过')
                    return
        
        # 提取应用信息 - 匹配 Markdown 标题格式
        body = issue.get('body', '')
        app_id_match = re.search(r'### 应用唯一ID\s+([^\s]+)', body, re.IGNORECASE)
        app_name_match = re.search(r'### 应用名称\s+([^\n]+)', body, re.IGNORECASE)
        repo_url_match = re.search(r'### GitHub仓库URL\s+([^\n]+)', body, re.IGNORECASE)
        
        app_id = app_id_match.group(1).strip() if app_id_match else None
        app_name = app_name_match.group(1).strip() if app_name_match else None
        repo_url = repo_url_match.group(1).strip() if repo_url_match else None
        
        print('Extracted values:', {'app_id': app_id, 'app_name': app_name, 'repo_url': repo_url})
        
        if not app_id or not app_name or not repo_url:
            comment = '❌ **验证失败**：无法从Issue中提取完整的应用信息，请确保所有字段都已正确填写。'
            api.add_issue_comment(repo_owner, repo_name, issue_number, comment)
            api.add_issue_labels(repo_owner, repo_name, issue_number, ['invalid'])
            return
        
        # 验证应用信息
        validation_result = validate_app_info(app_id, app_name, repo_url)
        
        if not validation_result['is_valid']:
            error_list = '\n'.join([f'- {err}' for err in validation_result['errors']])
            comment = f'❌ **验证失败**：应用信息存在问题\n\n{error_list}'
            api.add_issue_comment(repo_owner, repo_name, issue_number, comment)
            api.add_issue_labels(repo_owner, repo_name, issue_number, ['invalid'])
            return
        
        # 增加对应用仓库的详细校验
        try:
            print(f'开始获取应用 {app_name} 的详细信息进行校验...')
            app_info = fetch_app_info(repo_url)
            
            # 检查必填项 - 下载链接
            if not app_info.get('downloadUrl') or app_info['downloadUrl'] in ['暂无下载链接', '获取失败']:
                comment = '❌ **验证失败**：下载链接是必填项，请确保GitHub仓库的Release中有.fpk文件。'
                api.add_issue_comment(repo_owner, repo_name, issue_number, comment)
                api.add_issue_labels(repo_owner, repo_name, issue_number, ['invalid'])
                return
            
            # 显示校验通过信息
            comment_body = "## 📋 应用信息检查结果\n\n"
            
            if app_info.get('iconUrl'):
                comment_body += f'<img src="{app_info["iconUrl"]}" width="64" height="64" alt="应用图标" />\n\n'
            
            comment_body += "| 项目 | 信息 |\n"
            comment_body += "|------|------|\n"
            comment_body += f"| 应用ID | `{app_id}` |\n"
            comment_body += f"| 应用名称 | `{app_name}` |\n"
            comment_body += f"| 仓库URL | [{repo_url}]({repo_url}) |\n"
            comment_body += f"| 应用描述 | {app_info.get('description', '暂无描述')} |\n"
            comment_body += f"| 作者信息 | `{app_info.get('author')}` |\n"
            comment_body += f"| 星标数/分支数 | ⭐ {app_info.get('stars', 0)} / 🍴 {app_info.get('forks', 0)} |\n"
            comment_body += f"| 最后更新时间 | {app_info.get('lastUpdate', '未知')} |\n"
            comment_body += f"| 最新版本 | `{app_info.get('version', '未知')}` |\n"
            comment_body += f"| 下载链接 | [{app_info.get('downloadUrl', '未知')}]({app_info.get('downloadUrl', '未知')}) |\n"
            comment_body += f"| 应用分类 | `{app_info.get('category', 'uncategorized')}` |\n\n"
            
            comment_body += "✅ **应用信息验证通过！**\n\n"
            
            update_apps_json(app_id, app_name, repo_url)
            
            comment_body += "✅ **apps.json已成功更新！**\n\n"
            comment_body += "您的应用已合并到仓库，稍后系统将自动更新应用详细信息并在前端展示。"
            
            api.add_issue_comment(repo_owner, repo_name, issue_number, comment_body)
            api.add_issue_labels(repo_owner, repo_name, issue_number, ['processed'])
            
        except Exception as meta_err:
            comment = f'❌ **处理应用信息失败：** {str(meta_err)}'
            api.add_issue_comment(repo_owner, repo_name, issue_number, comment)
            
    except Exception as error:
        print(f'处理应用Issue失败: {str(error)}')
        sys.exit(1)


if __name__ == "__main__":
    process_app_issue()