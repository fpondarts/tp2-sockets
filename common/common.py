from constants.constants import HEADER_SEP


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
