import os
from cryptography.fernet import Fernet
import socket
import psutil
import threading
import time
import sys
from infi.systray import SysTrayIcon
import json
import os

fullPath = os.getcwd()
# Function to load the existing key
def secret_key():
    key_path = os.path.join(fullPath, 'lib', 'secret.key')
    with open(key_path, 'rb') as key_file:
        return key_file.read()

def active_key():
    key_path = os.path.join(fullPath, 'lib', 'activate.key')
    with open(key_path, 'rb') as key_file:
        return key_file.read()

def decrypt_message(encrypted_message, key):
    f = Fernet(key)
    decrypted_message = f.decrypt(encrypted_message).decode()
    return decrypted_message

def get_client_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        except Exception:
            return "None"

def get_disk_info():
    disk_list = []
    partitions = psutil.disk_partitions()
    for partition in partitions:
        try:
            disk_info = {}
            partition_usage = psutil.disk_usage(partition.mountpoint)
            disk_info['USAGE_FREE'] = partition_usage.free
            disk_info['USED'] = partition_usage.used
            disk_info['USAGE_TOTAL'] = partition_usage.total
            disk_info['PERCENT'] = partition_usage.percent
            disk_list.append(disk_info)
        except PermissionError:
            continue
    return disk_list

def handle_server_message(client_socket):
    tried_time = 0
    global running
    while running:
        try:
            message, server_address = client_socket.recvfrom(1024)
            if 'INFO' in message.decode():
                disk_info = get_disk_info()  # GET DISK INFO
                pc_info = {'DISKS': disk_info}
                pc_info_json = json.dumps(pc_info).encode()
                client_socket.sendto(pc_info_json, server_address)
        except:
            tried_time += 1
            if tried_time == 5:
                break

def start_client(port):
    'Start the client to listen on port.'
    global running
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
        client_port = port
        client_socket.bind(("0.0.0.0", client_port))
        print(f"Client listening on port {client_port}...")

        # Start a thread to handle incoming messages from the server
        listener_thread = threading.Thread(target=handle_server_message, args=(client_socket,))
        listener_thread.daemon = True
        listener_thread.start()

        # Keep the client running until the user quits
        while running:
            time.sleep(1)

def stop_client(systray):
    "Quit the client completely when selected from the system tray."
    global running
    running = False  # Stop the client loop
    time.sleep(1)  # Allow time for threads to stop
    try:
        sys.exit()  # Terminate the program
    except SystemExit:
        pass  # Suppress the SystemExit exception message

def restart_client(systray):
    "Restart the client when selected from the system tray."
    global running
    #Stop the client
    running = False  # Stop the client loop
    time.sleep(1)  # Allow time for threads to stop

    #Restart the client
    running = True  # Set the flag to True to start the client again

    # Start the client in a new thread to avoid blocking the system tray
    client_thread = threading.Thread(target=start_client)
    client_thread.daemon = True
    client_thread.start()

def quit_client(systray):
    "Custom quit function that will be called when the user selects 'Quit'."
    global running

    # Stop the client
    running = False  # Stop the client loop
    time.sleep(1)  # Allow time for threads to stop

    # Clean up and exit
    try:
        sys.exit()  # Terminate the program
    except SystemExit:
        pass  # Suppress the SystemExit exception message


def run_systray_client():
    "Runs the client with a system tray icon."
    # Define menu options, including the Quit option which will close the program
    menu_options = (("Restart", None, restart_client), ("Stop", None, stop_client),)

    systray = SysTrayIcon("lib/client.ico", f"Client Running on {port}", menu_options, on_quit=quit_client)
    systray.start()

    # Run the client in the background
    start_client(port)

running = True
decrypted_text = decrypt_message(active_key(), secret_key())
port = int(str(decrypted_text).split('-')[-1])
run_systray_client()



