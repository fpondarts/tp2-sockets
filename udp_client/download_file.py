import os
from socket import socket, AF_INET, SOCK_DGRAM, timeout
from common.common import ack_message, add_header, log
MAX_PACKET_SIZE = 4096
SEP = '\r\n'


def initial_message(filename):
    message = ""
    message = add_header('INIT DOWNLOAD', message)
    message = add_header(filename, message)
    return message


def download_file(server_address, name, dst, verbose):
    print('UDP: download_file({}, {}, {})'.format(server_address, name, dst))
    client_socket = socket(AF_INET, SOCK_DGRAM)
    f = open(dst, 'wb')
    total_length = int(1e10)  # Muy alto
    client_socket.sendto(initial_message(name).encode(), server_address)
    total_received = 0
    client_socket.settimeout(3)

    while total_received < total_length:
        try:
            raw_received, sender_address = client_socket\
                .recvfrom(MAX_PACKET_SIZE)
        except timeout:
            if verbose:
                print("Timeout")
            if total_received == 0:
                client_socket.sendto(initial_message(name).encode(),
                                     server_address)
            continue

        if sender_address != server_address:
            continue

        headers_and_data = raw_received.\
            split(bytes('DATA' + SEP, encoding='utf-8'), 1)
        headers = headers_and_data[0].decode().split(SEP)

        if headers[0] != 'DOWNLOAD' and headers[1] != name:
            print("Ha ocurrido un error, fin de la descarga")
            break

        data = headers_and_data[1]

        offset = int(headers[2])
        log("Recibido paquete con offset {}".format(offset),
            verbose)
        if total_received == 0:
            total_length = int(headers[3])

        if offset != total_received:
            log("Envío ACK con offset {}".format(total_received), verbose)
            client_socket.sendto(ack_message(name, total_received).encode(),
                                 server_address)
            continue
        f.write(data)
        total_received += len(data)
        client_socket.sendto(ack_message(name, total_received).encode(),
                             server_address)
        log("Envío ACK con offset {}".format(total_received), verbose)

        print("Porcentaje recibido: {}%".format(
            total_received / total_length * 100))
    print("Fin de recepción")
    f.close()