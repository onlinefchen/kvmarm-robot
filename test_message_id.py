#!/usr/bin/env python3
"""
测试Message-ID解析问题
"""
import email
from email import policy
import subprocess

def test_message_id_parsing():
    """测试Message-ID解析"""
    print("🔍 测试Message-ID解析...")
    
    # 获取失败的邮件内容
    failed_shas = ['d7dfe3f6', '700258b2', 'cf4cf19c']
    
    for sha in failed_shas:
        print(f"\n测试 {sha}:")
        print("-" * 40)
        
        # 获取原始邮件内容
        cmd = ["git", "-C", "kvmarm/git/0.git", "show", f"{sha}:m"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ 无法获取内容: {result.stderr}")
            continue
        
        content = result.stdout
        
        try:
            # 使用Python的email解析器
            msg = email.message_from_string(content, policy=policy.default)
            
            # 提取字段
            from_field = msg.get("From", "")
            subject_field = msg.get("Subject", "")
            message_id_field = msg.get("Message-ID", "")
            
            print(f"From: '{from_field}'")
            print(f"Subject: '{subject_field}'")
            print(f"Message-ID: '{message_id_field}'")
            
            # 清理Message-ID
            clean_message_id = message_id_field.strip('<>')
            print(f"清理后的Message-ID: '{clean_message_id}'")
            
            # 检查为什么被认为是无效的
            if not from_field:
                print("❌ From字段为空")
            if not subject_field:
                print("❌ Subject字段为空")
            if not message_id_field:
                print("❌ Message-ID字段为空")
            if len(subject_field.strip()) < 3:
                print("❌ Subject太短")
            
            # 模拟原来的验证逻辑
            print(f"\n原验证逻辑结果:")
            print(f"  有From: {bool(from_field)}")
            print(f"  有Subject: {bool(subject_field)}")
            print(f"  有Message-ID: {bool(message_id_field)}")
            print(f"  Subject长度: {len(subject_field.strip())}")
            
            # 显示Message-ID的详细信息
            if message_id_field:
                print(f"  Message-ID长度: {len(message_id_field)}")
                print(f"  Message-ID包含@: {'@' in message_id_field}")
            
        except Exception as e:
            print(f"❌ 邮件解析失败: {e}")

if __name__ == "__main__":
    test_message_id_parsing()