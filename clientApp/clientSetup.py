import os
from cryptography.fernet import Fernet
import tkinter as tk
from tkinter import ttk, messagebox
import ctypes
import socket
import psutil
import random
import os
import subprocess


def generate_key():
    key = Fernet.generate_key()
    with open('lib/secret.key', 'wb') as key_file:
        key_file.write(key)
    return key


def encrypt_message(message, key):
    f = Fernet(key)
    encrypted_message = f.encrypt(message.encode())
    return encrypted_message


def get_client_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        except Exception:
            return "None"


def get_port_open_list():
    connections = psutil.net_connections(kind='inet')
    open_ports = set()

    for conn in connections:
        # if conn.status == 'ESTABLISHED' or conn.status == 'LISTEN':
        open_ports.add(conn.laddr.port)
    return list(sorted(set(open_ports)))


def get_port_list():
    sorted_list = []
    if 9527 not in get_port_open_list():
        sorted_list.insert(0, 9527)
    else:
        if 8888 not in get_port_open_list():
            sorted_list.insert(0, 8888)
        else:
            result = set()
            while len(result) < 5:
                num = random.randint(7999, 9000)
                if num not in get_port_open_list():
                    result.add(num)
            sorted_list = sorted(result, reverse=True)
    return list(sorted_list)


def save_info():
    try:
        os.system('taskkill /f /im clientApp.exe')
    except:
        None
    device_name = 'ABC'
    ip_address = ip_address_entry.get()
    selected_port = port_var.get()

    if device_name and ip_address and selected_port:
        key = generate_key()
        text = f"{device_name}-{selected_port}"
        encrypted_text = encrypt_message(text, key)
        with open('lib/activate.key', 'wb') as f:
            f.write(encrypted_text)
        messagebox.showinfo("Saved", "Activate successfully!")
        exe_path = os.path.join(os.getcwd(), "clientApp.exe")
        if os.path.exists(exe_path):
            subprocess.Popen([exe_path])
        else:
            messagebox.showerror("Error", "clientApp.exe not found!")
        root.quit()
        root.destroy()
    else:
        messagebox.showerror("Error", "Error Happened !")


ctypes.windll.shcore.SetProcessDpiAwareness(1)
root = tk.Tk()
root.iconbitmap('lib/setup.ico')
root.title("Setup Configuration")
root.geometry("920x540")
root.configure(bg="white")
# Create a frame to hold the form elements with padding
frame = tk.Frame(root, padx=20, pady=20, bg="white")
frame.pack(fill=tk.BOTH, expand=True)

# Add Logo Label (aligned to the left, limited height and width)
logo_label = tk.Label(frame, text="LOGO", font=("Arial", 14, "bold"), borderwidth=1, relief="solid", width=15, height=2,
                      bg="white")
logo_label.grid(row=0, column=0, padx=7, pady=7, sticky="w")

# Add Device Name Label and Entry
device_name_label = tk.Label(frame, text="Device Name:", font=("Arial", 13, "bold"), bg="white")
device_name_label.grid(row=1, column=0, sticky="e", pady=50)
device_name_entry = tk.Entry(frame, font=("Arial", 13), width=30, bg="white", relief="solid")
device_name_entry.grid(row=1, column=1, padx=100, pady=50)

# Add IP Address Label and Entry (disabled)
ip_address_label = tk.Label(frame, text="IP Address:", font=("Arial", 13, "bold"), bg="white")
ip_address_label.grid(row=2, column=0, sticky="e", pady=10)
ip_address_entry = tk.Entry(frame, font=("Arial", 13), width=30, bg="white", relief="solid")
ip_address_entry.grid(row=2, column=1, padx=100, pady=10)
ip_address_entry.insert(0, get_client_ip())
ip_address_entry.config(state="disabled")

# Port label and dropdown menu
port_label = tk.Label(frame, text="Port:", font=("Arial", 13, "bold"), bg="white")
port_label.grid(row=3, column=0, sticky="e", pady=50)
port_var = tk.StringVar()
port_menu = ttk.Combobox(frame, textvariable=port_var, values=get_port_list(), width=28, state="readonly",
                         font=("Arial", 13))
port_menu.grid(row=3, column=1, padx=100, pady=50)
port_menu.current(0)
if len(get_port_list()) == 1:
    port_menu.config(state="disabled")
else:
    port_menu.config(state="readonly")

# Save button
save_button = tk.Button(frame, text="SAVE", font=("Arial", 12, "bold"), bg="#0B76A0", fg="white", command=save_info)
save_button.grid(row=4, column=0, columnspan=2, pady=10)

root.mainloop()
