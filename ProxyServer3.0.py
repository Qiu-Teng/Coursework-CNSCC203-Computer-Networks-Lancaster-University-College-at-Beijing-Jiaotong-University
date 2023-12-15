# 导入 socket 库，用于网络通信
from socket import socket, AF_INET, SOCK_STREAM, gethostbyname, gethostname
# 导入 re 库，用于正则表达式操作
import re
# 导入 select 库，用于 I/O 多路复用
import select
import os

# 定义一个函数，用于从 URL 生成文件名
def generate_filename_from_url(url):
    # 使用正则表达式替换 URL 中的非字母数字字符为下划线，并添加 '.html' 扩展名
    return re.sub(r'[^\w]', '_', url) + '.html'

# 定义一个函数，用于处理客户端的请求
def handle_request(client_socket, client_address):
    # 从客户端套接字接收数据
    sentence = client_socket.recv(1024).decode()# decode把bytes解码成字符串
    # 打印接收到的数据和客户端地址.在大括号内部的内容会被解释为表达式并计算出结果
    print(f"Received from {client_address}:")
    print(sentence)# 请求头部信息

    # 将 HTTP 请求分割成多个部分，并将结果存储在一个列表中,取出索引为2
    url_needed = re.split("/", sentence, 3)[2] # 用来提取客户端请求中的目标 URL 的部分。
    # 生成文件名
    filename = generate_filename_from_url(url_needed)

    try:
        # 尝试打开文件
        with open(filename, "r") as f:
            # 读取文件内容
            file_content = f.read()
            # 打印缓存命中信息
            print(f"Cache hit. Serving content from {filename}")
            # 发送 HTTP 响应头
            response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"

            # 将构造的HTTP响应头发送给客户端，以通知客户端响应状态和内容类型。
            client_socket.send(response.encode())
            # 发送文件内容
            client_socket.send(file_content.encode())
    except FileNotFoundError:
        # 如果文件不存在，打印缓存未命中信息
        print(f"Cache miss. Fetching content from {url_needed}")
        # 获取服务器 IP 地址，解析主机名或域名并返回对应的 IP 地址
        server_name = gethostbyname(url_needed)
        # 打印解析的服务器信息
        print(f"Resolved {url_needed} to {server_name}")
        # 设置服务器端口
        server_port = 80
        # 创建一个新的套接字
        host_socket = socket(AF_INET, SOCK_STREAM)
        # 连接到服务器
        host_socket.connect((server_name, server_port))
        # 构造完整的 URL
        full_url = "http://" + url_needed + "/"
        # 构造 HTTP 请求内容
        request_content = "GET " + full_url + " HTTP/1.1\r\n" + "Host: " + url_needed + "\r\n\r\n"
        # 发送请求到服务器
        host_socket.send(request_content.encode())
        # 初始化响应变量，这个变量将在后续的代码中用于存储从服务器接收到的响应数据
        response = ""
        # 设置非阻塞模式。在等待服务器响应时不阻塞程序的执行。
        host_socket.setblocking(0)

        # 循环接收数据
        while True:
            # 使用 select 检查套接字是否可读。接受四个参数，分别是要检查的套接字列表
            # 检查可写性的套接字列表，用于检查异常情况的套接字列表，以及一个超时值。
            readable = select.select([host_socket], [], [], 2)# 可读、可写、异常

            # 如果host_socket可读，readable列表将包含host_socket，否则将为空列表。
            # 这是一种非阻塞操作，允许程序继续执行后续操作，而不必一直等待数据到达。
            # 这个函数在指定的超时时间内等待套接字变得可读，
            # 如果在超时时间内套接字变得可读，它将返回一个包含可读套接字的列表，否则返回一个空列表
            if readable[0]:# 意味着host_socket可读，有数据可接收；
                # 如果在 2 秒内没有数据可读，循环也会退出，以防止程序一直等待数据的到达。

                # 接收数据
                received_data = host_socket.recv(4096).decode("gbk", "ignore")# 数据被解码为GBK编码，并忽略了无法解码的字符。
                # 追加到响应变量
                response += received_data
            else:
                # 不管是因为成功接收完所有数据还是因为没有更多数据可读而退出循环
                break
        # 关闭套接字
        host_socket.close()

        # 将接收到的内容写入文件
        with open(filename, 'w') as f:
            # 从一个文本中提取 HTML 部分
            # 使用索引[-1]来获取分割后的部分列表中的最后一个部分，即响应的HTML内容。
            html = "<html" + re.split("<html", response, 10)[-1]# 响应拆分得太多，只分割最多10个部分。
            # 写入文件
            f.write(html)
            # 打印接收和保存信息
            print(f"Received {len(response)} bytes of content from {url_needed}. Saved to {filename}")

        # 构造客户端响应
        response_to_client = "HTTP/1.1 200 OK\r\n\r\n" + html
        # 发送响应到客户端
        client_socket.send(response_to_client.encode())
    except Exception as e:
        # 打印处理请求时的错误
        print(f"Error handling request: {e}")
    finally:
        # 关闭客户端套接字
        client_socket.close()

# 定义一个函数，用于启动代理服务器
def start_proxy_server(server_address, server_port):
    # 创建套接字
    # Address Family - Internet，表示 IPv4 地址族。;
    # 基于流的套接字是一种可靠的、面向连接的套接字，通常用于 TCP 协议
    server_socket = socket(AF_INET, SOCK_STREAM)


    # 绑定套接字到地址和端口
    server_socket.bind((server_address, server_port))

    # 这是一个套接字对象的方法，用于开始监听连接请求
    # 参数是1，这务器将允许最多1个客户端连接排队等待。如果有多个客户端尝试连接服务器，多余的连接将被服务器拒绝。
    server_socket.listen(1)
    # 打印服务器准备就绪信息
    print('Server ready to receive')

    # 无限循环等待连接
    while True:
        # 阻塞程序的执行，直到有客户端尝试连接。一旦有连接请求到达，它会返回一个新的套接字对象 'connection_socket'，以及连接的客户端地址 'addr'
        connection_socket, addr = server_socket.accept()
        # 处理请求
        handle_request(connection_socket, addr)

    # 关闭服务器套接字
    server_socket.close()

# 提示用户输入端口号
print("Please set your own serverPort")
port = int(input())
# 启动代理服务器
start_proxy_server("", port)
