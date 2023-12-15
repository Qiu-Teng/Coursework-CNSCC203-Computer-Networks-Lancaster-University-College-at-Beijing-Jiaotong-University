# Qiu Teng 21726062
# -*- coding: UTF-8 -*-

import os
import struct
import time
import select
import socket

# ICMP消息类型常量
ICMP_ECHO_REQUEST = 8  # 回显请求
ICMP_ECHO_REPLY = 0  # 回显应答
ICMP_UNREACHABLE_TYPE = 3  # 不可达类型
ICMP_HOST_UNREACHABLE_CODE = 1  # 主机不可达代码
ICMP_NETWORK_UNREACHABLE_CODE = 0  # 网络不可达代码

# ICMP包格式常量，无符号字节，无符号短整数，有符号短整数
ICMP_PACKET_FORMAT = '!bbHHh'  # 格式为：类型、代码、校验和、ID、序列号

# 全局变量：ICMP包ID和序列号
icmp_id = os.getpid() & 0xFFFF  # 使用进程ID作为ICMP包ID，并限制为16位
icmp_sequence = 0  # ICMP包序列号

def checksum(packet):
    """
    计算并返回给定数据包的校验和。
    """
    # 初始化校验和为零
    csum = 0
    count_to = (len(packet) // 2) * 2
    count = 0

    # 两字节一组累加数据包
    while count < count_to:
        this_val = packet[count+1] * 256 + packet[count]
        csum += this_val
        csum &= 0xffffffff  # 截断为32位
        count += 2

    # 如果有剩余字节，加入校验和
    if count_to < len(packet):
        csum += packet[len(packet) - 1]
        csum &= 0xffffffff  # 截断为32位

    # 校验和计算的最后步骤
    csum = (csum >> 16) + (csum & 0xffff)  # 高16位加低16位
    csum += (csum >> 16)  # 加上进位（如果有）
    answer = ~csum & 0xffff  # 取反并截断为16位
    answer = answer >> 8 | (answer << 8 & 0xff00)  # 字节交换
    return answer

def send_one_ping(icmp_socket, destination_addr, icmp_id, icmp_sequence):
    """
    向指定目标地址发送一个ICMP回显请求。
    """
    # 构建ICMP头：类型、代码、校验和、ID、序列号
    # 将数据按照指定的格式（format）打包成二进制数据。在这里，它被用来打包 ICMP  头部。
    icmp_header = struct.pack(ICMP_PACKET_FORMAT, ICMP_ECHO_REQUEST, 0, 0, icmp_id, icmp_sequence)

    # 载荷为当前时间
    payload = struct.pack('!d', time.time())

    # 计算头和负载的校验和
    icmp_checksum = checksum(icmp_header + payload)

    # 使用正确校验和重新打包头
    icmp_header = struct.pack(ICMP_PACKET_FORMAT, ICMP_ECHO_REQUEST, 0, icmp_checksum, icmp_id, icmp_sequence)

    # ICMP包为头加负载
    icmp_packet = icmp_header + payload

    # 向目标地址发送包
    icmp_socket.sendto(icmp_packet, (destination_addr, 1))

def receive_one_ping(icmp_socket, icmp_id, timeout):
    # icmp_socket: 这是一个已经创建的 ICMP 套接字，用于接收 ICMP 数据包（通常是 Ping 回复）。
    # icmp_id: ICMP 数据包的 ID，通常用于标识发送方。
    # timeout: 等待超时时间，指定了在等待套接字准备好读取数据时，最长要等待多少秒。
    """
    从ICMP套接字接收一个回显应答，并返回延迟。
    """

    # 使用select等待套接字准备好读取
    ready = select.select([icmp_socket], [], [], timeout)
    # select函数是一个多路复用函数，用于监视一组套接字，以确定它们是否已准备好读取、写入或出现错误。
    # 在这里，我们传递了一个包含 icmp_socket的列表给select函数的第一个参数，表示我们要监视的套接字列表。
    # 空列表[] 表示我们不关心写入或错误事件。
    # timeout参数指定了等待超时时间，如果在指定时间内没有套接字准备好读取数据，select将返回，以便程序继续执行。

    # 如果没有准备好读取，返回超时
    if not ready[0]:
        return -1

    # 接收到包，记录当前时间
    time_received = time.time()
    # 接收包
    rec_packet, _ = icmp_socket.recvfrom(1024) # 忽略IP 地址和端口号

    # 从IP包中提取ICMP头
    icmp_header = rec_packet[20:28]

    # 解析ICMP头，这行代码从 ICMP 头部中解包出所需的字段，即 ICMP 数据包的类型和标识，
    type_, _, _, packet_id, _ = struct.unpack(ICMP_PACKET_FORMAT, icmp_header) # 根据 ICMP_PACKET_FORMAT 中的规则，解析的字段包括 ICMP 数据包的类型、代码、校验和、标识和序列号等
    # 代码，校验和，序列号

    # 计算延迟
    delay = time_received - struct.unpack('!d', rec_packet[28:36])[0]
    # 格式字符串 '!d' 来解包数据，并返回一个包含解包后的值的元组，然后 [0] 用于获取解包后的浮点数值。

    # 检查类型、代码和包ID是否匹配
    if type_ == ICMP_ECHO_REPLY and packet_id == icmp_id:
        return delay
    else:
        return -1

def do_one_ping(destination_addr, timeout):
    """
    执行一次ICMP回显请求并接收应答。
    """
    global icmp_sequence
    # 创建ICMP套接字
    icmp_proto = socket.getprotobyname('icmp')

    # 套接字类型为原始套接字，这意味着您可以在套接字层次上直接处理数据包，而不是在更高级别的协议层次上（例如TCP或UDP）。
    icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp_proto)
    # 序列号递增
    icmp_sequence += 1

    # 发送一个ping

    send_one_ping(icmp_socket, destination_addr, icmp_id, icmp_sequence)

    # 接收一个ping
    delay = receive_one_ping(icmp_socket, icmp_id, timeout)
    # 关闭ICMP套接字
    icmp_socket.close()
    # 返回延迟
    return delay

def ping(host, timeout=1000, count=4):
    """
    向指定主机发送一定次数的ICMP回显请求，并给定超时时间。
    """
    # 将主机名解析为IPv4地址
    dest_addr = socket.gethostbyname(host)
    print(f"向 {host} 发送 {count} 次ICMP请求：")
    # 初始化发送、丢失和接收的包数
    sent, lost, received = 0, 0, 0
    # 延迟列表
    delays = []

    for _ in range(count):
        # 执行一次ping
        delay = do_one_ping(dest_addr, timeout / 1000)
        # 发送包数递增
        sent += 1
        if delay > 0:
            # 包被接收，记录延迟
            received += 1
            delays.append(delay)
            print(f"从 {dest_addr} 收到：icmp_seq={icmp_sequence} 时间={delay*1000:.2f} ms")
        else:
            # 包丢失
            lost += 1
            print("请求超时。")

        # 等待1秒再发送下一个ping
        time.sleep(1)

    # 打印统计信息
    if received > 0:
        # 计算最小、最大和平均延迟
        min_delay = min(delays)
        max_delay = max(delays)
        avg_delay = sum(delays) / received
        print(f"--- {host} ping 统计信息 ---")
        print(f"{sent} 包发送, {received} 接收, {100 * lost / sent:.1f}% 丢包, 总时间 {sum(delays)*1000:.2f}ms")
        print(f"rtt 最小/平均/最大 = {min_delay*1000:.3f}/{avg_delay*1000:.3f}/{max_delay*1000:.3f} ms")
    else:
        print(f"--- {host} ping 统计信息 ---")
        print(f"{sent} 包发送, {received} 接收, 100% 丢包")

if __name__ == "__main__":
    # 获取用户输入
    host_input = input("输入要ping的IP或主机名 [默认: lancaster.ac.uk]: ") or "lancaster.ac.uk"
    count_input = input("输入ping的次数 [默认: 5]: ") or 5
    timeout_input = input("输入每次ping的超时时间（毫秒） [默认: 1000]: ") or 1000

    # 使用用户输入调用ping函数
    ping(host_input, int(timeout_input), int(count_input))
