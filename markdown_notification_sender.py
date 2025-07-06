#!/usr/bin/env python3
"""
基于Markdown文件的通知发送器
直接使用生成的完美MD文件内容发送通知
"""

import os
import json
import logging
import requests
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from notification_sender import NotificationConfig

logger = logging.getLogger(__name__)


class MarkdownNotificationManager:
    """基于Markdown文件的通知管理器"""
    
    def __init__(self, github_pages_url: Optional[str] = None):
        self.config = NotificationConfig()
        self.github_pages_url = github_pages_url or "https://onlinefchen.github.io/kvmarm-robot"
        self.notifiers = {}
        
        # 初始化通知器
        if self.config.is_configured('lark'):
            self.notifiers['lark'] = MarkdownLarkNotifier(self.config, self.github_pages_url)
            logger.info("✅ Markdown Lark通知器已启用")
        
        if self.config.is_configured('email'):
            self.notifiers['email'] = MarkdownEmailNotifier(self.config, self.github_pages_url)
            logger.info("✅ Markdown Email通知器已启用")
        
        if self.config.is_configured('telegram'):
            self.notifiers['telegram'] = MarkdownTelegramNotifier(self.config, self.github_pages_url)
            logger.info("✅ Markdown Telegram通知器已启用")
        
        if not self.notifiers:
            logger.warning("⚠️ 未配置任何通知平台")
    
    def send_markdown_notifications(self, results_dir: str) -> Dict[str, bool]:
        """基于Markdown文件发送通知"""
        logger.info("📤 正在发送基于Markdown的通知...")
        
        results = {}
        
        # 查找Markdown文件
        markdown_file = self._find_markdown_file(results_dir)
        if not markdown_file:
            logger.error("❌ 未找到Markdown报告文件")
            return {}
        
        # 读取Markdown内容
        markdown_content = self._read_markdown_file(markdown_file)
        if not markdown_content:
            logger.error("❌ 无法读取Markdown文件内容")
            return {}
        
        # 解析Markdown内容
        parsed_content = self._parse_markdown_content(markdown_content)
        
        # 获取附件文件
        attachments = self._get_attachment_files(results_dir)
        
        for platform, notifier in self.notifiers.items():
            logger.info(f"📤 正在发送{platform} Markdown通知...")
            try:
                if platform == 'email':
                    success = notifier.send_markdown_notification(markdown_content, parsed_content, attachments)
                else:
                    success = notifier.send_markdown_notification(markdown_content, parsed_content)
                
                results[platform] = success
                
                if success:
                    logger.info(f"✅ {platform} Markdown通知发送成功")
                else:
                    logger.error(f"❌ {platform} Markdown通知发送失败")
                    
            except Exception as e:
                logger.error(f"❌ {platform} Markdown通知发送异常: {e}")
                results[platform] = False
        
        return results
    
    def _find_markdown_file(self, results_dir: str) -> Optional[str]:
        """查找Markdown报告文件"""
        possible_files = [
            'analysis_report_zh.md',
            'analysis_report_en.md', 
            'analysis_report.md',
            'weekly_report.md'
        ]
        
        for file_name in possible_files:
            file_path = os.path.join(results_dir, file_name)
            if os.path.exists(file_path):
                logger.info(f"📄 找到Markdown文件: {file_name}")
                return file_path
        
        return None
    
    def _read_markdown_file(self, file_path: str) -> Optional[str]:
        """读取Markdown文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"📖 成功读取Markdown文件，长度: {len(content)} 字符")
            return content
        except Exception as e:
            logger.error(f"❌ 读取Markdown文件失败: {e}")
            return None
    
    def _parse_markdown_content(self, markdown_content: str) -> Dict[str, Any]:
        """解析Markdown内容，提取关键信息"""
        parsed = {
            'title': '',
            'time_range': '',
            'statistics': {},
            'threads': [],
            'trends': '',
            'full_content': markdown_content
        }
        
        lines = markdown_content.split('\n')
        current_section = None
        current_thread = None
        
        for line in lines:
            line = line.strip()
            
            # 提取标题
            if line.startswith('# '):
                parsed['title'] = line[2:].strip()
            
            # 提取时间范围
            elif line.startswith('**时间范围**:'):
                parsed['time_range'] = line.replace('**时间范围**:', '').strip()
            
            # 提取统计信息
            elif line.startswith('- **邮件总数**:'):
                match = re.search(r'(\d+)', line)
                if match:
                    parsed['statistics']['total_messages'] = int(match.group(1))
            elif line.startswith('- **线程数量**:'):
                match = re.search(r'(\d+)', line)
                if match:
                    parsed['statistics']['total_threads'] = int(match.group(1))
            elif line.startswith('- **活跃贡献者**:'):
                match = re.search(r'(\d+)', line)
                if match:
                    parsed['statistics']['contributors'] = int(match.group(1))
            
            # 提取线程信息
            elif line.startswith('### ') and '. [' in line:
                if current_thread:
                    parsed['threads'].append(current_thread)
                
                # 解析线程标题
                thread_title = line[4:].strip()  # 移除 "### "
                current_thread = {
                    'title': thread_title,
                    'details': []
                }
            elif current_thread and line.startswith('- **'):
                current_thread['details'].append(line)
            
            # 提取技术趋势
            elif line.startswith('本周ARM KVM社区重点关注：'):
                current_section = 'trends'
                parsed['trends'] = line + '\n'
            elif current_section == 'trends' and (line.startswith('1.') or line.startswith('2.') or line.startswith('3.')):
                parsed['trends'] += line + '\n'
        
        # 添加最后一个线程
        if current_thread:
            parsed['threads'].append(current_thread)
        
        return parsed
    
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


class MarkdownLarkNotifier:
    """基于Markdown的飞书通知器"""
    
    def __init__(self, config: NotificationConfig, github_pages_url: str):
        self.config = config
        self.webhook_url = config.lark_webhook
        self.secret = config.lark_secret
        self.github_pages_url = github_pages_url
    
    def send_markdown_notification(self, markdown_content: str, parsed_content: Dict[str, Any]) -> bool:
        """发送基于Markdown的飞书通知"""
        try:
            # 发送概览卡片
            overview_success = self._send_overview_card(parsed_content)
            
            # 发送线程详情卡片
            threads_success = self._send_threads_cards(parsed_content)
            
            # 发送技术趋势卡片
            trends_success = self._send_trends_card(parsed_content)
            
            success = overview_success and threads_success and trends_success
            
            if success:
                logger.info("✅ 飞书Markdown通知发送成功")
            else:
                logger.warning("⚠️ 飞书Markdown通知部分发送失败")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ 飞书Markdown通知发送异常: {e}")
            return False
    
    def _send_overview_card(self, parsed: Dict[str, Any]) -> bool:
        """发送概览卡片"""
        stats = parsed.get('statistics', {})
        
        # 生成GitHub Pages URL
        date_str = datetime.now().strftime('%Y-%m-%d')
        pages_url = f"{self.github_pages_url}/reports/{date_str}/"
        
        card = {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "blue",
                "title": {"content": parsed.get('title', 'ARM KVM 邮件列表分析报告'), "tag": "text"}
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "content": f"**📅 时间范围**: {parsed.get('time_range', 'Unknown')}\n\n"
                                 f"**📧 邮件统计**: {stats.get('total_messages', 0)} 封邮件，{stats.get('total_threads', 0)} 个线程\n\n"
                                 f"**👥 活跃贡献者**: {stats.get('contributors', 0)} 位\n\n"
                                 f"**🕒 生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                                 f"**📄 完整报告**: [查看GitHub Pages]({pages_url})\n\n"
                                 f"**📚 详细信息**: 请查看后续卡片",
                        "tag": "lark_md"
                    }
                }
            ]
        }
        
        return self._send_card(card)
    
    def _send_threads_cards(self, parsed: Dict[str, Any]) -> bool:
        """发送线程详情卡片"""
        threads = parsed.get('threads', [])
        
        if not threads:
            return True
        
        # 每个卡片2个线程
        threads_per_card = 2
        success_count = 0
        total_cards = (len(threads) + threads_per_card - 1) // threads_per_card
        
        for i in range(0, len(threads), threads_per_card):
            batch_threads = threads[i:i + threads_per_card]
            card_number = (i // threads_per_card) + 1
            
            elements = []
            
            for j, thread in enumerate(batch_threads):
                thread_num = i + j + 1
                title = thread.get('title', 'Unknown Thread')
                details = thread.get('details', [])
                
                # 构建线程内容
                thread_content = f"**{thread_num}. {title}**\n\n"
                
                # 添加详情（限制长度）
                for detail in details[:4]:  # 最多4个详情
                    # 转换为飞书Markdown格式
                    detail_text = detail.replace('**', '*').replace('- **', '• **')
                    thread_content += f"{detail_text}\n"
                
                elements.append({
                    "tag": "div",
                    "text": {"content": thread_content.strip(), "tag": "lark_md"}
                })
                
                # 添加分隔线
                if j < len(batch_threads) - 1:
                    elements.append({"tag": "hr"})
            
            card = {
                "config": {"wide_screen_mode": True},
                "header": {
                    "template": "green",
                    "title": {"content": f"🔥 重要线程详情 ({card_number}/{total_cards})", "tag": "text"}
                },
                "elements": elements
            }
            
            if self._send_card(card):
                success_count += 1
            
            # 延迟避免发送过快
            import time
            time.sleep(0.5)
        
        return success_count == total_cards
    
    def _send_trends_card(self, parsed: Dict[str, Any]) -> bool:
        """发送技术趋势卡片"""
        trends = parsed.get('trends', '')
        
        if not trends:
            return True
        
        # 生成GitHub Pages URL
        date_str = datetime.now().strftime('%Y-%m-%d')
        pages_url = f"{self.github_pages_url}/reports/{date_str}/"
        
        card = {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "purple",
                "title": {"content": "🎯 技术趋势分析", "tag": "text"}
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "content": trends.strip() + "\n\n" +
                                 "**📚 相关资源**:\n" +
                                 "• [ARM KVM邮件归档](https://lore.kernel.org/kvmarm/)\n" +
                                 "• [Linux内核主页](https://www.kernel.org/)\n" +
                                 "• [ARM开发者资源](https://developer.arm.com/)\n" +
                                 f"• [完整HTML报告]({pages_url})",
                        "tag": "lark_md"
                    }
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"content": "📄 查看HTML报告", "tag": "plain_text"},
                            "type": "primary",
                            "url": pages_url
                        },
                        {
                            "tag": "button",
                            "text": {"content": "📧 邮件归档", "tag": "plain_text"},
                            "type": "default",
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


class MarkdownEmailNotifier:
    """基于Markdown的邮件通知器"""
    
    def __init__(self, config: NotificationConfig, github_pages_url: str):
        self.config = config
        self.smtp_server = config.smtp_server
        self.smtp_port = config.smtp_port
        self.user = config.email_user
        self.password = config.email_password
        self.recipients = [r.strip() for r in config.email_recipients if r.strip()]
        self.github_pages_url = github_pages_url
    
    def send_markdown_notification(self, markdown_content: str, parsed_content: Dict[str, Any], 
                                  attachments: Optional[List[str]] = None) -> bool:
        """发送基于Markdown的邮件通知"""
        try:
            title = parsed_content.get('title', 'ARM KVM 邮件列表分析报告')
            time_range = parsed_content.get('time_range', '')
            
            subject = f"{title} - {time_range}" if time_range else title
            
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.user
            msg['To'] = ', '.join(self.recipients)
            
            # 转换Markdown为HTML
            html_content = self._markdown_to_html(markdown_content, parsed_content)
            html_part = MIMEText(html_content, 'html', 'utf-8')
            
            # 纯文本版本（直接使用Markdown）
            text_part = MIMEText(markdown_content, 'plain', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # 添加附件
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        self._add_attachment(msg, file_path)
            
            # 检查邮件大小
            total_size = len(msg.as_string().encode('utf-8'))
            logger.info(f"邮件总大小: {total_size/1024:.1f}KB")
            
            # 发送邮件
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.send_message(msg)
            
            logger.info(f"✅ Markdown邮件通知发送成功，收件人: {len(self.recipients)}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Markdown邮件通知发送异常: {e}")
            return False
    
    def _markdown_to_html(self, markdown_content: str, parsed_content: Dict[str, Any]) -> str:
        """将Markdown转换为HTML"""
        try:
            # 使用markdown库转换
            import markdown
            html_body = markdown.markdown(markdown_content, extensions=['tables', 'codehilite'])
        except ImportError:
            # 如果没有markdown库，使用简单转换
            html_body = self._simple_markdown_to_html(markdown_content)
        
        # 添加CSS样式
        css = """
        <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
        .container { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; border-bottom: 2px solid #ecf0f1; padding-bottom: 8px; margin-top: 30px; }
        h3 { color: #2980b9; margin-top: 25px; }
        ul { margin: 15px 0; }
        li { margin: 8px 0; }
        strong { color: #2c3e50; }
        .stats { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #ecf0f1; text-align: center; color: #7f8c8d; }
        </style>
        """
        
        # 构建完整HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{parsed_content.get('title', 'ARM KVM Report')}</title>
            {css}
        </head>
        <body>
            <div class="container">
                {html_body}
                <div class="footer">
                    <p>🤖 由ARM KVM分析系统自动生成 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _simple_markdown_to_html(self, markdown_content: str) -> str:
        """简单的Markdown到HTML转换"""
        html = markdown_content
        
        # 标题转换
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        
        # 粗体转换
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        
        # 列表转换
        html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'(<li>.*</li>)', r'<ul>\1</ul>', html, flags=re.DOTALL)
        
        # 换行转换
        html = html.replace('\n', '<br>\n')
        
        return html
    
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


class MarkdownTelegramNotifier:
    """基于Markdown的Telegram通知器"""
    
    def __init__(self, config: NotificationConfig, github_pages_url: str):
        self.config = config
        self.bot_token = config.telegram_bot_token
        self.chat_id = config.telegram_chat_id
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.github_pages_url = github_pages_url
    
    def send_markdown_notification(self, markdown_content: str, parsed_content: Dict[str, Any]) -> bool:
        """发送基于Markdown的Telegram通知"""
        try:
            # 为Telegram优化Markdown格式
            telegram_content = self._optimize_for_telegram(markdown_content, parsed_content)
            
            # 分段发送（如果内容太长）
            max_length = 4000  # Telegram消息长度限制
            
            if len(telegram_content) <= max_length:
                return self._send_message(telegram_content)
            else:
                return self._send_long_message(telegram_content, max_length)
            
        except Exception as e:
            logger.error(f"❌ Telegram Markdown通知发送异常: {e}")
            return False
    
    def _optimize_for_telegram(self, markdown_content: str, parsed_content: Dict[str, Any]) -> str:
        """为Telegram优化Markdown格式"""
        # 简化格式，避免Telegram解析错误
        content = markdown_content
        
        # 移除可能导致解析错误的字符
        content = re.sub(r'\*\*', '*', content)  # 双星号改为单星号
        content = re.sub(r'`([^`]+)`', r'\1', content)  # 移除代码格式
        
        # 简化标题格式
        content = re.sub(r'^# (.+)$', r'📊 \1', content, flags=re.MULTILINE)
        content = re.sub(r'^## (.+)$', r'\n🔹 \1', content, flags=re.MULTILINE)
        content = re.sub(r'^### (.+)$', r'\n▫️ \1', content, flags=re.MULTILINE)
        
        # 生成GitHub Pages URL
        date_str = datetime.now().strftime('%Y-%m-%d')
        pages_url = f"{self.github_pages_url}/reports/{date_str}/"
        
        # 添加GitHub Pages链接
        content += f"\n\n📄 *完整HTML报告*: {pages_url}"
        content += f"\n🤖 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return content
    
    def _send_message(self, content: str) -> bool:
        """发送单条消息"""
        try:
            payload = {
                'chat_id': self.chat_id,
                'text': content,
                'disable_web_page_preview': False
            }
            
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    logger.info("✅ Telegram Markdown消息发送成功")
                    return True
                else:
                    logger.error(f"❌ Telegram发送失败: {result.get('description')}")
            else:
                logger.error(f"❌ Telegram HTTP错误: {response.status_code}")
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Telegram消息发送异常: {e}")
            return False
    
    def _send_long_message(self, content: str, max_length: int) -> bool:
        """分段发送长消息"""
        lines = content.split('\n')
        current_chunk = ""
        success_count = 0
        total_chunks = 0
        
        for line in lines:
            if len(current_chunk) + len(line) + 1 > max_length:
                if current_chunk:
                    total_chunks += 1
                    if self._send_message(current_chunk):
                        success_count += 1
                    current_chunk = line
                    
                    # 延迟避免发送过快
                    import time
                    time.sleep(0.5)
                else:
                    # 单行太长，截断
                    current_chunk = line[:max_length]
            else:
                current_chunk += "\n" + line if current_chunk else line
        
        # 发送最后一块
        if current_chunk:
            total_chunks += 1
            if self._send_message(current_chunk):
                success_count += 1
        
        logger.info(f"Telegram分段发送: {success_count}/{total_chunks} 成功")
        return success_count == total_chunks


if __name__ == "__main__":
    # 测试基于Markdown的通知功能
    from dotenv import load_dotenv
    load_dotenv()
    
    print("🧪 测试基于Markdown的通知功能")
    print("=" * 50)
    
    manager = MarkdownNotificationManager()
    
    if manager.notifiers:
        # 使用测试数据
        test_results = manager.send_markdown_notifications("test_notification_results/2025-07-06")
        
        print("\n📊 Markdown通知发送结果:")
        for platform, success in test_results.items():
            status = "✅ 成功" if success else "❌ 失败"
            print(f"   {platform}: {status}")
            
        print("\n💡 Markdown通知特性:")
        print("   📄 直接使用生成的完美MD文件")
        print("   📱 飞书: 解析MD内容生成多卡片")
        print("   📧 邮件: MD转HTML，保持完美格式")
        print("   📱 Telegram: 优化MD格式，支持长消息分段")
        
    else:
        print("❌ 未配置任何通知平台")