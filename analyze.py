#!/usr/bin/env python3
"""
Linux ARM KVM邮件列表自动化分析系统
主程序和测试入口
"""

import os
import logging
import click
from datetime import datetime, timedelta
from typing import Optional, Tuple
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from repository import RepositoryManager, test_repository_management
from email_parser import extract_emails_by_date_range, test_email_parsing
from lore_links import add_lore_links, validate_lore_links, test_lore_link_generation, test_lore_link_validation
from tree_builder import build_email_forest, test_tree_building
from content_chunker import apply_intelligent_chunking, test_content_chunking
from ai_analyzer import analyze_with_ai, test_ai_analysis
from report_generator import generate_reports
from notification_sender import NotificationManager
from enhanced_notification_sender import EnhancedNotificationManager
from optimized_notification_sender import OptimizedNotificationManager
from markdown_notification_sender import MarkdownNotificationManager
from html_generator import HTMLReportGenerator


def setup_debug_logging():
    """设置调试模式日志"""
    logging.getLogger().setLevel(logging.DEBUG)
    

def main_pipeline(
    date_range: Optional[Tuple[datetime, datetime]] = None,
    debug: bool = True,
    limit: Optional[int] = None,
    ai_provider: str = "openai",
    output_dir: str = "results",
    language: str = "zh",
    verify_completeness: bool = True,
    send_notifications: bool = False
) -> Tuple[object, dict]:
    """主处理流程"""
    
    if debug:
        setup_debug_logging()
        print("🚀 启动ARM KVM邮件列表分析系统")
        print("=" * 50)
    
    try:
        # Step 1: 仓库管理
        print("📂 Step 1: 仓库管理...")
        repo_manager = RepositoryManager()
        repo_path = repo_manager.ensure_repository_updated()
        
        # Step 2: 邮件提取和解析
        print("📧 Step 2: 邮件提取...")
        emails = extract_emails_by_date_range(
            str(repo_path), 
            date_range, 
            limit, 
            verify_completeness=verify_completeness
        )
        print(f"   提取到 {len(emails)} 封邮件")
        
        if not emails:
            print("❌ 没有找到邮件，程序退出")
            return None, {}
        
        # Step 3: 构建树形结构
        print("🌳 Step 3: 构建树形结构...")
        forest = build_email_forest(emails)
        print(f"   构建了 {len(forest.threads)} 个线程")
        
        # Step 4: 生成lore链接
        print("🔗 Step 4: 生成lore链接...")
        add_lore_links(forest)
        
        # Step 5: 验证lore链接
        print("🔍 Step 5: 验证lore链接...")
        validate_lore_links(forest, debug=debug)
        
        # Step 6: 智能分割
        print("✂️  Step 6: 智能内容分割...")
        chunked_data = apply_intelligent_chunking(forest)
        
        # Step 7: AI分析
        print("🤖 Step 7: AI分析...")
        analyses = analyze_with_ai(chunked_data, forest, ai_provider, language, debug=debug)
        
        # Step 8: 生成报告
        print("📊 Step 8: 生成报告...")
        result_path = generate_reports(forest, analyses, output_dir, language)
        
        # Step 8.5: 生成HTML报告并部署到GitHub Pages
        print("🌐 Step 8.5: 生成HTML报告...")
        try:
            html_generator = HTMLReportGenerator()
            html_file = html_generator.generate_html_report(result_path)
            if html_file:
                print(f"   ✅ HTML报告已生成: {html_file}")
            else:
                print("   ⚠️ HTML报告生成跳过")
        except Exception as e:
            print(f"   ⚠️ HTML报告生成失败: {e}")
        
        # Step 9: 发送通知 (可选)
        if send_notifications:
            print("📤 Step 9: 发送Markdown通知...")
            
            # 使用Markdown通知管理器（直接使用生成的完美MD文件）
            markdown_manager = MarkdownNotificationManager()
            
            if markdown_manager.notifiers:
                print("   🚀 使用Markdown通知功能（直接使用生成的完美MD文件）")
                notification_results = markdown_manager.send_markdown_notifications(result_path)
                
                success_count = sum(1 for success in notification_results.values() if success)
                total_count = len(notification_results)
                
                print(f"   📊 Markdown通知发送结果: {success_count}/{total_count} 平台成功")
                
                for platform, success in notification_results.items():
                    status = "✅" if success else "❌"
                    print(f"      {status} {platform}")
                    
                if success_count > 0:
                    print("   💡 Markdown通知特性:")
                    print("      📄 直接使用生成的完美MD文件内容")
                    print("      📱 飞书: 解析MD内容生成多卡片")
                    print("      📧 邮件: MD转HTML，保持完美格式")
                    print("      📱 Telegram: 优化MD格式，支持长消息分段")
            else:
                print("   ⚠️  未配置任何通知平台，跳过通知发送")
        
        print("✅ 分析完成！")
        return forest, analyses
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        if debug:
            import traceback
            traceback.print_exc()
        return None, {}


# 测试函数
def test_repository_management():
    """测试仓库管理功能"""
    print("🧪 测试仓库管理...")
    
    manager = RepositoryManager()
    
    # 测试仓库克隆/更新
    repo_path = manager.ensure_repository_updated()
    
    assert repo_path.exists()
    assert manager._is_git_repository(repo_path)
    
    # 测试获取最近的commits
    recent_commits = manager.get_recent_commits(limit=5)
    print(f"   获取到 {len(recent_commits)} 个最近的commits")
    
    for commit in recent_commits[:3]:
        print(f"   📧 {commit.hexsha[:8]} - {commit.summary[:50]}...")
    
    print("✅ 仓库管理测试通过")


def test_email_parsing_with_lore():
    """测试邮件解析和lore链接生成"""
    print("🧪 测试邮件解析和lore链接...")
    
    # 提取最近10封邮件进行测试
    emails = extract_emails_by_date_range(None, limit=10)
    
    assert len(emails) > 0
    print(f"   提取了 {len(emails)} 封邮件")
    
    # 检查基本字段
    for i, email in enumerate(emails[:5]):
        # 生成lore链接
        from lore_links import LoreLinksManager
        lore_manager = LoreLinksManager()
        email.lore_url = lore_manager.generate_lore_url(email.message_id)
        
        print(f"\n   📧 邮件 {i+1}:")
        print(f"      主题: {email.subject[:50]}...")
        print(f"      发送者: {email.sender}")
        print(f"      类型: {email.message_type.value}")
        print(f"      🔗 Lore: {email.lore_url}")
        
        assert email.git_hash
        assert email.message_id
        assert email.lore_url
    
    print("\n✅ 邮件解析和lore链接测试通过")


def test_full_pipeline():
    """测试完整流程"""
    print("🧪 测试完整流程...")
    
    # 使用最近3天的邮件进行测试
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3)
    
    print(f"   📅 测试时间范围: {start_date.date()} 到 {end_date.date()}")
    
    forest, analyses = main_pipeline(
        date_range=(start_date, end_date),
        debug=True,
        limit=50,  # 限制邮件数量以加快测试
        output_dir="test_results",
        language="zh"
    )
    
    if forest is None:
        print("   ⚠️  没有提取到邮件或处理失败")
        return
    
    # 检查输出文件
    expected_files = [
        "test_results",
        f"test_results/{datetime.now().strftime('%Y-%m-%d')}"
    ]
    
    for file_path in expected_files:
        assert Path(file_path).exists(), f"缺少输出目录: {file_path}"
        print(f"   ✅ 生成目录: {file_path}")
    
    print("✅ 完整流程测试通过")


# CLI命令
@click.command()
@click.option('--since', type=str, help='开始日期 (YYYY-MM-DD)')
@click.option('--until', type=str, help='结束日期 (YYYY-MM-DD)')
@click.option('--limit', type=int, help='限制处理的邮件数量')
@click.option('--mode', type=click.Choice(['recent', 'date_range', 'weekly']), default='weekly', help='处理模式')
@click.option('--debug', is_flag=True, help='开启调试模式')
@click.option('--provider', type=click.Choice(['openai', 'gemini']), default='openai', help='AI提供商')
@click.option('--output', type=str, default='results', help='输出目录')
@click.option('--language', type=click.Choice(['zh', 'en']), default='zh', help='报告语言 (zh: 中文, en: English)')
@click.option('--verify-completeness', is_flag=True, default=True, help='验证邮件提取的完整性')
@click.option('--send-notifications', is_flag=True, help='分析完成后发送通知到配置的平台')
def main(since, until, limit, mode, debug, provider, output, language, verify_completeness, send_notifications):
    """ARM KVM邮件列表分析系统 - 默认生成过去一周的邮件总结"""
    
    date_range = None
    
    if mode == 'weekly' or (mode == 'recent' and not since and not until and not limit):
        # 默认模式：生成过去一周的报告
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        date_range = (start_date, end_date)
        print(f"📅 默认模式：生成过去一周的邮件总结")
        print(f"   时间范围: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
    elif mode == 'date_range' and since and until:
        start_date = datetime.strptime(since, '%Y-%m-%d')
        end_date = datetime.strptime(until, '%Y-%m-%d')
        date_range = (start_date, end_date)
    
    # 检查环境变量
    if provider == 'openai' and not os.getenv('OPENAI_API_KEY'):
        print("❌ 错误: OPENAI_API_KEY 环境变量未设置")
        return
    
    if provider == 'gemini' and not os.getenv('GEMINI_API_KEY'):
        print("❌ 错误: GEMINI_API_KEY 环境变量未设置")
        return
    
    # 运行主流程
    forest, analyses = main_pipeline(
        date_range=date_range,
        debug=debug,
        limit=limit,
        ai_provider=provider,
        output_dir=output,
        language=language,
        verify_completeness=verify_completeness,
        send_notifications=send_notifications
    )
    
    if forest:
        print(f"\n🎉 成功分析了 {forest.total_emails} 封邮件")
        print(f"📊 生成了 {len(forest.threads)} 个线程分析")
        print(f"📁 结果保存在: {output}")


# 单独的测试命令
@click.group()
def test():
    """运行测试"""
    pass


@test.command()
def repo():
    """测试仓库管理"""
    test_repository_management()


@test.command()
def email():
    """测试邮件解析"""
    test_email_parsing_with_lore()


@test.command()
def lore_gen():
    """测试lore链接生成"""
    test_lore_link_generation()


@test.command()
def lore_val():
    """测试lore链接验证"""
    test_lore_link_validation()


@test.command()
def tree():
    """测试树形结构构建"""
    test_tree_building()


@test.command()
def chunk():
    """测试内容分割"""
    test_content_chunking()


@test.command()
def ai():
    """测试AI分析"""
    test_ai_analysis()


@test.command()
def full():
    """测试完整流程"""
    test_full_pipeline()


@test.command()
def notifications():
    """测试通知功能"""
    print("🧪 测试通知功能...")
    
    try:
        manager = NotificationManager()
        
        if not manager.notifiers:
            print("⚠️ 未配置任何通知平台")
            print("\n📝 请设置以下环境变量来启用通知:")
            print("   Lark: LARK_WEBHOOK_URL, ENABLE_LARK=true")
            print("   Telegram: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, ENABLE_TELEGRAM=true")
            print("   Email: EMAIL_USER, EMAIL_PASSWORD, EMAIL_RECIPIENTS, ENABLE_EMAIL=true")
            return
        
        print(f"📊 已配置 {len(manager.notifiers)} 个通知平台")
        
        results = manager.test_all_notifications()
        
        print("\n📊 测试结果:")
        for platform, success in results.items():
            status = "✅ 成功" if success else "❌ 失败"
            print(f"   {platform}: {status}")
        
        success_count = sum(1 for success in results.values() if success)
        print(f"\n🎯 总结: {success_count}/{len(results)} 平台测试成功")
        
    except Exception as e:
        print(f"❌ 通知测试失败: {e}")
        import traceback
        traceback.print_exc()


@test.command()
def all():
    """运行所有测试"""
    print("🧪 运行所有测试...")
    print("=" * 50)
    
    try:
        test_repository_management()
        print()
        
        test_email_parsing_with_lore()
        print()
        
        test_lore_link_generation()
        print()
        
        # test_lore_link_validation()  # 跳过网络验证以加快测试
        # print()
        
        test_tree_building()
        print()
        
        test_content_chunking()
        print()
        
        # test_ai_analysis()  # 跳过AI测试以避免API调用
        # print()
        
        print("🎉 所有测试通过！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


# 通知管理命令组
@click.group()
def notify():
    """通知管理"""
    pass


@notify.command()
def test_platforms():
    """测试所有通知平台的连通性"""
    print("🧪 测试通知平台连通性...")
    
    try:
        manager = NotificationManager()
        
        if not manager.notifiers:
            print("⚠️ 未配置任何通知平台")
            print("\n📝 环境变量配置说明:")
            print("   Lark (飞书):")
            print("     LARK_WEBHOOK_URL=https://open.larksuite.com/open-apis/bot/v2/hook/xxx")
            print("     ENABLE_LARK=true")
            print("\n   Telegram:")
            print("     TELEGRAM_BOT_TOKEN=123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ")
            print("     TELEGRAM_CHAT_ID=-1001234567890")
            print("     ENABLE_TELEGRAM=true")
            print("\n   Email:")
            print("     EMAIL_USER=your-email@gmail.com")
            print("     EMAIL_PASSWORD=your-app-password")
            print("     EMAIL_RECIPIENTS=recipient1@example.com,recipient2@example.com")
            print("     ENABLE_EMAIL=true")
            print("     SMTP_SERVER=smtp.gmail.com (可选)")
            print("     SMTP_PORT=587 (可选)")
            return
        
        print(f"📊 已配置 {len(manager.notifiers)} 个通知平台")
        
        results = manager.test_all_notifications()
        
        print("\n📊 测试结果:")
        for platform, success in results.items():
            status = "✅ 成功" if success else "❌ 失败"
            print(f"   {platform}: {status}")
        
        success_count = sum(1 for success in results.values() if success)
        print(f"\n🎯 总结: {success_count}/{len(results)} 平台测试成功")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


@notify.command()
@click.argument('results_dir', type=click.Path(exists=True))
def send(results_dir):
    """发送分析结果通知（标准版）"""
    print(f"📤 发送分析结果通知，目录: {results_dir}")
    
    try:
        manager = NotificationManager()
        
        if not manager.notifiers:
            print("❌ 未配置任何通知平台，请先配置环境变量")
            return
        
        results = manager.send_weekly_summary(results_dir)
        
        print("\n📊 发送结果:")
        for platform, success in results.items():
            status = "✅ 成功" if success else "❌ 失败"
            print(f"   {platform}: {status}")
        
        success_count = sum(1 for success in results.values() if success)
        print(f"\n🎯 总结: {success_count}/{len(results)} 平台发送成功")
        
    except Exception as e:
        print(f"❌ 发送失败: {e}")
        import traceback
        traceback.print_exc()


@notify.command()
@click.argument('results_dir', type=click.Path(exists=True))
def send_enhanced(results_dir):
    """发送增强版通知（支持完整内容显示）"""
    print(f"📤 发送增强版通知，目录: {results_dir}")
    print("🚀 使用增强通知功能（支持完整内容显示）")
    
    try:
        manager = EnhancedNotificationManager()
        
        if not manager.notifiers:
            print("❌ 未配置任何通知平台，请先配置环境变量")
            return
        
        results = manager.send_enhanced_summary(results_dir)
        
        print("\n📊 增强通知发送结果:")
        for platform, success in results.items():
            status = "✅ 成功" if success else "❌ 失败"
            print(f"   {platform}: {status}")
        
        success_count = sum(1 for success in results.values() if success)
        print(f"\n🎯 总结: {success_count}/{len(results)} 平台发送成功")
        
        if success_count > 0:
            print("\n💡 增强功能特性:")
            print("   📱 飞书: 多个详细卡片，突破长度限制")
            print("   📧 邮件: 完整HTML格式，包含所有线程详情")
            print("   📱 Telegram: 保持原有格式")
        
    except Exception as e:
        print(f"❌ 增强通知发送失败: {e}")
        import traceback
        traceback.print_exc()


@notify.command()
@click.argument('results_dir', type=click.Path(exists=True))
def send_optimized(results_dir):
    """发送优化版通知（遵守平台限制，确保完整显示）"""
    print(f"📤 发送优化版通知，目录: {results_dir}")
    print("🚀 使用优化通知功能（遵守平台限制，确保完整显示）")
    
    try:
        manager = OptimizedNotificationManager()
        
        if not manager.notifiers:
            print("❌ 未配置任何通知平台，请先配置环境变量")
            return
        
        results = manager.send_optimized_summary(results_dir)
        
        print("\n📊 优化通知发送结果:")
        for platform, success in results.items():
            status = "✅ 成功" if success else "❌ 失败"
            print(f"   {platform}: {status}")
        
        success_count = sum(1 for success in results.values() if success)
        print(f"\n🎯 总结: {success_count}/{len(results)} 平台发送成功")
        
        if success_count > 0:
            print("\n💡 优化功能特性:")
            print("   📧 邮件: 遵守Gmail 102KB限制，自动压缩优化")
            print("   📱 飞书: 智能分卡片发送，避免内容长度限制")
            print("   📱 Telegram: 保持优化格式")
            print("   🔍 附件: 只包含重要文件，避免邮件过大")
        
    except Exception as e:
        print(f"❌ 优化通知发送失败: {e}")
        import traceback
        traceback.print_exc()


@notify.command()
@click.argument('results_dir', type=click.Path(exists=True))
def send_markdown(results_dir):
    """发送Markdown通知（直接使用生成的完美MD文件）⭐ 推荐"""
    print(f"📤 发送Markdown通知，目录: {results_dir}")
    print("🚀 使用Markdown通知功能（直接使用生成的完美MD文件）")
    
    try:
        manager = MarkdownNotificationManager()
        
        if not manager.notifiers:
            print("❌ 未配置任何通知平台，请先配置环境变量")
            return
        
        results = manager.send_markdown_notifications(results_dir)
        
        print("\n📊 Markdown通知发送结果:")
        for platform, success in results.items():
            status = "✅ 成功" if success else "❌ 失败"
            print(f"   {platform}: {status}")
        
        success_count = sum(1 for success in results.values() if success)
        print(f"\n🎯 总结: {success_count}/{len(results)} 平台发送成功")
        
        if success_count > 0:
            print("\n💡 Markdown通知特性:")
            print("   📄 直接使用生成的完美MD文件内容")
            print("   📱 飞书: 解析MD内容生成精美多卡片")
            print("   📧 邮件: MD转HTML，保持完美格式和样式")
            print("   📱 Telegram: 优化MD格式，支持长消息分段")
            print("   ✨ 内容一致性: 所有平台使用相同的完美内容源")
        
    except Exception as e:
        print(f"❌ Markdown通知发送失败: {e}")
        import traceback
        traceback.print_exc()


@notify.command()
def status():
    """显示通知配置状态"""
    print("📊 通知配置状态:")
    
    try:
        manager = NotificationManager()
        config = manager.config
        
        # Lark状态
        lark_configured = config.is_configured('lark')
        print(f"\n🟢 Lark (飞书): {'✅ 已配置' if lark_configured else '❌ 未配置'}")
        if lark_configured:
            print(f"   Webhook URL: {config.lark_webhook[:30]}...")
        
        # Telegram状态
        telegram_configured = config.is_configured('telegram')
        print(f"\n🟢 Telegram: {'✅ 已配置' if telegram_configured else '❌ 未配置'}")
        if telegram_configured:
            print(f"   Bot Token: {config.telegram_bot_token[:20]}...")
            print(f"   Chat ID: {config.telegram_chat_id}")
        
        # Email状态
        email_configured = config.is_configured('email')
        print(f"\n🟢 Email: {'✅ 已配置' if email_configured else '❌ 未配置'}")
        if email_configured:
            print(f"   SMTP Server: {config.smtp_server}:{config.smtp_port}")
            print(f"   User: {config.email_user}")
            print(f"   Recipients: {len(config.email_recipients)} 个")
        
        total_configured = sum([lark_configured, telegram_configured, email_configured])
        print(f"\n🎯 总结: {total_configured}/3 平台已配置")
        
    except Exception as e:
        print(f"❌ 获取状态失败: {e}")


# GitHub Pages管理命令组
@click.group()
def pages():
    """GitHub Pages管理"""
    pass


@pages.command()
@click.option('--github-repo', default='https://onlinefchen.github.io/kvmarm-robot', help='GitHub Pages URL')
def setup(github_repo):
    """设置GitHub Pages目录结构"""
    print("🚀 设置GitHub Pages...")
    
    try:
        generator = HTMLReportGenerator(github_repo)
        docs_dir = generator.setup_github_pages()
        
        print(f"\n✅ GitHub Pages设置完成!")
        print(f"📁 文档目录: {docs_dir}")
        print(f"🔗 GitHub Pages URL: {github_repo}")
        print(f"\n📝 接下来的步骤:")
        print(f"   1. 提交并推送代码到GitHub")
        print(f"   2. 在GitHub仓库设置中启用Pages")
        print(f"   3. 选择 'docs' 目录作为源")
        print(f"   4. 配置自定义域名（可选）")
        
    except Exception as e:
        print(f"❌ GitHub Pages设置失败: {e}")
        import traceback
        traceback.print_exc()


@pages.command()
@click.argument('results_dir', type=click.Path(exists=True))
@click.option('--github-repo', default='https://onlinefchen.github.io/kvmarm-robot', help='GitHub Pages URL')
def deploy(results_dir, github_repo):
    """部署报告到GitHub Pages"""
    print(f"🚀 部署报告到GitHub Pages...")
    
    try:
        generator = HTMLReportGenerator(github_repo)
        docs_dir = 'docs'
        
        pages_url = generator.deploy_to_pages(results_dir, docs_dir)
        
        print(f"\n✅ 部署完成!")
        print(f"🔗 报告URL: {pages_url}")
        print(f"📁 本地文件: {docs_dir}")
        print(f"\n📝 提交更改:")
        print(f"   git add {docs_dir}")
        print(f"   git commit -m 'Deploy report for {datetime.now().strftime('%Y-%m-%d')}'")
        print(f"   git push")
        
    except Exception as e:
        print(f"❌ 部署失败: {e}")
        import traceback
        traceback.print_exc()


@pages.command()
@click.argument('results_dir', type=click.Path(exists=True))
@click.option('--github-repo', default='https://onlinefchen.github.io/kvmarm-robot', help='GitHub Pages URL')
def generate_html(results_dir, github_repo):
    """只生成HTML报告"""
    print(f"📄 生成HTML报告...")
    
    try:
        generator = HTMLReportGenerator(github_repo)
        html_file = generator.generate_html_report(results_dir)
        
        print(f"✅ HTML报告已生成: {html_file}")
        
    except Exception as e:
        print(f"❌ HTML生成失败: {e}")
        import traceback
        traceback.print_exc()


# CLI入口点
cli = click.Group()
cli.add_command(main)
cli.add_command(test)
cli.add_command(notify)


if __name__ == '__main__':
    cli()