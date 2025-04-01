import sys
import toml
import base64
import json
import socket

class HTTP_request:
    def __init__(self, list):
        self.sender = list[0]
        self.recipient = list[1]
        self.message = list[2]
        self.host = list[3]
        self.port = list[4]
        self.name = list[5]
        self.password = list[6]

    def to_bytes(self):
        auth_msg = f"{self.name}:{self.password}"
        msg_bytes = auth_msg.encode()
        bs64_msg = base64.b64encode(msg_bytes).decode()

        data = json.dumps({
            "sender":self.sender,
            "recipient":self.recipient,
            "message":self.message
        })

        http_request = (
            f"POST /send_sms HTTP/1.1\r\n"
            f"HOST: {self.host}:{self.port}\r\n"
            f"Content-Type: application/json\r\n"
            f"Authorization: Basic {bs64_msg}\r\n"
            f"Content-Length: {len(data)}\r\n"
            f"\r\n"
            f"{data}"
        )

        return http_request.encode()

    def from_bytes(self,bytes):
        data = bytes.decode()


class HTTP_response:
    def __init__(self):
        self.headers = ''
        self.body = ''

    def to_bytes(self):
        data = json.dump(self.body)

        http_response = (
            f"{self.headers}\r\n"
            f"\r\n"
            f"{data}"
        )

        return http_response.encode()

    def from_bytes(self, bytes):
        response_text = bytes.decode()
        code = int(response_text.split()[1])
        self.headers, self.body = response_text.split("\r\n\r\n", 1)
        return (code, self.body)


if __name__ == "__main__":
    sender = sys.argv[1]
    recipient = sys.argv[2]
    message = sys.argv[3]

    config = toml.load(open("config.toml","r"))
    url = config['url'].split(':')
    host = url[1][2::]
    port = int(url[2])
    name = config['name']
    password = config['password']

    data_list = (sender, recipient, message, host, port, name, password)

    http_request = HTTP_request(data_list).to_bytes()

    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    client.connect((host, port))

    client.sendall(http_request)

    response = client.recv(1024)

    http_response = HTTP_response().from_bytes(response)

    print(f"Код ответа: {http_response[0]}\nТело ответа: {http_response[1]}")

    client.close()

    file_log = open("log.txt","a")
    log = (
        f"--------------------------------------------------------------------------------\n"
        f"Аргументы командной строки:\n"
        f"Отправитель: {sender}\n"
        f"Получатель: {recipient}\n"
        f"Сообщение: {message}\n"
        f"Ответ сервиса:\n"
        f"Код ответа: {http_response[0]}\n"
        f"Тело ответа: {http_response[1]}\n"
        f"--------------------------------------------------------------------------------\n\n"
    )
    file_log.write(log)
    file_log.close()
