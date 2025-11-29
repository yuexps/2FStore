#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import re
import urllib.request
from datetime import datetime
import base64

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入fetch_app_info函数
from fetch_app_info import fetch_app_info


def add_comment(issue_number, comment, github_token, repo_owner, repo_name):
    """
    添加评论到Issue/PR
    使用token认证方式
    """
    url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{issue_number}/comments'
    data = json.dumps({'body': comment}).encode('utf-8')
    
    try:
        req = urllib.request.Request(url, method='POST', data=data)
        req.add_header('Authorization', f'token {github_token}')
        req.add_header('Content-Type', 'application/json')
        
        response = urllib.request.urlopen(req)
        return response.getcode() == 201        
    except Exception as e:
        print(f"添加评论失败: {str(e)} （在公开仓库中这是正常的）")
    
    return False


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

def check_app_id_exists(app_id):
    """
    检查应用ID是否已存在（检查GitHub主分支上的apps.json）
    使用GitHub API并添加认证，从环境变量获取仓库信息
    """
    try:
        # 获取GitHub token和仓库信息
        github_token = os.environ.get('GITHUB_TOKEN')
        repo_owner = os.environ.get('REPO_OWNER', 'yuexps')
        repo_name = os.environ.get('REPO_NAME', '2FStore')
        
        # 使用GitHub API获取apps.json内容
        url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/contents/apps.json'
        req = urllib.request.Request(url)
        
        # 添加认证头
        if github_token:
            req.add_header('Authorization', f'token {github_token}')
            
        print(f"正在检查应用ID {app_id} 是否存在于主分支...")
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode('utf-8'))
        
        # 解码base64内容
        if data.get('content'):
            content = base64.b64decode(data['content']).decode('utf-8')
            apps_data = json.loads(content)
            exists = any(app.get('id') == app_id for app in apps_data.get('apps', []))
            print(f"应用ID {app_id} 检查结果: {'已存在' if exists else '不存在'}")
            return exists
    except Exception as e:
        print(f"检查应用ID存在性时出错: {str(e)}")
        # 如果无法获取或解析失败，认为ID不存在
        return False

def get_pull_request(pr_number, github_token, repo_owner, repo_name):
    """
    获取PR信息
    """
    url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}'
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'token {github_token}')
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read())
        return data
    except Exception as e:
        print(f"获取PR失败: {str(e)}")
        return None

def get_apps_json_from_pr(pr_number, github_token, repo_owner, repo_name):
    """
    从PR获取apps.json的内容
    """
    print(f"开始从PR #{pr_number} 获取apps.json内容...")
    
    try:
        print("尝试从PR的head分支直接获取apps.json...")
        # 先获取PR信息以获取head分支信息
        pr_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}'
        pr_req = urllib.request.Request(pr_url)
        pr_req.add_header('Authorization', f'token {github_token}')
        
        print(f"获取PR信息: {pr_url}")
        pr_response = urllib.request.urlopen(pr_req)
        pr_data = json.loads(pr_response.read().decode('utf-8'))
        
        # 获取head分支信息
        head_sha = pr_data.get('head', {}).get('sha')
        head_ref = pr_data.get('head', {}).get('ref')
        
        if not head_sha:
            raise Exception(f'无法获取PR的head分支SHA')
            
        print(f"PR head SHA: {head_sha}, 分支: {head_ref}")
        
        # 直接从head分支获取apps.json
        file_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/contents/apps.json?ref={head_sha}'
        file_req = urllib.request.Request(file_url)
        file_req.add_header('Authorization', f'token {github_token}')
        
        print(f"从head分支获取apps.json: {file_url}")
        file_response = urllib.request.urlopen(file_req)
        file_data = json.loads(file_response.read().decode('utf-8'))
        
        if file_data.get('content'):
            content = base64.b64decode(file_data['content']).decode('utf-8')
            print("成功从head分支获取并解码apps.json内容")
            return json.loads(content)
        else:
            raise Exception('PR分支中的apps.json文件内容为空')
            
    except Exception as e:
        error_msg = f"从PR #{pr_number} 获取apps.json失败: {str(e)}"
        print(error_msg)
        raise Exception(error_msg)

def get_base_apps_json(base_sha, github_token, repo_owner, repo_name):
    """
    从PR的基础分支获取apps.json内容
    """
    try:
        url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/contents/apps.json?ref={base_sha}'
        req = urllib.request.Request(url)
        req.add_header('Authorization', f'token {github_token}')
        
        response = urllib.request.urlopen(req)
        data = json.loads(response.read())
        
        if data.get('content'):
            content = base64.b64decode(data['content']).decode('utf-8')
            return json.loads(content)
    except Exception as e:
        print(f"获取基础分支apps.json失败: {str(e)}")
        # 如果文件不存在，返回空的应用列表
        return {'apps': []}
    
    return {'apps': []}

# 修改find_modified_apps函数
def find_modified_apps(pr_apps_data, base_apps_data):
    """
    找出PR中新增、修改或删除的应用
    返回(modified_apps, deleted_apps)
    """
    pr_apps = pr_apps_data.get('apps', [])
    base_apps = base_apps_data.get('apps', [])
    
    pr_app_ids = {app.get('id'): app for app in pr_apps}
    base_app_ids = {app.get('id'): app for app in base_apps}
    
    modified_apps = []
    deleted_apps = []
    
    # 检查新增或修改的应用
    for pr_app in pr_apps:
        pr_app_id = pr_app.get('id')
        base_app = base_app_ids.get(pr_app_id)
        
        if not base_app:
            # 新增应用
            modified_apps.append(pr_app)
        elif (base_app.get('name') != pr_app.get('name') or 
              base_app.get('repository') != pr_app.get('repository')):
            # 修改的应用
            modified_apps.append(pr_app)
    
    # 检查删除的应用
    for base_app in base_apps:
        base_app_id = base_app.get('id')
        if base_app_id not in pr_app_ids:
            # 删除的应用
            deleted_apps.append(base_app)
    
    return modified_apps, deleted_apps

# 修改run函数中的相关部分
def run():
    """
    GitHub Action入口函数
    """
    try:
        # 获取GitHub上下文
        github_token = os.environ.get('GITHUB_TOKEN')
        pull_request_number = os.environ.get('PR_NUMBER')
        repo_owner = os.environ.get('REPO_OWNER')
        repo_name = os.environ.get('REPO_NAME')
        
        if not github_token or not pull_request_number or not repo_owner or not repo_name:
            print('缺少必要的环境变量')
            sys.exit(1)
        
        # 获取PR信息
        pr = get_pull_request(pull_request_number, github_token, repo_owner, repo_name)
        if not pr:
            sys.exit(1)
        
        # 从PR中获取apps.json内容
        pr_apps_data = get_apps_json_from_pr(pull_request_number, github_token, repo_owner, repo_name)
        
        # 从基础分支获取apps.json内容
        base_apps_data = get_base_apps_json(pr['base']['sha'], github_token, repo_owner, repo_name)
        
        # 找出新增或修改的应用
        modified_apps, deleted_apps = find_modified_apps(pr_apps_data, base_apps_data)
        
        if len(modified_apps) == 0 and len(deleted_apps) == 0:
            print('PR中没有检测到新增、修改或删除的应用')
            sys.exit(1)
        
        # 处理删除的应用
        if len(deleted_apps) > 0:
            if len(deleted_apps) > 1 or len(modified_apps) > 0:
                print('PR中检测到多个应用的变更，请一次只提交一个应用的变更')
                sys.exit(1)
            
            # 获取被删除的应用
            deleted_app = deleted_apps[0]
            app_id = deleted_app.get('id')
            app_name = deleted_app.get('name')
            
            print(f'检测到应用删除: {app_name} ({app_id})')
            
            # 构造评论内容
            comment_body = "## 📋 应用删除通知\n\n"
            comment_body += f"该PR将删除应用: **{app_name}** (ID: `{app_id}`)\n\n"
            comment_body += "⚠️ **注意**: 此操作将从应用列表中永久移除该应用\n\n"
            
            # 添加评论到PR
            if add_comment(pull_request_number, comment_body, github_token, repo_owner, repo_name):
                print("✅ 应用删除通知已成功评论到PR")
            else:
                print("❌ 无法将应用删除通知评论到PR")
            
            # 输出变量供后续步骤使用
            github_output = os.environ.get('GITHUB_OUTPUT')
            if github_output:
                with open(github_output, 'a') as f:
                    f.write(f'app_id={app_id}\n')
                    f.write(f'app_name={app_name}\n')
                    f.write(f'action=delete\n')
            else:
                print(f'::set-output name=app_id::{app_id}')
                print(f'::set-output name=app_name::{app_name}')
                print(f'::set-output name=action::delete')
            
            return
        
        # 处理新增或修改的应用
        if len(modified_apps) > 1:
            print('PR中检测到多个应用的修改，请一次只提交一个应用的变更')
            sys.exit(1)
        
        # 获取第一个（也是唯一的）修改的应用
        app = modified_apps[0]
        
        # 从应用对象中提取信息
        app_id = app.get('id')
        app_name = app.get('name')
        repo_url = app.get('repository')
        
        # 验证应用信息
        validation_result = validate_app_info(app_id, app_name, repo_url)
        
        if not validation_result['is_valid']:
            print('应用信息验证失败:')
            for error in validation_result['errors']:
                print(f'- {error}')
            sys.exit(1)
        
        # 获取GitHub上的应用信息，方便开发者预览
        try:
            print(f'正在获取GitHub上的应用信息用于预览...')
            github_app_info = fetch_app_info(repo_url)
            
            print('\n=== GitHub应用信息预览 ===')
            print(f'应用名称: {app_name}')  # 使用开发者提供的名称
            print(f'应用描述: {github_app_info.get("description", "暂无描述")}')
            print(f'版本信息: {github_app_info.get("version", "未知")}')
            print(f'作者信息: {github_app_info.get("author", "未知")}')
            print(f'星标数量: {github_app_info.get("stars", 0)}')
            print(f'分类信息: {github_app_info.get("category", "未分类")}')
            
            # 检查下载链接
            download_url = github_app_info.get('downloadUrl')
            download_status = ""
            if not download_url or download_url in ['暂无下载链接', '获取失败']:
                print('❌ 警告：未能从GitHub仓库获取有效的下载链接')
                print('请确保：')
                print('1. 仓库中包含Release版本')
                print('2. Release中包含.fpk后缀的文件')
                print('3. Release不是草稿状态')
                download_status = "❌ 无效"
            else:
                print(f'✅ 下载链接检查通过: {download_url}')
                download_status = f"✅ 有效"
            
            print('========================\n')
            
            # 构造评论内容
            comment_body = "## 📋 应用信息预览\n\n"
            
            # 如果有图标，显示图标
            if github_app_info.get('iconUrl'):
                comment_body += f"<img src=\"{github_app_info['iconUrl']}\" width=\"64\" height=\"64\" alt=\"应用图标\" />\n\n"
            
            comment_body += "| 项目 | 信息 |\n"
            comment_body += "|------|------|\n"
            comment_body += f"| 应用ID | `{app_id}` |\n"
            comment_body += f"| 应用名称 | `{app_name}` |\n"
            comment_body += f"| 仓库URL | [{repo_url}]({repo_url}) |\n"
            comment_body += f"| 应用描述 | {github_app_info.get('description', '暂无描述')} |\n"
            comment_body += f"| 作者信息 | `{github_app_info.get('author', '')}` |\n"
            comment_body += f"| 星标数/分支数 | ⭐ {github_app_info.get('stars', 0)} / 🍴 {github_app_info.get('forks', 0)} |\n"
            comment_body += f"| 最后更新时间 | {github_app_info.get('lastUpdate', '未知')} |\n"
            comment_body += f"| 最新版本 | `{github_app_info.get('version', '未知')}` |\n"
            comment_body += f"| 下载链接 | [{download_url or '未知'}]({download_url or '未知'}) ({download_status}) |\n"
            comment_body += f"| 应用分类 | `{github_app_info.get('category', 'uncategorized')}` |\n\n"
            
            # 检查应用ID是否已存在
            if check_app_id_exists(app_id):
                comment_body += "⚠️ **注意**: 应用ID已存在，合并后将更新现有应用\n\n"
                print(f'注意: 应用ID {app_id} 已存在，将更新现有应用')
            else:
                comment_body += "✅ **验证通过**: 这是一个新应用，请等待合并！\n\n"
                print(f'验证通过: 新应用 {app_name} ({app_id})')
            
            # 添加评论到PR
            if add_comment(pull_request_number, comment_body, github_token, repo_owner, repo_name):
                print("✅ 应用信息已成功评论到PR")
            else:
                print("❌ 无法将应用信息评论到PR")
            
        except Exception as e:
            print(f'获取GitHub应用信息预览失败: {str(e)}')
            # 即使获取信息失败，也要添加评论告知用户
            error_comment = f"## 📋 应用信息预览\n\n❌ 无法获取应用信息，请检查仓库URL是否正确以及仓库是否符合要求。\n\n错误信息: {str(e)}"
            add_comment(pull_request_number, error_comment, github_token, repo_owner, repo_name)
        
        # 输出变量供后续步骤使用
        # 使用新的 $GITHUB_OUTPUT 环境文件方式
        github_output = os.environ.get('GITHUB_OUTPUT')
        if github_output:
            with open(github_output, 'a') as f:
                f.write(f'app_id={app_id}\n')
                f.write(f'app_name={app_name}\n')
                f.write(f'repo_url={repo_url}\n')
        else:
            # 为了向后兼容，保留旧的输出方式
            print(f'::set-output name=app_id::{app_id}')
            print(f'::set-output name=app_name::{app_name}')
            print(f'::set-output name=repo_url::{repo_url}')
        
    except Exception as error:
        print(f'验证PR失败: {str(error)}')
        sys.exit(1)

if __name__ == "__main__":
    args = sys.argv[1:]
    
    if len(args) == 3:
        # 直接验证提供的参数
        app_id, app_name, repo_url = args
        validation_result = validate_app_info(app_id, app_name, repo_url)
        
        if validation_result['is_valid']:
            print('验证通过')
            if check_app_id_exists(app_id):
                print(f'应用ID {app_id} 已存在')
        else:
            print('验证失败:')
            for error in validation_result['errors']:
                print(f'- {error}')
            sys.exit(1)
    else:
        # 作为GitHub Action运行
        run()