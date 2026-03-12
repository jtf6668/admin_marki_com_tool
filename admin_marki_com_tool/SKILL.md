---
name: admin_marki_com_tool
description: 用于查询马克智慧物业系统数据的工具
requires:
  bins:
    - python3           # 确保系统安装了 python3
---

# Admin Marki Tool
这个工具可以让 AI 通过 HTTP 接口访问马克智慧物业系统。

# 使用方法

AI 应当根据需求选择以下指令运行：

- **查看我加入的团队列表信息**: `python3 {baseDir}/scripts/main.py get_my_team`
- **登出马克账号**: `python3 {baseDir}/scripts/main.py logout`