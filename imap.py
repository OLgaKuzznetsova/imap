import getpass
import socket
import ssl
import base64
from parse_email import Parser


class IMAP:
    def __init__(self, use_ssl: bool, server_address: str, port: int, mail_range, user: str):
        self.user = user
        self.port = port
        self.use_ssl = use_ssl
        self.server_address = server_address
        self.mail_range = mail_range
        self.sock = None
        self.password = None
        self.all_letters = False
        self.start_index = -1
        self.end_index = -1
        self.make_range_of_letters()
        self.ssl_socket = None
        self.counter = 1
        self.parser = Parser()
        self.ssl_context = ssl.create_default_context()

    def start(self):
        self.connect_to_server()
        print((self.sock.recv(1024).decode()))
        self.auth()
        self.sock.send(f'A{self.counter} SELECT INBOX\r\n'.encode())
        self.counter += 1
        self.sock.recv(1024).decode()
        numbers_of_letters = self.parser.get_messages_numbers(self.sock, self.all_letters, self.start_index,
                                                              self.end_index, self.counter)
        self.counter += 1
        for number in numbers_of_letters:
            sender, receiver, subject, date, size = self.parser.get_message_info(self.sock, int(number), self.counter)
            self.counter += 2
            attaches = self.parser.get_message_attachments(self.sock, int(number), self.counter)
            self.counter += 1
            print(f'ID: {int(number)}\n'
                  f'SENDER: {sender}\n'
                  f'RECEIVER: {receiver}\n'
                  f'SUBJECT: {subject}\n'
                  f'DATE: {date}\n'
                  f'SIZE: {size} bytes')
            if attaches:
                print(f'ATTACHES ({len(attaches)}):')
                print('\n'.join(map(lambda x: f'{x[0] + 1}. {x[1][1]}: {x[1][0]} bytes', enumerate(attaches))))
            print()
        self.sock.send(f"A{self.counter} logout\r\n".encode())

    def stop(self):
        if self.sock:
            self.sock.close()

    def connect_to_server(self):
        try:
            self.sock = socket.create_connection((self.server_address, self.port))
        except Exception as error:
            print(error)
            exit(0)

        if self.use_ssl:
            print('Trying to establish a secure connection')
            self.ssl_socket = self.sock
            try:
                self.sock = self.ssl_context.wrap_socket(self.sock, server_hostname=self.server_address)
            except ssl.SSLError:
                print('Can not establish secure connection')
                self.sock = socket.create_connection((self.connect_to_server(), self.port))
            else:
                print('Secure connection has established')
                return
            print('Trying to establish secure connection using STARTTLS')
            self.sock.send(f'A{self.counter} STARTTLS\r\n'.encode())
            self.counter += 1
            data = self.sock.recv(1024)
            print(data.decode())
            if b'NO' not in data and b'BAD' not in data:
                print('Secure connection with STARTTLS has established')
                return
        print('You use unsafe connection.')

    def make_range_of_letters(self):
        if len(self.mail_range) == 0:
            self.all_letters = True
        elif len(self.mail_range) == 1:
            self.start_index = self.mail_range[0]
        else:
            self.start_index = self.mail_range[0]
            self.end_index = self.mail_range[1]

    def auth(self):
        while True:
            if len(self.user) == 0:
                self.user = input('Enter username: ')
            self.password = getpass.getpass('Enter password: ')
            self.sock.send(f"A{self.counter} AUTHENTICATE PLAIN\r\n".encode())
            self.sock.recv(1024).decode()
            self.counter += 1
            qwe = self.encode_user_and_password()
            self.sock.send(qwe + "\r\n".encode())
            response = self.sock.recv(1024).decode()
            print(response)
            '''self.sock.send(f'A{self.counter} LOGIN {self.user} {self.password}\r\n'.encode())
            self.counter += 1
            response = self.sock.recv(1024).decode()
            print(response)'''
            if ('A' + str(self.counter - 1) + ' OK') in response:
                print('Authentication successful\n')
                break
            print('Login or password is not correct')
            self.user = ""

    def encode_user_and_password(self):
        byte_str = ("\x00" + self.user + "\x00" + self.password).encode()
        base64_str = base64.b64encode(byte_str)
        return base64_str


