from socket import socket, AF_INET, SOCK_STREAM
from selectors import DefaultSelector, EVENT_READ
from types import SimpleNamespace
from json import loads
from json.decoder import JSONDecodeError
from netifaces import ifaddresses
from time import sleep
from .matrix import Matrix as LCDMatrix

# Example usage:
# if __name__ == "__main__":
#     matrix = LCDMatrix([...])
#     server = MatrixCommandReceiver(matrix)
#     server.start()


class MatrixCommandReceiver:
    def __init__(self, matrix) -> None:
        if not isinstance(matrix, LCDMatrix):
            print("Given Matrix is not a valid 1602 LCDMatrix")
            exit(1)
        self.matrix = matrix
        self.state = False
        self.selector = DefaultSelector()
        self.selector.register(self._get_lsock(), EVENT_READ, data=None)

    def _get_lsock(self) -> socket:
        lsock = socket(AF_INET, SOCK_STREAM)
        connected = False
        while not connected:
            try:
                lsock.bind((ifaddresses("wlan0")[AF_INET][0]["addr"], 80))
                connected = True
            except (ValueError, KeyError):
                sleep(.1)
                continue
        lsock.listen()
        lsock.setblocking(False)
        return lsock

    def accept_wrapper(self, sock) -> None:
        conn, addr = sock.accept()
        conn.setblocking(False)
        data = SimpleNamespace(addr=addr, buffer="")
        self.selector.register(conn, EVENT_READ, data=data)

    def service_connection(self, key, mask) -> None:
        sock = key.fileobj
        data = key.data
        if mask & EVENT_READ:
            data.buffer = sock.recv(2048).decode()
            if not data.buffer:
                # Close connection because no data was send
                self.selector.unregister(sock)
                sock.close()
            parts = data.buffer.split("\n")
            msgs = parts[0:len(parts)-1]
            data.buffer = parts[len(parts)-1]
            for msg in msgs:
                if msg == "":
                    # Close connection because of connection end
                    # message was send (\n\n)
                    self.selector.unregister(sock)
                    sock.close()
                    continue
                try:
                    json_msg = loads(msg)
                except JSONDecodeError:
                    # not a valid json obj was send
                    continue
                if "exit" in json_msg and json_msg["exit"]:
                    self.matrix.exit()
                elif "selftest" in json_msg and json_msg["selftest"]:
                    self.matrix.self_test()
                elif "lock" in json_msg and json_msg["lock"]:
                    if "data" not in json_msg:
                        continue
                    if "id" in json_msg["data"]:
                        self.matrix.lock_display(id=json_msg["data"]["id"])
                    elif "index" in json_msg["data"]:
                        self.matrix.lock_display(
                            index=json_msg["data"]["index"]
                        )
                elif "unlock" in json_msg and json_msg["unlock"]:
                    if "data" not in json_msg:
                        continue
                    if "id" in json_msg["data"]:
                        self.matrix.unlock_display(
                            id=json_msg["data"]["id"]
                        )
                    elif "index" in json_msg["data"]:
                        self.matrix.unlock_display(
                            id=json_msg["data"]["index"]
                        )
                elif "print" in json_msg and json_msg["print"]:
                    if "data" not in json_msg:
                        # no data key was send
                        continue
                    if json_msg["print"] == "on_id":
                        self.matrix.display_on_id(
                            json_msg["data"]["lines"],
                            json_msg["data"]["id"]
                        )
                    if json_msg["print"] == "on_next":
                        self.matrix.display_on_next(
                            json_msg["data"]["lines"],
                            json_msg["data"]["id"]
                        )
                    if json_msg["print"] == "on_next_or_id":
                        self.matrix.display_on_next_or_id(
                            json_msg["data"]["lines"],
                            json_msg["data"]["id"]
                        )
                    if json_msg["print"] == "on_shift":
                        self.matrix.display_and_shift(
                            json_msg["data"]["lines"],
                            json_msg["data"]["id"]
                        )

    def start(self) -> None:
        try:
            self.state = True
            self.matrix.display_on_next(
                ["Receiver Ready", ifaddresses("wlan0")[AF_INET][0]["addr"]],
                "service"
            )
            while self.state:
                events = self.selector.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        self.accept_wrapper(key.fileobj)
                    else:
                        self.service_connection(key, mask)
        except KeyboardInterrupt:
            pass
        finally:
            self.selector.close()
