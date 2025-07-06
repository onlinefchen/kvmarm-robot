#!/usr/bin/env python3
"""
通知发送模块
支持 Lark（飞书）、Telegram、Email 多平台推送
"""

import os
import json
import logging
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import asyncio
import aiohttp

logger = logging.getLogger(__name__)


class NotificationConfig:
    """通知配置类"""
    
    def __init__(self):
        # Lark (飞书) 配置
        self.lark_webhook = os.getenv('LARK_WEBHOOK_URL')
        self.lark_secret = os.getenv('LARK_WEBHOOK_SECRET')  # 可选的安全配置
        
        # Telegram 配置
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        # Email 配置
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.email_recipients = os.getenv('EMAIL_RECIPIENTS', '').split(',')
        
        # 通知启用控制
        self.enable_lark = os.getenv('ENABLE_LARK', 'false').lower() == 'true'
        self.enable_telegram = os.getenv('ENABLE_TELEGRAM', 'false').lower() == 'true'
        self.enable_email = os.getenv('ENABLE_EMAIL', 'false').lower() == 'true'
    
    def is_configured(self, platform: str) -> bool:
        """检查指定平台是否已配置"""
        if platform == 'lark':
            return bool(self.lark_webhook and self.enable_lark)
        elif platform == 'telegram':
            return bool(self.telegram_bot_token and self.telegram_chat_id and self.enable_telegram)
        elif platform == 'email':
            return bool(self.email_user and self.email_password and self.email_recipients and self.enable_email)
        return False


class LarkNotifier:
    """飞书通知器"""
    
    def __init__(self, config: NotificationConfig):
        self.config = config
        self.webhook_url = config.lark_webhook
        self.secret = config.lark_secret
    
    def send_summary_notification(self, summary_data: Dict[str, Any]) -> bool:
        """发送总结通知到飞书"""
        try:
            # 构建飞书卡片消息
            card_content = self._build_summary_card(summary_data)
            
            payload = {
                "msg_type": "interactive",
                "card": card_content
            }
            
            # 如果配置了secret，添加签名
            if self.secret:
                payload["timestamp"] = str(int(datetime.now().timestamp()))
                # 这里应该添加签名逻辑，暂时简化处理
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    logger.info("✅ 飞书通知发送成功")
                    return True
                else:
                    logger.error(f"❌ 飞书通知发送失败: {result.get('msg')}")
            else:
                logger.error(f"❌ 飞书通知HTTP错误: {response.status_code}")
            
            return False
            
        except Exception as e:
            logger.error(f"❌ 飞书通知发送异常: {e}")
            return False
    
    def _build_summary_card(self, summary_data: Dict[str, Any]) -> Dict[str, Any]:
        """构建飞书卡片内容"""
        stats = summary_data.get('overview', {})
        total_messages = stats.get('total_messages', 0)
        total_threads = stats.get('total_threads', 0)
        contributors = stats.get('unique_contributors', 0)
        date_range = stats.get('date_range', ['', ''])
        
        # 获取重要线程
        important_threads = self._get_important_threads(summary_data)
        
        # 构建卡片
        card = {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "template": "blue",
                "title": {
                    "content": "📊 ARM KVM 邮件列表周报",
                    "tag": "text"
                }
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "content": f"**📅 时间范围**: {date_range[0][:10]} 至 {date_range[1][:10]}\n\n"
                                 f"**📧 邮件统计**: {total_messages} 封邮件，{total_threads} 个线程\n\n"
                                 f"**👥 贡献者**: {contributors} 位开发者参与",
                        "tag": "lark_md"
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "div",
                    "text": {
                        "content": "**🔥 重要线程**:",
                        "tag": "lark_md"
                    }
                }
            ]
        }
        
        # 添加重要线程
        for i, thread in enumerate(important_threads[:5], 1):
            card["elements"].append({
                "tag": "div",
                "text": {
                    "content": f"**{i}.** {thread['title']}\n"
                             f"📄 {thread['message_count']} 封邮件 | "
                             f"👤 {thread['contributor']} | "
                             f"🔗 [查看详情]({thread['lore_url']})",
                    "tag": "lark_md"
                }
            })
        
        # 添加操作按钮
        card["elements"].extend([
            {
                "tag": "hr"
            },
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {
                            "content": "📖 查看完整报告",
                            "tag": "plain_text"
                        },
                        "type": "primary",
                        "url": "https://lore.kernel.org/kvmarm/"
                    },
                    {
                        "tag": "button",
                        "text": {
                            "content": "📊 项目仓库",
                            "tag": "plain_text"
                        },
                        "type": "default",
                        "url": "https://github.com/your-repo/kvmarm-ai-mailist"
                    }
                ]
            }
        ])
        
        return card
    
    def _get_important_threads(self, summary_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """提取重要线程信息"""
        threads = []
        
        # 这里需要根据实际的数据结构调整
        # 假设从summary_data中提取线程信息
        thread_data = summary_data.get('threads', [])
        
        for thread in thread_data[:5]:  # 取前5个重要线程
            # 根据实际数据结构调整字段名
            threads.append({
                'title': thread.get('subject', 'Unknown Thread')[:80] + '...',
                'message_count': len(thread.get('all_nodes', {})),
                'contributor': thread.get('root_node', {}).get('sender', 'Unknown').split('<')[0].strip(),
                'lore_url': thread.get('root_node', {}).get('lore_url', 'https://lore.kernel.org/kvmarm/')
            })
        
        return threads


class TelegramNotifier:
    """Telegram通知器"""
    
    def __init__(self, config: NotificationConfig):
        self.config = config
        self.bot_token = config.telegram_bot_token
        self.chat_id = config.telegram_chat_id
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def send_summary_notification(self, summary_data: Dict[str, Any]) -> bool:
        """发送总结通知到Telegram"""
        try:
            message = self._build_summary_message(summary_data)
            
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    logger.info("✅ Telegram通知发送成功")
                    return True
                else:
                    logger.error(f"❌ Telegram通知发送失败: {result.get('description')}")
            else:
                logger.error(f"❌ Telegram通知HTTP错误: {response.status_code}")
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Telegram通知发送异常: {e}")
            return False
    
    def _build_summary_message(self, summary_data: Dict[str, Any]) -> str:
        """构建Telegram消息内容"""
        stats = summary_data.get('overview', {})
        total_messages = stats.get('total_messages', 0)
        total_threads = stats.get('total_threads', 0)
        contributors = stats.get('unique_contributors', 0)
        date_range = stats.get('date_range', ['', ''])
        
        message = f"""📊 *ARM KVM 邮件列表周报*

📅 *时间范围*: {date_range[0][:10]} 至 {date_range[1][:10]}

📧 *邮件统计*: {total_messages} 封邮件，{total_threads} 个线程
👥 *贡献者*: {contributors} 位开发者参与

🔥 *重要线程*:
"""
        
        # 添加重要线程
        important_threads = self._get_important_threads(summary_data)
        for i, thread in enumerate(important_threads[:5], 1):
            message += f"{i}. {thread['title']}\n"
            message += f"   📄 {thread['message_count']} 封邮件 | 👤 {thread['contributor']}\n"
            message += f"   🔗 [查看详情]({thread['lore_url']})\n\n"
        
        message += f"📖 [查看完整报告](https://lore.kernel.org/kvmarm/)\n"
        message += f"📊 [项目仓库](https://github.com/your-repo/kvmarm-ai-mailist)"
        
        return message
    
    def _get_important_threads(self, summary_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """提取重要线程信息（与Lark相同的逻辑）"""
        threads = []
        thread_data = summary_data.get('threads', [])
        
        for thread in thread_data[:5]:
            threads.append({
                'title': thread.get('subject', 'Unknown Thread')[:60] + '...',
                'message_count': len(thread.get('all_nodes', {})),
                'contributor': thread.get('root_node', {}).get('sender', 'Unknown').split('<')[0].strip(),
                'lore_url': thread.get('root_node', {}).get('lore_url', 'https://lore.kernel.org/kvmarm/')
            })
        
        return threads


class EmailNotifier:
    """邮件通知器"""
    
    def __init__(self, config: NotificationConfig):
        self.config = config
        self.smtp_server = config.smtp_server
        self.smtp_port = config.smtp_port
        self.user = config.email_user
        self.password = config.email_password
        self.recipients = [r.strip() for r in config.email_recipients if r.strip()]
    
    def send_summary_notification(self, summary_data: Dict[str, Any], 
                                 attachments: Optional[List[str]] = None) -> bool:
        """发送总结通知邮件"""
        try:
            stats = summary_data.get('overview', {})
            date_range = stats.get('date_range', ['', ''])
            
            subject = f"ARM KVM 邮件列表周报 - {date_range[0][:10]} 至 {date_range[1][:10]}"
            
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.user
            msg['To'] = ', '.join(self.recipients)
            
            # HTML内容
            html_content = self._build_html_content(summary_data)
            html_part = MIMEText(html_content, 'html', 'utf-8')
            
            # 纯文本内容
            text_content = self._build_text_content(summary_data)
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # 添加附件
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        self._add_attachment(msg, file_path)
            
            # 发送邮件
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.send_message(msg)
            
            logger.info(f"✅ 邮件通知发送成功，收件人: {len(self.recipients)}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 邮件通知发送异常: {e}")
            return False
    
    def _build_html_content(self, summary_data: Dict[str, Any]) -> str:
        """构建HTML邮件内容"""
        stats = summary_data.get('overview', {})
        total_messages = stats.get('total_messages', 0)
        total_threads = stats.get('total_threads', 0)
        contributors = stats.get('unique_contributors', 0)
        date_range = stats.get('date_range', ['', ''])
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>ARM KVM 邮件列表周报</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }}
        .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .stats {{ background-color: #e8f4f8; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
        .thread {{ border-left: 4px solid #007acc; padding-left: 15px; margin-bottom: 15px; }}
        .thread-title {{ font-weight: bold; color: #007acc; }}
        .thread-meta {{ color: #666; font-size: 0.9em; }}
        .footer {{ border-top: 1px solid #ddd; padding-top: 15px; margin-top: 30px; color: #666; }}
        a {{ color: #007acc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 ARM KVM 邮件列表周报</h1>
        <p><strong>时间范围</strong>: {date_range[0][:10]} 至 {date_range[1][:10]}</p>
    </div>
    
    <div class="stats">
        <h2>📈 统计摘要</h2>
        <ul>
            <li><strong>邮件总数</strong>: {total_messages} 封</li>
            <li><strong>讨论线程</strong>: {total_threads} 个</li>
            <li><strong>参与贡献者</strong>: {contributors} 位</li>
        </ul>
    </div>
    
    <h2>🔥 重要线程</h2>
"""
        
        # 添加重要线程
        important_threads = self._get_important_threads(summary_data)
        for i, thread in enumerate(important_threads[:5], 1):
            html += f"""
    <div class="thread">
        <div class="thread-title">{i}. {thread['title']}</div>
        <div class="thread-meta">
            📄 {thread['message_count']} 封邮件 | 
            👤 {thread['contributor']} | 
            <a href="{thread['lore_url']}" target="_blank">🔗 查看详情</a>
        </div>
    </div>
"""
        
        html += f"""
    <div class="footer">
        <p>
            <a href="https://lore.kernel.org/kvmarm/" target="_blank">📖 查看完整报告</a> | 
            <a href="https://github.com/your-repo/kvmarm-ai-mailist" target="_blank">📊 项目仓库</a>
        </p>
        <p><em>本报告由 ARM KVM Mail Analyzer 自动生成</em></p>
    </div>
</body>
</html>
"""
        return html
    
    def _build_text_content(self, summary_data: Dict[str, Any]) -> str:
        """构建纯文本邮件内容"""
        stats = summary_data.get('overview', {})
        total_messages = stats.get('total_messages', 0)
        total_threads = stats.get('total_threads', 0)
        contributors = stats.get('unique_contributors', 0)
        date_range = stats.get('date_range', ['', ''])
        
        text = f"""ARM KVM 邮件列表周报

时间范围: {date_range[0][:10]} 至 {date_range[1][:10]}

== 统计摘要 ==
邮件总数: {total_messages} 封
讨论线程: {total_threads} 个
参与贡献者: {contributors} 位

== 重要线程 ==
"""
        
        # 添加重要线程
        important_threads = self._get_important_threads(summary_data)
        for i, thread in enumerate(important_threads[:5], 1):
            text += f"""
{i}. {thread['title']}
   📄 {thread['message_count']} 封邮件 | 👤 {thread['contributor']}
   🔗 {thread['lore_url']}
"""
        
        text += f"""

== 链接 ==
📖 完整报告: https://lore.kernel.org/kvmarm/
📊 项目仓库: https://github.com/your-repo/kvmarm-ai-mailist

---
本报告由 ARM KVM Mail Analyzer 自动生成
"""
        return text
    
    def _get_important_threads(self, summary_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """提取重要线程信息（与其他通知器相同的逻辑）"""
        threads = []
        thread_data = summary_data.get('threads', [])
        
        for thread in thread_data[:5]:
            threads.append({
                'title': thread.get('subject', 'Unknown Thread')[:80],
                'message_count': len(thread.get('all_nodes', {})),
                'contributor': thread.get('root_node', {}).get('sender', 'Unknown').split('<')[0].strip(),
                'lore_url': thread.get('root_node', {}).get('lore_url', 'https://lore.kernel.org/kvmarm/')
            })
        
        return threads
    
    def _add_attachment(self, msg: MIMEMultipart, file_path: str):
        """添加邮件附件"""
        try:
            with open(file_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(file_path)}'
                )
                msg.attach(part)
        except Exception as e:
            logger.warning(f"⚠️ 添加附件失败 {file_path}: {e}")


class NotificationManager:
    """通知管理器 - 统一管理所有通知平台"""
    
    def __init__(self):
        self.config = NotificationConfig()
        self.notifiers = {}
        
        # 初始化各平台通知器
        if self.config.is_configured('lark'):
            self.notifiers['lark'] = LarkNotifier(self.config)
            logger.info("✅ Lark通知器已启用")
        
        if self.config.is_configured('telegram'):
            self.notifiers['telegram'] = TelegramNotifier(self.config)
            logger.info("✅ Telegram通知器已启用")
        
        if self.config.is_configured('email'):
            self.notifiers['email'] = EmailNotifier(self.config)
            logger.info("✅ Email通知器已启用")
        
        if not self.notifiers:
            logger.warning("⚠️ 未配置任何通知平台")
    
    def send_weekly_summary(self, results_dir: str) -> Dict[str, bool]:
        """发送周报通知到所有已配置的平台"""
        results = {}
        
        # 加载分析结果数据
        try:
            summary_data = self._load_summary_data(results_dir)
            if not summary_data:
                logger.error("❌ 无法加载分析结果数据")
                return results
        except Exception as e:
            logger.error(f"❌ 加载分析结果失败: {e}")
            return results
        
        # 发送到各平台
        for platform, notifier in self.notifiers.items():
            try:
                logger.info(f"📤 正在发送{platform}通知...")
                
                if platform == 'email':
                    # 邮件可以包含附件
                    attachments = self._get_attachment_files(results_dir)
                    success = notifier.send_summary_notification(summary_data, attachments)
                else:
                    success = notifier.send_summary_notification(summary_data)
                
                results[platform] = success
                
                if success:
                    logger.info(f"✅ {platform}通知发送成功")
                else:
                    logger.error(f"❌ {platform}通知发送失败")
                    
            except Exception as e:
                logger.error(f"❌ {platform}通知发送异常: {e}")
                results[platform] = False
        
        return results
    
    def _load_summary_data(self, results_dir: str) -> Optional[Dict[str, Any]]:
        """加载分析结果数据"""
        # 尝试加载主要的分析结果文件
        json_files = [
            'arm_kvm_analysis.json',
            'statistics.json'
        ]
        
        summary_data = {}
        
        for json_file in json_files:
            file_path = os.path.join(results_dir, json_file)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        summary_data.update(data)
                except Exception as e:
                    logger.warning(f"⚠️ 读取{json_file}失败: {e}")
        
        return summary_data if summary_data else None
    
    def _get_attachment_files(self, results_dir: str) -> List[str]:
        """获取邮件附件文件列表"""
        attachments = []
        
        # 可以作为附件的文件
        attachment_files = [
            'analysis_report_zh.md',
            'weekly_report.txt',
            'statistics.json'
        ]
        
        for file_name in attachment_files:
            file_path = os.path.join(results_dir, file_name)
            if os.path.exists(file_path):
                # 检查文件大小，避免附件过大
                file_size = os.path.getsize(file_path)
                if file_size < 10 * 1024 * 1024:  # 小于10MB
                    attachments.append(file_path)
                else:
                    logger.warning(f"⚠️ 文件{file_name}过大，跳过附件")
        
        return attachments
    
    def test_all_notifications(self) -> Dict[str, bool]:
        """测试所有通知平台的连通性"""
        results = {}
        
        # 创建测试数据
        test_data = {
            'overview': {
                'total_messages': 5,
                'total_threads': 2,
                'unique_contributors': 3,
                'date_range': ['2025-07-06T00:00:00+00:00', '2025-07-06T23:59:59+00:00']
            },
            'threads': [
                {
                    'subject': '[TEST] 测试通知功能',
                    'all_nodes': [1, 2, 3],
                    'root_node': {
                        'sender': 'Test User <test@example.com>',
                        'lore_url': 'https://lore.kernel.org/kvmarm/test-message-id/'
                    }
                }
            ]
        }
        
        for platform, notifier in self.notifiers.items():
            try:
                logger.info(f"🧪 测试{platform}通知...")
                success = notifier.send_summary_notification(test_data)
                results[platform] = success
                
                if success:
                    logger.info(f"✅ {platform}通知测试成功")
                else:
                    logger.error(f"❌ {platform}通知测试失败")
                    
            except Exception as e:
                logger.error(f"❌ {platform}通知测试异常: {e}")
                results[platform] = False
        
        return results


# 命令行工具
if __name__ == "__main__":
    import argparse
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description="ARM KVM 邮件列表通知发送工具")
    parser.add_argument('--test', action='store_true', help='测试所有通知平台')
    parser.add_argument('--send', type=str, help='发送周报通知，指定结果目录')
    parser.add_argument('--platform', type=str, choices=['lark', 'telegram', 'email'], 
                       help='指定特定平台进行操作')
    
    args = parser.parse_args()
    
    manager = NotificationManager()
    
    if args.test:
        print("🧪 开始测试所有通知平台...")
        results = manager.test_all_notifications()
        
        print("\n📊 测试结果:")
        for platform, success in results.items():
            status = "✅ 成功" if success else "❌ 失败"
            print(f"   {platform}: {status}")
    
    elif args.send:
        if not os.path.exists(args.send):
            print(f"❌ 结果目录不存在: {args.send}")
            exit(1)
        
        print(f"📤 开始发送周报通知，结果目录: {args.send}")
        results = manager.send_weekly_summary(args.send)
        
        print("\n📊 发送结果:")
        for platform, success in results.items():
            status = "✅ 成功" if success else "❌ 失败"
            print(f"   {platform}: {status}")
    
    else:
        parser.print_help()