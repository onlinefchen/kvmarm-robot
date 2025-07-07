#!/usr/bin/env python3
"""
简单的调试脚本，分析邮件解析失败
"""
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from repository import RepositoryManager
from email_parser import EmailParser, extract_emails_by_date_range
from datetime import datetime, timedelta

def analyze_failures():
    """分析解析失败"""
    print("🔍 分析邮件解析失败...")
    
    # 使用与GitHub Actions相同的参数
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    print(f"📅 时间范围: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
    
    # 直接调用email_parser的函数，它会输出详细信息
    emails = extract_emails_by_date_range(
        repo_path=None,  # 会自动下载/更新
        date_range=(start_date, end_date),
        limit=None,
        verify_completeness=True  # 这会输出失败详情
    )
    
    print(f"\n✅ 成功提取: {len(emails)} 封邮件")
    
    # 检查前几个邮件的内容
    print("\n📧 成功解析的邮件示例:")
    for i, email in enumerate(emails[:3]):
        print(f"\n{i+1}. {email.subject}")
        print(f"   发送者: {email.sender}")
        print(f"   类型: {email.message_type}")
        print(f"   Git SHA: {email.git_hash[:8]}")

if __name__ == "__main__":
    analyze_failures()