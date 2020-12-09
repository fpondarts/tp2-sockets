import os
import time
from socket import socket, timeout, AF_INET, SOCK_DGRAM

SEP = '\r\n'
ERROR_MESSAGE = 'ERROR'+SEP
MAX_PACKET_SIZE = 16384
DATA_LENGTH = 1024

def add_line(line, message):
  message += line + SEP
  return message

def ack_message(filename, offset):
  message = ''
  message = add_line('ACK',message)
  message = add_line(filename, message)
  message = add_line(str(offset), message)
  return message

def download_message(file, filename, offset, total_length, max_data_length):
  message = ''
  message = add_line('DOWNLOAD', message)
  message = add_line(filename, message)
  message = add_line(str(offset),message)
  message = add_line(str(total_length),message)
  data = file.read(max_data_length)
  message = add_line("DATA", message)
  message = message.encode() + data
  return message, len(data)

def handle_file_reception(aSocket, anAddress, filename, total_length, storage_dir):
  try:
    path = storage_dir+'/'+filename
    file = open(path, 'wb')
  except IOError:
    errorMessage = ''
    add_line('ERROR', errorMessage)
    aSocket.sendto(errorMessage.encode(), anAddress)
    return

  first_ack = ack_message(filename, 0)
  aSocket.sendto(first_ack.encode(), anAddress)
  print(first_ack)
  total_received = 0

  while total_received < total_length:
    timeouts = 0
    sender_address = None
    while sender_address != anAddress and timeouts < 3:
      try: 
        raw_received, sender_address = aSocket.recvfrom(MAX_PACKET_SIZE)
        print(raw_received)
      except timeout:
        print("Timeout")
        aSocket.sendto(ack_message(filename, total_received).encode(), anAddress)
        timeouts += 1
    if timeouts == 3:
      break

    headers_and_data = raw_received.split(bytes('DATA'+SEP, encoding='utf-8'), 1)
    headers = headers_and_data[0].decode().split(SEP)
    data = headers_and_data[1]
    offset = int(headers[2])

    if (offset != total_received):
      aSocket.sendto(ack_message(filename, total_received).encode(), anAddress)
      continue
    print("Recibida: {}".format(data))
    file.write(data)
    total_received += len(data)
    aSocket.sendto(ack_message(filename, total_received).encode(), anAddress)

def handle_file_sending(aSocket, anAddress, filename, storage_dir):
  path = storage_dir + '/' + filename
  if not os.path.isfile(path):
    aSocket.sendto(ERROR_MESSAGE.encode(), anAddress)
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
      aSocket.sendto(to_send, anAddress)
      print("Recibo ack")
      senderAddress = None
      
      while senderAddress != anAddress:
        try:
          raw_data, senderAddress = aSocket.recvfrom(MAX_PACKET_SIZE)
        except timeout:
          timeouts += 1
          break
      
      if senderAddress != anAddress:
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

  serverSocket = socket(AF_INET, SOCK_DGRAM)
  serverSocket.bind(server_address)

  while True:
    # Mensaje inicial de la transmision
    print("Esperando cliente")
    raw_data, clientAddress = serverSocket.recvfrom(MAX_PACKET_SIZE)
    message = raw_data.decode()
    headers = message.split(SEP)
    is_upload = headers[0].upper() == 'UPLOAD'
    file_name = headers[1]
    total_length = 0
    if (is_upload): # Upload
      total_length = int(headers[2])
      handle_file_reception(serverSocket, clientAddress, file_name, total_length, storage_dir)
    else: # Download
      handle_file_sending(serverSocket, clientAddress, file_name, storage_dir)
  
      
