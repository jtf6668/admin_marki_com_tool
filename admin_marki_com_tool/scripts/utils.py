import os
import json

class SessionManager:
    def __init__(self):
        # 统一获取 Skill 根目录 (scripts/ 的上一级)
        self.skill_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.cookie_path = os.path.join(self.skill_root, "session.json")
        self.pid_path = os.path.join(self.skill_root, "server.pid") # 新增 PID 文件路径
        self.url_cache_path = os.path.join(self.skill_root, "last_url.txt")

    def get_session(self):
        """读取 Session 数据，如果不存在或损坏则返回 None"""
        if not os.path.exists(self.cookie_path):
            return None
        try:
            with open(self.cookie_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def save_session(self, data):
        """保存 Session 数据"""
        try:
            # 确保根目录存在（虽然通常已存在）
            os.makedirs(self.skill_root, exist_ok=True)
            with open(self.cookie_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"保存 Session 失败: {e}")
            return False

    def clear_session(self):
        """删除 Session 文件（用于登出或过期处理）"""
        if os.path.exists(self.cookie_path):
            os.remove(self.cookie_path)

    def get_cookies_dict(self):
        """快速获取 requests 库可用的 cookies 字典"""
        session = self.get_session()
        if session and "ck" in session:
            # 这里兼容你接口返回的 ck 字段
            return session["ck"] if isinstance(session["ck"], dict) else {}
        return {}
    
    def is_server_running(self):
        """检查授权服务器是否已在运行"""
        if not os.path.exists(self.pid_path):
            return False
        try:
            with open(self.pid_path, 'r') as f:
                pid = int(f.read().strip())
            # 检查该 PID 是否真的在运行
            import psutil
            return psutil.pid_exists(pid)
        except:
            return False
        
    def save_pid(self, pid):
        with open(self.pid_path, 'w') as f:
            f.write(str(pid))

    def clear_pid(self):
        if os.path.exists(self.pid_path):
            os.remove(self.pid_path)

    # --- 进程与 URL 缓存管理 ---
    def get_running_server_url(self):
        """检查服务器是否在运行，如果在，返回缓存的 URL"""
        if os.path.exists(self.pid_path) and os.path.exists(self.url_cache_path):
            try:
                with open(self.pid_path, 'r') as f:
                    pid = int(f.read().strip())
                
                # 检查进程是否真的存在
                if psutil.pid_exists(pid):
                    with open(self.url_cache_path, 'r') as f:
                        return f.read().strip()
            except:
                pass
        return None

    def save_server_info(self, pid, url):
        """记录进程号和生成的 URL"""
        with open(self.pid_path, 'w') as f:
            f.write(str(pid))
        with open(self.url_cache_path, 'w') as f:
            f.write(url)

    def clear_server_info(self):
        """清理进程记录"""
        for path in [self.pid_path, self.url_cache_path]:
            if os.path.exists(path):
                os.remove(path)