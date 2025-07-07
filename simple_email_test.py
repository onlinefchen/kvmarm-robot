#!/usr/bin/env python3
"""
简化的邮件解析测试，不依赖外部模块
"""
import os
import sys
import subprocess
import json
from datetime import datetime, timedelta

def test_git_repo():
    """测试git仓库状态"""
    print("🔍 检查Git仓库...")
    
    repo_path = "kvmarm/git/0.git"
    
    if not os.path.exists(repo_path):
        print("📥 下载仓库...")
        cmd = ["git", "clone", "--mirror", "https://lore.kernel.org/kvmarm/0", repo_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ 下载失败: {result.stderr}")
            return False
    else:
        print("🔄 更新仓库...")
        cmd = ["git", "-C", repo_path, "remote", "update"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ 更新失败: {result.stderr}")
            return False
    
    print("✅ 仓库准备就绪")
    return True

def get_commits_in_range(repo_path, since_date, until_date):
    """获取时间范围内的commits"""
    print(f"📅 获取 {since_date} 到 {until_date} 的commits...")
    
    cmd = [
        "git", "-C", repo_path, "rev-list",
        "--since", since_date.strftime("%Y-%m-%d"),
        "--until", until_date.strftime("%Y-%m-%d"),
        "refs/heads/master"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ 获取commits失败: {result.stderr}")
        return []
    
    commits = [line.strip() for line in result.stdout.split('\n') if line.strip()]
    print(f"🔍 找到 {len(commits)} 个commits")
    return commits

def analyze_commit(repo_path, commit_sha):
    """分析单个commit"""
    # 获取commit信息
    cmd = ["git", "-C", repo_path, "show", "--format=fuller", "--name-only", commit_sha]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        return {"status": "error", "error": f"无法获取commit信息: {result.stderr}"}
    
    info = {"status": "ok", "sha": commit_sha, "has_m_file": False}
    
    lines = result.stdout.split('\n')
    
    # 解析commit信息
    for line in lines:
        if line.startswith('Author:'):
            info['author'] = line[7:].strip()
        elif line.startswith('AuthorDate:'):
            info['date'] = line[11:].strip()
        elif line.startswith('    '):
            if 'subject' not in info:
                info['subject'] = line.strip()
        elif line.strip() == 'm':
            info['has_m_file'] = True
    
    # 如果没有'm'文件，这不是邮件commit
    if not info['has_m_file']:
        return {"status": "no_m_file", "info": info}
    
    # 获取'm'文件内容
    cmd = ["git", "-C", repo_path, "show", f"{commit_sha}:m"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        return {"status": "m_file_error", "error": result.stderr, "info": info}
    
    content = result.stdout
    info['content_size'] = len(content)
    
    # 检查邮件头
    headers = {
        'from': 'From:' in content,
        'subject': 'Subject:' in content,
        'message_id': 'Message-ID:' in content or 'Message-Id:' in content,
        'date': 'Date:' in content
    }
    info['headers'] = headers
    
    # 提取实际的邮件字段
    lines = content.split('\n')
    for line in lines:
        if line.startswith('From:'):
            info['email_from'] = line[5:].strip()
        elif line.startswith('Subject:'):
            info['email_subject'] = line[8:].strip()
        elif line.startswith('Message-ID:') or line.startswith('Message-Id:'):
            info['email_message_id'] = line.split(':', 1)[1].strip()
    
    # 判断是否是有效邮件
    missing_headers = [k for k, v in headers.items() if not v]
    if missing_headers:
        info['missing_headers'] = missing_headers
        return {"status": "invalid_email", "info": info}
    
    # 检查字段是否为空
    empty_fields = []
    if not info.get('email_from', '').strip():
        empty_fields.append('from')
    if not info.get('email_subject', '').strip():
        empty_fields.append('subject')
    if not info.get('email_message_id', '').strip():
        empty_fields.append('message_id')
    
    if empty_fields:
        info['empty_fields'] = empty_fields
        return {"status": "empty_fields", "info": info}
    
    # 检查subject长度
    subject = info.get('email_subject', '')
    if len(subject.strip()) < 3:
        info['subject_too_short'] = True
        return {"status": "subject_too_short", "info": info}
    
    return {"status": "valid", "info": info}

def main():
    """主函数"""
    print("🚀 开始邮件解析测试")
    print("=" * 60)
    
    # 确保仓库存在
    if not test_git_repo():
        return
    
    repo_path = "kvmarm/git/0.git"
    
    # 设置时间范围（过去10天）
    end_date = datetime.now()
    start_date = end_date - timedelta(days=10)
    
    # 获取commits
    commits = get_commits_in_range(repo_path, start_date, end_date)
    
    if not commits:
        print("❌ 没有找到commits")
        return
    
    # 分析每个commit
    print(f"\n🔍 开始分析 {len(commits)} 个commits...")
    
    results = {
        "valid": [],
        "no_m_file": [],
        "invalid_email": [],
        "empty_fields": [],
        "subject_too_short": [],
        "m_file_error": [],
        "error": []
    }
    
    for i, commit_sha in enumerate(commits):
        result = analyze_commit(repo_path, commit_sha)
        status = result["status"]
        results[status].append(result)
        
        # 显示进度
        if (i + 1) % 20 == 0:
            print(f"   📊 已处理: {i + 1}/{len(commits)} commits")
    
    # 输出统计结果
    print(f"\n📊 分析结果:")
    print(f"   ✅ 有效邮件: {len(results['valid'])}")
    print(f"   📁 无'm'文件: {len(results['no_m_file'])}")
    print(f"   📧 无效邮件格式: {len(results['invalid_email'])}")
    print(f"   📝 字段为空: {len(results['empty_fields'])}")
    print(f"   📏 主题太短: {len(results['subject_too_short'])}")
    print(f"   💥 文件错误: {len(results['m_file_error'])}")
    print(f"   ❌ 其他错误: {len(results['error'])}")
    
    total_failed = len(commits) - len(results['valid'])
    if total_failed > 0:
        print(f"\n⚠️  失败率: {total_failed}/{len(commits)} ({total_failed/len(commits)*100:.1f}%)")
        
        # 详细分析失败原因
        print(f"\n🔍 失败详情分析:")
        
        for category, items in results.items():
            if category != "valid" and items:
                print(f"\n📋 {category} ({len(items)} 个):")
                for item in items[:3]:  # 只显示前3个
                    info = item.get('info', {})
                    print(f"   {info.get('sha', 'unknown')[:8]}: {info.get('subject', 'No subject')[:60]}")
                    if 'missing_headers' in info:
                        print(f"      缺少头部: {info['missing_headers']}")
                    if 'empty_fields' in info:
                        print(f"      空字段: {info['empty_fields']}")
                    if item.get('error'):
                        print(f"      错误: {item['error']}")
                
                if len(items) > 3:
                    print(f"   ... 还有 {len(items) - 3} 个")
    else:
        print(f"\n🎉 太棒了！所有 {len(commits)} 个commits都成功解析！")
    
    # 保存详细结果
    with open('email_analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n📄 详细结果已保存到: email_analysis_results.json")

if __name__ == "__main__":
    main()