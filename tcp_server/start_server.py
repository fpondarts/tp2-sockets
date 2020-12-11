import os
import signal
from socket import socket, AF_INET, SOCK_STREAM

server_socket = None
connection_socket = None

SEP = '\r\n'
ERROR_MESSAGE = 'ERROR' + SEP
MAX_PACKET_SIZE = 4096
DATA_LENGTH = 1024


def signal_handler(_, __):
    if server_socket is None:
        exit(0)
    server_socket.close()

    if connection_socket is None:
        exit(0)
    connection_socket.close()

    exit(0)


signal.signal(signal.SIGINT, signal_handler)


def add_line(line, message):
    message += line + SEP
    return message


def download_initial_message(filename, total_length):
    message = ''
    message = add_line('DOWNLOAD', message)
    message = add_line(filename, message)
    data = str(total_length).encode()
    message = add_line("DATA", message)
    message = message.encode() + data
    return message


def handle_file_reception(a_socket,
                          an_address, filename, total_length, storage_dir):
    try:
        path = storage_dir + '/' + filename
        file = open(path, 'wb')
    except IOError:
        error_message = ''
        add_line('ERROR', error_message)
        a_socket.sendto(error_message.encode(), an_address)
        return

    total_received = 0

    while total_received < total_length:
        print("received loop, total_received", total_received)
        data = a_socket.recv(MAX_PACKET_SIZE)

        print("Recibida: {}".format(data))
        file.write(data)
        total_received += len(data)

    a_socket.close()


def handle_file_sending(a_socket, filename, storage_dir):
    path = storage_dir + '/' + filename
    if not os.path.isfile(path):
        a_socket.sendto(ERROR_MESSAGE.encode())
        return

    total_length = os.path.getsize(path)
    f = open(path, 'rb')

    a_socket.send(download_initial_message(filename, total_length))
    total_sent = 0

    while total_sent < total_length:
        data = f.read(DATA_LENGTH)
        a_socket.send(data)

        total_sent += len(data)

    f.close()
    a_socket.close()


def start_server(server_address, storage_dir):
    print('TCP: start_server({}, {})'.format(server_address, storage_dir))

    if not os.path.isdir(storage_dir):
        os.makedirs(storage_dir)

    global server_socket
    global connection_socket

    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind(server_address)
    server_socket.listen(1)

    while True:
        # Mensaje inicial de la transmision
        print("Esperando cliente")
        connection_socket, client_address = server_socket.accept()
        if not connection_socket:
            break

        print("Accepted connection from {}".format(client_address))

        raw_data = connection_socket.recv(MAX_PACKET_SIZE)
        message = raw_data.decode()
        print('message', message)
        headers = message.split(SEP)
        is_upload = headers[0].upper() == 'UPLOAD'
        file_name = headers[1]
        total_length = 0

        if is_upload:  # Upload
            total_length = int(headers[2])
            print('headers', headers)
            print('is_upload', is_upload)
            print('file_name', file_name)
            print('total_length', total_length)

            handle_file_reception(
                connection_socket,
                client_address,
                file_name,
                total_length,
                storage_dir)
        else:  # Download
            handle_file_sending(connection_socket, file_name, storage_dir)
