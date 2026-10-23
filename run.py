# -*- coding: utf-8 -*-
"""
MVP 下单系统 - 后端启动入口
运行方式：
    python run.py
或：
    uvicorn app.main:app --reload --port 8000
"""
import uvicorn

if __name__ == "__main__":
    # 首次启动会自动初始化 SQLite 数据库（见 app/core/database.py）
    # 绑定 0.0.0.0，允许局域网设备访问（真机调试）
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
