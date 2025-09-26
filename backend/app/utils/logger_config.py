import os
import sys
from typing import Optional

class LoggerConfig:
    """日志配置类"""
    
    def __init__(self):
        # 从环境变量读取日志级别
        self.debug_level = os.getenv('DIFF_DEBUG_LEVEL', 'INFO').upper()
        self.enable_debug = self.debug_level in ['DEBUG', 'ALL']
        self.enable_verbose = self.debug_level in ['VERBOSE', 'ALL']
        
    def should_log(self, level: str) -> bool:
        """判断是否应该输出指定级别的日志"""
        if level == 'DEBUG':
            return self.enable_debug
        elif level == 'VERBOSE':
            return self.enable_verbose
        return True
    
    def debug(self, message: str, level: str = 'DEBUG'):
        """条件性输出调试信息"""
        if self.should_log(level):
            print(f"[{level}] {message}")
    
    def info(self, message: str):
        """输出信息"""
        print(f"[INFO] {message}")
    
    def warn(self, message: str):
        """输出警告"""
        print(f"[WARN] {message}")
    
    def error(self, message: str):
        """输出错误"""
        print(f"[ERROR] {message}")

# 全局日志配置实例
logger = LoggerConfig()

def debug_log(message: str, level: str = 'DEBUG'):
    """全局调试日志函数"""
    logger.debug(message, level)

def info_log(message: str):
    """全局信息日志函数"""
    logger.info(message)

def warn_log(message: str):
    """全局警告日志函数"""
    logger.warn(message)

def error_log(message: str):
    """全局错误日志函数"""
    logger.error(message)
