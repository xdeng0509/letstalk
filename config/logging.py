# -*- coding: utf-8 -*-
"""
日志配置模块
为 Let's Talk 项目提供统一的日志配置
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logging(app=None, log_level=None):
    """
    设置日志配置
    
    Args:
        app: Flask应用实例（可选）
        log_level: 日志级别（可选，默认从环境变量读取）
    """
    
    # 确定日志级别
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # 创建logs目录
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # 清除现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 创建格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level, logging.INFO))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 文件处理器（主日志）
    main_log_file = os.path.join(log_dir, 'letstalk.log')
    file_handler = RotatingFileHandler(
        main_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # 错误日志处理器
    error_log_file = os.path.join(log_dir, 'error.log')
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)
    
    # Flask应用日志配置
    if app:
        app.logger.setLevel(getattr(logging, log_level, logging.INFO))
        
        # 移除Flask默认处理器
        for handler in app.logger.handlers[:]:
            app.logger.removeHandler(handler)
        
        # 添加我们的处理器
        app.logger.addHandler(console_handler)
        app.logger.addHandler(file_handler)
        app.logger.addHandler(error_handler)
        
        # 禁用Flask默认日志传播
        app.logger.propagate = False
    
    # 配置特定模块的日志级别
    logging.getLogger('werkzeug').setLevel(logging.WARNING)  # Flask开发服务器日志
    logging.getLogger('urllib3').setLevel(logging.WARNING)   # HTTP请求库日志
    
    # LLM相关日志
    llm_logger = logging.getLogger('llm')
    llm_log_file = os.path.join(log_dir, 'llm.log')
    llm_handler = RotatingFileHandler(
        llm_log_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    llm_handler.setLevel(logging.DEBUG)
    llm_handler.setFormatter(formatter)
    llm_logger.addHandler(llm_handler)
    
    logging.info(f"日志系统初始化完成 - 级别: {log_level}")
    logging.info(f"主日志文件: {main_log_file}")
    logging.info(f"错误日志文件: {error_log_file}")
    logging.info(f"LLM日志文件: {llm_log_file}")

def get_logger(name):
    """
    获取指定名称的日志器
    
    Args:
        name: 日志器名称
        
    Returns:
        logging.Logger: 配置好的日志器
    """
    return logging.getLogger(name)

# 预定义的日志器
app_logger = get_logger('letstalk.app')
agent_logger = get_logger('letstalk.agent')
llm_logger = get_logger('llm')
api_logger = get_logger('letstalk.api')