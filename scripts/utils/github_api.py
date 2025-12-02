#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub API 封装模块
统一处理 GitHub API 调用、认证、重试等逻辑
"""

import json
import os
import time
import urllib.request
import urllib.error
import base64


class GitHubAPI:
    """GitHub API 封装类"""
    
    def __init__(self, token=None):
        """
        初始化 GitHub API 客户端
        
        参数:
        - token: GitHub API token，如果不提供则从环境变量获取
        """
        self.token = token or os.environ.get('GITHUB_TOKEN') or os.environ.get('PERSONAL_TOKEN')
        self.base_url = 'https://api.github.com'
        self.user_agent = '2FStore-App/1.0'
    
    def _make_request(self, url, method='GET', data=None, max_retries=3, timeout=10):
        """
        发起 HTTP 请求
        
        参数:
        - url: 请求 URL
        - method: 请求方法
        - data: 请求数据（用于 POST/PUT）
        - max_retries: 最大重试次数
        - timeout: 超时时间
        """
        req = urllib.request.Request(url, method=method)
        req.add_header('User-Agent', self.user_agent)
        req.add_header('Accept', 'application/vnd.github.v3+json')
        
        if self.token:
            req.add_header('Authorization', f'token {self.token}')
        
        if data:
            req.add_header('Content-Type', 'application/json')
            req.data = json.dumps(data).encode('utf-8')
        
        for attempt in range(max_retries):
            try:
                response = urllib.request.urlopen(req, timeout=timeout)
                return {
                    'status': response.getcode(),
                    'data': json.loads(response.read().decode('utf-8')),
                    'success': True
                }
            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8') if e.fp else ''
                if attempt < max_retries - 1 and e.code in [502, 503, 504]:
                    wait_time = 2 ** attempt
                    print(f"HTTP {e.code} 错误，{wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    return {
                        'status': e.code,
                        'error': str(e),
                        'error_body': error_body,
                        'success': False
                    }
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"请求错误 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                    print(f"{wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    return {
                        'status': 0,
                        'error': str(e),
                        'success': False
                    }
        
        return {'status': 0, 'error': '所有重试均失败', 'success': False}
    
    def get(self, endpoint, **kwargs):
        """GET 请求"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        return self._make_request(url, method='GET', **kwargs)
    
    def post(self, endpoint, data=None, **kwargs):
        """POST 请求"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        return self._make_request(url, method='POST', data=data, **kwargs)
    
    def get_repo(self, owner, repo):
        """获取仓库信息"""
        return self.get(f'repos/{owner}/{repo}')
    
    def get_file_content(self, owner, repo, path, ref=None):
        """
        获取文件内容
        
        返回解码后的文件内容字符串
        """
        endpoint = f'repos/{owner}/{repo}/contents/{path}'
        if ref:
            endpoint += f'?ref={ref}'
        
        result = self.get(endpoint)
        if result['success'] and 'content' in result['data']:
            return base64.b64decode(result['data']['content']).decode('utf-8')
        return None
    
    def get_releases(self, owner, repo):
        """获取仓库的 Release 列表"""
        return self.get(f'repos/{owner}/{repo}/releases')
    
    def get_latest_release(self, owner, repo):
        """获取最新 Release"""
        result = self.get_releases(owner, repo)
        if result['success'] and result['data']:
            return result['data'][0]
        return None
    
    def get_readme(self, owner, repo):
        """获取 README 内容"""
        result = self.get(f'repos/{owner}/{repo}/readme')
        if result['success'] and 'content' in result['data']:
            return base64.b64decode(result['data']['content']).decode('utf-8')
        return None
    
    def add_issue_comment(self, owner, repo, issue_number, body):
        """
        添加 Issue/PR 评论
        
        返回是否成功
        """
        result = self.post(f'repos/{owner}/{repo}/issues/{issue_number}/comments', data={'body': body})
        return result['success'] and result['status'] == 201
    
    def add_issue_labels(self, owner, repo, issue_number, labels):
        """
        添加 Issue/PR 标签
        
        返回是否成功
        """
        result = self.post(f'repos/{owner}/{repo}/issues/{issue_number}/labels', data={'labels': labels})
        return result['success']
    
    def get_issue(self, owner, repo, issue_number):
        """获取 Issue 信息"""
        return self.get(f'repos/{owner}/{repo}/issues/{issue_number}')
    
    def get_pull_request(self, owner, repo, pr_number):
        """获取 PR 信息"""
        return self.get(f'repos/{owner}/{repo}/pulls/{pr_number}')


def fetch_github_api(url, github_token=None, max_retries=3, silent=False):
    """
    兼容旧代码的 GitHub API 调用函数
    
    参数:
    - url: 完整的 GitHub API URL
    - github_token: GitHub API token
    - max_retries: 最大重试次数
    - silent: 是否静默模式（不打印错误日志，用于探测性请求）
    
    返回:
    - 成功时返回 JSON 数据
    - 失败时返回 None
    """
    req = urllib.request.Request(url)
    req.add_header('User-Agent', '2FStore-App/1.0')
    
    if github_token:
        req.add_header('Authorization', f'token {github_token}')
    
    for attempt in range(max_retries):
        try:
            response = urllib.request.urlopen(req, timeout=10)
            data = response.read()
            return json.loads(data)
        except urllib.error.HTTPError as e:
            # 404 错误不重试（资源不存在是确定的）
            if e.code == 404:
                return None
            # 其他 HTTP 错误
            if attempt < max_retries - 1 and e.code in [502, 503, 504, 429]:
                wait_time = 2 ** attempt
                if not silent:
                    print(f"错误 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                    print(f"{wait_time}秒后重试...")
                time.sleep(wait_time)
            else:
                if not silent:
                    print(f"Error fetching {url} (所有尝试均失败): {str(e)}")
                return None
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                if not silent:
                    print(f"错误 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                    print(f"{wait_time}秒后重试...")
                time.sleep(wait_time)
            else:
                if not silent:
                    print(f"Error fetching {url} (所有尝试均失败): {str(e)}")
                return None
    
    return None
