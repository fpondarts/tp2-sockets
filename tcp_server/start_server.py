from socket import socket, AF_INET, SOCK_STREAM
from constants.constants import HEADER_SEP
READ_CHUNK_SIZE = 1024


def read_header(conn_socket, previous):
    headers = previous.split(HEADER_SEP, 1)
    if len(headers) > 1:
        header = headers[0]
        message = headers[1]
    else: 
        header = None
        message = previous
    while header is None:
        message = message + conn_socket.recv(READ_CHUNK_SIZE).decode()
        headers = message.split(HEADER_SEP, 1)
        if len(headers) > 1:
            header = headers[0]
            message = headers[1]
    return header, message


def start_server(server_address, storage_dir):
    print('TCP: start_server({}, {})'.format(server_address, storage_dir))
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind(server_address)
    server_socket.listen(1)

    while True: 
        connection_socket, addr = server_socket.accept()
        header, remaining_bytes = read_header(connection_socket, '')
        if (header == 'INIT UPLOAD'):
            print("File upload")
        if (header == 'INIT DOWNLOAD'):
            print("File download")
