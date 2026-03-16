import os
import sys
import time
import json
import socket
import requests
import subprocess
import urllib.parse
from datetime import datetime, timedelta
from utils import SessionManager
from logger import logger


API_BASE_URL = "https://admin-api.markiapp.com"
CHARGE_API_BASE_URL = "https://charge-api-test.markiapp.com"
BASE_DOMAIN = "markiapp.com"
#AUTH_URL = f"https://os-lgn.{BASE_DOMAIN}/lgn/login/authorize.do" # 生产环境
#APP_ID = "1435186595"

AUTH_URL = f"https://sttc-os-lgn-test.{BASE_DOMAIN}/lgn/login/authorize.do" # 测试环境，注意：测试环境的 appid 和生产环境不一样，不能混用
APP_ID = "1435186595"


session_mgr = SessionManager()


def ensure_authenticated() -> dict:
    """
    确保用户已登录，如果未登录则启动授权服务器。

    Returns:
        cookies dict 如果已登录，None 如果需要登录
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
            return None

        # 启动接收器（异步非阻塞）
        # 注意：这里假设 auth_server.py 在同一目录下
        server_path = os.path.join(os.path.dirname(__file__), "auth_server.py")
        process = subprocess.Popen(
            [sys.executable, server_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        # 读取子进程输出，直到拿到端口号
        real_port = None
        for line in process.stdout:
            if line.startswith("REAL_PORT:"):
                real_port = line.strip().split(":")[1]
                break

        if not real_port:
            print("错误：无法获取授权服务器端口")
            return None

        logger.info(f"授权服务器已启动，监听端口: {real_port}")

        login_url = generate_login_url(real_port)

        # 核心：保存 PID 和 URL 供下次查询使用
        session_mgr.save_server_info(process.pid, login_url)

        print(f"AUTH_REQUIRED:检测到您未登录。")
        print(f"1. 请点击此链接登录：{login_url}")
        print(f"2. 登录成功后，此窗口会自动检测到状态，请稍等片刻后再次询问。")

        logger.info(f"提示用户登录，链接: {login_url}")
        return None

    return ck_dict


def get_headers_with_cookies(ck_dict: dict, additional_headers: dict = None) -> dict:
    """
    构建带有 cookies 的请求头

    Args:
        ck_dict: cookies 字典
        additional_headers: 额外的请求头

    Returns:
        完整的请求头字典
    """
    # 将字典拼接成字符串
    raw_cookies = "; ".join([f"{k}={v}" for k, v in ck_dict.items()])

    headers = {
            "Cookie": raw_cookies,
            "Content-Type": "application/json"
    }

    if additional_headers:
        headers.update(additional_headers)

    return headers


def find_available_port(start_port=8080):
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
        "callback": f"http://localhost:{port}/callback",
        "ctype": "json",
        "type": "mobile",
        "state": "openclaw_auth",
        "autoTime": 7,
        "backEnd": 1
    }
    query_string = urllib.parse.urlencode(params)
    return f"{AUTH_URL}?{query_string}"


def get_my_team() -> str:
    """
    查看我加入的马克智慧服务平台的团队列表信息。
    """
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return

    headers = get_headers_with_cookies(ck_dict)

    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/getMyTeam?page=1&pageSize=100",
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"接口调用失败，状态码: {response.status_code}, 响应内容: {response.text}")
            return "请求异常，请稍后再试。"

        response.raise_for_status()
        data = response.json()

        output = format_team_list(data)
        logger.info("成功获取团队列表信息")
        print(f"返回数据：{output}")
        return output

    except requests.exceptions.RequestException as e:
        logger.error(f"接口调用发生异常: {e}")
        return f"接口调用发生异常: {str(e)}"


def format_team_list(raw_response):
    if isinstance(raw_response, str):
        res = json.loads(raw_response)
    else:
        res = raw_response

    if res.get('code') != 0:
        return f"获取失败：{res.get('msg')}"

    teams = res.get('data', {}).get('team', [])
    if not teams:
        return "您还没有加入任何团队。"

    role_map = {
        1: "创建者",
        2: "管理员",
        3: "普通成员"
    }

    output = ["### 您的团队列表\n"]
    output.append("| 团队名称 | 角色 | 加入时间 |")
    output.append("| :--- | :--- | :--- |")

    for item in teams:
        name = item.get('name')
        role_id = item.get('role')
        role_name = role_map.get(role_id, f"其他({role_id})")
        timestamp = item.get('crttime')
        join_time = time.strftime("%Y-%m-%d %H:%M", time.localtime(timestamp))

        output.append(f"| {name} | {role_name} | {join_time} |")

    return "\n".join(output)


def get_user_charge_systems(return_map=False):
    """
    获取用户的收费系统列表

    Args:
        return_map: 如果为 True，返回 {名称: id} 字典；否则打印列表给用户
    """
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None if return_map else None

    headers = get_headers_with_cookies(ck_dict)

    try:
        response = requests.get(
            f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/getUserChargeSysList",
            params={"page": 1, "pageSize": 100},
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"接口调用失败，状态码: {response.status_code}, 响应内容: {response.text}")
            return None if return_map else "请求异常，请稍后再试。"

        data = response.json()

        if data.get('code') != 0:
            msg = f"获取失败：{data.get('msg')}"
            return None if return_map else msg

        systems_list = data.get('data', {}).get('list', [])

        if return_map:
            system_map = {}
            for sys in systems_list:
                name = sys.get('name')
                sys_id = sys.get('csID') or sys.get('id')
                if name and sys_id:
                    system_map[name] = sys_id
            return system_map
        else:
            return format_charge_systems_list(systems_list)

    except requests.exceptions.RequestException as e:
        logger.error(f"接口调用发生异常: {e}")
        return None if return_map else f"接口调用发生异常: {str(e)}"


def format_charge_systems_list(systems_list):
    if not systems_list:
        return "没有找到可用的收费系统。"

    output = ["### 可用的收费系统\n"]
    output.append("| 序号 | 收费系统名称 | 绑定团队 |")
    output.append("| :--- | :--- | :--- |")

    for idx, sys in enumerate(systems_list, 1):
        name = sys.get('name', '')
        bind_item_name = sys.get('bindItemName', '')
        output.append(f"| {idx} | {name} | {bind_item_name} |")

    return "\n".join(output)


def search_community(charge_system_id, keyword, return_map=False):
    """
    搜索小区

    Args:
        charge_system_id: 收费系统 ID
        keyword: 小区名称关键词
        return_map: 如果为 True，返回 {名称: id} 字典；否则打印列表给用户
    """
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None if return_map else None

    headers = get_headers_with_cookies(ck_dict)

    try:
        response = requests.get(
            f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/getCommunityList",
            params={
                "chargeSystemID": charge_system_id,
                "page": 1,
                "pageSize": 100,
                "kw": keyword
            },
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"接口调用失败，状态码: {response.status_code}, 响应内容: {response.text}")
            return None if return_map else "请求异常，请稍后再试。"

        data = response.json()

        if data.get('code') != 0:
            msg = f"获取失败：{data.get('msg')}"
            return None if return_map else msg

        community_list = data.get('data', {}).get('list', [])

        if return_map:
            community_map = {}
            for comm in community_list:
                name = comm.get('name')
                comm_id = comm.get('id')
                if name and comm_id:
                    community_map[name] = comm_id
            return community_map
        else:
            return format_community_list(community_list)

    except requests.exceptions.RequestException as e:
        logger.error(f"接口调用发生异常: {e}")
        return None if return_map else f"接口调用发生异常: {str(e)}"


def format_community_list(community_list):
    if not community_list:
        return "没有找到匹配的小区。"

    output = ["### 找到的小区\n"]
    output.append("| 序号 | 小区名称 | 地址 | 房屋数 |")
    output.append("| :--- | :--- | :--- | :--- |")

    for idx, comm in enumerate(community_list, 1):
        name = comm.get('name', '')
        address = comm.get('address', '')
        house_num = comm.get('houseNum', 0)
        output.append(f"| {idx} | {name} | {address} | {house_num} |")

    return "\n".join(output)


def get_current_year_time_range():
    """
    获取本年度的开始和结束时间戳

    Returns:
        (start_time, end_time) 时间戳元组
    """
    now = datetime.now()
    # 本年度开始时间：1月1日 00:00:00
    start_of_year = datetime(now.year, 1, 1, 0, 0, 0)
    # 本年度结束时间：12月31日 23:59:59
    end_of_year = datetime(now.year, 12, 31, 23, 59, 59)

    # 转换为时间戳
    start_time = int(start_of_year.timestamp())
    end_time = int(end_of_year.timestamp())

    return start_time, end_time


def parse_iso_date(date_str):
    """
    解析 ISO 格式的日期字符串 (YYYY-MM-DD)

    Args:
        date_str: 日期字符串，格式为 YYYY-MM-DD

    Returns:
        datetime 对象
    """
    date_str = date_str.strip()
    # 尝试解析 YYYY-MM-DD 格式
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        # 也支持 YYYY/MM/DD 格式
        try:
            return datetime.strptime(date_str, "%Y/%m/%d")
        except ValueError:
            raise ValueError(f"无法解析日期，请使用 YYYY-MM-DD 或 YYYY/MM/DD 格式: {date_str}")


def get_community_total_arrears(community_id: str, start_time: int = None, end_time: int = None) -> str:
    """
    获取小区欠费总额。

    Args:
        community_id: 小区ID
        start_time: 开始时间戳（可选）
        end_time: 结束时间戳（可选）
    """
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return

    headers = get_headers_with_cookies(ck_dict, {"communityid": community_id})

    params = {
        "id": community_id,
        "idType": 1,
        "assetType": 1,
        "page": 1,
        "pageSize": 20
    }

    # 如果指定了时间范围，添加到参数中
    if start_time is not None:
        params["startTime"] = start_time
    if end_time is not None:
        params["endTime"] = end_time

    try:
        response = requests.get(
            f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/getArrearsHouseList",
            params=params,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"接口调用失败，状态码: {response.status_code}, 响应内容: {response.text}")
            return "请求异常，请稍后再试。"

        response.raise_for_status()
        data = response.json()

        if start_time is not None and end_time is not None:
            # 本年度查询
            start_dt = datetime.fromtimestamp(start_time)
            end_dt = datetime.fromtimestamp(end_time)
            output = format_arrears_result(data, True, start_dt, end_dt)
        elif start_time is not None:
            output = format_arrears_result(data, True)
        else:
            output = format_arrears_result(data, False)
        logger.info(f"成功获取小区 {community_id} 的欠费总额信息")
        print(f"返回数据：{output}")
        return output

    except requests.exceptions.RequestException as e:
        logger.error(f"接口调用发生异常: {e}")
        return f"接口调用发生异常: {str(e)}"


def get_community_current_year_arrears(community_id: str) -> str:
    """
    获取小区本年度物业费欠费金额。

    Args:
        community_id: 小区ID
    """
    start_time, end_time = get_current_year_time_range()
    return get_community_total_arrears(community_id, start_time, end_time)


def format_arrears_result(raw_response, is_time_range=False, start_dt=None, end_dt=None):
    if isinstance(raw_response, str):
        res = json.loads(raw_response)
    else:
        res = raw_response

    if res.get('code') != 0:
        return f"获取失败：{res.get('msg')}"

    data = res.get('data', {})
    total_arrears = data.get('totalArrearsAmount', 0)
    total_arrears_yuan = total_arrears / 100.0

    total_houses = data.get('total', 0)
    community_name = data.get('communityName', '')

    if start_dt and end_dt:
        # 自定义日期范围
        start_str = start_dt.strftime("%Y年%m月%d日")
        end_str = end_dt.strftime("%Y年%m月%d日")
        title = f"### 小区物业费欠费统计（{start_str} 至 {end_str}）\n"
    elif is_time_range:
        title = "### 小区本年度物业费欠费统计\n"
    else:
        title = "### 小区欠费总额统计\n"

    output = [title]
    if community_name:
        output.append(f"**小区名称**: {community_name}")
    output.append(f"**欠费总额**: ¥{total_arrears_yuan:,.2f}")
    output.append(f"**涉及房屋数**: {total_houses} 户")

    return "\n".join(output)


def get_community_custom_range_arrears(community_id: str, start_time: int, end_time: int) -> str:
    """
    获取小区自定义时间范围内的物业费欠费金额

    Args:
        community_id: 小区ID
        start_time: 开始时间戳
        end_time: 结束时间戳
    """
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return

    headers = get_headers_with_cookies(ck_dict, {"communityid": community_id})

    params = {
        "id": community_id,
        "idType": 1,
        "assetType": 1,
        "page": 1,
        "pageSize": 20,
        "startTime": start_time,
        "endTime": end_time
    }

    try:
        response = requests.get(
            f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/getArrearsHouseList",
            params=params,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"接口调用失败，状态码: {response.status_code}, 响应内容: {response.text}")
            return "请求异常，请稍后再试。"

        response.raise_for_status()
        data = response.json()

        start_dt = datetime.fromtimestamp(start_time)
        end_dt = datetime.fromtimestamp(end_time)
        output = format_arrears_result(data, True, start_dt, end_dt)
        logger.info(f"成功获取小区 {community_id} 的自定义时间范围欠费信息")
        print(f"返回数据：{output}")
        return output

    except requests.exceptions.RequestException as e:
        logger.error(f"接口调用发生异常: {e}")
        return f"接口调用发生异常: {str(e)}"


def get_custom_range_arrears(charge_system_name=None, community_name=None, start_date_str=None, end_date_str=None):
    """
    通过名称和自定义日期范围查询欠费（智能模式）

    Args:
        charge_system_name: 收费系统名称
        community_name: 小区名称
        start_date_str: 开始日期 (YYYY-MM-DD 格式)
        end_date_str: 结束日期 (YYYY-MM-DD 格式)
    """
    # 检查必要参数
    if not charge_system_name:
        print("NEED_INFO: 请提供收费系统名称")
        print("提示：可以先使用 list_charge_systems 命令查看可用的收费系统")
        return

    if not community_name:
        print("NEED_INFO: 请提供小区名称")
        return

    if not start_date_str or not end_date_str:
        print("NEED_INFO: 请提供开始日期和结束日期")
        print("日期格式: YYYY-MM-DD")
        print("示例: python3 main.py get_custom_range_arrears <收费系统> <小区> 2025-01-01 2026-12-31")
        return

    # 解析日期
    try:
        start_dt = parse_iso_date(start_date_str)
        end_dt = parse_iso_date(end_date_str)
        # 设置结束时间为当天的 23:59:59
        end_dt = datetime(end_dt.year, end_dt.month, end_dt.day, 23, 59, 59)
    except ValueError as e:
        print(f"日期解析失败：{e}")
        print("请使用 YYYY-MM-DD 格式，例如：2025-01-01")
        return

    # 转换为时间戳
    start_time = int(start_dt.timestamp())
    end_time = int(end_dt.timestamp())

    # 获取收费系统映射
    system_map = get_user_charge_systems(return_map=True)
    if not system_map:
        print("获取收费系统列表失败")
        return

    # 查找收费系统 ID
    charge_system_id = system_map.get(charge_system_name)
    if not charge_system_id:
        print(f"未找到收费系统：{charge_system_name}")
        print("可用的收费系统：" + ", ".join(system_map.keys()))
        return

    # 搜索小区
    community_map = search_community(charge_system_id, community_name, return_map=True)
    if community_map is None:
        print("搜索小区失败")
        return

    if not community_map:
        print(f"未找到匹配的小区：{community_name}")
        return

    if len(community_map) == 1:
        # 只有一个匹配，直接查询
        comm_name, comm_id = next(iter(community_map.items()))
        print(f"找到小区：{comm_name}")
        print(f"查询时间范围：{start_dt.strftime('%Y年%m月%d日')} 至 {end_dt.strftime('%Y年%m月%d日')}")
        get_community_custom_range_arrears(str(comm_id), start_time, end_time)
    else:
        # 多个匹配，列出供用户选择
        print(f"找到多个匹配的小区，请使用完整的小区名称重新查询：")
        for name in community_map.keys():
            print(f"  - {name}")


def get_arrears(charge_system_name=None, community_name=None):
    """
    通过名称查询欠费（智能模式）

    Args:
        charge_system_name: 收费系统名称
        community_name: 小区名称
    """
    # 检查必要参数
    if not charge_system_name:
        print("NEED_INFO: 请提供收费系统名称")
        print("提示：可以先使用 list_charge_systems 命令查看可用的收费系统")
        return

    if not community_name:
        print("NEED_INFO: 请提供小区名称")
        return

    # 获取收费系统映射
    system_map = get_user_charge_systems(return_map=True)
    if not system_map:
        print("获取收费系统列表失败")
        return

    # 查找收费系统 ID
    charge_system_id = system_map.get(charge_system_name)
    if not charge_system_id:
        print(f"未找到收费系统：{charge_system_name}")
        print("可用的收费系统：" + ", ".join(system_map.keys()))
        return

    # 搜索小区
    community_map = search_community(charge_system_id, community_name, return_map=True)
    if community_map is None:
        print("搜索小区失败")
        return

    if not community_map:
        print(f"未找到匹配的小区：{community_name}")
        return

    if len(community_map) == 1:
        # 只有一个匹配，直接查询
        comm_name, comm_id = next(iter(community_map.items()))
        print(f"找到小区：{comm_name}")
        get_community_total_arrears(str(comm_id))
    else:
        # 多个匹配，列出供用户选择
        print(f"找到多个匹配的小区，请使用完整的小区名称重新查询：")
        for name in community_map.keys():
            print(f"  - {name}")


def get_current_year_arrears(charge_system_name=None, community_name=None):
    """
    通过名称查询本年度物业费欠费（智能模式）

    Args:
        charge_system_name: 收费系统名称
        community_name: 小区名称
    """
    # 检查必要参数
    if not charge_system_name:
        print("NEED_INFO: 请提供收费系统名称")
        print("提示：可以先使用 list_charge_systems 命令查看可用的收费系统")
        return

    if not community_name:
        print("NEED_INFO: 请提供小区名称")
        return

    # 获取收费系统映射
    system_map = get_user_charge_systems(return_map=True)
    if not system_map:
        print("获取收费系统列表失败")
        return

    # 查找收费系统 ID
    charge_system_id = system_map.get(charge_system_name)
    if not charge_system_id:
        print(f"未找到收费系统：{charge_system_name}")
        print("可用的收费系统：" + ", ".join(system_map.keys()))
        return

    # 搜索小区
    community_map = search_community(charge_system_id, community_name, return_map=True)
    if community_map is None:
        print("搜索小区失败")
        return

    if not community_map:
        print(f"未找到匹配的小区：{community_name}")
        return

    if len(community_map) == 1:
        # 只有一个匹配，直接查询
        comm_name, comm_id = next(iter(community_map.items()))
        print(f"找到小区：{comm_name}")
        get_community_current_year_arrears(str(comm_id))
    else:
        # 多个匹配，列出供用户选择
        print(f"找到多个匹配的小区，请使用完整的小区名称重新查询：")
        for name in community_map.keys():
            print(f"  - {name}")


def logout() -> str:
    """
    登出马克账号。
    """
    session_mgr.clear_session()
    logger.info("成功登出马克账号")
    return "已成功登出马克账号。"


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""

    if command == "get_my_team":
        get_my_team()
    elif command == "logout":
        result = logout()
        print(result)
    elif command == "list_charge_systems":
        result = get_user_charge_systems(return_map=False)
        if result:
            print(result)
    elif command == "search_community":
        if len(sys.argv) < 4:
            print("错误：请提供收费系统名称和小区关键词")
            print("用法: python3 main.py search_community <收费系统名称> <小区关键词>")
        else:
            charge_system_name = sys.argv[2]
            keyword = sys.argv[3]

            # 先获取收费系统 ID
            system_map = get_user_charge_systems(return_map=True)
            if not system_map:
                print("获取收费系统列表失败")
            elif charge_system_name not in system_map:
                print(f"未找到收费系统：{charge_system_name}")
                print("可用的收费系统：" + ", ".join(system_map.keys()))
            else:
                charge_system_id = system_map[charge_system_name]
                result = search_community(charge_system_id, keyword, return_map=False)
                if result:
                    print(result)
    elif command == "get_arrears":
        if len(sys.argv) < 3:
            print("错误：请提供收费系统名称和小区名称")
            print("用法: python3 main.py get_arrears <收费系统名称> <小区名称>")
        else:
            charge_system_name = sys.argv[2]
            community_name = sys.argv[3] if len(sys.argv) > 3 else None
            get_arrears(charge_system_name, community_name)
    elif command == "get_current_year_arrears":
        if len(sys.argv) < 3:
            print("错误：请提供收费系统名称和小区名称")
            print("用法: python3 main.py get_current_year_arrears <收费系统名称> <小区名称>")
        else:
            charge_system_name = sys.argv[2]
            community_name = sys.argv[3] if len(sys.argv) > 3 else None
            get_current_year_arrears(charge_system_name, community_name)
    elif command == "get_custom_range_arrears":
        if len(sys.argv) < 6:
            print("错误：请提供收费系统名称、小区名称、开始日期和结束日期")
            print("用法: python3 main.py get_custom_range_arrears <收费系统名称> <小区名称> <开始日期> <结束日期>")
            print("日期格式: YYYY-MM-DD")
            print("示例: python3 main.py get_custom_range_arrears <收费系统> <小区> 2025-01-01 2026-12-31")
        else:
            charge_system_name = sys.argv[2]
            community_name = sys.argv[3]
            start_date_str = sys.argv[4]
            end_date_str = sys.argv[5]
            get_custom_range_arrears(charge_system_name, community_name, start_date_str, end_date_str)
    elif command == "_get_charge_system_map":
        # 内部命令：返回 JSON 格式的收费系统映射
        system_map = get_user_charge_systems(return_map=True)
        print(json.dumps(system_map, ensure_ascii=False))
    elif command == "_get_community_map":
        # 内部命令：返回 JSON 格式的小区映射
        if len(sys.argv) < 4:
            print("{}")
        else:
            charge_system_id = sys.argv[2]
            keyword = sys.argv[3]
            community_map = search_community(charge_system_id, keyword, return_map=True)
            print(json.dumps(community_map, ensure_ascii=False) if community_map else "{}")
    elif command == "get_community_total_arrears":
        # 保留原有命令，兼容旧版本
        if len(sys.argv) < 3:
            print("错误：请提供小区ID参数")
            print("用法: python3 main.py get_community_total_arrears <小区ID>")
        else:
            community_id = sys.argv[2]
            get_community_total_arrears(community_id)
    elif command == "get_community_current_year_arrears":
        # 通过小区ID查询本年度物业费欠费
        if len(sys.argv) < 3:
            print("错误：请提供小区ID参数")
            print("用法: python3 main.py get_community_current_year_arrears <小区ID>")
        else:
            community_id = sys.argv[2]
            get_community_current_year_arrears(community_id)
    else:
        print("错误：未知的指令或参数不足")
        print("可用指令:")
        print("  get_my_team - 查看我加入的团队列表")
        print("  logout - 登出马克账号")
        print("  list_charge_systems - 列出可用的收费系统")
        print("  search_community <收费系统名称> <小区关键词> - 搜索小区")
        print("  get_arrears <收费系统名称> <小区名称> - 通过名称查询欠费")
        print("  get_current_year_arrears <收费系统名称> <小区名称> - 通过名称查询本年度物业费欠费")
        print("  get_custom_range_arrears <收费系统名称> <小区名称> <日期范围> - 自定义时间范围查询欠费")
        print("  get_community_total_arrears <小区ID> - 通过ID查询欠费（旧版）")
        print("  get_community_current_year_arrears <小区ID> - 通过ID查询本年度物业费欠费")
