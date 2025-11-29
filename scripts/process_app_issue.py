#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import re
import urllib.request
import subprocess
from datetime import datetime
import base64

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fetch_app_info import fetch_app_info

def validate_app_info(app_id, app_name, repo_url):
    """
    验证应用信息
    """
    errors = []
    
    # 验证应用ID
    if not app_id or not isinstance(app_id, str) or app_id.strip() == '':
        errors.append('应用ID不能为空')
    elif not re.match(r'^[a-z0-9-]+$', app_id):
        errors.append('应用ID只能包含小写字母、数字和连字符')
    
    # 验证应用名称
    if not app_name or not isinstance(app_name, str) or app_name.strip() == '':
        errors.append('应用名称不能为空')
    elif len(app_name) > 100:
        errors.append('应用名称长度不能超过100个字符')
    
    # 验证GitHub仓库URL
    if not repo_url or not isinstance(repo_url, str) or repo_url.strip() == '':
        errors.append('GitHub仓库URL不能为空')
    elif not re.match(r'^https://github\.com/[^/]+/[^/]+$', repo_url):
        errors.append('请提供有效的GitHub仓库URL')
    
    return {
        'is_valid': len(errors) == 0,
        'errors': errors
    }

def get_issue_body(issue_number, github_token, repo_owner, repo_name):
    """
    获取Issue内容
    """
    url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{issue_number}'
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'token {github_token}')
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read())
        return data
    except Exception as e:
        print(f"获取Issue失败: {str(e)}")
        return None

def add_comment(issue_number, comment, github_token, repo_owner, repo_name):
    """
    添加评论到Issue
    """
    url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{issue_number}/comments'
    req = urllib.request.Request(url, method='POST')
    req.add_header('Authorization', f'token {github_token}')
    req.add_header('Content-Type', 'application/json')
    
    data = {
        'body': comment
    }
    
    try:
        req.data = json.dumps(data).encode('utf-8')
        response = urllib.request.urlopen(req)
        return response.getcode() == 201
    except Exception as e:
        print(f"添加评论失败: {str(e)}")
        return False

def add_labels(issue_number, labels, github_token, repo_owner, repo_name):
    """
    添加标签到Issue
    """
    url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{issue_number}/labels'
    req = urllib.request.Request(url, method='POST')
    req.add_header('Authorization', f'token {github_token}')
    req.add_header('Content-Type', 'application/json')
    
    data = {
        'labels': labels
    }
    
    try:
        req.data = json.dumps(data).encode('utf-8')
        response = urllib.request.urlopen(req)
        return response.getcode() == 200
    except Exception as e:
        print(f"添加标签失败: {str(e)}")
        return False

def run_git_command(command):
    """
    运行git命令并返回输出
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
    更新apps.json文件内容
    """
    # 获取apps.json文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    apps_json_path = os.path.join(script_dir, '..', 'apps.json')
    
    try:
        # 读取现有apps.json内容
        try:
            with open(apps_json_path, 'r', encoding='utf-8') as f:
                apps_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # 如果文件不存在或无效，创建新的数据结构
            apps_data = {'apps': []}
        
        # 确保apps字段存在
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
            # 更新现有应用
            apps_data['apps'][existing_app_index] = app_info
            print(f"更新apps.json中的应用: {app_id}")
        else:
            # 添加新应用
            apps_data['apps'].append(app_info)
            print(f"添加新应用到apps.json: {app_id}")
        
        # 保存更新后的apps.json
        with open(apps_json_path, 'w', encoding='utf-8') as f:
            json.dump(apps_data, f, ensure_ascii=False, indent=2)
        print('apps.json文件已更新')
        return True
        
    except Exception as error:
        print(f"更新apps.json失败: {str(error)}")
        raise error

def process_app_issue():
    """
    处理应用提交的Issue
    """
    try:
        github_token = os.environ.get('GITHUB_TOKEN')
        issue_number = os.environ.get('ISSUE_NUMBER')
        repo_owner = os.environ.get('REPO_OWNER')
        repo_name = os.environ.get('REPO_NAME')
        
        if not github_token or not issue_number or not repo_owner or not repo_name:
            print('缺少必要的环境变量')
            sys.exit(1)
        
        # 获取Issue信息
        issue = get_issue_body(issue_number, github_token, repo_owner, repo_name)
        if not issue:
            sys.exit(1)
        
        # 检查Issue是否已处理
        if 'labels' in issue:
            for label in issue['labels']:
                if label.get('name') == 'processed':
                    print('Issue已处理，跳过')
                    return
        
        # 提取应用信息 - 匹配Markdown标题格式
        app_id_match = re.search(r'### 应用唯一ID\s+([^\s]+)', issue.get('body', ''), re.IGNORECASE)
        app_name_match = re.search(r'### 应用名称\s+([^\n]+)', issue.get('body', ''), re.IGNORECASE)
        repo_url_match = re.search(r'### GitHub仓库URL\s+([^\n]+)', issue.get('body', ''), re.IGNORECASE)
        
        app_id = app_id_match.group(1).strip() if app_id_match else None
        app_name = app_name_match.group(1).strip() if app_name_match else None
        repo_url = repo_url_match.group(1).strip() if repo_url_match else None
        
        # 添加调试输出以便于排查问题
        print('Extracted values:', {'app_id': app_id, 'app_name': app_name, 'repo_url': repo_url})
        
        if not app_id or not app_name or not repo_url:
            comment = '❌ **验证失败**：无法从Issue中提取完整的应用信息，请确保所有字段都已正确填写。'
            add_comment(issue_number, comment, github_token, repo_owner, repo_name)
            add_labels(issue_number, ['invalid'], github_token, repo_owner, repo_name)
            return
        
        # 验证应用信息
        validation_result = validate_app_info(app_id, app_name, repo_url)
        
        if not validation_result['is_valid']:
            error_list = '\n'.join([f'- {err}' for err in validation_result['errors']])
            comment = f'❌ **验证失败**：应用信息存在问题\n\n{error_list}'
            add_comment(issue_number, comment, github_token, repo_owner, repo_name)
            add_labels(issue_number, ['invalid'], github_token, repo_owner, repo_name)
            return
        
        # 增加对应用仓库的详细校验
        try:
            print(f'开始获取应用 {app_name} 的详细信息进行校验...')
            app_info = fetch_app_info(repo_url)
            
            # 检查必填项 - 下载链接
            if not app_info.get('downloadUrl') or app_info['downloadUrl'] in ['暂无下载链接', '获取失败']:
                comment = '❌ **验证失败**：下载链接是必填项，请确保GitHub仓库的Release中有.fpk文件。'
                add_comment(issue_number, comment, github_token, repo_owner, repo_name)
                add_labels(issue_number, ['invalid'], github_token, repo_owner, repo_name)
                return
            
            # 显示校验通过信息
            comment_body = "## 📋 应用信息检查结果\n\n"
            
            # 如果有图标，显示图标
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
            
            # 移更新文件内容
            update_apps_json(app_id, app_name, repo_url)
            
            comment_body += "✅ **apps.json已成功更新！**\n\n"
            comment_body += "您的应用已合并到仓库，稍后系统将自动更新应用详细信息并在前端展示。"
            
            add_comment(issue_number, comment_body, github_token, repo_owner, repo_name)
            add_labels(issue_number, ['processed'], github_token, repo_owner, repo_name)
            
        except Exception as meta_err:
            comment = f'❌ **处理应用信息失败：** {str(meta_err)}'
            add_comment(issue_number, comment, github_token, repo_owner, repo_name)
            
    except Exception as error:
        print(f'处理应用Issue失败: {str(error)}')
        sys.exit(1)

if __name__ == "__main__":
    process_app_issue()