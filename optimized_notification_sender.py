#!/usr/bin/env python3
"""
优化的通知发送模块
解决Gmail 102KB限制和飞书内容长度问题
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
import re
from notification_sender import NotificationConfig

logger = logging.getLogger(__name__)


class OptimizedEmailNotifier:
    """优化的邮件通知器 - 遵守Gmail 102KB限制"""
    
    def __init__(self, config: NotificationConfig):
        self.config = config
        self.smtp_server = config.smtp_server
        self.smtp_port = config.smtp_port
        self.user = config.email_user
        self.password = config.email_password
        self.recipients = [r.strip() for r in config.email_recipients if r.strip()]
        
        # Gmail 102KB限制，留出安全边距
        self.max_content_size = 95 * 1024  # 95KB
    
    def send_summary_notification(self, summary_data: Dict[str, Any], 
                                 attachments: Optional[List[str]] = None) -> bool:
        """发送优化的邮件通知，遵守Gmail限制"""
        try:
            stats = summary_data.get('overview', {})
            date_range = stats.get('date_range', ['', ''])
            
            subject = f"ARM KVM 邮件列表周报 - {date_range[0][:10]} 至 {date_range[1][:10]}"
            
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.user
            msg['To'] = ', '.join(self.recipients)
            
            # 构建优化的HTML内容
            html_content = self._build_optimized_html_content(summary_data)
            
            # 检查大小并优化
            if len(html_content.encode('utf-8')) > self.max_content_size:
                logger.warning(f"邮件内容超过{self.max_content_size//1024}KB，进行压缩优化")
                html_content = self._compress_html_content(html_content, summary_data)
            
            html_part = MIMEText(html_content, 'html', 'utf-8')
            
            # 简化的纯文本内容
            text_content = self._build_optimized_text_content(summary_data)
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # 添加重要附件（限制数量）
            if attachments:
                important_attachments = self._select_important_attachments(attachments)
                for file_path in important_attachments:
                    if os.path.exists(file_path):
                        self._add_attachment(msg, file_path)
            
            # 检查最终邮件大小
            total_size = len(msg.as_string().encode('utf-8'))
            logger.info(f"邮件总大小: {total_size/1024:.1f}KB")
            
            if total_size > 102 * 1024:
                logger.warning("邮件可能会被Gmail截断，建议进一步优化")
            
            # 发送邮件
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.send_message(msg)
            
            logger.info(f"✅ 优化邮件通知发送成功，收件人: {len(self.recipients)}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 优化邮件通知发送异常: {e}")
            return False
    
    def _build_optimized_html_content(self, summary_data: Dict[str, Any]) -> str:
        """构建优化的HTML内容，最小化文件大小"""
        stats = summary_data.get('overview', {})
        total_messages = stats.get('total_messages', 0)
        total_threads = stats.get('total_threads', 0)
        contributors = stats.get('unique_contributors', 0)
        date_range = stats.get('date_range', ['', ''])
        threads = summary_data.get('threads', [])
        
        # 优化的CSS - 使用简化语法
        optimized_css = """
        body{font-family:Arial,sans-serif;line-height:1.6;margin:0;padding:20px;background:#f5f5f5}
        .container{max-width:800px;margin:0 auto;background:#fff;border-radius:10px;box-shadow:0 0 20px rgba(0,0,0,0.1);overflow:hidden}
        .header{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;padding:30px;text-align:center}
        .header h1{margin:0;font-size:28px}
        .header p{margin:10px 0 0 0;opacity:0.9}
        .content{padding:30px}
        .stats{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;padding:20px;border-radius:10px;margin-bottom:30px}
        .stats h2{margin-top:0}
        .stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;margin-top:15px}
        .stat-item{background:rgba(255,255,255,0.1);padding:15px;border-radius:8px;text-align:center}
        .stat-number{font-size:24px;font-weight:bold}
        .stat-label{font-size:14px;opacity:0.9}
        .thread{border:1px solid #e0e0e0;border-radius:8px;padding:20px;margin-bottom:20px;background:#fafafa}
        .thread-title{font-size:18px;font-weight:bold;color:#333;margin-bottom:10px}
        .thread-meta{color:#666;font-size:14px;line-height:1.5;margin-bottom:10px}
        .footer{border-top:1px solid #e0e0e0;padding:20px 30px;background:#f8f9fa;text-align:center;color:#666}
        a{color:#667eea;text-decoration:none}
        a:hover{text-decoration:underline}
        .highlight{background:#fff3cd;padding:15px;border-radius:8px;margin:20px 0}
        </style>
        """
        
        # 构建线程内容 - 限制数量和长度
        threads_html = ""
        max_threads = min(len(threads), 10)  # 最多显示10个线程
        
        for i, thread in enumerate(threads[:max_threads], 1):
            subject = thread.get('subject', 'Unknown Subject')[:100]  # 限制标题长度
            message_count = len(thread.get('all_nodes', []))
            root_node = thread.get('root_node', {})
            sender = root_node.get('sender', 'Unknown Sender')
            lore_url = root_node.get('lore_url', '#')
            date = root_node.get('date', '')
            
            # 简化发送者信息
            if '<' in sender:
                sender_name = sender.split('<')[0].strip()[:30]  # 限制长度
            else:
                sender_name = sender[:30]
            
            threads_html += f"""
            <div class="thread">
                <div class="thread-title">{i}. {subject}</div>
                <div class="thread-meta">
                    <strong>📄</strong> {message_count} 封邮件 | 
                    <strong>👤</strong> {sender_name} | 
                    <strong>📅</strong> {date[:10] if date else 'Unknown'} | 
                    <strong>🔗</strong> <a href="{lore_url}" target="_blank">查看详情</a>
                </div>
            </div>
            """
        
        # 如果有更多线程，显示提示
        if len(threads) > max_threads:
            threads_html += f"""
            <div class="highlight">
                <strong>📌 注意</strong>: 还有 {len(threads) - max_threads} 个线程未显示。
                <a href="https://lore.kernel.org/kvmarm/" target="_blank">查看完整列表</a>
            </div>
            """
        
        # 构建完整HTML - 使用简化结构
        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>ARM KVM 邮件列表周报</title>
<style>{optimized_css}</style>
</head>
<body>
<div class="container">
<div class="header">
<h1>📊 ARM KVM 邮件列表周报</h1>
<p>{date_range[0][:10]} 至 {date_range[1][:10]}</p>
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
<strong>📌 重要提示</strong>: 本报告包含ARM KVM邮件列表的重要技术讨论和开发动态。
</div>
<h2>🔥 重要线程</h2>
{threads_html}
<div class="highlight">
<h3>📚 相关资源</h3>
<p>
<a href="https://lore.kernel.org/kvmarm/" target="_blank">ARM KVM邮件归档</a> | 
<a href="https://www.kernel.org/" target="_blank">Linux内核主页</a> | 
<a href="https://developer.arm.com/" target="_blank">ARM开发者资源</a>
</p>
</div>
</div>
<div class="footer">
<p>🤖 由ARM KVM分析系统自动生成 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</div>
</div>
</body>
</html>"""
        
        return html
    
    def _compress_html_content(self, html_content: str, summary_data: Dict[str, Any]) -> str:
        """压缩HTML内容以符合大小限制"""
        logger.info("开始压缩HTML内容...")
        
        # 移除多余的空白字符
        html_content = re.sub(r'\s+', ' ', html_content)
        html_content = re.sub(r'>\s+<', '><', html_content)
        
        # 如果仍然太大，创建简化版本
        if len(html_content.encode('utf-8')) > self.max_content_size:
            logger.warning("创建简化版本邮件")
            return self._build_simplified_html_content(summary_data)
        
        return html_content
    
    def _build_simplified_html_content(self, summary_data: Dict[str, Any]) -> str:
        """构建简化版HTML内容"""
        stats = summary_data.get('overview', {})
        total_messages = stats.get('total_messages', 0)
        total_threads = stats.get('total_threads', 0)
        contributors = stats.get('unique_contributors', 0)
        date_range = stats.get('date_range', ['', ''])
        threads = summary_data.get('threads', [])
        
        # 极简CSS
        minimal_css = "body{font-family:Arial;padding:20px}h1{color:#333}table{border-collapse:collapse;width:100%}th,td{border:1px solid #ddd;padding:8px;text-align:left}th{background:#f2f2f2}a{color:#0066cc}"
        
        # 只显示前5个最重要的线程
        threads_rows = ""
        for i, thread in enumerate(threads[:5], 1):
            subject = thread.get('subject', 'Unknown')[:60]  # 更短的标题
            message_count = len(thread.get('all_nodes', []))
            root_node = thread.get('root_node', {})
            sender = root_node.get('sender', 'Unknown')
            lore_url = root_node.get('lore_url', '#')
            
            # 简化发送者
            sender_name = sender.split('<')[0].strip()[:20] if '<' in sender else sender[:20]
            
            threads_rows += f"<tr><td>{i}</td><td>{subject}</td><td>{message_count}</td><td>{sender_name}</td><td><a href='{lore_url}'>查看</a></td></tr>"
        
        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>ARM KVM 周报</title>
<style>{minimal_css}</style>
</head>
<body>
<h1>📊 ARM KVM 邮件列表周报</h1>
<p><strong>时间</strong>: {date_range[0][:10]} 至 {date_range[1][:10]}</p>
<h2>📈 统计</h2>
<p>📧 {total_messages} 封邮件 | 🌳 {total_threads} 个线程 | 👥 {contributors} 位贡献者</p>
<h2>🔥 重要线程</h2>
<table>
<tr><th>#</th><th>主题</th><th>邮件数</th><th>发起者</th><th>链接</th></tr>
{threads_rows}
</table>
<p><strong>📚 更多信息</strong>: <a href="https://lore.kernel.org/kvmarm/">ARM KVM邮件归档</a></p>
<p><em>🤖 由ARM KVM分析系统生成 - {datetime.now().strftime('%Y-%m-%d %H:%M')}</em></p>
</body>
</html>"""
        
        return html
    
    def _build_optimized_text_content(self, summary_data: Dict[str, Any]) -> str:
        """构建优化的纯文本内容"""
        stats = summary_data.get('overview', {})
        total_messages = stats.get('total_messages', 0)
        total_threads = stats.get('total_threads', 0)
        contributors = stats.get('unique_contributors', 0)
        date_range = stats.get('date_range', ['', ''])
        threads = summary_data.get('threads', [])
        
        text = f"""📊 ARM KVM 邮件列表周报
{'-' * 40}

📅 时间范围: {date_range[0][:10]} 至 {date_range[1][:10]}

📈 统计摘要:
• 📧 邮件总数: {total_messages} 封
• 🌳 讨论线程: {total_threads} 个
• 👥 参与贡献者: {contributors} 位

🔥 重要线程:
"""
        
        # 限制线程数量
        for i, thread in enumerate(threads[:8], 1):
            subject = thread.get('subject', 'Unknown Subject')[:80]
            message_count = len(thread.get('all_nodes', []))
            root_node = thread.get('root_node', {})
            sender = root_node.get('sender', 'Unknown')
            lore_url = root_node.get('lore_url', '#')
            
            sender_name = sender.split('<')[0].strip()[:25] if '<' in sender else sender[:25]
            
            text += f"""
{i}. {subject}
   📄 {message_count} 封邮件 | 👤 {sender_name}
   🔗 {lore_url}
"""
        
        if len(threads) > 8:
            text += f"\n... 还有 {len(threads) - 8} 个线程\n"
        
        text += f"""
📚 更多信息: https://lore.kernel.org/kvmarm/
🤖 由ARM KVM分析系统生成 - {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
        return text
    
    def _select_important_attachments(self, attachments: List[str]) -> List[str]:
        """选择重要的附件，避免邮件过大"""
        important_files = ['statistics.json', 'analysis_report_zh.md']
        selected = []
        
        for file_path in attachments:
            file_name = os.path.basename(file_path)
            if file_name in important_files and len(selected) < 2:  # 最多2个附件
                selected.append(file_path)
        
        return selected
    
    def _add_attachment(self, msg, file_path: str):
        """添加邮件附件"""
        try:
            # 检查文件大小，避免过大附件
            file_size = os.path.getsize(file_path)
            if file_size > 5 * 1024 * 1024:  # 5MB限制
                logger.warning(f"附件过大，跳过: {file_path}")
                return
            
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


class OptimizedLarkNotifier:
    """优化的飞书通知器 - 解决内容长度限制"""
    
    def __init__(self, config: NotificationConfig):
        self.config = config
        self.webhook_url = config.lark_webhook
        self.secret = config.lark_secret
        
        # 飞书卡片内容限制 (经验值)
        self.max_card_content = 4000  # 字符数限制
    
    def send_summary_notification(self, summary_data: Dict[str, Any]) -> bool:
        """发送优化的飞书通知"""
        try:
            # 发送主要信息卡片
            main_success = self._send_main_card(summary_data)
            
            # 发送线程列表（可能分多个卡片）
            threads_success = self._send_threads_cards(summary_data)
            
            success = main_success and threads_success
            
            if success:
                logger.info("✅ 飞书优化通知发送成功")
            else:
                logger.warning("⚠️ 飞书通知部分发送失败")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ 飞书优化通知发送异常: {e}")
            return False
    
    def _send_main_card(self, summary_data: Dict[str, Any]) -> bool:
        """发送主要信息卡片"""
        stats = summary_data.get('overview', {})
        total_messages = stats.get('total_messages', 0)
        total_threads = stats.get('total_threads', 0)
        contributors = stats.get('unique_contributors', 0)
        date_range = stats.get('date_range', ['', ''])
        
        card = {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "blue",
                "title": {"content": "📊 ARM KVM 邮件列表周报", "tag": "text"}
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "content": f"**📅 时间范围**: {date_range[0][:10]} 至 {date_range[1][:10]}\n\n"
                                 f"**📧 邮件统计**: {total_messages} 封邮件，{total_threads} 个线程\n\n"
                                 f"**👥 贡献者**: {contributors} 位开发者参与\n\n"
                                 f"**🕒 生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                                 f"**📚 详细信息**: 请查看后续卡片或访问 [ARM KVM邮件归档](https://lore.kernel.org/kvmarm/)",
                        "tag": "lark_md"
                    }
                }
            ]
        }
        
        return self._send_card(card)
    
    def _send_threads_cards(self, summary_data: Dict[str, Any]) -> bool:
        """发送线程信息卡片（分批发送）"""
        threads = summary_data.get('threads', [])
        
        if not threads:
            return True
        
        # 每个卡片最多2个线程，确保不超过长度限制
        threads_per_card = 2
        success_count = 0
        total_cards = (len(threads) + threads_per_card - 1) // threads_per_card
        
        for i in range(0, len(threads), threads_per_card):
            batch_threads = threads[i:i + threads_per_card]
            card_number = (i // threads_per_card) + 1
            
            # 构建线程内容，严格控制长度
            elements = []
            
            for j, thread in enumerate(batch_threads):
                thread_num = i + j + 1
                subject = thread.get('subject', 'Unknown Subject')[:80]  # 限制标题长度
                message_count = len(thread.get('all_nodes', []))
                root_node = thread.get('root_node', {})
                sender = root_node.get('sender', 'Unknown Sender')
                lore_url = root_node.get('lore_url', '#')
                date = root_node.get('date', '')
                
                # 简化发送者信息
                sender_name = sender.split('<')[0].strip()[:20] if '<' in sender else sender[:20]
                
                # 构建线程内容，控制长度
                thread_content = f"**{thread_num}. {subject}**\n\n"
                thread_content += f"📄 **邮件**: {message_count} 封\n"
                thread_content += f"👤 **发起者**: {sender_name}\n"
                thread_content += f"📅 **日期**: {date[:10] if date else 'Unknown'}\n"
                thread_content += f"🔗 [查看详情]({lore_url})"
                
                elements.append({
                    "tag": "div",
                    "text": {"content": thread_content, "tag": "lark_md"}
                })
                
                # 添加分隔线（除了最后一个）
                if j < len(batch_threads) - 1:
                    elements.append({"tag": "hr"})
            
            card = {
                "config": {"wide_screen_mode": True},
                "header": {
                    "template": "green",
                    "title": {"content": f"🔥 重要线程 ({card_number}/{total_cards})", "tag": "text"}
                },
                "elements": elements
            }
            
            if self._send_card(card):
                success_count += 1
            
            # 避免发送过快
            import time
            time.sleep(0.5)
        
        return success_count == total_cards
    
    def _send_card(self, card: Dict[str, Any]) -> bool:
        """发送单个卡片，检查内容大小"""
        try:
            payload = {"msg_type": "interactive", "card": card}
            
            # 检查payload大小
            payload_size = len(json.dumps(payload, ensure_ascii=False))
            if payload_size > 50000:  # 50KB限制
                logger.warning(f"飞书卡片内容过大: {payload_size} bytes")
                return False
            
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


class OptimizedNotificationManager:
    """优化的通知管理器"""
    
    def __init__(self):
        self.config = NotificationConfig()
        self.notifiers = {}
        
        # 初始化优化通知器
        if self.config.is_configured('lark'):
            self.notifiers['lark'] = OptimizedLarkNotifier(self.config)
            logger.info("✅ 优化Lark通知器已启用")
        
        if self.config.is_configured('email'):
            self.notifiers['email'] = OptimizedEmailNotifier(self.config)
            logger.info("✅ 优化Email通知器已启用")
        
        # Telegram 保持原有实现
        if self.config.is_configured('telegram'):
            from notification_sender import TelegramNotifier
            self.notifiers['telegram'] = TelegramNotifier(self.config)
            logger.info("✅ Telegram通知器已启用")
        
        if not self.notifiers:
            logger.warning("⚠️ 未配置任何通知平台")
    
    def send_optimized_summary(self, results_dir: str) -> Dict[str, bool]:
        """发送优化的通知，遵守各平台限制"""
        logger.info("📤 正在发送优化通知（遵守平台限制）...")
        
        results = {}
        summary_data = self._load_summary_data(results_dir)
        
        if not summary_data:
            logger.error("❌ 无法加载分析数据")
            return {}
        
        # 获取附件文件
        attachments = self._get_attachment_files(results_dir)
        
        for platform, notifier in self.notifiers.items():
            logger.info(f"📤 正在发送{platform}优化通知...")
            try:
                if platform == 'email':
                    success = notifier.send_summary_notification(summary_data, attachments)
                else:
                    success = notifier.send_summary_notification(summary_data)
                
                results[platform] = success
                
                if success:
                    logger.info(f"✅ {platform}优化通知发送成功")
                else:
                    logger.error(f"❌ {platform}优化通知发送失败")
                    
            except Exception as e:
                logger.error(f"❌ {platform}优化通知发送异常: {e}")
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
            'statistics.json',
            'analysis_report_zh.md'
        ]
        
        for file_name in attachment_files:
            file_path = os.path.join(results_dir, file_name)
            if os.path.exists(file_path):
                attachments.append(file_path)
        
        return attachments


if __name__ == "__main__":
    # 测试优化通知功能
    from dotenv import load_dotenv
    load_dotenv()
    
    print("🧪 测试优化通知功能（遵守平台限制）")
    print("=" * 50)
    
    manager = OptimizedNotificationManager()
    
    if manager.notifiers:
        # 使用测试数据
        test_results = manager.send_optimized_summary("test_notification_results/2025-07-06")
        
        print("\n📊 优化通知发送结果:")
        for platform, success in test_results.items():
            status = "✅ 成功" if success else "❌ 失败"
            print(f"   {platform}: {status}")
            
        print("\n💡 优化特性:")
        print("   📧 邮件: 遵守Gmail 102KB限制，自动压缩")
        print("   📱 飞书: 分卡片发送，避免长度限制")
        print("   📱 Telegram: 保持原有优化格式")
        
    else:
        print("❌ 未配置任何通知平台")