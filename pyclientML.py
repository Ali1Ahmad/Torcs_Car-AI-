import sys
import socket
import argparse
from MLdriver import MLDriver  # Make sure the filename is exactly MLdriver.py

# Initialize ML driver
d = MLDriver(stage="train")  # or "test" if you're in evaluation mode


# Parse command-line arguments
parser = argparse.ArgumentParser(description='ML TORCS Client')
parser.add_argument('--host-ip', default='localhost', help='TORCS server IP')
parser.add_argument('--host-port', type=int, default=3001, help='TORCS server port')
parser.add_argument('--id', default='SCR', help='Client ID')
parser.add_argument('--max-episodes', type=int, default=1, help='Max episodes to run')
parser.add_argument('--max-steps', type=int, default=0, help='Max steps per episode (0 = unlimited)')
args = parser.parse_args()

# Setup UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(1.0)

shutdownClient = False
curEpisode = 0

# --- Handshake with TORCS ---
connected = False
while not connected:
    try:
        print(f"🔌 Sending ID to server: {args.id}")
        buf = args.id + d.init()
        sock.sendto(buf.encode(), (args.host_ip, args.host_port))
        buf, addr = sock.recvfrom(1000)
        buf = buf.decode()
        if '***identified***' in buf:
            print("✅ Connected to TORCS:", buf)
            connected = True
    except socket.error as msg:
        print("⏳ Waiting for TORCS to accept connection:", msg)

# --- Main control loop ---
while not shutdownClient:
    currentStep = 0
    while True:
        try:
            buf, addr = sock.recvfrom(1000)
            buf = buf.decode()
        except socket.error as msg:
            print("⚠️ Receive error:", msg)
            continue

        if '***shutdown***' in buf:
            d.onShutDown()
            print("🛑 TORCS shutdown.")
            shutdownClient = True
            break

        if '***restart***' in buf:
            d.onRestart()
            print("🔁 Restart received.")
            break

        # Use ML model to drive
        action = d.drive(buf)

        try:
            sock.sendto(action.encode(), (args.host_ip, args.host_port))
        except socket.error as msg:
            print("❌ Send error:", msg)
            sys.exit(-1)

        currentStep += 1
        if args.max_steps > 0 and currentStep >= args.max_steps:
            print("⏹ Max steps reached.")
            break

    curEpisode += 1
    if curEpisode >= args.max_episodes:
        print("🏁 Max episodes done.")
        shutdownClient = True

sock.close()
print("🔚 Client socket closed.")
