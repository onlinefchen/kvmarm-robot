#!/usr/bin/env python3
"""
快速启动脚本
帮助用户快速测试和运行ARM KVM邮件分析系统
"""

import os
import sys
from pathlib import Path


def check_dependencies():
    """检查依赖是否安装"""
    print("🔍 检查依赖...")
    
    required_packages = [
        'git', 'email', 'requests', 'click', 'tiktoken'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            if package == 'git':
                import git
            elif package == 'email':
                import email
            elif package == 'requests':
                import requests
            elif package == 'click':
                import click
            elif package == 'tiktoken':
                import tiktoken
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少依赖: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    print("✅ 所有依赖已安装")
    return True


def check_api_keys():
    """检查API密钥"""
    print("🔑 检查API密钥...")
    
    openai_key = os.getenv('OPENAI_API_KEY')
    gemini_key = os.getenv('GEMINI_API_KEY')
    
    if not openai_key and not gemini_key:
        print("⚠️  未检测到AI API密钥")
        print("请设置OPENAI_API_KEY或GEMINI_API_KEY环境变量")
        print("或创建.env文件并配置API密钥")
        return False
    
    if openai_key:
        print("✅ 检测到OpenAI API密钥")
    if gemini_key:
        print("✅ 检测到Gemini API密钥")
    
    return True


def run_quick_test():
    """运行快速测试"""
    print("🧪 运行快速测试...")
    
    try:
        # 导入测试函数
        from analyze import test_repository_management, test_email_parsing_with_lore
        
        # 测试仓库管理
        test_repository_management()
        print()
        
        # 测试邮件解析
        test_email_parsing_with_lore()
        print()
        
        print("🎉 快速测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def run_sample_analysis():
    """运行样例分析"""
    print("📊 运行样例分析（最近10封邮件）...")
    
    try:
        from analyze import main_pipeline
        
        # 运行主流程，限制10封邮件
        forest, analyses = main_pipeline(
            date_range=None,
            debug=True,
            limit=10,
            ai_provider="openai" if os.getenv('OPENAI_API_KEY') else "gemini",
            output_dir="quick_start_results"
        )
        
        if forest:
            print(f"✅ 成功分析了 {forest.total_emails} 封邮件")
            print(f"📊 生成了 {len(forest.threads)} 个线程分析")
            print("📁 结果保存在: quick_start_results/")
            return True
        else:
            print("❌ 分析失败")
            return False
            
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("🚀 ARM KVM邮件分析系统 - 快速启动")
    print("=" * 50)
    
    # 1. 检查依赖
    if not check_dependencies():
        return
    
    print()
    
    # 2. 检查API密钥
    has_api_keys = check_api_keys()
    
    print()
    
    # 3. 运行快速测试
    if not run_quick_test():
        return
    
    print()
    
    # 4. 如果有API密钥，运行样例分析
    if has_api_keys:
        response = input("🤖 是否运行AI分析样例？(y/N): ")
        if response.lower() in ['y', 'yes']:
            print()
            run_sample_analysis()
        else:
            print("跳过AI分析样例")
    else:
        print("⚠️  跳过AI分析样例（缺少API密钥）")
    
    print()
    print("🎯 快速启动完成！")
    print("接下来你可以:")
    print("1. 设置API密钥运行完整分析: python analyze.py --limit 50 --debug")
    print("2. 查看测试结果: ls -la quick_start_results/")
    print("3. 运行所有测试: python analyze.py test all")
    print("4. 查看帮助: python analyze.py --help")


if __name__ == '__main__':
    main()