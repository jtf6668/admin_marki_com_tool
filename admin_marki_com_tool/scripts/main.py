import os
import sys
import time
import json
import socket
import requests
import subprocess
import urllib.parse
from typing import Optional
from datetime import datetime, timedelta
from utils import SessionManager
from logger import logger


API_BASE_URL = "https://admin-api-test.markiapp.com"
CHARGE_API_BASE_URL = "https://charge-api-test.markiapp.com"
BASE_DOMAIN = "markiapp.com"
#AUTH_URL = f"https://os-lgn.{BASE_DOMAIN}/lgn/login/authorize.do" # 生产环境
#APP_ID = "1435186595"

AUTH_URL = f"https://sttc-os-lgn-test.{BASE_DOMAIN}/lgn/login/authorize.do" # 测试环境，注意：测试环境的 appid 和生产环境不一样，不能混用
APP_ID = "1435186595"


session_mgr = SessionManager()


# === 匹配缓存相关函数 ===
def get_match_cache_path():
    """获取匹配缓存文件路径"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, '.match_cache.json')


def save_match_cache(community_id, nodes):
    """
    保存匹配列表到缓存

    Args:
        community_id: 小区ID
        nodes: 匹配的节点列表
    """
    cache_data = {
        "timestamp": time.time(),
        "community_id": str(community_id),
        "nodes": nodes
    }
    try:
        with open(get_match_cache_path(), 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        logger.info(f"已保存匹配缓存，包含 {len(nodes)} 个节点")
    except Exception as e:
        logger.warning(f"保存匹配缓存失败: {e}")


def load_match_cache():
    """
    从缓存加载匹配列表（5分钟内有效）

    Returns:
        dict: {community_id, nodes} 或 None
    """
    cache_path = get_match_cache_path()
    if not os.path.exists(cache_path):
        return None

    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)

        # 检查是否过期（5分钟）
        if time.time() - cache_data.get('timestamp', 0) > 300:
            logger.info("匹配缓存已过期")
            clear_match_cache()
            return None

        logger.info(f"从缓存加载了 {len(cache_data.get('nodes', []))} 个匹配节点")
        return cache_data
    except Exception as e:
        logger.warning(f"加载匹配缓存失败: {e}")
        return None


def clear_match_cache():
    """清除匹配缓存"""
    cache_path = get_match_cache_path()
    if os.path.exists(cache_path):
        try:
            os.remove(cache_path)
            logger.info("已清除匹配缓存")
        except Exception as e:
            logger.warning(f"清除匹配缓存失败: {e}")


# === 短信催缴确认缓存相关函数 ===
def get_sms_confirmation_cache_path():
    """获取短信催缴确认缓存文件路径"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, '.sms_confirmation_cache.json')


def save_sms_confirmation(data):
    """保存短信催缴确认数据到缓存"""
    cache_data = {
        "timestamp": time.time(),
        "data": data
    }
    try:
        with open(get_sms_confirmation_cache_path(), 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        logger.info(f"已保存短信催缴确认数据")
    except Exception as e:
        logger.warning(f"保存短信催缴确认数据失败: {e}")


def load_sms_confirmation():
    """从缓存加载短信催缴确认数据（5分钟内有效）

    Returns:
        dict: 确认数据或 None
    """
    cache_path = get_sms_confirmation_cache_path()
    if not os.path.exists(cache_path):
        return None

    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)

        # 检查是否过期（5分钟）
        if time.time() - cache_data.get('timestamp', 0) > 300:
            logger.info("短信催缴确认缓存已过期")
            clear_sms_confirmation()
            return None

        logger.info(f"从缓存加载了短信催缴确认数据")
        return cache_data.get('data')
    except Exception as e:
        logger.warning(f"加载短信催缴确认数据失败: {e}")
        return None


def clear_sms_confirmation():
    """清除短信催缴确认缓存"""
    cache_path = get_sms_confirmation_cache_path()
    if os.path.exists(cache_path):
        try:
            os.remove(cache_path)
            logger.info("已清除短信催缴确认缓存")
        except Exception as e:
            logger.warning(f"清除短信催缴确认缓存失败: {e}")


# === 催缴工单确认缓存相关函数 ===
def get_work_order_confirmation_cache_path():
    """获取催缴工单确认缓存文件路径"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, '.work_order_confirmation_cache.json')


def save_work_order_confirmation(data):
    """保存催缴工单确认数据到缓存"""
    cache_data = {
        "timestamp": time.time(),
        "data": data
    }
    try:
        with open(get_work_order_confirmation_cache_path(), 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        logger.info(f"已保存催缴工单确认数据")
    except Exception as e:
        logger.warning(f"保存催缴工单确认数据失败: {e}")


def load_work_order_confirmation():
    """从缓存加载催缴工单确认数据（5分钟内有效）

    Returns:
        dict: 确认数据或 None
    """
    cache_path = get_work_order_confirmation_cache_path()
    if not os.path.exists(cache_path):
        return None

    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)

        # 检查是否过期（5分钟）
        if time.time() - cache_data.get('timestamp', 0) > 300:
            logger.info("催缴工单确认缓存已过期")
            clear_work_order_confirmation()
            return None

        logger.info(f"从缓存加载了催缴工单确认数据")
        return cache_data.get('data')
    except Exception as e:
        logger.warning(f"加载催缴工单确认数据失败: {e}")
        return None


def clear_work_order_confirmation():
    """清除催缴工单确认缓存"""
    cache_path = get_work_order_confirmation_cache_path()
    if os.path.exists(cache_path):
        try:
            os.remove(cache_path)
            logger.info("已清除催缴工单确认缓存")
        except Exception as e:
            logger.warning(f"清除催缴工单确认缓存失败: {e}")


# === 用户选择解析函数 ===
def parse_user_selection(input_str, matching_nodes):
    """
    解析用户选择，支持多种方式

    Args:
        input_str: 用户输入字符串
        matching_nodes: 上一次的匹配节点列表

    Returns:
        dict: 选中的节点，或 None（表示需要继续模糊匹配）
    """
    if not input_str or not matching_nodes:
        return None

    input_str = input_str.strip()
    node_count = len(matching_nodes)

    # 中文数字映射
    chinese_numbers = {
        "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
        "六": 6, "七": 7, "八": 8, "九": 9, "十": 10
    }

    # 1. 检查是否为阿拉伯数字序号（"1"、"2"）
    if input_str.isdigit():
        idx = int(input_str) - 1
        if 0 <= idx < node_count:
            logger.info(f"用户通过阿拉伯数字选择: {idx + 1}")
            return matching_nodes[idx]

    # 2. 检查是否为中文数字序号（"一"、"二"）
    if input_str in chinese_numbers:
        idx = chinese_numbers[input_str] - 1
        if 0 <= idx < node_count:
            logger.info(f"用户通过中文数字选择: {input_str}")
            return matching_nodes[idx]

    # 3. 检查是否为文字描述（"第一个"、"第二个"、"最后一个"）
    if "第" in input_str and ("个" in input_str or "项" in input_str):
        # 提取中文或阿拉伯数字
        for cn_num, num in chinese_numbers.items():
            if cn_num in input_str:
                idx = num - 1
                if 0 <= idx < node_count:
                    logger.info(f"用户通过文字描述选择: {input_str}")
                    return matching_nodes[idx]
        # 检查阿拉伯数字
        for char in input_str:
            if char.isdigit():
                idx = int(char) - 1
                if 0 <= idx < node_count:
                    logger.info(f"用户通过文字描述选择: {input_str}")
                    return matching_nodes[idx]

    if "最后" in input_str:
        logger.info("用户选择最后一个")
        return matching_nodes[-1]

    # 4. 检查是否包含 "/"，尝试精确匹配
    if "/" in input_str:
        # 先尝试完全匹配
        for node in matching_nodes:
            if node.get('full_name', node.get('name', '')) == input_str:
                logger.info(f"用户通过完整路径精确匹配: {input_str}")
                return node
        # 再尝试包含匹配（忽略"查询"、"欠费"等词）
        clean_input = input_str.replace("查询", "").replace("的欠费", "").replace("欠费", "").strip()
        for node in matching_nodes:
            node_name = node.get('full_name', node.get('name', ''))
            if clean_input in node_name:
                logger.info(f"用户通过路径包含匹配: {clean_input} -> {node_name}")
                return node

    # 5. 尝试直接匹配节点名称（去除"查询"、"欠费"等词）
    clean_input = input_str.replace("查询", "").replace("的欠费", "").replace("欠费", "").strip()
    for node in matching_nodes:
        node_name = node.get('full_name', node.get('name', ''))
        if clean_input == node_name or clean_input == node.get('name', ''):
            logger.info(f"用户通过名称匹配: {clean_input}")
            return node

    return None


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
            print(f"AUTH_REQUIRED")
            print(f"LOGIN_URL:{existing_url}")
            print(f"MESSAGE:检测到您未登录马克智慧物业系统，请点击以下链接登录：")
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

        print(f"AUTH_REQUIRED")
        print(f"LOGIN_URL:{login_url}")
        print(f"MESSAGE:检测到您未登录马克智慧物业系统，请点击以下链接登录：")

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


def get_property_charge_item_id(community_id: str, charge_system_id: str) -> Optional[str]:
    """
    获取小区物业费收费项目ID。

    Args:
        community_id: 小区ID
        charge_system_id: 收费系统ID

    Returns:
        物业费ID，如果找不到返回 None
    """
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None

    headers = get_headers_with_cookies(ck_dict, {"communityid": str(community_id)})

    request_body = {
        "index": "",
        "communityID": int(community_id),
        "pageSize": 40,
        "kw": "",
        "idList": [],
        "itemType": 57
    }

    try:
        response = requests.post(
            f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/getCommunityItemList",
            json=request_body,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"获取收费项目列表失败，状态码: {response.status_code}, 响应内容: {response.text}")
            return None

        data = response.json()
        if data.get('code') != 0:
            logger.error(f"获取收费项目列表失败，错误信息: {data.get('msg')}")
            return None

        items = data.get('data', {}).get('list', [])
        if not items:
            logger.warning(f"小区 {community_id} 未找到任何收费项目")
            return None

        # 提取所有项目的 id 和 name
        item_list = [(str(item['id']), item['name']) for item in items if 'id' in item and 'name' in item]

        # 第一步：精确匹配标准名称
        exact_names = ["物业费", "物业管理费", "物业服务费"]
        for item_id, item_name in item_list:
            if item_name in exact_names:
                logger.info(f"[精确匹配] 找到物业费项目: {item_name} (ID: {item_id})")
                print(f"✓ 精确匹配找到物业费项目：{item_name} (ID: {item_id})")
                return item_id

        # 第二步：模糊匹配名称中包含"物业"的项目
        property_candidates = [
            (item_id, item_name)
            for item_id, item_name in item_list
            if '物业' in item_name
        ]

        if len(property_candidates) >= 1:
            # 展示所有找到的含"物业"的候选项目
            candidate_names = [name for _, name in property_candidates]
            print(f"ℹ 找到 {len(property_candidates)} 个含'物业'的收费项目：{', '.join(candidate_names)}")

            if len(property_candidates) == 1:
                # 只有一个匹配，直接返回
                item_id, item_name = property_candidates[0]
                logger.info(f"[模糊匹配] 找到物业费项目: {item_name} (ID: {item_id})")
                print(f"✓ 只有一个匹配，直接使用：{item_name} (ID: {item_id})")
                return item_id
            else:
                # 多个匹配，LLM识别判断哪个最可能是物业费
                logger.info(f"[LLM识别] 找到多个包含'物业'的项目，共 {len(property_candidates)} 个，进行智能识别")
            # 多个匹配，LLM识别判断哪个最可能是物业费
            logger.info(f"[LLM识别] 找到多个包含'物业'的项目，共 {len(property_candidates)} 个，进行智能识别")
            candidate_names = [name for _, name in property_candidates]
            print(f"ℹ 找到多个含'物业'的收费项目：{', '.join(candidate_names)}")

            # LLM判断规则：优先选择名称最接近标准物业费的
            # 评分规则：精确匹配"物业费"得分最高，其次"物业管理费"，越短越好
            scored_candidates = []
            for item_id, name in property_candidates:
                score = 0
                if name == "物业费":
                    score = 100
                elif "物业管理费" in name:
                    score = 90
                elif "物业服务费" in name:
                    score = 85
                elif "物业费" in name:
                    score = 80
                elif "物业" in name:
                    score = 70 - len(name)  # 越短得分越高
                scored_candidates.append((-score, item_id, name))  # 负号用于升序排序

            scored_candidates.sort()
            best_score = -scored_candidates[0][0]
            best_item_id = scored_candidates[0][1]
            best_name = scored_candidates[0][2]

            logger.info(f"[LLM识别] LLM选择：{best_name} (ID: {best_item_id})，置信度得分：{best_score}")
            print(f"🤖 LLM识别判断：最可能是物业费的项目是【{best_name}】(ID: {best_item_id})，置信度得分 {best_score}/100")
            print(f"✓ 已使用LLM选择的项目进行过滤")
            return best_item_id
        else:
            # 找不到包含"物业"的项目，返回 None，让用户兜底
            logger.warning(f"小区 {community_id} 未能识别出物业费项目，所有项目: {[name for _, name in item_list]}")
            print(f"⚠ 未找到物业费项目，所有收费项目：{', '.join([name for _, name in item_list])}")
            print(f"⚠ 将返回所有费用类型的欠费总额（包含停车费、公摊水电费等）")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"调用getCommunityItemList接口发生异常: {e}")
        return None


def get_charge_item_id_by_name(community_id: str, charge_system_id: str, fee_type: str) -> Optional[str]:
    """
    根据费用类型名称获取收费项目ID。

    支持的费用类型：物业费、水费、电费、燃气费

    Args:
        community_id: 小区ID
        charge_system_id: 收费系统ID
        fee_type: 费用类型名称（物业费、水费、电费、燃气费）

    Returns:
        收费项目ID，如果找不到返回 None
    """
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None

    headers = get_headers_with_cookies(ck_dict, {"communityid": str(community_id)})

    request_body = {
        "index": "",
        "communityID": int(community_id),
        "pageSize": 40,
        "kw": "",
        "idList": [],
        "itemType": 57
    }

    try:
        response = requests.post(
            f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/getCommunityItemList",
            json=request_body,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"获取收费项目列表失败，状态码: {response.status_code}, 响应内容: {response.text}")
            return None

        data = response.json()
        if data.get('code') != 0:
            logger.error(f"获取收费项目列表失败，错误信息: {data.get('msg')}")
            return None

        items = data.get('data', {}).get('list', [])
        if not items:
            logger.warning(f"小区 {community_id} 未找到任何收费项目")
            print(f"⚠ 小区未找到任何收费项目")
            return None

        # 提取所有项目的 id 和 name
        item_list = [(str(item['id']), item['name']) for item in items if 'id' in item and 'name' in item]

        # 根据费用类型定义匹配规则
        match_rules = {
            '物业费': {
                'exact': ["物业费", "物业管理费", "物业服务费"],
                'fuzzy_keywords': ["物业"]
            },
            '水费': {
                'exact': ["水费", "自来水费", "水资源费"],
                'fuzzy_keywords': ["水"]
            },
            '电费': {
                'exact': ["电费", "公共电费", "公摊电费"],
                'fuzzy_keywords': ["电"]
            },
            '燃气费': {
                'exact': ["燃气费", "煤气费", "天然气费"],
                'fuzzy_keywords': ["燃气", "煤气"]
            }
        }

        rule = match_rules.get(fee_type)
        if not rule:
            # 如果不是预定义的类型，尝试直接模糊匹配
            logger.info(f"未预定义费用类型 '{fee_type}'，尝试直接模糊匹配")
            rule = {
                'exact': [fee_type],
                'fuzzy_keywords': [fee_type]
            }

        # 第一步：精确匹配
        for exact_name in rule['exact']:
            for item_id, item_name in item_list:
                if item_name == exact_name:
                    logger.info(f"[精确匹配] 找到{fee_type}项目: {item_name} (ID: {item_id})")
                    print(f"✓ 精确匹配找到{fee_type}项目：{item_name} (ID: {item_id})")
                    return item_id

        # 第二步：模糊匹配（包含关键词）
        fuzzy_candidates = []
        for item_id, item_name in item_list:
            for kw in rule['fuzzy_keywords']:
                if kw in item_name:
                    fuzzy_candidates.append((item_id, item_name))
                    break

        if not fuzzy_candidates:
            logger.warning(f"小区 {community_id} 未找到{fee_type}收费项目，所有项目: {[name for _, name in item_list]}")
            print(f"⚠ 未找到{fee_type}收费项目，所有收费项目：{', '.join([name for _, name in item_list])}")
            print(f"⚠ 将返回所有费用类型的欠费总额")
            return None

        if len(fuzzy_candidates) == 1:
            # 只有一个匹配，直接返回
            item_id, item_name = fuzzy_candidates[0]
            logger.info(f"[模糊匹配] 找到{fee_type}项目: {item_name} (ID: {item_id})")
            print(f"✓ 只有一个匹配，直接使用：{item_name} (ID: {item_id})")
            return item_id
        else:
            # 多个匹配，评分排序选择最佳
            candidate_names = [name for _, name in fuzzy_candidates]
            print(f"ℹ 找到 {len(fuzzy_candidates)} 个含{fee_type}的收费项目：{', '.join(candidate_names)}")

            # 评分规则：精确匹配完整费用类型得分最高，越短越好
            scored_candidates = []
            for item_id, name in fuzzy_candidates:
                score = 0
                if name == fee_type:
                    score = 100
                elif any(kw in name for kw in rule['exact']):
                    score = 90
                elif any(kw in name for kw in rule['fuzzy_keywords']):
                    score = 70 - len(name)  # 越短得分越高
                scored_candidates.append((-score, item_id, name))  # 负号用于升序排序

            scored_candidates.sort()
            best_score = -scored_candidates[0][0]
            best_item_id = scored_candidates[0][1]
            best_name = scored_candidates[0][2]

            logger.info(f"[智能识别] 选择：{best_name} (ID: {best_item_id})，置信度得分：{best_score}")
            print(f"🤖 智能识别判断：最可能是{fee_type}的项目是【{best_name}】(ID: {best_item_id})，置信度得分 {best_score}/100")
            print(f"✓ 已使用智能选择的项目进行过滤")
            return best_item_id

    except requests.exceptions.RequestException as e:
        logger.error(f"调用getCommunityItemList接口发生异常: {e}")
        return None


def get_community_total_arrears(community_id: str, start_time: int = None, end_time: int = None, charge_system_id: str = None) -> str:
    """
    获取小区欠费总额。

    Args:
        community_id: 小区ID
        start_time: 开始时间戳（可选）
        end_time: 结束时间戳（可选）
        charge_system_id: 收费系统ID（可选，用于获取物业费项目ID）
    """
    """
    获取小区欠费总额。

    Args:
        community_id: 小区ID
        start_time: 开始时间戳（可选）
        end_time: 结束时间戳（可选）
        charge_system_id: 收费系统ID（可选，用于获取物业费项目ID）
    """
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return

    headers = get_headers_with_cookies(ck_dict, {"communityid": str(community_id)})

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

    # 如果提供了收费系统ID，尝试获取物业费项目ID并添加过滤
    if charge_system_id is not None:
        property_item_id = get_property_charge_item_id(community_id, charge_system_id)
        if property_item_id:
            params["selectChargeItemList"] = property_item_id
            logger.info(f"已添加物业费过滤，项目ID: {property_item_id}")
        else:
            logger.warning(f"未找到物业费项目，将返回所有费用类型的欠费总额")

    # 打印请求参数用于调试
    print(f"\n[DEBUG] 实际发送的请求参数:")
    print(f"[DEBUG] {json.dumps(params, indent=2, ensure_ascii=False)}")

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


def get_community_current_year_arrears(community_id: str, charge_system_id: str = None) -> str:
    """
    获取小区本年度物业费欠费金额。

    Args:
        community_id: 小区ID
        charge_system_id: 收费系统ID（可选，用于获取物业费项目ID）
    """
    start_time, end_time = get_current_year_time_range()
    return get_community_total_arrears(community_id, start_time, end_time, charge_system_id)


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


def get_community_custom_range_arrears(community_id: str, start_time: int, end_time: int, charge_system_id: str = None) -> str:
    """
    获取小区自定义时间范围内的物业费欠费金额

    Args:
        community_id: 小区ID
        start_time: 开始时间戳
        end_time: 结束时间戳
        charge_system_id: 收费系统ID（可选，用于获取物业费项目ID）
    """
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return

    headers = get_headers_with_cookies(ck_dict, {"communityid": str(community_id)})

    params = {
        "id": community_id,
        "idType": 1,
        "assetType": 1,
        "page": 1,
        "pageSize": 20,
        "startTime": start_time,
        "endTime": end_time
    }

    # 如果提供了收费系统ID，尝试获取物业费项目ID并添加过滤
    if charge_system_id is not None:
        property_item_id = get_property_charge_item_id(community_id, charge_system_id)
        if property_item_id:
            params["selectChargeItemList"] = property_item_id
            logger.info(f"已添加物业费过滤，项目ID: {property_item_id}")
        else:
            logger.warning(f"未找到物业费项目，将返回所有费用类型的欠费总额")

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
        get_community_custom_range_arrears(str(comm_id), start_time, end_time, charge_system_id)
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
        get_community_current_year_arrears(str(comm_id), charge_system_id)
    else:
        # 多个匹配，列出供用户选择
        print(f"找到多个匹配的小区，请使用完整的小区名称重新查询：")
        for name in community_map.keys():
            print(f"  - {name}")


def get_today_time_range():
    """
    获取今天的开始和结束时间戳

    Returns:
        (start_time, end_time) 时间戳元组
    """
    now = datetime.now()
    # 今天开始时间：00:00:00
    start_of_day = datetime(now.year, now.month, now.day, 0, 0, 0)
    # 今天结束时间：23:59:59
    end_of_day = datetime(now.year, now.month, now.day, 23, 59, 59)

    # 转换为时间戳
    start_time = int(start_of_day.timestamp())
    end_time = int(end_of_day.timestamp())

    return start_time, end_time


def get_deal_log(community_id: str, start_time: int, end_time: int) -> dict:
    """
    获取小区指定时间范围内的交易记录

    Args:
        community_id: 小区ID
        start_time: 开始时间戳
        end_time: 结束时间戳

    Returns:
        交易记录数据字典
    """
    import random
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None

    headers = get_headers_with_cookies(ck_dict, {"communityid": str(community_id)})

    # 使用正确的参数名
    payload = {
        "__r__": random.random(),
        "current": 1,
        "dealType": [],
        "payChannel": [],
        "maxDealTime": end_time,
        "minDealTime": start_time,
        "communityId": int(community_id),
        "assetID": 0,
        "page": 1,
        "pageSize": 1000  # 获取足够多的记录
    }

    try:
        response = requests.post(
            f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/getDealLogPost",
            json=payload,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"接口调用失败，状态码: {response.status_code}, 响应内容: {response.text}")
            return None

        response.raise_for_status()
        data = response.json()

        if data.get('code') != 0:
            logger.error(f"获取交易记录失败: {data.get('msg')}")
            return None

        return data.get('data', {})

    except requests.exceptions.RequestException as e:
        logger.error(f"接口调用发生异常: {e}")
        return None


def format_today_stats(community_name: str, deal_data: dict, start_dt: datetime = None, end_dt: datetime = None) -> str:
    """
    格式化统计数据

    Args:
        community_name: 小区名称
        deal_data: 交易数据
        start_dt: 开始时间（可选，不传则表示今日）
        end_dt: 结束时间（可选，不传则表示今日）

    Returns:
        格式化后的统计文本
    """
    if start_dt and end_dt:
        if start_dt.date() == end_dt.date():
            date_str = start_dt.strftime("%Y年%m月%d日")
        else:
            date_str = f"{start_dt.strftime('%Y年%m月%d日')} 至 {end_dt.strftime('%Y年%m月%d日')}"
    else:
        date_str = datetime.now().strftime("%Y年%m月%d日")
    output = [f"### {community_name} {date_str} 收入统计\n"]

    list_data = deal_data.get('list', [])

    # 统计各项数据
    total_income = deal_data.get('incomeTotalAmount', 0) / 100.0
    total_bill = deal_data.get('billTotalAmount', 0) / 100.0
    total_deposit = deal_data.get('depositTotalAmount', 0) / 100.0

    cash_income = 0  # 现金收入（需要根据payChannel判断）
    prepay_recharge = 0  # 预存款充值 (dealType=1)
    deposit_collect = 0  # 押金收取 (dealType=5)
    pay_count = len(list_data)  # 缴费笔数

    # 按收费项统计（需要确认收费项字段，这里先按dealType统计）
    charge_item_stats = {}
    # 按支付方式统计
    pay_channel_stats = {}
    # 按收款员统计
    payee_stats = {}

    deal_type_map = {
        1: "预存款充值",
        2: "预存款退款",
        3: "账单实收",
        4: "账单退款",
        5: "收取押金",
        6: "退还押金"
    }

    for deal in list_data:
        deal_type = deal.get('dealType')
        income_amount = deal.get('incomeAmount', 0)
        income_yuan = income_amount / 100.0
        pay_channel = deal.get('payChannelStr', '未知')
        payee = deal.get('payee', '未知')

        # 预存款充值
        if deal_type == 1:
            prepay_recharge += income_yuan
        # 押金收取
        elif deal_type == 5:
            deposit_collect += income_yuan

        # 按交易类型统计（作为收费项统计）
        type_name = deal_type_map.get(deal_type, f'其他({deal_type})')
        if type_name not in charge_item_stats:
            charge_item_stats[type_name] = 0
        charge_item_stats[type_name] += income_yuan

        # 按支付方式统计
        if pay_channel not in pay_channel_stats:
            pay_channel_stats[pay_channel] = 0
        pay_channel_stats[pay_channel] += income_yuan

        # 按收款员统计
        if payee not in payee_stats:
            payee_stats[payee] = 0
        payee_stats[payee] += income_yuan

    # 基础统计
    output.append(f"**总收入**: ¥{total_income:,.2f}")
    output.append(f"**账单实收**: ¥{total_bill:,.2f}")
    output.append(f"**预存款充值**: ¥{prepay_recharge:,.2f}")
    output.append(f"**押金收取**: ¥{deposit_collect:,.2f}")
    output.append(f"**缴费笔数**: {pay_count} 笔")
    output.append("")

    # 按收费项统计
    output.append("**各收费项收入情况**:")
    for item_name, amount in charge_item_stats.items():
        output.append(f"  - {item_name}: ¥{amount:,.2f}")
    output.append("")

    # 按支付方式统计
    output.append("**各支付方式收入情况**:")
    for channel_name, amount in pay_channel_stats.items():
        output.append(f"  - {channel_name}: ¥{amount:,.2f}")
    output.append("")

    # 按收款员统计
    output.append("**各收款员收入情况**:")
    for payee_name, amount in payee_stats.items():
        output.append(f"  - {payee_name}: ¥{amount:,.2f}")

    return "\n".join(output)


def get_community_today_stats(community_id: str, community_name: str = None) -> str:
    """
    获取小区今日收入统计

    Args:
        community_id: 小区ID
        community_name: 小区名称（可选）

    Returns:
        统计结果文本
    """
    start_time, end_time = get_today_time_range()
    deal_data = get_deal_log(community_id, start_time, end_time)

    if deal_data is None:
        return "获取交易记录失败"

    if not community_name:
        community_name = "该小区"

    output = format_today_stats(community_name, deal_data)
    logger.info(f"成功获取小区 {community_id} 的今日收入统计")
    print(f"返回数据：{output}")
    return output


def get_today_stats(charge_system_name=None, community_name=None):
    """
    通过名称查询小区今日收入统计（智能模式）

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
        get_community_today_stats(str(comm_id), comm_name)
    else:
        # 多个匹配，列出供用户选择
        print(f"找到多个匹配的小区，请使用完整的小区名称重新查询：")
        for name in community_map.keys():
            print(f"  - {name}")


def get_community_custom_range_stats(community_id: str, start_time: int, end_time: int, community_name: str = None) -> str:
    """
    获取小区自定义时间范围的收入统计

    Args:
        community_id: 小区ID
        start_time: 开始时间戳
        end_time: 结束时间戳
        community_name: 小区名称（可选）

    Returns:
        统计结果文本
    """
    deal_data = get_deal_log(community_id, start_time, end_time)

    if deal_data is None:
        return "获取交易记录失败"

    if not community_name:
        community_name = "该小区"

    start_dt = datetime.fromtimestamp(start_time)
    end_dt = datetime.fromtimestamp(end_time)

    output = format_today_stats(community_name, deal_data, start_dt, end_dt)
    logger.info(f"成功获取小区 {community_id} 的自定义时间范围收入统计")
    print(f"返回数据：{output}")
    return output


def get_custom_range_stats(charge_system_name=None, community_name=None, start_date_str=None, end_date_str=None):
    """
    通过名称和自定义日期范围查询收入统计（智能模式）

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
        print("示例: python3 main.py get_custom_range_stats <收费系统> <小区> 2025-01-01 2026-12-31")
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
        get_community_custom_range_stats(str(comm_id), start_time, end_time, comm_name)
    else:
        # 多个匹配，列出供用户选择
        print(f"找到多个匹配的小区，请使用完整的小区名称重新查询：")
        for name in community_map.keys():
            print(f"  - {name}")


def get_current_month_time_range():
    """
    获取本月的开始和结束日期字符串（YYYY-MM-DD格式）

    Returns:
        (start_date_str, end_date_str) 日期字符串元组
    """
    now = datetime.now()
    # 本月开始日期：1日
    start_of_month = datetime(now.year, now.month, 1)
    # 本月结束日期：下一个月的第一天减去一天
    if now.month == 12:
        end_of_month = datetime(now.year + 1, 1, 1) - timedelta(days=1)
    else:
        end_of_month = datetime(now.year, now.month + 1, 1) - timedelta(days=1)

    start_date_str = start_of_month.strftime("%Y-%m-%d")
    end_date_str = end_of_month.strftime("%Y-%m-%d")

    return start_date_str, end_date_str


def get_outcome_detail_list(community_id: str, start_date_str: str, end_date_str: str) -> dict:
    """
    获取小区指定时间范围内的支出明细

    Args:
        community_id: 小区ID
        start_date_str: 开始日期 (YYYY-MM-DD)
        end_date_str: 结束日期 (YYYY-MM-DD)

    Returns:
        支出明细数据字典
    """
    import random
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None

    headers = get_headers_with_cookies(ck_dict, {"communityid": str(community_id)})

    params = {
        "startTimeStr": start_date_str,
        "endTimeStr": end_date_str,
        "communityID": int(community_id),
        "page": 1,
        "pageSize": 1000,  # 获取足够多的记录
        "r": random.random()
    }

    try:
        response = requests.get(
            f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/GetOutComeDetailList",
            params=params,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"接口调用失败，状态码: {response.status_code}, 响应内容: {response.text}")
            return None

        response.raise_for_status()
        data = response.json()

        if data.get('code') != 0:
            logger.error(f"获取支出明细失败: {data.get('msg')}")
            return None

        return data.get('data', {})

    except requests.exceptions.RequestException as e:
        logger.error(f"接口调用发生异常: {e}")
        return None


def format_monthly_expense_stats(community_name: str, outcome_data: dict, start_date_str: str, end_date_str) -> str:
    """
    格式化月度支出统计数据

    Args:
        community_name: 小区名称
        outcome_data: 支出数据
        start_date_str: 开始日期
        end_date_str: 结束日期

    Returns:
        格式化后的统计文本
    """
    start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date_str, "%Y-%m-%d")
    month_str = start_dt.strftime("%Y年%m月")

    output = [f"### {community_name} {month_str} 支出统计\n"]

    list_data = outcome_data.get('list', [])
    total_count = outcome_data.get('total', 0)

    # 统计总支出
    total_expense = 0.0
    # 按支出项目统计
    expense_item_stats = {}
    # 按收款人统计
    payee_stats = {}
    # 按操作人统计
    operator_stats = {}

    for item in list_data:
        amount = item.get('amount', 0)
        amount_yuan = amount / 100.0  # 分转元
        item_name = item.get('itemName', '未知项目')
        payee = item.get('payee', '未知收款人')
        operator = item.get('opName', '未知操作人')

        total_expense += amount_yuan

        # 按支出项目统计
        if item_name not in expense_item_stats:
            expense_item_stats[item_name] = 0
        expense_item_stats[item_name] += amount_yuan

        # 按收款人统计
        if payee not in payee_stats:
            payee_stats[payee] = 0
        payee_stats[payee] += amount_yuan

        # 按操作人统计
        if operator not in operator_stats:
            operator_stats[operator] = 0
        operator_stats[operator] += amount_yuan

    # 基础统计
    output.append(f"**统计时间**: {start_date_str} 至 {end_date_str}")
    output.append(f"**总支出**: ¥{total_expense:,.2f}")
    output.append(f"**支出笔数**: {total_count} 笔")
    output.append("")

    # 按支出项目统计
    output.append("**各支出项目情况**:")
    for item_name, amount in expense_item_stats.items():
        output.append(f"  - {item_name}: ¥{amount:,.2f}")
    output.append("")

    # 按收款人统计（如果有数据）
    if payee_stats and any(k for k in payee_stats.keys() if k != '未知收款人'):
        output.append("**各收款人情况**:")
        for payee_name, amount in payee_stats.items():
            if payee_name:  # 只显示非空的收款人
                output.append(f"  - {payee_name}: ¥{amount:,.2f}")
        output.append("")

    # 按操作人统计
    output.append("**各操作人情况**:")
    for operator_name, amount in operator_stats.items():
        output.append(f"  - {operator_name}: ¥{amount:,.2f}")

    return "\n".join(output)


def get_community_monthly_expense(community_id: str, community_name: str = None) -> str:
    """
    获取小区本月支出统计

    Args:
        community_id: 小区ID
        community_name: 小区名称（可选）

    Returns:
        统计结果文本
    """
    start_date_str, end_date_str = get_current_month_time_range()
    outcome_data = get_outcome_detail_list(community_id, start_date_str, end_date_str)

    if outcome_data is None:
        return "获取支出明细失败"

    if not community_name:
        community_name = "该小区"

    output = format_monthly_expense_stats(community_name, outcome_data, start_date_str, end_date_str)
    logger.info(f"成功获取小区 {community_id} 的本月支出统计")
    print(f"返回数据：{output}")
    return output


def get_monthly_expense(charge_system_name=None, community_name=None):
    """
    通过名称查询小区本月支出统计（智能模式）

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
        get_community_monthly_expense(str(comm_id), comm_name)
    else:
        # 多个匹配，列出供用户选择
        print(f"找到多个匹配的小区，请使用完整的小区名称重新查询：")
        for name in community_map.keys():
            print(f"  - {name}")


def get_current_month_year_range():
    """
    获取当前月的年和月（YYYY-MM格式）

    Returns:
        (year_month_str) 日期字符串
    """
    now = datetime.now()
    return now.strftime("%Y-%m")


def get_ledger_list_v2(community_id: str, cs_id: str, year_month: str, charge_item_id: str = None) -> dict:
    """
    获取小区指定月份的台账信息

    Args:
        community_id: 小区ID
        cs_id: 收费系统ID
        year_month: 年月 (YYYY-MM格式)
        charge_item_id: 收费项目ID（可选，筛选指定收费类型）

    Returns:
        台账数据字典
    """
    import random
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None

    headers = get_headers_with_cookies(ck_dict, {"communityid": str(community_id)})

    payload = {
        "type": "1",
        "startTime": year_month,
        "endTime": year_month,
        "current": 1,
        "__r__": random.random(),
        "communityIdList": [int(community_id)],
        "version": 3,
        "opAssetType": 1,
        "csId": int(cs_id),
        "mergeChargeItem": False,
        "page": 1,
        "pageSize": 1000
    }

    # 如果指定了收费项目ID，添加筛选条件并调整参数
    if charge_item_id:
        payload["selectChargeItemList"] = [int(charge_item_id)]
        payload["type"] = "28"
        payload["opAssetType"] = 28

    try:
        response = requests.post(
            f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/getLedgerListV2",
            json=payload,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"接口调用失败，状态码: {response.status_code}, 响应内容: {response.text}")
            return None

        response.raise_for_status()
        data = response.json()

        if data.get('code') != 0:
            logger.error(f"获取台账信息失败: {data.get('msg')}")
            return None

        return data.get('data', {})

    except requests.exceptions.RequestException as e:
        logger.error(f"接口调用发生异常: {e}")
        return None


def format_collection_rate_stats(community_name: str, ledger_data: dict, year_month: str, fee_type_name: str = None) -> str:
    """
    格式化收缴率统计数据

    Args:
        community_name: 小区名称
        ledger_data: 台账数据
        year_month: 年月 (YYYY-MM格式)
        fee_type_name: 费用类型名称（可选）

    Returns:
        格式化后的统计文本
    """
    year_month_dt = datetime.strptime(year_month, "%Y-%m")
    month_str = year_month_dt.strftime("%Y年%m月")

    if fee_type_name:
        output = [f"### {community_name} {month_str} {fee_type_name} 收缴率统计\n"]
    else:
        output = [f"### {community_name} {month_str} 房屋收缴率统计\n"]

    # 从数据中提取统计信息
    total_property = ledger_data.get('totalProperty', 0)  # 总房屋数
    total_amount = ledger_data.get('totalAmount', 0) / 100.0  # 总金额（分转元）
    total_paid_amount = ledger_data.get('totalPaidAmount', 0) / 100.0  # 已缴金额
    total_no_paid_amount = ledger_data.get('totalNoPaidAmount', 0) / 100.0  # 未缴金额
    paid_rate = ledger_data.get('paidRate', '0.00%')  # 收缴率
    total_paid_clear_property = ledger_data.get('totalPaidClearProperty', 0)  # 已缴清房屋数

    # 解析 index 字段获取更多信息
    index_str = ledger_data.get('index', '{}')
    try:
        index_data = json.loads(index_str)
        not_paid_house_num = index_data.get('notPaidHouseNum', 0)
    except (json.JSONDecodeError, KeyError):
        not_paid_house_num = 0

    # 基础统计
    output.append(f"**统计时间**: {month_str}")
    output.append(f"**收缴率**: {paid_rate}")
    output.append("")
    output.append(f"**总房屋数**: {total_property} 户")
    output.append(f"**已缴清房屋数**: {total_paid_clear_property} 户")
    output.append(f"**未缴清房屋数**: {not_paid_house_num if not_paid_house_num else (total_property - total_paid_clear_property)} 户")
    output.append("")
    output.append(f"**总应收金额**: ¥{total_amount:,.2f}")
    output.append(f"**已缴金额**: ¥{total_paid_amount:,.2f}")
    output.append(f"**未缴金额**: ¥{total_no_paid_amount:,.2f}")

    return "\n".join(output)


def get_community_collection_rate(community_id: str, cs_id: str, community_name: str = None, charge_item_id: str = None, fee_type_name: str = None) -> str:
    """
    获取小区本月收缴率统计

    Args:
        community_id: 小区ID
        cs_id: 收费系统ID
        community_name: 小区名称（可选）
        charge_item_id: 收费项目ID（可选，筛选指定收费类型）
        fee_type_name: 费用类型名称（可选，用于输出显示）

    Returns:
        统计结果文本
    """
    year_month = get_current_month_year_range()
    ledger_data = get_ledger_list_v2(community_id, cs_id, year_month, charge_item_id)

    if ledger_data is None:
        return "获取台账信息失败"

    if not community_name:
        community_name = "该小区"

    output = format_collection_rate_stats(community_name, ledger_data, year_month, fee_type_name)
    logger.info(f"成功获取小区 {community_id} 的本月收缴率统计")
    print(f"返回数据：{output}")
    return output


def get_collection_rate(charge_system_name=None, community_name=None, fee_type=None):
    """
    通过名称查询小区本月收缴率统计（智能模式）

    Args:
        charge_system_name: 收费系统名称
        community_name: 小区名称
        fee_type: 费用类型名称（可选，如"物业管理费"）
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

        # 如果指定了费用类型，获取收费项目ID
        charge_item_id = None
        if fee_type:
            charge_item_id = get_charge_item_id_by_name(str(comm_id), str(charge_system_id), fee_type)
            if not charge_item_id:
                print(f"警告：未找到匹配的收费项目 '{fee_type}'，将返回所有收费类型汇总数据")

        get_community_collection_rate(str(comm_id), str(charge_system_id), comm_name, charge_item_id, fee_type)
    else:
        # 多个匹配，列出供用户选择
        print(f"找到多个匹配的小区，请使用完整的小区名称重新查询：")
        for name in community_map.keys():
            print(f"  - {name}")


def get_community_house_info(community_id: str) -> dict:
    """
    获取小区房屋信息

    Args:
        community_id: 小区ID

    Returns:
        房屋信息数据字典
    """
    import random
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None

    headers = get_headers_with_cookies(ck_dict, {"communityid": str(community_id)})

    # 使用较大的时间范围来获取所有数据
    payload = {
        "communityID": int(community_id),
        "startTimeStr": "2020-01-01",
        "endTimeStr": "2030-12-31",
        "pageSize": 1000,  # 获取足够多的记录
        "page": 1,
        "r": random.random()
    }

    try:
        response = requests.post(
            f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/getCommunityHouseInfo",
            json=payload,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"接口调用失败，状态码: {response.status_code}, 响应内容: {response.text}")
            return None

        response.raise_for_status()
        data = response.json()

        if data.get('code') != 0:
            logger.error(f"获取房屋信息失败: {data.get('msg')}")
            return None

        return data.get('data', {})

    except requests.exceptions.RequestException as e:
        logger.error(f"接口调用发生异常: {e}")
        return None


def format_arrear_household_stats(community_name: str, house_info_data: dict) -> str:
    """
    格式化欠费户数统计数据

    Args:
        community_name: 小区名称
        house_info_data: 房屋信息数据

    Returns:
        格式化后的统计文本
    """
    output = [f"### {community_name} 欠费户数统计\n"]

    # 从数据中提取统计信息
    total_households = house_info_data.get('houseTotal', 0)  # 总房屋数
    arrear_households = house_info_data.get('arrearHouseTotal', 0)  # 欠费房屋数

    # 计算欠费比例
    arrear_rate = 0.0
    if total_households > 0:
        arrear_rate = (arrear_households / total_households) * 100

    # 基础统计
    output.append(f"**总房屋数**: {total_households} 户")
    output.append(f"**欠费户数**: {arrear_households} 户")
    output.append(f"**欠费比例**: {arrear_rate:.2f}%")

    # 按单元统计欠费户数
    unit_list = house_info_data.get('unitList', [])
    if unit_list:
        output.append("")
        output.append("**各单元欠费情况**:")
        for unit in unit_list:
            unit_name = unit.get('unitName', '未知单元')
            unit_total = unit.get('totalHouseCount', 0)
            unit_arrear = unit.get('arrearageHouseCount', 0)
            output.append(f"  - {unit_name}: {unit_arrear}/{unit_total} 户欠费")

    return "\n".join(output)


def get_community_arrear_households(community_id: str, community_name: str = None) -> str:
    """
    获取小区欠费户数统计

    Args:
        community_id: 小区ID
        community_name: 小区名称（可选）

    Returns:
        统计结果文本
    """
    house_info_data = get_community_house_info(community_id)

    if house_info_data is None:
        return "获取房屋信息失败"

    if not community_name:
        community_name = "该小区"

    output = format_arrear_household_stats(community_name, house_info_data)
    logger.info(f"成功获取小区 {community_id} 的欠费户数统计")
    print(f"返回数据：{output}")
    return output


def get_arrear_households(charge_system_name=None, community_name=None):
    """
    通过名称查询小区欠费户数统计（智能模式）

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
        get_community_arrear_households(str(comm_id), comm_name)
    else:
        # 多个匹配，列出供用户选择
        print(f"找到多个匹配的小区，请使用完整的小区名称重新查询：")
        for name in community_map.keys():
            print(f"  - {name}")


def search_household_structure(community_id: str, keyword: str) -> dict:
    """
    调用 getCommunityInfo 接口，模糊搜索楼宇/单元/房屋

    Args:
        community_id: 小区ID
        keyword: 搜索关键词

    Returns:
        嵌套的楼宇/单元/房屋结构数据
    """
    import random
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None

    headers = get_headers_with_cookies(ck_dict, {"communityid": str(community_id)})

    params = {
        "communityID": community_id,
        "kw": keyword,
        "needHouse": 1,
        "r": random.random()
    }

    try:
        response = requests.get(
            f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/getCommunityInfo",
            params=params,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"接口调用失败，状态码: {response.status_code}, 响应内容: {response.text}")
            return None

        data = response.json()

        if data.get('code') != 0:
            logger.error(f"获取房屋结构失败: {data.get('msg')}")
            return None

        return data.get('data', {})

    except requests.exceptions.RequestException as e:
        logger.error(f"接口调用发生异常: {e}")
        return None


def convert_chinese_numbers(text: str) -> str:
    """
    将中文数字转换为阿拉伯数字

    Args:
        text: 包含中文数字的文本，如"一栋一单元103"

    Returns:
        转换后的文本，如"1栋1单元103"
    """
    if not text:
        return text

    # 中文数字到阿拉伯数字的映射
    chinese_to_arabic = {
        '零': '0', '〇': '0',
        '一': '1', '二': '2', '三': '3', '四': '4',
        '五': '5', '六': '6', '七': '7', '八': '8', '九': '9',
        '壹': '1', '贰': '2', '叁': '3', '肆': '4',
        '伍': '5', '陆': '6', '柒': '7', '捌': '8', '玖': '9'
    }

    # 处理"十"的特殊情况
    # 十 -> 10, 十一 -> 11, 二十 -> 20, 二十一 -> 21
    result = []
    i = 0
    n = len(text)

    while i < n:
        char = text[i]

        # 处理"十"
        if char == '十':
            # 检查前面是否有数字
            has_prefix = i > 0 and text[i-1] in chinese_to_arabic
            # 检查后面是否有数字
            has_suffix = i + 1 < n and text[i+1] in chinese_to_arabic

            if not has_prefix and not has_suffix:
                # 单独的"十" -> "10"
                result.append('10')
            elif has_prefix and not has_suffix:
                # "二十" -> "20"
                result.append('0')
            elif not has_prefix and has_suffix:
                # "十一" -> "1"
                result.append('1')
            # else: "二十一" -> 前面已经处理了"二"，这里处理"十"后面的"一"，所以"十"直接忽略
            i += 1
        elif char in chinese_to_arabic:
            # 普通中文数字
            result.append(chinese_to_arabic[char])
            i += 1
        else:
            # 非数字字符直接添加
            result.append(char)
            i += 1

    return ''.join(result)


def split_keywords(keyword: str) -> list:
    """
    将用户输入拆分成多个关键词

    Args:
        keyword: 用户输入的关键词，如"2栋202"

    Returns:
        关键词列表，如["2栋", "202"]
    """
    import re
    # 移除空格
    keyword = keyword.strip()
    if not keyword:
        return []

    # 尝试按常见分隔符拆分
    separators = ['/', '\\', '-', ' ', '、', '，', ',']
    for sep in separators:
        if sep in keyword:
            parts = [p.strip() for p in keyword.split(sep) if p.strip()]
            if parts:
                return parts

    # 对于没有分隔符的情况，尝试智能拆分
    # 例如"2栋202" -> ["2栋", "202"]
    parts = []
    i = 0
    n = len(keyword)

    while i < n:
        # 查找数字
        if keyword[i].isdigit():
            j = i
            while j < n and keyword[j].isdigit():
                j += 1
            # 数字后面可能跟着单位词（栋、单元、室等）
            while j < n and '\u4e00' <= keyword[j] <= '\u9fff':
                j += 1
            parts.append(keyword[i:j])
            i = j
        # 查找中文字符
        elif '\u4e00' <= keyword[i] <= '\u9fff':
            j = i
            while j < n and '\u4e00' <= keyword[j] <= '\u9fff':
                j += 1
            parts.append(keyword[i:j])
            i = j
        else:
            i += 1

    # 如果拆分失败，返回原关键词
    return parts if parts else [keyword]


def find_matching_nodes(community_data: dict, keyword: str, exact_match: bool = False, relaxed_match: bool = False) -> list:
    """
    从嵌套结构中找出所有匹配的节点，并按层级关系筛选

    Args:
        community_data: getCommunityInfo 返回的数据
        keyword: 用户输入的关键词
        exact_match: 是否使用精确匹配模式（完全匹配 full_name）
        relaxed_match: 是否使用宽松匹配模式（支持中文数字转换、部分关键词匹配）

    Returns:
        筛选后的节点列表，每个节点包含 id, name, level, path
        level: 'building' | 'unit' | 'house'
        path: 节点的完整路径，用于判断层级关系
    """
    if not community_data:
        return []

    building_list = community_data.get('buildingList', [])
    if not building_list:
        return []

    # 精确匹配模式
    if exact_match:
        target_name = keyword.strip()
        logger.info(f"使用精确匹配模式，目标: {target_name}")
        all_nodes = []
        for building in building_list:
            building_name = building.get('name', '')
            building_id = building.get('id')
            building_path = [building_id]
            full_building_name = building_name

            if full_building_name == target_name:
                all_nodes.append({
                    'id': building_id,
                    'name': building_name,
                    'full_name': full_building_name,
                    'level': 'building',
                    'id_type': 2,
                    'path': building_path.copy()
                })

            unit_list = building.get('unitList', [])
            for unit in unit_list:
                unit_name = unit.get('name', '')
                unit_id = unit.get('id')
                unit_path = building_path + [unit_id]
                full_unit_name = f"{building_name}/{unit_name}"

                if full_unit_name == target_name:
                    all_nodes.append({
                        'id': unit_id,
                        'name': f"{building_name}/{unit_name}",
                        'full_name': full_unit_name,
                        'level': 'unit',
                        'id_type': 3,
                        'path': unit_path.copy()
                    })

                house_list = unit.get('houseList', [])
                for house in house_list:
                    house_name = house.get('name', '')
                    house_id = house.get('id')
                    house_path = unit_path + [house_id]
                    full_house_name = f"{building_name}/{unit_name}/{house_name}"

                    if full_house_name == target_name:
                        all_nodes.append({
                            'id': house_id,
                            'name': f"{building_name}/{unit_name}/{house_name}",
                            'full_name': full_house_name,
                            'level': 'house',
                            'id_type': 4,
                            'path': house_path.copy()
                        })

        if all_nodes:
            logger.info(f"精确匹配找到 {len(all_nodes)} 个节点")
        return all_nodes

    # 准备匹配用的关键词列表
    search_keywords_list = []

    # 原始关键词
    original_keywords = split_keywords(keyword)
    if original_keywords:
        search_keywords_list.append((original_keywords, False))  # (关键词列表, 是否需要部分匹配)

    # 如果是宽松模式，添加中文数字转换后的关键词
    if relaxed_match:
        converted_keyword = convert_chinese_numbers(keyword)
        if converted_keyword != keyword:
            converted_keywords = split_keywords(converted_keyword)
            if converted_keywords:
                search_keywords_list.append((converted_keywords, False))
                logger.info(f"添加中文数字转换后的关键词: {converted_keywords}")

        # 提取所有数字用于纯数字匹配
        import re
        digits_only = ''.join(re.findall(r'\d+', keyword + converted_keyword))
        if digits_only:
            search_keywords_list.append(([digits_only], True))
            logger.info(f"添加纯数字匹配关键词: {digits_only}")

        # 最后添加部分匹配模式
        search_keywords_list.append((original_keywords, True))

    all_nodes = []
    seen_node_ids = set()

    # 遍历所有搜索关键词组合
    for keywords, use_partial_match in search_keywords_list:
        if not keywords:
            continue

        # 所有关键词都转为小写用于匹配
        keywords_lower = [k.lower() for k in keywords]

        # 遍历所有节点，收集匹配的
        for building in building_list:
            building_name = building.get('name', '')
            building_id = building.get('id')
            building_path = [building_id]
            full_building_name = building_name

            # 检查楼宇是否匹配
            node_full_text = full_building_name.lower()
            if use_partial_match:
                # 部分匹配：至少有一个关键词出现
                node_matches = any(k in node_full_text for k in keywords_lower)
            else:
                # 完整匹配：所有关键词都要出现
                node_matches = all(k in node_full_text for k in keywords_lower)

            if node_matches and building_id not in seen_node_ids:
                seen_node_ids.add(building_id)
                all_nodes.append({
                    'id': building_id,
                    'name': building_name,
                    'full_name': full_building_name,
                    'level': 'building',
                    'id_type': 2,
                    'path': building_path.copy()
                })

            unit_list = building.get('unitList', [])
            for unit in unit_list:
                unit_name = unit.get('name', '')
                unit_id = unit.get('id')
                unit_path = building_path + [unit_id]
                full_unit_name = f"{building_name}/{unit_name}"

                # 检查单元是否匹配
                node_full_text = full_unit_name.lower()
                if use_partial_match:
                    node_matches = any(k in node_full_text for k in keywords_lower)
                else:
                    node_matches = all(k in node_full_text for k in keywords_lower)

                if node_matches and unit_id not in seen_node_ids:
                    seen_node_ids.add(unit_id)
                    all_nodes.append({
                        'id': unit_id,
                        'name': f"{building_name}/{unit_name}",
                        'full_name': full_unit_name,
                        'level': 'unit',
                        'id_type': 3,
                        'path': unit_path.copy()
                    })

                house_list = unit.get('houseList', [])
                for house in house_list:
                    house_name = house.get('name', '')
                    house_id = house.get('id')
                    house_path = unit_path + [house_id]
                    full_house_name = f"{building_name}/{unit_name}/{house_name}"

                    # 检查房屋是否匹配
                    node_full_text = full_house_name.lower()
                    if use_partial_match:
                        node_matches = any(k in node_full_text for k in keywords_lower)
                    else:
                        node_matches = all(k in node_full_text for k in keywords_lower)

                    if node_matches and house_id not in seen_node_ids:
                        seen_node_ids.add(house_id)
                        all_nodes.append({
                            'id': house_id,
                            'name': f"{building_name}/{unit_name}/{house_name}",
                            'full_name': full_house_name,
                            'level': 'house',
                            'id_type': 4,
                            'path': house_path.copy()
                        })

        # 如果已经找到匹配节点，且不是部分匹配模式，就不需要继续尝试更宽松的匹配了
        if all_nodes and not use_partial_match:
            break

    if not all_nodes:
        return []

    # 筛选最高层级的节点：如果一个节点的祖先也在匹配列表中，则只保留祖先
    # 构建 id 到节点的映射
    id_to_node = {node['id']: node for node in all_nodes}
    selected_nodes = []

    for node in all_nodes:
        # 检查该节点的祖先是否也在匹配列表中
        has_ancestor_in_list = False
        # path 包含从根到该节点的所有 id，最后一个是自己，所以检查前面的
        for ancestor_id in node['path'][:-1]:
            if ancestor_id in id_to_node:
                has_ancestor_in_list = True
                break
        if not has_ancestor_in_list:
            selected_nodes.append(node)

    return selected_nodes


def generate_candidates(community_data: dict, keyword: str, max_candidates: int = 20) -> list:
    """
    从完整小区结构中提取相关的候选房屋

    Args:
        community_data: getCommunityInfo 返回的完整数据
        keyword: 用户原始查询关键词
        max_candidates: 最大返回候选数量

    Returns:
        候选房屋列表，按楼栋、单元排序
    """
    if not community_data:
        return []

    building_list = community_data.get('buildingList', [])
    if not building_list:
        return []

    # 尝试从关键词中提取楼栋信息
    keyword_lower = keyword.lower()
    converted_keyword = convert_chinese_numbers(keyword).lower()

    candidates = []
    target_building_names = set()

    # 首先尝试找出用户可能想找的楼栋
    for building in building_list:
        building_name = building.get('name', '').lower()
        if building_name in keyword_lower or building_name in converted_keyword:
            target_building_names.add(building.get('name', ''))

    # 如果找到了目标楼栋，只收集该楼栋下的房屋
    if target_building_names:
        for building in building_list:
            building_name = building.get('name', '')
            if building_name not in target_building_names:
                continue

            unit_list = building.get('unitList', [])
            for unit in unit_list:
                unit_name = unit.get('name', '')
                house_list = unit.get('houseList', [])
                for house in house_list:
                    house_name = house.get('name', '')
                    full_path = f"{building_name}/{unit_name}/{house_name}"
                    candidates.append(full_path)
                    if len(candidates) >= max_candidates:
                        return candidates
    else:
        # 如果没有找到明确的楼栋，收集一些示例房屋
        for building in building_list:
            building_name = building.get('name', '')
            unit_list = building.get('unitList', [])
            for unit in unit_list:
                unit_name = unit.get('name', '')
                house_list = unit.get('houseList', [])
                for house in house_list:
                    house_name = house.get('name', '')
                    full_path = f"{building_name}/{unit_name}/{house_name}"
                    candidates.append(full_path)
                    if len(candidates) >= max_candidates:
                        return candidates

    return candidates


def print_candidates(keyword: str, candidates: list):
    """
    打印候选列表格式输出

    Args:
        keyword: 用户原始查询关键词
        candidates: 候选房屋列表
    """
    print("CANDIDATES:")
    print(f"用户查询: {keyword}")
    print("候选列表:")
    for idx, candidate in enumerate(candidates, 1):
        print(f"{idx}. {candidate}")
    print("提示: 未找到精确匹配，请从以上候选中选择，或使用完整路径如\"1栋/1单元/103\"")


def format_household_arrears_result(raw_response, node_name: str, community_name: str = None) -> str:
    """
    格式化房屋欠费查询结果

    Args:
        raw_response: API 返回的原始数据
        node_name: 查询的节点名称
        community_name: 小区名称（可选）

    Returns:
        格式化后的欠费信息文本
    """
    if isinstance(raw_response, str):
        res = json.loads(raw_response)
    else:
        res = raw_response

    if res.get('code') != 0:
        return f"获取失败：{res.get('msg')}"

    data = res.get('data', {})
    total_arrears = data.get('totalArrearsAmount', 0)
    total_arrears_yuan = total_arrears / 100.0

    output = ["### 房屋欠费统计\n"]
    if community_name:
        output.append(f"**小区名称**: {community_name}")
    output.append(f"**查询对象**: {node_name}")
    output.append(f"**欠费总额**: ¥{total_arrears_yuan:,.2f}")

    return "\n".join(output)


def format_household_specific_arrears_result(raw_response, node_name: str, community_name: str = None, start_time: int = None, end_time: int = None, fee_type_name: str = None) -> str:
    """
    格式化特定房屋特定条件欠费查询结果（支持时间范围和费用类型过滤）

    Args:
        raw_response: API 返回的原始数据
        node_name: 查询的节点名称
        community_name: 小区名称（可选）
        start_time: 开始时间戳（秒），可选
        end_time: 结束时间戳（秒），可选
        fee_type_name: 费用类型名称（如"物业费"、"水费"），可选

    Returns:
        格式化后的欠费信息文本
    """
    if isinstance(raw_response, str):
        res = json.loads(raw_response)
    else:
        res = raw_response

    if res.get('code') != 0:
        return f"获取失败：{res.get('msg')}"

    data = res.get('data', {})
    total_arrears = data.get('totalArrearsAmount', 0)
    total_arrears_yuan = total_arrears / 100.0

    output = ["### 房屋欠费统计\n"]
    if community_name:
        output.append(f"**小区名称**: {community_name}")
    output.append(f"**查询对象**: {node_name}")

    if start_time is not None and end_time is not None:
        start_dt = datetime.fromtimestamp(start_time)
        end_dt = datetime.fromtimestamp(end_time)
        output.append(f"**时间范围**: {start_dt.strftime('%Y-%m-%d')} 至 {end_dt.strftime('%Y-%m-%d')}")

    if fee_type_name:
        output.append(f"**费用类型**: {fee_type_name}")

    output.append(f"**欠费金额**: ¥{total_arrears_yuan:,.2f}")

    if not fee_type_name:
        output.append("\n*注：未指定费用类型，显示所有费用类型总欠费*")
    elif not total_arrears_yuan:
        output.append("\n*注：该条件下查询结果为0欠费*")

    return "\n".join(output)


def get_household_arrears(community_id: str, object_id: str, id_type: int, node_name: str, community_name: str = None) -> str:
    """
    查询指定对象的欠费总额

    Args:
        community_id: 小区ID
        object_id: 楼宇/单元/房屋ID
        id_type: 2=楼宇, 3=单元, 4=房屋
        node_name: 节点名称，用于展示
        community_name: 小区名称（可选）

    Returns:
        格式化的欠费信息
    """
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return

    headers = get_headers_with_cookies(ck_dict, {"communityid": str(community_id)})

    params = {
        "id": object_id,
        "idType": id_type,
        "assetType": 1,
        "page": 1,
        "pageSize": 20
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

        output = format_household_arrears_result(data, node_name, community_name)
        logger.info(f"成功获取 {community_id} 中 {node_name} 的欠费信息")
        print(f"返回数据：{output}")
        return output

    except requests.exceptions.RequestException as e:
        logger.error(f"接口调用发生异常: {e}")
        return f"接口调用发生异常: {str(e)}"


def get_household_arrears_by_name(charge_system_name=None, community_name=None, keyword=None):
    """
    通过名称查询房屋相关欠费（智能模式）

    Args:
        charge_system_name: 收费系统名称
        community_name: 小区名称
        keyword: 搜索关键词（楼栋/单元/房屋）
    """
    # 检查必要参数
    if not charge_system_name:
        print("NEED_INFO: 请提供收费系统名称")
        print("提示：可以先使用 list_charge_systems 命令查看可用的收费系统")
        return

    if not community_name:
        print("NEED_INFO: 请提供小区名称")
        return

    if not keyword:
        print("NEED_INFO: 请提供搜索关键词（楼栋/单元/房屋名称）")
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

    if len(community_map) > 1:
        # 多个匹配，列出供用户选择
        print(f"找到多个匹配的小区，请使用完整的小区名称重新查询：")
        for name in community_map.keys():
            print(f"  - {name}")
        return

    # 只有一个匹配，继续处理
    comm_name, comm_id = next(iter(community_map.items()))
    print(f"找到小区：{comm_name}")

    # 先尝试从缓存加载上一次的匹配列表
    cache_data = load_match_cache()
    if cache_data and str(cache_data.get('community_id')) == str(comm_id):
        cached_nodes = cache_data.get('nodes', [])
        if cached_nodes:
            # 尝试解析用户选择
            selected_node = parse_user_selection(keyword, cached_nodes)
            if selected_node:
                logger.info(f"用户选择了: {selected_node.get('name')}")
                # 清除缓存，使用选中的节点查询欠费
                clear_match_cache()
                print(f"✓ 已选择：{selected_node['name']}")
                get_household_arrears(str(comm_id), selected_node['id'], selected_node['id_type'], selected_node['name'], comm_name)
                return
            else:
                # 解析失败，清除缓存，按新关键词重新搜索
                logger.info("无法解析用户选择，清除缓存并重新搜索")
                clear_match_cache()

    # 清理关键词：去除"查询"、"的欠费"等词
    clean_keyword = keyword.replace("查询", "").replace("的欠费", "").replace("欠费", "").strip()

    # 检查是否使用精确匹配（包含 "/"）
    use_exact_match = "/" in clean_keyword

    # 获取完整房屋结构用于本地匹配（搜索空字符串获取完整结构）
    household_data = search_household_structure(str(comm_id), "")

    if household_data is None:
        print("搜索房屋结构失败")
        return

    # 找出匹配的节点
    is_exact_match = False
    is_relaxed_match = False
    if use_exact_match:
        # 先尝试精确匹配
        matching_nodes = find_matching_nodes(household_data, clean_keyword, exact_match=True)
        if matching_nodes:
            is_exact_match = True
        if not matching_nodes:
            # 精确匹配失败，降级到模糊匹配
            logger.info("精确匹配未找到结果，使用模糊匹配")
            # 拆分关键词，用最后一个关键词搜索（可能被 "/" 分割）
            keywords = clean_keyword.split("/")
            search_kw = keywords[-1] if keywords else clean_keyword
            # 重新获取针对该关键词的搜索结果（可能更准确）
            household_data_for_search = search_household_structure(str(comm_id), search_kw)
            if household_data_for_search:
                household_data = household_data_for_search
            matching_nodes = find_matching_nodes(household_data, clean_keyword)
    else:
        # 模糊匹配模式：先用关键词搜索获取更相关的结果
        keywords = split_keywords(clean_keyword)
        search_kw = keywords[-1] if keywords else clean_keyword
        household_data_for_search = search_household_structure(str(comm_id), search_kw)
        if household_data_for_search:
            household_data = household_data_for_search
        matching_nodes = find_matching_nodes(household_data, clean_keyword)

    if not matching_nodes:
        # 尝试宽松匹配
        logger.info(f"严格匹配未找到，尝试宽松匹配: {clean_keyword}")
        matching_nodes = find_matching_nodes(household_data, clean_keyword, relaxed_match=True)
        if matching_nodes:
            is_relaxed_match = True

    if not matching_nodes:
        # 仍然没找到，生成候选列表
        logger.info(f"宽松匹配也未找到，生成候选列表")
        candidates = generate_candidates(household_data, clean_keyword)
        if candidates:
            print_candidates(clean_keyword, candidates)
        else:
            print(f"未找到与'{clean_keyword}'匹配的楼栋/单元/房屋，请确认输入是否正确")
        return

    if len(matching_nodes) == 1:
        # 只有一个匹配，输出匹配信息后查询欠费
        node = matching_nodes[0]
        if is_exact_match:
            print(f"✓  找到：{node['name']}")
        elif is_relaxed_match:
            print(f"🤖 找到：{node['name']}")
        else:
            print(f"🔍 找到：{node['name']}")
        get_household_arrears(str(comm_id), node['id'], node['id_type'], node['name'], comm_name)
    else:
        # 多个匹配，保存到缓存并列出供用户选择
        save_match_cache(comm_id, matching_nodes)
        print("MULTI_MATCH:")
        for idx, node in enumerate(matching_nodes, 1):
            level_label = {
                'building': '楼栋',
                'unit': '单元',
                'house': '房屋'
            }.get(node['level'], '未知')
            print(f"{idx}. {node['name']} ({level_label})")


def get_household_specific_arrears(community_id: str, object_id: str, id_type: int, node_name: str, community_name: str = None, start_time: int = None, end_time: int = None, charge_item_id: str = None, fee_type_name: str = None) -> str:
    """
    查询指定对象特定条件的欠费（支持时间范围和费用类型过滤）

    Args:
        community_id: 小区ID
        object_id: 楼宇/单元/房屋ID
        id_type: 2=楼宇, 3=单元, 4=房屋
        node_name: 节点名称，用于展示
        community_name: 小区名称（可选）
        start_time: 开始时间戳（秒），可选
        end_time: 结束时间戳（秒），可选
        charge_item_id: 收费项目ID，用于过滤特定费用类型，可选
        fee_type_name: 费用类型名称，用于显示，可选

    Returns:
        格式化的欠费信息
    """
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return

    headers = get_headers_with_cookies(ck_dict, {"communityid": str(community_id)})

    params = {
        "id": object_id,
        "idType": id_type,
        "assetType": 1,
        "page": 1,
        "pageSize": 20
    }

    # 添加可选过滤参数
    if start_time is not None:
        params["startTime"] = start_time
    if end_time is not None:
        params["endTime"] = end_time
    if charge_item_id is not None:
        params["selectChargeItemList"] = [int(charge_item_id)]

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

        output = format_household_specific_arrears_result(data, node_name, community_name, start_time, end_time, fee_type_name)
        logger.info(f"成功获取 {community_id} 中 {node_name} 的特定条件欠费信息")
        print(output)
        return output

    except requests.exceptions.RequestException as e:
        logger.error(f"接口调用发生异常: {e}")
        return f"接口调用发生异常: {str(e)}"


def get_household_specific_arrears_by_name(charge_system_name=None, community_name=None, keyword=None, start_date_str=None, end_date_str=None, fee_type=None):
    """
    通过名称查询特定房屋特定条件的欠费（智能模式，支持时间范围和费用类型过滤）

    Args:
        charge_system_name: 收费系统名称
        community_name: 小区名称
        keyword: 搜索关键词（楼栋/单元/房屋）
        start_date_str: 开始日期，格式 YYYY-MM-DD，可选
        end_date_str: 结束日期，格式 YYYY-MM-DD，可选
        fee_type: 费用类型（物业费、水费、电费、燃气费），可选
    """
    # 检查必要参数
    if not charge_system_name:
        print("NEED_INFO: 请提供收费系统名称")
        print("提示：可以先使用 list_charge_systems 命令查看可用的收费系统")
        return

    if not community_name:
        print("NEED_INFO: 请提供小区名称")
        return

    if not keyword:
        print("NEED_INFO: 请提供搜索关键词（楼栋/单元/房屋名称）")
        return

    # 解析日期（如果提供）
    start_time = None
    end_time = None
    if start_date_str and end_date_str:
        start_dt = parse_iso_date(start_date_str)
        if not start_dt:
            print(f"错误：无法解析开始日期 '{start_date_str}'，请使用 YYYY-MM-DD 格式")
            return
        end_dt = parse_iso_date(end_date_str)
        if not end_dt:
            print(f"错误：无法解析结束日期 '{end_date_str}'，请使用 YYYY-MM-DD 格式")
            return

        # 开始时间设置为当天 00:00:00
        start_dt = start_dt.replace(hour=0, minute=0, second=0)
        # 结束时间设置为当天 23:59:59
        end_dt = end_dt.replace(hour=23, minute=59, second=59)
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

    if len(community_map) > 1:
        # 多个匹配，列出供用户选择
        print(f"找到多个匹配的小区，请使用完整的小区名称重新查询：")
        for name in community_map.keys():
            print(f"  - {name}")
        return

    # 只有一个匹配，继续处理
    comm_name, comm_id = next(iter(community_map.items()))
    print(f"找到小区：{comm_name}")

    # 获取收费项目ID（如果指定了费用类型）
    charge_item_id = None
    if fee_type:
        charge_item_id = get_charge_item_id_by_name(str(comm_id), charge_system_id, fee_type)

    # 先尝试从缓存加载上一次的匹配列表
    cache_data = load_match_cache()
    if cache_data and str(cache_data.get('community_id')) == str(comm_id):
        cached_nodes = cache_data.get('nodes', [])
        if cached_nodes:
            # 尝试解析用户选择
            selected_node = parse_user_selection(keyword, cached_nodes)
            if selected_node:
                logger.info(f"用户选择了: {selected_node.get('name')}")
                # 清除缓存，使用选中的节点查询欠费
                clear_match_cache()
                print(f"✓ 已选择：{selected_node['name']}")
                get_household_specific_arrears(str(comm_id), selected_node['id'], selected_node['id_type'], selected_node['name'], comm_name, start_time, end_time, charge_item_id, fee_type)
                return
            else:
                # 解析失败，清除缓存，按新关键词重新搜索
                logger.info("无法解析用户选择，清除缓存并重新搜索")
                clear_match_cache()

    # 清理关键词：去除无关词汇
    clean_keyword = keyword
    for word in ["查询", "的欠费", "欠费", "的", "金额", "多少", "是多少"]:
        clean_keyword = clean_keyword.replace(word, "").strip()

    # 检查是否使用精确匹配（包含 "/"）
    use_exact_match = "/" in clean_keyword

    # 获取完整房屋结构用于本地匹配
    household_data = search_household_structure(str(comm_id), "")

    if household_data is None:
        print("搜索房屋结构失败")
        return

    # 找出匹配的节点
    is_exact_match = False
    is_relaxed_match = False
    if use_exact_match:
        # 先尝试精确匹配
        matching_nodes = find_matching_nodes(household_data, clean_keyword, exact_match=True)
        if matching_nodes:
            is_exact_match = True
        if not matching_nodes:
            # 精确匹配失败，降级到模糊匹配
            logger.info("精确匹配未找到结果，使用模糊匹配")
            keywords = clean_keyword.split("/")
            search_kw = keywords[-1] if keywords else clean_keyword
            household_data_for_search = search_household_structure(str(comm_id), search_kw)
            if household_data_for_search:
                household_data = household_data_for_search
            matching_nodes = find_matching_nodes(household_data, clean_keyword)
    else:
        # 模糊匹配模式
        keywords = split_keywords(clean_keyword)
        search_kw = keywords[-1] if keywords else clean_keyword
        household_data_for_search = search_household_structure(str(comm_id), search_kw)
        if household_data_for_search:
            household_data = household_data_for_search
        matching_nodes = find_matching_nodes(household_data, clean_keyword)

    if not matching_nodes:
        # 尝试宽松匹配
        logger.info(f"严格匹配未找到，尝试宽松匹配: {clean_keyword}")
        matching_nodes = find_matching_nodes(household_data, clean_keyword, relaxed_match=True)
        if matching_nodes:
            is_relaxed_match = True

    if not matching_nodes:
        # 仍然没找到，生成候选列表
        logger.info(f"宽松匹配也未找到，生成候选列表")
        candidates = generate_candidates(household_data, clean_keyword)
        if candidates:
            print_candidates(clean_keyword, candidates)
        else:
            print(f"未找到与'{clean_keyword}'匹配的楼栋/单元/房屋，请确认输入是否正确")
        return

    if len(matching_nodes) == 1:
        # 只有一个匹配，输出匹配信息后查询欠费
        node = matching_nodes[0]
        if is_exact_match:
            print(f"✓ 找到：{node['name']}")
        elif is_relaxed_match:
            print(f"🤖 找到：{node['name']}")
        else:
            print(f"🔍 找到：{node['name']}")

        # 重新格式化输出，此时传入正确的 fee_type 名称用于显示
        result = get_household_specific_arrears(str(comm_id), node['id'], node['id_type'], node['name'], comm_name, start_time, end_time, charge_item_id, fee_type)
        if result:
            # 由于get_household_specific_arrears已经打印了结果，这里只需要重新格式化添加fee_type名称
            if fee_type and '### 房屋欠费统计' in result:
                # 我们需要重新输出一次，因为第一次格式化的时候 fee_type_name 是 None
                # 重新读取数据重新格式化
                import re
                match = re.search(r'"code":\s*\d+.*', result)
                if match:
                    pass  # 如果已经格式化了，就直接用原来的输出，只添加fee_type信息
                # 直接重新输出一次完整格式（用户看到两次也没关系，主要是信息正确）
                data = json.loads(result) if isinstance(result, str) and result.startswith('{') else None
                if data:
                    output = format_household_specific_arrears_result(data, node['name'], comm_name, start_time, end_time, fee_type)
                    print("\n" + output)
        return
    else:
        # 多个匹配，保存到缓存并列出供用户选择
        save_match_cache(comm_id, matching_nodes)
        print("MULTI_MATCH:")
        for idx, node in enumerate(matching_nodes, 1):
            level_label = {
                'building': '楼栋',
                'unit': '单元',
                'house': '房屋'
            }.get(node['level'], '未知')
            print(f"{idx}. {node['name']} ({level_label})")


def format_cs_init_info(raw_response) -> str:
    """
    格式化初始化信息数据

    Args:
        raw_response: API 返回的原始数据

    Returns:
        格式化后的统计文本
    """
    if isinstance(raw_response, str):
        res = json.loads(raw_response)
    else:
        res = raw_response

    if res.get('code') != 0:
        return f"获取失败：{res.get('msg')}"

    data = res.get('data', {})
    community_info = data.get('communityInfo', {})

    cs_info = data.get('csInfo', {})
    user_info_data = data.get('userInfo', {}).get('data', {})

    output = ["### 当前登录用户信息\n"]

    # 用户信息
    output.append("**用户信息**:")
    if user_info_data:

        output.append(f"- 昵称: {user_info_data.get('nick', '')}")
        output.append(f"- 真实姓名: {user_info_data.get('real_nick', '')}")
        output.append(f"- 手机号: {user_info_data.get('phone', '')}")
        output.append(f"- UID: {user_info_data.get('uid', '')}")
    output.append("")

    # 小区信息
    output.append("**小区信息**:")
    if community_info:
        output.append(f"- 小区名称: {community_info.get('name', '')}")
        output.append(f"- 小区ID: {community_info.get('id', '')}")
        output.append(f"- 地址: {community_info.get('address', '')}")
        output.append(f"- 省份: {community_info.get('province', '')}")
        output.append(f"- 城市: {community_info.get('city', '')}")
    output.append("")

    # 收费系统信息
    output.append("**收费系统信息**:")
    if cs_info:
        output.append(f"- 系统名称: {cs_info.get('name', '')}")
        output.append(f"- 系统ID: {cs_info.get('id', '')}")
        output.append(f"- 创建者: {cs_info.get('createUserName', '')}")
        output.append(f"- 绑定团队: {cs_info.get('bindItemName', '')}")
        output.append(f"- 是否收费系统管理员: {'是' if cs_info.get('isCsAdmin') else '否'}")

    return "\n".join(output)


def get_community_cs_init_info(community_id: str, cs_id: str, community_name: str = None) -> str:
    """
    获取小区初始化信息（包含当前登录用户信息）

    Args:
        community_id: 小区ID
        cs_id: 收费系统ID
        community_name: 小区名称（可选）

    Returns:
        统计结果文本
    """
    import random
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None

    headers = get_headers_with_cookies(ck_dict, {"communityid": str(community_id)})

    params = {
        "communityID": int(community_id),
        "csID": int(cs_id),
        "r": random.random()
    }

    try:
        response = requests.get(
            f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/getCsInitInfo",
            params=params,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"接口调用失败，状态码: {response.status_code}, 响应内容: {response.text}")
            return "请求异常，请稍后再试。"

        if not community_name:
            community_name = "该小区"

        output = format_cs_init_info(response.json())
        logger.info(f"成功获取小区 {community_id} 的初始化信息")
        return output

    except requests.exceptions.RequestException as e:
        logger.error(f"接口调用发生异常: {e}")
        return f"接口调用发生异常: {str(e)}"


def get_current_login_user_info():
    """
    直接从 session 获取当前登录用户信息（不需要团队/小区信息）

    Returns:
        用户信息文本
    """
    session = session_mgr.get_session()
    if not session:
        print("未检测到登录信息，请先登录马克智慧物业系统。")
        return None

    output = ["### 当前登录用户信息\n"]

    # 首先尝试通过 API 获取详细的用户信息（包含昵称、真实姓名等）
    try:
        # 获取收费系统列表
        system_map = get_user_charge_systems(return_map=True)
        if system_map:
            # 取第一个收费系统
            charge_system_name = next(iter(system_map.keys()))
            charge_system_id = system_map[charge_system_name]

            # 获取该收费系统下的小区列表
            community_map = search_community(str(charge_system_id), "", return_map=True)
            if community_map:
                # 取第一个小区
                comm_name, comm_id = next(iter(community_map.items()))

                # 调用 API 获取详细用户信息
                import random
                ck_dict = ensure_authenticated()
                if ck_dict:
                    headers = get_headers_with_cookies(ck_dict, {"communityid": str(comm_id)})
                    params = {
                        "communityID": int(comm_id),
                        "csID": int(charge_system_id),
                        "r": random.random()
                    }
                    response = requests.get(
                        f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/getCsInitInfo",
                        params=params,
                        headers=headers,
                        timeout=10
                    )
                    if response.status_code == 200:
                        res = response.json()
                        if res.get('code') == 0:
                            data = res.get('data', {})
                            user_info_data = data.get('userInfo', {}).get('data', {})

                            # 用户信息
                            output.append("**用户信息**:")
                            if user_info_data:
                                nick = user_info_data.get('nick', '')
                                real_nick = user_info_data.get('real_nick', '')
                                phone = user_info_data.get('phone', '')
                                uid = user_info_data.get('uid', '')

                                if nick:
                                    output.append(f"- 昵称: {nick}")
                                if real_nick:
                                    output.append(f"- 真实姓名: {real_nick}")
                                if phone:
                                    output.append(f"- 手机号: {phone}")
                                if uid:
                                    output.append(f"- UID: {uid}")
                            output.append("")

                            # 小区信息
                            community_info = data.get('communityInfo', {})
                            output.append("**小区信息**:")
                            if community_info:
                                output.append(f"- 小区名称: {community_info.get('name', '')}")
                                output.append(f"- 小区ID: {community_info.get('id', '')}")
                            output.append("")

                            # 收费系统信息
                            cs_info = data.get('csInfo', {})
                            output.append("**收费系统信息**:")
                            if cs_info:
                                output.append(f"- 系统名称: {cs_info.get('name', '')}")
                                output.append(f"- 系统ID: {cs_info.get('id', '')}")

                            result = "\n".join(output)
                            logger.info(f"成功获取当前登录用户详细信息")
                            return result
    except Exception as e:
        logger.warning(f"获取详细用户信息失败，将显示基础信息: {e}")

    # 如果获取详细信息失败，显示基础信息
    output = ["### 当前登录用户信息\n"]

    # 从 extUIMsg 中获取信息
    ext_ui_msg = session.get('extUIMsg', {})
    uid = ext_ui_msg.get('uid')
    unum = ext_ui_msg.get('unum')

    if uid:
        output.append(f"**UID**: {uid}")
    if unum:
        output.append(f"**UNUM**: {unum}")

    # 从 ck 中获取信息
    ck = session.get('ck', {})
    osudb_uid = ck.get('osudb_uid')
    osudb_appid = ck.get('osudb_appid')

    if osudb_uid and osudb_uid != uid:
        output.append(f"**osudb_uid**: {osudb_uid}")
    if osudb_appid:
        output.append(f"**AppID**: {osudb_appid}")

    # 尝试获取团队信息补充显示
    try:
        system_map = get_user_charge_systems(return_map=True)
        if system_map:
            output.append("")
            output.append(f"**已加入的收费系统**: {len(system_map)} 个")
            for name in system_map.keys():
                output.append(f"  - {name}")
    except:
        pass

    result = "\n".join(output)
    logger.info(f"成功获取当前登录用户信息")
    return result


def get_current_user_info(charge_system_name=None, community_name=None):
    """
    通过名称查询当前登录用户信息（智能模式）

    Args:
        charge_system_name: 收费系统名称（可选，不提供则直接显示登录用户信息）
        community_name: 小区名称（可选）
    """
    # 如果没有提供参数，直接显示当前登录用户信息
    if not charge_system_name and not community_name:
        result = get_current_login_user_info()
        if result:
            print(result)
        return

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

    if len(community_map) > 1:
        # 多个匹配，列出供用户选择
        print(f"找到多个匹配的小区，请使用完整的小区名称重新查询：")
        for name in community_map.keys():
            print(f"  - {name}")
        return

    # 只有一个匹配，继续处理
    comm_name, comm_id = next(iter(community_map.items()))
    print(f"找到小区：{comm_name}")

    # 获取初始化信息
    result = get_community_cs_init_info(str(comm_id), str(charge_system_id), comm_name)
    if result:
        print(result)


def send_wechat_payment_reminder(community_id: str, community_name: str = None) -> dict:
    """
    发送微信缴费提醒

    Args:
        community_id: 小区ID
        community_name: 小区名称（可选）

    Returns:
        API响应数据字典
    """
    import random
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None

    headers = get_headers_with_cookies(ck_dict, {"communityid": str(community_id)})

    payload = {
        "userTypes": [1],
        "houseLoc": [{"id": int(community_id), "houseType": 1}],
        "selectList": [],
        "assetType": 1,
        "tagIdList": None,
        "selectAll": True,
        "sendType": 3
    }

    try:
        response = requests.post(
            f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/wxCallSend",
            json=payload,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"接口调用失败，状态码: {response.status_code}, 响应内容: {response.text}")
            return None

        response.raise_for_status()
        data = response.json()

        if data.get('code') != 0:
            logger.error(f"发送微信缴费提醒失败: {data.get('msg')}")
            return None

        logger.info(f"成功发送微信缴费提醒到小区 {community_id}")
        return data

    except requests.exceptions.RequestException as e:
        logger.error(f"接口调用发生异常: {e}")
        return None


def send_wechat_payment_reminder_by_name(charge_system_name=None, community_name=None):
    """
    通过名称发送微信缴费提醒（智能模式）

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
        # 只有一个匹配，直接发送
        comm_name, comm_id = next(iter(community_map.items()))
        print(f"找到小区：{comm_name}")
        result = send_wechat_payment_reminder(str(comm_id), comm_name)
        if result:
            print(f"微信缴费提醒发送成功！")
            print(f"响应消息：{result.get('msg', '无')}")
        else:
            print("微信缴费提醒发送失败，请查看日志获取详细信息")
    else:
        # 多个匹配，列出供用户选择
        print(f"找到多个匹配的小区，请使用完整的小区名称重新查询：")
        for name in community_map.keys():
            print(f"  - {name}")


def send_single_house_sms_reminder(community_id: str, asset_id: int, uids: list, ids: list) -> dict:
    """
    发送单个房屋短信催缴

    Args:
        community_id: 小区ID
        asset_id: 房屋ID
        uids: 业主ID列表
        ids: 账单ID列表

    Returns:
        API响应数据字典
    """
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None

    headers = get_headers_with_cookies(ck_dict, {"communityid": str(community_id)})

    payload = {
        "sendType": 2,
        "templateId": -1,
        "uids": uids,
        "assetType": 1,
        "assetId": asset_id,
        "ids": ids,
        "communityID": int(community_id)
    }

    try:
        response = requests.post(
            f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/sendMessage",
            json=payload,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"发送短信催缴失败，状态码: {response.status_code}, 响应内容: {response.text}")
            return None

        response.raise_for_status()
        data = response.json()

        if data.get('code') != 0:
            logger.error(f"发送短信催缴失败: {data.get('msg')}")
            return None

        logger.info(f"成功发送短信催缴到房屋 {asset_id}，业主ID: {uids}，账单ID: {ids}")
        return data

    except requests.exceptions.RequestException as e:
        logger.error(f"发送短信催缴发生异常: {e}")
        return None


def send_single_house_sms_reminder_by_name(charge_system_name=None, community_name=None, keyword=None):
    """
    通过名称智能匹配房屋并发送短信催缴

    Args:
        charge_system_name: 收费系统名称
        community_name: 小区名称
        keyword: 房屋位置关键词
    """
    # 检查必要参数
    if not charge_system_name:
        print("NEED_INFO: 请提供收费系统名称")
        print("提示：可以先使用 list_charge_systems 命令查看可用的收费系统")
        return

    if not community_name:
        print("NEED_INFO: 请提供小区名称")
        return

    if not keyword:
        print("NEED_INFO: 请提供房屋位置关键词（如楼栋/单元/房屋号）")
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

    if len(community_map) > 1:
        # 多个匹配，列出供用户选择
        print(f"找到多个匹配的小区，请使用完整的小区名称重新查询：")
        for name in community_map.keys():
            print(f"  - {name}")
        return

    # 只有一个匹配，继续处理
    comm_name, comm_id = next(iter(community_map.items()))
    print(f"找到小区：{comm_name}")

    # 先尝试从缓存加载上一次的匹配列表
    cache_data = load_match_cache()
    if cache_data and str(cache_data.get('community_id')) == str(comm_id):
        cached_nodes = cache_data.get('nodes', [])
        if cached_nodes:
            # 尝试解析用户选择
            selected_node = parse_user_selection(keyword, cached_nodes)
            if selected_node:
                logger.info(f"用户选择了: {selected_node.get('name')}")
                # 清除缓存
                clear_match_cache()
                # 检查是否是房屋级别
                if selected_node['level'] != 'house':
                    print(f"请选择具体的房屋进行短信催缴，当前选择的是{selected_node['name']}（{selected_node['level']}）")
                    return
                # 继续处理
                return _process_single_house_sms_reminder(str(comm_id), selected_node, comm_name)
            else:
                # 解析失败，清除缓存，按新关键词重新搜索
                logger.info("无法解析用户选择，清除缓存并重新搜索")
                clear_match_cache()

    # 清理关键词
    clean_keyword = keyword.replace("短信催缴", "").replace("催缴", "").replace("的", "").strip()

    # 检查是否使用精确匹配
    use_exact_match = "/" in clean_keyword

    # 获取完整房屋结构
    household_data = search_household_structure(str(comm_id), "")

    if household_data is None:
        print("搜索房屋结构失败")
        return

    # 找出匹配的节点
    if use_exact_match:
        matching_nodes = find_matching_nodes(household_data, clean_keyword, exact_match=True)
        if not matching_nodes:
            logger.info("精确匹配未找到结果，使用模糊匹配")
            keywords = clean_keyword.split("/")
            search_kw = keywords[-1] if keywords else clean_keyword
            household_data_for_search = search_household_structure(str(comm_id), search_kw)
            if household_data_for_search:
                household_data = household_data_for_search
            matching_nodes = find_matching_nodes(household_data, clean_keyword)
    else:
        keywords = split_keywords(clean_keyword)
        search_kw = keywords[-1] if keywords else clean_keyword
        household_data_for_search = search_household_structure(str(comm_id), search_kw)
        if household_data_for_search:
            household_data = household_data_for_search
        matching_nodes = find_matching_nodes(household_data, clean_keyword)

    if not matching_nodes:
        # 尝试宽松匹配
        logger.info(f"严格匹配未找到，尝试宽松匹配: {clean_keyword}")
        matching_nodes = find_matching_nodes(household_data, clean_keyword, relaxed_match=True)

    if not matching_nodes:
        # 仍然没找到，生成候选列表
        logger.info(f"宽松匹配也未找到，生成候选列表")
        candidates = generate_candidates(household_data, clean_keyword)
        if candidates:
            print_candidates(clean_keyword, candidates)
        else:
            print(f"未找到与'{clean_keyword}'匹配的楼栋/单元/房屋，请确认输入是否正确")
        return

    if len(matching_nodes) == 1:
        node = matching_nodes[0]
        if node['level'] != 'house':
            print(f"请选择具体的房屋进行短信催缴，当前选择的是{node['name']}（{node['level']}）")
            return
        return _process_single_house_sms_reminder(str(comm_id), node, comm_name)
    else:
        save_match_cache(comm_id, matching_nodes)
        print("MULTI_MATCH:")
        for idx, node in enumerate(matching_nodes, 1):
            level_label = {
                'building': '楼栋',
                'unit': '单元',
                'house': '房屋'
            }.get(node['level'], '未知')
            print(f"{idx}. {node['name']} ({level_label})")


def _process_single_house_sms_reminder(community_id: str, house_node: dict, community_name: str):
    """
    内部函数：处理单个房屋短信催缴流程

    Args:
        community_id: 小区ID
        house_node: 房屋节点
        community_name: 小区名称
    """
    house_id = house_node['id']
    house_name = house_node['name']

    print(f"已选择房屋：{house_name}")

    # 查询欠费信息获取业主和账单ID
    arrears_data = get_household_arrears_by_id(community_id, str(house_id))
    if not arrears_data:
        print("查询欠费信息失败")
        return

    arrears_list = arrears_data.get('data', [])
    if not arrears_list:
        print(f"该房屋当前没有欠费账单，无需发送短信催缴")
        return

    # 提取信息：房屋ID、业主列表、账单ID列表
    # 从第一个欠费项获取房屋信息
    first_arrear = arrears_list[0]
    house_info = first_arrear.get('houseInfo', {})
    asset_id = house_info.get('id')
    if not asset_id:
        print("无法获取房屋ID信息")
        return

    # 收集所有业主ID和姓名
    # 每个欠费项可能包含houseUser，需要去重
    user_map = {}  # uid -> user name
    bill_ids = []  # 所有账单ID
    for arrear in arrears_list:
        # 收集账单ID - 从 idStr 拆分逗号分隔
        id_str = arrear.get('idStr', '')
        if id_str:
            for bill_id_str in id_str.split(','):
                bill_id_str = bill_id_str.strip()
                if bill_id_str and bill_id_str.isdigit():
                    bill_ids.append(int(bill_id_str))
        # 收集业主
        house_users = arrear.get('houseUser', [])
        for hu in house_users:
            uid = hu.get('id')  # 字段名是 id，不是 uid
            user_name = hu.get('name', '')  # 字段名是 name，不是 userName
            if uid and uid not in user_map:
                user_map[uid] = user_name

    if not user_map:
        print(f"未找到该房屋的业主信息，无法发送短信")
        return

    if not bill_ids:
        print(f"未找到该房屋的欠费账单ID，无法发送短信")
        return

    # 输出待确认信息
    print("\n### 待发送短信催缴信息\n")
    print(f"**小区**: {community_name}")
    print(f"**房屋**: {house_name}")
    print(f"**欠费账单数**: {len(bill_ids)} 条")
    print(f"**业主列表**: {', '.join(user_map.values())}\n")

    print("请确认是否发送短信催缴？")
    print("- 运行命令 `confirm_sms_reminder yes` 发送给全部业主")
    print("- 运行命令 `confirm_sms_reminder <序号>`（如`confirm_sms_reminder 1`或`confirm_sms_reminder 1,2`）只发送给指定业主")
    print("- 运行命令 `confirm_sms_reminder no` 取消")

    # 保存信息供用户确认
    # 将用户列表转为有序列表以便按序号选择
    pending_data = {
        'community_id': community_id,
        'asset_id': asset_id,
        'user_map': user_map,
        'bill_ids': bill_ids,
        'house_name': house_name,
        'community_name': community_name
    }
    # 存储到文件供后续处理
    save_sms_confirmation(pending_data)


def get_household_arrears_by_id(community_id: str, house_id: str) -> dict:
    """
    通过房屋ID查询房屋欠费信息

    Args:
        community_id: 小区ID
        house_id: 房屋ID

    Returns:
        API响应数据字典
    """
    import random
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None

    headers = get_headers_with_cookies(ck_dict, {"communityid": str(community_id)})

    params = {
        "id": house_id,
        "idType": 4,
        "assetType": 1,
        "page": 1,
        "pageSize": 20,
        "r": random.random()
    }

    try:
        response = requests.get(
            f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/getArrearsHouseList",
            params=params,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"查询房屋欠费失败，状态码: {response.status_code}, 响应内容: {response.text}")
            return None

        response.raise_for_status()
        data = response.json()

        if data.get('code') != 0:
            logger.error(f"查询房屋欠费失败: {data.get('msg')}")
            return None

        # 数据在 data.list 中
        arrears_list = data.get('data', {}).get('list', [])
        logger.info(f"成功查询房屋 {house_id} 欠费，共 {len(arrears_list)} 条")
        # 返回格式保持一致，外层data直接放列表
        result_data = data.copy()
        result_data['data'] = arrears_list
        return result_data

    except requests.exceptions.RequestException as e:
        logger.error(f"查询房屋欠费发生异常: {e}")
        return None


def confirm_sms_reminder(confirmation_input):
    """
    处理用户对短信催缴的确认，根据用户选择发送短信

    Args:
        confirmation_input: 用户确认输入 yes/no 或序号
    """
    confirmation_input = confirmation_input.strip().lower()

    # 加载待确认数据
    pending_data = load_sms_confirmation()
    if not pending_data:
        print("未找到待确认的短信催缴数据，请先使用 send_sms_reminder 命令查询")
        print("数据已过期（超过5分钟）或已被处理，请重新查询")
        return

    community_id = pending_data.get('community_id')
    asset_id = pending_data.get('asset_id')
    user_map = pending_data.get('user_map', {})  # uid -> user name
    bill_ids = pending_data.get('bill_ids', [])
    house_name = pending_data.get('house_name')
    community_name = pending_data.get('community_name')

    # 用户列表转为有序列表
    users_list = list(user_map.items())  # [(uid, name), ...]

    # 处理取消
    if confirmation_input in ['no', 'n', '否', '取消']:
        print("已取消短信催缴")
        clear_sms_confirmation()
        return

    # 处理发送全部业主
    if confirmation_input in ['yes', 'y', '是']:
        selected_uids = [uid for uid, name in users_list]
        selected_names = [name for uid, name in users_list]
    else:
        # 处理序号选择
        # 解析多个序号（逗号分隔）
        selected_indices = []
        try:
            for part in confirmation_input.split(','):
                part = part.strip()
                if part.isdigit():
                    idx = int(part) - 1  # 用户看到的是从1开始
                    if 0 <= idx < len(users_list):
                        selected_indices.append(idx)
        except ValueError:
            print(f"无法解析选择: {confirmation_input}，请使用 yes/no 或序号（如 1 或 1,2）")
            return

        if not selected_indices:
            print(f"未找到任何有效的选择，请重新输入")
            return

        selected_uids = [users_list[idx][0] for idx in selected_indices]
        selected_names = [users_list[idx][1] for idx in selected_indices]

    # 现在发送短信
    print(f"正在发送短信催缴...")
    result = send_single_house_sms_reminder(community_id, asset_id, selected_uids, bill_ids)

    if result:
        print("\n✓ 短信催缴发送成功！\n")
        print(f"**小区**: {community_name}")
        print(f"**房屋**: {house_name}")
        print(f"**接收业主**: {', '.join(selected_names)}")
        print(f"**账单数量**: {len(bill_ids)}")
        logger.info(f"短信催缴发送成功: 小区={community_name}, 房屋={house_name}, 业主={selected_names}, 账单数={len(bill_ids)}")
    else:
        print("\n✗ 短信催缴发送失败，请查看日志获取详细信息")

    # 清除确认缓存
    clear_sms_confirmation()


def get_meter_list(community_id: str, house_id: str) -> dict:
    """
    获取指定房屋的仪器列表

    Args:
        community_id: 小区ID
        house_id: 房屋ID

    Returns:
        API响应数据字典
    """
    import random
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None

    headers = get_headers_with_cookies(ck_dict, {"communityid": str(community_id)})

    params = {
        "publicType": 100,
        "id": house_id,
        "type": 4,
        "communityID": community_id,
        "page": 1,
        "pageSize": 20,
        "r": random.random()
    }

    try:
        response = requests.get(
            f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/getMeterList",
            params=params,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"获取仪器列表失败，状态码: {response.status_code}, 响应内容: {response.text}")
            return None

        response.raise_for_status()
        data = response.json()

        if data.get('code') != 0:
            logger.error(f"获取仪器列表失败: {data.get('msg')}")
            return None

        logger.info(f"成功获取房屋 {house_id} 的仪器列表")
        return data

    except requests.exceptions.RequestException as e:
        logger.error(f"获取仪器列表发生异常: {e}")
        return None


def get_meter_status(community_id: str, meter_id: str) -> dict:
    """
    获取指定仪器的状态（包括当前读数）

    Args:
        community_id: 小区ID
        meter_id: 仪器ID

    Returns:
        API响应数据字典
    """
    import random
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None

    headers = get_headers_with_cookies(ck_dict, {"communityid": str(community_id)})

    params = {
        "id": meter_id,
        "r": random.random()
    }

    try:
        response = requests.get(
            f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/getMeterStatus",
            params=params,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"获取仪器状态失败，状态码: {response.status_code}, 响应内容: {response.text}")
            return None

        response.raise_for_status()
        data = response.json()

        if data.get('code') != 0:
            logger.error(f"获取仪器状态失败: {data.get('msg')}")
            return None

        logger.info(f"成功获取仪器 {meter_id} 的状态")
        return data

    except requests.exceptions.RequestException as e:
        logger.error(f"获取仪器状态发生异常: {e}")
        return None


def submit_meter_reading(community_id: str, meter_id: str, meter_type: int, cur_set_reading: float, remark: str = "") -> dict:
    """
    提交抄表数据

    Args:
        community_id: 小区ID
        meter_id: 仪器ID
        meter_type: 仪器类型 (1=水表, 2=电表)
        cur_set_reading: 本期读数
        remark: 备注

    Returns:
        API响应数据字典
    """
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None

    headers = get_headers_with_cookies(ck_dict, {"communityid": str(community_id)})

    payload = {
        "meterId": meter_id,
        "meterType": meter_type,
        "curSetReading": cur_set_reading,
        "remark": remark,
        "entranceId": 10,
        "imgList": []
    }

    try:
        response = requests.post(
            f"{CHARGE_API_BASE_URL}/mkg/api/wechat/Charge/setMeterReading",
            json=payload,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"提交抄表失败，状态码: {response.status_code}, 响应内容: {response.text}")
            return None

        response.raise_for_status()
        data = response.json()

        if data.get('code') != 0:
            logger.error(f"提交抄表失败: {data.get('msg')}")
            return None

        logger.info(f"成功提交抄表数据，仪器ID: {meter_id}")
        return data

    except requests.exceptions.RequestException as e:
        logger.error(f"提交抄表发生异常: {e}")
        return None


def do_meter_reading_by_name(charge_system_name=None, community_name=None, keyword=None, meter_type_str=None, reading=None, remark=None):
    """
    智能抄表入口函数，处理整个抄表流程

    Args:
        charge_system_name: 收费系统名称
        community_name: 小区名称
        keyword: 房屋位置关键词
        meter_type_str: 仪器类型（"水表"或"电表"）
        reading: 本期读数
        remark: 备注
    """
    # 检查必要参数
    if not charge_system_name:
        print("NEED_INFO: 请提供收费系统名称")
        print("提示：可以先使用 list_charge_systems 命令查看可用的收费系统")
        return

    if not community_name:
        print("NEED_INFO: 请提供小区名称")
        return

    if not keyword:
        print("NEED_INFO: 请提供房屋位置关键词（如楼栋/单元/房屋号）")
        return

    if not meter_type_str:
        print("NEED_INFO: 请提供仪器类型（水表或电表）")
        return

    if not reading:
        print("NEED_INFO: 请提供本期读数")
        return

    # 转换仪器类型
    meter_type_str = meter_type_str.strip()
    if meter_type_str in ["水表", "水"]:
        meter_type = 1
        meter_type_label = "水表"
    elif meter_type_str in ["电表", "电"]:
        meter_type = 2
        meter_type_label = "电表"
    else:
        print(f"未知的仪器类型：{meter_type_str}，请使用'水表'或'电表'")
        return

    # 转换读数为浮点数
    try:
        reading_float = float(reading)
    except ValueError:
        print(f"读数格式错误：{reading}，请输入有效的数字")
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

    if len(community_map) > 1:
        # 多个匹配，列出供用户选择
        print(f"找到多个匹配的小区，请使用完整的小区名称重新查询：")
        for name in community_map.keys():
            print(f"  - {name}")
        return

    # 只有一个匹配，继续处理
    comm_name, comm_id = next(iter(community_map.items()))
    print(f"找到小区：{comm_name}")

    # 先尝试从缓存加载上一次的匹配列表
    cache_data = load_match_cache()
    if cache_data and str(cache_data.get('community_id')) == str(comm_id):
        cached_nodes = cache_data.get('nodes', [])
        if cached_nodes:
            # 尝试解析用户选择
            selected_node = parse_user_selection(keyword, cached_nodes)
            if selected_node:
                logger.info(f"用户选择了: {selected_node.get('name')}")
                # 清除缓存
                clear_match_cache()
                # 检查是否是房屋级别
                if selected_node['level'] != 'house':
                    print(f"请选择具体的房屋进行抄表，当前选择的是{selected_node['name']}（{selected_node['level']}）")
                    return
                # 继续处理抄表
                return _process_meter_reading(str(comm_id), selected_node, meter_type, meter_type_label, reading_float, remark, comm_name)
            else:
                # 解析失败，清除缓存，按新关键词重新搜索
                logger.info("无法解析用户选择，清除缓存并重新搜索")
                clear_match_cache()

    # 清理关键词
    clean_keyword = keyword.replace("抄表", "").replace("的", "").strip()

    # 检查是否使用精确匹配
    use_exact_match = "/" in clean_keyword

    # 获取完整房屋结构
    household_data = search_household_structure(str(comm_id), "")

    if household_data is None:
        print("搜索房屋结构失败")
        return

    # 找出匹配的节点
    if use_exact_match:
        matching_nodes = find_matching_nodes(household_data, clean_keyword, exact_match=True)
        if not matching_nodes:
            logger.info("精确匹配未找到结果，使用模糊匹配")
            keywords = clean_keyword.split("/")
            search_kw = keywords[-1] if keywords else clean_keyword
            household_data_for_search = search_household_structure(str(comm_id), search_kw)
            if household_data_for_search:
                household_data = household_data_for_search
            matching_nodes = find_matching_nodes(household_data, clean_keyword)
    else:
        keywords = split_keywords(clean_keyword)
        search_kw = keywords[-1] if keywords else clean_keyword
        household_data_for_search = search_household_structure(str(comm_id), search_kw)
        if household_data_for_search:
            household_data = household_data_for_search
        matching_nodes = find_matching_nodes(household_data, clean_keyword)

    if not matching_nodes:
        # 尝试宽松匹配
        logger.info(f"严格匹配未找到，尝试宽松匹配: {clean_keyword}")
        matching_nodes = find_matching_nodes(household_data, clean_keyword, relaxed_match=True)

    if not matching_nodes:
        # 仍然没找到，生成候选列表
        logger.info(f"宽松匹配也未找到，生成候选列表")
        candidates = generate_candidates(household_data, clean_keyword)
        if candidates:
            print_candidates(clean_keyword, candidates)
        else:
            print(f"未找到与'{clean_keyword}'匹配的楼栋/单元/房屋，请确认输入是否正确")
        return

    if len(matching_nodes) == 1:
        node = matching_nodes[0]
        if node['level'] != 'house':
            print(f"请选择具体的房屋进行抄表，当前选择的是{node['name']}（{node['level']}）")
            return
        return _process_meter_reading(str(comm_id), node, meter_type, meter_type_label, reading_float, remark, comm_name)
    else:
        save_match_cache(comm_id, matching_nodes)
        print("MULTI_MATCH:")
        for idx, node in enumerate(matching_nodes, 1):
            level_label = {
                'building': '楼栋',
                'unit': '单元',
                'house': '房屋'
            }.get(node['level'], '未知')
            print(f"{idx}. {node['name']} ({level_label})")


def get_meter_status_by_name(charge_system_name=None, community_name=None, keyword=None, meter_type_str=None):
    """
    智能查询当前读数入口函数，处理整个查询流程

    Args:
        charge_system_name: 收费系统名称
        community_name: 小区名称
        keyword: 房屋位置关键词
        meter_type_str: 仪器类型（"水表"或"电表"）
    """
    # 检查必要参数
    if not charge_system_name:
        print("NEED_INFO: 请提供收费系统名称")
        print("提示：可以先使用 list_charge_systems 命令查看可用的收费系统")
        return

    if not community_name:
        print("NEED_INFO: 请提供小区名称")
        return

    if not keyword:
        print("NEED_INFO: 请提供房屋位置关键词（如楼栋/单元/房屋号）")
        return

    if not meter_type_str:
        print("NEED_INFO: 请提供仪器类型（水表或电表）")
        return

    # 转换仪器类型
    meter_type_str = meter_type_str.strip()
    if meter_type_str in ["水表", "水"]:
        meter_type = 1
        meter_type_label = "水表"
    elif meter_type_str in ["电表", "电"]:
        meter_type = 2
        meter_type_label = "电表"
    else:
        print(f"未知的仪器类型：{meter_type_str}，请使用'水表'或'电表'")
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

    if len(community_map) > 1:
        # 多个匹配，列出供用户选择
        print(f"找到多个匹配的小区，请使用完整的小区名称重新查询：")
        for name in community_map.keys():
            print(f"  - {name}")
        return

    # 只有一个匹配，继续处理
    comm_name, comm_id = next(iter(community_map.items()))
    print(f"找到小区：{comm_name}")

    # 先尝试从缓存加载上一次的匹配列表
    cache_data = load_match_cache()
    if cache_data and str(cache_data.get('community_id')) == str(comm_id):
        cached_nodes = cache_data.get('nodes', [])
        if cached_nodes:
            # 尝试解析用户选择
            selected_node = parse_user_selection(keyword, cached_nodes)
            if selected_node:
                logger.info(f"用户选择了: {selected_node.get('name')}")
                # 清除缓存
                clear_match_cache()
                # 检查是否是房屋级别
                if selected_node['level'] != 'house':
                    print(f"请选择具体的房屋进行查询，当前选择的是{selected_node['name']}（{selected_node['level']}）")
                    return
                # 继续处理查询
                return _process_get_meter_status(str(comm_id), selected_node, meter_type, meter_type_label, comm_name)
            else:
                # 解析失败，清除缓存，按新关键词重新搜索
                logger.info("无法解析用户选择，清除缓存并重新搜索")
                clear_match_cache()

    # 清理关键词
    clean_keyword = keyword.replace("当前读数", "").replace("读数", "").replace("的", "").strip()

    # 检查是否使用精确匹配
    use_exact_match = "/" in clean_keyword

    # 获取完整房屋结构
    household_data = search_household_structure(str(comm_id), "")

    if household_data is None:
        print("搜索房屋结构失败")
        return

    # 找出匹配的节点
    if use_exact_match:
        matching_nodes = find_matching_nodes(household_data, clean_keyword, exact_match=True)
        if not matching_nodes:
            logger.info("精确匹配未找到结果，使用模糊匹配")
            keywords = clean_keyword.split("/")
            search_kw = keywords[-1] if keywords else clean_keyword
            household_data_for_search = search_household_structure(str(comm_id), search_kw)
            if household_data_for_search:
                household_data = household_data_for_search
            matching_nodes = find_matching_nodes(household_data, clean_keyword)
    else:
        keywords = split_keywords(clean_keyword)
        search_kw = keywords[-1] if keywords else clean_keyword
        household_data_for_search = search_household_structure(str(comm_id), search_kw)
        if household_data_for_search:
            household_data = household_data_for_search
        matching_nodes = find_matching_nodes(household_data, clean_keyword)

    if not matching_nodes:
        # 尝试宽松匹配
        logger.info(f"严格匹配未找到，尝试宽松匹配: {clean_keyword}")
        matching_nodes = find_matching_nodes(household_data, clean_keyword, relaxed_match=True)

    if not matching_nodes:
        # 仍然没找到，生成候选列表
        logger.info(f"宽松匹配也未找到，生成候选列表")
        candidates = generate_candidates(household_data, clean_keyword)
        if candidates:
            print_candidates(clean_keyword, candidates)
        else:
            print(f"未找到与'{clean_keyword}'匹配的楼栋/单元/房屋，请确认输入是否正确")
        return

    if len(matching_nodes) == 1:
        node = matching_nodes[0]
        if node['level'] != 'house':
            print(f"请选择具体的房屋进行查询，当前选择的是{node['name']}（{node['level']}）")
            return
        return _process_get_meter_status(str(comm_id), node, meter_type, meter_type_label, comm_name)
    else:
        save_match_cache(comm_id, matching_nodes)
        print("MULTI_MATCH:")
        for idx, node in enumerate(matching_nodes, 1):
            level_label = {
                'building': '楼栋',
                'unit': '单元',
                'house': '房屋'
            }.get(node['level'], '未知')
            print(f"{idx}. {node['name']} ({level_label})")


def _process_meter_reading(community_id: str, house_node: dict, meter_type: int, meter_type_label: str, reading: float, remark: str, community_name: str):
    """
    内部函数：处理抄表流程

    Args:
        community_id: 小区ID
        house_node: 房屋节点
        meter_type: 仪器类型
        meter_type_label: 仪器类型标签
        reading: 本期读数
        remark: 备注
        community_name: 小区名称
    """
    house_id = house_node['id']
    house_name = house_node['name']

    print(f"找到房屋：{house_name}")

    # 获取仪器列表
    meter_list_data = get_meter_list(community_id, str(house_id))
    if not meter_list_data:
        print("获取仪器列表失败")
        return

    meter_list = meter_list_data.get('data', {}).get('list', [])
    if not meter_list:
        print(f"该房屋未找到任何仪器")
        return

    # 筛选对应类型的仪器
    matching_meters = [m for m in meter_list if m.get('type') == meter_type]
    if not matching_meters:
        print(f"该房屋未找到{meter_type_label}")
        # 列出所有可用仪器
        print("可用的仪器：")
        for m in meter_list:
            mt_label = "水表" if m.get('type') == 1 else "电表"
            print(f"  - {m.get('name', '未知')} ({mt_label})")
        return

    if len(matching_meters) > 1:
        print(f"找到多个{meter_type_label}，请选择：")
        for idx, m in enumerate(matching_meters, 1):
            print(f"{idx}. {m.get('name', '未知')}")
        return

    # 只有一个匹配的仪器，提交抄表
    meter = matching_meters[0]
    meter_id = meter.get('id')
    meter_name = meter.get('name', '未知')

    print(f"找到{meter_type_label}：{meter_name}")

    # 提交抄表
    result = submit_meter_reading(community_id, meter_id, meter_type, reading, remark or "")
    if not result:
        print("提交抄表失败")
        return

    print("### 抄表成功\n")
    print(f"**小区名称**: {community_name}")
    print(f"**房屋位置**: {house_name}")
    print(f"**仪器类型**: {meter_type_label}")
    print(f"**仪器名称**: {meter_name}")
    print(f"**本期读数**: {reading}")
    if remark:
        print(f"**备注**: {remark}")


def _process_get_meter_status(community_id: str, house_node: dict, meter_type: int, meter_type_label: str, community_name: str):
    """
    内部函数：处理获取当前读数流程

    Args:
        community_id: 小区ID
        house_node: 房屋节点
        meter_type: 仪器类型
        meter_type_label: 仪器类型标签
        community_name: 小区名称
    """
    house_id = house_node['id']
    house_name = house_node['name']

    print(f"找到房屋：{house_name}")

    # 获取仪器列表
    meter_list_data = get_meter_list(community_id, str(house_id))
    if not meter_list_data:
        print("获取仪器列表失败")
        return

    meter_list = meter_list_data.get('data', {}).get('list', [])
    if not meter_list:
        print(f"该房屋未找到任何仪器")
        return

    # 筛选对应类型的仪器
    matching_meters = [m for m in meter_list if m.get('type') == meter_type]
    if not matching_meters:
        print(f"该房屋未找到{meter_type_label}")
        # 列出所有可用仪器
        print("可用的仪器：")
        for m in meter_list:
            mt_label = "水表" if m.get('type') == 1 else "电表"
            print(f"  - {m.get('name', '未知')} ({mt_label})")
        return

    if len(matching_meters) > 1:
        print(f"找到多个{meter_type_label}，请选择：")
        for idx, m in enumerate(matching_meters, 1):
            print(f"{idx}. {m.get('name', '未知')}")
        return

    # 只有一个匹配的仪器，获取当前读数
    meter = matching_meters[0]
    meter_id = meter.get('id')
    meter_name = meter.get('name', '未知')

    print(f"找到{meter_type_label}：{meter_name}")

    # 获取仪器状态（当前读数）
    result = get_meter_status(community_id, meter_id)
    if not result:
        print("获取当前读数失败")
        return

    data = result.get('data', {})
    now_num = data.get('nowNum', '未知')

    print("### 查询成功\n")
    print(f"**小区名称**: {community_name}")
    print(f"**房屋位置**: {house_name}")
    print(f"**仪器类型**: {meter_type_label}")
    print(f"**仪器名称**: {meter_name}")
    print(f"**当前读数**: {now_num}")


def logout() -> str:
    """
    登出马克账号。
    """
    session_mgr.clear_session()
    logger.info("成功登出马克账号")
    return "已成功登出马克账号。"


# === 收款确认缓存相关函数 ===
def get_payment_confirmation_cache_path():
    """获取收款确认缓存文件路径"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), '.payment_confirmation_cache.json')


def save_payment_confirmation_cache(cache_data):
    """保存收款待确认信息到缓存"""
    cache_path = get_payment_confirmation_cache_path()
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)
    logger.info("收款确认缓存已保存")


def load_payment_confirmation_cache():
    """从缓存加载收款待确认信息"""
    cache_path = get_payment_confirmation_cache_path()
    if not os.path.exists(cache_path):
        return None
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"读取收款确认缓存失败: {e}")
        return None


def clear_payment_confirmation_cache():
    """清除收款确认缓存"""
    cache_path = get_payment_confirmation_cache_path()
    if os.path.exists(cache_path):
        os.remove(cache_path)
        logger.info("收款确认缓存已清除")


# === 退款确认缓存相关函数 ===
def get_refund_confirmation_cache_path():
    """获取退款确认缓存文件路径"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), '.refund_confirmation_cache.json')


def save_refund_confirmation_cache(cache_data):
    """保存退款待确认信息到缓存"""
    cache_path = get_refund_confirmation_cache_path()
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)
    logger.info("退款确认缓存已保存")


def load_refund_confirmation_cache():
    """从缓存加载退款待确认信息"""
    cache_path = get_refund_confirmation_cache_path()
    if not os.path.exists(cache_path):
        return None
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"读取退款确认缓存失败: {e}")
        return None


def clear_refund_confirmation_cache():
    """清除退款确认缓存"""
    cache_path = get_refund_confirmation_cache_path()
    if os.path.exists(cache_path):
        os.remove(cache_path)
        logger.info("退款确认缓存已清除")


# === 已缴账单撤回缓存相关 ===
def get_revoke_confirmation_cache_path():
    """获取撤回确认缓存文件路径"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, '.revoke_confirmation_cache.json')


def save_revoke_confirmation_cache(cache_data):
    """保存待确认撤回信息到缓存"""
    cache_path = get_revoke_confirmation_cache_path()
    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        logger.info("撤回确认缓存已保存")
    except Exception as e:
        logger.error(f"保存撤回确认缓存失败: {e}")


def load_revoke_confirmation_cache():
    """从缓存加载待确认撤回信息"""
    cache_path = get_revoke_confirmation_cache_path()
    if not os.path.exists(cache_path):
        return None
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"读取撤回确认缓存失败: {e}")
        return None


def clear_revoke_confirmation_cache():
    """清除撤回确认缓存"""
    cache_path = get_revoke_confirmation_cache_path()
    if os.path.exists(cache_path):
        os.remove(cache_path)
        logger.info("撤回确认缓存已清除")


# === 优惠减免确认缓存相关 ===
def get_discount_confirmation_cache_path():
    """获取优惠确认缓存文件路径"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, '.discount_confirmation_cache.json')


def save_discount_confirmation_cache(cache_data):
    """保存待确认优惠信息到缓存"""
    cache_path = get_discount_confirmation_cache_path()
    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        logger.info("优惠确认缓存已保存")
    except Exception as e:
        logger.error(f"保存优惠确认缓存失败: {e}")


def load_discount_confirmation_cache():
    """从缓存加载待确认优惠信息"""
    cache_path = get_discount_confirmation_cache_path()
    if not os.path.exists(cache_path):
        return None
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"读取优惠确认缓存失败: {e}")
        return None


def clear_discount_confirmation_cache():
    """清除优惠确认缓存"""
    cache_path = get_discount_confirmation_cache_path()
    if os.path.exists(cache_path):
        os.remove(cache_path)
        logger.info("优惠确认缓存已清除")


# === 违约金设置确认缓存相关 ===
def get_late_money_confirmation_cache_path():
    """获取违约金设置确认缓存文件路径"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, '.late_money_confirmation_cache.json')


def save_late_money_confirmation_cache(cache_data):
    """保存待确认违约金信息到缓存"""
    cache_path = get_late_money_confirmation_cache_path()
    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        logger.info("违约金设置确认缓存已保存")
    except Exception as e:
        logger.error(f"保存违约金设置确认缓存失败: {e}")


def load_late_money_confirmation_cache():
    """从缓存加载待确认违约金信息"""
    cache_path = get_late_money_confirmation_cache_path()
    if not os.path.exists(cache_path):
        return None
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"读取违约金设置确认缓存失败: {e}")
        return None


def clear_late_money_confirmation_cache():
    """清除违约金设置确认缓存"""
    cache_path = get_late_money_confirmation_cache_path()
    if os.path.exists(cache_path):
        os.remove(cache_path)
        logger.info("违约金设置确认缓存已清除")


# === 支付方式映射 ===
def get_pay_type_by_name(pay_type_name: str) -> int:
    """根据支付方式中文名称获取 payType 编码"""
    mapping = {
        '现金': 2,
        '微信': 1,
        '支付宝': 3,
    }
    # 模糊匹配
    for name, code in mapping.items():
        if name in pay_type_name:
            return code
    # 默认返回现金
    return 2


def get_pay_name_by_type(pay_type: int) -> str:
    """根据 payType 编码获取中文名称"""
    mapping = {
        1: '微信',
        2: '现金',
        3: '支付宝',
    }
    return mapping.get(pay_type, f'未知({pay_type})')


def collect_house_bills(community_id: str, asset_id: str, asset_type: int, node_name: str,
                       community_name: str, start_time: int, end_time: int, charge_item_id: str = None, pay_type: int = None):
    """
    查询特定房屋的待收款账单列表
    """
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None

    headers = get_headers_with_cookies(ck_dict)

    # 构建请求负载
    payload = {
        "communityID": int(community_id),
        "assetType": asset_type,
        "assetId": int(asset_id),
        "payStatus": 0,  # 0 = 未付
        "index": "",
        "selectChargeItemList": [],
        "selectChargeItemAll": False,
        "generateStartTime": start_time,
        "generateEndTime": end_time,
        "dealLogId": 0,
        "categoryId": 0,
        "sortType": 1,
        "chargeItemVersion": 2,
        "chargeItemCategorys": []
    }

    # 如果指定了收费项目，添加筛选条件
    if charge_item_id is not None:
        payload["selectChargeItemList"] = [int(charge_item_id)]

    url = f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/getCashierDeskListByIndex"

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=10
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"查询账单接口调用发生异常: {e}")
        print(f"接口调用发生异常: {str(e)}")
        return None

    if response.status_code != 200:
        logger.error(f"查询账单失败，状态码: {response.status_code}, 响应内容: {response.text}")
        print(f"查询账单失败，HTTP状态码: {response.status_code}")
        return None

    data = response.json()
    if data.get('code') != 0:
        logger.error(f"查询账单错误: {data.get('msg')}")
        print(f"查询账单失败：{data.get('msg')}")
        return None

    result_data = data.get('data', {})
    bill_list = []

    # 解析账单列表
    date_list = result_data.get('list', [])
    for date_item in date_list:
        for category_data in date_item.get('categoryData', []):
            for record in category_data.get('records', []):
                bill_list.append({
                    'id': record.get('id'),
                    'version': record.get('version', 0),
                    'chargeItemName': record.get('chargeItemName', '未知收费项目'),
                    'date': record.get('date', ''),
                    'amount': record.get('billAmount', 0),  # 单位：分，使用 billAmount 字段
                })

    if not bill_list:
        print(f"未找到该房屋在此时间段内的未付账单")
        print(f"小区：{community_name}")
        print(f"房屋：{node_name}")
        print(f"时间范围：{datetime.fromtimestamp(start_time).strftime('%Y-%m-%d')} 至 {datetime.fromtimestamp(end_time).strftime('%Y-%m-%d')}")
        return None

    # 计算总金额
    total_amount = sum(bill['amount'] for bill in bill_list)

    # 保存到缓存供确认
    cache_data = {
        'community_id': community_id,
        'community_name': community_name,
        'asset_id': asset_id,
        'asset_type': asset_type,
        'node_name': node_name,
        'start_time': start_time,
        'end_time': end_time,
        'charge_item_id': charge_item_id,
        'bill_list': bill_list,
        'total_amount': total_amount,
        'pay_type': pay_type,
    }
    save_payment_confirmation_cache(cache_data)

    # 输出给用户
    total_amount_yuan = total_amount / 100
    pay_type_name = get_pay_name_by_type(pay_type) if pay_type else '现金'
    print(f"\n### 待收款账单信息\n")
    print(f"**小区**: {community_name}")
    print(f"**房屋**: {node_name}")
    print(f"**时间范围**: {datetime.fromtimestamp(start_time).strftime('%Y-%m-%d')} 至 {datetime.fromtimestamp(end_time).strftime('%Y-%m-%d')}")
    print(f"**支付方式**: {pay_type_name}")
    print(f"**待收款账单数**: {len(bill_list)} 条")
    print(f"**总金额**: ¥ {total_amount_yuan:.2f}\n")
    print("账单列表:")
    for idx, bill in enumerate(bill_list, 1):
        amount_yuan = bill['amount'] / 100
        date_str = f"{bill['date']} " if bill['date'] else ""
        print(f"{idx}. {date_str}{bill['chargeItemName']} - ¥ {amount_yuan:.2f}")
    print()
    print("请确认是否进行收款？")
    print("- 运行命令 `confirm_payment yes` 收取全部账单")
    print("- 运行命令 `confirm_payment <序号>`（如`confirm_payment 1`或`confirm_payment 1,2`）只收取指定账单")
    print("- 运行命令 `confirm_payment no` 取消")

    return cache_data


def collect_house_bills_by_name(charge_system_name=None, community_name=None, keyword=None,
                               start_date_str=None, end_date_str=None, charge_item_name=None, pay_type_name=None):
    """
    通过名称对特定房屋指定时间范围的账单进行收款（智能匹配模式）
    """
    # 1. 获取收费系统
    system_map = get_user_charge_systems(return_map=True)
    if not system_map:
        print("获取收费系统列表失败")
        return
    if charge_system_name not in system_map:
        print(f"未找到收费系统：{charge_system_name}")
        print("可用的收费系统：" + ", ".join(system_map.keys()))
        return
    charge_system_id = system_map[charge_system_name]
    print(f"找到收费系统：{charge_system_name}")

    # 2. 搜索小区
    community_map = search_community(charge_system_id, community_name, return_map=True)
    if not community_map:
        print(f"未找到匹配的小区：{community_name}")
        return
    if len(community_map) > 1:
        print(f"找到多个匹配的小区，请选择：")
        for name in community_map.keys():
            print(f"  - {name}")
        return
    # 只有一个匹配，直接使用
    community_name_found = list(community_map.keys())[0]
    community_id = community_map[community_name_found]
    print(f"找到小区：{community_name_found}")

    # 2.5 处理收费项目筛选
    charge_item_id = None
    if charge_item_name:
        print(f"正在匹配收费项目：{charge_item_name}...")
        charge_item_id = get_charge_item_id_by_name(str(community_id), str(charge_system_id), charge_item_name)
        logger.info(f"收费项目筛选: {charge_item_name} → ID: {charge_item_id}")

    # 3. 解析日期
    try:
        if start_date_str:
            start_date = parse_iso_date(start_date_str)
            start_time = int(datetime.combine(start_date, datetime.min.time()).timestamp())
        else:
            # 默认本月开始
            today = datetime.today()
            start_time = int(datetime(today.year, today.month, 1).timestamp())
            start_date_str = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d')

        if end_date_str:
            end_date = parse_iso_date(end_date_str)
            end_time = int(datetime.combine(end_date, datetime.max.time()).timestamp())
        else:
            # 默认今天结束
            today = datetime.today()
            end_time = int(datetime.combine(today, datetime.max.time()).timestamp())
            end_date_str = datetime.fromtimestamp(end_time).strftime('%Y-%m-%d')
    except ValueError as e:
        print(f"日期解析错误: {e}")
        print("请使用 YYYY-MM-DD 格式，比如 2026-03-01")
        return

    # 4. 加载匹配缓存
    cache_data = load_match_cache()
    selected_node = None

    # 检查缓存中是否有可用的匹配结果（用户选择场景）
    if cache_data and str(cache_data.get('community_id')) == str(community_id):
        cached_nodes = cache_data.get('nodes', [])
        if cached_nodes:
            # 尝试解析用户选择
            selected_node = parse_user_selection(keyword, cached_nodes)
            if selected_node:
                logger.info(f"用户选择了: {selected_node.get('full_name')}")
                # 清除缓存
                clear_match_cache()
                # 检查是否是房屋级别
                if selected_node['level'] != 'house':
                    print(f"请选择具体的房屋进行收款，当前选择的是{selected_node['full_name']}（{selected_node['level']}）")
                    return
                # 继续处理
                node_id = str(selected_node['id'])
                node_name = selected_node['full_name']
                asset_type = 1  # 房屋固定为1

                # 解析支付方式
                if pay_type_name:
                    pay_type = get_pay_type_by_name(pay_type_name)
                else:
                    pay_type = 2  # 默认现金
                logger.info(f"支付方式: {pay_type_name}, 编码: {pay_type}")
                logger.info(f"已选择房屋: {node_name}, ID: {node_id}")

                # 5. 查询账单
                collect_house_bills(str(community_id), node_id, asset_type, node_name, community_name_found, start_time, end_time, charge_item_id, pay_type)
                return
            else:
                # 解析失败，清除缓存，按新关键词重新搜索
                logger.info("无法解析用户选择，清除缓存并重新搜索")
                clear_match_cache()

    # 清理关键词
    clean_keyword = keyword.replace("收款", "").replace("账单", "").replace("的", "").strip()

    # 检查是否使用精确匹配（包含 / 分隔符）
    use_exact_match = "/" in clean_keyword

    # 获取完整房屋结构
    household_data = search_household_structure(str(community_id), "")
    if household_data is None:
        print("搜索房屋结构失败")
        return

    # 找出匹配的节点
    if use_exact_match:
        matching_nodes = find_matching_nodes(household_data, clean_keyword, exact_match=True)
        if not matching_nodes:
            logger.info("精确匹配未找到结果，使用模糊匹配")
            keywords = clean_keyword.split("/")
            search_kw = keywords[-1] if keywords else clean_keyword
            household_data_for_search = search_household_structure(str(community_id), search_kw)
            matching_nodes = find_matching_nodes(household_data_for_search, clean_keyword, exact_match=False, relaxed_match=True)
    else:
        # 模糊匹配
        matching_nodes = find_matching_nodes(household_data, clean_keyword, exact_match=False, relaxed_match=True)

    if not matching_nodes:
        # 宽松匹配也没找到，尝试宽松匹配整个关键词
        matching_nodes = find_matching_nodes(household_data, clean_keyword, exact_match=False, relaxed_match=True)
        if not matching_nodes:
            print("未找到任何匹配的房屋，请检查关键词重试")
            return

    if len(matching_nodes) == 1:
        # 只有一个匹配，直接使用
        selected_node = matching_nodes[0]
        if selected_node['level'] != 'house':
            print(f"匹配结果不是房屋，当前匹配到的是 {selected_node['level']}：{selected_node['full_name']}")
            print("请提供更精确的关键词匹配到具体房屋")
            return

        clear_match_cache()
        node_id = str(selected_node['id'])
        node_name = selected_node['full_name']
        asset_type = 1  # 房屋固定为1

        # 解析支付方式
        if pay_type_name:
            pay_type = get_pay_type_by_name(pay_type_name)
        else:
            pay_type = 2  # 默认现金
        logger.info(f"支付方式: {pay_type_name}, 编码: {pay_type}")
        logger.info(f"已选择房屋: {node_name}, ID: {node_id}")

        # 5. 查询账单
        collect_house_bills(str(community_id), node_id, asset_type, node_name, community_name_found, start_time, end_time, charge_item_id, pay_type)
    else:
        # 多个匹配，保存到缓存让用户选择
        save_match_cache(community_id, matching_nodes)
        print(f"找到多个匹配，请选择：")
        for idx, node in enumerate(matching_nodes, 1):
            print(f"{idx}. {node['full_name']} ({node['level']})")
        return


def confirm_payment_collection(confirmation_input: str, pay_type_name: str = None):
    """
    处理用户确认，执行收款
    """
    # 加载缓存
    cache_data = load_payment_confirmation_cache()
    if not cache_data:
        print("没有待确认的收款，请先运行 collect_payment 查询账单")
        return

    if confirmation_input.lower() == 'no':
        print("已取消收款")
        clear_payment_confirmation_cache()
        return

    community_id = cache_data['community_id']
    community_name = cache_data['community_name']
    asset_id = cache_data['asset_id']
    asset_type = cache_data['asset_type']
    node_name = cache_data['node_name']
    all_bills = cache_data['bill_list']

    # 解析用户选择
    selected_bills = []
    if confirmation_input.lower() == 'yes':
        # 全部选择
        selected_bills = all_bills
    else:
        # 按序号选择，支持逗号分隔，如 1,2
        try:
            # 处理中文逗号
            confirmation_input = confirmation_input.replace('，', ',')
            indices = [int(idx.strip()) - 1 for idx in confirmation_input.split(',') if idx.strip()]
            for idx in indices:
                if 0 <= idx < len(all_bills):
                    selected_bills.append(all_bills[idx])
        except ValueError:
            print("序号解析错误，请使用 yes/no 或数字序号（如 1 或 1,2）")
            return

    if not selected_bills:
        print("没有选中任何账单，请重新选择或确认取消")
        return

    # 计算总金额
    total_amount = sum(bill['amount'] for bill in selected_bills)

    # 获取支付类型编码，优先使用缓存中的，如果没有则使用参数（兼容旧调用）
    cached_pay_type = cache_data.get('pay_type')
    if cached_pay_type:
        pay_type = cached_pay_type
    elif pay_type_name:
        pay_type = get_pay_type_by_name(pay_type_name)
    else:
        # 默认现金
        pay_type = 2

    pay_type_name = get_pay_name_by_type(pay_type)

    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None

    headers = get_headers_with_cookies(ck_dict)

    # 构建 billInfos
    bill_infos = [{'id': bill['id'], 'version': bill['version']} for bill in selected_bills]

    # 当前时间戳
    pay_time = int(datetime.now().timestamp())

    # 构建请求负载
    payload = {
        "communityID": int(community_id),
        "payType": pay_type,
        "payTime": pay_time,
        "billInfos": bill_infos,
        "assetType": asset_type,
        "assetId": int(asset_id),
        "amount": total_amount,
        "houseId": int(asset_id),
        "depositCheck": {
            "depositPayAmount": total_amount,
            "leftPayAmount": 0
        },
        "version": 3
    }

    url = f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/addBillPayV2"

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=10
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"收款接口调用发生异常: {e}")
        print(f"接口调用发生异常: {str(e)}")
        return None

    if response.status_code != 200:
        logger.error(f"收款失败，状态码: {response.status_code}, 响应内容: {response.text}")
        print(f"收款失败，HTTP状态码: {response.status_code}")
        return None

    data = response.json()
    if data.get('code') != 0:
        logger.error(f"收款错误: {data.get('msg')}")
        print(f"收款失败：{data.get('msg')}")
        return None

    # 收款成功
    pay_time_str = datetime.fromtimestamp(pay_time).strftime('%Y-%m-%d %H:%M:%S')
    total_amount_yuan = total_amount / 100

    print(f"\n✓ 收款成功！\n")
    print(f"**小区**: {community_name}")
    print(f"**房屋**: {node_name}")
    print(f"**支付方式**: {pay_type_name}")
    print(f"**收款账单数**: {len(selected_bills)} 条")
    print(f"**总金额**: ¥ {total_amount_yuan:.2f}")
    print(f"**交易时间**: {pay_time_str}")

    logger.info(f"收款成功，小区: {community_name}, 房屋: {node_name}, 账单数: {len(selected_bills)}, 总金额: {total_amount_yuan:.2f}")

    # 清除缓存
    clear_payment_confirmation_cache()

    return data


def list_house_refundable_bills(community_id: str, asset_id: str, asset_type: int, node_name: str,
                       community_name: str, start_time: int, end_time: int, charge_item_id: str = None):
    """
    查询特定房屋的可退款（已支付）账单列表

    Args:
        community_id: 小区ID
        asset_id: 资产ID（房屋ID）
        asset_type: 资产类型（1=房屋）
        node_name: 节点名称（房屋全名）
        community_name: 小区名称
        start_time: 开始时间戳
        end_time: 结束时间戳
        charge_item_id: 收费项目ID（可选，筛选）
    """
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None

    headers = get_headers_with_cookies(ck_dict)

    # 构建请求负载 - 查询已支付账单（payStatus = 1）
    payload = {
        "communityID": int(community_id),
        "assetType": asset_type,
        "assetId": int(asset_id),
        "payStatus": 1,  # 1 = 已支付，可退款
        "index": "",
        "selectChargeItemList": [],
        "selectChargeItemAll": False,
        "dealLogId": 0,
        "categoryId": 0,
        "chargeItemVersion": 2,
        "chargeItemCategorys": []
    }

    # 如果指定了收费项目，添加筛选条件
    if charge_item_id is not None:
        payload["selectChargeItemList"] = [int(charge_item_id)]

    url = f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/getCashierDeskListByIndex"

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=10
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"查询可退款账单接口调用发生异常: {e}")
        print(f"接口调用发生异常: {str(e)}")
        return None

    if response.status_code != 200:
        logger.error(f"查询可退款账单失败，状态码: {response.status_code}, 响应内容: {response.text}")
        print(f"查询失败，HTTP状态码: {response.status_code}")
        return None

    data = response.json()
    if data.get('code') != 0:
        logger.error(f"查询错误: {data.get('msg')}")
        print(f"查询失败：{data.get('msg')}")
        return None

    # 提取账单列表
    # API返回结构: data.list[] 中每个元素按月份分组 {"date": "2026-03", "records": [实际账单数组]}
    month_groups = data.get('data', {}).get('list', [])
    if not month_groups:
        print(f"\n未找到可退款账单。")
        print(f"小区: {community_name}")
        print(f"房屋: {node_name}")
        clear_refund_confirmation_cache()
        return None

    # 展平所有月份的账单
    all_bills = []
    for month_group in month_groups:
        records = month_group.get('records', [])
        all_bills.extend(records)

    # 筛选时间范围内的账单（接口返回的是所有已支付，我们需要根据时间过滤）
    filtered_bills = []
    total_amount = 0
    for bill in all_bills:
        # 检查账单是否可退款（canRevoke = 1）
        if bill.get('canRevoke') != 1:
            continue
        # 按时间筛选
        bill_pay_time = bill.get('payTime', 0)
        if start_time <= bill_pay_time <= end_time:
            filtered_bills.append(bill)
            total_amount += bill.get('amount', 0)

    if not filtered_bills:
        print(f"\n指定时间范围内没有可退款账单。")
        print(f"小区: {community_name}")
        print(f"房屋: {node_name}")
        clear_refund_confirmation_cache()
        return None

    # 保存到缓存供确认
    cache_data = {
        "community_id": community_id,
        "community_name": community_name,
        "asset_id": asset_id,
        "asset_type": asset_type,
        "node_name": node_name,
        "start_time": start_time,
        "end_time": end_time,
        "charge_item_id": charge_item_id,
        "bill_list": filtered_bills,
        "total_amount": total_amount
    }
    save_refund_confirmation_cache(cache_data)

    # 按月份分组
    from collections import defaultdict
    bills_by_month = defaultdict(list)
    for bill in filtered_bills:
        date_str = bill.get('date', '')
        # date_str 格式一般是 "YYYY-MM"
        bills_by_month[date_str].append(bill)

    # 格式化输出
    start_date_str = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d')
    end_date_str = datetime.fromtimestamp(end_time).strftime('%Y-%m-%d')
    total_amount_yuan = total_amount / 100

    print(f"\n找到收费系统：{charge_system_name if 'charge_system_name' in locals() else '未知'}")
    print(f"找到小区：{community_name}")
    print(f"已选择房屋：{node_name}\n")
    print(f"### 可退款账单信息\n")
    print(f"**小区**: {community_name}")
    print(f"**房屋**: {node_name}")
    print(f"**时间范围**: {start_date_str} 至 {end_date_str}")
    print(f"**可退款账单数**: {len(filtered_bills)} 条")
    print(f"**总金额**: ¥ {total_amount_yuan:.2f}\n")
    print(f"账单列表按月份分组：\n")

    # 按月份排序输出
    sorted_months = sorted(bills_by_month.keys(), reverse=True)
    global_idx = 1
    for month in sorted_months:
        month_bills = bills_by_month[month]
        # 转换为 "YYYY年MM月" 格式
        try:
            y, m = month.split('-')
            month_display = f"{y}年{m}月"
        except:
            month_display = month
        print(f"---\n")
        print(f"#### {month_display}\n")
        for bill in month_bills:
            amount_yuan = bill.get('amount', 0) / 100
            pay_time_str = datetime.fromtimestamp(bill.get('payTime', 0)).strftime('%Y-%m-%d %H:%M:%S')
            charge_item_name = bill.get('chargeItemName', '未知收费项目')
            pay_type = bill.get('payType', '未知支付方式')
            deal_log_id = bill.get('dealLogId', 0)

            print(f"{global_idx}. **{charge_item_name}**")
            print(f"   - 实缴金额: ¥ {amount_yuan:.2f}")
            print(f"   - 支付方式: {pay_type}")
            print(f"   - 缴费时间: {pay_time_str}")
            print(f"   - 交易单号: {deal_log_id}")
            print(f"   - 可退款: 是\n")
            global_idx += 1

    print(f"---\n")
    print(f"请确认是否进行退款？")
    print(f"- 运行命令 `confirm_refund yes` 退款全部账单")
    print(f"- 运行命令 `confirm_refund <序号>`（如`confirm_refund 1`或`confirm_refund 1,2`）只退款指定账单")
    print(f"- 运行命令 `confirm_refund no` 取消")

    logger.info(f"找到 {len(filtered_bills)} 条可退款账单，总金额 {total_amount_yuan:.2f}，等待用户确认")
    return cache_data


def list_house_revocable_bills(community_id: str, asset_id: str, asset_type: int, node_name: str,
                       community_name: str, start_time: int, end_time: int, charge_item_id: str = None):
    """
    查询特定房屋的可撤回（已支付）账单列表

    Args:
        community_id: 小区ID
        asset_id: 资产ID（房屋ID）
        asset_type: 资产类型（1=房屋）
        node_name: 节点名称（房屋全名）
        community_name: 小区名称
        start_time: 开始时间戳
        end_time: 结束时间戳
        charge_item_id: 收费项目ID（可选，筛选）
    """
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None

    headers = get_headers_with_cookies(ck_dict)

    # 构建请求负载 - 查询已支付账单（payStatus = 1）
    payload = {
        "communityID": int(community_id),
        "assetType": asset_type,
        "assetId": int(asset_id),
        "payStatus": 1,  # 1 = 已支付，可撤回
        "index": "",
        "selectChargeItemList": [],
        "selectChargeItemAll": False,
        "dealLogId": 0,
        "categoryId": 0,
        "chargeItemVersion": 2,
        "chargeItemCategorys": []
    }

    # 如果指定了收费项目，添加筛选条件
    if charge_item_id is not None:
        payload["selectChargeItemList"] = [int(charge_item_id)]

    url = f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/getCashierDeskListByIndex"

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=10
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"查询可撤回账单接口调用发生异常: {e}")
        print(f"接口调用发生异常: {str(e)}")
        return None

    if response.status_code != 200:
        logger.error(f"查询可撤回账单失败，状态码: {response.status_code}, 响应内容: {response.text}")
        print(f"查询失败，HTTP状态码: {response.status_code}")
        return None

    data = response.json()
    if data.get('code') != 0:
        logger.error(f"查询错误: {data.get('msg')}")
        print(f"查询失败：{data.get('msg')}")
        return None

    # 提取账单列表
    # API返回结构: data.list[] 中每个元素按月份分组 {"date": "2026-03", "records": [实际账单数组]}
    month_groups = data.get('data', {}).get('list', [])
    if not month_groups:
        print(f"\n未找到可撤回账单。")
        print(f"小区: {community_name}")
        print(f"房屋: {node_name}")
        clear_revoke_confirmation_cache()
        return None

    # 展平所有月份的账单
    all_bills = []
    for month_group in month_groups:
        records = month_group.get('records', [])
        all_bills.extend(records)

    # 筛选时间范围内的账单（接口返回的是所有已支付，我们需要根据时间过滤）
    filtered_bills = []
    total_amount = 0
    for bill in all_bills:
        # 检查账单是否可撤回（canRevoke = 1）
        if bill.get('canRevoke') != 1:
            continue
        # 按时间筛选
        bill_pay_time = bill.get('payTime', 0)
        if start_time <= bill_pay_time <= end_time:
            filtered_bills.append(bill)
            total_amount += bill.get('amount', 0)

    if not filtered_bills:
        print(f"\n指定时间范围内没有可撤回账单。")
        print(f"小区: {community_name}")
        print(f"房屋: {node_name}")
        clear_revoke_confirmation_cache()
        return None

    # 保存到缓存供确认
    cache_data = {
        "community_id": community_id,
        "community_name": community_name,
        "asset_id": asset_id,
        "asset_type": asset_type,
        "node_name": node_name,
        "start_time": start_time,
        "end_time": end_time,
        "charge_item_id": charge_item_id,
        "bill_list": filtered_bills,
        "total_amount": total_amount
    }
    save_revoke_confirmation_cache(cache_data)

    # 按月份分组
    from collections import defaultdict
    bills_by_month = defaultdict(list)
    for bill in filtered_bills:
        date_str = bill.get('date', '')
        # date_str 格式一般是 "YYYY-MM"
        bills_by_month[date_str].append(bill)

    # 格式化输出
    start_date_str = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d')
    end_date_str = datetime.fromtimestamp(end_time).strftime('%Y-%m-%d')
    total_amount_yuan = total_amount / 100

    print(f"\n找到小区：{community_name}")
    print(f"已选择房屋：{node_name}\n")
    print(f"### 可撤回已缴账单信息\n")
    print(f"**小区**: {community_name}")
    print(f"**房屋**: {node_name}")
    print(f"**时间范围**: {start_date_str} 至 {end_date_str}")
    print(f"**可撤回账单数**: {len(filtered_bills)} 条")
    print(f"**总金额**: ¥ {total_amount_yuan:.2f}\n")
    print(f"账单列表按月份分组：\n")

    # 按月份排序输出
    sorted_months = sorted(bills_by_month.keys(), reverse=True)
    global_idx = 1
    for month in sorted_months:
        month_bills = bills_by_month[month]
        # 转换为 "YYYY年MM月" 格式
        try:
            y, m = month.split('-')
            month_display = f"{y}年{m}月"
        except:
            month_display = month
        print(f"---\n")
        print(f"#### {month_display}\n")
        for bill in month_bills:
            amount_yuan = bill.get('amount', 0) / 100
            pay_time_str = datetime.fromtimestamp(bill.get('payTime', 0)).strftime('%Y-%m-%d %H:%M:%S')
            charge_item_name = bill.get('chargeItemName', '未知收费项目')
            pay_type = bill.get('payType', '未知支付方式')
            deal_log_id = bill.get('dealLogId', 0)

            print(f"{global_idx}. **{charge_item_name}**")
            print(f"   - 实缴金额: ¥ {amount_yuan:.2f}")
            print(f"   - 支付方式: {get_pay_name_by_type(bill.get('payType', 0))}")
            print(f"   - 缴费时间: {pay_time_str}")
            print(f"   - 交易单号: {deal_log_id}")
            print(f"   - 可撤回: 是\n")
            global_idx += 1

    print(f"---\n")
    print(f"请确认是否进行撤回？")
    print(f"- 运行命令 `confirm_revoke yes` 撤回全部账单")
    print(f"- 运行命令 `confirm_revoke <序号>`（如`confirm_revoke 1`或`confirm_revoke 1,2`）只撤回指定账单")
    print(f"- 运行命令 `confirm_revoke no` 取消")

    logger.info(f"找到 {len(filtered_bills)} 条可撤回账单，总金额 {total_amount_yuan:.2f}，等待用户确认")
    return cache_data


def list_refundable_bills_by_name(charge_system_name=None, community_name=None, keyword=None,
                           start_date_str=None, end_date_str=None, charge_item_name=None):
    """
    通过名称智能匹配查询可退款账单

    Args:
        charge_system_name: 收费系统名称
        community_name: 小区名称
        keyword: 房屋关键词
        start_date_str: 开始日期字符串（可选）
        end_date_str: 结束日期字符串（可选）
        charge_item_name: 收费项目名称（可选）
    """
    # 解析日期，如果没有提供则默认本月
    today = datetime.now()
    if start_date_str is None:
        # 本月第一天
        start_date = datetime(today.year, today.month, 1)
        start_time = int(start_date.timestamp())
    else:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            start_time = int(start_date.timestamp())
        except ValueError:
            print(f"错误：开始日期格式不正确，请使用 YYYY-MM-DD 格式（如 {today.strftime('%Y-%m-%d')}）")
            return

    if end_date_str is None:
        # 今天
        end_date = datetime(today.year, today.month, today.day, 23, 59, 59)
        end_time = int(end_date.timestamp())
    else:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            end_date = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
            end_time = int(end_date.timestamp())
        except ValueError:
            print(f"错误：结束日期格式不正确，请使用 YYYY-MM-DD 格式（如 {today.strftime('%Y-%m-%d')}）")
            return

    logger.info(f"时间范围: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")

    # 1. 获取收费系统
    system_map = get_user_charge_systems(return_map=True)
    if not system_map:
        print("获取收费系统列表失败")
        return
    if charge_system_name not in system_map:
        print(f"未找到收费系统：{charge_system_name}")
        print("可用的收费系统：" + ", ".join(system_map.keys()))
        return
    charge_system_id = system_map[charge_system_name]
    print(f"找到收费系统：{charge_system_name}")

    # 2. 搜索小区
    community_map = search_community(charge_system_id, community_name, return_map=True)
    if not community_map:
        print(f"未找到匹配的小区：{community_name}")
        return
    if len(community_map) > 1:
        print(f"找到多个匹配的小区，请选择：")
        for name in community_map.keys():
            print(f"  - {name}")
        return
    # 只有一个匹配，直接使用
    community_name_found = list(community_map.keys())[0]
    community_id = community_map[community_name_found]
    print(f"找到小区：{community_name_found}")

    # 2.5 处理收费项目筛选
    charge_item_id = None
    if charge_item_name:
        print(f"正在匹配收费项目：{charge_item_name}...")
        charge_item_id = get_charge_item_id_by_name(str(community_id), str(charge_system_id), charge_item_name)
        logger.info(f"收费项目筛选: {charge_item_name} → ID: {charge_item_id}")

    # 3. 加载匹配缓存
    cache_data = load_match_cache()
    selected_node = None

    # 检查缓存中是否有可用的匹配结果（用户选择场景）
    if cache_data and str(cache_data.get('community_id')) == str(community_id):
        cached_nodes = cache_data.get('nodes', [])
        if cached_nodes:
            # 尝试解析用户选择
            selected_node = parse_user_selection(keyword, cached_nodes)
            if selected_node:
                logger.info(f"用户选择了: {selected_node.get('full_name')}")
                # 清除缓存
                clear_match_cache()
                # 检查是否是房屋级别
                if selected_node['level'] != 'house':
                    print(f"请选择具体的房屋进行退款，当前选择的是{selected_node['full_name']}（{selected_node['level']}）")
                    return
                # 继续处理
                node_id = str(selected_node['id'])
                node_name = selected_node['full_name']
                asset_type = 1  # 房屋固定为1

                logger.info(f"已选择房屋: {node_name}, ID: {node_id}")

                # 4. 查询可退款账单
                list_house_refundable_bills(str(community_id), node_id, asset_type, node_name, community_name_found, start_time, end_time, charge_item_id)
                return
            else:
                # 解析失败，清除缓存，按新关键词重新搜索
                logger.info("无法解析用户选择，清除缓存并重新搜索")
                clear_match_cache()

    # 清理关键词
    clean_keyword = keyword.replace("退款", "").replace("账单", "").replace("的", "").strip()

    # 检查是否使用精确匹配（包含 / 分隔符）
    use_exact_match = "/" in clean_keyword

    # 获取完整房屋结构
    household_data = search_household_structure(str(community_id), "")
    if household_data is None:
        print("搜索房屋结构失败")
        return

    # 找出匹配的节点
    if use_exact_match:
        matching_nodes = find_matching_nodes(household_data, clean_keyword, exact_match=True)
        if not matching_nodes:
            logger.info("精确匹配未找到结果，使用模糊匹配")
            keywords = clean_keyword.split("/")
            search_kw = keywords[-1] if keywords else clean_keyword
            household_data_for_search = search_household_structure(str(community_id), search_kw)
            matching_nodes = find_matching_nodes(household_data_for_search, clean_keyword, exact_match=False, relaxed_match=True)
    else:
        # 模糊匹配
        matching_nodes = find_matching_nodes(household_data, clean_keyword, exact_match=False, relaxed_match=True)

    if not matching_nodes:
        # 宽松匹配也没找到，尝试宽松匹配整个关键词
        matching_nodes = find_matching_nodes(household_data, clean_keyword, exact_match=False, relaxed_match=True)
        if not matching_nodes:
            print("未找到任何匹配的房屋，请检查关键词重试")
            return

    if len(matching_nodes) == 1:
        # 只有一个匹配，直接使用
        selected_node = matching_nodes[0]
        if selected_node['level'] != 'house':
            print(f"匹配结果不是房屋，当前匹配到的是 {selected_node['level']}：{selected_node['full_name']}")
            print("请提供更精确的关键词匹配到具体房屋")
            return

        clear_match_cache()
        node_id = str(selected_node['id'])
        node_name = selected_node['full_name']
        asset_type = 1  # 房屋固定为1

        # 查找收费项目ID（如果指定了）
        charge_item_id = None
        if charge_item_name:
            # 获取初始化信息查找收费项目
            logger.info(f"筛选收费项目: {charge_item_name}")
            cs_init_info = get_community_cs_init_info(str(community_id), str(charge_system_id))
            if cs_init_info:
                charge_items = cs_init_info.get('chargeItemList', [])
                for item in charge_items:
                    if charge_item_name in item.get('name', ''):
                        charge_item_id = str(item.get('id'))
                        logger.info(f"匹配到收费项目: {item.get('name')}, ID: {charge_item_id}")
                        break

        logger.info(f"已选择房屋: {node_name}, ID: {node_id}")

        # 查询可退款账单
        list_house_refundable_bills(str(community_id), node_id, asset_type, node_name, community_name_found, start_time, end_time, charge_item_id)
    else:
        # 多个匹配，保存到缓存让用户选择
        save_match_cache(community_id, matching_nodes)
        print(f"找到多个匹配，请选择：")
        for idx, node in enumerate(matching_nodes, 1):
            print(f"{idx}. {node['full_name']} ({node['level']})")
        return


def list_revocable_bills_by_name(charge_system_name=None, community_name=None, keyword=None,
                           start_date_str=None, end_date_str=None, charge_item_name=None):
    """
    通过名称智能匹配查询可撤回已缴账单

    Args:
        charge_system_name: 收费系统名称
        community_name: 小区名称
        keyword: 房屋关键词
        start_date_str: 开始日期字符串（可选）
        end_date_str: 结束日期字符串（可选）
        charge_item_name: 收费项目名称（可选）
    """
    # 解析日期，如果没有提供则默认本月
    today = datetime.now()
    if start_date_str is None:
        # 本月第一天
        start_date = datetime(today.year, today.month, 1)
        start_time = int(start_date.timestamp())
    else:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            start_time = int(start_date.timestamp())
        except ValueError:
            print(f"错误：开始日期格式不正确，请使用 YYYY-MM-DD 格式（如 {today.strftime('%Y-%m-%d')}）")
            return

    if end_date_str is None:
        # 今天
        end_date = datetime(today.year, today.month, today.day, 23, 59, 59)
        end_time = int(end_date.timestamp())
    else:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            end_date = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
            end_time = int(end_date.timestamp())
        except ValueError:
            print(f"错误：结束日期格式不正确，请使用 YYYY-MM-DD 格式（如 {today.strftime('%Y-%m-%d')}）")
            return

    logger.info(f"时间范围: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")

    # 1. 获取收费系统
    system_map = get_user_charge_systems(return_map=True)
    if not system_map:
        print("获取收费系统列表失败")
        return
    if charge_system_name not in system_map:
        print(f"未找到收费系统：{charge_system_name}")
        print("可用的收费系统：" + ", ".join(system_map.keys()))
        return
    charge_system_id = system_map[charge_system_name]
    print(f"找到收费系统：{charge_system_name}")

    # 2. 搜索小区
    community_map = search_community(charge_system_id, community_name, return_map=True)
    if not community_map:
        print(f"未找到匹配的小区：{community_name}")
        return
    if len(community_map) > 1:
        print(f"找到多个匹配的小区，请选择：")
        for name in community_map.keys():
            print(f"  - {name}")
        return
    # 只有一个匹配，直接使用
    community_name_found = list(community_map.keys())[0]
    community_id = community_map[community_name_found]
    print(f"找到小区：{community_name_found}")

    # 2.5 处理收费项目筛选
    charge_item_id = None
    if charge_item_name:
        print(f"正在匹配收费项目：{charge_item_name}...")
        charge_item_id = get_charge_item_id_by_name(str(community_id), str(charge_system_id), charge_item_name)
        logger.info(f"收费项目筛选: {charge_item_name} → ID: {charge_item_id}")

    # 3. 加载匹配缓存
    cache_data = load_match_cache()
    selected_node = None

    # 检查缓存中是否有可用的匹配结果（用户选择场景）
    if cache_data and str(cache_data.get('community_id')) == str(community_id):
        cached_nodes = cache_data.get('nodes', [])
        if cached_nodes:
            # 尝试解析用户选择
            selected_node = parse_user_selection(keyword, cached_nodes)
            if selected_node:
                logger.info(f"用户选择了: {selected_node.get('full_name')}")
                # 清除缓存
                clear_match_cache()
                # 检查是否是房屋级别
                if selected_node['level'] != 'house':
                    print(f"请选择具体的房屋进行撤回，当前选择的是{selected_node['full_name']}（{selected_node['level']}）")
                    return
                # 继续处理
                node_id = str(selected_node['id'])
                node_name = selected_node['full_name']
                asset_type = 1  # 房屋固定为1

                logger.info(f"已选择房屋: {node_name}, ID: {node_id}")

                # 4. 查询可撤回账单
                list_house_revocable_bills(str(community_id), node_id, asset_type, node_name, community_name_found, start_time, end_time, charge_item_id)
                return
            else:
                # 解析失败，清除缓存，按新关键词重新搜索
                logger.info("无法解析用户选择，清除缓存并重新搜索")
                clear_match_cache()

    # 清理关键词 - 移除"撤回"关键词
    clean_keyword = keyword.replace("撤回", "").replace("账单", "").replace("的", "").strip()

    # 检查是否使用精确匹配（包含 / 分隔符）
    use_exact_match = "/" in clean_keyword

    # 获取完整房屋结构
    household_data = search_household_structure(str(community_id), "")
    if household_data is None:
        print("搜索房屋结构失败")
        return

    # 找出匹配的节点
    if use_exact_match:
        matching_nodes = find_matching_nodes(household_data, clean_keyword, exact_match=True)
        if not matching_nodes:
            logger.info("精确匹配未找到结果，使用模糊匹配")
            keywords = clean_keyword.split("/")
            search_kw = keywords[-1] if keywords else clean_keyword
            household_data_for_search = search_household_structure(str(community_id), search_kw)
            matching_nodes = find_matching_nodes(household_data_for_search, clean_keyword, exact_match=False, relaxed_match=True)
    else:
        # 模糊匹配
        matching_nodes = find_matching_nodes(household_data, clean_keyword, exact_match=False, relaxed_match=True)

    if not matching_nodes:
        # 宽松匹配也没找到，尝试宽松匹配整个关键词
        matching_nodes = find_matching_nodes(household_data, clean_keyword, exact_match=False, relaxed_match=True)
        if not matching_nodes:
            print("未找到任何匹配的房屋，请检查关键词重试")
            return

    if len(matching_nodes) == 1:
        # 只有一个匹配，直接使用
        selected_node = matching_nodes[0]
        if selected_node['level'] != 'house':
            print(f"匹配结果不是房屋，当前匹配到的是 {selected_node['level']}：{selected_node['full_name']}")
            print("请提供更精确的关键词匹配到具体房屋")
            return

        clear_match_cache()
        node_id = str(selected_node['id'])
        node_name = selected_node['full_name']
        asset_type = 1  # 房屋固定为1

        # 查找收费项目ID（如果指定了）
        charge_item_id = None
        if charge_item_name:
            # 获取初始化信息查找收费项目
            logger.info(f"筛选收费项目: {charge_item_name}")
            cs_init_info = get_community_cs_init_info(str(community_id), str(charge_system_id))
            if cs_init_info:
                charge_items = cs_init_info.get('chargeItemList', [])
                for item in charge_items:
                    if charge_item_name in item.get('name', ''):
                        charge_item_id = str(item.get('id'))
                        logger.info(f"匹配到收费项目: {item.get('name')}, ID: {charge_item_id}")
                        break

        logger.info(f"已选择房屋: {node_name}, ID: {node_id}")

        # 查询可撤回账单
        list_house_revocable_bills(str(community_id), node_id, asset_type, node_name, community_name_found, start_time, end_time, charge_item_id)
    else:
        # 多个匹配，保存到缓存让用户选择
        save_match_cache(community_id, matching_nodes)
        print(f"找到多个匹配，请选择：")
        for idx, node in enumerate(matching_nodes, 1):
            print(f"{idx}. {node['full_name']} ({node['level']})")
        return


def confirm_refund(confirmation_input: str):
    """
    确认退款，根据用户选择执行退款

    Args:
        confirmation_input: 用户输入 yes/no/序号
    """
    # 加载缓存
    cache_data = load_refund_confirmation_cache()
    if not cache_data:
        print("没有待确认的退款，请先运行 list_refundable_bills 查询可退款账单")
        return

    confirmation_input = confirmation_input.strip().lower()
    if confirmation_input == 'no':
        print("已取消退款")
        clear_refund_confirmation_cache()
        logger.info("用户取消退款")
        return

    all_bills = cache_data.get('bill_list', [])
    if not all_bills:
        print("缓存中没有可退款账单")
        clear_refund_confirmation_cache()
        return

    # 解析用户选择哪些账单
    selected_bills = []
    if confirmation_input == 'yes' or confirmation_input == 'y':
        # 全部退款
        selected_bills = all_bills
        logger.info(f"用户选择退款全部 {len(selected_bills)} 个账单")
    else:
        # 解析序号（支持逗号分隔，如 "1" 或 "1,2"）
        try:
            # 处理逗号分隔
            if ',' in confirmation_input:
                indices = [int(idx.strip()) - 1 for idx in confirmation_input.split(',')]
            else:
                indices = [int(confirmation_input) - 1]

            for idx in indices:
                if 0 <= idx < len(all_bills):
                    selected_bills.append(all_bills[idx])
                else:
                    print(f"序号 {idx + 1} 超出范围，请检查输入")
                    return
        except ValueError:
            print("输入格式不正确，请使用 yes/no 或序号（如 1 或 1,2）")
            return

    if not selected_bills:
        print("未选择任何可退款账单")
        return

    # 开始逐个退款
    community_id = cache_data.get('community_id')
    community_name = cache_data.get('community_name')
    node_name = cache_data.get('node_name')

    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None

    headers = get_headers_with_cookies(ck_dict)

    success_count = 0
    success_bills = []
    total_refund_amount = 0
    failed_bills = []

    for bill in selected_bills:
        bill_id = bill.get('id')
        deal_log_id = bill.get('dealLogId')
        charge_item_name = bill.get('chargeItemName')
        amount = bill.get('amount', 0)
        date_str = bill.get('date', '')

        payload = {
            "communityID": int(community_id),
            "dealLogId": int(deal_log_id),
            "billId": int(bill_id)
        }

        url = f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/refundByDealLog"

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=10
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"退款接口调用发生异常: {e}")
            failed_bills.append({
                "bill": bill,
                "error": str(e)
            })
            continue

        if response.status_code != 200:
            logger.error(f"退款失败，账单ID: {bill_id}, 状态码: {response.status_code}, 响应: {response.text}")
            failed_bills.append({
                "bill": bill,
                "error": f"HTTP {response.status_code}"
            })
            continue

        data = response.json()
        if data.get('code') != 0:
            error_msg = data.get('msg', '未知错误')
            logger.error(f"退款失败，账单ID: {bill_id}, 错误: {error_msg}")
            failed_bills.append({
                "bill": bill,
                "error": error_msg
            })
            continue

        # 退款成功
        success_count += 1
        total_refund_amount += amount
        success_bills.append({
            "bill": bill,
            "date": date_str,
            "charge_item_name": charge_item_name,
            "amount": amount
        })
        logger.info(f"退款成功，账单ID: {bill_id}, 交易单号: {deal_log_id}, 金额: {amount / 100:.2f}")

    # 输出结果
    refund_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    total_refund_amount_yuan = total_refund_amount / 100

    if success_count > 0:
        print(f"\n✓ 退款成功！\n")
        print(f"**小区**: {community_name}")
        print(f"**房屋**: {node_name}")
        print(f"**退款账单数**: {success_count} 条")
        print(f"**总金额**: ¥ {total_refund_amount_yuan:.2f}")
        print(f"**退款时间**: {refund_time_str}\n")
        print(f"退款账单明细：")
        for idx, sb in enumerate(success_bills, 1):
            amount_yuan = sb['amount'] / 100
            date_display = sb['date']
            try:
                y, m = date_display.split('-')
                date_display = f"{y}年{m}月"
            except:
                pass
            print(f"{idx}. {date_display} {sb['charge_item_name']} - ¥ {amount_yuan:.2f}")

        if failed_bills:
            print(f"\n部分退款失败 ({len(failed_bills)} 项):")
            for idx, fb in enumerate(failed_bills, 1):
                bill = fb['bill']
                print(f"{idx}. {bill.get('chargeItemName')} - {fb['error']}")

    else:
        print(f"\n退款全部失败！\n")
        for idx, fb in enumerate(failed_bills, 1):
            bill = fb['bill']
            print(f"{idx}. {bill.get('chargeItemName')} - {fb['error']}")

    # 清除缓存
    clear_refund_confirmation_cache()
    logger.info(f"退款完成，成功 {success_count}/{len(selected_bills)}，总退款 {total_refund_amount_yuan:.2f}")


def confirm_revoke(confirmation_input: str):
    """
    确认撤回，根据用户选择执行已缴账单撤回

    Args:
        confirmation_input: 用户输入 yes/no/序号
    """
    # 加载缓存
    cache_data = load_revoke_confirmation_cache()
    if not cache_data:
        print("没有待确认的撤回，请先运行 list_revocable_bills 查询可撤回账单")
        return

    confirmation_input = confirmation_input.strip().lower()
    if confirmation_input == 'no':
        print("已取消撤回")
        clear_revoke_confirmation_cache()
        logger.info("用户取消撤回")
        return

    all_bills = cache_data.get('bill_list', [])
    if not all_bills:
        print("缓存中没有可撤回账单")
        clear_revoke_confirmation_cache()
        return
        return

    # 解析用户选择哪些账单
    selected_bills = []
    if confirmation_input == 'yes' or confirmation_input == 'y':
        # 全部撤回
        selected_bills = all_bills
        logger.info(f"用户选择撤回全部 {len(selected_bills)} 个账单")
    else:
        # 解析序号（支持逗号分隔，如 "1" 或 "1,2"）
        try:
            # 处理逗号分隔
            if ',' in confirmation_input:
                indices = [int(idx.strip()) - 1 for idx in confirmation_input.split(',')]
            else:
                indices = [int(confirmation_input) - 1]

            for idx in indices:
                if 0 <= idx < len(all_bills):
                    selected_bills.append(all_bills[idx])
                else:
                    print(f"序号 {idx + 1} 超出范围，请检查输入")
                    return
        except ValueError:
            print("输入格式不正确，请使用 yes/no 或序号（如 1 或 1,2）")
            return

    if not selected_bills:
        print("未选择任何可撤回账单")
        return

    # 开始逐个撤回
    community_id = cache_data.get('community_id')
    community_name = cache_data.get('community_name')
    node_name = cache_data.get('node_name')

    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None

    headers = get_headers_with_cookies(ck_dict, {"communityid": str(community_id)})

    success_count = 0
    success_bills = []
    total_revoke_amount = 0
    failed_bills = []

    for bill in selected_bills:
        bill_id = bill.get('id')
        charge_item_name = bill.get('chargeItemName')
        amount = bill.get('amount', 0)
        date_str = bill.get('date', '')
        version = bill.get('version', 0)

        payload = {
            "id": int(bill_id),
            "payStatus": 4,  # 固定值4表示撤回
            "version": int(version)
        }

        url = f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/modBill"

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=10
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"撤回接口调用发生异常: {e}")
            failed_bills.append({
                "bill": bill,
                "error": str(e)
            })
            continue

        if response.status_code != 200:
            logger.error(f"撤回失败，账单ID: {bill_id}, 状态码: {response.status_code}, 响应: {response.text}")
            failed_bills.append({
                "bill": bill,
                "error": f"HTTP {response.status_code}"
            })
            continue

        data = response.json()
        if data.get('code') != 0:
            error_msg = data.get('msg', '未知错误')
            logger.error(f"撤回失败，账单ID: {bill_id}, 错误: {error_msg}")
            failed_bills.append({
                "bill": bill,
                "error": error_msg
            })
            continue

        # 撤回成功
        success_count += 1
        total_revoke_amount += amount
        success_bills.append({
            "bill": bill,
            "date": date_str,
            "charge_item_name": charge_item_name,
            "amount": amount
        })
        logger.info(f"撤回成功，账单ID: {bill_id}, 金额: {amount / 100:.2f}")

    # 输出结果
    revoke_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    total_revoke_amount_yuan = total_revoke_amount / 100

    if success_count > 0:
        print(f"\n✓ 撤回成功！\n")
        print(f"**小区**: {community_name}")
        print(f"**房屋**: {node_name}")
        print(f"**撤回账单数**: {success_count} 条")
        print(f"**总金额**: ¥ {total_revoke_amount_yuan:.2f}")
        print(f"**撤回时间**: {revoke_time_str}\n")
        print(f"撤回账单明细：")
        for idx, sb in enumerate(success_bills, 1):
            amount_yuan = sb['amount'] / 100
            date_display = sb['date']
            try:
                y, m = date_display.split('-')
                date_display = f"{y}年{m}月"
            except:
                pass
            print(f"{idx}. {date_display} {sb['charge_item_name']} - ¥ {amount_yuan:.2f}")

        if failed_bills:
            print(f"\n部分撤回失败 ({len(failed_bills)} 项):")
            for idx, fb in enumerate(failed_bills, 1):
                bill = fb['bill']
                print(f"{idx}. {bill.get('chargeItemName')} - {fb['error']}")

    else:
        print(f"\n撤回全部失败！\n")
        for idx, fb in enumerate(failed_bills, 1):
            bill = fb['bill']
            print(f"{idx}. {bill.get('chargeItemName')} - {fb['error']}")

    # 清除缓存
    clear_revoke_confirmation_cache()
    logger.info(f"撤回完成，成功 {success_count}/{len(selected_bills)}，总撤回 {total_revoke_amount_yuan:.2f}")


def discount_house_bills(community_id: str, asset_id: str, asset_type: int, node_name: str,
                       community_name: str, start_time: int, end_time: int, charge_item_id: str = None, discount_amount_yuan: float = 0):
    """
    查询特定房屋的待优惠账单列表，检查支付状态后保存到缓存等待用户确认
    """
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None

    headers = get_headers_with_cookies(ck_dict, {"communityid": str(community_id)})

    # 构建查询参数
    payload = {
        "communityID": int(community_id),
        "assetType": asset_type,
        "assetId": int(asset_id),
        "payStatus": 0,  # 只查询未支付账单
        "index": "",
        "selectChargeItemList": [int(charge_item_id)] if charge_item_id else [],
        "selectChargeItemAll": charge_item_id is None,
        "generateStartTime": start_time,
        "generateEndTime": end_time,
        "dealLogId": 0,
        "categoryId": 0,
        "sortType": 1,
        "chargeItemVersion": 2,
        "chargeItemCategorys": []
    }

    url = f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/getCashierDeskListByIndex"

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=30
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"查询账单接口调用发生异常: {e}")
        print(f"查询账单失败：{e}")
        return None

    if response.status_code != 200:
        logger.error(f"查询账单失败，状态码: {response.status_code}, 响应: {response.text}")
        print(f"查询账单失败，HTTP状态码 {response.status_code}")
        return None

    result = response.json()
    if result.get('code') != 0:
        msg = result.get('msg', '未知错误')
        logger.error(f"查询账单返回错误: code={result.get('code')}, msg={msg}")
        print(f"查询账单失败：{msg}")
        return None

    result_data = result.get('data', {})
    bill_list = []
    bill_id_list = []
    total_original_amount = 0

    # 解析账单列表，API 结构：data -> list[] (按日期分组) -> categoryData[] -> records[] (每个账单)
    date_list = result_data.get('list', [])
    for date_item in date_list:
        for category_data in date_item.get('categoryData', []):
            for record in category_data.get('records', []):
                # 如果有收费项目筛选，只保留匹配的
                if charge_item_id and str(record.get('chargeItemId')) != str(charge_item_id):
                    continue
                # 只保留未支付账单，字段是 state，0 表示未支付
                if record.get('state') != 0:
                    continue
                bill_info = {
                    'id': record.get('id'),
                    'version': record.get('version', 0),
                    'amount': record.get('billAmount', 0),  # 账单金额，单位分
                    'chargeItemId': record.get('chargeItemId'),
                    'chargeItemName': record.get('chargeItemName', '未知项目'),
                    'date': record.get('date', ''),
                    'showMonth': record.get('showMonth', ''),
                    'generateTime': record.get('generateTime', 0)
                }
                bill_list.append(bill_info)
                bill_id_list.append(int(record.get('id')))
                total_original_amount += record.get('billAmount', 0)

    if not bill_list:
        print(f"未找到任何未支付账单，请检查时间范围和收费项目")
        print(f"小区：{community_name}")
        print(f"房屋：{node_name}")
        print(f"时间范围：{datetime.fromtimestamp(start_time).strftime('%Y-%m-%d')} 至 {datetime.fromtimestamp(end_time).strftime('%Y-%m-%d')}")
        return None

    logger.info(f"查询到 {len(bill_list)} 个未支付账单，总金额 {total_original_amount / 100:.2f} 元")

    logger.info(f"未支付账单总金额: {total_original_amount / 100:.2f} 元")

    # 第二步：检查是否有正在支付中的订单
    print(f"\n正在检查账单支付状态...")
    check_payload = {
        "selectList": bill_id_list
    }
    check_url = f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/checkInPayBill"

    try:
        check_response = requests.post(
            check_url,
            json=check_payload,
            headers=headers,
            timeout=10
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"检查支付状态接口调用发生异常: {e}")
        print(f"检查支付状态失败：{e}")
        return None

    if check_response.status_code != 200:
        logger.error(f"检查支付状态失败，状态码: {check_response.status_code}, 响应: {check_response.text}")
        print(f"检查支付状态失败，HTTP状态码 {check_response.status_code}")
        return None

    check_result = check_response.json()
    if check_result.get('code') != 0:
        msg = check_result.get('msg', '未知错误')
        logger.error(f"检查支付状态返回错误: code={check_result.get('code')}, msg={msg}")
        print(f"检查支付状态失败：{msg}")
        return None

    check_data = check_result.get('data', {})
    has_in_pay = check_data.get('hasInPay', False)
    if has_in_pay:
        print(f"✗ 检测到有账单正在支付中，请完成支付后再进行优惠操作")
        logger.warning("存在支付中订单，终止优惠操作")
        return None

    logger.info("支付状态检查通过，没有正在支付中的订单")

    # 转换优惠金额为分
    discount_amount_fen = int(round(discount_amount_yuan * 100))

    # 保存到缓存等待用户确认
    cache_data = {
        'community_id': community_id,
        'community_name': community_name,
        'asset_id': asset_id,
        'asset_type': asset_type,
        'node_name': node_name,
        'start_time': start_time,
        'end_time': end_time,
        'charge_item_id': charge_item_id,
        'discount_amount_yuan': discount_amount_yuan,
        'discount_amount_fen': discount_amount_fen,
        'bill_list': bill_list,
        'total_original_amount': total_original_amount
    }
    save_discount_confirmation_cache(cache_data)

    # 输出给用户
    total_original_amount_yuan = total_original_amount / 100
    print(f"\n### 待优惠账单信息\n")
    print(f"**小区**: {community_name}")
    print(f"**房屋**: {node_name}")
    print(f"**时间范围**: {datetime.fromtimestamp(start_time).strftime('%Y-%m-%d')} 至 {datetime.fromtimestamp(end_time).strftime('%Y-%m-%d')}")
    print(f"**优惠总金额**: ¥ {discount_amount_yuan:.2f}")
    print(f"**待优惠账单数**: {len(bill_list)} 条")
    print(f"**账单总金额**: ¥ {total_original_amount_yuan:.2f}\n")
    print("账单列表:")
    for idx, bill in enumerate(bill_list, 1):
        amount_yuan = bill['amount'] / 100
        date_str = f"{bill['date']} " if bill['date'] else ""
        # 转换日期格式如 2026-03 -> 2026年03月
        try:
            y, m = date_str.strip().split('-')
            date_str = f"{y}年{m}月 "
        except:
            pass
        print(f"{idx}. {date_str}{bill['chargeItemName']} - ¥ {amount_yuan:.2f}")
    print()
    print("请确认是否进行优惠减免？")
    print("- 运行命令 `confirm_discount yes` 优惠全部账单")
    print("- 运行命令 `confirm_discount <序号>`（如`confirm_discount 1`或`confirm_discount 1,2`）只优惠指定账单")
    print("- 运行命令 `confirm_discount no` 取消")

    return cache_data


def discount_bills_by_name(charge_system_name=None, community_name=None, keyword=None,
                          start_date_str=None, end_date_str=None, charge_item_name=None, discount_amount_yuan=None):
    """
    通过名称对特定房屋指定时间范围的账单进行优惠减免（智能匹配模式）
    """
    # 1. 获取收费系统
    system_map = get_user_charge_systems(return_map=True)
    if not system_map:
        print("获取收费系统列表失败")
        return
    if charge_system_name not in system_map:
        print(f"未找到收费系统：{charge_system_name}")
        print("可用的收费系统：" + ", ".join(system_map.keys()))
        return
    charge_system_id = system_map[charge_system_name]
    print(f"找到收费系统：{charge_system_name}")

    # 2. 搜索小区
    community_map = search_community(charge_system_id, community_name, return_map=True)
    if not community_map:
        print(f"未找到匹配的小区：{community_name}")
        return
    if len(community_map) > 1:
        print(f"找到多个匹配的小区，请选择：")
        for name in community_map.keys():
            print(f"  - {name}")
        return
    # 只有一个匹配，直接使用
    community_name_found = list(community_map.keys())[0]
    community_id = community_map[community_name_found]
    print(f"找到小区：{community_name_found}")

    # 3. 解析日期范围，如果没有提供则默认当月
    today = datetime.now()
    if discount_amount_yuan is None:
        # 参数位置调整：当 start_date_str 是数字（优惠金额），说明没有提供日期范围，默认本月
        # 格式: discount_bills 系统 小区 房屋 优惠金额 或者 discount_bills 系统 小区 房屋 收费项目 优惠金额
        try:
            discount_amount_yuan = float(start_date_str)
            # 没有提供日期，使用本月
            start_time = datetime(today.year, today.month, 1)
            end_time = today
            start_date_str = None
            end_date_str = None
            logger.info(f"未提供日期范围，使用本月: {start_time.strftime('%Y-%m-%d')} 至 {end_time.strftime('%Y-%m-%d')}")
        except ValueError:
            print(f"参数解析失败，请检查命令格式。示例：discount_bills 收费系统 小区 1栋/1单元/101 物业费 50")
            return
    elif charge_item_name is None and end_date_str is not None:
        # 格式: discount_bills 系统 小区 房屋 开始日期 结束日期 优惠金额，不指定收费项目
        try:
            discount_amount_yuan = float(end_date_str)
            charge_item_name = None
            logger.info(f"不指定收费项目，对所有未付账单优惠 {discount_amount_yuan} 元")
        except ValueError:
            print(f"优惠金额必须是数字，请检查：{end_date_str}")
            return
    elif charge_item_name is not None:
        # 格式: discount_bills 系统 小区 房屋 开始日期 结束日期 收费项目 优惠金额
        try:
            discount_amount_yuan = float(discount_amount_yuan)
        except ValueError:
            print(f"优惠金额必须是数字，请检查：{discount_amount_yuan}")
            return

    if 'start_time' not in locals():
        # 解析用户提供的日期范围
        if not start_date_str or not end_date_str:
            # 使用本月
            start_time = datetime(today.year, today.month, 1)
            end_time = today
        else:
            try:
                start_time = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_time = datetime.strptime(end_date_str, '%Y-%m-%d')
            except ValueError:
                print(f"日期格式错误，请使用 YYYY-MM-DD 格式，如 2026-03-01")
                return

    start_timestamp = int(start_time.timestamp())
    end_timestamp = int(end_time.timestamp()) + 86399  # 包含结束日期当天

    # 4. 匹配收费项目
    charge_item_id = None
    if charge_item_name:
        print(f"正在匹配收费项目：{charge_item_name}...")
        charge_item_id = get_charge_item_id_by_name(str(community_id), str(charge_system_id), charge_item_name)
        logger.info(f"收费项目筛选: {charge_item_name} → ID: {charge_item_id}")

    # 4.5 加载匹配缓存（处理用户选择多个匹配的场景）
    cache_data = load_match_cache()
    selected_node = None

    # 检查缓存中是否有可用的匹配结果（用户选择场景）
    if cache_data and str(cache_data.get('community_id')) == str(community_id):
        cached_nodes = cache_data.get('nodes', [])
        if cached_nodes:
            # 尝试解析用户选择
            selected_node = parse_user_selection(keyword, cached_nodes)
            if selected_node:
                logger.info(f"用户选择了: {selected_node.get('full_name')}")
                # 清除缓存
                clear_match_cache()
                # 检查是否是房屋级别
                if selected_node['level'] != 'house':
                    print(f"请选择具体的房屋进行优惠，当前选择的是{selected_node['full_name']}（{selected_node['level']}）")
                    return
                # 继续处理
                node_id = str(selected_node['id'])
                node_name = selected_node['full_name']
                asset_type = 1  # 房屋固定为1

                logger.info(f"已选择房屋: {node_name}, ID: {node_id}")

                # 查询账单
                discount_house_bills(str(community_id), node_id, asset_type, node_name, community_name_found, start_timestamp, end_timestamp, charge_item_id, discount_amount_yuan)
                return
            else:
                # 解析失败，清除缓存，按新关键词重新搜索
                logger.info("无法解析用户选择，清除缓存并重新搜索")
                clear_match_cache()

    # 5. 搜索房屋
    # 清理关键词
    clean_keyword = keyword.replace("优惠", "").replace("减免", "").replace("账单", "").replace("的", "").strip()

    # 检查是否使用精确匹配（包含 / 分隔符）
    use_exact_match = "/" in clean_keyword

    # 获取完整房屋结构
    household_data = search_household_structure(str(community_id), "")
    if household_data is None:
        print("搜索房屋结构失败")
        return

    # 找出匹配的节点
    if use_exact_match:
        matching_nodes = find_matching_nodes(household_data, clean_keyword, exact_match=True)
        if not matching_nodes:
            logger.info("精确匹配未找到结果，使用模糊匹配")
            keywords = clean_keyword.split("/")
            search_kw = keywords[-1] if keywords else clean_keyword
            household_data_for_search = search_household_structure(str(community_id), search_kw)
            matching_nodes = find_matching_nodes(household_data_for_search, clean_keyword, exact_match=False, relaxed_match=True)
    else:
        # 模糊匹配
        matching_nodes = find_matching_nodes(household_data, clean_keyword, exact_match=False, relaxed_match=True)

    if not matching_nodes:
        # 宽松匹配也没找到，尝试宽松匹配整个关键词
        matching_nodes = find_matching_nodes(household_data, clean_keyword, exact_match=False, relaxed_match=True)
        if not matching_nodes:
            print("未找到任何匹配的房屋，请检查关键词重试")
            return

    if len(matching_nodes) == 1:
        # 只有一个匹配，直接使用
        selected_node = matching_nodes[0]
        if selected_node['level'] != 'house':
            print(f"匹配结果不是房屋，当前匹配到的是 {selected_node['level']}：{selected_node['full_name']}")
            print("请提供更精确的关键词匹配到具体房屋")
            return

        clear_match_cache()
        node_id = str(selected_node['id'])
        node_name = selected_node['full_name']
        asset_type = 1  # 房屋固定为1
        logger.info(f"已选择房屋: {node_name}, ID: {node_id}")

        # 查询账单
        discount_house_bills(str(community_id), node_id, asset_type, node_name, community_name_found, start_timestamp, end_timestamp, charge_item_id, discount_amount_yuan)
    else:
        # 多个匹配，保存到缓存让用户选择
        save_match_cache(community_id, matching_nodes)
        print(f"找到多个匹配，请选择：")
        for idx, node in enumerate(matching_nodes, 1):
            print(f"{idx}. {node['full_name']} ({node['level']})")
        return


def confirm_discount(confirmation_input: str):
    """
    处理用户确认，执行优惠减免
    """
    # 加载缓存
    cache_data = load_discount_confirmation_cache()
    if not cache_data:
        print("没有待确认的优惠，请先运行 discount_bills 查询账单")
        return

    if confirmation_input.lower() == 'no':
        print("已取消优惠")
        clear_discount_confirmation_cache()
        return

    community_id = cache_data['community_id']
    community_name = cache_data['community_name']
    node_name = cache_data['node_name']
    discount_amount_yuan = cache_data['discount_amount_yuan']
    discount_amount_fen = cache_data['discount_amount_fen']
    all_bills = cache_data['bill_list']

    # 解析用户选择
    selected_bills = []
    if confirmation_input.lower() == 'yes':
        # 全部选择
        selected_bills = all_bills
    else:
        # 按序号选择，支持逗号分隔，如 1,2
        try:
            # 拆分序号
            index_strs = confirmation_input.replace('，', ',').split(',')
            selected_indices = [int(s.strip()) - 1 for s in index_strs if s.strip()]
            for idx in selected_indices:
                if 0 <= idx < len(all_bills):
                    selected_bills.append(all_bills[idx])
        except ValueError:
            print(f"输入格式错误，请输入 yes/no 或以逗号分隔的序号，如：1,2")
            return

    if not selected_bills:
        print(f"未选择任何账单，已取消")
        clear_discount_confirmation_cache()
        return

    logger.info(f"用户选择了 {len(selected_bills)} 个账单进行优惠")

    # 准备调用接口
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None

    headers = get_headers_with_cookies(ck_dict, {"communityid": str(community_id)})

    # 收集账单ID列表
    bill_id_list = [int(bill['id']) for bill in selected_bills]

    # 构建请求
    payload = {
        "communityID": int(community_id),
        "billIdList": bill_id_list,
        "discountType": 1,  # 1 = 金额减免
        "discountRate": 0,  # 金额减免固定为0
        "amount": discount_amount_fen,  # 优惠金额，单位分
        "amountType": 1  # 1 = 按金额减免
    }

    url = f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/modDiscountOrLateMoney"

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=30
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"优惠接口调用发生异常: {e}")
        print(f"优惠失败：{e}")
        return

    if response.status_code != 200:
        logger.error(f"优惠失败，状态码: {response.status_code}, 响应: {response.text}")
        print(f"优惠失败，HTTP状态码 {response.status_code}")
        return

    result = response.json()
    if result.get('code') != 0:
        msg = result.get('msg', '未知错误')
        logger.error(f"优惠返回错误: code={result.get('code')}, msg={msg}")
        print(f"优惠失败：{msg}")
        clear_discount_confirmation_cache()
        return

    # 获取异步 keyCode 进行轮询
    key_code = result.get('data', {}).get('keyCode')
    if not key_code:
        logger.error(f"未获取到异步任务 keyCode，响应: {result}")
        print(f"优惠失败：未获取到异步任务标识")
        clear_discount_confirmation_cache()
        return

    logger.info(f"优惠任务已提交，keyCode: {key_code}，开始轮询结果...")
    print(f"\n优惠任务已提交，正在处理，请等待结果...\n")

    # 轮询异步结果
    max_retries = 10
    retry_interval = 2
    success = False
    final_result = None

    for i in range(max_retries):
        try:
            import random
            random_num = random.random()
            poll_url = f"{CHARGE_API_BASE_URL}/api/v1/GetAsyncResult?keyCode={key_code}&r={random_num}"
            poll_response = requests.get(poll_url, headers=headers, timeout=10)
            if poll_response.status_code == 200:
                poll_result = poll_response.json()
                if poll_result.get('code') == 0:
                    # 解析 data 里面还有一层 code
                    data_str = poll_result.get('data', '{}')
                    try:
                        if isinstance(data_str, str):
                            data_result = json.loads(data_str)
                        else:
                            data_result = data_str
                        # 只要能解析出结果，不管成功失败都停止轮询
                        # 外层 code=0 表示已经拿到最终结果
                        success = (data_result.get('code') == 0)
                        final_result = data_result
                        break
                    except json.JSONDecodeError:
                        logger.info(f"轮询 {i+1}/{max_retries}，结果解析错误，继续等待...")
                else:
                    logger.info(f"轮询 {i+1}/{max_retries}，code={poll_result.get('code')}，继续等待...")
            time.sleep(retry_interval)
        except Exception as e:
            logger.warning(f"轮询异常 {i+1}/{max_retries}: {e}")
            time.sleep(retry_interval)

    if final_result is None:
        # 真的超时，没拿到结果
        print(f"✗ 优惠处理超时，请稍后查询结果")
        logger.error(f"优惠轮询超时，keyCode: {key_code}")
        clear_discount_confirmation_cache()
        return
    if not success:
        # 拿到了结果，但业务失败
        msg = final_result.get('msg', '未知错误')
        print(f"✗ 优惠处理失败：{msg}")
        logger.error(f"优惠业务失败: code={final_result.get('code')}, msg={msg}")
        clear_discount_confirmation_cache()
        return

    logger.info(f"优惠处理成功: {final_result}")

    # 输出成功结果
    process_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print(f"\n✓ 优惠减免成功！\n")
    print(f"**小区**: {community_name}")
    print(f"**房屋**: {node_name}")
    print(f"**优惠账单数**: {len(selected_bills)} 条")
    print(f"**优惠总金额**: ¥ {discount_amount_yuan:.2f}")
    print(f"**处理时间**: {process_time_str}\n")

    print("优惠账单明细：")
    for idx, bill in enumerate(selected_bills, 1):
        amount_yuan = bill['amount'] / 100
        date_display = bill['date']
        try:
            y, m = date_display.split('-')
            date_display = f"{y}年{m}月"
        except:
            pass
        print(f"{idx}. {date_display} {bill['chargeItemName']} - 原金额 ¥ {amount_yuan:.2f} - 优惠 ¥ {discount_amount_yuan / len(selected_bills):.2f}")

    # 清除缓存
    clear_discount_confirmation_cache()
    logger.info(f"优惠完成，成功 {len(selected_bills)} 个账单，总优惠 {discount_amount_yuan:.2f}")


def clear_late_money_house_bills(community_id: str, asset_id: str, asset_type: int, node_name: str,
                       community_name: str, start_time: int, end_time: int, charge_item_id: str = None, set_amount_yuan: float = 0.0):
    """
    查询特定房屋的账单并准备设置违约金（通常用于清零）

    Args:
        community_id: 小区ID
        asset_id: 资产ID（房屋ID）
        asset_type: 资产类型
        node_name: 节点名称（房屋位置）
        community_name: 小区名称
        start_time: 开始时间戳
        end_time: 结束时间戳
        charge_item_id: 收费项目ID，None表示不筛选
        set_amount_yuan: 要设置的违约金金额，单位元，默认0表示清零
    """
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None

    headers = get_headers_with_cookies(ck_dict, {"communityid": str(community_id)})

    # 构建查询参数
    payload = {
        "communityID": int(community_id),
        "assetType": asset_type,
        "assetId": int(asset_id),
        "payStatus": 0,  # 只查询未支付账单
        "index": "",
        "selectChargeItemList": [int(charge_item_id)] if charge_item_id else [],
        "selectChargeItemAll": charge_item_id is None,
        "generateStartTime": start_time,
        "generateEndTime": end_time,
        "dealLogId": 0,
        "categoryId": 0,
        "sortType": 1,
        "chargeItemVersion": 2,
        "chargeItemCategorys": []
    }

    url = f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/getCashierDeskListByIndex"

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=30
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"查询账单接口调用发生异常: {e}")
        print(f"查询账单失败：{e}")
        return None

    if response.status_code != 200:
        logger.error(f"查询账单失败，状态码: {response.status_code}, 响应: {response.text}")
        print(f"查询账单失败，HTTP状态码 {response.status_code}")
        return None

    result = response.json()
    if result.get('code') != 0:
        msg = result.get('msg', '未知错误')
        logger.error(f"查询账单返回错误: code={result.get('code')}, msg={msg}")
        print(f"查询账单失败：{msg}")
        return None

    result_data = result.get('data', {})
    pending_bills = []
    total_original_late = 0.0

    # 解析账单列表，API 结构：data -> list[] (按日期分组)
    # date 分组下可能有：
    # 1. categoryData[] -> records[] (每个账单)
    # 2. 直接在 date 分组下有 records[] (每个账单)
    # 两种情况都要遍历，确保不遗漏
    date_list = result_data.get('list', [])
    for date_item in date_list:
        # 遍历 categoryData 中的 records
        for category_data in date_item.get('categoryData', []):
            for record in category_data.get('records', []):
                # 如果有收费项目筛选，只保留匹配的
                if charge_item_id and str(record.get('chargeItemId')) != str(charge_item_id):
                    continue
                # 只保留未支付账单，字段是 state，0 表示未支付
                if record.get('state') != 0:
                    continue
                bill_info = {
                    'id': record.get('id'),
                    'version': record.get('version', 0),
                    'chargeItemName': record.get('chargeItemName', '未知收费项目'),
                    'amount': record.get('billAmount', 0),  # 账单本金，单位分
                    'lateMoney': record.get('lateMoneyAmount', 0),  # 当前违约金，单位分 - 字段名是 lateMoneyAmount
                    'generateTime': record.get('generateTime', 0),
                    'date': record.get('date', '未知月份')  # 格式就是 date 字段，YYYY-MM
                }
                pending_bills.append(bill_info)
                total_original_late += bill_info['lateMoney']
        # 遍历 date 分组直接下的 records
        for record in date_item.get('records', []):
            # 如果有收费项目筛选，只保留匹配的
            if charge_item_id and str(record.get('chargeItemId')) != str(charge_item_id):
                continue
            # 只保留未支付账单，字段是 state，0 表示未支付
            if record.get('state') != 0:
                continue
            bill_info = {
                'id': record.get('id'),
                'version': record.get('version', 0),
                'chargeItemName': record.get('chargeItemName', '未知收费项目'),
                'amount': record.get('billAmount', 0),  # 账单本金，单位分
                'lateMoney': record.get('lateMoneyAmount', 0),  # 当前违约金，单位分 - 字段名是 lateMoneyAmount
                'generateTime': record.get('generateTime', 0),
                'date': record.get('date', '未知月份')  # 格式就是 date 字段，YYYY-MM
            }
            pending_bills.append(bill_info)
            total_original_late += bill_info['lateMoney']

    if not pending_bills:
        print(f"未找到任何未支付账单，请检查时间范围和收费项目")
        print(f"小区：{community_name}")
        print(f"房屋：{node_name}")
        start_display = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d')
        end_display = datetime.fromtimestamp(end_time).strftime('%Y-%m-%d')
        print(f"时间范围：{start_display} 至 {end_display}")
        return None

    logger.info(f"查询到 {len(pending_bills)} 个未支付账单，原总违约金 {total_original_late / 100:.2f} 元")

    # 第二步：检查是否有正在支付中的订单
    print(f"\n正在检查账单支付状态...")
    bill_ids = [bill['id'] for bill in pending_bills]
    check_payload = {
        "selectList": bill_ids
    }
    check_url = f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/checkInPayBill"
    try:
        check_response = requests.post(
            check_url,
            json=check_payload,
            headers=headers,
            timeout=10
        )
        if check_response.status_code != 200:
            logger.error(f"检查支付中订单失败，状态码: {check_response.status_code}")
            print(f"✗ 检查支付中订单失败，请稍后重试")
            return None
        check_data = check_response.json()
        if check_data.get('code') != 0:
            logger.error(f"检查支付中订单返回错误: {check_data.get('msg')}")
            print(f"✗ 检查支付中订单失败: {check_data.get('msg')}")
            return None
        has_in_pay = check_data.get('data', {}).get('hasInPay', False)
        if has_in_pay:
            print(f"✗ 选中账单中有正在支付中的订单，请稍后再试")
            logger.warning(f"存在支付中订单，终止操作")
            return None
    except Exception as e:
        logger.error(f"检查支付中订单异常: {e}")
        print(f"✗ 检查支付中订单发生异常，请查看日志")
        return None

    # 转换开始结束时间为可读格式
    start_dt = datetime.fromtimestamp(start_time)
    end_dt = datetime.fromtimestamp(end_time)
    start_display = start_dt.strftime('%Y-%m-%d')
    end_display = end_dt.strftime('%Y-%m-%d')

    # 计算总金额
    total_original_late_yuan = total_original_late / 100

    # 保存待确认数据到缓存
    cache_data = {
        'community_id': community_id,
        'asset_id': asset_id,
        'asset_type': asset_type,
        'node_name': node_name,
        'community_name': community_name,
        'start_time': start_time,
        'end_time': end_time,
        'set_amount_yuan': set_amount_yuan,
        'pending_bills': pending_bills
    }
    save_late_money_confirmation_cache(cache_data)

    # 输出结果给用户确认
    print(f"\n### 待处理账单信息\n")
    print(f"**小区**: {community_name}")
    print(f"**房屋**: {node_name}")
    print(f"**时间范围**: {start_display} 至 {end_display}")
    print(f"**设置违约金金额**: ¥ {set_amount_yuan:.2f}")
    print(f"**待处理账单数**: {len(pending_bills)} 条")
    print(f"**原总违约金**: ¥ {total_original_late_yuan:.2f}\n")

    print("账单列表:")
    for idx, bill in enumerate(pending_bills, 1):
        principal_yuan = bill['amount'] / 100
        late_yuan = bill['lateMoney'] / 100
        date_display = bill['date']
        try:
            y, m = date_display.split('-')
            date_display = f"{y}年{m}月"
        except:
            pass
        print(f"{idx}. {date_display} {bill['chargeItemName']} - 本金 ¥ {principal_yuan:.2f}, 当前违约金 ¥ {late_yuan:.2f}")

    print(f"\n请确认是否进行操作？")
    if set_amount_yuan == 0:
        print(f"- 运行命令 `confirm_clear_late_money yes` 将所有账单违约金清零")
    else:
        print(f"- 运行命令 `confirm_clear_late_money yes` 将所有账单违约金设置为 ¥ {set_amount_yuan:.2f}（总金额）")
    print(f"- 运行命令 `confirm_clear_late_money <序号>`（如`confirm_clear_late_money 1`或`confirm_clear_late_money 1,2`）只处理指定账单")
    print(f"- 运行命令 `confirm_clear_late_money no` 取消")

    logger.info(f"已保存待确认数据，等待用户确认，待处理账单数: {len(pending_bills)}")
    return cache_data


def clear_late_money_by_name(charge_system_name: str, community_name: str, keyword: str,
                      start_date_str: str = None, end_date_str: str = None,
                      charge_item_name: str = None, set_amount_yuan: float = 0.0):
    """
    通过名称智能匹配房屋并查询待处理账单（两步完成，准备设置违约金）

    Args:
        charge_system_name: 收费系统名称
        community_name: 小区名称
        keyword: 房屋位置关键词
        start_date_str: 开始日期字符串（YYYY-MM-DD），None表示默认当月1日
        end_date_str: 结束日期字符串（YYYY-MM-DD），None表示默认今天
        charge_item_name: 收费项目名称，None表示不筛选
        set_amount_yuan: 要设置的违约金金额，默认0表示清零
    """
    # 检查必要参数
    if not charge_system_name:
        print("NEED_INFO: 请提供收费系统名称")
        print("提示：可以先使用 list_charge_systems 命令查看可用的收费系统")
        return
    if not community_name:
        print("NEED_INFO: 请提供小区名称")
        return
    if not keyword:
        print("NEED_INFO: 请提供房屋位置关键词（如楼栋/单元/房屋号）")
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
    if len(community_map) > 1:
        # 多个匹配，列出供用户选择
        print(f"找到多个匹配的小区，请使用完整的小区名称重新查询：")
        for name in community_map.keys():
            print(f"  - {name}")
        return

    # 只有一个匹配，继续处理
    comm_name, comm_id = next(iter(community_map.items()))
    print(f"找到小区：{comm_name}")

    # 处理默认日期 - 如果没有提供，默认为全部时间段（从2000-01-01到今天）
    # 这样包含所有历史账单，适合违约金清零操作
    if not start_date_str or not end_date_str:
        today = datetime.now()
        if not start_date_str:
            # 默认从 2000-01-01 开始，包含所有历史账单
            start_dt = datetime(2000, 1, 1)
            start_date_str = start_dt.strftime('%Y-%m-%d')
        if not end_date_str:
            # 到今天结束
            end_date_str = today.strftime('%Y-%m-%d')

    # 解析日期为时间戳
    try:
        start_dt = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date_str, '%Y-%m-%d')
        # 结束时间设为当天最后一秒
        end_dt = end_dt.replace(hour=23, minute=59, second=59)
        start_time = int(start_dt.timestamp())
        end_time = int(end_dt.timestamp())
    except ValueError:
        print(f"日期解析失败，请检查日期格式是否正确，正确格式: YYYY-MM-DD")
        return

    # 先尝试从缓存加载上一次的匹配列表
    cache_data = load_match_cache()
    if cache_data and str(cache_data.get('community_id')) == str(comm_id):
        cached_nodes = cache_data.get('nodes', [])
        if cached_nodes:
            # 尝试解析用户选择
            selected_node = parse_user_selection(keyword, cached_nodes)
            if selected_node:
                logger.info(f"用户选择了: {selected_node.get('name')}")
                # 清除缓存
                clear_match_cache()
                # 检查是否是房屋级别
                if selected_node['level'] != 'house':
                    print(f"请选择具体的房屋，当前选择的是{selected_node['name']}（{selected_node['level']}）")
                    return
                # 继续处理 - 匹配收费项目
                if charge_item_name:
                    charge_item_id = match_charge_item(charge_system_id, comm_id, charge_item_name)
                    if charge_item_id is None:
                        # 匹配失败已经输出了信息
                        return
                else:
                    charge_item_id = None
                # 查询账单
                clear_late_money_house_bills(
                    community_id=str(comm_id),
                    asset_id=str(selected_node['id']),
                    asset_type=1,
                    node_name=selected_node['name'],
                    community_name=comm_name,
                    start_time=start_time,
                    end_time=end_time,
                    charge_item_id=charge_item_id,
                    set_amount_yuan=set_amount_yuan
                )
                return
            else:
                # 解析失败，清除缓存，按新关键词重新搜索
                logger.info("无法解析用户选择，清除缓存并重新搜索")
                clear_match_cache()

    # 清理关键词
    clean_keyword = keyword.replace("违约金", "").replace("清零", "").replace("设置", "").replace("的", "").strip()

    # 检查是否使用精确匹配
    use_exact_match = "/" in clean_keyword

    # 获取完整房屋结构
    household_data = search_household_structure(str(comm_id), "")
    if household_data is None:
        print("搜索房屋结构失败")
        return

    # 找出匹配的节点
    if use_exact_match:
        matching_nodes = find_matching_nodes(household_data, clean_keyword, exact_match=True)
        if not matching_nodes:
            logger.info("精确匹配未找到结果，使用模糊匹配")
            keywords = clean_keyword.split("/")
            search_kw = keywords[-1] if keywords else clean_keyword
            household_data_for_search = search_household_structure(str(comm_id), search_kw)
            if household_data_for_search:
                household_data = household_data_for_search
            matching_nodes = find_matching_nodes(household_data, clean_keyword)
    else:
        keywords = split_keywords(clean_keyword)
        search_kw = keywords[-1] if keywords else clean_keyword
        household_data_for_search = search_household_structure(str(comm_id), search_kw)
        if household_data_for_search:
            household_data = household_data_for_search
        matching_nodes = find_matching_nodes(household_data, clean_keyword)

    if not matching_nodes:
        # 尝试宽松匹配
        logger.info(f"严格匹配未找到，尝试宽松匹配: {clean_keyword}")
        matching_nodes = find_matching_nodes(household_data, clean_keyword, relaxed_match=True)
    if not matching_nodes:
        # 仍然没找到，生成候选列表
        logger.info(f"宽松匹配也未找到，生成候选列表")
        candidates = generate_candidates(household_data, clean_keyword)
        if candidates:
            print_candidates(clean_keyword, candidates)
        else:
            print(f"未找到与'{clean_keyword}'匹配的楼栋/单元/房屋，请确认输入是否正确")
        return

    if len(matching_nodes) == 1:
        node = matching_nodes[0]
        if node['level'] != 'house':
            print(f"请选择具体的房屋，当前选择的是{node['name']}（{node['level']}）")
            return
        # 匹配收费项目
        if charge_item_name:
            charge_item_id = match_charge_item(charge_system_id, comm_id, charge_item_name)
            if charge_item_id is None:
                # 匹配失败已经输出了信息
                return
        else:
            charge_item_id = None
        # 查询账单
        clear_late_money_house_bills(
            community_id=str(comm_id),
            asset_id=str(node['id']),
            asset_type=1,
            node_name=node['name'],
            community_name=comm_name,
            start_time=start_time,
            end_time=end_time,
            charge_item_id=charge_item_id,
            set_amount_yuan=set_amount_yuan
        )
        return
    else:
        save_match_cache(comm_id, matching_nodes)
        print("MULTI_MATCH:")
        for idx, node in enumerate(matching_nodes, 1):
            level_label = {
                'building': '楼栋',
                'unit': '单元',
                'house': '房屋'
            }.get(node['level'], '未知')
            print(f"{idx}. {node['name']} ({level_label})")
        return


def confirm_clear_late_money(confirmation_input: str):
    """
    确认设置违约金，处理用户选择

    Args:
        confirmation_input: 用户选择的字符串，yes/no/序号
    """
    from datetime import datetime
    # 从缓存加载待确认数据
    pending_data = load_late_money_confirmation_cache()
    if not pending_data:
        print("没有待确认的设置数据，或数据已过期，请重新开始流程")
        print("请先运行：python3 main.py clear_late_money <收费系统名称> <小区名称> <房屋关键词> [开始日期] [结束日期] [收费项目] [金额]")
        return

    # 获取基本信息
    community_id = pending_data['community_id']
    asset_id = pending_data['asset_id']
    community_name = pending_data['community_name']
    node_name = pending_data['node_name']
    set_amount_yuan = pending_data['set_amount_yuan']
    pending_bills = pending_data['pending_bills']

    # 解析用户选择
    if confirmation_input.lower() == 'no' or confirmation_input.lower() == 'n':
        print("操作已取消")
        clear_late_money_confirmation_cache()
        return

    selected_bills = []
    if confirmation_input.lower() == 'yes':
        # 全部选择
        selected_bills = pending_bills
    else:
        # 按序号选择，支持逗号分隔，如 1,2
        try:
            # 拆分序号
            index_strs = confirmation_input.replace('，', ',').split(',')
            selected_indices = [int(s.strip()) - 1 for s in index_strs if s.strip()]
            for idx in selected_indices:
                if 0 <= idx < len(pending_bills):
                    selected_bills.append(pending_bills[idx])
        except ValueError:
            print(f"输入格式错误，请输入 yes/no 或以逗号分隔的序号，如：1,2")
            return

    if not selected_bills:
        print(f"未选择任何账单，已取消")
        clear_late_money_confirmation_cache()
        return

    # 提取选中的账单ID
    bill_id_list = [bill['id'] for bill in selected_bills]
    set_amount_fen = int(round(set_amount_yuan * 100))

    # 调用API执行设置违约金
    ck_dict = ensure_authenticated()
    if not ck_dict:
        clear_late_money_confirmation_cache()
        return

    headers = get_headers_with_cookies(ck_dict, {"communityid": str(community_id)})

    # 构建请求负载
    payload = {
        "communityID": int(community_id),
        "billIdList": bill_id_list,
        "amount": set_amount_fen,
        "amountType": 2
    }

    logger.info(f"开始执行设置违约金，社区ID={community_id}, 账单数={len(bill_id_list)}, 设置金额={set_amount_yuan}元")

    try:
        response = requests.post(
            f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/asyncModDiscountOrLateMoney",
            json=payload,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"设置违约金失败，状态码: {response.status_code}, 响应内容: {response.text}")
            print(f"✗ 设置违约金失败，状态码: {response.status_code}")
            clear_late_money_confirmation_cache()
            return

        response.raise_for_status()
        data = response.json()

        if data.get('code') != 0:
            logger.error(f"设置违约金失败: {data.get('msg')}")
            print(f"✗ 设置违约金失败: {data.get('msg')}")
            clear_late_money_confirmation_cache()
            return

        # 获取 keyCode 进行轮询
        key_code = data.get('data', {}).get('keyCode')
        if not key_code:
            logger.error(f"未获取到 keyCode，返回数据: {data}")
            print(f"✗ 设置违约金失败：未获取到任务ID")
            clear_late_money_confirmation_cache()
            return

        # 异步轮询获取结果
        print(f"正在处理，请等待结果...")
        max_retries = 10
        retry_interval = 2
        success = False
        final_result = None

        for i in range(max_retries):
            try:
                import random
                random_num = random.random()
                poll_url = f"{CHARGE_API_BASE_URL}/api/v1/GetAsyncResult?keyCode={key_code}&r={random_num}"
                poll_response = requests.get(poll_url, headers=headers, timeout=10)
                if poll_response.status_code == 200:
                    poll_result = poll_response.json()
                    if poll_result.get('code') == 0:
                        # 解析 data 里面还有一层 code
                        data_str = poll_result.get('data', '{}')
                        try:
                            if isinstance(data_str, str):
                                data_result = json.loads(data_str)
                            else:
                                data_result = data_str
                            # 只要能解析出结果，不管成功失败都停止轮询
                            # 外层 code=0 表示已经拿到最终结果
                            code = data_result.get('code')
                            msg = data_result.get('msg', '').lower()
                            # 如果 msg 是 success，不管 code 是什么都认为成功
                            success = (code == 0) or (msg == 'success')
                            final_result = data_result
                            break
                        except json.JSONDecodeError:
                            logger.info(f"轮询 {i+1}/{max_retries}，结果解析错误，继续等待...")
                    else:
                        logger.info(f"轮询 {i+1}/{max_retries}，code={poll_result.get('code')}，继续等待...")
                time.sleep(retry_interval)
            except Exception as e:
                logger.warning(f"轮询异常 {i+1}/{max_retries}: {e}")
                time.sleep(retry_interval)

        if final_result is None:
            # 真的超时，没拿到结果
            print(f"✗ 处理超时，请稍后查询结果")
            logger.error(f"设置违约金轮询超时，keyCode: {key_code}")
            clear_late_money_confirmation_cache()
            return
        if not success:
            # 拿到了结果，但业务失败
            msg = final_result.get('msg', '未知错误')
            print(f"✗ 处理失败：{msg}")
            logger.error(f"设置违约金业务失败: code={final_result.get('code')}, msg={msg}")
            clear_late_money_confirmation_cache()
            return

        logger.info(f"设置违约金成功: {final_result}")

        # 输出成功结果
        process_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        print(f"\n✓ 设置违约金成功！\n")
        print(f"**小区**: {community_name}")
        print(f"**房屋**: {node_name}")
        print(f"**处理账单数**: {len(selected_bills)} 条")
        print(f"**设置金额**: ¥ {set_amount_yuan:.2f}")
        print(f"**处理时间**: {process_time_str}\n")

        print("处理账单明细：")
        for idx, bill in enumerate(selected_bills, 1):
            principal_yuan = bill['amount'] / 100
            original_late_yuan = bill['lateMoney'] / 100
            date_display = bill['date']
            try:
                y, m = date_display.split('-')
                date_display = f"{y}年{m}月"
            except:
                pass
            if set_amount_yuan == 0:
                print(f"{idx}. {date_display} {bill['chargeItemName']} - 本金 ¥ {principal_yuan:.2f}, 原违约金 ¥ {original_late_yuan:.2f} → 已清零")
            else:
                print(f"{idx}. {date_display} {bill['chargeItemName']} - 本金 ¥ {principal_yuan:.2f}, 原违约金 ¥ {original_late_yuan:.2f} → 已设置为 ¥ {set_amount_yuan / len(selected_bills):.2f}")

        # 清除缓存
        clear_late_money_confirmation_cache()
        logger.info(f"设置违约金完成，成功 {len(selected_bills)} 个账单，设置金额 {set_amount_yuan:.2f}")

    except requests.exceptions.RequestException as e:
        logger.error(f"设置违约金发生异常: {e}")
        print(f"✗ 设置违约金发生异常，请查看日志")
        clear_late_money_confirmation_cache()
        return None


# === 收取押金确认缓存相关函数 ===
def get_cash_pledge_confirmation_cache_path() -> str:
    """获取收取押金确认缓存文件路径"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, '.cash_pledge_confirmation_cache.json')


def save_cash_pledge_confirmation_cache(cache_data: dict) -> None:
    """保存收取押金确认数据到缓存"""
    cache_data_with_ts = {
        "timestamp": time.time(),
        **cache_data
    }
    try:
        with open(get_cash_pledge_confirmation_cache_path(), 'w', encoding='utf-8') as f:
            json.dump(cache_data_with_ts, f, ensure_ascii=False, indent=2)
        logger.info(f"已保存收取押金确认数据")
    except Exception as e:
        logger.warning(f"保存收取押金确认缓存失败: {e}")


def load_cash_pledge_confirmation_cache() -> Optional[dict]:
    """从缓存加载收取押金确认数据（5分钟内有效）

    Returns:
        dict: 确认数据或 None
    """
    cache_path = get_cash_pledge_confirmation_cache_path()
    if not os.path.exists(cache_path):
        return None

    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)

        # 检查是否过期（5分钟）
        if time.time() - cache_data.get('timestamp', 0) > 300:
            logger.info("收取押金确认缓存已过期")
            clear_cash_pledge_confirmation_cache()
            return None

        logger.info(f"从缓存加载了收取押金确认数据")
        return cache_data
    except Exception as e:
        logger.warning(f"加载收取押金确认缓存失败: {e}")
        return None


def clear_cash_pledge_confirmation_cache() -> None:
    """清除收取押金确认缓存"""
    cache_path = get_cash_pledge_confirmation_cache_path()
    if os.path.exists(cache_path):
        try:
            os.remove(cache_path)
            logger.info("已清除收取押金确认缓存")
        except Exception as e:
            logger.warning(f"清除收取押金确认缓存失败: {e}")


def query_cash_pledge_items(community_id: str) -> Optional[list[dict]]:
    """查询小区已有押金项目列表

    Args:
        community_id: 小区ID

    Returns:
        list[dict]: 押金项目列表，None 表示查询失败
    """
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None

    headers = get_headers_with_cookies(ck_dict, {"communityid": str(community_id)})
    payload = {
        "cashPledgeName": "",
        "page": 1,
        "size": 100,
        "communityId": int(community_id)
    }

    try:
        response = requests.post(
            f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/queryCashPledgeItem",
            json=payload,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"查询押金项目失败，状态码: {response.status_code}, 响应内容: {response.text}")
            return None

        response.raise_for_status()
        data = response.json()

        if data.get('code') != 0:
            logger.error(f"查询押金项目失败: {data.get('msg')}")
            return None

        # Get the correct list from response
        data_obj = data.get('data', {})
        items = data_obj.get('cashPledgeItemList', [])
        logger.info(f"查询到小区 {community_id} 共有 {len(items)} 个押金项目")
        return items
    except requests.exceptions.RequestException as e:
        logger.error(f"查询押金项目发生异常: {e}")
        return None


def match_cash_pledge_item(community_id: str, input_name: str) -> Optional[dict]:
    """智能匹配押金项目

    Matching rules:
    1. Exact match first (name exactly equals input)
    2. Fuzzy match (input name is contained in item name)
    3. Multiple matches: score by length preference (shorter better match)
    4. No match: return None

    Args:
        community_id: 小区ID
        input_name: 用户输入的押金名称

    Returns:
        dict: matched item, None if no match
    """
    items = query_cash_pledge_items(community_id)
    if items is None:
        return None
    if not items:
        return None

    input_lower = input_name.lower()

    # 1. 精确匹配
    exact_matches = [item for item in items if item.get('cashPledgeName', '').lower() == input_lower]
    if len(exact_matches) == 1:
        logger.info(f"找到精确匹配押金项目: {exact_matches[0]}")
        return exact_matches[0]

    # 2. 模糊匹配（包含关键词）
    fuzzy_matches = [item for item in items if input_lower in item.get('cashPledgeName', '').lower()]
    if not fuzzy_matches:
        logger.info(f"未找到匹配的押金项目: {input_name}")
        return None

    # 3. 多个模糊匹配，按名称长度排序（越短越好，因为包含关键词更精准）
    fuzzy_matches.sort(key=lambda x: len(x.get('cashPledgeName', '')))
    best_match = fuzzy_matches[0]
    logger.info(f"模糊匹配找到最佳押金项目: {best_match}, 共 {len(fuzzy_matches)} 个候选")
    return best_match


def create_cash_pledge_item(community_id: str, pledge_name: str, amount_fen: int) -> Optional[str]:
    """创建新的押金项目

    Args:
        community_id: 小区ID
        pledge_name: 押金项目名称
        amount_fen: 默认金额（单位：分）

    Returns:
        str: 新创建的押金项目ID，None 表示创建失败
    """
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None

    headers = get_headers_with_cookies(ck_dict, {"communityid": str(community_id)})
    payload = {
        "cashPledgeName": pledge_name,
        "amount": amount_fen,
        "communityId": int(community_id)
    }

    try:
        response = requests.post(
            f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/addCashPledgeItem",
            json=payload,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"创建押金项目失败，状态码: {response.status_code}, 响应内容: {response.text}")
            return None

        response.raise_for_status()
        data = response.json()

        if data.get('code') != 0:
            logger.error(f"创建押金项目失败: {data.get('msg')}")
            print(f"✗ 创建押金项目失败: {data.get('msg')}")
            return None

        data_obj = data.get('data')
        if data_obj is None:
            # 根据用户提供的API示例，成功时data可能为null但code=0表示成功
            # 需要重新查询获取ID
            logger.info(f"创建押金项目成功，重新查询获取ID: {pledge_name}")
            # 重新查询找到新项目
            items = query_cash_pledge_items(community_id)
            if items is None:
                return None
            matched = match_cash_pledge_item(community_id, pledge_name)
            if matched is None:
                logger.error(f"创建成功但未找到新项目: {pledge_name}")
                print(f"✗ 创建押金项目成功但无法获取ID，请重试")
                return None
            pledge_id = str(matched.get('id'))
        else:
            pledge_id = str(data_obj.get('id', ''))

        logger.info(f"创建押金项目成功: {pledge_name}, ID={pledge_id}")
        return pledge_id
    except requests.exceptions.RequestException as e:
        logger.error(f"创建押金项目发生异常: {e}")
        print(f"✗ 创建押金项目发生异常，请查看日志")
        return None


def add_cash_pledge_order(community_id: str, asset_id: str, asset_type: int, pledge_item_id: str,
                          amount_fen: int, pay_type: int) -> Optional[dict]:
    """调用API收取押金

    Args:
        community_id: 小区ID
        asset_id: 房屋资产ID
        asset_type: 资产类型（1=房屋）
        pledge_item_id: 押金项目ID
        amount_fen: 押金金额（单位：分）
        pay_type: 支付方式编码

    Returns:
        dict: 响应数据，None 表示收取失败
    """
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None

    headers = get_headers_with_cookies(ck_dict, {"communityid": str(community_id)})
    payload = {
        "cashPledgeId": int(pledge_item_id),
        "communityId": int(community_id),
        "houseId": int(asset_id),
        "payTime": int(time.time() * 1000),
        "payType": pay_type,
        "payer": 0,
        "amount": amount_fen
    }

    try:
        response = requests.post(
            f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/addCashPledgeOrder",
            json=payload,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"收取押金失败，状态码: {response.status_code}, 响应内容: {response.text}")
            return None

        response.raise_for_status()
        data = response.json()

        if data.get('code') != 0:
            logger.error(f"收取押金失败: {data.get('msg')}")
            return data.get('msg'), None

        logger.info(f"收取押金成功: 小区={community_id}, 房屋={asset_id}, 押金项目={pledge_item_id}, 金额={amount_fen/100:.2f}")
        return data.get('data', {})
    except requests.exceptions.RequestException as e:
        logger.error(f"收取押金发生异常: {e}")
        return None


def collect_cash_pledge_by_name(charge_system_name: str, community_name: str, node_keyword: str,
                                pledge_name: str, amount_yuan: float, pay_type_name: str = None) -> None:
    """第一步：智能匹配收费系统、小区、房屋、押金项目，准备收取押金

    Two-step process:
    1. This step: do all matching, save to cache, show confirmation to user
    2. User confirms: call confirm_collect_cash_pledge() to execute

    Args:
        charge_system_name: 收费系统名称
        community_name: 小区名称
        node_keyword: 房屋关键词
        pledge_name: 押金名称
        amount_yuan: 押金金额（元）
        pay_type_name: 支付方式名称（可选，默认现金）
    """
    # 检查必要参数
    if not charge_system_name:
        print("NEED_INFO: 请提供收费系统名称")
        print("提示：可以先使用 list_charge_systems 命令查看可用的收费系统")
        return
    if not community_name:
        print("NEED_INFO: 请提供小区名称")
        return
    if not node_keyword:
        print("NEED_INFO: 请提供房屋位置关键词（如楼栋/单元/房屋号）")
        return
    if not pledge_name:
        print("NEED_INFO: 请提供押金名称（如装修押金、水电押金）")
        return
    if amount_yuan <= 0:
        print("错误：押金金额必须大于0")
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
    print(f"找到收费系统：{charge_system_name}")

    # 搜索小区
    community_map = search_community(charge_system_id, community_name, return_map=True)
    if community_map is None:
        print("搜索小区失败")
        return
    if not community_map:
        print(f"未找到匹配的小区：{community_name}")
        return
    if len(community_map) > 1:
        # 多个匹配，列出供用户选择
        print(f"找到多个匹配的小区，请使用完整的小区名称重新查询：")
        for name in community_map.keys():
            print(f"  - {name}")
        return

    # 只有一个匹配，继续处理
    comm_name, comm_id = next(iter(community_map.items()))
    community_id = str(comm_id)
    print(f"找到小区：{comm_name}")

    # 先尝试从缓存加载上一次的匹配列表
    cache_data = load_match_cache()
    if cache_data and str(cache_data.get('community_id')) == str(community_id):
        cached_nodes = cache_data.get('nodes', [])
        if cached_nodes:
            # 尝试解析用户选择
            selected_node = parse_user_selection(node_keyword, cached_nodes)
            if selected_node:
                logger.info(f"用户选择了: {selected_node.get('name')}")
                # 清除缓存
                clear_match_cache()
                # 检查是否是房屋级别
                if selected_node['level'] != 'house':
                    print(f"请选择具体的房屋，当前选择的是{selected_node['name']}（{selected_node['level']}）")
                    return
                # 继续处理 - 匹配押金项目
                asset_id = str(selected_node['id'])
                asset_type = 1
                node_name = selected_node['name']
                logger.info(f"从缓存获取房屋: {node_name}, ID={asset_id}")
            else:
                # 解析失败，清除缓存，按新关键词重新搜索
                logger.info("无法解析用户选择，清除缓存并重新搜索")
                clear_match_cache()
                selected_node = None
    else:
        selected_node = None

    if 'asset_id' not in locals():
        # 清理关键词
        clean_keyword = node_keyword.replace("押金", "").replace("收取", "").replace("的", "").strip()

        # 检查是否使用精确匹配
        use_exact_match = "/" in clean_keyword

        # 获取完整房屋结构
        household_data = search_household_structure(str(community_id), "")
        if household_data is None:
            print("搜索房屋结构失败")
            return

        # 找出匹配的节点
        if use_exact_match:
            matching_nodes = find_matching_nodes(household_data, clean_keyword, exact_match=True)
            if not matching_nodes:
                logger.info("精确匹配未找到结果，使用模糊匹配")
                keywords = clean_keyword.split("/")
                search_kw = keywords[-1] if keywords else clean_keyword
                household_data_for_search = search_household_structure(str(community_id), search_kw)
                if household_data_for_search:
                    household_data = household_data_for_search
                matching_nodes = find_matching_nodes(household_data, clean_keyword)
        else:
            keywords = split_keywords(clean_keyword)
            search_kw = keywords[-1] if keywords else clean_keyword
            household_data_for_search = search_household_structure(str(community_id), search_kw)
            if household_data_for_search:
                household_data = household_data_for_search
            matching_nodes = find_matching_nodes(household_data, clean_keyword)

        if not matching_nodes:
            print(f"未找到匹配的房屋: {node_keyword}")
            return

        if len(matching_nodes) > 1:
            # 多个匹配，保存到缓存并列出供用户选择
            print(f"找到多个匹配的房屋，请选择序号：")
            for idx, node in enumerate(matching_nodes, 1):
                print(f"  {idx}. {node['name']} ({node['level']})")
            save_match_cache(community_id, matching_nodes)
            print(f"\n请使用序号重新选择，例如：confirm_collect_cash_pledge 1")
            return

        # 只有一个匹配，直接使用
        selected_node = matching_nodes[0]
        if selected_node['level'] != 'house':
            print(f"匹配结果不是房屋，请选择具体的房屋，当前匹配到: {selected_node['name']}（{selected_node['level']}）")
            return
        asset_id = str(selected_node['id'])
        asset_type = 1
        node_name = selected_node['name']
        logger.info(f"匹配到房屋: {node_name}, ID={asset_id}")

    print(f"已选择房屋：{node_name}")

    # 4. 匹配押金项目
    matched_pledge = match_cash_pledge_item(community_id, pledge_name)
    need_create = False
    pledge_item_id = None
    pledge_item_name = pledge_name

    if matched_pledge is None:
        need_create = True
        logger.info(f"未找到押金项目 '{pledge_name}'，需要创建")
    else:
        pledge_item_id = str(matched_pledge.get('id'))
        pledge_item_name = matched_pledge.get('cashPledgeName')
        logger.info(f"找到已有押金项目: {pledge_item_name} (ID={pledge_item_id})")

    # 5. 处理支付方式
    pay_type = get_pay_type_by_name(pay_type_name) if pay_type_name else 2
    pay_type_name_result = get_pay_name_by_type(pay_type)

    # 6. 计算金额
    amount_fen = int(round(amount_yuan * 100))

    # 7. 保存到缓存
    cache_data = {
        "charge_system_name": charge_system_name,
        "community_id": community_id,
        "community_name": comm_name,
        "asset_id": asset_id,
        "asset_type": asset_type,
        "node_name": node_name,
        "pledge_item_id": pledge_item_id,
        "pledge_item_name": pledge_item_name,
        "amount_fen": amount_fen,
        "amount_yuan": amount_yuan,
        "pay_type": pay_type,
        "pay_type_name": pay_type_name_result,
        "need_create": need_create
    }
    save_cash_pledge_confirmation_cache(cache_data)

    # 8. 输出确认信息
    print(f"\n### 待收取押金信息\n")
    print(f"**小区**: {comm_name}")
    print(f"**房屋**: {node_name}")
    print(f"**押金项目**: {pledge_item_name}")
    print(f"**押金金额**: ¥ {amount_yuan:.2f}")
    print(f"**支付方式**: {pay_type_name_result}")

    if need_create:
        print(f"\n⚠ 未找到押金项目 '{pledge_name}'，需要创建新项目。")

    print(f"\n请确认是否收取押金？")
    print(f"- 运行命令 `confirm_collect_cash_pledge yes` 确认收取")
    print(f"- 运行命令 `confirm_collect_cash_pledge no` 取消")
    return


def confirm_collect_cash_pledge(confirmation_input: str) -> None:
    """第二步：确认收取押金，执行实际操作

    Args:
        confirmation_input: 用户确认输入 ('yes'/'no')
    """
    # 加载缓存
    pending_data = load_cash_pledge_confirmation_cache()
    if not pending_data:
        print("✗ 没有待确认的押金收取信息，或信息已过期，请重新查询")
        return

    # 提取缓存信息
    community_id = pending_data['community_id']
    community_name = pending_data['community_name']
    asset_id = pending_data['asset_id']
    asset_type = pending_data['asset_type']
    node_name = pending_data['node_name']
    pledge_item_id = pending_data['pledge_item_id']
    pledge_item_name = pending_data['pledge_item_name']
    amount_fen = pending_data['amount_fen']
    amount_yuan = pending_data['amount_yuan']
    pay_type = pending_data['pay_type']
    pay_type_name = pending_data['pay_type_name']
    need_create = pending_data['need_create']

    # 用户取消
    if confirmation_input.lower() == 'no' or confirmation_input.lower() == 'n':
        print("操作已取消")
        clear_cash_pledge_confirmation_cache()
        return

    if confirmation_input.lower() != 'yes' and confirmation_input.lower() != 'y':
        print("输入错误，请输入 yes 或 no")
        return

    # 如果需要创建，先创建押金项目
    if need_create:
        logger.info(f"需要先创建新押金项目: {pledge_item_name}")
        new_pledge_id = create_cash_pledge_item(community_id, pledge_item_name, amount_fen)
        if new_pledge_id is None:
            # 创建失败，可能是因为已经存在，重新查询一次
            logger.info(f"创建失败，重新查询押金项目: {pledge_item_name}")
            matched_pledge = match_cash_pledge_item(community_id, pledge_item_name)
            if matched_pledge is None:
                # 还是找不到，真的失败了
                clear_cash_pledge_confirmation_cache()
                return
            # 重新查询找到了，使用找到的
            pledge_item_id = str(matched_pledge.get('id'))
            pledge_item_name = matched_pledge.get('pledgeName')
            logger.info(f"重新查询找到已有押金项目: {pledge_item_name} (ID={pledge_item_id})")
        else:
            pledge_item_id = new_pledge_id

    # 调用API收取押金
    logger.info(f"开始收取押金: 小区={community_id}, 房屋={asset_id}, 押金项目={pledge_item_id}, 金额={amount_yuan:.2f}")
    result = add_cash_pledge_order(community_id, asset_id, asset_type, pledge_item_id, amount_fen, pay_type)

    if result is None:
        print(f"✗ 收取押金失败，请查看日志")
        clear_cash_pledge_confirmation_cache()
        return

    if isinstance(result, tuple):
        # error case: (message, None)
        error_msg = result[0]
        print(f"✗ 收取押金失败: {error_msg}")
        clear_cash_pledge_confirmation_cache()
        return

    # 成功，输出结果
    process_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n✓ 收取押金成功！\n")
    print(f"**小区**: {community_name}")
    print(f"**房屋**: {node_name}")
    print(f"**押金项目**: {pledge_item_name}")
    print(f"**押金金额**: ¥ {amount_yuan:.2f}")
    print(f"**支付方式**: {pay_type_name}")
    print(f"**收取时间**: {process_time_str}\n")

    # 清除缓存
    clear_cash_pledge_confirmation_cache()
    logger.info(f"收取押金完成: {community_name} / {node_name} / {pledge_item_name} / {amount_yuan:.2f}")


def generate_web_bill_share_url(community_id: int, asset_id: int, bill_ids: list) -> dict:
    """
    调用 API 生成微信账单分享链接

    Args:
        community_id: 小区ID
        asset_id: 房屋ID
        bill_ids: 账单ID列表

    Returns:
        API响应数据字典
    """
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None

    headers = get_headers_with_cookies(ck_dict, {"communityid": str(community_id)})

    payload = {
        "communityID": int(community_id),
        "assetType": 1,
        "assetId": int(asset_id),
        "ids": bill_ids
    }

    try:
        response = requests.post(
            f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/getWebBillShareURL",
            json=payload,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"生成催缴链接失败，状态码: {response.status_code}, 响应内容: {response.text}")
            return None

        response.raise_for_status()
        data = response.json()

        if data.get('code') != 0:
            logger.error(f"生成催缴链接失败: {data.get('msg')}")
            return None

        logger.info(f"成功生成催缴链接，小区ID: {community_id}, 房屋ID: {asset_id}, 账单数: {len(bill_ids)}")
        return data

    except requests.exceptions.RequestException as e:
        logger.error(f"生成催缴链接发生异常: {e}")
        return None


def check_user_in_team(teamID: int) -> bool:
    """
    检查当前用户是否在指定团队中

    Args:
        teamID: 团队ID

    Returns:
        bool: True = 在团队中，False = 不在团队中
    """
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return False

    headers = get_headers_with_cookies(ck_dict)

    import random
    params = {
        "teamID": int(teamID),
        "r": random.random()
    }

    try:
        response = requests.get(
            f"{CHARGE_API_BASE_URL}/mkg/api/v2/Team/checkInTeamT",
            params=params,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"检查用户团队成员资格失败，状态码: {response.status_code}, 响应内容: {response.text}")
            return False

        response.raise_for_status()
        data = response.json()

        # inTeam 直接在根级别（实际API返回格式），也兼容data里面的情况
        in_team = data.get('inTeam', False)
        if not in_team:
            in_team = data.get('data', {}).get('inTeam', False)
        logger.info(f"用户团队检查结果: teamID={teamID}, inTeam={in_team}")
        return in_team

    except requests.exceptions.RequestException as e:
        logger.error(f"检查用户团队成员资格发生异常: {e}")
        return False


def add_charge_notice(community_id: int, asset_id: int, bill_ids: list) -> dict:
    """
    添加支付通知（用于生成工单）

    Args:
        community_id: 小区ID
        asset_id: 房屋ID
        bill_ids: 账单ID列表

    Returns:
        dict: API响应数据，包含orderID
    """
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None

    headers = get_headers_with_cookies(ck_dict, {"communityid": str(community_id)})

    payload = {
        "communityID": int(community_id),
        "assetType": 1,
        "assetId": int(asset_id),
        "ids": bill_ids
    }

    try:
        response = requests.post(
            f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/addChargeNotice",
            json=payload,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"添加支付通知失败，状态码: {response.status_code}, 响应内容: {response.text}")
            return None

        response.raise_for_status()
        data = response.json()

        if data.get('code') != 0:
            logger.error(f"添加支付通知失败: {data.get('msg')}")
            return None

        logger.info(f"成功添加支付通知，小区ID: {community_id}, 房屋ID: {asset_id}, orderID: {data.get('data', {}).get('orderID')}")
        return data

    except requests.exceptions.RequestException as e:
        logger.error(f"添加支付通知发生异常: {e}")
        return None


def get_team_members(teamID: int) -> list:
    """
    获取团队成员列表

    Args:
        teamID: 团队ID

    Returns:
        list: 成员列表，每个元素包含 userID, nickname, phone
    """
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None

    headers = get_headers_with_cookies(ck_dict)

    import random
    params = {
        "teamID": int(teamID),
        "page": 1,
        "pageSize": 100,
        "keyword": "",
        "memberType": "1,2,3",
        "r": random.random()
    }

    try:
        response = requests.get(
            f"{API_BASE_URL}/mkg/api/v1/Organize/getMemberT",
            params=params,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"获取团队成员列表失败，状态码: {response.status_code}, 响应内容: {response.text}")
            return None

        response.raise_for_status()
        data = response.json()

        if data.get('code') != 0:
            logger.error(f"获取团队成员列表失败: {data.get('msg')}")
            return None

        # items 直接在根级别
        items = data.get('items', [])
        # 如果找不到，再尝试从 data 获取（兼容两种格式）
        if not items:
            items = data.get('data', {}).get('items', [])
        logger.info(f"成功获取团队成员列表，teamID={teamID}, 成员数={len(items)}")
        return items

    except requests.exceptions.RequestException as e:
        logger.error(f"获取团队成员列表发生异常: {e}")
        return None


def generate_charge_work_order(
    teamID: int,
    community_id: int,
    asset_id: int,
    order_id: int,
    share_url: str,
    worker_uids: list
) -> dict:
    """
    生成催缴工单

    Args:
        teamID: 团队ID
        community_id: 小区ID
        asset_id: 房屋ID
        order_id: 支付通知ID
        share_url: 催缴分享链接
        worker_uids: 代办人用户ID列表

    Returns:
        dict: API响应数据
    """
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None

    headers = get_headers_with_cookies(ck_dict, {"communityid": str(community_id)})

    import time
    current_timestamp = int(time.time())

    payload = {
        "teamID": int(teamID),
        "content": f"【催费任务】，业主缴费链接：{share_url}",
        "startTime": current_timestamp,
        "handModel": 2,
        "workerTeamId": int(teamID),
        "workerUids": worker_uids,
        "woTagList": [],
        "attachs": [],
        "media": [],
        "selectAll": False,
        "informTeamId": None,
        "from": 5,
        "communityID": int(community_id),
        "assetType": 1,
        "assetId": int(asset_id),
        "orderId": int(order_id)
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/mkg/api/v2/Charge/addChargeWorkOrder",
            json=payload,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"生成催缴工单失败，状态码: {response.status_code}, 响应内容: {response.text}")
            return None

        response.raise_for_status()
        data = response.json()

        if data.get('code') != 0:
            logger.error(f"生成催缴工单失败: {data.get('msg')}")
            return None

        logger.info(f"成功生成催缴工单，teamID={teamID}, communityID={community_id}, assetId={asset_id}")
        return data

    except requests.exceptions.RequestException as e:
        logger.error(f"生成催缴工单发生异常: {e}")
        return None


def _process_generate_collection_url(community_id: str, house_node: dict, community_name: str):
    """
    内部函数：处理生成催缴链接流程

    Args:
        community_id: 小区ID
        house_node: 房屋节点
        community_name: 小区名称
    """
    house_id = house_node['id']
    house_name = house_node['name']

    print(f"已选择房屋：{house_name}")

    # 查询欠费信息获取账单ID
    arrears_data = get_household_arrears_by_id(community_id, str(house_id))
    if not arrears_data:
        print("查询欠费信息失败")
        return

    arrears_list = arrears_data.get('data', [])
    if not arrears_list:
        print(f"该房屋当前无欠费，无法生成催缴链接")
        return

    # 提取所有账单ID
    # 从每个欠费项的 idStr 拆分逗号分隔
    bill_ids = []
    for arrear in arrears_list:
        id_str = arrear.get('idStr', '')
        if id_str:
            for bill_id_str in id_str.split(','):
                bill_id_str = bill_id_str.strip()
                if bill_id_str and bill_id_str.isdigit():
                    bill_ids.append(int(bill_id_str))

    if not bill_ids:
        print(f"未找到该房屋的欠费账单ID，无法生成催缴链接")
        return

    # 获取房屋ID（assetId）- 从第一个欠费项获取
    first_arrear = arrears_list[0]
    house_info = first_arrear.get('houseInfo', {})
    asset_id = house_info.get('id')
    if not asset_id:
        print("无法获取房屋ID信息")
        return

    # 调用 API 生成催缴链接
    print(f"正在生成催缴链接...")
    result = generate_web_bill_share_url(int(community_id), int(asset_id), bill_ids)

    if result:
        share_text = result.get('data', {}).get('text', '')
        if not share_text:
            print(f"\n✓ 催缴链接生成成功，但未返回分享文案")
            print(f"API返回数据: {result}")
        else:
            print(f"\n✓ 催缴链接生成成功！\n")
            print(f"**小区**: {community_name}")
            print(f"**房屋**: {house_name}")
            print(f"**账单数量**: {len(bill_ids)}")
            print(f"\n--- 分享链接文案 ---\n")
            print(share_text)
            logger.info(f"催缴链接生成成功: 小区={community_name}, 房屋={house_name}, 账单数={len(bill_ids)}")
    else:
        print("\n✗ 催缴链接生成失败，请查看日志获取详细信息")


def generate_collection_url_by_name(charge_system_name=None, community_name=None, keyword=None):
    """
    通过名称智能匹配房屋并生成催缴链接

    Args:
        charge_system_name: 收费系统名称
        community_name: 小区名称
        keyword: 房屋位置关键词
    """
    # 检查必要参数
    if not charge_system_name:
        print("NEED_INFO: 请提供收费系统名称")
        print("提示：可以先使用 list_charge_systems 命令查看可用的收费系统")
        return

    if not community_name:
        print("NEED_INFO: 请提供小区名称")
        return

    if not keyword:
        print("NEED_INFO: 请提供房屋位置关键词（如楼栋/单元/房屋号）")
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

    if len(community_map) > 1:
        # 多个匹配，列出供用户选择
        print(f"找到多个匹配的小区，请使用完整的小区名称重新查询：")
        for name in community_map.keys():
            print(f"  - {name}")
        return

    # 只有一个匹配，继续处理
    comm_name, comm_id = next(iter(community_map.items()))
    print(f"找到小区：{comm_name}")

    # 先尝试从缓存加载上一次的匹配列表
    cache_data = load_match_cache()
    if cache_data and str(cache_data.get('community_id')) == str(comm_id):
        cached_nodes = cache_data.get('nodes', [])
        if cached_nodes:
            # 尝试解析用户选择
            selected_node = parse_user_selection(keyword, cached_nodes)
            if selected_node:
                logger.info(f"用户选择了: {selected_node.get('name')}")
                # 清除缓存
                clear_match_cache()
                # 检查是否是房屋级别
                if selected_node['level'] != 'house':
                    print(f"请选择具体的房屋生成催缴链接，当前选择的是{selected_node['name']}（{selected_node['level']}）")
                    return
                # 继续处理
                return _process_generate_collection_url(str(comm_id), selected_node, comm_name)
            else:
                # 解析失败，清除缓存，按新关键词重新搜索
                logger.info("无法解析用户选择，清除缓存并重新搜索")
                clear_match_cache()

    # 清理关键词
    clean_keyword = keyword.replace("催缴链接", "").replace("链接", "").replace("的", "").strip()

    # 检查是否使用精确匹配
    use_exact_match = "/" in clean_keyword

    # 获取完整房屋结构
    household_data = search_household_structure(str(comm_id), "")

    if household_data is None:
        print("搜索房屋结构失败")
        return

    # 找出匹配的节点
    if use_exact_match:
        matching_nodes = find_matching_nodes(household_data, clean_keyword, exact_match=True)
        if not matching_nodes:
            logger.info("精确匹配未找到结果，使用模糊匹配")
            keywords = clean_keyword.split("/")
            search_kw = keywords[-1] if keywords else clean_keyword
            household_data_for_search = search_household_structure(str(comm_id), search_kw)
            if household_data_for_search:
                household_data = household_data_for_search
            matching_nodes = find_matching_nodes(household_data, clean_keyword)
    else:
        keywords = split_keywords(clean_keyword)
        search_kw = keywords[-1] if keywords else clean_keyword
        household_data_for_search = search_household_structure(str(comm_id), search_kw)
        if household_data_for_search:
            household_data = household_data_for_search
        matching_nodes = find_matching_nodes(household_data, clean_keyword)

    if not matching_nodes:
        # 尝试宽松匹配
        logger.info(f"严格匹配未找到，尝试宽松匹配: {clean_keyword}")
        matching_nodes = find_matching_nodes(household_data, clean_keyword, relaxed_match=True)

    if not matching_nodes:
        # 仍然没找到，生成候选列表
        logger.info(f"宽松匹配也未找到，生成候选列表")
        candidates = generate_candidates(household_data, clean_keyword)
        if candidates:
            print_candidates(clean_keyword, candidates)
        else:
            print(f"未找到与'{clean_keyword}'匹配的楼栋/单元/房屋，请确认输入是否正确")
        return

    if len(matching_nodes) == 1:
        node = matching_nodes[0]
        if node['level'] != 'house':
            print(f"请选择具体的房屋生成催缴链接，当前选择的是{node['name']}（{node['level']}）")
            return
        return _process_generate_collection_url(str(comm_id), node, comm_name)
    else:
        save_match_cache(comm_id, matching_nodes)
        print("MULTI_MATCH:")
        for idx, node in enumerate(matching_nodes, 1):
            level_label = {
                'building': '楼栋',
                'unit': '单元',
                'house': '房屋'
            }.get(node['level'], '未知')
            print(f"{idx}. {node['name']} ({level_label})")


def _process_generate_charge_work_order(community_id: str, house_node: dict, community_name: str, charge_system_id: str):
    """
    内部函数：处理生成催缴工单流程

    Args:
        community_id: 小区ID
        house_node: 房屋节点
        community_name: 小区名称
        charge_system_id: 收费系统ID
    """
    house_id = house_node['id']
    house_name = house_node['name']

    print(f"已选择房屋：{house_name}")

    # 获取小区收费系统初始化信息，从中提取团队ID
    print(f"正在获取团队信息...")
    init_info_result = get_community_cs_init_info(community_id, charge_system_id, None)
    if not init_info_result:
        print("获取小区初始化信息失败，无法继续")
        return

    # 解析团队ID：从csInfo.bindItemID获取
    try:
        # 重新调用API获取原始数据，因为上面的函数返回格式化文本
        import random
        ck_dict = ensure_authenticated()
        if not ck_dict:
            return None

        headers = get_headers_with_cookies(ck_dict, {"communityid": str(community_id)})
        params = {
            "communityID": int(community_id),
            "csID": int(charge_system_id),
            "r": random.random()
        }
        response = requests.get(
            f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/getCsInitInfo",
            params=params,
            headers=headers,
            timeout=10
        )
        if response.status_code != 200:
            print(f"获取团队ID失败，状态码: {response.status_code}")
            return
        data = response.json()
        if data.get('code') != 0:
            print(f"获取团队ID失败: {data.get('msg')}")
            return
        cs_info = data.get('data', {}).get('csInfo', {})
        team_id = cs_info.get('bindItemID')
        if not team_id:
            print(f"无法获取团队ID，请确认收费系统已正确绑定团队")
            return
        team_id = int(team_id)
        print(f"已绑定团队ID: {team_id}")
    except Exception as e:
        logger.error(f"解析团队ID失败: {e}")
        print(f"解析团队ID失败: {e}")
        return

    # 查询欠费信息获取账单ID
    arrears_data = get_household_arrears_by_id(community_id, str(house_id))
    if not arrears_data:
        print("查询欠费信息失败")
        return

    arrears_list = arrears_data.get('data', [])
    if not arrears_list:
        print(f"该房屋当前无欠费，无法生成催缴工单")
        return

    # 提取所有账单ID
    # 从每个欠费项的 idStr 拆分逗号分隔
    bill_ids = []
    for arrear in arrears_list:
        id_str = arrear.get('idStr', '')
        if id_str:
            for bill_id_str in id_str.split(','):
                bill_id_str = bill_id_str.strip()
                if bill_id_str and bill_id_str.isdigit():
                    bill_ids.append(int(bill_id_str))

    if not bill_ids:
        print(f"未找到该房屋的欠费账单ID，无法生成催缴工单")
        return

    # 获取房屋ID（assetId）- 从第一个欠费项获取
    first_arrear = arrears_list[0]
    house_info = first_arrear.get('houseInfo', {})
    asset_id = house_info.get('id')
    if not asset_id:
        print("无法获取房屋ID信息")
        return
    asset_id = int(asset_id)
    community_id_int = int(community_id)

    # 检查当前用户是否在团队中
    print(f"正在检查用户团队权限...")
    if not check_user_in_team(team_id):
        print(f"\n✗ 当前用户不在该收费系统绑定的团队（ID: {team_id}）中")
        print(f"请先加入团队后再生成催缴工单")
        return

    # 调用 API 生成催缴链接（复用已有函数）
    print(f"正在生成催缴链接...")
    url_result = generate_web_bill_share_url(community_id_int, asset_id, bill_ids)
    if not url_result:
        print(f"\n✗ 生成催缴链接失败，无法继续生成工单")
        return
    share_text = url_result.get('data', {}).get('text', '')
    # 从分享文本中提取第一个URL链接
    import re
    url_matches = re.findall(r'https?://[^\s]+', share_text)
    if url_matches:
        # 取第一个URL
        share_url = url_matches[0]
    else:
        # 如果没找到，直接用整个文本（不应该发生）
        share_url = share_text

    # 调用 API 添加支付通知
    print(f"正在添加支付通知...")
    notice_result = add_charge_notice(community_id_int, asset_id, bill_ids)
    if not notice_result:
        print(f"\n✗ 添加支付通知失败，请查看日志获取详细信息")
        return
    order_id = notice_result.get('data', {}).get('orderID')
    if not order_id:
        print(f"\n✗ 未获取到支付通知ID，请查看日志获取详细信息")
        return
    # API要求 orderId 是字符串类型
    order_id = str(order_id)

    # 获取团队成员列表
    print(f"正在获取团队成员列表...")
    members = get_team_members(team_id)
    if members is None:
        print(f"\n✗ 获取团队成员列表失败，请查看日志获取详细信息")
        return
    if not members:
        print(f"\n✗ 团队中没有找到成员，请检查团队配置")
        return

    # 保存待确认数据到缓存
    pending_data = {
        "teamID": team_id,
        "community_id": community_id_int,
        "asset_id": asset_id,
        "community_name": community_name,
        "house_name": house_name,
        "bill_ids": bill_ids,
        "share_url": share_url,
        "order_id": order_id,
        "members_list": members
    }
    save_work_order_confirmation(pending_data)

    # 输出成员列表供用户选择
    print(f"\n### 请选择代办人")
    print(f"\n**小区**: {community_name}")
    print(f"**房屋**: {house_name}")
    print(f"**欠费账单数**: {len(bill_ids)} 条")
    print(f"\n请选择指定序号的团队成员作为代办人：")
    print()
    for idx, member in enumerate(members, 1):
        nickname = member.get('nickname', '未知')
        phone = member.get('phone', '')
        user_id = member.get('userID', '')
        display_name = nickname
        if phone:
            display_name = f"{nickname} ({phone})"
        print(f"  {idx}. {display_name} - 用户ID: {user_id}")
    print()
    print(f"请运行命令确认选择：")
    print(f"  python3 main.py confirm_charge_work_order <序号>")
    print(f"示例：python3 main.py confirm_charge_work_order 1")
    print(f"支持多选：python3 main.py confirm_charge_work_order 1,2")
    logger.info(f"已生成待确认催缴工单，等待用户选择代办人: community={community_name}, house={house_name}")


def generate_charge_work_order_by_name(charge_system_name=None, community_name=None, keyword=None):
    """
    通过名称智能匹配房屋并生成催缴工单（两步完成）

    Args:
        charge_system_name: 收费系统名称
        community_name: 小区名称
        keyword: 房屋位置关键词
    """
    # 检查必要参数
    if not charge_system_name:
        print("NEED_INFO: 请提供收费系统名称")
        print("提示：可以先使用 list_charge_systems 命令查看可用的收费系统")
        return

    if not community_name:
        print("NEED_INFO: 请提供小区名称")
        return

    if not keyword:
        print("NEED_INFO: 请提供房屋位置关键词（如楼栋/单元/房屋号）")
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

    if len(community_map) > 1:
        # 多个匹配，列出供用户选择
        print(f"找到多个匹配的小区，请使用完整的小区名称重新查询：")
        for name in community_map.keys():
            print(f"  - {name}")
        return

    # 只有一个匹配，继续处理
    comm_name, comm_id = next(iter(community_map.items()))
    print(f"找到小区：{comm_name}")

    # 先尝试从缓存加载上一次的匹配列表
    cache_data = load_match_cache()
    if cache_data and str(cache_data.get('community_id')) == str(comm_id):
        cached_nodes = cache_data.get('nodes', [])
        if cached_nodes:
            # 尝试解析用户选择
            selected_node = parse_user_selection(keyword, cached_nodes)
            if selected_node:
                logger.info(f"用户选择了: {selected_node.get('name')}")
                # 清除缓存
                clear_match_cache()
                # 检查是否是房屋级别
                if selected_node['level'] != 'house':
                    print(f"请选择具体的房屋生成催缴工单，当前选择的是{selected_node['name']}（{selected_node['level']}）")
                    return
                # 继续处理
                return _process_generate_charge_work_order(str(comm_id), selected_node, comm_name, charge_system_id)
            else:
                # 解析失败，清除缓存，按新关键词重新搜索
                logger.info("无法解析用户选择，清除缓存并重新搜索")
                clear_match_cache()

    # 清理关键词
    clean_keyword = keyword.replace("工单", "").replace("催缴", "").replace("的", "").strip()

    # 检查是否使用精确匹配
    use_exact_match = "/" in clean_keyword

    # 获取完整房屋结构
    household_data = search_household_structure(str(comm_id), "")

    if household_data is None:
        print("搜索房屋结构失败")
        return

    # 找出匹配的节点
    if use_exact_match:
        matching_nodes = find_matching_nodes(household_data, clean_keyword, exact_match=True)
        if not matching_nodes:
            logger.info("精确匹配未找到结果，使用模糊匹配")
            keywords = clean_keyword.split("/")
            search_kw = keywords[-1] if keywords else clean_keyword
            household_data_for_search = search_household_structure(str(comm_id), search_kw)
            if household_data_for_search:
                household_data = household_data_for_search
            matching_nodes = find_matching_nodes(household_data, clean_keyword)
    else:
        keywords = split_keywords(clean_keyword)
        search_kw = keywords[-1] if keywords else clean_keyword
        household_data_for_search = search_household_structure(str(comm_id), search_kw)
        if household_data_for_search:
            household_data = household_data_for_search
        matching_nodes = find_matching_nodes(household_data, clean_keyword)

    if not matching_nodes:
        # 尝试宽松匹配
        logger.info(f"严格匹配未找到，尝试宽松匹配: {clean_keyword}")
        matching_nodes = find_matching_nodes(household_data, clean_keyword, relaxed_match=True)

    if not matching_nodes:
        # 仍然没找到，生成候选列表
        logger.info(f"宽松匹配也未找到，生成候选列表")
        candidates = generate_candidates(household_data, clean_keyword)
        if candidates:
            print_candidates(clean_keyword, candidates)
        else:
            print(f"未找到与'{clean_keyword}'匹配的楼栋/单元/房屋，请确认输入是否正确")
        return

    if len(matching_nodes) == 1:
        node = matching_nodes[0]
        if node['level'] != 'house':
            print(f"请选择具体的房屋生成催缴工单，当前选择的是{node['name']}（{node['level']}）")
            return
        return _process_generate_charge_work_order(str(comm_id), node, comm_name, charge_system_id)
    else:
        save_match_cache(comm_id, matching_nodes)
        print("MULTI_MATCH:")
        for idx, node in enumerate(matching_nodes, 1):
            level_label = {
                'building': '楼栋',
                'unit': '单元',
                'house': '房屋'
            }.get(node['level'], '未知')
            print(f"{idx}. {node['name']} ({level_label})")


def confirm_charge_work_order(selection_input: str):
    """
    确认生成催缴工单，处理用户对代办人的选择

    Args:
        selection_input: 用户选择的序号字符串，支持单个 "1" 或多个 "1,2"
    """
    # 从缓存加载待确认数据
    pending_data = load_work_order_confirmation()
    if not pending_data:
        print("没有待确认的催缴工单数据，或数据已过期，请重新开始流程")
        print("请先运行：python3 main.py generate_charge_work_order <收费系统名称> <小区名称> <房屋关键词>")
        return

    # 获取成员列表
    members = pending_data.get('members_list', [])
    if not members:
        print("缓存数据中没有成员信息，请重新开始流程")
        clear_work_order_confirmation()
        return

    # 解析用户选择
    # 支持："1", "1,2", "1, 2" 等格式
    selected_indices = []
    try:
        # 分割并去除空格
        for part in selection_input.replace('，', ',').split(','):
            part = part.strip()
            if part:
                idx = int(part)
                if idx < 1 or idx > len(members):
                    print(f"序号 {idx} 超出范围，请输入 1 到 {len(members)} 之间的序号")
                    return
                selected_indices.append(idx - 1)  # 转成0-based索引
    except ValueError:
        print(f"无法解析选择：{selection_input}，请输入数字序号如 '1' 或 '1,2'")
        return

    if not selected_indices:
        print(f"未选择任何代办人，请重新输入")
        return

    # 提取选中的代办人用户ID
    selected_members = []
    selected_user_ids = []
    for idx in selected_indices:
        member = members[idx]
        selected_members.append(member)
        user_id = member.get('userID')
        if user_id:
            selected_user_ids.append(int(user_id))

    if not selected_user_ids:
        print(f"无法获取选中成员的用户ID，请重新开始流程")
        clear_work_order_confirmation()
        return

    # 调用API生成工单
    print(f"正在生成催缴工单...")
    logger.info(f"开始生成催缴工单，选中 {len(selected_user_ids)} 个代办人")

    result = generate_charge_work_order(
        teamID=pending_data['teamID'],
        community_id=pending_data['community_id'],
        asset_id=pending_data['asset_id'],
        order_id=pending_data['order_id'],
        share_url=pending_data['share_url'],
        worker_uids=selected_user_ids
    )

    if not result:
        print(f"\n✗ 生成催缴工单失败，请查看日志获取详细信息")
        return

    # 生成成功，输出结果
    # 清除缓存
    clear_work_order_confirmation()

    # 准备显示信息
    selected_names = []
    for member in selected_members:
        nickname = member.get('nickname', '未知')
        phone = member.get('phone', '')
        if phone:
            display = f"{nickname} ({phone})"
        else:
            display = nickname
        selected_names.append(display)

    print(f"\n✅ 催缴工单生成成功！\n")
    print(f"**小区**: {pending_data['community_name']}")
    print(f"**房屋**: {pending_data['house_name']}")
    print(f"**欠费账单数**: {len(pending_data['bill_ids'])} 条")
    print(f"**指定代办人**: {', '.join(selected_names)}")
    print(f"**团队ID**: {pending_data['teamID']}")
    print(f"**支付通知ID**: {pending_data['order_id']}")

    if 'data' in result and result['data']:
        work_order_id = result['data'].get('id', '')
        if work_order_id:
            print(f"**工单ID**: {work_order_id}")

    logger.info(f"催缴工单生成成功: community={pending_data['community_name']}, house={pending_data['house_name']},代办人={len(selected_user_ids)}")


def create_phone_call_log(community_id: int, asset_id: int, call_user_uid: int) -> dict:
    """
    创建电话催缴记录

    Args:
        community_id: 小区ID
        asset_id: 房屋ID
        call_user_uid: 拨打电话用户ID（当前登录用户）

    Returns:
        API返回结果字典，失败返回None
    """
    import time
    import random
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None

    headers = get_headers_with_cookies(ck_dict, {"communityid": str(community_id)})

    payload = {
        "communityId": community_id,
        "callUser": call_user_uid,
        "assetId": asset_id,
        "callType": 5,
        "callTime": int(time.time()),
        "imgs": [],
        "assetType": 1
    }

    try:
        response = requests.post(
            f"{CHARGE_API_BASE_URL}/mkg/api/v2/Charge/addMoneyCallLog",
            json=payload,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"创建电话催缴记录失败，状态码: {response.status_code}, 响应内容: {response.text}")
            return None

        response.raise_for_status()
        data = response.json()

        if data.get('code') != 0:
            logger.error(f"创建电话催缴记录失败: {data.get('msg')}")
            return None

        logger.info(f"创建电话催缴记录成功: communityId={community_id}, assetId={asset_id}, callUser={call_user_uid}")
        return data

    except requests.exceptions.RequestException as e:
        logger.error(f"创建电话催缴记录调用发生异常: {e}")
        return None


def _process_create_phone_call_log(community_id: str, house_node: dict, community_name: str, call_user_uid: int):
    """
    内部函数：处理创建电话催缴记录流程

    Args:
        community_id: 小区ID
        house_node: 房屋节点
        community_name: 小区名称
        call_user_uid: 当前登录用户ID
    """
    house_id = house_node['id']
    house_name = house_node['name']

    print(f"已选择房屋：{house_name}")
    print(f"正在创建电话催缴记录...")

    result = create_phone_call_log(int(community_id), int(house_id), call_user_uid)

    if result is not None:
        print(f"\n✅ 电话催缴记录创建成功！\n")
        print(f"**小区**: {community_name}")
        print(f"**房屋**: {house_name}")
        print(f"**记录类型**: 电话催缴")
        logger.info(f"电话催缴记录创建完成: 小区={community_name}, 房屋={house_name}")
    else:
        print(f"\n✗ 电话催缴记录创建失败，请查看日志获取详细信息")


def create_phone_call_log_by_name(charge_system_name=None, community_name=None, keyword=None):
    """
    通过名称智能匹配房屋并创建电话催缴记录

    Args:
        charge_system_name: 收费系统名称
        community_name: 小区名称
        keyword: 房屋位置关键词
    """
    # 检查必要参数
    if not charge_system_name:
        print("NEED_INFO: 请提供收费系统名称")
        print("提示：可以先使用 list_charge_systems 命令查看可用的收费系统")
        return

    if not community_name:
        print("NEED_INFO: 请提供小区名称")
        return

    if not keyword:
        print("NEED_INFO: 请提供房屋位置关键词（如楼栋/单元/房屋号）")
        return

    # 获取当前登录用户ID
    session = session_mgr.get_session()
    if not session or 'extUIMsg' not in session:
        print("无法获取当前登录用户ID，请先登录")
        return
    ext_info = session['extUIMsg']
    if 'uid' not in ext_info:
        print("无法获取当前登录用户ID，请先登录")
        return
    call_user_uid = int(ext_info['uid'])

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

    if len(community_map) > 1:
        # 多个匹配，列出供用户选择
        print(f"找到多个匹配的小区，请使用完整的小区名称重新查询：")
        for name in community_map.keys():
            print(f"  - {name}")
        return

    # 只有一个匹配，继续处理
    comm_name, comm_id = next(iter(community_map.items()))
    print(f"找到小区：{comm_name}")

    # 先尝试从缓存加载上一次的匹配列表
    cache_data = load_match_cache()
    if cache_data and str(cache_data.get('community_id')) == str(comm_id):
        cached_nodes = cache_data.get('nodes', [])
        if cached_nodes:
            # 尝试解析用户选择
            selected_node = parse_user_selection(keyword, cached_nodes)
            if selected_node:
                logger.info(f"用户选择了: {selected_node.get('name')}")
                # 清除缓存
                clear_match_cache()
                # 检查是否是房屋级别
                if selected_node['level'] != 'house':
                    print(f"请选择具体的房屋创建电话催缴记录，当前选择的是{selected_node['name']}（{selected_node['level']}）")
                    return
                # 继续处理
                return _process_create_phone_call_log(str(comm_id), selected_node, comm_name, call_user_uid)
            else:
                # 解析失败，清除缓存，按新关键词重新搜索
                logger.info("无法解析用户选择，清除缓存并重新搜索")
                clear_match_cache()

    # 清理关键词
    clean_keyword = keyword.replace("电话催缴", "").replace("催缴", "").replace("记录", "").replace("的", "").strip()

    # 检查是否使用精确匹配
    use_exact_match = "/" in clean_keyword

    # 获取完整房屋结构
    household_data = search_household_structure(str(comm_id), "")

    if household_data is None:
        print("搜索房屋结构失败")
        return

    # 找出匹配的节点
    if use_exact_match:
        matching_nodes = find_matching_nodes(household_data, clean_keyword, exact_match=True)
        if not matching_nodes:
            logger.info("精确匹配未找到结果，使用模糊匹配")
            keywords = clean_keyword.split("/")
            search_kw = keywords[-1] if keywords else clean_keyword
            household_data_for_search = search_household_structure(str(comm_id), search_kw)
            if household_data_for_search:
                household_data = household_data_for_search
            matching_nodes = find_matching_nodes(household_data, clean_keyword)
    else:
        keywords = split_keywords(clean_keyword)
        search_kw = " ".join(keywords)
        household_data_for_search = search_household_structure(str(comm_id), search_kw)
        if household_data_for_search:
            household_data = household_data_for_search
        matching_nodes = find_matching_nodes(household_data, clean_keyword)

    if not matching_nodes:
        # 尝试宽松匹配
        logger.info(f"严格匹配未找到，尝试宽松匹配: {clean_keyword}")
        matching_nodes = find_matching_nodes(household_data, clean_keyword, relaxed_match=True)

    if not matching_nodes:
        # 仍然没找到，生成候选列表
        logger.info(f"宽松匹配也未找到，生成候选列表")
        candidates = generate_candidates(household_data, clean_keyword)
        if candidates:
            print_candidates(clean_keyword, candidates)
        else:
            print(f"未找到与'{clean_keyword}'匹配的楼栋/单元/房屋，请确认输入是否正确")
        return

    if len(matching_nodes) == 1:
        node = matching_nodes[0]
        if node['level'] != 'house':
            print(f"请选择具体的房屋创建电话催缴记录，当前选择的是{node['name']}（{node['level']}）")
            return
        return _process_create_phone_call_log(str(comm_id), node, comm_name, call_user_uid)
    else:
        save_match_cache(comm_id, matching_nodes)
        print("MULTI_MATCH:")
        for idx, node in enumerate(matching_nodes, 1):
            level_label = {
                'building': '楼栋',
                'unit': '单元',
                'house': '房屋'
            }.get(node['level'], '未知')
            print(f"{idx}. {node['name']} ({level_label})")


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
    elif command == "get_custom_range_stats":
        # 查询小区自定义时间范围收入统计
        if len(sys.argv) < 6:
            print("错误：请提供收费系统名称、小区名称、开始日期和结束日期")
            print("用法: python3 main.py get_custom_range_stats <收费系统名称> <小区名称> <开始日期> <结束日期>")
            print("日期格式: YYYY-MM-DD")
            print("示例: python3 main.py get_custom_range_stats <收费系统> <小区> 2025-01-01 2026-12-31")
        else:
            charge_system_name = sys.argv[2]
            community_name = sys.argv[3]
            start_date_str = sys.argv[4]
            end_date_str = sys.argv[5]
            get_custom_range_stats(charge_system_name, community_name, start_date_str, end_date_str)
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
    elif command == "get_today_stats":
        # 查询小区今日收入统计
        if len(sys.argv) < 4:
            print("错误：请提供收费系统名称和小区名称")
            print("用法: python3 main.py get_today_stats <收费系统名称> <小区名称>")
        else:
            charge_system_name = sys.argv[2]
            community_name = sys.argv[3]
            get_today_stats(charge_system_name, community_name)
    elif command == "get_community_today_stats":
        # 通过小区ID查询今日收入统计
        if len(sys.argv) < 3:
            print("错误：请提供小区ID参数")
            print("用法: python3 main.py get_community_today_stats <小区ID>")
        else:
            community_id = sys.argv[2]
            get_community_today_stats(community_id)
    elif command == "get_community_custom_range_stats":
        # 通过小区ID查询自定义时间范围收入统计
        if len(sys.argv) < 5:
            print("错误：请提供小区ID、开始时间戳和结束时间戳")
            print("用法: python3 main.py get_community_custom_range_stats <小区ID> <开始时间戳> <结束时间戳>")
        else:
            community_id = sys.argv[2]
            start_time = int(sys.argv[3])
            end_time = int(sys.argv[4])
            get_community_custom_range_stats(community_id, start_time, end_time)
    elif command == "get_monthly_expense":
        # 查询小区本月支出统计
        if len(sys.argv) < 4:
            print("错误：请提供收费系统名称和小区名称")
            print("用法: python3 main.py get_monthly_expense <收费系统名称> <小区名称>")
        else:
            charge_system_name = sys.argv[2]
            community_name = sys.argv[3]
            get_monthly_expense(charge_system_name, community_name)
    elif command == "get_community_monthly_expense":
        # 通过小区ID查询本月支出统计
        if len(sys.argv) < 3:
            print("错误：请提供小区ID参数")
            print("用法: python3 main.py get_community_monthly_expense <小区ID>")
        else:
            community_id = sys.argv[2]
            get_community_monthly_expense(community_id)
    elif command == "get_collection_rate":
        # 查询小区本月收缴率统计
        if len(sys.argv) < 4:
            print("错误：请提供收费系统名称和小区名称")
            print("用法: python3 main.py get_collection_rate <收费系统名称> <小区名称> [费用类型名称]")
            print("示例: python3 main.py get_collection_rate 收费系统 小区 物业管理费")
        else:
            charge_system_name = sys.argv[2]
            community_name = sys.argv[3]
            fee_type = sys.argv[4] if len(sys.argv) >= 5 else None
            get_collection_rate(charge_system_name, community_name, fee_type)
    elif command == "get_community_collection_rate":
        # 通过小区ID和收费系统ID查询本月收缴率统计
        if len(sys.argv) < 4:
            print("错误：请提供小区ID和收费系统ID参数")
            print("用法: python3 main.py get_community_collection_rate <小区ID> <收费系统ID> [收费项目ID] [费用类型名称]")
            print("示例: python3 main.py get_community_collection_rate 10587 10643 71107 物业管理费")
        else:
            community_id = sys.argv[2]
            cs_id = sys.argv[3]
            charge_item_id = sys.argv[4] if len(sys.argv) >= 5 else None
            fee_type_name = sys.argv[5] if len(sys.argv) >= 6 else charge_item_id
            get_community_collection_rate(community_id, cs_id, None, charge_item_id, fee_type_name)
    elif command == "get_arrear_households":
        # 查询小区欠费户数统计
        if len(sys.argv) < 4:
            print("错误：请提供收费系统名称和小区名称")
            print("用法: python3 main.py get_arrear_households <收费系统名称> <小区名称>")
        else:
            charge_system_name = sys.argv[2]
            community_name = sys.argv[3]
            get_arrear_households(charge_system_name, community_name)
    elif command == "get_community_arrear_households":
        # 通过小区ID查询欠费户数统计
        if len(sys.argv) < 3:
            print("错误：请提供小区ID参数")
            print("用法: python3 main.py get_community_arrear_households <小区ID>")
        else:
            community_id = sys.argv[2]
            get_community_arrear_households(community_id)
    elif command == "get_household_arrears":
        # 查询房屋/楼栋/单元欠费
        if len(sys.argv) < 5:
            print("错误：请提供收费系统名称、小区名称和搜索关键词")
            print("用法: python3 main.py get_household_arrears <收费系统名称> <小区名称> <关键词>")
        else:
            charge_system_name = sys.argv[2]
            community_name = sys.argv[3]
            keyword = sys.argv[4]
            get_household_arrears_by_name(charge_system_name, community_name, keyword)
    elif command == "get_household_specific_arrears":
        # 查询特定房屋指定时间范围和费用类型欠费
        if len(sys.argv) < 7:
            print("错误：请提供收费系统名称、小区名称、房屋关键词、开始日期、结束日期和费用类型")
            print("用法: python3 main.py get_household_specific_arrears <收费系统名称> <小区名称> <房屋关键词> <开始日期> <结束日期> <费用类型>")
            print("日期格式: YYYY-MM-DD")
            print("支持费用类型: 物业费, 水费, 电费, 燃气费")
            print("示例: python3 main.py get_household_specific_arrears <收费系统> <小区> 1栋/1单元/101 2025-01-01 2026-12-31 物业费")
        else:
            charge_system_name = sys.argv[2]
            community_name = sys.argv[3]
            keyword = sys.argv[4]
            start_date_str = sys.argv[5]
            end_date_str = sys.argv[6]
            fee_type = sys.argv[7] if len(sys.argv) > 7 else None
            get_household_specific_arrears_by_name(charge_system_name, community_name, keyword, start_date_str, end_date_str, fee_type)
    elif command == "get_household_fee_type_arrears":
        # 查询特定房屋指定费用类型欠费（不限制时间）
        if len(sys.argv) < 5:
            print("错误：请提供收费系统名称、小区名称、房屋关键词和费用类型")
            print("用法: python3 main.py get_household_fee_type_arrears <收费系统名称> <小区名称> <房屋关键词> <费用类型>")
            print("支持费用类型: 物业费, 水费, 电费, 燃气费")
        else:
            charge_system_name = sys.argv[2]
            community_name = sys.argv[3]
            keyword = sys.argv[4]
            fee_type = sys.argv[5]
            get_household_specific_arrears_by_name(charge_system_name, community_name, keyword, None, None, fee_type)
    elif command == "get_current_user_info":
        # 查询当前登录用户信息
        if len(sys.argv) < 3:
            # 没有参数，直接获取当前登录用户信息
            get_current_user_info()
        elif len(sys.argv) < 4:
            print("错误：请同时提供收费系统名称和小区名称，或者不提供任何参数直接查询登录信息")
            print("用法:")
            print("  python3 main.py get_current_user_info  # 直接查询当前登录用户信息")
            print("  python3 main.py get_current_user_info <收费系统名称> <小区名称>  # 查询完整信息")
        else:
            charge_system_name = sys.argv[2]
            community_name = sys.argv[3]
            get_current_user_info(charge_system_name, community_name)
    elif command == "send_wechat_reminder":
        # 通过名称发送微信缴费提醒（推荐）
        if len(sys.argv) < 4:
            print("错误：请提供收费系统名称和小区名称")
            print("用法: python3 main.py send_wechat_reminder <收费系统名称> <小区名称>")
        else:
            charge_system_name = sys.argv[2]
            community_name = sys.argv[3]
            send_wechat_payment_reminder_by_name(charge_system_name, community_name)
    elif command == "meter_reading":
        # 智能抄表入口
        if len(sys.argv) < 7:
            print("错误：请提供收费系统名称、小区名称、房屋关键词、仪器类型和读数")
            print("用法: python3 main.py meter_reading <收费系统名称> <小区名称> <房屋关键词> <仪器类型> <读数> [备注]")
            print("仪器类型: 水表 或 电表")
        else:
            charge_system_name = sys.argv[2]
            community_name = sys.argv[3]
            keyword = sys.argv[4]
            meter_type_str = sys.argv[5]
            reading = sys.argv[6]
            remark = sys.argv[7] if len(sys.argv) > 7 else ""
            do_meter_reading_by_name(charge_system_name, community_name, keyword, meter_type_str, reading, remark)
    elif command == "get_meter_status":
        # 智能查询当前读数入口
        if len(sys.argv) < 6:
            print("错误：请提供收费系统名称、小区名称、房屋关键词和仪器类型")
            print("用法: python3 main.py get_meter_status <收费系统名称> <小区名称> <房屋关键词> <仪器类型>")
            print("仪器类型: 水表 或 电表")
        else:
            charge_system_name = sys.argv[2]
            community_name = sys.argv[3]
            keyword = sys.argv[4]
            meter_type_str = sys.argv[5]
            get_meter_status_by_name(charge_system_name, community_name, keyword, meter_type_str)
    elif command == "send_community_wechat_reminder":
        # 通过小区ID发送微信缴费提醒（旧版）
        if len(sys.argv) < 3:
            print("错误：请提供小区ID参数")
            print("用法: python3 main.py send_community_wechat_reminder <小区ID>")
        else:
            community_id = sys.argv[2]
            result = send_wechat_payment_reminder(community_id)
            if result:
                print(f"微信缴费提醒发送成功！")
                print(f"响应消息：{result.get('msg', '无')}")
            else:
                print("微信缴费提醒发送失败，请查看日志获取详细信息")
    elif command == "get_community_cs_init_info":
        # 通过小区ID和收费系统ID查询初始化信息
        if len(sys.argv) < 4:
            print("错误：请提供小区ID和收费系统ID参数")
            print("用法: python3 main.py get_community_cs_init_info <小区ID> <收费系统ID>")
        else:
            community_id = sys.argv[2]
            cs_id = sys.argv[3]
            result = get_community_cs_init_info(community_id, cs_id)
            if result:
                print(result)
    elif command == "send_sms_reminder":
        # 发送单个房屋短信催缴（推荐，通过名称智能匹配）
        if len(sys.argv) < 5:
            print("错误：请提供收费系统名称、小区名称和房屋关键词")
            print("用法: python3 main.py send_sms_reminder <收费系统名称> <小区名称> <房屋关键词>")
            print("示例: python3 main.py send_sms_reminder 收费系统 小区 1栋/1单元/101")
        else:
            charge_system_name = sys.argv[2]
            community_name = sys.argv[3]
            keyword = sys.argv[4]
            send_single_house_sms_reminder_by_name(charge_system_name, community_name, keyword)
    elif command == "send_single_house_sms_reminder":
        # 发送单个房屋短信催缴（底层ID模式，备用）
        if len(sys.argv) < 6:
            print("错误：请提供小区ID、房屋ID、业主ID列表和账单ID列表")
            print("用法: python3 main.py send_single_house_sms_reminder <小区ID> <房屋ID> <业主ID逗号分隔> <账单ID逗号分隔>")
        else:
            community_id = sys.argv[2]
            asset_id = int(sys.argv[3])
            uids = [int(uid) for uid in sys.argv[4].split(',') if uid.strip()]
            ids = [int(bid) for bid in sys.argv[5].split(',') if bid.strip()]
            result = send_single_house_sms_reminder(community_id, asset_id, uids, ids)
            if result:
                print(f"✓ 短信催缴发送成功！")
                print(f"响应消息：{result.get('msg', '无')}")
            else:
                print("短信催缴发送失败，请查看日志获取详细信息")
    elif command == "confirm_sms_reminder":
        # 确认短信催发送，处理用户选择
        if len(sys.argv) < 3:
            print("错误：请提供确认选项（yes/no 或序号）")
            print("用法: python3 main.py confirm_sms_reminder <yes/no/序号>")
            print("示例: python3 main.py confirm_sms_reminder yes")
            print("示例: python3 main.py confirm_sms_reminder 1")
            print("示例: python3 main.py confirm_sms_reminder 1,2")
        else:
            confirmation_input = sys.argv[2]
            confirm_sms_reminder(confirmation_input)
    elif command == "collect_payment":
        # 对特定房屋指定时间范围的账单进行收款（推荐，智能匹配）
        if len(sys.argv) < 4:
            print("错误：请提供收费系统名称、小区名称和房屋关键词")
            print("用法: python3 main.py collect_payment <收费系统名称> <小区名称> <房屋关键词> [开始日期] [结束日期] [收费项目] [支付方式]")
            print("日期格式: YYYY-MM-DD")
            print("支持支付方式: 现金、微信、支付宝（默认现金）")
            print("示例: python3 main.py collect_payment 收费系统 小区 1栋/1单元/101 2026-03-01 2026-03-31 物业费 现金")
            print("示例（默认本月，只收物业费）: python3 main.py collect_payment 收费系统 小区 1栋/1单元/101 物业费 现金")
            print("示例（默认本月，默认现金）: python3 main.py collect_payment 收费系统 小区 1栋/1单元/101 物业费")
            print("示例（默认本月）: python3 main.py collect_payment 收费系统 小区 1栋/1单元/101 现金")
        else:
            charge_system_name = sys.argv[2]
            community_name = sys.argv[3]
            keyword = sys.argv[4]

            # 处理可选参数：开始日期、结束日期、收费项目、支付方式
            start_date_str = None
            end_date_str = None
            charge_item_name = None
            pay_type_name = None

            def is_pay_method(s: str) -> bool:
                """判断是否是支付方式名称"""
                return s in ["现金", "微信", "支付宝"]

            def is_date(s: str) -> bool:
                """简单判断是否是日期格式 YYYY-MM-DD"""
                return len(s) == 10 and '-' in s

            # len = 5 → 只有必填项：collect_payment cs community keyword
            # len = 6 → 要么是支付方式，要么是收费项目
            # len = 7 → 要么是 start end，要么是 charge_item pay_type
            # len = 8 → start end + charge_item
            # len = 9 → start end + charge_item + pay_type

            if len(sys.argv) == 6:
                # 判断第5个参数是支付方式还是收费项目
                arg = sys.argv[5]
                if is_pay_method(arg):
                    pay_type_name = arg
                else:
                    charge_item_name = arg
            elif len(sys.argv) == 7:
                arg1 = sys.argv[5]
                arg2 = sys.argv[6]
                if is_date(arg1) and is_date(arg2):
                    # 两个都是日期 → start end
                    start_date_str = arg1
                    end_date_str = arg2
                else:
                    # 否则第一个收费项目，第二个支付方式
                    charge_item_name = arg1
                    pay_type_name = arg2
            elif len(sys.argv) == 8:
                arg1 = sys.argv[5]
                arg2 = sys.argv[6]
                if is_date(arg1) and is_date(arg2):
                    # start end + charge_item
                    start_date_str = arg1
                    end_date_str = arg2
                    charge_item_name = sys.argv[7]
                else:
                    # 这种情况应该不会出现，按收费项目 + 支付方式处理
                    charge_item_name = arg1
                    pay_type_name = sys.argv[7]
            elif len(sys.argv) >= 9:
                # 完整参数：start end + charge_item + pay_type
                start_date_str = sys.argv[5]
                end_date_str = sys.argv[6]
                charge_item_name = sys.argv[7]
                pay_type_name = sys.argv[8]

            collect_house_bills_by_name(charge_system_name, community_name, keyword, start_date_str, end_date_str, charge_item_name, pay_type_name)
    elif command == "confirm_payment":
        # 确认收款，处理用户选择
        if len(sys.argv) < 3:
            print("错误：请提供确认选项（yes/no 或序号）")
            print("用法: python3 main.py confirm_payment <yes/no/序号>")
            print("示例: python3 main.py confirm_payment yes")
            print("示例: python3 main.py confirm_payment 1")
            print("示例: python3 main.py confirm_payment 1,2")
        else:
            confirmation_input = sys.argv[2]
            confirm_payment_collection(confirmation_input)
    elif command == "list_refundable_bills":
        # 查询可退款账单（推荐，智能匹配，两步完成）
        # 用法: list_refundable_bills <收费系统名称> <小区名称> <房屋关键词> [开始日期] [结束日期] [收费项目]
        if len(sys.argv) < 5:
            print("错误：请提供收费系统名称、小区名称和房屋关键词")
            print("用法: python3 main.py list_refundable_bills <收费系统名称> <小区名称> <房屋关键词> [开始日期] [结束日期] [收费项目]")
            print("日期格式: YYYY-MM-DD")
            print("示例: python3 main.py list_refundable_bills 收费系统 小区 1栋/1单元/101 2026-03-01 2026-03-31 物业费")
            print("示例（默认本月）: python3 main.py list_refundable_bills 收费系统 小区 1栋/1单元/101")
            print("示例（默认本月，只退物业费）: python3 main.py list_refundable_bills 收费系统 小区 1栋/1单元/101 物业费")
        else:
            charge_system_name = sys.argv[2]
            community_name = sys.argv[3]
            keyword = sys.argv[4]

            # 处理可选参数：开始日期、结束日期、收费项目
            start_date_str = None
            end_date_str = None
            charge_item_name = None

            def is_date(s: str) -> bool:
                """简单判断是否是日期格式 YYYY-MM-DD"""
                return len(s) == 10 and '-' in s

            # len = 5 → 只有必填项：list_refundable_bills cs community keyword
            # len = 6 → 收费项目
            # len = 7 → 要么是 start end，要么就是不可能出现的组合
            # len = 8 → start end + charge_item

            if len(sys.argv) == 6:
                # 第5个参数是收费项目
                charge_item_name = sys.argv[5]
            elif len(sys.argv) == 7:
                arg1 = sys.argv[5]
                arg2 = sys.argv[6]
                if is_date(arg1) and is_date(arg2):
                    # 两个都是日期 → start end
                    start_date_str = arg1
                    end_date_str = arg2
                else:
                    # 否则第一个收费项目
                    charge_item_name = arg1
            elif len(sys.argv) >= 8:
                arg1 = sys.argv[5]
                arg2 = sys.argv[6]
                if is_date(arg1) and is_date(arg2):
                    # start end + charge_item
                    start_date_str = arg1
                    end_date_str = arg2
                    charge_item_name = sys.argv[7]

            list_refundable_bills_by_name(charge_system_name, community_name, keyword, start_date_str, end_date_str, charge_item_name)
    elif command == "confirm_refund":
        # 确认退款，处理用户选择
        if len(sys.argv) < 3:
            print("错误：请提供确认选项（yes/no 或序号）")
            print("用法: python3 main.py confirm_refund <yes/no/序号>")
            print("示例: python3 main.py confirm_refund yes")
            print("示例: python3 main.py confirm_refund 1")
            print("示例: python3 main.py confirm_refund 1,2")
        else:
            confirmation_input = sys.argv[2]
            confirm_refund(confirmation_input)
    elif command == "list_revocable_bills":
        # 查询可撤回已缴账单（智能匹配，两步完成）
        if len(sys.argv) < 5:
            print("错误：请提供收费系统名称、小区名称和房屋关键词")
            print("用法: python3 main.py list_revocable_bills <收费系统名称> <小区名称> <房屋关键词> [开始日期] [结束日期] [收费项目]")
            print("示例: python3 main.py list_revocable_bills 收费系统 小区 1栋/1单元/101")
            print("示例: python3 main.py list_revocable_bills 收费系统 小区 1栋/1单元/101 2026-03-01 2026-03-31")
            print("示例: python3 main.py list_revocable_bills 收费系统 小区 1栋/1单元/101 2026-03-01 2026-03-31 物业费")
        else:
            charge_system_name = sys.argv[2]
            community_name = sys.argv[3]
            keyword = sys.argv[4]
            if len(sys.argv) == 5:
                # 只有三个必选参数
                list_revocable_bills_by_name(charge_system_name, community_name, keyword)
            elif len(sys.argv) == 6:
                # 只有开始日期，没有结束日期和收费项目
                start_date_str = sys.argv[5]
                list_revocable_bills_by_name(charge_system_name, community_name, keyword, start_date_str)
            elif len(sys.argv) == 7:
                # start end，没有收费项目
                start_date_str = sys.argv[5]
                end_date_str = sys.argv[6]
                list_revocable_bills_by_name(charge_system_name, community_name, keyword, start_date_str, end_date_str)
            elif len(sys.argv) >= 8:
                # start end + charge_item
                start_date_str = sys.argv[5]
                end_date_str = sys.argv[6]
                charge_item_name = sys.argv[7]
                list_revocable_bills_by_name(charge_system_name, community_name, keyword, start_date_str, end_date_str, charge_item_name)
    elif command == "confirm_revoke":
        # 确认撤回，处理用户选择
        if len(sys.argv) < 3:
            print("错误：请提供确认选项（yes/no 或序号）")
            print("用法: python3 main.py confirm_revoke <yes/no/序号>")
            print("示例: python3 main.py confirm_revoke yes")
            print("示例: python3 main.py confirm_revoke 1")
            print("示例: python3 main.py confirm_revoke 1,2")
        else:
            confirmation_input = sys.argv[2]
            confirm_revoke(confirmation_input)
    elif command == "discount_bills":
        # 查询待优惠账单（推荐，智能匹配，两步完成）
        if len(sys.argv) < 6:
            print("错误：请提供收费系统名称、小区名称、房屋关键词和优惠金额")
            print("用法: python3 main.py discount_bills <收费系统名称> <小区名称> <房屋关键词> [开始日期] [结束日期] [收费项目] <优惠金额>")
            print("日期格式: YYYY-MM-DD（省略则默认本月）")
            print("示例（完整格式）: python3 main.py discount_bills 收费系统 小区 1栋/1单元/101 2026-03-01 2026-03-31 物业费 50")
            print("示例（默认本月）: python3 main.py discount_bills 收费系统 小区 1栋/1单元/101 物业费 50")
            print("示例（不指定收费项目）: python3 main.py discount_bills 收费系统 小区 1栋/1单元/101 50")
        else:
            charge_system_name = sys.argv[2]
            community_name = sys.argv[3]
            keyword = sys.argv[4]

            # 处理可选参数：开始日期、结束日期、收费项目、优惠金额
            start_date_str = None
            end_date_str = None
            charge_item_name = None
            discount_amount_yuan = None

            def is_date(s: str) -> bool:
                """简单判断是否是日期格式 YYYY-MM-DD"""
                return len(s) == 10 and '-' in s

            # 参数位置分析：
            # len = 5 → discount_bills cs community keyword discount_amount
            # len = 6 → discount_bills cs community keyword charge_item discount_amount
            # len = 7 → discount_bills cs community keyword start end discount_amount
            # len = 8 → discount_bills cs community keyword start end charge_item discount_amount

            if len(sys.argv) == 5:
                # 最少参数，理论上不会到这里，因为 len < 6 已经拦截了
                pass
            elif len(sys.argv) == 6:
                # 第5个参数可能是优惠金额（不指定收费项目，默认本月），也可能是收费项目
                arg = sys.argv[5]
                try:
                    discount_amount_yuan = float(arg)
                    # 不指定收费项目，默认本月
                    start_date_str = None
                    end_date_str = None
                    charge_item_name = None
                except ValueError:
                    # 这是收费项目，需要用户继续？不可能，因为优惠金额必须有
                    print("错误：必须提供优惠金额（最后一个参数）")
                    print("示例: python3 main.py discount_bills 收费系统 小区 1栋/1单元/101 物业费 50")
                    exit(1)
            elif len(sys.argv) == 7:
                arg1 = sys.argv[5]
                arg2 = sys.argv[6]
                if is_date(arg1) and is_date(arg2):
                    # start end discount_amount
                    try:
                        start_date_str = arg1
                        end_date_str = arg2
                        discount_amount_yuan = float(arg2)
                        charge_item_name = None
                    except ValueError:
                        print("错误：优惠金额必须是数字，请检查参数位置")
                        exit(1)
                else:
                    # charge_item discount_amount
                    try:
                        charge_item_name = arg1
                        discount_amount_yuan = float(arg2)
                        start_date_str = None
                        end_date_str = None
                    except ValueError:
                        print("错误：优惠金额必须是数字，请检查参数位置")
                        exit(1)
            elif len(sys.argv) >= 8:
                # 完整参数 start end charge_item discount_amount
                if is_date(sys.argv[5]) and is_date(sys.argv[6]):
                    start_date_str = sys.argv[5]
                    end_date_str = sys.argv[6]
                    charge_item_name = sys.argv[7] if len(sys.argv) > 7 else None
                    try:
                        discount_amount_yuan = float(sys.argv[8]) if len(sys.argv) > 8 else float(sys.argv[7])
                    except ValueError:
                        print("错误：优惠金额必须是数字，请检查参数位置")
                        exit(1)
                else:
                    print("错误：参数解析失败，请检查日期格式是否正确")
                    exit(1)

            discount_bills_by_name(charge_system_name, community_name, keyword, start_date_str, end_date_str, charge_item_name, discount_amount_yuan)
    elif command == "confirm_discount":
        # 确认优惠，处理用户选择
        if len(sys.argv) < 3:
            print("错误：请提供确认选项（yes/no 或序号）")
            print("用法: python3 main.py confirm_discount <yes/no/序号>")
            print("示例: python3 main.py confirm_discount yes")
            print("示例: python3 main.py confirm_discount 1")
            print("示例: python3 main.py confirm_discount 1,2")
        else:
            confirmation_input = sys.argv[2]
            confirm_discount(confirmation_input)
    elif command == "clear_late_money":
        # 查询待处理账单，准备设置违约金（通常清零）（推荐，智能匹配，两步完成）
        # 用法: clear_late_money <收费系统名称> <小区名称> <房屋关键词> [开始日期] [结束日期] [收费项目] [设置金额]
        # 默认设置金额为0（清零），默认时间范围为本月
        if len(sys.argv) < 5:
            print("错误：请提供收费系统名称、小区名称和房屋关键词")
            print("用法: python3 main.py clear_late_money <收费系统名称> <小区名称> <房屋关键词> [开始日期] [结束日期] [收费项目] [设置金额]")
            print("日期格式: YYYY-MM-DD（省略则默认本月）")
            print("设置金额省略则默认为 0（清零）")
            print("示例（清零全部账单违约金，默认本月）: python3 main.py clear_late_money 收费系统 小区 1栋/1单元/101")
            print("示例（清零物业费违约金，默认本月）: python3 main.py clear_late_money 收费系统 小区 1栋/1单元/101 物业费")
            print("示例（完整格式，清零指定时间范围物业费）: python3 main.py clear_late_money 收费系统 小区 1栋/1单元/101 2026-03-01 2026-03-31 物业费")
            print("示例（设置指定金额）: python3 main.py clear_late_money 收费系统 小区 1栋/1单元/101 物业费 10")
        else:
            charge_system_name = sys.argv[2]
            community_name = sys.argv[3]
            keyword = sys.argv[4]

            # 处理可选参数：开始日期、结束日期、收费项目、设置金额
            start_date_str = None
            end_date_str = None
            charge_item_name = None
            set_amount_yuan = 0.0  # 默认0表示清零

            def is_date(s: str) -> bool:
                """简单判断是否是日期格式 YYYY-MM-DD"""
                return len(s) == 10 and '-' in s

            # len = 5 → clear_late_money cs community keyword
            # len = 6 → clear_late_money cs community keyword charge_item
            #             or clear_late_money cs community keyword set_amount
            # len = 7 → clear_late_money cs community keyword start end
            #             or clear_late_money cs community keyword charge_item set_amount
            # len = 8 → clear_late_money cs community keyword start end charge_item
            # len = 9 → clear_late_money cs community keyword start end charge_item set_amount

            if len(sys.argv) == 5:
                # 只有三个必选参数，默认全部，清零
                pass
            elif len(sys.argv) == 6:
                # 第5个参数可能是收费项目 或者 金额
                arg = sys.argv[5]
                try:
                    set_amount_yuan = float(arg)
                    # 用户直接指定了金额，不指定收费项目，默认本月
                    start_date_str = None
                    end_date_str = None
                    charge_item_name = None
                except ValueError:
                    # 这是收费项目，默认金额0
                    charge_item_name = arg
                    start_date_str = None
                    end_date_str = None
            elif len(sys.argv) == 7:
                arg1 = sys.argv[5]
                arg2 = sys.argv[6]
                if is_date(arg1) and is_date(arg2):
                    # start end，默认金额0
                    start_date_str = arg1
                    end_date_str = arg2
                    charge_item_name = None
                else:
                    # charge_item set_amount
                    try:
                        charge_item_name = arg1
                        set_amount_yuan = float(arg2)
                        start_date_str = None
                        end_date_str = None
                    except ValueError:
                        print("错误：最后一个参数必须是数字（设置金额），请检查参数位置")
                        exit(1)
            elif len(sys.argv) == 8:
                arg1 = sys.argv[5]
                arg2 = sys.argv[6]
                if is_date(arg1) and is_date(arg2):
                    # start end charge_item，默认金额0
                    start_date_str = arg1
                    end_date_str = arg2
                    charge_item_name = sys.argv[7]
                else:
                    print("错误：参数解析失败，请检查日期格式是否正确")
                    exit(1)
            elif len(sys.argv) >= 9:
                # 完整参数 start end charge_item set_amount
                if is_date(sys.argv[5]) and is_date(sys.argv[6]):
                    start_date_str = sys.argv[5]
                    end_date_str = sys.argv[6]
                    charge_item_name = sys.argv[7]
                    try:
                        set_amount_yuan = float(sys.argv[8])
                    except ValueError:
                        print("错误：最后一个参数必须是数字（设置金额），请检查参数位置")
                        exit(1)
                else:
                    print("错误：参数解析失败，请检查日期格式是否正确")
                    exit(1)

            clear_late_money_by_name(charge_system_name, community_name, keyword, start_date_str, end_date_str, charge_item_name, set_amount_yuan)
    elif command == "confirm_clear_late_money":
        # 确认设置违约金，处理用户选择
        if len(sys.argv) < 3:
            print("错误：请提供确认选项（yes/no 或序号）")
            print("用法: python3 main.py confirm_clear_late_money <yes/no/序号>")
            print("示例: python3 main.py confirm_clear_late_money yes")
            print("示例: python3 main.py confirm_clear_late_money 1")
            print("示例: python3 main.py confirm_clear_late_money 1,2")
        else:
            confirmation_input = sys.argv[2]
            confirm_clear_late_money(confirmation_input)
    elif command == "generate_collection_url":
        # 生成单个房屋催缴链接（推荐，智能匹配，一步完成）
        if len(sys.argv) < 5:
            print("错误：请提供收费系统名称、小区名称和房屋关键词")
            print("用法: python3 main.py generate_collection_url <收费系统名称> <小区名称> <房屋关键词>")
            print("示例: python3 main.py generate_collection_url 收费系统 小区 1栋/1单元/101")
        else:
            charge_system_name = sys.argv[2]
            community_name = sys.argv[3]
            keyword = sys.argv[4]
            generate_collection_url_by_name(charge_system_name, community_name, keyword)
    elif command == "generate_charge_work_order":
        # 生成单个房屋催缴工单（推荐，智能匹配，两步完成）
        if len(sys.argv) < 5:
            print("错误：请提供收费系统名称、小区名称和房屋关键词")
            print("用法: python3 main.py generate_charge_work_order <收费系统名称> <小区名称> <房屋关键词>")
            print("示例: python3 main.py generate_charge_work_order 收费系统 小区 1栋/1单元/101")
        else:
            charge_system_name = sys.argv[2]
            community_name = sys.argv[3]
            keyword = sys.argv[4]
            generate_charge_work_order_by_name(charge_system_name, community_name, keyword)
    elif command == "create_phone_call_log":
        # 创建单个房屋电话催缴记录（推荐，智能匹配，一步完成）
        if len(sys.argv) < 5:
            print("错误：请提供收费系统名称、小区名称和房屋关键词")
            print("用法: python3 main.py create_phone_call_log <收费系统名称> <小区名称> <房屋关键词>")
            print("示例: python3 main.py create_phone_call_log 收费系统 小区 1栋/1单元/101")
        else:
            charge_system_name = sys.argv[2]
            community_name = sys.argv[3]
            keyword = sys.argv[4]
            create_phone_call_log_by_name(charge_system_name, community_name, keyword)
    elif command == "confirm_charge_work_order":
        # 确认生成催缴工单，处理代办人选择
        if len(sys.argv) < 3:
            print("错误：请提供选择的代办人序号")
            print("用法: python3 main.py confirm_charge_work_order <序号>")
            print("示例: python3 main.py confirm_charge_work_order 1")
            print("示例（多选）: python3 main.py confirm_charge_work_order 1,2")
        else:
            selection_input = sys.argv[2]
            confirm_charge_work_order(selection_input)
    elif command == "collect_cash_pledge":
        # 收取押金（推荐，智能匹配，两步完成）
        # 用法: collect_cash_pledge <收费系统名称> <小区名称> <房屋关键词> <押金名称> <金额> [支付方式]
        # 金额单位：元
        # 支付方式默认：现金
        if len(sys.argv) < 7:
            print("错误：请提供收费系统名称、小区名称、房屋关键词、押金名称和金额")
            print("用法: python3 main.py collect_cash_pledge <收费系统名称> <小区名称> <房屋关键词> <押金名称> <金额> [支付方式]")
            print("示例（完整格式）: python3 main.py collect_cash_pledge 收费系统 小区 1栋/1单元/101 装修押金 1000 现金")
            print("示例（默认支付方式）: python3 main.py collect_cash_pledge 收费系统 小区 1栋/1单元/101 装修押金 1000")
        else:
            charge_system_name = sys.argv[2]
            community_name = sys.argv[3]
            keyword = sys.argv[4]
            pledge_name = sys.argv[5]

            try:
                amount_yuan = float(sys.argv[6])
            except ValueError:
                print("错误：金额必须是数字，请检查参数位置")
                exit(1)

            pay_type_name = sys.argv[7] if len(sys.argv) >= 8 else None
            collect_cash_pledge_by_name(charge_system_name, community_name, keyword, pledge_name, amount_yuan, pay_type_name)
    elif command == "confirm_collect_cash_pledge":
        # 确认收取押金，执行操作
        if len(sys.argv) < 3:
            print("错误：请提供确认选项（yes/no）")
            print("用法: python3 main.py confirm_collect_cash_pledge <yes/no>")
            print("示例: python3 main.py confirm_collect_cash_pledge yes")
            print("示例: python3 main.py confirm_collect_cash_pledge no")
        else:
            confirmation_input = sys.argv[2]
            confirm_collect_cash_pledge(confirmation_input)
    else:
        print("错误：未知的指令或参数不足")
        print("可用指令:")
        print("  get_my_team - 查看我加入的团队列表")
        print("  logout - 登出马克账号")
        print("  list_charge_systems - 列出可用的收费系统")
        print("  search_community <收费系统名称> <小区关键词> - 搜索小区")
        print("  get_arrears <收费系统名称> <小区名称> - 通过名称查询欠费")
        print("  get_current_year_arrears <收费系统名称> <小区名称> - 通过名称查询本年度物业费欠费")
        print("  get_custom_range_arrears <收费系统名称> <小区名称> <开始日期> <结束日期> - 自定义时间范围查询欠费")
        print("  get_today_stats <收费系统名称> <小区名称> - 查询小区今日收入统计")
        print("  get_custom_range_stats <收费系统名称> <小区名称> <开始日期> <结束日期> - 查询小区自定义时间范围收入统计")
        print("  get_monthly_expense <收费系统名称> <小区名称> - 查询小区本月支出统计")
        print("  get_collection_rate <收费系统名称> <小区名称> - 查询小区本月收缴率统计")
        print("  get_arrear_households <收费系统名称> <小区名称> - 查询小区欠费户数统计")
        print("  get_household_arrears <收费系统名称> <小区名称> <关键词> - 查询房屋/楼栋/单元欠费")
        print("  get_household_specific_arrears <收费系统名称> <小区名称> <房屋关键词> <开始日期> <结束日期> <费用类型> - 查询特定房屋指定时间范围和费用类型欠费")
        print("  get_household_fee_type_arrears <收费系统名称> <小区名称> <房屋关键词> <费用类型> - 查询特定房屋指定费用类型欠费（不限时间）")
        print("  get_current_user_info - 查询当前登录用户信息（无需参数）")
        print("  get_current_user_info <收费系统名称> <小区名称> - 查询当前登录用户完整信息")
        print("  send_wechat_reminder <收费系统名称> <小区名称> - 发送微信缴费提醒（推荐）")
        print("  meter_reading <收费系统名称> <小区名称> <房屋关键词> <仪器类型> <读数> [备注] - 智能抄表入口")
        print("  get_meter_status <收费系统名称> <小区名称> <房屋关键词> <仪器类型> - 查询电表/水表当前读数")
        print("  send_community_wechat_reminder <小区ID> - 通过小区ID发送微信缴费提醒")
        print("  get_community_total_arrears <小区ID> - 通过ID查询欠费（旧版）")
        print("  get_community_current_year_arrears <小区ID> - 通过ID查询本年度物业费欠费")
        print("  get_community_today_stats <小区ID> - 通过ID查询今日收入统计")
        print("  get_community_custom_range_stats <小区ID> <开始时间戳> <结束时间戳> - 通过ID查询自定义时间范围收入统计")
        print("  get_community_monthly_expense <小区ID> - 通过ID查询本月支出统计")
        print("  get_community_collection_rate <小区ID> <收费系统ID> - 通过ID查询本月收缴率统计")
        print("  get_community_arrear_households <小区ID> - 通过ID查询欠费户数统计")
        print("  get_community_cs_init_info <小区ID> <收费系统ID> - 通过ID查询初始化信息")
        print("  send_sms_reminder <收费系统名称> <小区名称> <房屋关键词> - 单个房屋短信催缴（推荐，智能匹配）")
        print("  confirm_sms_reminder <yes/no/序号> - 确认短信催缴发送处理")
        print("  send_single_house_sms_reminder <小区ID> <房屋ID> <业主ID逗号分隔> <账单ID逗号分隔> - 单个房屋短信催缴（ID模式，备用）")
        print("  collect_payment <收费系统名称> <小区名称> <房屋关键词> [开始日期] [结束日期] [支付方式] - 对特定房屋指定时间范围的账单进行收款（推荐，智能匹配）")
        print("  confirm_payment <yes/no/序号> - 确认收款，处理用户选择")
        print("  list_refundable_bills <收费系统名称> <小区名称> <房屋关键词> [开始日期] [结束日期] [收费项目] - 查询指定房屋已缴可退款账单（推荐，智能匹配，两步完成）")
        print("  confirm_refund <yes/no/序号> - 确认退款，处理用户选择")
        print("  list_revocable_bills <收费系统名称> <小区名称> <房屋关键词> [开始日期] [结束日期] [收费项目] - 查询指定房屋已缴可撤回账单（推荐，智能匹配，两步完成）")
        print("  confirm_revoke <yes/no/序号> - 确认撤回已缴账单，处理用户选择")
        print("  generate_collection_url <收费系统名称> <小区名称> <房屋关键词> - 生成房屋所有欠费账单的催缴链接（一步完成）")
        print("  generate_charge_work_order <收费系统名称> <小区名称> <房屋关键词> - 生成催缴工单（推荐，智能匹配，两步完成）")
        print("  confirm_charge_work_order <序号> - 确认选择代办人，生成催缴工单")
        print("  create_phone_call_log <收费系统名称> <小区名称> <房屋关键词> - 创建电话催缴记录（一步完成）")
        print("  discount_bills <收费系统名称> <小区名称> <房屋关键词> [开始日期] [结束日期] [收费项目] <优惠金额> - 查询待优惠账单（推荐，智能匹配，两步完成）")
        print("  confirm_discount <yes/no/序号> - 确认优惠，处理用户选择")
        print("  clear_late_money <收费系统名称> <小区名称> <房屋关键词> [开始日期] [结束日期] [收费项目] [设置金额] - 设置违约金（默认清零，推荐，智能匹配，两步完成）")
        print("  confirm_clear_late_money <yes/no/序号> - 确认设置违约金，处理用户选择")
        print("  collect_cash_pledge <收费系统名称> <小区名称> <房屋关键词> <押金名称> <金额> [支付方式] - 收取押金（装修押金、水电押金等，推荐，智能匹配，两步完成）")
        print("  confirm_collect_cash_pledge <yes/no> - 确认收取押金，处理用户选择")
