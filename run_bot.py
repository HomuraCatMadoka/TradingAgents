#!/usr/bin/env python3
"""
DeFi Telegram Bot启动脚本

运行：python3 run_bot.py
"""
import sys
import os

# 添加项目路径到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

if __name__ == "__main__":
    from bot import main
    main()
