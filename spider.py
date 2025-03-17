import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from factory.factory_equipment import CountingDeviceMonitor, AOIDeviceMonitor, ScadaPLCMonitor
from factory.key_device import KeyDeviceMonitor
from factory.mes_data_status import MesDataStatusMonitor
from factory.sap_data_status import SapDataStatusMonitor
from factory.wecom import WecomMonitor
from utils import Utils
import threading
import time

class MonitorThread(threading.Thread):
    def __init__(self, monitor, frequency):
        super().__init__()
        self.monitor = monitor
        self.frequency = frequency
        self._stop_event = threading.Event()

    def run(self):
        frequency = int(self.frequency)
        while not self._stop_event.is_set():
            self.monitor.monitor()
            time.sleep(frequency)  # Monitor periodically, can adjust as needed

    def stop(self):
        self.monitor.stop()
        self._stop_event.set()

class MonitorFactory:
    @staticmethod
    def create_monitor(device_type):
        if device_type == "COUNTING DEVICE":
            return CountingDeviceMonitor()
        elif device_type == "AOI DEVICE":
            return AOIDeviceMonitor()
        elif device_type == "PLC SCADA":
            return ScadaPLCMonitor()
        elif device_type == 'MES DATA':
            return MesDataStatusMonitor()
        elif device_type == 'WECOM':
            return WecomMonitor()
        elif device_type == 'KEY_DEVICE':
            return KeyDeviceMonitor()
        elif device_type == 'SAPTicket':
            return SapDataStatusMonitor()
        else:
            raise ValueError(f"Unknown device type: {device_type}")

def main():
    utils = Utils()
    device_type_list = utils.get_device_type_list()

    threads = []

    # Create and start threads for each device type
    for device_type in device_type_list:
        monitor = MonitorFactory.create_monitor(device_type.type_name)
        job_frequency = device_type.job_frequency
        thread = MonitorThread(monitor, job_frequency)
        threads.append(thread)
        thread.start()

if __name__ == "__main__":
    main()