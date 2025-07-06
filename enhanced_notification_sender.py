#!/usr/bin/env python3
"""
增强的通知发送模块
支持完整内容显示，突破长度限制
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
from notification_sender import NotificationConfig

logger = logging.getLogger(__name__)


class EnhancedLarkNotifier:
    """增强的飞书通知器 - 支持完整内容"""
    
    def __init__(self, config: NotificationConfig):
        self.config = config
        self.webhook_url = config.lark_webhook
        self.secret = config.lark_secret
    
    def send_summary_notification(self, summary_data: Dict[str, Any]) -> bool:
        """发送完整总结通知到飞书（分卡片发送）"""
        try:
            # 1. 发送概览卡片
            overview_success = self._send_overview_card(summary_data)
            
            # 2. 发送详细线程卡片（分批发送）
            threads_success = self._send_threads_details(summary_data)
            
            # 3. 发送附加信息卡片
            additional_success = self._send_additional_info(summary_data)
            
            success = overview_success and threads_success and additional_success
            
            if success:
                logger.info("✅ 飞书完整通知发送成功（多卡片）")
            else:
                logger.warning("⚠️ 飞书通知部分发送失败")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ 飞书增强通知发送异常: {e}")
            return False
    
    def _send_overview_card(self, summary_data: Dict[str, Any]) -> bool:
        """发送概览卡片"""
        stats = summary_data.get('overview', {})
        total_messages = stats.get('total_messages', 0)
        total_threads = stats.get('total_threads', 0)
        contributors = stats.get('unique_contributors', 0)
        date_range = stats.get('date_range', ['', ''])
        
        card = {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "blue",
                "title": {"content": "📊 ARM KVM 邮件列表周报 - 概览", "tag": "text"}
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "content": f"**📅 时间范围**: {date_range[0][:10]} 至 {date_range[1][:10]}\n\n"
                                 f"**📧 邮件统计**: {total_messages} 封邮件，{total_threads} 个线程\n\n"
                                 f"**👥 贡献者**: {contributors} 位开发者参与\n\n"
                                 f"**🕒 生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        "tag": "lark_md"
                    }
                }
            ]
        }
        
        return self._send_card(card)
    
    def _send_threads_details(self, summary_data: Dict[str, Any]) -> bool:
        """发送详细线程信息（可能分多个卡片）"""
        threads = summary_data.get('threads', [])
        
        if not threads:
            return True
        
        # 每个卡片最多显示3个线程
        threads_per_card = 3
        success_count = 0
        
        for i in range(0, len(threads), threads_per_card):
            batch_threads = threads[i:i + threads_per_card]
            card_number = (i // threads_per_card) + 1
            total_cards = (len(threads) + threads_per_card - 1) // threads_per_card
            
            card = {
                "config": {"wide_screen_mode": True},
                "header": {
                    "template": "green",
                    "title": {"content": f"🔥 重要线程详情 ({card_number}/{total_cards})", "tag": "text"}
                },
                "elements": []
            }
            
            for j, thread in enumerate(batch_threads):
                thread_num = i + j + 1
                subject = thread.get('subject', 'Unknown Subject')[:100]  # 限制标题长度
                message_count = len(thread.get('all_nodes', []))
                root_node = thread.get('root_node', {})
                sender = root_node.get('sender', 'Unknown Sender')
                lore_url = root_node.get('lore_url', '#')
                date = root_node.get('date', '')
                
                # 解析发送者名字
                sender_name = sender.split('<')[0].strip() if '<' in sender else sender
                
                thread_content = f"**{thread_num}. {subject}**\n\n"
                thread_content += f"📄 **邮件数量**: {message_count} 封\n"
                thread_content += f"👤 **发起者**: {sender_name}\n"
                thread_content += f"📅 **时间**: {date[:10] if date else 'Unknown'}\n"
                thread_content += f"🔗 **查看详情**: [点击跳转]({lore_url})"
                
                card["elements"].append({
                    "tag": "div",
                    "text": {"content": thread_content, "tag": "lark_md"}
                })
                
                # 添加分隔线（除了最后一个）
                if j < len(batch_threads) - 1:
                    card["elements"].append({"tag": "hr"})
            
            if self._send_card(card):
                success_count += 1
        
        return success_count == total_cards
    
    def _send_additional_info(self, summary_data: Dict[str, Any]) -> bool:
        """发送附加信息卡片"""
        card = {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "purple",
                "title": {"content": "📚 更多信息", "tag": "text"}
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "content": "**🔗 相关链接**:\n\n"
                                 "• [ARM KVM邮件归档](https://lore.kernel.org/kvmarm/)\n"
                                 "• [Linux内核主页](https://www.kernel.org/)\n"
                                 "• [ARM架构参考](https://developer.arm.com/)\n\n"
                                 "**📊 技术趋势**:\n"
                                 "本周重点关注ARM64新特性支持和KVM性能优化\n\n"
                                 "**🤖 系统信息**:\n"
                                 "由ARM KVM分析系统自动生成",
                        "tag": "lark_md"
                    }
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"content": "📖 查看完整归档", "tag": "plain_text"},
                            "type": "primary",
                            "url": "https://lore.kernel.org/kvmarm/"
                        }
                    ]
                }
            ]
        }
        
        return self._send_card(card)
    
    def _send_card(self, card: Dict[str, Any]) -> bool:
        """发送单个卡片"""
        try:
            payload = {"msg_type": "interactive", "card": card}
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    return True
                else:
                    logger.error(f"❌ 飞书卡片发送失败: {result.get('msg')}")
            else:
                logger.error(f"❌ 飞书HTTP错误: {response.status_code}")
            
            return False
            
        except Exception as e:
            logger.error(f"❌ 飞书卡片发送异常: {e}")
            return False


class EnhancedEmailNotifier:
    """增强的邮件通知器 - 支持完整内容"""
    
    def __init__(self, config: NotificationConfig):
        self.config = config
        self.smtp_server = config.smtp_server
        self.smtp_port = config.smtp_port
        self.user = config.email_user
        self.password = config.email_password
        self.recipients = [r.strip() for r in config.email_recipients if r.strip()]
    
    def send_summary_notification(self, summary_data: Dict[str, Any], 
                                 attachments: Optional[List[str]] = None) -> bool:
        """发送完整总结通知邮件"""
        try:
            stats = summary_data.get('overview', {})
            date_range = stats.get('date_range', ['', ''])
            
            subject = f"ARM KVM 邮件列表完整周报 - {date_range[0][:10]} 至 {date_range[1][:10]}"
            
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.user
            msg['To'] = ', '.join(self.recipients)
            
            # 完整HTML内容
            html_content = self._build_complete_html_content(summary_data)
            html_part = MIMEText(html_content, 'html', 'utf-8')
            
            # 完整纯文本内容
            text_content = self._build_complete_text_content(summary_data)
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
            
            logger.info(f"✅ 完整邮件通知发送成功，收件人: {len(self.recipients)}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 完整邮件通知发送异常: {e}")
            return False
    
    def _build_complete_html_content(self, summary_data: Dict[str, Any]) -> str:
        """构建完整HTML邮件内容"""
        stats = summary_data.get('overview', {})
        total_messages = stats.get('total_messages', 0)
        total_threads = stats.get('total_threads', 0)
        contributors = stats.get('unique_contributors', 0)
        date_range = stats.get('date_range', ['', ''])
        threads = summary_data.get('threads', [])
        
        # 详细的线程HTML
        threads_html = ""
        for i, thread in enumerate(threads, 1):
            subject = thread.get('subject', 'Unknown Subject')
            message_count = len(thread.get('all_nodes', []))
            root_node = thread.get('root_node', {})
            sender = root_node.get('sender', 'Unknown Sender')
            lore_url = root_node.get('lore_url', '#')
            date = root_node.get('date', '')
            
            # 解析发送者信息
            if '<' in sender:
                sender_name = sender.split('<')[0].strip()
                sender_email = sender.split('<')[1].replace('>', '').strip()
            else:
                sender_name = sender
                sender_email = ''
            
            threads_html += f"""
            <div class="thread">
                <div class="thread-title">{i}. {subject}</div>
                <div class="thread-meta">
                    <strong>📄 邮件数量</strong>: {message_count} 封<br>
                    <strong>👤 发起者</strong>: {sender_name} {f'({sender_email})' if sender_email else ''}<br>
                    <strong>📅 时间</strong>: {date[:19] if date else 'Unknown'}<br>
                    <strong>🔗 链接</strong>: <a href="{lore_url}" target="_blank">查看详情</a>
                </div>
                <div class="thread-description">
                    <p>这个线程包含 {message_count} 封邮件的讨论，涉及ARM KVM相关的技术开发和优化。</p>
                </div>
            </div>
            """
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ARM KVM 邮件列表完整周报</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            line-height: 1.6; 
            margin: 0; 
            padding: 20px; 
            background-color: #f5f5f5;
        }}
        .container {{ 
            max-width: 800px; 
            margin: 0 auto; 
            background-color: white; 
            border-radius: 10px; 
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            padding: 30px; 
            text-align: center; 
        }}
        .header h1 {{ margin: 0; font-size: 28px; }}
        .header p {{ margin: 10px 0 0 0; opacity: 0.9; }}
        .content {{ padding: 30px; }}
        .stats {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            padding: 20px; 
            border-radius: 10px; 
            margin-bottom: 30px; 
        }}
        .stats h2 {{ margin-top: 0; }}
        .stats-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 15px; 
            margin-top: 15px; 
        }}
        .stat-item {{ 
            background: rgba(255,255,255,0.1); 
            padding: 15px; 
            border-radius: 8px; 
            text-align: center; 
        }}
        .stat-number {{ font-size: 24px; font-weight: bold; }}
        .stat-label {{ font-size: 14px; opacity: 0.9; }}
        .threads-section {{ margin-top: 30px; }}
        .threads-section h2 {{ 
            color: #333; 
            border-bottom: 3px solid #667eea; 
            padding-bottom: 10px; 
        }}
        .thread {{ 
            border: 1px solid #e0e0e0; 
            border-radius: 8px; 
            padding: 20px; 
            margin-bottom: 20px; 
            background: #fafafa; 
        }}
        .thread-title {{ 
            font-size: 18px; 
            font-weight: bold; 
            color: #333; 
            margin-bottom: 10px; 
        }}
        .thread-meta {{ 
            color: #666; 
            font-size: 14px; 
            line-height: 1.5; 
            margin-bottom: 10px; 
        }}
        .thread-description {{ 
            color: #555; 
            font-style: italic; 
            margin-top: 10px; 
        }}
        .footer {{ 
            border-top: 1px solid #e0e0e0; 
            padding: 20px 30px; 
            background: #f8f9fa; 
            text-align: center; 
            color: #666; 
        }}
        a {{ color: #667eea; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .highlight {{ background: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 ARM KVM 邮件列表完整周报</h1>
            <p>时间范围: {date_range[0][:10]} 至 {date_range[1][:10]}</p>
        </div>
        
        <div class="content">
            <div class="stats">
                <h2>📈 统计摘要</h2>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-number">{total_messages}</div>
                        <div class="stat-label">封邮件</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">{total_threads}</div>
                        <div class="stat-label">个线程</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">{contributors}</div>
                        <div class="stat-label">位贡献者</div>
                    </div>
                </div>
            </div>
            
            <div class="highlight">
                <strong>📌 重要提示</strong>: 本报告包含了完整的ARM KVM邮件列表分析，
                涵盖了所有重要的技术讨论和开发动态。
            </div>
            
            <div class="threads-section">
                <h2>🔥 详细线程分析</h2>
                {threads_html}
            </div>
            
            <div class="highlight">
                <h3>📚 相关资源</h3>
                <ul>
                    <li><a href="https://lore.kernel.org/kvmarm/" target="_blank">ARM KVM邮件归档</a></li>
                    <li><a href="https://www.kernel.org/" target="_blank">Linux内核主页</a></li>
                    <li><a href="https://developer.arm.com/" target="_blank">ARM开发者资源</a></li>
                </ul>
            </div>
        </div>
        
        <div class="footer">
            <p>🤖 本报告由ARM KVM分析系统自动生成</p>
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def _build_complete_text_content(self, summary_data: Dict[str, Any]) -> str:
        """构建完整纯文本邮件内容"""
        stats = summary_data.get('overview', {})
        total_messages = stats.get('total_messages', 0)
        total_threads = stats.get('total_threads', 0)
        contributors = stats.get('unique_contributors', 0)
        date_range = stats.get('date_range', ['', ''])
        threads = summary_data.get('threads', [])
        
        text = f"""
📊 ARM KVM 邮件列表完整周报
{'=' * 50}

📅 时间范围: {date_range[0][:10]} 至 {date_range[1][:10]}
🕒 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📈 统计摘要
{'-' * 30}
📧 邮件总数: {total_messages} 封
🌳 讨论线程: {total_threads} 个
👥 参与贡献者: {contributors} 位

🔥 详细线程分析
{'-' * 30}
"""
        
        for i, thread in enumerate(threads, 1):
            subject = thread.get('subject', 'Unknown Subject')
            message_count = len(thread.get('all_nodes', []))
            root_node = thread.get('root_node', {})
            sender = root_node.get('sender', 'Unknown Sender')
            lore_url = root_node.get('lore_url', '#')
            date = root_node.get('date', '')
            
            text += f"""
{i}. {subject}
   📄 邮件数量: {message_count} 封
   👤 发起者: {sender}
   📅 时间: {date[:19] if date else 'Unknown'}
   🔗 链接: {lore_url}
   
"""
        
        text += f"""
📚 相关资源
{'-' * 30}
• ARM KVM邮件归档: https://lore.kernel.org/kvmarm/
• Linux内核主页: https://www.kernel.org/
• ARM开发者资源: https://developer.arm.com/

🤖 本报告由ARM KVM分析系统自动生成
"""
        return text
    
    def _add_attachment(self, msg, file_path: str):
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
            logger.warning(f"添加附件失败 {file_path}: {e}")


class EnhancedNotificationManager:
    """增强的通知管理器"""
    
    def __init__(self):
        self.config = NotificationConfig()
        self.notifiers = {}
        
        # 初始化增强通知器
        if self.config.is_configured('lark'):
            self.notifiers['lark'] = EnhancedLarkNotifier(self.config)
            logger.info("✅ 增强Lark通知器已启用")
        
        if self.config.is_configured('email'):
            self.notifiers['email'] = EnhancedEmailNotifier(self.config)
            logger.info("✅ 增强Email通知器已启用")
        
        # Telegram 保持原有实现（已经比较完整）
        if self.config.is_configured('telegram'):
            from notification_sender import TelegramNotifier
            self.notifiers['telegram'] = TelegramNotifier(self.config)
            logger.info("✅ Telegram通知器已启用")
        
        if not self.notifiers:
            logger.warning("⚠️ 未配置任何通知平台")
    
    def send_enhanced_summary(self, results_dir: str) -> Dict[str, bool]:
        """发送增强的完整通知"""
        logger.info("📤 正在发送增强通知...")
        
        results = {}
        summary_data = self._load_summary_data(results_dir)
        
        if not summary_data:
            logger.error("❌ 无法加载分析数据")
            return {}
        
        # 获取附件文件
        attachments = self._get_attachment_files(results_dir)
        
        for platform, notifier in self.notifiers.items():
            logger.info(f"📤 正在发送{platform}增强通知...")
            try:
                if platform == 'email':
                    success = notifier.send_summary_notification(summary_data, attachments)
                else:
                    success = notifier.send_summary_notification(summary_data)
                
                results[platform] = success
                
                if success:
                    logger.info(f"✅ {platform}增强通知发送成功")
                else:
                    logger.error(f"❌ {platform}增强通知发送失败")
                    
            except Exception as e:
                logger.error(f"❌ {platform}增强通知发送异常: {e}")
                results[platform] = False
        
        return results
    
    def _load_summary_data(self, results_dir: str) -> Optional[Dict[str, Any]]:
        """加载分析数据"""
        try:
            stats_file = os.path.join(results_dir, 'statistics.json')
            if os.path.exists(stats_file):
                with open(stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"加载分析数据失败: {e}")
        return None
    
    def _get_attachment_files(self, results_dir: str) -> List[str]:
        """获取附件文件列表"""
        attachments = []
        attachment_files = [
            'analysis_report_zh.md',
            'weekly_report.txt',
            'statistics.json'
        ]
        
        for file_name in attachment_files:
            file_path = os.path.join(results_dir, file_name)
            if os.path.exists(file_path):
                attachments.append(file_path)
        
        return attachments


if __name__ == "__main__":
    # 测试增强通知功能
    from dotenv import load_dotenv
    load_dotenv()
    
    print("🧪 测试增强通知功能")
    print("=" * 40)
    
    manager = EnhancedNotificationManager()
    
    if manager.notifiers:
        # 使用测试数据
        test_results = manager.send_enhanced_summary("test_notification_results/2025-07-06")
        
        print("\n📊 增强通知发送结果:")
        for platform, success in test_results.items():
            status = "✅ 成功" if success else "❌ 失败"
            print(f"   {platform}: {status}")
    else:
        print("❌ 未配置任何通知平台")