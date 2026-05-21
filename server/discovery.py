#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
服务端 UDP 广播服务
定时广播服务器地址，供客户端自动发现
"""

import socket
import json
import threading
import time


BROADCAST_PORT = 15432
BROADCAST_INTERVAL = 2


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class DiscoveryService:
    """UDP 广播服务，让客户端自动发现服务器"""

    def __init__(self, server_port=5000, server_name="待办事项提醒系统"):
        self.server_port = server_port
        self.server_name = server_name
        self.local_ip = get_local_ip()
        self._running = False
        self._thread = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._broadcast_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _broadcast_loop(self):
        msg = json.dumps({
            "name": self.server_name,
            "ip": self.local_ip,
            "port": self.server_port,
        }, ensure_ascii=False).encode("utf-8")

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        while self._running:
            try:
                sock.sendto(msg, ("255.255.255.255", BROADCAST_PORT))
            except Exception:
                pass
            time.sleep(BROADCAST_INTERVAL)

        sock.close()
