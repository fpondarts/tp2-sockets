from constants.constants import HEADER_SEP, MAX_PACKET_SIZE
from socket import timeout


def add_header(header, message):
    message += header + HEADER_SEP
    return message


def ack_message(filename, offset):
    message = ''
    message = add_header('ACK', message)
    message = add_header(filename, message)
    message = add_header(str(offset), message)
    return message


def log(msj, verbose):
    if (verbose):
        print(msj)


def fin_message(filename):
    message = ''
    message = add_header('FIN', message)
    message = add_header(filename, message)
    return message


def handle_fin_receptor(a_socket, an_address, filename,
                        total_length, verbose=False):
    print("Receptor en etapa de FIN")
    fin_arrived = False
    a_socket.settimeout(3)
    timeouts = 0
    while not fin_arrived and timeouts < 10:
        sender_address = None
        while sender_address != an_address:
            try:
                raw_data, sender_address = a_socket.recvfrom(MAX_PACKET_SIZE)
            except timeout:
                timeouts += 1
                break
        if sender_address != an_address:
            continue
        log("Receptor recibe {}".format(raw_data), verbose)
        first_header = raw_data.split(bytes('DATA' + HEADER_SEP,
                                      encoding='utf-8'), 1)[0]\
                               .decode()[0].split(HEADER_SEP)[0]
        if first_header == 'FIN':
            log("Receptor saliendo de FIN", verbose)
            a_socket.sendto(ack_message(filename, 'FIN').encode(), an_address)
            fin_arrived = True
        else:
            a_socket.sendto(ack_message(filename,
                                        total_length).encode(), an_address)


def handle_fin_emisor(a_socket, an_address, filename,
                      total_length, verbose=False):
    print("Emisor en etapa de FIN")
    acked = False
    a_socket.settimeout(3)
    timeouts = 0
    while not acked and timeouts < 10:
        a_socket.sendto(fin_message(filename).encode(), an_address)
        sender_address = None
        while sender_address != an_address:
            try:
                raw_data, sender_address = a_socket.recvfrom(MAX_PACKET_SIZE)
            except timeout:
                timeouts += 1
                break
        if sender_address != an_address:
            continue
        log("Receptor emisor recibe {}".format(raw_data), verbose)
        headers = raw_data.split(bytes('DATA' + HEADER_SEP,
                                 encoding='utf-8'), 1)[0]\
                          .decode()[0].split(HEADER_SEP)
        if len(headers) >= 3:
            if headers[0] == 'ACK' and headers[1] == filename \
                                    and headers[2] == 'FIN':
                log("Emisor saliendo de FIN", verbose)
                acked = True
