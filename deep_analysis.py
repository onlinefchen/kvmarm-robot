#!/usr/bin/env python3
"""
深入分析邮件解析失败的原因
"""
import os
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# 确保能导入项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_analysis():
    """运行分析"""
    print("🔍 深入分析过去10天的邮件解析情况")
    print("=" * 60)
    
    # 计算时间范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=10)
    
    # 运行analyze.py并捕获输出
    cmd = [
        sys.executable,
        "analyze.py",
        "main",
        "--since", start_date.strftime("%Y-%m-%d"),
        "--until", end_date.strftime("%Y-%m-%d"),
        "--debug"
    ]
    
    print(f"📅 分析时间范围: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
    print(f"🚀 执行命令: {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        # 运行命令并捕获输出
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": os.path.dirname(os.path.abspath(__file__))}
        )
        
        # 分析输出
        output_lines = result.stdout.split('\n')
        stderr_lines = result.stderr.split('\n')
        
        # 查找失败信息
        failed_info = []
        capture_failures = False
        
        for line in output_lines:
            if "解析失败:" in line and "个 commits" in line:
                print(f"⚠️  {line.strip()}")
                capture_failures = True
            elif "失败详情:" in line:
                capture_failures = True
            elif capture_failures and line.strip().startswith(('d', '7', 'c', '9', '6', 'a', 'b', 'e', 'f', '0', '1', '2', '3', '4', '5', '8')):
                failed_info.append(line.strip())
            elif capture_failures and "还有" in line:
                print(f"   {line.strip()}")
                capture_failures = False
        
        # 打印找到的失败信息
        if failed_info:
            print("\n📋 失败的commits:")
            for info in failed_info:
                print(f"   {info}")
        
        # 如果有错误输出
        if result.stderr:
            print("\n⚠️  错误输出:")
            for line in stderr_lines[:20]:  # 只显示前20行
                if line.strip():
                    print(f"   {line}")
        
        return result.returncode == 0, failed_info
        
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        return False, []

def analyze_specific_commit(commit_sha):
    """分析特定的commit"""
    print(f"\n🔍 详细分析commit: {commit_sha}")
    print("-" * 40)
    
    # 创建一个Python脚本来分析
    analysis_script = f'''
import sys
sys.path.insert(0, ".")

try:
    from repository import RepositoryManager
    from email_parser import EmailParser
    import email
    from email import policy
    
    # 获取仓库
    manager = RepositoryManager()
    repo_path = manager.ensure_repository_updated()
    
    # 使用git命令获取commit信息
    import subprocess
    
    # 获取commit信息
    cmd = ["git", "-C", str(repo_path), "show", "--format=fuller", "{commit_sha}"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("❌ 无法获取commit信息")
        sys.exit(1)
    
    print("📝 Commit信息:")
    lines = result.stdout.split("\\n")[:10]
    for line in lines:
        print(f"   {{line}}")
    
    # 检查是否有'm'文件
    cmd = ["git", "-C", str(repo_path), "ls-tree", "{commit_sha}", "m"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if not result.stdout:
        print("\\n❌ 此commit没有'm'文件")
        # 列出文件
        cmd = ["git", "-C", str(repo_path), "ls-tree", "--name-only", "{commit_sha}"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        print("📁 Commit中的文件:")
        for f in result.stdout.strip().split("\\n")[:10]:
            print(f"   - {{f}}")
    else:
        print("\\n✅ 找到'm'文件")
        
        # 获取'm'文件内容
        cmd = ["git", "-C", str(repo_path), "show", f"{commit_sha}:m"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            content = result.stdout
            print(f"📄 文件大小: {{len(content)}} 字符")
            
            # 检查邮件头
            print("\\n📧 邮件头检查:")
            print(f"   From: {{'✅' if 'From:' in content else '❌'}}")
            print(f"   Subject: {{'✅' if 'Subject:' in content else '❌'}}")
            print(f"   Message-ID: {{'✅' if 'Message-ID:' in content or 'Message-Id:' in content else '❌'}}")
            print(f"   Date: {{'✅' if 'Date:' in content else '❌'}}")
            
            # 显示前500字符
            print("\\n📜 内容预览:")
            print("-" * 40)
            preview = content[:500].replace("\\n", "\\n")
            print(preview)
            print("-" * 40)
            
            # 尝试解析
            try:
                msg = email.message_from_string(content, policy=policy.default)
                print("\\n✅ Email解析成功")
                print(f"   Subject: {{msg.get('Subject', 'N/A')[:60]}}")
                print(f"   From: {{msg.get('From', 'N/A')}}")
                print(f"   Message-ID: {{msg.get('Message-ID', 'N/A')}}")
            except Exception as e:
                print(f"\\n❌ Email解析失败: {{e}}")
                
except Exception as e:
    print(f"💥 分析过程出错: {{e}}")
    import traceback
    traceback.print_exc()
'''
    
    # 执行分析脚本
    try:
        result = subprocess.run(
            [sys.executable, "-c", analysis_script],
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print("错误:", result.stderr)
    except Exception as e:
        print(f"❌ 执行分析失败: {e}")

def main():
    """主函数"""
    print("🚀 开始深入分析邮件解析情况")
    print("=" * 60)
    
    # 运行主分析
    success, failed_commits = run_analysis()
    
    if not success:
        print("\n❌ 分析过程出现错误")
        return
    
    # 如果有失败的commits，深入分析
    if failed_commits:
        print(f"\n📊 发现 {len(failed_commits)} 个解析失败的commits")
        print("开始深入分析每个失败的原因...")
        
        # 分析前5个失败的commits
        for i, commit_info in enumerate(failed_commits[:5]):
            # 提取commit SHA
            commit_sha = commit_info.split(':')[0].strip()
            analyze_specific_commit(commit_sha)
            
            if i < len(failed_commits) - 1:
                print("\n" + "=" * 60)
    else:
        print("\n✅ 太好了！没有解析失败的commits")
    
    print("\n📊 分析完成")
    print("=" * 60)

if __name__ == "__main__":
    main()