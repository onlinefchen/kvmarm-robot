#!/usr/bin/env python3
"""
测试失败的commits，找出真正的原因
"""
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from repository import RepositoryManager
from email_parser import EmailParser
from git import Repo

def test_failed_commits():
    """测试失败的commits"""
    print("🔍 测试失败的commits...")
    
    # 初始化
    manager = RepositoryManager()
    repo_path = manager.ensure_repository_updated()
    repo = Repo(str(repo_path))
    parser = EmailParser()
    
    # 失败的commit SHA（从错误报告中提取）
    failed_shas = [
        'd7dfe3f6', '700258b2', 'cf4cf19c', '968dba96', 'defec975'
    ]
    
    print(f"📊 测试 {len(failed_shas)} 个失败的commits\n")
    
    for i, sha in enumerate(failed_shas):
        print(f"{i+1}. 测试 commit {sha}")
        print("-" * 60)
        
        try:
            # 获取commit
            commit = repo.commit(sha)
            print(f"   作者: {commit.author.name} <{commit.author.email}>")
            print(f"   日期: {datetime.fromtimestamp(commit.committed_date)}")
            print(f"   消息: {commit.summary[:80]}...")
            
            # 检查是否有'm'文件
            if 'm' in commit.tree:
                print("   ✅ 找到 'm' 文件")
                
                # 获取内容
                m_content = commit.tree['m'].data_stream.read()
                print(f"   📄 文件大小: {len(m_content)} bytes")
                
                # 尝试解码
                try:
                    content_str = m_content.decode('utf-8')
                    print("   ✅ UTF-8解码成功")
                    
                    # 检查邮件头
                    has_from = 'From:' in content_str
                    has_subject = 'Subject:' in content_str
                    has_message_id = 'Message-ID:' in content_str or 'Message-Id:' in content_str
                    
                    print(f"   📧 邮件头检查:")
                    print(f"      From: {'✅' if has_from else '❌'}")
                    print(f"      Subject: {'✅' if has_subject else '❌'}")
                    print(f"      Message-ID: {'✅' if has_message_id else '❌'}")
                    
                    # 显示前500字符
                    print(f"   📜 内容预览:")
                    print("   " + "-" * 40)
                    preview = content_str[:500].replace('\n', '\n   ')
                    print(f"   {preview}")
                    print("   " + "-" * 40)
                    
                    # 尝试解析
                    try:
                        email_node = parser.parse_commit_to_email(commit)
                        print(f"   🔍 解析结果:")
                        print(f"      Message-ID: {email_node.message_id}")
                        print(f"      Subject: {email_node.subject}")
                        print(f"      Sender: {email_node.sender}")
                        
                        # 检查为什么被标记为Invalid
                        if not email_node.message_id:
                            print("      ❌ 原因: 缺少Message-ID")
                        elif not email_node.subject:
                            print("      ❌ 原因: 缺少Subject")
                        elif not email_node.sender:
                            print("      ❌ 原因: 缺少Sender")
                        elif len(email_node.subject.strip()) < 3:
                            print("      ❌ 原因: Subject太短")
                        else:
                            print("      ❓ 其他验证失败")
                            
                    except Exception as e:
                        print(f"   ❌ 解析失败: {e}")
                    
                except UnicodeDecodeError as e:
                    print(f"   ❌ UTF-8解码失败: {e}")
                    # 尝试其他编码
                    try:
                        content_str = m_content.decode('latin-1')
                        print("   ✅ Latin-1解码成功")
                    except:
                        print("   ❌ 所有编码都失败")
            else:
                print("   ❌ 没有 'm' 文件")
                print(f"   📁 文件列表: {list(commit.tree.trees.keys())[:10]}")
                
                # 检查是否是合并commit
                if len(commit.parents) > 1:
                    print("   🔀 这是一个合并commit")
                    
        except Exception as e:
            print(f"   💥 错误: {e}")
        
        print()

    # 总结
    print("💡 可能的原因:")
    print("   1. 某些commits不是邮件commits（如仓库维护commits）")
    print("   2. 邮件格式不标准，缺少必要的头部字段")
    print("   3. 编码问题导致解析失败")
    print("   4. 验证规则过于严格")

if __name__ == "__main__":
    test_failed_commits()