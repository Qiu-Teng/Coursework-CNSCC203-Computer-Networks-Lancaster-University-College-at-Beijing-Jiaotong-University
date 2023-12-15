# 多线程、put\delete GET方法client


import socket                   # 导入 'socket' 模块，用于网络通信。
import threading                # 导入 'threading' 模块，提供多线程支持。
import os                       # 导入 'os' 模块，用于操作系统级别的接口，如文件管理。

# 定义处理客户端请求的函数，将在独立线程上运行
def handle_request(tcp_socket):
    print('Waiting for connection...')   # 打印信息，表示服务器正在等待连接。

    try:
        # 从客户端接收并解码HTTP请求
        data = tcp_socket.recv(2048).decode()   # 从TCP套接字接收最多2048字节数据，并将其解码为UTF-8字符串。

        # 打印完整的请求数据
        print("Full Request:")   # 打印消息，表示下面将显示完整的HTTP请求内容。
        print(data)              # 打印接收到的HTTP请求。
        # 解析请求以提取请求的文件名和HTTP方法
        request_lines = data.splitlines()   # 将接收到的数据按换行符分割成多行。

        if request_lines:                   # 如果请求行列表不为空。
            request_line = request_lines[0]  # 获取请求的第一行。
            # 它将第一行按空格分割成单词列表，以获取HTTP方法和请求的文件名。同时，它去除文件名开头的斜杠。
            words = request_line.split()     # 将请求行按空格分割成单词列表。

            if len(words) >= 2:              # 如果分割后的单词数量不少于2个。
                http_method = words[0]       # 获取请求的HTTP方法（如GET, POST）。

                # GET / index.html HTTP / 1.1

                filename = words[1].lstrip("/")  # 获取请求的文件名，去除开头的斜杠。
                print(f"HTTP Method: {http_method}")
                print(f"Requested file: {filename}")  # 打印HTTP方法和请求的文件名。

                # 处理GET请求
                if http_method == "GET":
                    with open(filename, 'rb') as f:
                    # 以二进制读模式打开文件，以原始字节返回给客户端，避免不正确的解码方法而使数据失真
                        content = f.read().decode()   # 读取文件内容并解码为字符串。
                    res_header = 'HTTP/1.1 200 OK\r\n\r\n'   # 创建HTTP响应头，状态码为200 OK。
                    tcp_socket.send((res_header + content).encode())  # 将响应头和内容编码后发送给客户端。

                # 处理PUT请求
                elif http_method == "PUT":
                    try:
                        content_length = 0  # 初始化内容长度为0。

                        # 在请求头中查找 'Content-Length' 字段
                        for line in request_lines:
                            if "Content-Length:" in line:# 检查每一行是否包含字符串 "Content-Length:"
                                content_length = int(line.split(" ")[1])  # [1] 索引用于获取列表中的第二部分，即包含内容长度的部分。
                                # 当找到包含 “Content-Length：” 的行时，使用 将行按空格分割，取第二部分，即内容长度的部分，并将其转换为整数。这将设置  变量为请求中指定的内容长度

                        # 如果存在Content-Length，接收相应长度的数据
                        if content_length > 0:
                            received_data = b''  # 初始化接收数据的变量。字节串以 b 前缀开头，表示它是一个二进制数据序列。
                            while len(received_data) < content_length:  # 循环直到接收足够长度的数据。
                                chunk = tcp_socket.recv(2048)  # 接收数据。
                                if not chunk:
                                    break  # 如果没有接收到数据，则退出循环。
                                received_data += chunk  # 将接收到的数据追加到变量中。

                            # 将接收到的数据写入文件
                            with open(filename, 'wb') as f:
                                f.write(received_data)  # 以二进制写模式打开文件，并写入数据。

                        # 构建成功响应的头部
                        res_header = 'HTTP/1.1 200 OK\r\n'
                        res_header += 'Content-Type: text/plain\r\n'
                        res_header += '\r\n'
                        tcp_socket.send(res_header.encode())  # 发送响应头给客户端。

                    except Exception as e:
                        print("Error while handling PUT request:", str(e))
                        res_header = 'HTTP/1.1 500 INTERNAL SERVER ERROR\r\n\r\n'
                        tcp_socket.send(res_header.encode())  # 发送500错误响应。

                # 处理DELETE请求
                elif http_method == "DELETE":
                    # 实现DELETE请求的处理逻辑（例如删除文件）。
                    try:
                        os.remove(filename)  # 尝试删除指定的文件。
                        res_header = 'HTTP/1.1 200 OK (DELETE request handled)\r\n\r\n'
                        tcp_socket.send(res_header.encode())  # 发送成功响应。
                    except FileNotFoundError:
                        res_header = 'HTTP/1.1 404 NOT FOUND (File not found)\r\n\r\n'
                        tcp_socket.send(res_header.encode())  # 发送404错误响应。

                else:
                    raise ValueError(f"Unsupported HTTP method: {http_method}")
            else:
                raise ValueError("Malformed request line")  # 如果请求行格式错误，则抛出异常。
        else:
            raise ValueError("Empty request")  # 如果请求为空，则抛出异常。

    except IOError:
        # 处理文件未找到的情况，响应404错误
        res_header = 'HTTP/1.1 404 NOT FOUND\r\n\r\n'  # 创建404错误的响应头。
        tcp_socket.send(res_header.encode())           # 发送响应头给客户端。
        print(res_header)                              # 打印响应头。

    except ValueError as ve:
        print("Error: ", ve)                           # 打印错误信息。
        res_header = 'HTTP/1.1 400 BAD REQUEST\r\n\r\n'  # 创建400错误的响应头。
        tcp_socket.send(res_header.encode())             # 发送响应头给客户端。

    finally:
        tcp_socket.close()   # 关闭客户端套接字。

# 定义启动服务器的函数
def start_server(server_address, server_port):
    TCP = socket.getprotobyname('tcp')   # 获取TCP协议的常量,增加可读性
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, TCP)
    #                                   创建IPv4, TCP的套接字对象。

    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)   # 设置套接字选项，以便重用地址。
    #SOL_SOCKET套接字级别，影响套接字的一般行为。
    # 1表示启用socket.SO_REUSEADDR允许重用地址。这个选项告诉操作系统可以在服务器套接字关闭后立即重新绑定到之前使用的地址和端口，而不必等待一段时间
    print("Server ready to serve...")   # 打印消息，表示服务器准备就绪。

    server_socket.bind((server_address, int(server_port)))   # 绑定服务器套接字到指定地址和端口。
    server_socket.listen(128)   # 开始监听来自客户端的连接。
    # 等待连接队列的最大长度。这个参数决定了服务器可以同时处理多少个等待连接的客户端。

    while True:
        try:
            connection_socket, client_addr = server_socket.accept()   # 接受一个客户端连接。

            # 为客户端请求创建一个新线程
            # target指定了线程要运行的函数
            # args参数传递了connection_socket，即客户端连接的套接字
            thread = threading.Thread(target=handle_request, args=(connection_socket,))   # 创建一个新线程。
            print("Connection established with: %s" % str(client_addr))   # 打印客户端连接信息。
            thread.start()   # 启动线程处理客户端请求。

        except Exception as err:
            print(err)   # 打印任何异常信息。
            break

    server_socket.close()   # 关闭服务器套接字。

# 主程序入口
if __name__ == "__main__":
    server_address = ""   # 初始化服务器地址为空字符串，监听所有可用的网络接口和IP地址，
    server_port = input("Enter the port number [default:8000]: ")   # 提示用户输入服务器端口号。
    if not server_port:
        server_port = 8000   # 如果用户未提供端口号，则使用默认值8000。

    start_server(server_address, server_port)   # 使用指定的地址和端口启动服务器。
