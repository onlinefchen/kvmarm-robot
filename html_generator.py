#!/usr/bin/env python3
"""
HTML报告生成器
基于Markdown文件生成精美的HTML报告，适合GitHub Pages托管
"""

import os
import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import markdown
from pathlib import Path


class HTMLReportGenerator:
    """HTML报告生成器"""
    
    def __init__(self, github_repo_url: Optional[str] = None):
        self.github_repo_url = github_repo_url or "https://onlinefchen.github.io/kvmarm-robot"
        
    def generate_html_report(self, results_dir: str) -> str:
        """生成HTML报告"""
        print(f"📄 正在生成HTML报告，目录: {results_dir}")
        
        # 查找Markdown文件
        markdown_file = self._find_markdown_file(results_dir)
        if not markdown_file:
            print("❌ 未找到Markdown文件")
            return ""
        
        # 读取Markdown内容
        markdown_content = self._read_markdown_file(markdown_file)
        if not markdown_content:
            print("❌ 无法读取Markdown内容")
            return ""
        
        # 加载统计数据
        stats_data = self._load_statistics(results_dir)
        
        # 生成HTML
        html_content = self._generate_html_content(markdown_content, stats_data, results_dir)
        
        # 保存HTML文件
        html_file = os.path.join(results_dir, 'report.html')
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HTML报告已生成: {html_file}")
        return html_file
    
    def setup_github_pages(self, base_dir: str = "docs") -> str:
        """设置GitHub Pages目录结构"""
        print("🚀 设置GitHub Pages目录结构...")
        
        # 创建docs目录
        docs_dir = os.path.join(os.getcwd(), base_dir)
        os.makedirs(docs_dir, exist_ok=True)
        
        # 生成index.html
        index_file = self._generate_index_page(docs_dir)
        
        # 生成GitHub Actions workflow
        self._generate_github_workflow()
        
        # 生成_config.yml
        self._generate_jekyll_config(docs_dir)
        
        print(f"✅ GitHub Pages设置完成，目录: {docs_dir}")
        return docs_dir
    
    def deploy_to_pages(self, results_dir: str, docs_dir: str) -> str:
        """部署报告到GitHub Pages"""
        print(f"🚀 部署报告到GitHub Pages...")
        
        # 生成HTML报告
        html_file = self.generate_html_report(results_dir)
        if not html_file:
            return ""
        
        # 创建日期目录
        date_str = datetime.now().strftime('%Y-%m-%d')
        report_dir = os.path.join(docs_dir, 'reports', date_str)
        os.makedirs(report_dir, exist_ok=True)
        
        # 复制文件到docs目录
        import shutil
        
        # 复制HTML报告
        shutil.copy2(html_file, os.path.join(report_dir, 'index.html'))
        
        # 复制其他文件
        files_to_copy = [
            'analysis_report_zh.md',
            'statistics.json',
            'weekly_report.txt'
        ]
        
        for file_name in files_to_copy:
            src_file = os.path.join(results_dir, file_name)
            if os.path.exists(src_file):
                shutil.copy2(src_file, report_dir)
        
        # 更新index页面
        self._update_index_page(docs_dir, date_str)
        
        # 生成URL
        pages_url = f"{self.github_repo_url}/reports/{date_str}/"
        
        print(f"✅ 报告已部署到: {pages_url}")
        return pages_url
    
    def _find_markdown_file(self, results_dir: str) -> Optional[str]:
        """查找Markdown文件"""
        possible_files = [
            'analysis_report_zh.md',
            'analysis_report_en.md',
            'analysis_report.md'
        ]
        
        for file_name in possible_files:
            file_path = os.path.join(results_dir, file_name)
            if os.path.exists(file_path):
                return file_path
        return None
    
    def _read_markdown_file(self, file_path: str) -> Optional[str]:
        """读取Markdown文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"❌ 读取Markdown文件失败: {e}")
            return None
    
    def _load_statistics(self, results_dir: str) -> Dict[str, Any]:
        """加载统计数据"""
        stats_file = os.path.join(results_dir, 'statistics.json')
        if os.path.exists(stats_file):
            try:
                with open(stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ 加载统计数据失败: {e}")
        return {}
    
    def _generate_html_content(self, markdown_content: str, stats_data: Dict[str, Any], results_dir: str) -> str:
        """生成HTML内容"""
        
        # 将Markdown转换为HTML
        try:
            html_body = markdown.markdown(
                markdown_content, 
                extensions=['tables', 'codehilite', 'toc']
            )
        except Exception as e:
            print(f"⚠️ Markdown转换失败，使用简单转换: {e}")
            html_body = self._simple_markdown_to_html(markdown_content)
        
        # 提取统计信息
        overview = stats_data.get('overview', {})
        total_messages = overview.get('total_messages', 'Unknown')
        total_threads = overview.get('total_threads', 'Unknown')
        contributors = overview.get('unique_contributors', 'Unknown')
        date_range = overview.get('date_range', ['Unknown', 'Unknown'])
        
        # 生成GitHub Pages URL
        date_str = datetime.now().strftime('%Y-%m-%d')
        pages_url = f"{self.github_repo_url}/reports/{date_str}/"
        
        # CSS样式
        css = """
        <style>
        :root {
            --primary-color: #2c3e50;
            --secondary-color: #3498db;
            --accent-color: #e74c3c;
            --background-color: #f8f9fa;
            --card-background: #ffffff;
            --text-color: #2c3e50;
            --text-light: #7f8c8d;
            --border-color: #ecf0f1;
            --success-color: #27ae60;
            --warning-color: #f39c12;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            background: var(--background-color);
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 3rem 2rem;
            text-align: center;
            border-radius: 15px;
            margin-bottom: 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            font-weight: 300;
        }
        
        .header .subtitle {
            font-size: 1.2rem;
            opacity: 0.9;
            margin-bottom: 1rem;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }
        
        .stat-card {
            background: var(--card-background);
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        }
        
        .stat-number {
            font-size: 3rem;
            font-weight: bold;
            color: var(--secondary-color);
            margin-bottom: 0.5rem;
        }
        
        .stat-label {
            font-size: 1.1rem;
            color: var(--text-light);
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .content-card {
            background: var(--card-background);
            border-radius: 15px;
            padding: 2.5rem;
            margin: 2rem 0;
            box-shadow: 0 5px 20px rgba(0,0,0,0.08);
        }
        
        .content-card h1 {
            color: var(--primary-color);
            border-bottom: 3px solid var(--secondary-color);
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
        }
        
        .content-card h2 {
            color: var(--secondary-color);
            margin: 2rem 0 1rem 0;
            position: relative;
        }
        
        .content-card h2::before {
            content: '';
            position: absolute;
            left: -1rem;
            top: 50%;
            transform: translateY(-50%);
            width: 4px;
            height: 100%;
            background: var(--secondary-color);
            border-radius: 2px;
        }
        
        .content-card h3 {
            color: var(--primary-color);
            margin: 1.5rem 0 1rem 0;
        }
        
        .content-card ul {
            margin: 1rem 0;
            padding-left: 1.5rem;
        }
        
        .content-card li {
            margin: 0.5rem 0;
            position: relative;
        }
        
        .content-card li::marker {
            color: var(--secondary-color);
        }
        
        .content-card strong {
            color: var(--primary-color);
        }
        
        .footer {
            background: var(--primary-color);
            color: white;
            padding: 2rem;
            text-align: center;
            border-radius: 12px;
            margin-top: 3rem;
        }
        
        .footer a {
            color: #3498db;
            text-decoration: none;
        }
        
        .footer a:hover {
            text-decoration: underline;
        }
        
        .github-link {
            background: var(--secondary-color);
            color: white;
            padding: 1rem 2rem;
            border-radius: 8px;
            text-decoration: none;
            display: inline-block;
            margin: 1rem;
            transition: background 0.3s ease;
        }
        
        .github-link:hover {
            background: #2980b9;
            color: white;
            text-decoration: none;
        }
        
        .navigation {
            background: var(--card-background);
            padding: 1rem 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        
        .navigation a {
            color: var(--secondary-color);
            text-decoration: none;
            margin: 0 1rem;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            transition: background 0.3s ease;
        }
        
        .navigation a:hover {
            background: var(--background-color);
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .header {
                padding: 2rem 1rem;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .content-card {
                padding: 1.5rem;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
        }
        
        .highlight {
            background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%);
            padding: 1.5rem;
            border-radius: 10px;
            margin: 1.5rem 0;
            border-left: 5px solid var(--warning-color);
        }
        
        .info-box {
            background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 10px;
            margin: 1.5rem 0;
        }
        
        .info-box a {
            color: #ddd;
        }
        </style>
        """
        
        # 完整HTML
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="ARM KVM邮件列表自动分析报告">
    <meta name="author" content="ARM KVM Analysis System">
    <title>ARM KVM 邮件列表分析报告</title>
    {css}
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 ARM KVM 邮件列表分析报告</h1>
            <div class="subtitle">
                {date_range[0][:10]} 至 {date_range[1][:10]}
            </div>
            <div class="subtitle">
                🤖 由 ARM KVM 分析系统自动生成
            </div>
        </div>
        
        <div class="navigation">
            <a href="{self.github_repo_url}">🏠 首页</a>
            <a href="{pages_url}analysis_report_zh.md">📄 Markdown版本</a>
            <a href="{pages_url}statistics.json">📊 原始数据</a>
            <a href="https://lore.kernel.org/kvmarm/">📧 邮件归档</a>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{total_messages}</div>
                <div class="stat-label">封邮件</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{total_threads}</div>
                <div class="stat-label">个线程</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{contributors}</div>
                <div class="stat-label">位贡献者</div>
            </div>
        </div>
        
        <div class="highlight">
            <strong>📌 报告亮点</strong>: 本报告包含ARM KVM邮件列表的完整技术分析，
            涵盖了所有重要的开发动态和技术讨论。通过GitHub Pages自动托管，确保内容的可访问性。
        </div>
        
        <div class="content-card">
            {html_body}
        </div>
        
        <div class="info-box">
            <h3>🔗 相关资源</h3>
            <p>
                <a href="https://lore.kernel.org/kvmarm/" target="_blank">ARM KVM邮件归档</a> | 
                <a href="https://www.kernel.org/" target="_blank">Linux内核主页</a> | 
                <a href="https://developer.arm.com/" target="_blank">ARM开发者资源</a>
            </p>
        </div>
        
        <div class="footer">
            <div>
                <a href="{pages_url}" class="github-link">
                    📄 查看此报告的GitHub Pages
                </a>
                <a href="{self.github_repo_url}" class="github-link">
                    🏠 返回报告首页
                </a>
            </div>
            <p style="margin-top: 1rem;">
                🤖 由 ARM KVM 分析系统自动生成 | 
                📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
                🔗 <a href="{pages_url}">永久链接</a>
            </p>
        </div>
    </div>
</body>
</html>"""
        
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
        lines = html.split('\n')
        in_list = False
        result_lines = []
        
        for line in lines:
            if line.strip().startswith('- '):
                if not in_list:
                    result_lines.append('<ul>')
                    in_list = True
                result_lines.append(f'<li>{line.strip()[2:]}</li>')
            else:
                if in_list:
                    result_lines.append('</ul>')
                    in_list = False
                result_lines.append(line)
        
        if in_list:
            result_lines.append('</ul>')
        
        # 段落转换
        html = '\n'.join(result_lines)
        html = re.sub(r'\n\n', '</p><p>', html)
        html = f'<p>{html}</p>'
        html = html.replace('<p></p>', '')
        
        return html
    
    def _generate_index_page(self, docs_dir: str) -> str:
        """生成index页面"""
        index_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ARM KVM 邮件列表分析报告</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 3rem 2rem;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            font-weight: 300;
        }}
        
        .content {{
            padding: 2rem;
        }}
        
        .report-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }}
        
        .report-card {{
            border: 1px solid #e0e0e0;
            border-radius: 12px;
            padding: 1.5rem;
            background: #f8f9fa;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .report-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        
        .report-card h3 {{
            color: #2c3e50;
            margin-top: 0;
        }}
        
        .report-links {{
            margin-top: 1rem;
        }}
        
        .report-links a {{
            display: inline-block;
            margin: 0.25rem 0.5rem 0.25rem 0;
            padding: 0.5rem 1rem;
            background: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            transition: background 0.3s ease;
        }}
        
        .report-links a:hover {{
            background: #2980b9;
        }}
        
        .footer {{
            background: #2c3e50;
            color: white;
            padding: 2rem;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 ARM KVM 邮件列表分析报告</h1>
            <p>自动生成的技术分析和开发动态报告</p>
        </div>
        
        <div class="content">
            <div class="report-grid" id="reportGrid">
                <!-- 报告将动态添加到这里 -->
            </div>
            
            <div style="text-align: center; margin: 2rem 0; padding: 2rem; background: #e8f4f8; border-radius: 12px;">
                <h3>📚 相关资源</h3>
                <p>
                    <a href="https://lore.kernel.org/kvmarm/" style="margin: 0 1rem; color: #2980b9;">ARM KVM邮件归档</a>
                    <a href="https://www.kernel.org/" style="margin: 0 1rem; color: #2980b9;">Linux内核主页</a>
                    <a href="https://developer.arm.com/" style="margin: 0 1rem; color: #2980b9;">ARM开发者资源</a>
                </p>
            </div>
        </div>
        
        <div class="footer">
            <p>🤖 由 ARM KVM 分析系统自动生成和更新</p>
            <p>📅 最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
    
    <script>
        // 这里可以添加JavaScript来动态加载报告列表
        console.log('ARM KVM Analysis Reports loaded');
    </script>
</body>
</html>"""
        
        index_file = os.path.join(docs_dir, 'index.html')
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        return index_file
    
    def _update_index_page(self, docs_dir: str, date_str: str):
        """更新index页面，添加新报告"""
        # 这里可以实现动态更新index页面的逻辑
        # 目前简单重新生成
        self._generate_index_page(docs_dir)
        print(f"✅ 已更新index页面，添加了 {date_str} 的报告")
    
    def _generate_github_workflow(self):
        """生成GitHub Actions工作流"""
        workflow_dir = os.path.join('.github', 'workflows')
        os.makedirs(workflow_dir, exist_ok=True)
        
        workflow_content = """name: Deploy to GitHub Pages

on:
  push:
    branches: [ main ]
  schedule:
    # 每周一早上9点 (UTC) 运行
    - cron: '0 9 * * 1'
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout
      uses: actions/checkout@v4
      
    - name: Setup Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        
    - name: Run analysis and generate reports
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      run: |
        python analyze.py main --output docs/reports/$(date +%Y-%m-%d)
        
    - name: Generate HTML reports
      run: |
        python html_generator.py --deploy
        
    - name: Setup Pages
      uses: actions/configure-pages@v4
      
    - name: Upload artifact
      uses: actions/upload-pages-artifact@v3
      with:
        path: './docs'
        
    - name: Deploy to GitHub Pages
      id: deployment
      uses: actions/deploy-pages@v4
"""
        
        workflow_file = os.path.join(workflow_dir, 'deploy.yml')
        with open(workflow_file, 'w', encoding='utf-8') as f:
            f.write(workflow_content)
        
        print(f"✅ GitHub Actions工作流已生成: {workflow_file}")
    
    def _generate_jekyll_config(self, docs_dir: str):
        """生成Jekyll配置"""
        config_content = """title: ARM KVM 邮件列表分析报告
description: 自动生成的ARM KVM邮件列表技术分析报告
baseurl: ""
url: "https://your-username.github.io"

markdown: kramdown
highlighter: rouge
theme: minima

plugins:
  - jekyll-feed
  - jekyll-sitemap

exclude:
  - Gemfile
  - Gemfile.lock
  - node_modules
  - vendor

collections:
  reports:
    output: true
    permalink: /:collection/:name/

defaults:
  - scope:
      path: ""
      type: "reports"
    values:
      layout: "report"
"""
        
        config_file = os.path.join(docs_dir, '_config.yml')
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print(f"✅ Jekyll配置已生成: {config_file}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='生成HTML报告和设置GitHub Pages')
    parser.add_argument('--results-dir', default='test_notification_results/2025-07-06', help='结果目录')
    parser.add_argument('--github-repo', default='https://onlinefchen.github.io/kvmarm-robot', help='GitHub Pages URL')
    parser.add_argument('--setup-pages', action='store_true', help='设置GitHub Pages')
    parser.add_argument('--deploy', action='store_true', help='部署到GitHub Pages')
    
    args = parser.parse_args()
    
    generator = HTMLReportGenerator(args.github_repo)
    
    if args.setup_pages:
        docs_dir = generator.setup_github_pages()
        print(f"📚 GitHub Pages设置完成，请提交并推送到GitHub")
    
    if args.deploy:
        docs_dir = 'docs'
        os.makedirs(docs_dir, exist_ok=True)
        pages_url = generator.deploy_to_pages(args.results_dir, docs_dir)
        print(f"🚀 报告已部署，URL: {pages_url}")
    else:
        html_file = generator.generate_html_report(args.results_dir)
        print(f"📄 HTML报告已生成: {html_file}")