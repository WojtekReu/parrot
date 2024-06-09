import json
import selectors
import socket
import types


def start_connections(sel, host, port, num_conns, word):
    server_addr = (host, port)
    for connid in range(1, num_conns + 1):
        # print(f"Starting connection {connid} to {server_addr}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        sock.connect_ex(server_addr)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        data = types.SimpleNamespace(
            connid=connid,
            msg_total=len(word),
            recv_total=0,
            messages=word,
            outb=b"",
            received=b"",
        )
        sel.register(sock, events, data=data)


def service_connection(sel, key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if recv_data:
            # print(f"Received {recv_data!r} from connection {data.connid}")
            data.recv_total += len(recv_data)
            data.received += recv_data
        if not recv_data or recv_data.endswith(b"\x00"):
            # print(f"Closing connection {data.connid}")
            data.received = data.received.strip(b"\x00")
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if not data.outb and data.messages:
            data.outb = data.messages
            data.messages = b''
        if data.outb:
            # print(f"Sending {data.outb!r} to connection {data.connid}")
            sent = sock.send(data.outb)  # Should be ready to write
            data.outb = data.outb[sent:]


def find_definition(word: str, sentence: str) -> [tuple[str, str]]:
    sel = selectors.DefaultSelector()
    message = {"word": word, "sentence": sentence}
    host, port, num_conns = '127.0.0.1', 65432, 1
    start_connections(sel, host, int(port), int(num_conns), json.dumps(message).encode())
    response_str = ''
    try:
        while True:
            events = sel.select(timeout=1)
            if events:
                for key, mask in events:
                    service_connection(sel, key, mask)
                    if key.data.received:
                        response_str = key.data.received.decode().strip("\0")
            # Check for a socket being monitored to continue.
            if not sel.get_map():
                break
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
    finally:
        sel.close()
    # print(f"{response_str = }")
    response = json.loads(response_str)
    return response
