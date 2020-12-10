import os
from socket import socket, SOCK_DGRAM, AF_INET, timeout
from common.common import add_header
from constants.constants import MAX_TIMEOUTS, MAX_PACKET_SIZE, HEADER_SEP, TIMEOUT_SECONDS

DATA_LENGTH = 1024


def initial_message(name, length):
    message = ''
    message = add_header('INIT UPLOAD', message)
    message = add_header(name, message)
    message = add_header(str(length), message)

    return message


def upload_message(name, offset, file):
    message = ''
    message = add_header('UPLOAD', message)
    message = add_header(name, message)
    message = add_header(str(offset), message)
    data = file.read(DATA_LENGTH)
    message = add_header("DATA", message)
    message = message.encode() + data
    return message, len(data)


def upload_file(server_address, src, name):
    print('UDP: upload_file({}, {}, {})'.format(server_address, src, name))

    if not os.path.isfile(src):
        print("Error: el archivo no existe")
        return

    client_socket = socket(AF_INET, SOCK_DGRAM)
    client_socket.settimeout(TIMEOUT_SECONDS)
    total_length = os.path.getsize(src)
    total_uploaded = 0
    f = open(src, 'rb')
    first_acked = False
    total_uploaded = 0
    while total_uploaded < total_length:
        print("")
        print("Subidos: {} de {} [{}%]".format(total_uploaded,
                                              total_length,
                                              total_uploaded / total_length * 100))
        if not first_acked:
            to_send = initial_message(name, total_length).encode()
            data_length = 0
        else:
            to_send, data_length = upload_message(name, total_uploaded, f)

        total_uploaded += data_length
        acked = False
        send_message = True
        timeouts = 0
        while not acked and timeouts < MAX_TIMEOUTS:
            if send_message:
                client_socket.sendto(to_send, server_address)
            sender_address = None
            while sender_address != server_address:
                try:
                    raw_data, sender_address = client_socket.\
                        recvfrom(MAX_PACKET_SIZE)
                except timeout:
                    timeouts += 1
                    send_message = True
                    print("Timeout {}".format(timeouts))
                    break
            if sender_address != server_address:
                continue
            headers = raw_data.decode().split(HEADER_SEP)
            if headers[0] == 'ACK' and headers[1] == name:
                send_message = False
                if int(headers[2]) == total_uploaded:
                    first_acked = True
                    acked = True
