import os
import sys
from loguru import logger

# 1. 动态获取当前 Skill 的根目录 (即 my_weather_skill 文件夹)
# __file__ 是 logger.py，它的上一级是 utils，再上一级就是技能根目录
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(SKILL_ROOT, "logs")

# 确保文件夹存在
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 2. 配置配置
logger.remove() # 移除默认配置

# 控制台输出
logger.add(sys.stdout, level="DEBUG", colorize=True)

# 文件输出 (存放在当前 Skill 下的 logs 目录)
log_path = os.path.join(LOG_DIR, "{time:YYYY-MM-DD}.log")
logger.add(log_path, rotation="00:00", retention="10 days", level="INFO", encoding="utf-8")

# 导出对象
__all__ = ["logger"]