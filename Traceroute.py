# this version adds comments
import socket  # Import socket module for network connections
import os  # Import os module for system operations like getting the process ID
import struct  # Import struct module for packing and unpacking data to and from C structures
import sys  # Import sys module for system-specific parameters and functions
import time  # Import time module for time-related functions
import select  # Import select module for efficient I/O multiplexing

# Define constants for ICMP message types
ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request messages
ICMP_ECHO_REPLY = 0  # ICMP type code for echo reply messages
TYPE_ICMP_OVERTIME = 11  # ICMP type code for indicating timeout (Time Exceeded)
CODE_TTL_OVERTIME = 0  # ICMP code for Time To Live exceeded in transit
TYPE_ICMP_UNREACHED = 3  # ICMP type code for unreachable destination
addr = None  # Initialize a global variable 'addr' to store the address
timeSent = None  # Initialize a global variable 'timeSent' to store the time a packet is sent

# Function to calculate checksum for packet integrity
def checksum(string):
    csum = 0  # Initialize checksum to 0
    to_count = (len(string) / 2) * 2  # Compute the count for the checksum loop
    count = 0  # Initialize count for the loop

    # Loop to calculate checksum
    while count < to_count:
        this_val = string[count + 1] * 256 + string[count]  # Calculate the value for current bytes
        csum = csum + this_val  # Add the value to the checksum
        csum = csum & 0xffffffff  # Ensure checksum stays within 32 bits
        count = count + 2  # Increment count by 2 bytes

    # Check for any remaining bytes to be added to checksum
    if count < len(string):
        csum = csum + ord(string[len(string) - 1])  # Add the value of the last byte
        csum = csum & 0xffffffff  # Ensure checksum stays within 32 bits

    # Finalize the checksum calculation
    csum = (csum >> 16) + (csum & 0xffff)  # Add high 16 bits to low 16 bits
    csum = csum + (csum >> 16)  # Add carry from above step
    answer = ~csum  # Take one's complement of the result
    answer = answer & 0xffff  # Keep only the lower 16 bits
    answer = answer >> 8 | (answer << 8 & 0xff00)  # Swap the bytes
    return answer  # Return the computed checksum

# Function to resolve an IP address to its corresponding hostname
def get_host_name(des_addr):
    try:
        hostname = socket.gethostbyaddr(des_addr)[0]  # Try to get the hostname from the IP address
        IP = des_addr  # Store the IP address
        return "{0} [{1}]".format(hostname, IP)  # Return the hostname and IP in formatted string
    except socket.herror:
        return des_addr  # Return the original IP address if hostname resolution fails

# Function to receive a single ping response
def receive_oneping(receive_socket, id, timeout, _):
    def calculate_delay(time_begin):
        return time.time() - time_begin  # Calculate and return the time delay

    def parse_address(response_packet):
        header = response_packet[20:28]  # Extract the header from the response packet
        access_type, _, _, packet_id, _ = struct.unpack("!bbHHh", header)  # Unpack the header to get necessary values
        if access_type == 11 or 3 and packet_id == id:  # Check if the response is for our packet
            return addr[0], access_type  # Return the address and access type
        return None, None  # Return None if not the desired packet

    time_left = timeout  # Initialize time left for timeout

    # Loop to wait for response until timeout
    while True:
        time_begin = time.time()  # Record the start time
        what_ready = select.select([receive_socket], [], [], time_left)  # Wait for response with timeout
        time_spent = (time.time() - time_begin)  # Calculate the time spent waiting
        time_left = time_left - time_spent  # Update the time left
        if time_left <= 0:  # Check if time left is less than or equal to 0
            return -1  # Return -1 indicating timeout
        if not what_ready[0]:  # Check if the socket is not ready
            return -2  # Return -2 indicating no response
        rec_packet, addr = receive_socket.recvfrom(1024)  # Receive the packet
        total_delay = calculate_delay(time_begin)  # Calculate the total delay
        addr, access_type = parse_address(rec_packet)  # Parse the received packet
        if total_delay is not None and addr is not None and access_type is not None:  # Check if packet is valid
            return total_delay, addr, access_type  # Return the delay, address, and access type

# Function to send a single ping
def send_oneping(send_socket, destination_address, id):
    # Function to send an ICMP echo request packet
    def send_icmppacket(send_socket, destination_address, id):
        my_checksum = 0  # Initialize checksum to 0
        header = struct.pack('!bbHHh', ICMP_ECHO_REQUEST, 0, my_checksum, id, 1)  # Pack the ICMP header
        data = struct.pack("!d", time.time())  # Pack the current time as data
        my_checksum = checksum(header + data)  # Calculate the checksum with header and data
        header = struct.pack("!bbHHh", ICMP_ECHO_REQUEST, 0, my_checksum, id, 1)  # Repack the header with checksum
        packet = header + data  # Combine header and data to form the packet
        send_socket.sendto(packet, (destination_address, 1))  # Send the packet

    # Function to send a UDP packet (used for traceroute)
    def send_udppacket(send_socket, destination_address, _):
        msg = struct.pack("!d", time.time())  # Pack the current time as message
        length = 8 + len(msg)  # Calculate the total length of the UDP packet
        my_checksum = 0  # Initialize checksum to 0
        sport = 9  # Source port number
        dport = 33434  # Destination port number
        udp_header = struct.pack('!HHHH', sport, dport, length, my_checksum)  # Pack the UDP header
        my_checksum = checksum(udp_header + msg)  # Calculate the checksum with UDP header and message
        udp_header = struct.pack('!HHHH', sport, dport, length, my_checksum)  # Repack the UDP header with checksum
        packet = udp_header + msg  # Combine UDP header and message to form the packet
        send_socket.sendto(packet, (destination_address, 1))  # Send the packet
        send_socket.close()  # Close the send socket

    # Check protocol type and call the respective function to send packet
    if prot == "ICMP":
        send_icmppacket(send_socket, destination_address, id)  # Send an ICMP packet
    elif prot == "UDP":
        send_udppacket(send_socket, destination_address, id)  # Send a UDP packet

# Function to perform one trace operation (ping or traceroute) to a destination address
def do_onetrace(destination_address, timeout, ttl, prot):
    # Function to create and configure an ICMP socket for sending and receiving
    def create_icmpsocket(ttl):
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname('ICMP'))  # Create a raw socket for ICMP protocol
        send_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)  # Set the Time-To-Live option for the socket
        return send_socket, send_socket  # Return the same socket for both sending and receiving

    # Function to create and configure UDP and RAW ICMP sockets for traceroute
    def create_udpsocket(ttl):
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.getprotobyname('udp'))  # Create a socket for UDP protocol
        send_socket.bind(("", 7))  # Bind the socket to an arbitrary local port
        receive_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname('ICMP'))  # Create a raw socket for receiving ICMP responses
        receive_socket.bind(("", 7))  # Bind the receive socket to the same port as the send socket
        send_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)  # Set the Time-To-Live option for the send socket
        receive_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)  # Set the Time-To-Live option for the receive socket
        return send_socket, receive_socket  # Return the send and receive sockets

    # Check protocol type and create the respective sockets
    if prot == "ICMP":
        send_socket, receive_socket = create_icmpsocket(ttl)  # For ICMP protocol, use ICMP sockets
    elif prot == "UDP":
        send_socket, receive_socket = create_udpsocket(ttl)  # For UDP protocol, use UDP and RAW ICMP sockets

    send_oneping(send_socket, destination_address, ID)  # Send one ping to the destination
    delay = receive_oneping(receive_socket, ID, timeout, prot)  # Receive the ping response
    send_socket.close()  # Close the sending socket
    receive_socket.close()  # Close the receiving socket
    return delay  # Return the delay experienced during the ping

# Function to display delay and packet loss information
def print_delay_and_loss(_, loss, addr):
    if loss == 3:  # Check if all three packets were lost
        print("time out")  # Print "time out" indicating complete loss
    else:
        print(get_host_name(addr))  # Print the hostname or IP address of the responding node

# Function to process the result of a packet transmission and update statistics
def process_packet_result(result, seq, delay, loss, addr, run_over):
    if result in [-1, -2]:  # Check if the packet transmission failed
        delay[seq] = '*'  # Mark the delay for this sequence as '*'
        print("*", end=" ")  # Print '*' indicating packet loss
        loss += 1  # Increment the packet loss count
    else:  # If the packet was transmitted successfully
        print(str(int(result[0] * 1000)) + " ms", end=" ")  # Print the round-trip time in milliseconds
        addr = result[1]  # Update the address with the responding node's address
        if result[2] == 0:
            run_over = True  # Set 'run_over' to True if the destination is reached
    return delay, loss, addr, run_over  # Return the updated values

# Function to trace one hop (TTL level) towards the destination
def trace_one_hop(dest_add, timeout, ttl, prot):
    delay = [0, 0, 0]  # Initialize the delay array for three packets
    loss = 0  # Initialize the loss count
    addr = None  # Initialize the address variable
    run_over = False  # Initialize the run_over flag
    print(str(ttl), end=" ")  # Print the current TTL value
    for seq in range(3):  # Loop to send three packets
        result = do_onetrace(dest_add, timeout, ttl, prot)  # Perform one trace operation
        delay, loss, addr, run_over = process_packet_result(result, seq, delay, loss, addr, run_over)  # Process the result of the trace
    print_delay_and_loss(delay, loss, addr)  # Print the delay and loss information
    return run_over, addr  # Return whether the destination was reached and the responding address

# Main function to perform traceroute to a specified host
def trace(host, timeout, prot):
    global ID  # Declare ID as a global variable
    ID = os.getpid()  # Set ID to the current process ID
    ttl = 1  # Initialize TTL to 1
    dest_add = socket.gethostbyname(host)  # Resolve the host to an IP address
    max_hop = 30  # Set the maximum number of hops

    for i in range(max_hop):  # Loop through each hop up to the maximum
        run_over, addr = trace_one_hop(dest_add, timeout, ttl, prot)  # Trace one hop
        ttl += 1  # Increment the TTL for the next hop
        if run_over:  # Check if the destination was reached
            print("program run over", end=" ")  # Print a message indicating the end of the program
        if addr == dest_add:  # Check if the responding address matches the destination
            break  # Exit the loop if the destination is reached
        if i == (max_hop - 1):  # Check if the maximum number of hops is reached
            print("exceed max_hop")  # Print a message indicating the maximum hops exceeded
            sys.exit()  # Exit the program

# Entry point of the script
if __name__ == "__main__":
    desAddr = input("Please enter the IP or host name[default(www.lancaster.ac.uk)]:\n")  # Prompt user to enter a destination address
    if len(desAddr) == 0:  # Check if the user input is empty
        desAddr = 'www.lancaster.ac.uk'  # Use a default address if no input is provided

    timeout = input("Please enter the timeout[default:1s]:\n")  # Prompt user to enter a timeout value
    if len(timeout) == 0:  # Check if the user input is empty
        timeout = 1  # Use a default timeout if no input is provided

    prot = input("Please choose protocol (ICMP or UDP)[default ICMP]:\n")  # Prompt user to choose a protocol
    if len(prot) == 0:  # Check if the user input is empty
        prot = 'ICMP'  # Use ICMP as the default protocol
    elif prot != 'ICMP' and prot != 'UDP':  # Check if the input is neither ICMP nor UDP
        print("Please enter 'ICMP' or 'UDP', default(ICMP)")  # Prompt the user to enter a valid protocol

    # Start the traceroute process
    print("Tracing address: " + desAddr + " " + socket.gethostbyname(desAddr))  # Print the address being traced
    trace(desAddr, int(timeout), prot)  # Call the trace function with the specified parameters
