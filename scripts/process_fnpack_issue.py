#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
处理 FnPack 应用提交 Issue
从 Issue 中提取仓库信息并更新 fnpacks.json
"""

import os
import sys
import json
import re

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import GitHubAPI, FnpacksStore, parse_github_url, get_fnpacks_json_path
from fetch_fnpack_info import fetch_fnpack_info, update_apps_from_fnpack


def update_fnpacks_json(owner, repo_url):
    """
    更新 fnpacks.json 文件内容
    """
    fnpacks_json_path = get_fnpacks_json_path()
    
    try:
        # 读取现有 fnpacks.json 内容
        try:
            with open(fnpacks_json_path, 'r', encoding='utf-8') as f:
                fnpacks_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            fnpacks_data = {'fnpacks': []}
        
        if 'fnpacks' not in fnpacks_data or not isinstance(fnpacks_data['fnpacks'], list):
            fnpacks_data['fnpacks'] = []
        
        # 检查仓库是否已存在
        existing_index = -1
        for i, fnpack in enumerate(fnpacks_data['fnpacks']):
            if fnpack.get('repository') == repo_url:
                existing_index = i
                break
        
        fnpack_info = {
            'id': owner,
            'repository': repo_url
        }
        
        if existing_index >= 0:
            fnpacks_data['fnpacks'][existing_index] = fnpack_info
            print(f"更新fnpacks.json中的仓库: {repo_url}")
        else:
            fnpacks_data['fnpacks'].append(fnpack_info)
            print(f"添加新仓库到fnpacks.json: {repo_url}")
        
        with open(fnpacks_json_path, 'w', encoding='utf-8') as f:
            json.dump(fnpacks_data, f, ensure_ascii=False, indent=2)
        print('fnpacks.json文件已更新')
        return True
        
    except Exception as error:
        print(f"更新fnpacks.json失败: {str(error)}")
        raise error


def process_fnpack_issue():
    """
    处理 FnPack 应用提交的 Issue
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
        
        # 提取仓库信息 - 匹配 Markdown 标题格式
        body = issue.get('body', '')
        repo_url_match = re.search(r'### FnDepot 仓库URL\s+([^\n]+)', body, re.IGNORECASE)
        
        repo_url = repo_url_match.group(1).strip() if repo_url_match else None
        
        print('Extracted values:', {'repo_url': repo_url})
        
        if not repo_url:
            comment = '❌ **验证失败**：无法从Issue中提取仓库URL，请确保已正确填写。'
            api.add_issue_comment(repo_owner, repo_name, issue_number, comment)
            api.add_issue_labels(repo_owner, repo_name, issue_number, ['invalid'])
            return
        
        # 验证仓库URL格式
        owner, repo = parse_github_url(repo_url)
        if not owner or not repo:
            comment = '❌ **验证失败**：无效的GitHub仓库URL格式。'
            api.add_issue_comment(repo_owner, repo_name, issue_number, comment)
            api.add_issue_labels(repo_owner, repo_name, issue_number, ['invalid'])
            return
        
        # 获取并验证 fnpack.json
        try:
            print(f'开始从 {repo_url} 获取 fnpack.json 信息...')
            app_info = fetch_fnpack_info(repo_url, None, github_token)
            
            if not app_info:
                comment = '❌ **验证失败**：无法从仓库获取有效的 fnpack.json 文件，请确保：\n' \
                         '- 仓库根目录存在 fnpack.json 文件\n' \
                         '- fnpack.json 格式正确'
                api.add_issue_comment(repo_owner, repo_name, issue_number, comment)
                api.add_issue_labels(repo_owner, repo_name, issue_number, ['invalid'])
                return
            
            # 构建验证结果评论
            comment_body = "## 📋 FnPack 仓库检查结果\n\n"
            
            # 处理多个应用
            if isinstance(app_info, dict) and 'name' in app_info:
                # 单个应用信息
                apps_to_show = {'main': app_info}
            else:
                # 多个应用
                apps_to_show = app_info
            
            app_count = len(apps_to_show) if isinstance(apps_to_show, dict) else 1
            comment_body += f"**仓库**: [{repo_url}]({repo_url})\n"
            comment_body += f"**应用数量**: {app_count}\n\n"
            
            # 显示每个应用的信息
            for key, info in apps_to_show.items():
                if not isinstance(info, dict):
                    continue
                    
                comment_body += f"### 📦 {info.get('name', key)}\n\n"
                
                if info.get('iconUrl'):
                    comment_body += f'<img src="{info["iconUrl"]}" width="64" height="64" alt="应用图标" />\n\n'
                
                comment_body += "| 项目 | 信息 |\n"
                comment_body += "|------|------|\n"
                comment_body += f"| 应用Key | `{key}` |\n"
                comment_body += f"| 应用名称 | `{info.get('name', '未知')}` |\n"
                comment_body += f"| 版本 | `{info.get('version', '未知')}` |\n"
                comment_body += f"| 作者 | `{info.get('author', '未知')}` |\n"
                comment_body += f"| 分类 | `{info.get('category', 'uncategorized')}` |\n"
                
                if info.get('downloadUrl'):
                    comment_body += f"| 下载链接 | [下载]({info.get('downloadUrl')}) |\n"
                
                # 检查描述是否包含HTML标签
                description = info.get('description', '暂无描述')
                has_html = bool(re.search(r'<[^>]+>', description)) if description else False
                
                if has_html:
                    # 包含HTML的描述单独显示
                    comment_body += "\n**📝 应用描述**\n\n"
                    comment_body += f"<blockquote>\n{description}\n</blockquote>\n\n"
                else:
                    # 纯文本描述放在表格中
                    comment_body += f"| 描述 | {description} |\n\n"
            
            # 更新 fnpacks.json
            update_fnpacks_json(owner, repo_url)
            
            comment_body += "---\n\n"
            comment_body += "✅ **fnpacks.json 已成功更新！**\n\n"
            comment_body += "您的仓库已添加到列表，稍后系统将自动更新应用详细信息并在前端展示。"
            
            api.add_issue_comment(repo_owner, repo_name, issue_number, comment_body)
            api.add_issue_labels(repo_owner, repo_name, issue_number, ['processed'])
            
        except Exception as meta_err:
            comment = f'❌ **处理仓库信息失败：** {str(meta_err)}'
            api.add_issue_comment(repo_owner, repo_name, issue_number, comment)
            api.add_issue_labels(repo_owner, repo_name, issue_number, ['invalid'])
            
    except Exception as error:
        print(f'处理FnPack Issue失败: {str(error)}')
        sys.exit(1)


if __name__ == "__main__":
    process_fnpack_issue()
