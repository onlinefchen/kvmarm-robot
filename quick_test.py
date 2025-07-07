#!/usr/bin/env python3
"""
快速测试真正的email解析器
"""
import email
from email import policy
import subprocess

def test_with_python_email():
    """使用Python email库测试"""
    failed_shas = ['d7dfe3f6']
    
    for sha in failed_shas:
        print(f"测试 {sha}:")
        
        # 获取内容
        cmd = ["git", "-C", "kvmarm/git/0.git", "show", f"{sha}:m"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        content = result.stdout
        
        # 使用Python email库解析
        msg = email.message_from_string(content, policy=policy.default)
        
        from_field = msg.get("From", "")
        subject_field = msg.get("Subject", "")  
        message_id_field = msg.get("Message-ID", "")
        
        print(f"From: '{from_field}' (长度: {len(from_field)})")
        print(f"Subject: '{subject_field}' (长度: {len(subject_field)})")
        print(f"Message-ID: '{message_id_field}' (长度: {len(message_id_field)})")
        
        # 测试验证函数
        all_fields_exist = bool(from_field) and bool(subject_field) and bool(message_id_field)
        subject_long_enough = len(subject_field.strip()) >= 3
        
        print(f"所有字段存在: {all_fields_exist}")
        print(f"Subject长度足够: {subject_long_enough}")
        print(f"应该通过验证: {all_fields_exist and subject_long_enough}")

if __name__ == "__main__":
    test_with_python_email()