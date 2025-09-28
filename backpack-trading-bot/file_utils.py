#!/usr/bin/env python3
"""
跨平台文件操作工具
解决Windows和Linux/Mac之间的编码问题
"""

import os
import sys
from typing import Optional

def write_pid_file(pid: int, filename: str = "backpack_farming.pid") -> bool:
    """
    写入PID文件，使用跨平台兼容的编码
    
    Args:
        pid: 进程ID
        filename: PID文件名
        
    Returns:
        bool: 是否成功写入
    """
    try:
        # 使用UTF-8编码，不添加BOM
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(str(pid))
        return True
    except Exception as e:
        print(f"写入PID文件失败: {e}")
        return False

def read_pid_file(filename: str = "backpack_farming.pid") -> Optional[int]:
    """
    读取PID文件，处理各种编码问题
    
    Args:
        filename: PID文件名
        
    Returns:
        Optional[int]: 进程ID，如果读取失败返回None
    """
    if not os.path.exists(filename):
        return None
    
    try:
        # 尝试不同的编码方式
        encodings = ['utf-8-sig', 'utf-8', 'gbk', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(filename, 'r', encoding=encoding) as f:
                    content = f.read().strip()
                    # 移除可能的BOM字符
                    if content.startswith('\ufeff'):
                        content = content[1:]
                    return int(content)
            except (UnicodeDecodeError, ValueError):
                continue
        
        # 如果所有编码都失败，尝试二进制读取
        with open(filename, 'rb') as f:
            content = f.read().decode('utf-8', errors='ignore').strip()
            if content.startswith('\ufeff'):
                content = content[1:]
            return int(content)
            
    except Exception as e:
        print(f"读取PID文件失败: {e}")
        return None

def remove_pid_file(filename: str = "backpack_farming.pid") -> bool:
    """
    删除PID文件
    
    Args:
        filename: PID文件名
        
    Returns:
        bool: 是否成功删除
    """
    try:
        if os.path.exists(filename):
            os.remove(filename)
        return True
    except Exception as e:
        print(f"删除PID文件失败: {e}")
        return False

def write_log_file(message: str, filename: str = "background_farming.log") -> bool:
    """
    写入日志文件，使用跨平台兼容的编码
    
    Args:
        message: 日志消息
        filename: 日志文件名
        
    Returns:
        bool: 是否成功写入
    """
    try:
        from datetime import datetime
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        log_message = f"{timestamp} {message}\n"
        
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(log_message)
        return True
    except Exception as e:
        print(f"写入日志文件失败: {e}")
        return False

def get_system_info() -> dict:
    """
    获取系统信息，用于诊断问题
    
    Returns:
        dict: 系统信息
    """
    import platform
    import sys
    
    return {
        'platform': platform.platform(),
        'system': platform.system(),
        'python_version': sys.version,
        'default_encoding': sys.getdefaultencoding(),
        'file_system_encoding': sys.getfilesystemencoding()
    }

if __name__ == "__main__":
    # 测试功能
    print("文件操作工具测试")
    print(f"系统信息: {get_system_info()}")
    
    # 测试PID文件操作
    test_pid = 12345
    if write_pid_file(test_pid):
        print(f"✅ 写入PID文件成功: {test_pid}")
        
        read_pid = read_pid_file()
        if read_pid == test_pid:
            print(f"✅ 读取PID文件成功: {read_pid}")
        else:
            print(f"❌ 读取PID文件失败: 期望 {test_pid}, 实际 {read_pid}")
        
        if remove_pid_file():
            print("✅ 删除PID文件成功")
        else:
            print("❌ 删除PID文件失败")
    else:
        print("❌ 写入PID文件失败")
