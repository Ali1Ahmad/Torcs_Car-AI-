import sys
import argparse
import socket
import driver
import csv
import os
import re
import keyboard

if __name__ == '__main__':
    pass

# Configure the argument parser
parser = argparse.ArgumentParser(description='Python client to connect to the TORCS SCRC server.')

parser.add_argument('--host', action='store', dest='host_ip', default='localhost',
                    help='Host IP address (default: localhost)')
parser.add_argument('--port', action='store', type=int, dest='host_port', default=3001,
                    help='Host port number (default: 3001)')
parser.add_argument('--id', action='store', dest='id', default='SCR',
                    help='Bot ID (default: SCR)')
parser.add_argument('--maxEpisodes', action='store', dest='max_episodes', type=int, default=1,
                    help='Maximum number of learning episodes (default: 1)')
parser.add_argument('--maxSteps', action='store', dest='max_steps', type=int, default=0,
                    help='Maximum number of steps (default: 0)')
parser.add_argument('--track', action='store', dest='track', default=None,
                    help='Name of the track')
parser.add_argument('--stage', action='store', dest='stage', type=int, default=3,
                    help='Stage (0 - Warm-Up, 1 - Qualifying, 2 - Race, 3 - Unknown)')

arguments = parser.parse_args()

# Print summary
print('Connecting to server host ip:', arguments.host_ip, '@ port:', arguments.host_port)
print('Bot ID:', arguments.id)
print('Maximum episodes:', arguments.max_episodes)
print('Maximum steps:', arguments.max_steps)
print('Track:', arguments.track)
print('Stage:', arguments.stage)
print('*********************************************')

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
except socket.error as msg:  # FIXED
    print('Could not make a socket:', msg)
    sys.exit(-1)

# one second timeout
sock.settimeout(1.0)

shutdownClient = False
curEpisode = 0

verbose = True

d = driver.Driver(arguments.stage)

# Global dictionary to store the current key states
key_states = {
    "accelerate": 0,  # 'W' key
    "brake": 0,       # 'S' key
    "steer_left": 0,   # 'A' key
    "steer_right": 0   # 'D' key
}




while not shutdownClient:
    while True:

        print('Sending id to server: ', arguments.id)
        buf = arguments.id + d.init()
        print('Sending init string to server:', buf)

        try:
            sock.sendto(buf.encode(), (arguments.host_ip, arguments.host_port))  # Encode string before sending
        except socket.error as msg:  # FIXED
            print("Failed to send data...Exiting...", msg)
            sys.exit(-1)

        try:
            buf, addr = sock.recvfrom(1000)
            buf = buf.decode()  # Decode received bytes
        except socket.error as msg:  # FIXED
            print("Didn't get response from server...", msg)

        if buf and '***identified***' in buf:
            print('Received: ', buf)
            
        if buf and '***identified***' in buf:
            print('Received:', buf)
            track_match = re.search(r'\(track ([^)]+)\)', buf)  # Try to extract track name
            if track_match:
                track_name = track_match.group(1)
                print("Detected Track Name:", track_name)
            
            break


    currentStep = 0
    # Define the CSV file
    csv_filename = "telemetry_data.csv"
    csv_headers = [
        "Step", "track_name", "angle", "curLapTime", "distFromStart", "distRaced", 
        "fuel", "gear", "lastLapTime", "racePos", "rpm", "speedX", "speedY", "speedZ",
        "trackPos", "wheelSpinVel", "z",
        "accelerate", "brake", "steer_left", "steer_right"
    ]


    # Add 19 track sensor values
    for i in range(19):
        csv_headers.append(f"track_{i}")

    # Create the file and write headers if it doesn't exist
    if not os.path.exists(csv_filename):
        with open(csv_filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(csv_headers)

    while True:
            # Update key states dynamically inside the loop
        key_states["accelerate"] = 1 if keyboard.is_pressed('up') else 0
        key_states["brake"] = 1 if keyboard.is_pressed('down') else 0
        key_states["steer_left"] = 1 if keyboard.is_pressed('left') else 0
        key_states["steer_right"] = 1 if keyboard.is_pressed('right') else 0
        # wait for an answer from server
        buf = None
        try:
            buf, addr = sock.recvfrom(1000)
            buf = buf.decode()  # Decode received bytes
        except socket.error as msg:  # FIXED
            print("Didn't get response from server...", msg)

        if verbose and buf:
            print('Received: ', buf)

        if buf and '***shutdown***' in buf:
            d.onShutDown()
            shutdownClient = True
            print('Client Shutdown')
            break

        if buf and '***restart***' in buf:
            d.onRestart()
            print('Client Restart')
            break
        
        buf = None
        try:
            buf, addr = sock.recvfrom(1000)
            buf = buf.decode()  # Decode received bytes
        except socket.error as msg:
            print("Didn't get response from server...", msg)
            buf = ""  # Ensure buf is not None to avoid TypeError

        # Only process data if it's not empty
        data_dict = {}
        if buf:
            matches = re.findall(r'\((\S+) ([^()]+)\)', buf)
            if matches:
                data_dict = dict(matches)  # Fix: Properly format dictionary assignment

        # Extract track sensor values
        track_values = data_dict.get("track", "").split()
        track_values = track_values if len(track_values) == 19 else ["N/A"] * 19  # Ensure 19 values



        # Define values for CSV based on extracted data
        track_name = "G-Speedway"
        telemetry_values = [
            currentStep,
            track_name,
            data_dict.get("angle", "N/A"),
            data_dict.get("curLapTime", "N/A"),
            data_dict.get("distFromStart", "N/A"),
            data_dict.get("distRaced", "N/A"),
            data_dict.get("fuel", "N/A"),
            data_dict.get("gear", "N/A"),
            data_dict.get("lastLapTime", "N/A"),
            data_dict.get("racePos", "N/A"),
            data_dict.get("rpm", "N/A"),
            data_dict.get("speedX", "N/A"),
            data_dict.get("speedY", "N/A"),
            data_dict.get("speedZ", "N/A"),
            data_dict.get("trackPos", "N/A"),
            data_dict.get("wheelSpinVel", "N/A"),
            data_dict.get("z", "N/A"),
            key_states["accelerate"],   # Capture 'W' key state
            key_states["brake"],        # Capture 'S' key state
            key_states["steer_left"],   # Capture 'A' key state
            key_states["steer_right"],  # Capture 'D' key state
        ] + track_values


        # Append data to CSV
        with open(csv_filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(telemetry_values)
        
        currentStep += 1
        if currentStep != arguments.max_steps:
            if buf:
                buf = d.drive(buf)
        else:
            buf = '(meta 1)'

        if verbose:
            print('Sending: ', buf)

        if buf:
            try:
                sock.sendto(buf.encode(), (arguments.host_ip, arguments.host_port))  # Encode before sending
            except socket.error as msg:  # FIXED
                print("Failed to send data...Exiting...", msg)
                sys.exit(-1)

    curEpisode += 1

    if curEpisode == arguments.max_episodes:
        shutdownClient = True

sock.close()
