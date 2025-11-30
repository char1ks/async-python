import asyncio
import websockets
import datetime
import time
from collections import deque
import threading
from flask import Flask, render_template, jsonify, request
import psutil
import json

connections = 0
total_messages = 0
message_timestamps = deque()
rps_history = []  # Для графика RPS

def run_flask():
    app = Flask(__name__, template_folder='templates', static_folder='static')

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/metrics')
    def metrics():
        now = time.time()
        while message_timestamps and message_timestamps[0] < now - 1:
            message_timestamps.popleft()
        rps = len(message_timestamps)
        rps_history.append(rps)
        if len(rps_history) > 60:  # Храним последние 60 сек
            rps_history.pop(0)

        cpu_percent = psutil.cpu_percent(interval=0.1)
        net_io = psutil.net_io_counters()
        net_sent = net_io.bytes_sent
        net_recv = net_io.bytes_recv

        return jsonify({
            'rps': rps,
            'connections': connections,
            'total_messages': total_messages,
            'rps_history': rps_history,
            'cpu_percent': cpu_percent,
            'net_sent': net_sent,
            'net_recv': net_recv
        })

    app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)

async def monitor():
    global message_timestamps, total_messages, connections
    while True:
        now = time.time()
        while message_timestamps and message_timestamps[0] < now - 1:
            message_timestamps.popleft()
        print(f"[{datetime.datetime.now()}] RPS: {len(message_timestamps)} | Total connections: {connections} | Total messages: {total_messages}")
        await asyncio.sleep(1)

async def handle(websocket):
    global connections, total_messages, message_timestamps
    connections += 1
    print(f"[{datetime.datetime.now()}] New connection. Total connections: {connections}")
    try:
        async for message in websocket:
            total_messages += 1
            message_timestamps.append(time.time())
            await websocket.send(f"Echo: {message}")
    except Exception as e:
        print(f"[{datetime.datetime.now()}] Error: {e}")
    finally:
        connections -= 1
        print(f"[{datetime.datetime.now()}] Connection closed. Total connections: {connections}")

async def main():
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    async with websockets.serve(handle, "0.0.0.0", 8765):
        print(f"[{datetime.datetime.now()}] WebSocket server started at ws://0.0.0.0:8765")
        print(f"[{datetime.datetime.now()}] Flask UI started at http://0.0.0.0:5001")
        await asyncio.gather(monitor())

if __name__ == "__main__":
    asyncio.run(main())