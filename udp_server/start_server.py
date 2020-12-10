import os
import time
from socket import socket, timeout, AF_INET, SOCK_DGRAM

SEP = '\r\n'
ERROR_MESSAGE = 'ERROR' + SEP
MAX_PACKET_SIZE = 16384
DATA_LENGTH = 1024


def add_line(line, message):
    message += line + SEP
    return message


def ack_message(filename, offset):
    message = ''
    message = add_line('ACK', message)
    message = add_line(filename, message)
    message = add_line(str(offset), message)
    return message


def download_message(file, filename, offset, total_length, max_data_length):
    message = ''
    message = add_line('DOWNLOAD', message)
    message = add_line(filename, message)
    message = add_line(str(offset), message)
    message = add_line(str(total_length), message)
    data = file.read(max_data_length)
    message = add_line("DATA", message)
    message = message.encode() + data
    return message, len(data)


def handle_file_reception(a_socket, an_address, filename, total_length, storage_dir):
    try:
        path = storage_dir + '/' + filename
        file = open(path, 'wb')
    except IOError:
        error_message = ''
        add_line('ERROR', error_message)
        a_socket.sendto(error_message.encode(), an_address)
        return

    first_ack = ack_message(filename, 0)
    a_socket.sendto(first_ack.encode(), an_address)
    print(first_ack)
    total_received = 0

    while total_received < total_length:
        timeouts = 0
        sender_address = None
        while sender_address != an_address and timeouts < 3:
            try:
                raw_received, sender_address = a_socket.recvfrom(MAX_PACKET_SIZE)
                print(raw_received)
            except timeout:
                print("Timeout")
                a_socket.sendto(ack_message(filename, total_received).encode(), an_address)
                timeouts += 1
        if timeouts == 3:
            break

        headers_and_data = raw_received.split(bytes('DATA' + SEP, encoding='utf-8'), 1)
        headers = headers_and_data[0].decode().split(SEP)
        data = headers_and_data[1]
        offset = int(headers[2])

        if offset != total_received:
            a_socket.sendto(ack_message(filename, total_received).encode(), an_address)
            continue
        print("Recibida: {}".format(data))
        file.write(data)
        total_received += len(data)
        a_socket.sendto(ack_message(filename, total_received).encode(), an_address)


def handle_file_sending(a_socket, an_address, filename, storage_dir):
    path = storage_dir + '/' + filename
    if not os.path.isfile(path):
        a_socket.sendto(ERROR_MESSAGE.encode(), an_address)
        return

    total_length = os.path.getsize(path)
    f = open(path, 'rb')
    total_sent = 0
    while total_sent < total_length:
        to_send, data_length = download_message(f, filename, total_sent, total_length, DATA_LENGTH)
        total_sent += data_length
        acked = False
        timeouts = 0

        while not acked and timeouts < 3:
            print("Envío")
            a_socket.sendto(to_send, an_address)
            print("Recibo ack")
            sender_address = None

            while sender_address != an_address:
                try:
                    raw_data, sender_address = a_socket.recvfrom(MAX_PACKET_SIZE)
                except timeout:
                    timeouts += 1
                    break

            if sender_address != an_address:
                continue

            message = raw_data.decode().split(SEP)
            if int(message[1]) == total_sent:
                acked = True
        if not acked:
            break
    f.close()


def start_server(server_address, storage_dir):
    print('UDP: start_server({}, {})'.format(server_address, storage_dir))

    if not os.path.isdir(storage_dir):
        os.makedirs(storage_dir)

    server_socket = socket(AF_INET, SOCK_DGRAM)
    server_socket.bind(server_address)

    while True:
        # Mensaje inicial de la transmision
        print("Esperando cliente")
        raw_data, client_address = server_socket.recvfrom(MAX_PACKET_SIZE)
        message = raw_data.decode()
        headers = message.split(SEP)
        is_upload = headers[0].upper() == 'UPLOAD'
        file_name = headers[1]
        total_length = 0
        if is_upload:  # Upload
            total_length = int(headers[2])
            handle_file_reception(server_socket, client_address, file_name, total_length, storage_dir)
        else:  # Download
            handle_file_sending(server_socket, client_address, file_name, storage_dir)
