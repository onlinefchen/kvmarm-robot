import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from models import EmailForest, EmailThread, EmailNode


class ReportGenerator:
    def __init__(self, output_dir: str = "results", language: str = "zh"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.language = language
        
        # 创建时间戳目录
        self.timestamp = datetime.now().strftime("%Y-%m-%d")
        self.report_dir = self.output_dir / self.timestamp
        self.report_dir.mkdir(exist_ok=True)
        
        # 初始化多语言文本
        self._init_i18n()
    
    def _init_i18n(self):
        """初始化多语言文本"""
        self.texts = {
            "zh": {
                "report_title": "ARM KVM邮件列表分析报告",
                "period": "时间段",
                "total": "总计",
                "messages": "messages",  # 保持英文
                "threads": "threads",    # 保持英文
                "full_report": "完整报告",
                "thread_url": "线程URL",
                "ai_analysis": "AI分析摘要",
                "purpose": "目的",
                "highlights": "亮点",
                "status": "状态",
                "impact": "影响",
                "weekly_stats": "周统计",
                "types": "类型",
                "contributors": "贡献者",
                "unique": "位",
                "lore_links": "Lore链接",
                "generated": "已生成",
                "verified": "已验证",
                "metadata": "元数据",
                "generated_at": "生成时间",
                "date_range": "日期范围",
                "total_threads": "总线程数",
                "total_messages": "总消息数",
                "processing_stats": "处理统计",
                "statistics": "统计信息",
                "overview": "概览",
                "thread_statistics": "线程统计",
                "contributor_activity": "贡献者活动",
                "chunking_statistics": "分块统计",
                "lore_validation": "Lore验证",
                "summary": "摘要",
                "technical_highlights": "技术亮点",
                "discussion_points": "讨论要点",
                "thread_status": "线程状态",
                "impact_level": "影响级别"
            },
            "en": {
                "report_title": "ARM KVM Mailing List Analysis Report",
                "period": "Period",
                "total": "Total",
                "messages": "messages",
                "threads": "threads",
                "full_report": "Full Report",
                "thread_url": "Thread URL",
                "ai_analysis": "AI Analysis Summary",
                "purpose": "Purpose",
                "highlights": "Highlights",
                "status": "Status",
                "impact": "Impact",
                "weekly_stats": "Weekly Statistics",
                "types": "Types",
                "contributors": "Contributors",
                "unique": "unique",
                "lore_links": "Lore Links",
                "generated": "generated",
                "verified": "verified",
                "metadata": "Metadata",
                "generated_at": "Generated at",
                "date_range": "Date Range",
                "total_threads": "Total Threads",
                "total_messages": "Total Messages",
                "processing_stats": "Processing Statistics",
                "statistics": "Statistics",
                "overview": "Overview",
                "thread_statistics": "Thread Statistics",
                "contributor_activity": "Contributor Activity",
                "chunking_statistics": "Chunking Statistics",
                "lore_validation": "Lore Validation",
                "summary": "Summary",
                "technical_highlights": "Technical Highlights",
                "discussion_points": "Discussion Points",
                "thread_status": "Thread Status",
                "impact_level": "Impact Level"
            }
        }
    
    def t(self, key: str) -> str:
        """获取当前语言的文本"""
        return self.texts.get(self.language, self.texts["zh"]).get(key, key)
    
    def generate_reports(self, forest: EmailForest, analyses: Dict[str, Dict[str, Any]]):
        """生成所有报告"""
        if self.language == "zh":
            print("📊 生成报告...")
        else:
            print("📊 Generating reports...")
        
        # 1. 生成JSON报告
        self._generate_json_report(forest, analyses)
        
        # 2. 生成ASCII可视化报告
        self._generate_ascii_report(forest, analyses)
        
        # 3. 生成HTML报告
        self._generate_html_report(forest, analyses)
        
        # 4. 生成Markdown报告
        self._generate_markdown_report(forest, analyses)
        
        # 5. 生成统计报告
        self._generate_statistics_report(forest, analyses)
        
        # 6. 生成Lore链接报告
        self._generate_lore_links_report(forest)
        
        if self.language == "zh":
            print(f"   ✅ 报告已生成到: {self.report_dir}")
        else:
            print(f"   ✅ Reports generated to: {self.report_dir}")
    
    def _generate_json_report(self, forest: EmailForest, analyses: Dict[str, Dict[str, Any]]):
        """生成JSON格式的详细报告"""
        report_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "date_range": [
                    forest.date_range[0].isoformat(),
                    forest.date_range[1].isoformat()
                ],
                "total_threads": len(forest.threads),
                "total_messages": forest.total_emails,
                "processing_stats": {
                    "chunked_emails": self._count_chunked_emails(forest),
                    "total_chunks": self._count_total_chunks(forest),
                    "lore_links_generated": forest.total_emails,
                    "lore_links_verified": self._count_verified_lore_links(forest)
                }
            },
            "threads": []
        }
        
        # 处理每个线程
        for thread in forest.threads:
            thread_data = {
                "thread_id": thread.thread_id,
                "subject": thread.subject,
                "root_git_hash": thread.root_node.git_hash,
                "root_lore_url": thread.root_node.lore_url,
                "thread_lore_url": f"{thread.root_node.lore_url}T/",
                "date_range": [
                    thread.statistics.date_range[0].isoformat(),
                    thread.statistics.date_range[1].isoformat()
                ],
                "statistics": {
                    "total_messages": thread.statistics.total_messages,
                    "patches": thread.statistics.patches,
                    "replies": thread.statistics.replies,
                    "reviews": thread.statistics.reviews,
                    "acks": thread.statistics.acks,
                    "max_depth": thread.statistics.max_depth,
                    "contributors": thread.statistics.contributors,
                    "patch_series": thread.statistics.patch_series
                },
                "tree": self._build_tree_structure(thread.root_node, thread.all_nodes),
                "ai_summary": thread.ai_summary
            }
            
            report_data["threads"].append(thread_data)
        
        # 保存JSON报告
        json_file = self.report_dir / "arm_kvm_analysis.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"   📄 JSON报告: {json_file}")
    
    def _generate_ascii_report(self, forest: EmailForest, analyses: Dict[str, Dict[str, Any]]):
        """生成ASCII可视化报告"""
        report_lines = []
        
        # 报告头部
        report_lines.append(f"📊 {self.t('report_title')}")
        report_lines.append("=" * 60)
        report_lines.append(f"🕒 {self.t('period')}: {forest.date_range[0].strftime('%Y-%m-%d')} to {forest.date_range[1].strftime('%Y-%m-%d')}")
        report_lines.append(f"📧 {self.t('total')}: {forest.total_emails} {self.t('messages')}, {len(forest.threads)} {self.t('threads')}")
        report_lines.append(f"🔗 {self.t('full_report')}: https://lore.kernel.org/kvmarm/")
        report_lines.append("")
        
        # 处理每个线程
        for i, thread in enumerate(forest.threads):
            report_lines.append(f"Thread {i+1}: {thread.subject}")
            report_lines.append(f"🔗 Thread URL: {thread.root_node.lore_url}T/")
            report_lines.append("")
            
            # 构建线程的ASCII树
            tree_lines = self._build_ascii_tree(thread.root_node, thread.all_nodes)
            report_lines.extend(tree_lines)
            
            # 添加AI分析摘要
            if thread.ai_summary:
                report_lines.append("")
                report_lines.append("📈 AI Analysis Summary:")
                summary = thread.ai_summary
                
                if "executive_summary" in summary:
                    report_lines.append(f"   🎯 Purpose: {summary['executive_summary'][:100]}...")
                
                if "technical_highlights" in summary:
                    report_lines.append(f"   ⚡ Highlights: {', '.join(summary['technical_highlights'][:3])}")
                
                if "thread_status" in summary:
                    report_lines.append(f"   🔄 Status: {summary['thread_status']}")
                
                if "impact_level" in summary:
                    report_lines.append(f"   📊 Impact: {summary['impact_level']}")
            
            report_lines.append("")
            report_lines.append("-" * 60)
            report_lines.append("")
        
        # 添加统计信息
        report_lines.extend(self._generate_statistics_section(forest))
        
        # 保存ASCII报告
        ascii_file = self.report_dir / "weekly_report.txt"
        with open(ascii_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        print(f"   📄 ASCII报告: {ascii_file}")
    
    def _generate_html_report(self, forest: EmailForest, analyses: Dict[str, Dict[str, Any]]):
        """生成HTML格式的交互式报告"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>ARM KVM Mailing List Analysis</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .thread {{ border: 1px solid #ccc; margin: 10px 0; padding: 10px; }}
        .thread-header {{ background-color: #f0f0f0; padding: 10px; }}
        .email-node {{ margin: 10px 0; padding: 5px; border-left: 2px solid #007acc; }}
        .lore-link {{ color: #007acc; text-decoration: none; }}
        .lore-link:hover {{ text-decoration: underline; }}
        .stats {{ background-color: #f9f9f9; padding: 10px; margin: 10px 0; }}
        .ai-summary {{ background-color: #e8f4f8; padding: 10px; margin: 10px 0; }}
    </style>
</head>
<body>
    <h1>📊 ARM KVM Mailing List Analysis Report</h1>
    <p>Period: {forest.date_range[0].strftime('%Y-%m-%d')} to {forest.date_range[1].strftime('%Y-%m-%d')}</p>
    <p>Total: {forest.total_emails} messages in {len(forest.threads)} threads</p>
    
    <div class="stats">
        <h2>📈 Statistics</h2>
        <ul>
            <li>Total Threads: {len(forest.threads)}</li>
            <li>Total Messages: {forest.total_emails}</li>
            <li>Unique Contributors: {len(self._get_all_contributors(forest))}</li>
        </ul>
    </div>
"""
        
        # 添加每个线程
        for thread in forest.threads:
            html_content += f"""
    <div class="thread">
        <div class="thread-header">
            <h3>{thread.subject}</h3>
            <p><a href="{thread.root_node.lore_url}T/" class="lore-link">🔗 View Thread on Lore</a></p>
        </div>
        
        <div class="thread-content">
            {self._build_html_tree(thread.root_node, thread.all_nodes)}
        </div>
        
        {self._build_html_ai_summary(thread.ai_summary) if thread.ai_summary else ""}
    </div>
"""
        
        html_content += """
</body>
</html>
"""
        
        # 保存HTML报告
        html_file = self.report_dir / "interactive_report.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"   📄 HTML报告: {html_file}")
    
    def _generate_markdown_report(self, forest: EmailForest, analyses: Dict[str, Dict[str, Any]]):
        """生成Markdown格式的报告"""
        md_lines = []
        
        # 报告头部
        md_lines.append(f"# 📊 {self.t('report_title')}")
        md_lines.append("")
        md_lines.append(f"**{self.t('period')}**: {forest.date_range[0].strftime('%Y-%m-%d')} to {forest.date_range[1].strftime('%Y-%m-%d')}")
        md_lines.append("")
        md_lines.append(f"**{self.t('total')}**: {forest.total_emails} {self.t('messages')}, {len(forest.threads)} {self.t('threads')}")
        md_lines.append("")
        md_lines.append(f"**{self.t('full_report')}**: [Lore.kernel.org](https://lore.kernel.org/kvmarm/)")
        md_lines.append("")
        
        # 目录 - 简化，只显示thread名称
        md_lines.append("## 📑 Threads")
        md_lines.append("")
        for i, thread in enumerate(forest.threads):
            # 使用series名称或根邮件主题
            thread_title = self._get_thread_title(thread)
            md_lines.append(f"{i+1}. [{thread_title}](#{self._sanitize_anchor(thread_title)})")
        md_lines.append("")
        
        # 处理每个线程
        md_lines.append(f"## 📧 Thread Details")
        md_lines.append("")
        
        for i, thread in enumerate(forest.threads):
            thread_title = self._get_thread_title(thread)
            md_lines.append(f"### {i+1}. {thread_title}")
            md_lines.append("")
            
            # Thread URL
            md_lines.append(f"🔗 **Thread**: {thread.root_node.lore_url}T/")
            md_lines.append("")
            
            # Thread树形结构 - 首先显示
            md_lines.append("**📋 Thread Structure**:")
            md_lines.append("")
            tree_lines = self._build_markdown_tree(thread.root_node, thread.all_nodes)
            md_lines.extend(tree_lines)
            md_lines.append("")
            
            # Thread AI总结 - 如果有多个message，显示thread级别的总结
            if thread.ai_summary and len(thread.all_nodes) > 1:
                md_lines.append(f"**🤖 Thread Summary**:")
                md_lines.append("")
                summary = thread.ai_summary
                
                if "executive_summary" in summary:
                    md_lines.append(f"> {summary['executive_summary']}")
                    md_lines.append("")
                
                if "technical_highlights" in summary and summary["technical_highlights"]:
                    md_lines.append(f"**技术要点**:")
                    for highlight in summary["technical_highlights"][:3]:
                        md_lines.append(f"- {highlight}")
                    md_lines.append("")
            
            # 单个Message分析 - 如果thread中有多个message
            if len(thread.all_nodes) > 1:
                md_lines.append("**📄 Individual Messages**:")
                md_lines.append("")
                
                for node in thread.all_nodes.values():
                    if node.ai_analysis:
                        md_lines.append(f"##### {node.subject}")  # 使用五级标题，形成父子关系
                        md_lines.append("")
                        
                        analysis = node.ai_analysis
                        if "summary" in analysis:
                            md_lines.append(f"**分析**: {analysis['summary']}")
                            md_lines.append("")
                        
                        # 不再显示技术要点，因为Thread Summary已经包含了
            else:
                # 只有一个message的情况，直接显示AI分析
                node = thread.root_node
                if node.ai_analysis:
                    md_lines.append(f"**🤖 Analysis**:")
                    md_lines.append("")
                    
                    analysis = node.ai_analysis
                    if "summary" in analysis:
                        md_lines.append(f"**概述**: {analysis['summary']}")
                        md_lines.append("")
                    
                    if "technical_points" in analysis and analysis["technical_points"]:
                        md_lines.append("**技术要点**:")
                        for point in analysis["technical_points"][:3]:
                            md_lines.append(f"- {point}")
                        md_lines.append("")
            
            md_lines.append("---")
            md_lines.append("")
        
        # 添加footer
        md_lines.append(f"## 📝 {self.t('metadata')}")
        md_lines.append("")
        md_lines.append(f"- **{self.t('generated_at')}**: {datetime.now().isoformat()}")
        md_lines.append(f"- **Language**: {self.language}")
        md_lines.append(f"- **Generator**: ARM KVM Mailing List Analyzer v1.0")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")
        md_lines.append("*Generated with ❤️ by ARM KVM Mail Analyzer*")
        
        # 保存Markdown报告
        md_file = self.report_dir / f"analysis_report_{self.language}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_lines))
        
        print(f"   📄 Markdown报告: {md_file}")
    
    def _get_thread_title(self, thread) -> str:
        """获取thread的标题"""
        root_subject = thread.root_node.subject
        
        # 如果是patch series，提取series名称
        if thread.statistics.patch_series and len(thread.all_nodes) > 1:
            # 尝试从subject中提取系列名称
            import re
            # 匹配类似 [PATCH v10 x/y] 的格式
            match = re.search(r'\[PATCH.*?\]\s*(.+)', root_subject)
            if match:
                series_name = match.group(1).strip()
                version = thread.statistics.patch_series.get('version', '?')
                total = thread.statistics.patch_series.get('total_patches', len(thread.all_nodes))
                return f"[PATCH v{version} series] {series_name} ({total} patches)"
        
        return root_subject
    
    def _sanitize_anchor(self, text: str) -> str:
        """清理文本用作Markdown锚点"""
        import re
        # 移除特殊字符，保留字母数字和连字符
        sanitized = re.sub(r'[^\w\s-]', '', text.lower())
        # 将空格替换为连字符
        sanitized = re.sub(r'\s+', '-', sanitized)
        return sanitized
    
    def _build_markdown_tree(self, node: EmailNode, all_nodes: Dict[str, EmailNode], depth: int = 0) -> List[str]:
        """构建Markdown格式的树形结构"""
        lines = []
        
        # 当前节点
        indent = "  " * depth
        icon = self._get_message_icon(node.message_type)
        
        # 构建节点描述
        sender_name = node.sender.split('<')[0].strip() if '<' in node.sender else node.sender
        date_str = node.date.strftime('%m-%d %H:%M')
        
        line = f"{indent}- {icon} **{node.subject}**"
        if sender_name:
            line += f" - *{sender_name}* ({date_str})"
        
        lines.append(line)
        
        # 添加Lore链接
        lines.append(f"{indent}  - 🔗 [View on Lore]({node.lore_url})")
        
        # 递归添加子节点
        for child_id in node.children_ids:
            if child_id in all_nodes:
                child_node = all_nodes[child_id]
                child_lines = self._build_markdown_tree(child_node, all_nodes, depth + 1)
                lines.extend(child_lines)
        
        return lines
    
    def _generate_statistics_report(self, forest: EmailForest, analyses: Dict[str, Dict[str, Any]]):
        """生成统计报告"""
        stats = {
            "overview": {
                "total_threads": len(forest.threads),
                "total_messages": forest.total_emails,
                "date_range": [
                    forest.date_range[0].isoformat(),
                    forest.date_range[1].isoformat()
                ],
                "unique_contributors": len(self._get_all_contributors(forest))
            },
            "message_types": self._count_message_types(forest),
            "thread_statistics": self._gather_thread_statistics(forest),
            "contributor_activity": self._analyze_contributor_activity(forest),
            "chunking_statistics": self._gather_chunking_statistics(forest),
            "lore_validation": self._gather_lore_validation_stats(forest)
        }
        
        # 保存统计报告
        stats_file = self.report_dir / "statistics.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        print(f"   📄 统计报告: {stats_file}")
    
    def _generate_lore_links_report(self, forest: EmailForest):
        """生成Lore链接报告"""
        lore_report = {
            "summary": {
                "total_links": forest.total_emails,
                "verified_links": self._count_verified_lore_links(forest),
                "high_confidence_matches": self._count_high_confidence_matches(forest)
            },
            "links": []
        }
        
        # 收集所有链接
        for thread in forest.threads:
            for node in thread.all_nodes.values():
                link_data = {
                    "message_id": node.message_id,
                    "subject": node.subject,
                    "lore_url": node.lore_url,
                    "validation": node.lore_validation
                }
                lore_report["links"].append(link_data)
        
        # 保存Lore链接报告
        lore_file = self.report_dir / "lore_links.json"
        with open(lore_file, 'w', encoding='utf-8') as f:
            json.dump(lore_report, f, indent=2, ensure_ascii=False)
        
        print(f"   📄 Lore链接报告: {lore_file}")
    
    def _build_tree_structure(self, root_node: EmailNode, all_nodes: Dict[str, EmailNode]) -> Dict[str, Any]:
        """构建树形结构数据"""
        node_data = {
            "node": {
                "git_hash": root_node.git_hash,
                "message_id": root_node.message_id,
                "lore_url": root_node.lore_url,
                "subject": root_node.subject,
                "sender": root_node.sender,
                "date": root_node.date.isoformat(),
                "message_type": root_node.message_type.value,
                "lore_validation": root_node.lore_validation,
                "patch_info": root_node.patch_info.__dict__ if root_node.patch_info else None,
                "ai_analysis": root_node.ai_analysis
            },
            "children": []
        }
        
        # 递归构建子节点
        for child_id in root_node.children_ids:
            if child_id in all_nodes:
                child_node = all_nodes[child_id]
                child_data = self._build_tree_structure(child_node, all_nodes)
                node_data["children"].append(child_data)
        
        return node_data
    
    def _build_ascii_tree(self, node: EmailNode, all_nodes: Dict[str, EmailNode], prefix: str = "", is_last: bool = True) -> List[str]:
        """构建ASCII树形结构"""
        lines = []
        
        # 当前节点
        connector = "└─ " if is_last else "├─ "
        icon = self._get_message_icon(node.message_type)
        
        line = f"{prefix}{connector}{icon} {node.subject[:60]}"
        if node.sender:
            line += f" - {node.sender.split('<')[0].strip()}"
        line += f" ({node.date.strftime('%m-%d %H:%M')})"
        
        lines.append(line)
        
        # 添加Lore链接
        link_prefix = prefix + ("    " if is_last else "│   ")
        lines.append(f"{link_prefix}🔗 {node.lore_url}")
        
        # 递归添加子节点
        child_prefix = prefix + ("    " if is_last else "│   ")
        for i, child_id in enumerate(node.children_ids):
            if child_id in all_nodes:
                child_node = all_nodes[child_id]
                child_is_last = (i == len(node.children_ids) - 1)
                child_lines = self._build_ascii_tree(child_node, all_nodes, child_prefix, child_is_last)
                lines.extend(child_lines)
        
        return lines
    
    def _build_html_tree(self, node: EmailNode, all_nodes: Dict[str, EmailNode], depth: int = 0) -> str:
        """构建HTML树形结构"""
        indent = "  " * depth
        icon = self._get_message_icon(node.message_type)
        
        html = f"""
{indent}<div class="email-node" style="margin-left: {depth * 20}px;">
{indent}  <strong>{icon} {node.subject}</strong><br>
{indent}  <small>{node.sender} - {node.date.strftime('%Y-%m-%d %H:%M')}</small><br>
{indent}  <a href="{node.lore_url}" class="lore-link">🔗 View on Lore</a>
{indent}</div>
"""
        
        # 递归添加子节点
        for child_id in node.children_ids:
            if child_id in all_nodes:
                child_node = all_nodes[child_id]
                html += self._build_html_tree(child_node, all_nodes, depth + 1)
        
        return html
    
    def _build_html_ai_summary(self, ai_summary: Dict[str, Any]) -> str:
        """构建HTML AI摘要"""
        html = '<div class="ai-summary">'
        html += '<h4>🤖 AI Analysis Summary</h4>'
        
        if "executive_summary" in ai_summary:
            html += f"<p><strong>Summary:</strong> {ai_summary['executive_summary']}</p>"
        
        if "technical_highlights" in ai_summary:
            html += "<p><strong>Technical Highlights:</strong></p><ul>"
            for highlight in ai_summary["technical_highlights"][:5]:
                html += f"<li>{highlight}</li>"
            html += "</ul>"
        
        if "thread_status" in ai_summary:
            html += f"<p><strong>Status:</strong> {ai_summary['thread_status']}</p>"
        
        html += '</div>'
        return html
    
    def _get_message_icon(self, message_type) -> str:
        """获取消息类型对应的图标"""
        icons = {
            "patch": "📄",
            "patch_cover": "📋",
            "reply": "💬",
            "review": "🔍",
            "ack": "✅",
            "other": "📝"
        }
        return icons.get(message_type.value, "📝")
    
    def _generate_statistics_section(self, forest: EmailForest) -> List[str]:
        """生成统计信息部分"""
        lines = []
        
        lines.append("📊 Weekly Statistics:")
        lines.append(f"   📧 Messages: {forest.total_emails} total")
        
        # 统计消息类型
        type_counts = self._count_message_types(forest)
        type_strs = [f"{count} {msg_type}s" for msg_type, count in type_counts.items()]
        lines.append(f"   📊 Types: {', '.join(type_strs)}")
        
        # 统计贡献者
        contributors = self._get_all_contributors(forest)
        lines.append(f"   👥 Contributors: {len(contributors)} unique")
        
        # 统计Lore链接
        verified_links = self._count_verified_lore_links(forest)
        lines.append(f"   🔗 Lore Links: {forest.total_emails} generated, {verified_links} verified")
        
        return lines
    
    def _count_chunked_emails(self, forest: EmailForest) -> int:
        """统计被分割的邮件数量"""
        count = 0
        for thread in forest.threads:
            for node in thread.all_nodes.values():
                if len(node.content_chunks) > 1:
                    count += 1
        return count
    
    def _count_total_chunks(self, forest: EmailForest) -> int:
        """统计总分块数量"""
        count = 0
        for thread in forest.threads:
            for node in thread.all_nodes.values():
                count += len(node.content_chunks)
        return count
    
    def _count_verified_lore_links(self, forest: EmailForest) -> int:
        """统计验证成功的Lore链接数量"""
        count = 0
        for thread in forest.threads:
            for node in thread.all_nodes.values():
                if node.lore_validation and node.lore_validation.get("valid", False):
                    count += 1
        return count
    
    def _count_high_confidence_matches(self, forest: EmailForest) -> int:
        """统计高置信度匹配的链接数量"""
        count = 0
        for thread in forest.threads:
            for node in thread.all_nodes.values():
                if (node.lore_validation and 
                    node.lore_validation.get("match_score", 0) > 0.8):
                    count += 1
        return count
    
    def _count_message_types(self, forest: EmailForest) -> Dict[str, int]:
        """统计消息类型"""
        counts = {}
        for thread in forest.threads:
            for node in thread.all_nodes.values():
                msg_type = node.message_type.value
                counts[msg_type] = counts.get(msg_type, 0) + 1
        return counts
    
    def _get_all_contributors(self, forest: EmailForest) -> List[str]:
        """获取所有贡献者"""
        contributors = set()
        for thread in forest.threads:
            for node in thread.all_nodes.values():
                contributors.add(node.sender)
        return list(contributors)
    
    def _gather_thread_statistics(self, forest: EmailForest) -> Dict[str, Any]:
        """收集线程统计信息"""
        stats = {
            "average_thread_size": 0,
            "max_thread_depth": 0,
            "patch_series_count": 0,
            "active_discussions": 0
        }
        
        if forest.threads:
            total_size = sum(len(thread.all_nodes) for thread in forest.threads)
            stats["average_thread_size"] = total_size / len(forest.threads)
            stats["max_thread_depth"] = max(thread.statistics.max_depth for thread in forest.threads)
            stats["patch_series_count"] = sum(1 for thread in forest.threads if thread.statistics.patch_series)
            stats["active_discussions"] = sum(1 for thread in forest.threads if thread.statistics.replies > 0)
        
        return stats
    
    def _analyze_contributor_activity(self, forest: EmailForest) -> Dict[str, int]:
        """分析贡献者活动"""
        activity = {}
        for thread in forest.threads:
            for node in thread.all_nodes.values():
                sender = node.sender
                activity[sender] = activity.get(sender, 0) + 1
        
        # 返回前10个最活跃的贡献者
        sorted_activity = sorted(activity.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_activity[:10])
    
    def _gather_chunking_statistics(self, forest: EmailForest) -> Dict[str, Any]:
        """收集分块统计信息"""
        stats = {
            "total_chunks": 0,
            "chunked_emails": 0,
            "chunk_types": {},
            "average_chunk_size": 0
        }
        
        total_tokens = 0
        chunk_count = 0
        
        for thread in forest.threads:
            for node in thread.all_nodes.values():
                if len(node.content_chunks) > 1:
                    stats["chunked_emails"] += 1
                
                stats["total_chunks"] += len(node.content_chunks)
                
                for chunk in node.content_chunks:
                    chunk_type = chunk.chunk_type.value
                    stats["chunk_types"][chunk_type] = stats["chunk_types"].get(chunk_type, 0) + 1
                    total_tokens += chunk.token_count
                    chunk_count += 1
        
        if chunk_count > 0:
            stats["average_chunk_size"] = total_tokens / chunk_count
        
        return stats
    
    def _gather_lore_validation_stats(self, forest: EmailForest) -> Dict[str, Any]:
        """收集Lore验证统计信息"""
        stats = {
            "total_links": 0,
            "verified_links": 0,
            "high_confidence": 0,
            "medium_confidence": 0,
            "low_confidence": 0,
            "failed_validations": 0
        }
        
        for thread in forest.threads:
            for node in thread.all_nodes.values():
                stats["total_links"] += 1
                
                if node.lore_validation:
                    if node.lore_validation.get("valid", False):
                        stats["verified_links"] += 1
                        
                        match_score = node.lore_validation.get("match_score", 0)
                        if match_score > 0.8:
                            stats["high_confidence"] += 1
                        elif match_score > 0.6:
                            stats["medium_confidence"] += 1
                        else:
                            stats["low_confidence"] += 1
                    else:
                        stats["failed_validations"] += 1
        
        return stats


def generate_reports(forest: EmailForest, analyses: Dict[str, Dict[str, Any]], output_dir: str = "results", language: str = "zh"):
    """生成报告的便捷函数"""
    generator = ReportGenerator(output_dir, language)
    generator.generate_reports(forest, analyses)