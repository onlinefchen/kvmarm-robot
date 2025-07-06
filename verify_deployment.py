#!/usr/bin/env python3
"""
GitHub部署验证和调试脚本
"""
import os
import sys
import subprocess
import requests
import json
from datetime import datetime
from pathlib import Path

def check_github_repo():
    """检查GitHub仓库状态"""
    print("🔍 检查GitHub仓库状态...")
    
    try:
        result = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True)
        if 'onlinefchen/kvmarm-robot' in result.stdout:
            print("✅ GitHub远程仓库配置正确")
            print(f"   仓库URL: git@github.com:onlinefchen/kvmarm-robot.git")
        else:
            print("❌ GitHub远程仓库配置错误")
            return False
    except Exception as e:
        print(f"❌ 无法检查Git状态: {e}")
        return False
    
    return True

def check_github_pages():
    """检查GitHub Pages状态"""
    print("\n🌐 检查GitHub Pages状态...")
    
    pages_url = "https://onlinefchen.github.io/kvmarm-robot"
    
    try:
        response = requests.get(pages_url, timeout=10)
        if response.status_code == 200:
            print(f"✅ GitHub Pages 可访问: {pages_url}")
            return True
        elif response.status_code == 404:
            print(f"⚠️  GitHub Pages 尚未激活: {pages_url}")
            print("   请在GitHub仓库设置中启用Pages功能")
            return False
        else:
            print(f"⚠️  GitHub Pages 状态异常: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"⚠️  无法连接到GitHub Pages: {e}")
        print("   这是正常的，Pages可能尚未设置")
        return False

def check_github_actions():
    """检查GitHub Actions配置"""
    print("\n⚙️  检查GitHub Actions配置...")
    
    workflow_file = Path('.github/workflows/deploy.yml')
    if workflow_file.exists():
        print("✅ GitHub Actions工作流已配置")
        print(f"   文件位置: {workflow_file}")
        
        with open(workflow_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'OPENAI_API_KEY' in content:
                print("✅ 工作流包含OpenAI API密钥配置")
            if 'schedule:' in content:
                print("✅ 工作流包含定时任务配置")
        return True
    else:
        print("❌ GitHub Actions工作流文件不存在")
        return False

def check_environment():
    """检查环境配置"""
    print("\n🔧 检查环境配置...")
    
    required_packages = [
        'requests', 'click', 'python-dotenv', 'gitpython', 
        'openai', 'markdown', 'beautifulsoup4'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n📦 安装缺失的包:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_env_file():
    """检查环境变量文件"""
    print("\n📝 检查环境变量配置...")
    
    env_file = Path('.env')
    if env_file.exists():
        print("✅ .env 文件存在")
        
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        required_vars = ['OPENAI_API_KEY']
        optional_vars = ['LARK_WEBHOOK_URL', 'TELEGRAM_BOT_TOKEN', 'EMAIL_USER', 'GITHUB_TOKEN']
        
        for var in required_vars:
            if var in content and not content.split(f'{var}=')[1].split('\n')[0].strip() == '':
                print(f"✅ {var} 已配置")
            else:
                print(f"❌ {var} 未配置或为空")
        
        for var in optional_vars:
            if var in content and not content.split(f'{var}=')[1].split('\n')[0].strip() == '':
                print(f"✅ {var} 已配置（可选）")
            else:
                print(f"⚠️  {var} 未配置（可选）")
        
        return True
    else:
        print("❌ .env 文件不存在")
        print("   请复制 .env.example 到 .env 并配置相应的值")
        return False

def test_local_functionality():
    """测试本地功能"""
    print("\n🧪 测试本地功能...")
    
    try:
        # 测试导入主要模块
        sys.path.append('.')
        
        # 测试仓库管理
        from repository import RepositoryManager
        print("✅ repository 模块导入成功")
        
        # 测试邮件解析
        from email_parser import EmailParser
        print("✅ email_parser 模块导入成功")
        
        # 测试HTML生成
        from html_generator import HTMLReportGenerator
        print("✅ html_generator 模块导入成功")
        
        # 测试通知功能
        from markdown_notification_sender import MarkdownNotificationManager
        print("✅ markdown_notification_sender 模块导入成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def generate_deployment_guide():
    """生成部署指南"""
    print("\n📚 生成部署指南...")
    
    guide = """
# 🚀 ARM KVM 机器人部署指南

## 当前状态
- ✅ 代码已推送到 GitHub
- ✅ GitHub Pages 结构已配置
- ✅ 自动化工作流已设置

## 立即执行的步骤

### 1. 启用 GitHub Pages
1. 访问: https://github.com/onlinefchen/kvmarm-robot/settings/pages
2. 在 "Source" 中选择 "Deploy from a branch"
3. 选择 "main" 分支和 "docs/" 目录
4. 点击 "Save"

### 2. 配置 GitHub Secrets
1. 访问: https://github.com/onlinefchen/kvmarm-robot/settings/secrets/actions
2. 添加以下 secrets:
   - `OPENAI_API_KEY`: 你的 OpenAI API 密钥
   - `LARK_WEBHOOK_URL`: 飞书机器人 Webhook（可选）
   - `TELEGRAM_BOT_TOKEN`: Telegram 机器人令牌（可选）
   - `EMAIL_USER`: 邮件账户（可选）
   - `EMAIL_PASSWORD`: 邮件密码（可选）

### 3. 手动触发第一次运行
1. 访问: https://github.com/onlinefchen/kvmarm-robot/actions
2. 选择 "Deploy to GitHub Pages" 工作流
3. 点击 "Run workflow"

### 4. 验证部署
等待几分钟后，访问：
- 主页: https://onlinefchen.github.io/kvmarm-robot
- 报告: https://onlinefchen.github.io/kvmarm-robot/reports/

## 本地测试

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，添加你的 API 密钥
```

### 运行测试
```bash
# 测试完整流程
python analyze.py

# 测试通知功能
python analyze.py notify test-platforms

# 生成HTML报告
python analyze.py pages generate-html results/$(date +%Y-%m-%d)
```

## 自动化特性
- 📅 每周一自动运行分析
- 📧 自动发送通知到配置的平台
- 🌐 自动更新 GitHub Pages
- 📊 生成多格式报告（JSON, Markdown, HTML）

## 故障排除
- 检查 GitHub Actions 日志
- 验证 API 密钥配置
- 确认 GitHub Pages 已启用
"""
    
    with open('DEPLOYMENT_GUIDE.md', 'w', encoding='utf-8') as f:
        f.write(guide)
    
    print("✅ 部署指南已生成: DEPLOYMENT_GUIDE.md")

def main():
    """主验证流程"""
    print("🔍 ARM KVM 机器人部署验证")
    print("=" * 50)
    
    checks = [
        check_github_repo(),
        check_environment(),
        check_env_file(),
        check_github_actions(),
        test_local_functionality(),
    ]
    
    # GitHub Pages 检查（可能失败是正常的）
    check_github_pages()
    
    success_count = sum(checks)
    total_checks = len(checks)
    
    print(f"\n📊 验证结果: {success_count}/{total_checks} 项检查通过")
    
    if success_count == total_checks:
        print("🎉 所有检查通过！项目已准备就绪")
    else:
        print("⚠️  部分检查未通过，请查看上述输出解决问题")
    
    generate_deployment_guide()
    
    print(f"\n🔗 GitHub仓库: https://github.com/onlinefchen/kvmarm-robot")
    print(f"🌐 GitHub Pages: https://onlinefchen.github.io/kvmarm-robot")
    print(f"📚 部署指南: DEPLOYMENT_GUIDE.md")

if __name__ == "__main__":
    main()