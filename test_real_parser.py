#!/usr/bin/env python3
"""
使用真实的邮件解析器测试失败的commits
"""
import sys
import os
import subprocess
import tempfile

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 创建一个最小的Git环境来测试
def create_test_git_commit(content, commit_sha):
    """创建一个临时的git commit来测试"""
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        # 初始化git仓库
        subprocess.run(['git', 'init'], cwd=temp_dir, capture_output=True)
        
        # 写入邮件内容
        m_file = os.path.join(temp_dir, 'm')
        with open(m_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 添加并提交
        subprocess.run(['git', 'add', 'm'], cwd=temp_dir, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'test'], cwd=temp_dir, capture_output=True)
        
        # 获取commit对象
        from git import Repo
        repo = Repo(temp_dir)
        commit = list(repo.iter_commits())[0]
        
        return commit

def test_email_parsing():
    """测试邮件解析"""
    print("🔍 使用真实parser测试失败的commits...")
    
    # 失败的commit SHAs
    failed_shas = ['d7dfe3f6', '700258b2', 'cf4cf19c']
    
    # 导入解析器
    from email_parser import EmailParser
    parser = EmailParser()
    
    for sha in failed_shas:
        print(f"\n测试 {sha}:")
        print("-" * 40)
        
        # 获取原始内容
        cmd = ["git", "-C", "kvmarm/git/0.git", "show", f"{sha}:m"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ 无法获取内容")
            continue
        
        content = result.stdout
        
        try:
            # 创建临时commit
            commit = create_test_git_commit(content, sha)
            
            # 解析邮件
            email_node = parser.parse_commit_to_email(commit)
            
            print(f"✅ 解析成功:")
            print(f"   From: {email_node.sender}")
            print(f"   Subject: {email_node.subject}")
            print(f"   Message-ID: {email_node.message_id}")
            print(f"   Date: {email_node.date}")
            
            # 验证邮件
            from email_parser import _is_valid_email
            is_valid = _is_valid_email(email_node)
            print(f"   有效性: {'✅' if is_valid else '❌'}")
            
            if not is_valid:
                print("   失败原因分析:")
                if not email_node.subject:
                    print("     - 缺少Subject")
                if not email_node.sender:
                    print("     - 缺少Sender")
                if not email_node.message_id:
                    print("     - 缺少Message-ID")
                if len(email_node.subject.strip()) < 3:
                    print("     - Subject太短")
            
        except Exception as e:
            print(f"❌ 解析失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_email_parsing()