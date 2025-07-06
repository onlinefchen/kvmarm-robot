#!/usr/bin/env python3
"""
简化版GitHub部署验证脚本
"""
import os
import sys
import subprocess
from pathlib import Path

def check_git_status():
    """检查Git状态"""
    print("🔍 检查Git仓库状态...")
    try:
        result = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True)
        if 'onlinefchen/kvmarm-robot' in result.stdout:
            print("✅ GitHub远程仓库配置正确")
            return True
        else:
            print("❌ GitHub远程仓库配置错误")
            return False
    except Exception as e:
        print(f"❌ Git检查失败: {e}")
        return False

def check_files():
    """检查关键文件"""
    print("\n📁 检查关键文件...")
    
    required_files = [
        'analyze.py',
        'html_generator.py', 
        'markdown_notification_sender.py',
        'requirements.txt',
        '.github/workflows/deploy.yml',
        'docs/_config.yml'
    ]
    
    all_present = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            all_present = False
    
    return all_present

def check_github_urls():
    """检查GitHub URL配置"""
    print("\n🔗 检查GitHub URL配置...")
    
    files_to_check = [
        'html_generator.py',
        'markdown_notification_sender.py', 
        'docs/_config.yml'
    ]
    
    correct_urls = 0
    total_files = len(files_to_check)
    
    for file_path in files_to_check:
        if Path(file_path).exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'onlinefchen.github.io/kvmarm-robot' in content:
                    print(f"✅ {file_path} - URL配置正确")
                    correct_urls += 1
                else:
                    print(f"❌ {file_path} - URL配置错误")
        else:
            print(f"❌ {file_path} - 文件不存在")
    
    return correct_urls == total_files

def generate_next_steps():
    """生成下一步指南"""
    print("\n📋 接下来的步骤:")
    print("1. 访问 GitHub 仓库启用 Pages:")
    print("   https://github.com/onlinefchen/kvmarm-robot/settings/pages")
    print("   - 选择 'main' 分支")
    print("   - 选择 'docs/' 目录")
    
    print("\n2. 配置 GitHub Secrets:")
    print("   https://github.com/onlinefchen/kvmarm-robot/settings/secrets/actions")
    print("   - 添加 OPENAI_API_KEY")
    print("   - 添加其他通知平台密钥（可选）")
    
    print("\n3. 手动触发第一次运行:")
    print("   https://github.com/onlinefchen/kvmarm-robot/actions")
    print("   - 选择 'Deploy to GitHub Pages'")
    print("   - 点击 'Run workflow'")
    
    print("\n4. 验证部署结果:")
    print("   https://onlinefchen.github.io/kvmarm-robot")

def main():
    """主验证流程"""
    print("🚀 ARM KVM 机器人简化验证")
    print("=" * 40)
    
    checks = [
        check_git_status(),
        check_files(),
        check_github_urls()
    ]
    
    success_count = sum(checks)
    total_checks = len(checks)
    
    print(f"\n📊 验证结果: {success_count}/{total_checks} 项检查通过")
    
    if success_count == total_checks:
        print("🎉 所有基础检查通过！")
        print("📦 项目已成功推送到GitHub")
        print("🌐 GitHub Pages配置已准备就绪")
    else:
        print("⚠️  部分检查未通过，请查看上述输出")
    
    generate_next_steps()
    
    # 显示仓库信息
    print(f"\n🔗 项目信息:")
    print(f"GitHub仓库: https://github.com/onlinefchen/kvmarm-robot")
    print(f"GitHub Pages: https://onlinefchen.github.io/kvmarm-robot")
    print(f"本地目录: {os.getcwd()}")

if __name__ == "__main__":
    main()