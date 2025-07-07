#!/usr/bin/env python3
"""
调试邮件解析失败的脚本
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from git import Repo

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from repository import RepositoryManager
from email_parser import EmailParser
import logging

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_failed_commits():
    """分析解析失败的commits"""
    print("🔍 分析邮件解析失败的原因...")
    print("=" * 60)
    
    # 初始化仓库管理器
    repo_manager = RepositoryManager()
    repo_path = repo_manager.ensure_repository_updated()
    
    # 设置时间范围（与GitHub Actions一致）
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    print(f"📅 时间范围: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
    
    # 获取commits
    repo = Repo(str(repo_path))
    commits = list(repo.iter_commits(
        'refs/heads/master',
        since=start_date.isoformat(),
        until=end_date.isoformat()
    ))
    
    print(f"📊 找到 {len(commits)} 个commits")
    
    # 失败的commit SHA列表（从错误信息中提取）
    failed_shas = [
        'd7dfe3f6', '700258b2', 'cf4cf19c', '968dba96', 
        'defec975'  # 还有9个，我们会找出所有的
    ]
    
    # 解析所有commits，找出失败的
    parser = EmailParser()
    failed_commits = []
    success_count = 0
    
    for i, commit in enumerate(commits):
        try:
            # 尝试解析
            email_node = parser.parse_commit(commit)
            if email_node:
                success_count += 1
            else:
                failed_commits.append(commit)
        except Exception as e:
            failed_commits.append(commit)
            logger.debug(f"解析失败 {commit.hexsha[:8]}: {str(e)}")
    
    print(f"\n📊 解析结果:")
    print(f"   ✅ 成功: {success_count}")
    print(f"   ❌ 失败: {len(failed_commits)}")
    
    # 详细分析失败的commits
    print(f"\n🔍 详细分析失败的commits:")
    print("-" * 60)
    
    for i, commit in enumerate(failed_commits[:10]):  # 分析前10个
        print(f"\n{i+1}. Commit: {commit.hexsha[:8]}")
        print(f"   作者: {commit.author.name} <{commit.author.email}>")
        print(f"   日期: {datetime.fromtimestamp(commit.committed_date)}")
        print(f"   消息: {commit.summary[:60]}...")
        
        # 检查commit内容
        try:
            # 获取树对象
            tree = commit.tree
            
            # 检查是否有'm'文件
            if 'm' in tree:
                m_file = tree['m']
                content = m_file.data_stream.read()
                
                # 分析内容
                print(f"   文件大小: {len(content)} bytes")
                
                # 检查内容类型
                if len(content) < 100:
                    print(f"   ⚠️  文件太小，可能不是邮件")
                    print(f"   内容预览: {content[:50]}...")
                
                # 检查是否是邮件格式
                content_str = content.decode('utf-8', errors='ignore')
                if 'From:' not in content_str and 'Subject:' not in content_str:
                    print(f"   ⚠️  缺少邮件标准头部（From/Subject）")
                
                # 检查编码问题
                try:
                    content.decode('utf-8')
                except UnicodeDecodeError as e:
                    print(f"   ⚠️  UTF-8解码错误: {e}")
                    
            else:
                print(f"   ❌ 没有找到'm'文件")
                print(f"   树中的文件: {list(tree.trees)[:5]}...")
                
        except Exception as e:
            print(f"   ❌ 分析失败: {str(e)}")
    
    # 分析失败模式
    print(f"\n📊 失败模式分析:")
    
    # 检查是否是特定类型的commits
    merge_commits = [c for c in failed_commits if len(c.parents) > 1]
    empty_commits = [c for c in failed_commits if not any(c.stats.files.keys())]
    
    print(f"   🔀 合并commits: {len(merge_commits)}")
    print(f"   📭 空commits: {len(empty_commits)}")
    
    # 检查特定路径
    non_m_commits = []
    for commit in failed_commits:
        if 'm' not in commit.stats.files:
            non_m_commits.append(commit)
    
    print(f"   📁 不包含'm'文件的commits: {len(non_m_commits)}")
    
    # 输出建议
    print(f"\n💡 建议:")
    print("   1. 这些commits可能不是邮件commits，而是仓库维护commits")
    print("   2. 可以在email_parser.py中添加更好的错误处理")
    print("   3. 可以过滤掉非邮件commits（如合并commits）")

def test_specific_commit(sha):
    """测试特定的commit"""
    print(f"\n🔍 详细测试commit: {sha}")
    print("-" * 60)
    
    repo_manager = RepositoryManager()
    repo_path = repo_manager.ensure_repository_updated()
    repo = Repo(str(repo_path))
    
    try:
        commit = repo.commit(sha)
        print(f"SHA: {commit.hexsha}")
        print(f"作者: {commit.author}")
        print(f"日期: {datetime.fromtimestamp(commit.committed_date)}")
        print(f"消息: {commit.summary}")
        
        # 检查文件
        print(f"\n文件变更:")
        for file_path in commit.stats.files:
            print(f"  - {file_path}")
        
        # 尝试获取'm'文件内容
        if 'm' in commit.tree:
            m_content = commit.tree['m'].data_stream.read()
            print(f"\n'm'文件内容 (前500字符):")
            print("-" * 40)
            print(m_content[:500].decode('utf-8', errors='replace'))
            print("-" * 40)
        else:
            print("\n❌ 此commit没有'm'文件")
            
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    # 运行分析
    analyze_failed_commits()
    
    # 测试特定的失败commit
    # test_specific_commit('d7dfe3f6')