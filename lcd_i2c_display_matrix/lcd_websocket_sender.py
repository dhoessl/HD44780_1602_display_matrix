from socket import socket, AF_INET, SOCK_STREAM
from json import dumps

# Exmaple Usage:
# if __name__ == "__main__":
#     sender = MatricCommandSender("10.10.10.5", 80)
#     sender.do_selftest()
#     sender.send("on_next", ["print me", None], "printer")
#     sender.send("on_next", ["This is", "a text"], "texting")
#     for x in range(20):
#         sender.send("on_next", ["Some Value", f"{x}"], "value")
#     for x in range(20):
#         sender.send("on_next", ["Some Value", f"{x}"], f"value{x}")
#     sender.do_exit()


class MatrixCommandSender:
    def __init__(self, address, port) -> None:
        self.address = address
        self.port = port

    def send(self, command: str, lines: list, id: str) -> None:
        output = dumps({
            "print": command,
            "data": {
                "lines": lines,
                "id": id
            }
        })
        self.use_socket(output)

    def lock_by_id(self, id: str) -> None:
        self.use_socket(
            dumps({
                "lock": True,
                "data": {
                    "id": id
                }
            })
        )

    def lock_by_index(self, index: int) -> None:
        self.use_socket(
            dumps({
                "lock": True,
                "data": {
                    "index": index
                }
            })
        )

    def unlock_by_id(self, id: str) -> None:
        self.use_socket(
            dumps({
                "unlock": True,
                "data": {
                    "id": id
                }
            })
        )

    def unlock_by_index(self, index: int) -> None:
        self.use_socket(
            dumps({
                "unlock": True,
                "data": {
                    "index": index
                }
            })
        )

    def do_selftest(self) -> None:
        self.use_socket(dumps({"selftest": True}))

    def do_exit(self) -> None:
        self.use_socket(dumps({"exit": True}))

    def use_socket(self, msg) -> None:
        with socket(AF_INET, SOCK_STREAM) as s:
            s.connect((self.address, self.port))
            s.sendall((msg + "\n\n").encode("UTF-8"))
