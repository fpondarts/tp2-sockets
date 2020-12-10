from socket import socket, AF_INET, SOCK_DGRAM, timeout

MAX_PACKET_SIZE = 16384
SEP = '\r\n'


def add_line(line, message):
    message += line + SEP
    return message


def ack_message(sequence_num):
    message = 'ACK' + SEP
    message += str(sequence_num) + SEP
    return message


def initial_message(filename):
    message = ""
    message = add_line('DOWNLOAD', message)
    message = add_line(filename, message)
    return message


def download_file(server_address, name, dst):
    print('UDP: download_file({}, {}, {})'.format(server_address, name, dst))

    client_socket = socket(AF_INET, SOCK_DGRAM)
    f = open(dst, 'wb')
    total_length = int(1e10)  # Muy alto
    client_socket.sendto(initial_message(name).encode(), server_address)
    total_received = 0
    while total_received < total_length:
        try:
            raw_received, sender_address = client_socket.recvfrom(MAX_PACKET_SIZE)
        except timeout:
            if total_received == 0:
                client_socket.sendto(initial_message(name).encode(), server_address)
            else:
                client_socket.sendto(ack_message(total_received).encode(), server_address)
            continue

        if sender_address != server_address:
            continue

        print(raw_received)
        headers_and_data = raw_received.split(bytes('DATA' + SEP, encoding='utf-8'), 1)
        headers = headers_and_data[0].decode().split(SEP)

        if headers[0] != 'DOWNLOAD' and headers[1] != name:
            print("Ha habido un error en el servidor, fin de la descarga")
            return

        data = headers_and_data[1]

        offset = int(headers[2])

        if total_received == 0:
            total_length = int(headers[3])

        if offset != total_received:
            client_socket.sendto(ack_message(total_received).encode(), server_address)
            continue
        f.write(data)
        total_received += len(data)
        client_socket.sendto(ack_message(total_received).encode(), server_address)
