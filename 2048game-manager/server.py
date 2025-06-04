# server.py
import mysql.connector
from mysql.connector import Error
import hashlib
from datetime import datetime, timedelta
import json
import socket
import threading
import signal
import sys

#服务器监听的ip和端口
host = "127.0.0.1"
#host = "10.29.107.164"
port = 20480

class GameServer2048:
    def __init__(self, host = host, port = port):
        self.host = host
        self.port = port
        self.server_socket = None
        self.db_connection = None
        self.running = True
        self.setup_database()
        
        # 添加残局对战相关属性
        self.battle_rooms = {}  # 存储对战房间信息
        self.battle_requests = {}  # 存储对战请求
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        
    def handle_shutdown(self, signum, frame):
        """处理关闭信号"""
        print("\n正在关闭服务器...")
        self.running = False
        if self.server_socket:
            # 创建一个临时连接来解除accept的阻塞
            try:
                temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                temp_socket.connect((self.host, self.port))
                temp_socket.close()
            except:
                pass
            self.server_socket.close()
        if self.db_connection:
            self.db_connection.close()
        print("服务器已关闭")
        sys.exit(0)
        
    def setup_database(self):
        """设置数据库连接"""
        try:
            self.db_connection = mysql.connector.connect(
                host='127.0.0.1',
                port=3306,
                database='game2048',
                user='manager2048',
                password='2147483647'
            )
            print("成功连接到MySQL数据库")
        except Error as e:
            print(f"数据库连接错误: {e}")
            raise

    def hash_password(self, password):
        """密码加密"""
        return hashlib.sha256(password.encode()).hexdigest()[:50]

    def create_session(self, uid):
        """创建用户会话"""
        cursor = self.db_connection.cursor()
        session_id = hashlib.sha256(f"{uid}{datetime.now().timestamp()}".encode()).hexdigest()
        created_at = datetime.now()
        expires_at = created_at + timedelta(hours=24)
        
        try:
            cursor.execute(
                "INSERT INTO session (session_id, uid, created_at, expires_at) VALUES (%s, %s, %s, %s)",
                (session_id, uid, created_at, expires_at)
            )
            self.db_connection.commit()
            return session_id
        except Error as e:
            print(f"创建会话错误: {e}")
            return None
        finally:
            cursor.close()

    def verify_session(self, session_id):
        """验证会话"""
        cursor = self.db_connection.cursor()
        try:
            cursor.execute(
                "SELECT uid FROM session WHERE session_id = %s AND expires_at > NOW()",
                (session_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else None
        finally:
            cursor.close()

    def register_user(self, username, password, is_admin=False):
        """注册新用户"""
        cursor = self.db_connection.cursor()
        try:
            cursor.execute("SELECT uid FROM user WHERE username = %s", (username,))
            if cursor.fetchone():
                return {'status': 'error', 'message': '用户名已存在'}

            hashed_password = self.hash_password(password)
            cursor.execute(
                "INSERT INTO user (username, password, is_admin) VALUES (%s, %s, %s)",
                (username, hashed_password, is_admin)
            )
            self.db_connection.commit()
            return {'status': 'success', 'message': '注册成功'}
        except Error as e:
            print(f"注册错误: {e}")
            return {'status': 'error', 'message': '服务器错误'}
        finally:
            cursor.close()

    def login(self, username, password, user_type='user'):
        """用户登录"""
        cursor = self.db_connection.cursor()
        try:
            hashed_password = self.hash_password(password)
            cursor.execute(
                "SELECT uid, is_admin FROM user WHERE username = %s AND password = %s AND blocked = FALSE",
                (username, hashed_password)
            )
            result = cursor.fetchone()
            
            if result:
                uid, is_admin = result
                if (user_type == 'admin' and not is_admin) or (user_type == 'user' and is_admin):
                    return {'status': 'error', 'message': '用户类型不匹配'}
                
                session_id = self.create_session(uid)
                return {
                    'status': 'success',
                    'session_id': session_id,
                    'uid': uid
                }
            return {'status': 'error', 'message': '用户名或密码错误 或者 已被封禁'}
        except Error as e:
            print(f"登录错误: {e}")
            return {'status': 'error', 'message': '服务器错误'}
        finally:
            cursor.close()

    def logout(self, session_id):
        """用户注销"""
        cursor = self.db_connection.cursor()
        try:
            cursor.execute("DELETE FROM session WHERE session_id = %s", (session_id,))
            self.db_connection.commit()
            return {'status': 'success', 'message': '注销成功'}
        except Error as e:
            print(f"注销错误: {e}")
            return {'status': 'error', 'message': '服务器错误'}
        finally:
            cursor.close()

    def get_user_list(self, search_term=None):
        """获取用户列表"""
        cursor = self.db_connection.cursor()
        try:
            if search_term:
                cursor.execute(
                    "SELECT uid, username, blocked, is_admin FROM user WHERE LOWER(username) LIKE %s AND is_admin = FALSE",
                    (f"%{search_term.lower()}%",)
                )
            else:
                cursor.execute("SELECT uid, username, blocked, is_admin FROM user WHERE is_admin = FALSE")
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'uid': row[0],
                    'username': row[1],
                    'blocked': bool(row[2]),
                    'is_admin': bool(row[3])
                })
            return {'status': 'success', 'users': users}
        except Error as e:
            print(f"获取用户列表错误: {e}")
            return {'status': 'error', 'message': '服务器错误'}
        finally:
            cursor.close()

    def ban_user(self, uid):
        """封禁用户"""
        cursor = self.db_connection.cursor()
        try:
            # 首先检查用户是否为管理员
            cursor.execute("SELECT is_admin FROM user WHERE uid = %s", (uid,))
            result = cursor.fetchone()
            if not result:
                return {'status': 'error', 'message': '用户不存在'}
            if result[0]:
                return {'status': 'error', 'message': '不能封禁管理员账号'}
                
            cursor.execute("UPDATE user SET blocked = TRUE WHERE uid = %s", (uid,))
            self.db_connection.commit()
            return {'status': 'success', 'message': '用户已封禁'}
        except Error as e:
            print(f"封禁用户错误: {e}")
            return {'status': 'error', 'message': '服务器错误'}
        finally:
            cursor.close()

    def unban_user(self, uid):
        """解封用户"""
        cursor = self.db_connection.cursor()
        try:
            # 首先检查用户是否为管理员
            cursor.execute("SELECT is_admin FROM user WHERE uid = %s", (uid,))
            result = cursor.fetchone()
            if not result:
                return {'status': 'error', 'message': '用户不存在'}
            if result[0]:
                return {'status': 'error', 'message': '不能解封管理员账号'}
                
            cursor.execute("UPDATE user SET blocked = FALSE WHERE uid = %s", (uid,))
            self.db_connection.commit()
            return {'status': 'success', 'message': '用户已解封'}
        except Error as e:
            print(f"解封用户错误: {e}")
            return {'status': 'error', 'message': '服务器错误'}
        finally:
            cursor.close()

    def save_record(self, session_id, score, steps):
        """保存游戏记录"""
        cursor = self.db_connection.cursor()
        try:
            # 验证会话
            uid = self.verify_session(session_id)
            if not uid:
                return {'status': 'error', 'message': '无效的会话'}
            
            # 保存记录
            cursor.execute(
                "INSERT INTO record (uid, created_at, score, step) VALUES (%s, NOW(), %s, %s)",
                (uid, score, steps)
            )
            self.db_connection.commit()
            return {'status': 'success', 'message': '记录保存成功'}
        except Error as e:
            print(f"保存记录错误: {e}")
            return {'status': 'error', 'message': '服务器错误'}
        finally:
            cursor.close()

    def get_records(self, session_id):
        """获取用户游戏记录"""
        cursor = self.db_connection.cursor()
        try:
            # 验证会话
            uid = self.verify_session(session_id)
            if not uid:
                return {'status': 'error', 'message': '无效的会话'}
            
            # 获取最近10条记录
            cursor.execute(
                "SELECT created_at, score, step FROM record WHERE uid = %s ORDER BY created_at DESC LIMIT 10",
                (uid,)
            )
            
            records = []
            for row in cursor.fetchall():
                records.append({
                    'created_at': row[0].strftime('%Y-%m-%d %H:%M:%S'),
                    'score': row[1],
                    'steps': row[2]
                })
            
            return {'status': 'success', 'records': records}
        except Error as e:
            print(f"获取记录错误: {e}")
            return {'status': 'error', 'message': '服务器错误'}
        finally:
            cursor.close()

    def get_leaderboard(self):
        """获取排行榜前五名"""
        cursor = self.db_connection.cursor()
        try:
            # 获取前五名记录，按分数降序，步数升序排序
            cursor.execute("""
                SELECT u.username, r.score, r.step, r.created_at 
                FROM record r 
                JOIN user u ON r.uid = u.uid 
                ORDER BY r.score DESC, r.step ASC 
                LIMIT 5
            """)
            
            leaderboard = []
            for row in cursor.fetchall():
                leaderboard.append({
                    'username': row[0],
                    'score': row[1],
                    'steps': row[2],
                    'created_at': row[3].strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return {'status': 'success', 'leaderboard': leaderboard}
        except Error as e:
            print(f"获取排行榜错误: {e}")
            return {'status': 'error', 'message': '服务器错误'}
        finally:
            cursor.close()

    def create_battle_room(self, uid1, uid2):
        """创建对战房间"""
        cursor = self.db_connection.cursor()
        try:
            room_id = hashlib.sha256(f"{uid1}{uid2}{datetime.now().timestamp()}".encode()).hexdigest()[:8]
            cursor.execute(
                "INSERT INTO battle_room (room_id, uid1, uid2, started, created_at) VALUES (%s, %s, %s, %s, %s)",
                (room_id, uid1, uid2, False, datetime.now())
            )
            self.db_connection.commit()
            return room_id
        except Error as e:
            print(f"创建对战房间错误: {e}")
            return None
        finally:
            cursor.close()

    def get_battle_room(self, room_id):
        """获取对战房间信息"""
        cursor = self.db_connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT * FROM battle_room WHERE room_id = %s",
                (room_id,)
            )
            return cursor.fetchone()
        finally:
            cursor.close()

    def update_battle_state(self, room_id, uid, state):
        """更新对战状态"""
        cursor = self.db_connection.cursor()
        try:
            # 检查房间是否存在
            cursor.execute("SELECT room_id FROM battle_room WHERE room_id = %s", (room_id,))
            if not cursor.fetchone():
                return {'status': 'error', 'message': '房间不存在'}

            # 检查用户是否在房间中
            cursor.execute("""
                SELECT uid1, uid2 FROM battle_room 
                WHERE room_id = %s AND (uid1 = %s OR uid2 = %s)
            """, (room_id, uid, uid))
            if not cursor.fetchone():
                return {'status': 'error', 'message': '用户不在房间中'}

            # 更新或插入状态
            try:
                current_time = datetime.now()
                cursor.execute("""
                    INSERT INTO battle_state (room_id, uid, score, steps, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    score = VALUES(score),
                    steps = VALUES(steps),
                    updated_at = VALUES(updated_at)
                """, (room_id, uid, state['score'], state['steps'], current_time))
                
                self.db_connection.commit()
                return {
                    'status': 'success',
                    'message': '状态更新成功',
                    'updated_at': current_time.strftime('%Y-%m-%d %H:%M:%S')
                }
            except Error as e:
                self.db_connection.rollback()
                print(f"更新对战状态数据库错误: {e}")
                return {'status': 'error', 'message': '数据库更新失败'}
            
        except Error as e:
            print(f"更新对战状态错误: {e}")
            return {'status': 'error', 'message': '服务器错误'}
        finally:
            cursor.close()

    def get_battle_state(self, room_id, uid):
        """获取对战状态"""
        cursor = self.db_connection.cursor(dictionary=True)
        try:
            # 获取房间信息
            cursor.execute("SELECT * FROM battle_room WHERE room_id = %s", (room_id,))
            room = cursor.fetchone()
            if not room:
                return None

            # 获取对手状态
            opponent_uid = room['uid2'] if room['uid1'] == uid else room['uid1']
            cursor.execute("""
                SELECT score, steps, updated_at 
                FROM battle_state 
                WHERE room_id = %s AND uid = %s
                ORDER BY updated_at DESC 
                LIMIT 1
            """, (room_id, opponent_uid))
            
            opponent_state = cursor.fetchone()
            
            # 将datetime对象转换为字符串
            if opponent_state and 'updated_at' in opponent_state:
                opponent_state['updated_at'] = opponent_state['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            return {
                'status': 'success',
                'opponent_state': opponent_state,
                'started': room['started']
            }
        except Error as e:
            print(f"获取对战状态错误: {e}")
            return None
        finally:
            cursor.close()

    def join_battle_room(self, room_id, uid):
        """加入对战房间"""
        cursor = self.db_connection.cursor()
        try:
            # 检查房间是否存在且未满
            cursor.execute("""
                SELECT uid2 FROM battle_room 
                WHERE room_id = %s AND uid2 IS NULL
            """, (room_id,))
            room = cursor.fetchone()
            
            if not room:
                return {'status': 'error', 'message': '房间已满或不存在'}
                
            # 更新房间信息
            cursor.execute("""
                UPDATE battle_room 
                SET uid2 = %s, started = TRUE 
                WHERE room_id = %s
            """, (uid, room_id))
            
            self.db_connection.commit()
            return {'status': 'success', 'room_id': room_id}
        except Error as e:
            print(f"加入对战房间错误: {e}")
            return {'status': 'error', 'message': '服务器错误'}
        finally:
            cursor.close()

    def get_score_distribution(self):
        """获取用户得分分布数据"""
        cursor = self.db_connection.cursor()
        try:
            # 获取所有用户的最高分
            cursor.execute("""
                SELECT u.username, MAX(r.score) as max_score
                FROM user u
                JOIN record r ON u.uid = r.uid
                WHERE u.is_admin = FALSE
                GROUP BY u.uid, u.username
                ORDER BY max_score DESC
            """)
            
            distribution = []
            for row in cursor.fetchall():
                distribution.append({
                    'username': row[0],
                    'max_score': row[1]
                })
            
            return {'status': 'success', 'distribution': distribution}
        except Error as e:
            print(f"获取得分分布错误: {e}")
            return {'status': 'error', 'message': '服务器错误'}
        finally:
            cursor.close()

    def handle_client(self, client_socket, address):
        """处理客户端连接"""
        print(f"接受来自 {address} 的连接")
        try:
            while self.running:
                try:
                    data = client_socket.recv(4096)
                    if not data:
                        break

                    request = json.loads(data.decode('utf-8'))
                    action = request.get('action')
                    response = None

                    if action == 'register':
                        response = self.register_user(
                            request.get('username'),
                            request.get('password'),
                            request.get('is_admin', False)
                        )
                    elif action == 'login':
                        response = self.login(
                            request.get('username'),
                            request.get('password'),
                            request.get('user_type', 'user')
                        )
                    elif action == 'logout':
                        response = self.logout(request.get('session_id'))
                    elif action == 'get_user_list':
                        response = self.get_user_list(request.get('search_term'))
                    elif action == 'ban_user':
                        response = self.ban_user(request.get('uid'))
                    elif action == 'unban_user':
                        response = self.unban_user(request.get('uid'))
                    elif action == 'save_record':
                        response = self.save_record(
                            request.get('session_id'),
                            request.get('score'),
                            request.get('steps')
                        )
                    elif action == 'get_records':
                        response = self.get_records(request.get('session_id'))
                    elif action == 'get_leaderboard':
                        response = self.get_leaderboard()
                    elif action == 'create_battle':
                        uid = self.verify_session(request.get('session_id'))
                        if uid:
                            room_id = self.create_battle_room(uid, None)
                            if room_id:
                                response = {'status': 'success', 'room_id': room_id}
                            else:
                                response = {'status': 'error', 'message': '创建房间失败'}
                        else:
                            response = {'status': 'error', 'message': '无效的会话'}
                    elif action == 'join_battle':
                        uid = self.verify_session(request.get('session_id'))
                        room_id = request.get('room_id')
                        if uid:
                            response = self.join_battle_room(room_id, uid)
                        else:
                            response = {'status': 'error', 'message': '无效的会话'}
                    elif action == 'update_battle_state':
                        uid = self.verify_session(request.get('session_id'))
                        room_id = request.get('room_id')
                        state = request.get('state')
                        if uid and room_id and state:
                            response = self.update_battle_state(room_id, uid, state)
                        else:
                            response = {'status': 'error', 'message': '参数不完整'}
                    elif action == 'get_battle_state':
                        uid = self.verify_session(request.get('session_id'))
                        room_id = request.get('room_id')
                        if uid:
                            result = self.get_battle_state(room_id, uid)
                            if result:
                                response = result
                            else:
                                response = {'status': 'error', 'message': '获取状态失败'}
                        else:
                            response = {'status': 'error', 'message': '无效的会话'}
                    elif action == 'get_score_distribution':
                        response = self.get_score_distribution()

                    if response:
                        client_socket.send(json.dumps(response).encode('utf-8'))
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"处理客户端 {address} 时出错: {e}")
                    break
        finally:
            client_socket.close()
            print(f"与 {address} 的连接已关闭")

    def start(self):
        """启动认证服务器"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            print(f"认证服务器正在监听 {self.host}:{self.port}")
            print("按 Ctrl+C 可以安全退出服务器")
            
            while self.running:
                try:
                    self.server_socket.settimeout(1)  # 设置超时，以便能够响应关闭信号
                    client_socket, address = self.server_socket.accept()
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address)
                    )
                    client_thread.daemon = True  # 设置为守护线程，这样主线程退出时，这些线程也会退出
                    client_thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:  # 只有在服务器仍在运行时才打印错误
                        print(f"接受连接时出错: {e}")
        except Exception as e:
            print(f"服务器错误: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
            if self.db_connection:
                self.db_connection.close()

if __name__ == "__main__":
    server = GameServer2048()
    server.start()