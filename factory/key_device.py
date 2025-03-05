from action.KeyDeviceAction import KeyDeviceAction
from monitor import Monitor
import threading
from datetime import datetime

class KeyDeviceMonitor(Monitor):
    DEVICE_TYPE = "KEY_DEVICE"

    def monitor(self):
        devices = self.get_device_list(self.DEVICE_TYPE)
        for device in devices:
            thread = threading.Thread(target=self.listner, args=(device,))
            thread.start()

    def listner(self, device):
        action = KeyDeviceAction(self).ConnectionTest
        status, msg = self.execute(action, device)
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}-Monitoring Factory Equipment: {device.device_type} - {device.device_name} - {self.status[status]}")

    def stop(self):
        print(f"Stopping Key Device Monitor: {self.device_id}")




