import os
from socket import socket, timeout, AF_INET, SOCK_DGRAM
from constants.constants import HEADER_SEP, MAX_PACKET_SIZE, \
                      TIMEOUT_SECONDS, MAX_TIMEOUTS
from common.common import add_header, ack_message, log,\
    handle_fin_emisor, handle_fin_receptor

ERROR_MESSAGE = 'ERROR' + HEADER_SEP
DATA_LENGTH = 1024


def download_message(file, filename, offset, total_length, max_data_length):
    message = ''
    message = add_header('DOWNLOAD', message)
    message = add_header(filename, message)
    message = add_header(str(offset), message)
    message = add_header(str(total_length), message)
    data = file.read(max_data_length)
    message = add_header("DATA", message)
    message = message.encode() + data
    return message, len(data)


def handle_file_reception(a_socket, an_address, filename,
                          total_length, storage_dir, verbose):

    path = storage_dir + '/' + filename
    file = open(path, 'wb')

    a_socket.settimeout(TIMEOUT_SECONDS)
    first_ack = ack_message(filename, 0)
    a_socket.sendto(first_ack.encode(), an_address)
    total_received = 0

    while total_received < total_length:
        print("Porcentaje recibido: {}%"
              .format(total_received / total_length * 100))
        timeouts = 0
        sender_address = None
        while sender_address != an_address and timeouts < MAX_TIMEOUTS:
            try:
                raw_received, sender_address = a_socket.\
                    recvfrom(MAX_PACKET_SIZE)
            except timeout:
                log("Timeout {}".format(timeouts), verbose)
                a_socket.sendto(ack_message(filename,
                                total_received).encode(), an_address)
                timeouts += 1

        headers_and_data = raw_received.split(bytes('DATA' + HEADER_SEP,
                                                    encoding='utf-8'), 1)
        headers = headers_and_data[0].decode().split(HEADER_SEP)
        data = headers_and_data[1]
        offset = int(headers[2])

        if offset != total_received:
            a_socket.sendto(ack_message(filename,
                            total_received).encode(), an_address)
            continue
        file.write(data)
        total_received += len(data)
        log("Se envia ACK con offset {}".format(total_received), verbose)
        a_socket.sendto(ack_message(filename,
                        total_received).encode(), an_address)
    handle_fin_receptor(a_socket, an_address, filename, total_length, verbose)
    print("Fin de recepción")


def handle_file_sending(a_socket, an_address,
                        filename, storage_dir, verbose):
    a_socket.settimeout(TIMEOUT_SECONDS)
    path = storage_dir + '/' + filename
    if not os.path.isfile(path):
        a_socket.sendto(ERROR_MESSAGE.encode(), an_address)
        return

    total_length = os.path.getsize(path)
    f = open(path, 'rb')
    total_sent = 0
    while total_sent < total_length:
        print("Porcentaje enviado: {}%"
              .format(total_sent / total_length * 100))
        to_send, data_length = download_message(f,
                                                filename, total_sent,
                                                total_length, DATA_LENGTH)
        total_sent += data_length
        acked = False
        timeouts = 0
        send_message = True
        while (not acked and timeouts < MAX_TIMEOUTS):
            if send_message:
                log("Se envia paquete con offset {} y {} bytes de datos"
                    .format(total_sent - data_length, data_length), verbose)
                a_socket.sendto(to_send, an_address)
            sender_address = None
            while sender_address != an_address:
                try:
                    raw_data, sender_address = a_socket.\
                        recvfrom(MAX_PACKET_SIZE)
                except timeout:
                    send_message = True
                    timeouts += 1
                    log("Timeout nro {}".format(timeouts),
                        verbose)
                    break

            if sender_address != an_address:
                continue

            message = raw_data.decode().split(HEADER_SEP)
            if message[0] == 'ACK' and message[1] == filename:
                send_message = False
                log("Recibido ACK con offset {}".format(message[2]),
                    verbose)
                if int(message[2]) == total_sent:
                    acked = True
        if not acked:
            break
    handle_fin_emisor(a_socket, an_address, filename, total_length, verbose)
    print("Fin de transmisión")
    f.close()


def start_server(server_address, storage_dir, verbose):
    print('UDP: start_server({}, {})'.format(server_address, storage_dir))

    if not os.path.isdir(storage_dir):
        os.makedirs(storage_dir)

    server_socket = socket(AF_INET, SOCK_DGRAM)
    server_socket.bind(server_address)

    while True:
        # Mensaje inicial de la transmision
        server_socket.settimeout(None)
        print("Esperando cliente")
        raw_data, client_address = server_socket.recvfrom(MAX_PACKET_SIZE)
        message = raw_data.decode()
        headers = message.split(HEADER_SEP)
        first_header = headers[0].upper()
        file_name = headers[1]
        total_length = 0
        if first_header == 'INIT UPLOAD':  # Upload
            total_length = int(headers[2])
            print("Inicio de subida de archivo {}, por cliente {}"
                  .format(file_name, client_address))
            handle_file_reception(server_socket, client_address, file_name,
                                  total_length, storage_dir, verbose)
        elif first_header == 'INIT DOWNLOAD':  # Download
            print("Inicio de descarga de archivo {}, por cliente {}"
                  .format(file_name, client_address))
            handle_file_sending(server_socket, client_address,
                                file_name, storage_dir, verbose)
