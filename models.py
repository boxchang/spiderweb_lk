
class DeviceInfo:

    def __init__(self, id, monitor_type, device_type, device_name, ip_address, port, plant, enable, status,
                 status_update_at, comment, update_at, update_by, attr1, attr2, attr3, attr4, attr5):
        self.id = id
        self.monitor_type = monitor_type
        self.device_type = device_type
        self.device_name = device_name
        self.ip_address = ip_address
        self.port = port
        self.plant = plant
        self.enable = enable
        self.status = status
        self.status_update_at = status_update_at
        self.comment = comment
        self.update_at = update_at
        self.update_by = update_by
        self.attr1 = attr1
        self.attr2 = attr2
        self.attr3 = attr3
        self.attr4 = attr4
        self.attr5 = attr5

class DeviceType:

    def __init__(self, type_name, job_frequency, update_at, update_by):
        self.type_name = type_name
        self.job_frequency = job_frequency
        self.update_at = update_at
        self.update_by = update_by

