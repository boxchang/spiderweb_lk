from action.SAPDataStatusAction import SAPDataStatusAction
from monitor import Monitor
from datetime import datetime


class SapDataStatusMonitor(Monitor):
    DEVICE_TYPE = "SAPTicket"

    def monitor(self):
        devices = self.get_device_list(self.DEVICE_TYPE)
        for device in devices:
            action = SAPDataStatusAction(self).CheckDataStatus
            status, msg = self.execute(action, device)
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}-Monitoring Factory Equipment: {device.device_type} - {device.device_name} - {self.status[status]}")

    def stop(self):
        print(f"Stopping Factory Equipment Monitor: {device.device_type} - {device.device_name}")
