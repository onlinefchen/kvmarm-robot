#!/usr/bin/env python3
"""
通知功能演示脚本
展示如何配置和使用 Lark、Telegram、Email 通知功能
"""

import os
import json
from datetime import datetime
from notification_sender import NotificationManager

def demo_notification_features():
    """演示通知功能"""
    print("🚀 ARM KVM邮件列表分析系统 - 通知功能演示")
    print("=" * 60)
    
    # 1. 显示当前配置状态
    print("\n📊 1. 当前通知配置状态")
    print("-" * 30)
    
    manager = NotificationManager()
    config = manager.config
    
    platforms = ['lark', 'telegram', 'email']
    for platform in platforms:
        status = "✅ 已配置" if config.is_configured(platform) else "❌ 未配置"
        print(f"   {platform.capitalize()}: {status}")
    
    # 2. 创建演示数据
    print("\n📝 2. 创建演示通知数据")
    print("-" * 30)
    
    demo_data = {
        'overview': {
            'total_messages': 15,
            'total_threads': 3,
            'unique_contributors': 7,
            'date_range': [
                '2025-07-01T00:00:00+00:00',
                '2025-07-07T23:59:59+00:00'
            ]
        },
        'threads': [
            {
                'subject': '[DEMO PATCH v2 1/3] KVM: arm64: 演示通知功能',
                'all_nodes': [1, 2, 3, 4, 5],
                'root_node': {
                    'sender': 'Demo Developer <demo@example.com>',
                    'lore_url': 'https://lore.kernel.org/kvmarm/demo-message-1/'
                }
            },
            {
                'subject': '[DEMO PATCH v1 1/2] KVM: arm64: 性能优化示例',
                'all_nodes': [1, 2, 3],
                'root_node': {
                    'sender': 'Performance Expert <perf@kernel.org>',
                    'lore_url': 'https://lore.kernel.org/kvmarm/demo-message-2/'
                }
            },
            {
                'subject': '[DEMO RFC] KVM: arm64: 新特性讨论',
                'all_nodes': [1, 2, 3, 4, 5, 6, 7],
                'root_node': {
                    'sender': 'Feature Architect <feature@arm.com>',
                    'lore_url': 'https://lore.kernel.org/kvmarm/demo-message-3/'
                }
            }
        ]
    }
    
    print("   ✅ 创建了包含3个重要线程的演示数据")
    print(f"   📊 模拟数据: {demo_data['overview']['total_messages']} 封邮件，{demo_data['overview']['total_threads']} 个线程")
    
    # 3. 演示配置方法
    print("\n🔧 3. 通知平台配置方法")
    print("-" * 30)
    
    print("   📱 Lark (飞书) 配置:")
    print("     export ENABLE_LARK=true")
    print("     export LARK_WEBHOOK_URL='https://open.larksuite.com/open-apis/bot/v2/hook/xxx'")
    print("")
    
    print("   📱 Telegram 配置:")
    print("     export ENABLE_TELEGRAM=true")
    print("     export TELEGRAM_BOT_TOKEN='123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ'")
    print("     export TELEGRAM_CHAT_ID='-1001234567890'")
    print("")
    
    print("   📧 Email 配置:")
    print("     export ENABLE_EMAIL=true")
    print("     export EMAIL_USER='your-email@gmail.com'")
    print("     export EMAIL_PASSWORD='your-app-password'")
    print("     export EMAIL_RECIPIENTS='user1@example.com,user2@example.com'")
    
    # 4. 展示消息格式
    print("\n🎨 4. 通知消息格式预览")
    print("-" * 30)
    
    # Telegram 消息格式
    print("   📱 Telegram 消息格式:")
    telegram_message = f"""📊 *ARM KVM 邮件列表周报*

📅 *时间范围*: {demo_data['overview']['date_range'][0][:10]} 至 {demo_data['overview']['date_range'][1][:10]}

📧 *邮件统计*: {demo_data['overview']['total_messages']} 封邮件，{demo_data['overview']['total_threads']} 个线程
👥 *贡献者*: {demo_data['overview']['unique_contributors']} 位开发者参与

🔥 *重要线程*:
1. [DEMO PATCH v2 1/3] KVM: arm64: 演示通知功能...
   📄 5 封邮件 | 👤 Demo Developer
   🔗 [查看详情](https://lore.kernel.org/kvmarm/demo-message-1/)

2. [DEMO PATCH v1 1/2] KVM: arm64: 性能优化示例...
   📄 3 封邮件 | 👤 Performance Expert
   🔗 [查看详情](https://lore.kernel.org/kvmarm/demo-message-2/)

📖 [查看完整报告](https://lore.kernel.org/kvmarm/)"""
    
    print("     " + telegram_message.replace('\n', '\n     '))
    
    # 5. 功能测试演示
    print("\n🧪 5. 功能测试演示")
    print("-" * 30)
    
    if manager.notifiers:
        print(f"   ✅ 检测到 {len(manager.notifiers)} 个已配置的通知平台")
        
        # 询问是否发送测试通知
        try:
            choice = input("\n   🤔 是否发送测试通知？(y/N): ").strip().lower()
            
            if choice in ['y', 'yes']:
                print("\n   📤 正在发送测试通知...")
                results = manager.test_all_notifications()
                
                print("\n   📊 测试结果:")
                for platform, success in results.items():
                    status = "✅ 成功" if success else "❌ 失败"
                    print(f"      {platform}: {status}")
                    
                success_count = sum(1 for success in results.values() if success)
                print(f"\n   🎯 总结: {success_count}/{len(results)} 平台测试成功")
            else:
                print("\n   ⏭️  跳过测试通知发送")
                
        except KeyboardInterrupt:
            print("\n\n   ⏹️  用户取消操作")
    else:
        print("   ⚠️  未配置任何通知平台，无法进行测试")
    
    # 6. 使用建议
    print("\n💡 6. 使用建议和最佳实践")
    print("-" * 30)
    
    print("   🔐 安全建议:")
    print("     • 使用环境变量存储敏感信息")
    print("     • 定期轮换API密钥和令牌")
    print("     • 启用两步验证")
    
    print("\n   ⚡ 性能建议:")
    print("     • 避免过于频繁的通知")
    print("     • 只在有重要更新时发送")
    print("     • 使用异步发送减少等待时间")
    
    print("\n   🎨 用户体验:")
    print("     • 保持消息格式清晰简洁")
    print("     • 提供有用的跳转链接")
    print("     • 包含关键统计信息")
    
    # 7. 命令行使用示例
    print("\n⚙️  7. 命令行使用示例")
    print("-" * 30)
    
    print("   基本使用:")
    print("     # 分析并自动发送通知")
    print("     python analyze.py main --send-notifications")
    print("")
    print("     # 测试通知平台")
    print("     python analyze.py notify test-platforms")
    print("")
    print("     # 查看配置状态")
    print("     python analyze.py notify status")
    print("")
    print("     # 手动发送通知")
    print("     python analyze.py notify send results/2025-07-06")
    
    # 8. 自动化设置
    print("\n🔄 8. 自动化设置示例")
    print("-" * 30)
    
    print("   Cron 定时任务:")
    print("     # 每周一早上9点运行并发送通知")
    print("     0 9 * * 1 cd /path/to/project && python analyze.py main --send-notifications")
    print("")
    print("   GitHub Actions:")
    print("     # 在 .github/workflows/weekly-report.yml 中配置")
    print("     # 自动运行分析并推送到各个通知平台")
    
    print("\n" + "=" * 60)
    print("🎉 通知功能演示完成！")
    print("📚 更多详细信息请查看 NOTIFICATIONS.md 文档")


if __name__ == "__main__":
    try:
        demo_notification_features()
    except KeyboardInterrupt:
        print("\n\n👋 演示已退出")
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()