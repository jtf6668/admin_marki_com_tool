import os
import sys
import time
import json
import socket
import threading
from logger import logger
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from utils import SessionManager

def find_available_port(start_port=8080, max_attempts=100):
    """从指定端口开始，查找第一个可用的端口"""
    port = start_port
    while port < start_port + max_attempts:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                # 尝试绑定端口
                s.bind(('localhost', port))
                logger.info(f"找到可用端口: {port}")
                return port
            except socket.error:
                port += 1
    raise IOError("无法找到可用的本地端口")

def auto_shutdown(server, timeout=300):
    """5分钟后如果没有登录成功，自动关闭服务器"""
    time.sleep(timeout)
    print("AUTH_TIMEOUT: 授权超时，自动关闭。")
    server.shutdown()

callback_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>授权成功</title>
                <style>
                    body { font-family: -apple-system, sans-serif; text-align: center; padding-top: 50px; background: #f4f7f9; }
                    .card { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); display: inline-block; }
                    h1 { color: #2ecc71; }
                    .timer { color: #e67e22; font-weight: bold; font-size: 1.2em; }
                    .hint { color: #7f8c8d; font-size: 0.9em; margin-top: 20px; }
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>✅ 授权成功</h1>
                    <p>已成功获取凭证，请回到终端继续操作。</p>
                    <p>本窗口将在 <span id="countdown" class="timer">5</span> 秒后尝试自动关闭...</p>
                    <p class="hint">如果窗口未自动关闭，您可以手动关闭此页面。</p>
                </div>

                <script>
                    let seconds = 5;
                    const el = document.getElementById('countdown');
                    const timer = setInterval(() => {
                        seconds--;
                        el.innerText = seconds;
                        if (seconds <= 0) {
                            clearInterval(timer);
                            window.close(); // 尝试关闭窗口
                        }
                    }, 1000);
                </script>
            </body>
            </html>
            """

session_mgr = SessionManager()

class CallbackHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        logger.info("%s - - [%s] %s" % (
            self.client_address[0],
            self.log_date_time_string(),
            format % args
        ))

    def do_GET(self):

        def send_response_with_body(self, code, body, content_type="text/html; charset=utf-8"):
            body_bytes = body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-type", content_type)
            self.send_header("Content-Length", str(len(body_bytes)))
            self.end_headers()
            try:
                self.wfile.write(body_bytes)
            except BrokenPipeError:
                logger.warning("客户端已断开，无法写入响应。")

        try:
            logger.info(f"收到回调请求: {self.path} 来自 {self.client_address}")

            # 1. 解析请求的 URL
            parsed_url = urlparse(self.path)

            if parsed_url.path != "/callback":
                logger.warning(f"收到未知路径的请求: {self.path}")
                send_response_with_body(self, 404, "Not Found: 仅支持 /callback 路径")
                return

            query = parse_qs(urlparse(self.path).query)

            data_str = query.get("data", [None])[0]

            if data_str:
                try:
                    # 4. 将 JSON 字符串解析为字典
                    callback_data = json.loads(data_str)
                    
                    # 5. 提取 ck 部分（这是你要的 cookie 字典）
                    ck_content = callback_data.get("ck")
                    code = callback_data.get("code")

                    if code == "0" and ck_content:
                        # 使用工具类保存完整的 callback_data 或只保存 ck 部分
                        # 建议保存整个字典，以后可能需要 uid 等信息
                        session_mgr.save_session(callback_data)

                        # 授权成功，清理 PID 和 URL 缓存
                        session_mgr.clear_server_info()
                        
                        # 返回成功响应
                        send_response_with_body(self, 200, callback_html)
                        
                        # 通知服务器关闭，延迟3秒确保响应已发出
                        def delayed_shutdown():
                            time.sleep(5)
                            try:
                                self.server.shutdown()
                            except BrokenPipeError:
                                logger.warning("shutdown时Broken pipe，客户端已断开。")
                            except Exception as e:
                                logger.error(f"shutdown时发生异常: {e}")
                        threading.Thread(target=delayed_shutdown).start()

                    else:
                        self.send_response_with_body(self, 400, f"Login failed or missing cookies. Code: {code}")
                except json.JSONDecodeError:
                    self.send_response_with_body(self, 400, "Invalid JSON data format")

            else:
                self.send_response_with_body(self, 400, "Missing 'data' parameter in callback")

        except Exception as e:
            logger.error(f"do_GET异常: {e}")
            self.send_response_with_body(self, 500, "Internal Server Error")

if __name__ == "__main__":

    try:
        # 1. 查找可用端口
        port = find_available_port(8080)

        logger.info(f"授权服务器启动，监听端口: {port}")

        # 2. 告诉主进程我们最终用了哪个端口（通过标准输出）
        print(f"REAL_PORT:{port}")
        sys.stdout.flush() # 确保主进程能立即读到

        logger.info(f"授权服务器正在运行，等待用户登录...")
        
        # 3. 启动服务
        server = HTTPServer(("localhost", port), CallbackHandler)
        threading.Thread(target=auto_shutdown, args=(server,), daemon=True).start()
        server.serve_forever()
    except BrokenPipeError as e:
        logger.warning(f"主线程Broken pipe: {str(e)} (通常是客户端提前断开，不影响授权流程)")
    except Exception as e:
        print(f"ERROR:{str(e)}")
        logger.error(f"授权服务器启动失败: {str(e)}")