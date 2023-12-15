# -*- coding: UTF-8 -*-
import os               # Import the 'os' module for file operations.
import webbrowser       # Import the 'webbrowser' module for opening web pages.
from socket import socket, AF_INET, SOCK_STREAM   # Import specific names from the 'socket' module.

# Function to get a valid port number from user input with a default value
def get_valid_port(prompt, default):
    """Prompt for a valid port number with a default value."""
    while True:
        port = input(prompt)   # Prompt the user for a port number.
        if not port:           # If the input is empty, return the default value.
            return default
        try:
            port = int(port)   # Try to convert the input to an integer.
            if 1 <= port <= 65535:  # Check if the port is within a valid range (1-65535).
                return port
            else:
                print("Please enter a valid port number (1-65535).")  # Print an error message for an invalid port range.
        except ValueError:
            print("Please enter a valid port number.")  # Print an error message for a non-integer input.

while True:
    # Let the user input the server port with a default value of 8000
    server_port = get_valid_port("Enter the server port [default:8000]: ", 8000)

    # Let the user input the object filename with a default value of test1.html
    obj = input("Hello, which document do you want to query? (default: test1.html): ")
    if not obj:
        obj = "test1.html"   # Set a default object filename if no input is provided.

    # Build a new client socket for each request
    client_socket = socket(AF_INET, SOCK_STREAM)   # Create a new socket for IPv4, TCP communication.

    # Build a connection to the server
    client_socket.connect(("127.0.0.1", server_port))   # Connect to the server at IP 127.0.0.1 and the specified port.

    # Write the GET header with additional headers similar to a browser
    Head = 'GET /' + obj + ' HTTP/1.1\r\n'                  # Build the GET request header with the requested object.
    Head += 'Host: 127.0.0.1:' + str(server_port) + '\r\n'  # Specify the host and port in the header.
    # Add various HTTP headers to simulate a browser's request.
    Head += 'Connection: close\r\n'
    Head += 'User-Agent: Mozilla/5.0 (compatible; MyClient/0.1; +http://myclient.example.com)\r\n'
    Head += 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n'
    Head += 'Accept-Language: en-US,en;q=0.5\r\n'
    Head += 'Accept-Encoding: gzip, deflate, br\r\n'
    Head += 'Upgrade-Insecure-Requests: 1\r\n'
    Head += '\r\n'   # End of the request headers.

    # Send the request using the socket
    client_socket.send(Head.encode('utf-8'))   # Encode and send the HTTP request to the server.

    # Get the message
    recv_data = client_socket.recv(1024 * 1000).decode('utf-8')   # Receive and decode the server's response.

    # Check for a 404 Not Found status in the response
    if "404 NOT FOUND" in recv_data.splitlines()[0]:
        print("Error: File not found (404)")   # Print an error message for a 404 status.
    else:
        write_data = recv_data.splitlines()[4:]   # Extract the HTML content from the response.
        file_name = "./recv_index.html"  # Define the path where the received file will be saved.
        f = open(file_name, 'wb')   # Open the file for writing in binary mode.
        for lines in write_data:
            f.write(lines.encode())   # Write each line of the content to the file.
            f.write("\n".encode())    # Add newline characters between lines.
        f.close()   # Close the file.

        file_path = os.path.abspath(file_name)   # Get the absolute path of the saved file.
        print("HTML file request is stored in " + file_path)   # Print the path of the saved file.
        webbrowser.open_new_tab(file_path)   # Open the saved HTML file in a new browser tab.

    # Close the socket after receiving the response
    client_socket.close()   # Close the client socket for this request.
