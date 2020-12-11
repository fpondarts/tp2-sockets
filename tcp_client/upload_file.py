import os
import signal
from socket import socket, SOCK_STREAM, AF_INET

MAX_PACKET_SIZE = 4096
DATA_LENGTH = 1024
SEP = '\r\n'

client_socket = None


def signal_handler(_, __):
    if client_socket is None:
        exit(0)

    client_socket.close()
    exit(0)


signal.signal(signal.SIGINT, signal_handler)


def add_line(line, message):
    message += line + SEP
    return message


def initial_message(name, length):
    message = ''
    message = add_line('UPLOAD', message)
    message = add_line(name, message)
    message = add_line(str(length), message)

    return message


def upload_message(name, offset, file):
    message = ''
    message = add_line('UPLOAD', message)
    message = add_line(name, message)
    message = add_line(str(offset), message)
    data = file.read(DATA_LENGTH)
    message = add_line("DATA", message)
    message = message.encode() + data
    return message, len(data)


def upload_file(server_address, src, name):
    print('TCP: upload_file({}, {}, {})'.format(server_address, src, name))

    if not os.path.isfile(src):
        print("Error: el archivo no existe")
        return

    global client_socket

    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.connect(server_address)

    total_length = os.path.getsize(src)
    total_uploaded = 0
    f = open(src, 'rb')

    first_acked = False

    total_uploaded = 0
    while total_uploaded < total_length:
        if not first_acked:
            to_send = initial_message(name, total_length).encode()
            data_length = 0
            first_acked = True
        else:
            data = f.read(DATA_LENGTH)
            to_send, data_length = (data, len(data))

        print('to send', to_send)

        client_socket.sendto(to_send, server_address)
        total_uploaded += data_length

        print('total_uploaded, total expected', total_uploaded, total_length)

    client_socket.close()
