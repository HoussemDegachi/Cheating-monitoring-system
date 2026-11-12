import socket

def get_local_ipv4():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
    except socket.error:
        local_ip = None
    finally:
        s.close()
    return local_ip

def is_port_open(ip, port, timeout=2):
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except OSError:
        return False
    