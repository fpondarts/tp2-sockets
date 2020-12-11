import os
from socket import socket, timeout, AF_INET, SOCK_STREAM

SEP = '\r\n'
ERROR_MESSAGE = 'ERROR' + SEP
MAX_PACKET_SIZE = 4096
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

    # first_ack = ack_message(filename, 0)
    # a_socket.sendto(first_ack.encode(), an_address)
    # print(first_ack)
    total_received = 0

    while total_received < total_length:
        print("received loop, total_received", total_received)
        data = a_socket.recv(MAX_PACKET_SIZE)

        print("Recibida: {}".format(data))
        file.write(data)
        total_received += len(data)

    a_socket.close()


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
    print('TCP: start_server({}, {})'.format(server_address, storage_dir))

    if not os.path.isdir(storage_dir):
        os.makedirs(storage_dir)

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

            handle_file_reception(connection_socket, client_address, file_name, total_length, storage_dir)
        else:  # Download
            handle_file_sending(connection_socket, client_address, file_name, storage_dir)
