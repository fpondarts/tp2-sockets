from socket import socket, AF_INET, SOCK_STREAM

MAX_PACKET_SIZE = 4096
SEP = '\r\n'


def add_line(line, message):
    message += line + SEP
    return message


def initial_message(filename, length):
    message = ''
    message = add_line('INIT DOWNLOAD', message)
    message = add_line(filename, message)
    message = add_line(str(length), message)
    return message


def download_file(server_address, name, dst):
    print('TCP: download_file({}, {}, {})'.format(server_address, name, dst))
    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.connect(server_address)

    f = open(dst, 'wb')
    total_length = int(1e10)  # Muy alto
    client_socket.send(initial_message(name, total_length).encode())
    total_received = 0
    client_socket.settimeout(3)

    raw_message = client_socket.recv(MAX_PACKET_SIZE)
    print("raw_message", raw_message)
    data = raw_message.decode()
    print("data", data)
    file_info = data.split(SEP)
    is_download = file_info[0].upper() == 'DOWNLOAD'
    print("is_download", is_download)
    file_name = file_info[1]
    print("file_name", file_name)
    total_length = int(file_info[3])
    print("total_length", total_length)

    while total_received < total_length:
        print("Porcentaje recibido: {}%"
              .format(total_received / total_length * 100))
        data = client_socket.recv(MAX_PACKET_SIZE)

        f.write(data)
        total_received += len(data)

    client_socket.close()
