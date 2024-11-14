# logger.py
import logging
import colorlog

def setup_logger(name, log_level=logging.DEBUG):
    # 获取或创建 logger
    logger = logging.getLogger(name)
    
    # 移除已有的处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 禁用父级传播
    logger.propagate = False
    
    # 配置日志格式
    bold_seq = '\033[1m'
    colorlog_format = f'{bold_seq} %(log_color)s%(levelname)s:%(name)s:%(message)s'

    # 配置颜色
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        fmt=colorlog_format,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    ))

    # 设置日志级别并添加处理器
    logger.setLevel(log_level)
    logger.addHandler(handler)

    return logger