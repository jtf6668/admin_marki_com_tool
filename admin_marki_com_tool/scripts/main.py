import os
import sys
import time
import json
import socket
import requests
import subprocess
import urllib.parse
from utils import SessionManager # 导入工具类
from logger import logger


API_BASE_URL = "https://admin-api.markiapp.com"
BASE_DOMAIN = "markiapp.com"
#AUTH_URL = f"https://os-lgn.{BASE_DOMAIN}/lgn/login/authorize.do" # 生产环境
#APP_ID = "1435186595"

AUTH_URL = f"https://sttc-os-lgn-test.{BASE_DOMAIN}/lgn/login/authorize.do" # 测试环境，注意：测试环境的 appid 和生产环境不一样，不能混用
APP_ID = "1435186595"


session_mgr = SessionManager()

def get_my_team() -> str:
    """
    查看我加入的马克智慧服务平台的团队列表信息。
    """

    ck_dict = session_mgr.get_cookies_dict()

    if not ck_dict:

        logger.warning("未检测到有效的登录 Cookie，准备启动授权服务器。")

        #检查是否有正在运行的授权服务器，如果有，直接使用缓存的 URL 提示用户登录
        existing_url = session_mgr.get_running_server_url()
        if existing_url:
            print(f"AUTH_REQUIRED:检测到您未登录。")
            print(f"1. 请点击此链接登录：{existing_url}")
            print(f"2. 登录成功后，此窗口会自动检测到状态，请稍等片刻后再次询问。")
            return

        # 启动接收器（异步非阻塞）
        # 注意：这里假设 auth_server.py 在同一目录下
        server_path = os.path.join(os.path.dirname(__file__), "auth_server.py")
        process = subprocess.Popen(
            [sys.executable, server_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,  # 以文本模式读取输出
            bufsize=1   # 行缓冲
        )

        # 2. 读取子进程输出，直到拿到端口号
        real_port = None
        for line in process.stdout:
            if line.startswith("REAL_PORT:"):
                real_port = line.strip().split(":")[1]
                break
        
        if not real_port:
            print("错误：无法获取授权服务器端口")
            return
        
        logger.info(f"授权服务器已启动，监听端口: {real_port}")
        
        login_url = generate_login_url(real_port)

        # 核心：保存 PID 和 URL 供下次查询使用
        session_mgr.save_server_info(process.pid, login_url)

        print(f"AUTH_REQUIRED:检测到您未登录。")
        print(f"1. 请点击此链接登录：{login_url}")
        print(f"2. 登录成功后，此窗口会自动检测到状态，请稍等片刻后再次询问。")

        logger.info(f"提示用户登录，链接: {login_url}")
        return
    
    # 将字典拼接成字符串
    raw_cookies = "; ".join([f"{k}={v}" for k, v in ck_dict.items()])

    #raw_cookies = 'osudb_lang=zh-cn; osudb_third=04e6834433a7b9bd726ad0455b3d35f23f29314d648f8574bedebb415d4391f8a4db0e1e5b1e938605f6385669f5522181b96a305a151a93364618e31cb74d4b0647fdfe2604801f4e49b62ce1cd0d0860f759726195f778e138ef1ecbc513f11d12256d7f57265f68836526e6d078951a2aa322a0dd5e40e9539c4bcd05bc0805a4f1eca2a5212a6946a2e7543c3810ddd074a0fa560173e0a325a21adb467347b6744f9ad1483cd72d865280e1ac1c9924835d7a02147eea191ee93bc59513a5e799cf9d76969a1a7733c41639a41060d73876f54c2abded4f17156aca5f0e75e6554458f658b009298083e5060ce8db75f58dc0a8c16289103a3429ae0533; osudb_uid=3801824535; osudb_appid=1435186595; osudb_oar=29ee8d4097b1c7a2a70ad05f232d609d9610d99b9afb8601c0f5ef4e000f499a39edb8e3a73a3aac1246d39671551a39387fe7387e15aaea7daa889c8823b23c46471829f57d76665dff1707a577d3ef54131a6db3b5eb1063447e3e5155c4b7cc1cf0cee86fad702f004499d0946c2e681a6919a31cd5167daa5dfee2fa660c7963e696ff791c0c0c3be1f0414e617975bab41e24ae7f59c5864be376ea96996348b867ebcc089cd42da10526a3a2a099624980c5d1ff60dc503a51d36167e32aad07b3696a86c6d2601865a6765b5917fc6f176b84d3e45e74fb02338d3d77b5c8b020ce40939c0907820e2b5e1b91938d55a8b8eb0a51ebf4453baa9dd586; osudb_c=00004c32107a00017000becf871c4f7de439328ceb11b82f8731f3c84e7690337f0d259ef40badbf097b074d48534164d6f75e9f7d2a22a0f5650272ce1b18984c608ea2bbe47cb8679320e11fa9650e719ed97a7f1a44eaee925e8fa8784504336ad98f5df764aa3de337be30053452bf60b8c7957e700f5c5f; osudb_sex=0; osudb_param=; osudb_ustate=1; osudb_nickname=snail2swift; osudb_avatar=https://thirdwx.qlogo.cn/mmopen/vi_32/DYAIOgq83eqdLLDU791JuGXcOaV52o0CGesPzzb8sWdm2bDeicQkvIcyKylASzx05zrcMSfoZtg2IotSn5423Bg/132'


    headers = {
            "Cookie": raw_cookies,
            "Content-Type": "application/json"
    }

    try:
        # 发起 HTTP GET 请求
        response = requests.get(
            f"{API_BASE_URL}/api/v1/getMyTeam?page=1&pageSize=100", 
            headers=headers,
            timeout=10
        )
        
        # 检查状态码
        if response.status_code != 200:
            logger.error(f"接口调用失败，状态码: {response.status_code}, 响应内容: {response.text}")
            return "请求异常，请稍后再试。"
        
        response.raise_for_status()
        data = response.json()

        # 格式化返回给 AI 的结果。返回内容越清晰，AI 总结得越好。
        output = format_team_list(data)

        logger.info("成功获取团队列表信息")

        print(f"返回数据：{output}")
        return output

    except requests.exceptions.RequestException as e:
        logger.error(f"接口调用发生异常: {e}")
        return f"接口调用发生异常: {str(e)}"

def find_available_port(start_port=8080):
    # 此处逻辑与 auth_server 保持一致，确保两者算的端口是一样的
    # 或者由 main.py 算出端口后，作为命令行参数传给 auth_server.py
    port = start_port
    while port < start_port + 100:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return port
            except socket.error:
                port += 1
    return start_port

def generate_login_url(port):
    """生成给用户点击的授权链接"""
    params = {
        "appid": APP_ID,
        "callback": f"http://localhost:{port}/callback", # 假设你本地有个回调处理
        "ctype": "json",
        "type": "mobile", # 示例只支持邮箱
        "state": "openclaw_auth",
        "autoTime": 7,
        "backEnd": 1
    }
    query_string = urllib.parse.urlencode(params)
    return f"{AUTH_URL}?{query_string}"

def format_team_list(raw_response):
    # 解析 JSON
    if isinstance(raw_response, str):
        res = json.loads(raw_response)
    else:
        res = raw_response

    if res.get('code') != 0:
        return f"获取失败：{res.get('msg')}"

    teams = res.get('data', {}).get('team', [])
    if not teams:
        return "您还没有加入任何团队。"

    # 角色映射（请根据你系统的实际定义修改）
    role_map = {
        1: "创建者",
        2: "管理员",
        3: "普通成员"
    }

    # 构建 Markdown 格式的输出
    output = ["### 您的团队列表\n"]
    output.append("| 团队ID | 团队名称 | 角色 | 加入时间 |")
    output.append("| :--- | :--- | :--- | :--- |")

    for item in teams:
        team_id = item.get('teamid')
        name = item.get('name')
        # 转换角色
        role_id = item.get('role')
        role_name = role_map.get(role_id, f"其他({role_id})")
        # 转换时间戳为可读格式
        timestamp = item.get('crttime')
        join_time = time.strftime("%Y-%m-%d %H:%M", time.localtime(timestamp))
        
        output.append(f"| {team_id} | {name} | {role_name} | {join_time} |")

    return "\n".join(output)

def loginUserInfo():
    """
    获取当前登录马克系统的用户信息。
    """
    # 这里添加获取用户信息的逻辑
    # 例如，读取本地保存的 Cookie 信息并解析出用户信息
    session = session_mgr.get_cookies_dict()
    if session and "osudb_uid" in session:
        user_info = {
            "uid": session.get("osudb_uid")
        }
        logger.info(f"当前登录用户信息: {user_info}")
        return user_info
    else:
        logger.warning("未检测到有效的登录 Session")
        return None

def logout() -> str:
    """
    登出马克账号。
    """

    # 这里添加登出逻辑
    # 例如，清除本地保存的 Cookie 信息
    session_mgr.clear_session()
    logger.info("成功登出马克账号")
    return "已成功登出马克账号。"

if __name__ == "__main__":
    # 简单的路由逻辑
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    
    if command == "get_my_team":
        get_my_team()
    elif command == "logout":
        logout()
    else:
        print("错误：未知的指令或参数不足")