import re
import base64


class Parser:
    def __init__(self):
        self.attachment_regex = re.compile(r"(\d+) NIL \(\"attachment\" \(\"filename\" \"(.*?)\"\)")
        self.from_regex = re.compile(r"\nFrom: (.*?)\r\n\w".encode(), flags=re.M | re.S)
        self.date_regex = re.compile(r"\nDate: (.*?)\r\n".encode())
        self.to_regex = re.compile(r"\nTo: (.*?)\r\n".encode())
        self.subject_regex = re.compile(r"\nSubject:(.*?)\r\n\w".encode(), flags=re.M | re.S)
        self.size_regex = re.compile(r" \(RFC822.SIZE (.*)\)")
        self.letter_numbers_regex = re.compile(r"^\* SEARCH (.*)\r\n")

    @staticmethod
    def decode_header(data: bytes):
        data = data.decode()
        if '=?' not in data:
            return data
        data = data.split()
        res = ""
        for element in data:
            if "=?" in element:
                data_regex = re.compile(r"\?b\?(.*)\?=")
                st = data_regex.findall(element)[0]
                code_regex = re.compile(r"=\?(.*)\?b")
                code = code_regex.findall(element)[0]
                res += base64.b64decode(st).decode(code)
            else:
                res += element
        return res

    def parse_header(self, data):
        data = data
        sender = self.from_regex.findall(data)[0]
        date = self.date_regex.findall(data)[0]
        receiver = self.to_regex.findall(data)[0]
        subject = self.subject_regex.findall(data)[0]
        return self.decode_header(sender), self.decode_header(receiver), \
               self.decode_header(subject), self.decode_header(date)

    def get_message_info(self, sock, number, counter):
        sock.send(f'A{counter} FETCH {number} BODY[HEADER]\r\n'.encode())
        data = b''
        while True:
            s = sock.recv(1024)
            data += s
            if b'OK FETCH done\r\n' in data:
                break
        sender, receiver, subject, date = self.parse_header(data)
        sock.send(f'A{counter + 1} FETCH {number} RFC822.SIZE\r\n'.encode())
        data1 = sock.recv(1024).decode()
        size = self.size_regex.findall(data1)[0]
        return sender, receiver, subject, date, size

    def get_message_attachments(self, sock, number, counter):
        sock.send(f'A{counter} FETCH {number} BODYSTRUCTURE\r\n'.encode())
        data = b''
        while True:
            s = sock.recv(1024)
            data += s
            if b'OK FETCH done\r\n' in data:
                break
        data = data.decode()
        attachments = self.attachment_regex.findall(data)
        return attachments

    def get_messages_numbers(self, sock, all_letters: bool, start_index: int, end_index: int, counter):
        sock.send(f'A{counter} SEARCH ALL\r\n'.encode())
        data = sock.recv(1024).decode()
        numbers = self.letter_numbers_regex.findall(data)
        numbers = numbers[0].split()
        for i in range(len(numbers)):
            numbers[i] = int(numbers[i])
        if (end_index != -1 and end_index not in numbers) or (start_index != -1 and start_index not in numbers):
            print("There are no messages with entered number")
            exit(0)
        if end_index == -1 and start_index != -1:
            return [start_index]
        elif end_index != -1 and start_index != -1:
            return numbers[start_index - 1: end_index]
        return numbers
