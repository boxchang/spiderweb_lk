#import psutil
import random
import socket
import json

import psutil


class KeyDeviceAction():
    vnedc_db = None
    scada_db = None
    status = None

    def __init__(self, obj):
        self.vnedc_db = obj.vnedc_db
        self.scada_db = obj.scada_db
        self.status = obj.status

    def ConnectionTest(self, device):
        msg = ""
        request = "INFO"
        status = "S01"
        server_port = self.get_port_list()
        client_ip = device.ip_address
        client_port = int(device.port)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
            server_socket.settimeout(20)
            server_socket.bind(("0.0.0.0", server_port))
            print(f"Sending message to {client_ip}:{client_port}")
            server_socket.sendto(request.encode(), (client_ip, client_port))
            try:
                response, client_address = server_socket.recvfrom(4096)  # Buffer size of 4096
                client_message = response.decode()
                server_socket.close()

                pc_info = json.loads(client_message)
                disks = pc_info['DISKS']
                for disk in disks:
                    usage_rate = disk['PERCENT']
                    print(usage_rate)

                    if usage_rate > 85:
                        status = "E07"
                        msg = f"Disk used rate over 85%"
                        print(f"Disk used rate over 85%")
            except socket.timeout:
                msg = f"No response from {client_ip}:{client_port}."
                print(f"No response from {client_ip}:{client_port}.")
                status = "E06"
            except Exception as e:
                msg = f"Error: {str(e)}"
                print(f"Error: {str(e)}")
                status = "E06"
        return status, msg

    def get_port_open_list(self):
        connections = psutil.net_connections(kind='inet')
        open_ports = set()
        for conn in connections:
            if conn.status == 'ESTABLISHED' or conn.status == 'LISTEN':
                open_ports.add(conn.laddr.port)
        return sorted(open_ports)

    def get_port_list(self):
        open_ports = self.get_port_open_list()
        while True:
            num = random.randint(7000, 9000)
            if num not in open_ports:
                return num