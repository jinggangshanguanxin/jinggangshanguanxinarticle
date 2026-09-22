#!/usr/bin/env python3
"""
使用 GitHub API 只下载 txt/md/docx 文件
避免下载整个仓库
"""

import os
import json
import subprocess
from pathlib import Path

REPO = os.environ.get('GITHUB_REPOSITORY', 'coolapijust/front-text')
TOKEN = os.environ.get('GITHUB_TOKEN', '')
BRANCH = os.environ.get('GITHUB_REF', 'refs/heads/main').replace('refs/heads/', '')
WORKSPACE = Path(os.environ.get('GITHUB_WORKSPACE', '.'))

ALLOWED_EXTENSIONS = {'.txt', '.md', '.docx'}
SKIP_DIRS = {'.git', '.github', 'node_modules', '__pycache__', 'reader', 'scripts'}

def run_cmd(cmd, capture=True):
    result = subprocess.run(cmd, shell=True, capture_output=capture, text=capture)
    if capture and result.returncode != 0:
        print(f'[Error] {cmd}: {result.stderr}')
    return result

def get_tree_filesRecursive(sha):
    """获取指定 commit/tree 下所有文件"""
    url = f'https://api.github.com/repos/{REPO}/git/trees/{sha}?recursive=1'
    headers = {'Authorization': f'token {TOKEN}', 'Accept': 'application/vnd.github.v3+json'}
    
    import urllib.request
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        return data.get('tree', [])
    return []

def download_file(path, sha):
    """下载单个文件"""
    url = f'https://api.github.com/repos/{REPO}/git/blobs/{sha}'
    headers = {'Authorization': f'token {TOKEN}', 'Accept': 'application/vnd.github.v3.raw'}
    
    import urllib.request
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        content = resp.read()
        
        dest = WORKSPACE / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, 'wb') as f:
            f.write(content)
        print(f'[Download] {path}')

def main():
    print(f'[Download] 仓库: {REPO}, 分支: {BRANCH}')
    
    # 获取最新 commit
    result = run_cmd(f'git ls-remote https://github.com/{REPO}.git {BRANCH}')
    if result.returncode != 0:
        print('[Error] 无法获取仓库信息')
        return
    
    commit_sha = result.stdout.split()[0]
    print(f'[Download] Commit: {commit_sha}')
    
    # 获取文件列表
    files = get_tree_filesRecursive(commit_sha)
    
    downloaded = 0
    skipped = 0
    
    for item in files:
        if item['type'] != 'blob':
            continue
        
        path = item['path']
        parts = path.split('/')
        
        # 跳过目录
        if any(skip in parts for skip in SKIP_DIRS):
            continue
        
        # 只下载允许的类型
        ext = Path(path).suffix.lower()
        if ext in ALLOWED_EXTENSIONS:
            download_file(path, item['sha'])
            downloaded += 1
        else:
            skipped += 1
    
    print(f'[Download] 完成: {downloaded} 文件, 跳过 {skipped} 个不支持的类型')

if __name__ == '__main__':
    main()
