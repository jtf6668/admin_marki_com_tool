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


API_BASE_URL = "https://admin-api.markiapp.com"
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

    headers = get_headers_with_cookies(ck_dict, {"communityid": community_id})

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


def get_community_total_arrears(community_id: str, start_time: int = None, end_time: int = None, charge_system_id: str = None) -> str:
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

    headers = get_headers_with_cookies(ck_dict, {"communityid": community_id})

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

    headers = get_headers_with_cookies(ck_dict, {"communityid": community_id})

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


def get_ledger_list_v2(community_id: str, cs_id: str, year_month: str) -> dict:
    """
    获取小区指定月份的台账信息

    Args:
        community_id: 小区ID
        cs_id: 收费系统ID
        year_month: 年月 (YYYY-MM格式)

    Returns:
        台账数据字典
    """
    import random
    ck_dict = ensure_authenticated()
    if not ck_dict:
        return None

    headers = get_headers_with_cookies(ck_dict, {"communityid": community_id})

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


def format_collection_rate_stats(community_name: str, ledger_data: dict, year_month: str) -> str:
    """
    格式化收缴率统计数据

    Args:
        community_name: 小区名称
        ledger_data: 台账数据
        year_month: 年月 (YYYY-MM格式)

    Returns:
        格式化后的统计文本
    """
    year_month_dt = datetime.strptime(year_month, "%Y-%m")
    month_str = year_month_dt.strftime("%Y年%m月")

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


def get_community_collection_rate(community_id: str, cs_id: str, community_name: str = None) -> str:
    """
    获取小区本月收缴率统计

    Args:
        community_id: 小区ID
        cs_id: 收费系统ID
        community_name: 小区名称（可选）

    Returns:
        统计结果文本
    """
    year_month = get_current_month_year_range()
    ledger_data = get_ledger_list_v2(community_id, cs_id, year_month)

    if ledger_data is None:
        return "获取台账信息失败"

    if not community_name:
        community_name = "该小区"

    output = format_collection_rate_stats(community_name, ledger_data, year_month)
    logger.info(f"成功获取小区 {community_id} 的本月收缴率统计")
    print(f"返回数据：{output}")
    return output


def get_collection_rate(charge_system_name=None, community_name=None):
    """
    通过名称查询小区本月收缴率统计（智能模式）

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
        get_community_collection_rate(str(comm_id), str(charge_system_id), comm_name)
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

    headers = get_headers_with_cookies(ck_dict, {"communityid": community_id})

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

    headers = get_headers_with_cookies(ck_dict, {"communityid": community_id})

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

    headers = get_headers_with_cookies(ck_dict, {"communityid": community_id})

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

    headers = get_headers_with_cookies(ck_dict, {"communityid": community_id})

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

    headers = get_headers_with_cookies(ck_dict, {"communityid": community_id})

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

    headers = get_headers_with_cookies(ck_dict, {"communityid": community_id})

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

    headers = get_headers_with_cookies(ck_dict, {"communityid": community_id})

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
            print("用法: python3 main.py get_collection_rate <收费系统名称> <小区名称>")
        else:
            charge_system_name = sys.argv[2]
            community_name = sys.argv[3]
            get_collection_rate(charge_system_name, community_name)
    elif command == "get_community_collection_rate":
        # 通过小区ID和收费系统ID查询本月收缴率统计
        if len(sys.argv) < 4:
            print("错误：请提供小区ID和收费系统ID参数")
            print("用法: python3 main.py get_community_collection_rate <小区ID> <收费系统ID>")
        else:
            community_id = sys.argv[2]
            cs_id = sys.argv[3]
            get_community_collection_rate(community_id, cs_id)
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
