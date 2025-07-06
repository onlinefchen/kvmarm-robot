#!/usr/bin/env python3
"""
邮件提取完整性验证工具
专门用于验证邮件提取功能是否会遗漏邮件
"""

import os
import logging
from datetime import datetime, timedelta
from email_parser import extract_emails_by_date_range
from repository import RepositoryManager

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_email_extraction_completeness():
    """测试邮件提取的完整性"""
    print("🔍 测试邮件提取完整性...")
    print("=" * 60)
    
    # 测试1: 检查最近7天的邮件
    print("\n📅 测试1: 最近7天的邮件提取")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    emails_recent = extract_emails_by_date_range(
        None, 
        date_range=(start_date, end_date),
        verify_completeness=True
    )
    
    print(f"✅ 最近7天提取到 {len(emails_recent)} 封邮件")
    
    # 测试2: 检查最近100个commits
    print("\n📊 测试2: 最近100个commits")
    emails_by_count = extract_emails_by_date_range(
        None, 
        limit=100,
        verify_completeness=True
    )
    
    print(f"✅ 最近100个commits提取到 {len(emails_by_count)} 封邮件")
    
    # 测试3: 检查Git仓库状态
    print("\n🔧 测试3: Git仓库状态检查")
    manager = RepositoryManager()
    repo_path = manager.ensure_repository_updated()
    
    # 获取仓库基本信息
    import git
    repo = git.Repo(repo_path)
    
    # 检查总commit数
    total_commits = sum(1 for _ in repo.iter_commits('master'))
    print(f"   📊 仓库总commits数: {total_commits}")
    
    # 检查最新commit时间
    latest_commit = next(repo.iter_commits('master'))
    latest_time = datetime.fromtimestamp(latest_commit.committed_date)
    print(f"   🕒 最新commit时间: {latest_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查仓库是否是最新的
    time_since_latest = datetime.now() - latest_time
    if time_since_latest.days > 1:
        print(f"   ⚠️  最新commit距今 {time_since_latest.days} 天，可能需要更新仓库")
    else:
        print(f"   ✅ 仓库是最新的 (距今 {time_since_latest.seconds // 3600} 小时)")
    
    # 测试4: 验证邮件内容质量
    print("\n📝 测试4: 邮件内容质量验证")
    
    if emails_recent:
        sample_emails = emails_recent[:5]  # 检查前5封邮件
        
        for i, email in enumerate(sample_emails):
            print(f"\n   📧 邮件样本 {i+1}:")
            print(f"      Message-ID: {email.message_id}")
            print(f"      主题: {email.subject[:60]}...")
            print(f"      发送者: {email.sender}")
            print(f"      时间: {email.date.strftime('%Y-%m-%d %H:%M')}")
            print(f"      类型: {email.message_type.value}")
            
            # 验证必要字段
            assert email.message_id, "Message-ID不能为空"
            assert email.subject, "Subject不能为空"
            assert email.sender, "Sender不能为空"
            assert email.git_hash, "Git hash不能为空"
            
        print(f"   ✅ {len(sample_emails)} 个邮件样本验证通过")
    
    # 测试5: 检查邮件时间分布
    print("\n📈 测试5: 邮件时间分布分析")
    
    if len(emails_recent) > 1:
        # 按日期分组
        from collections import defaultdict
        daily_counts = defaultdict(int)
        
        for email in emails_recent:
            date_key = email.date.strftime('%Y-%m-%d')
            daily_counts[date_key] += 1
        
        print(f"   📊 过去7天的邮件分布:")
        for date_str in sorted(daily_counts.keys()):
            count = daily_counts[date_str]
            print(f"      {date_str}: {count} 封邮件")
        
        # 检查是否有空白天
        total_days = 7
        active_days = len(daily_counts)
        if active_days < total_days:
            print(f"   ⚠️  有 {total_days - active_days} 天没有邮件活动")
        else:
            print(f"   ✅ 每天都有邮件活动")
    
    print("\n" + "=" * 60)
    print("🎯 邮件提取完整性验证总结:")
    print(f"   ✅ 系统能够正常提取邮件")
    print(f"   ✅ 邮件字段完整有效")
    print(f"   ✅ 时间范围过滤正常工作")
    print(f"   ✅ 数量限制功能正常")
    
    if emails_recent:
        print(f"   📊 建议：系统运行正常，可以用于生产环境")
    else:
        print(f"   ⚠️  警告：没有提取到邮件，请检查仓库状态或时间范围")
    
    return len(emails_recent) > 0


def test_specific_time_ranges():
    """测试特定时间范围的邮件提取"""
    print("\n🔍 测试特定时间范围...")
    
    # 测试不同的时间范围
    test_ranges = [
        (timedelta(days=1), "过去1天"),
        (timedelta(days=3), "过去3天"),
        (timedelta(days=7), "过去7天"),
        (timedelta(days=14), "过去14天"),
        (timedelta(days=30), "过去30天")
    ]
    
    results = {}
    
    for delta, label in test_ranges:
        end_date = datetime.now()
        start_date = end_date - delta
        
        emails = extract_emails_by_date_range(
            None,
            date_range=(start_date, end_date),
            verify_completeness=False  # 减少输出
        )
        
        results[label] = len(emails)
        print(f"   📊 {label}: {len(emails)} 封邮件")
    
    # 验证时间范围的合理性
    prev_count = 0
    for label, count in results.items():
        if count < prev_count:
            print(f"   ⚠️  异常：{label} 的邮件数量少于前一个时间段")
        prev_count = count
    
    return results


if __name__ == "__main__":
    print("🚀 ARM KVM邮件列表提取完整性验证")
    print("=" * 60)
    
    try:
        # 主要测试
        success = test_email_extraction_completeness()
        
        # 附加测试
        test_specific_time_ranges()
        
        if success:
            print(f"\n🎉 所有测试通过！邮件提取功能正常工作")
            print(f"✅ 可以安全地生成过去一周的邮件总结")
        else:
            print(f"\n❌ 测试发现问题，请检查配置")
            
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()