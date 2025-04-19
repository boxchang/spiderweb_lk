from abc import abstractmethod, ABC

from database import vnedc_database, scada_database, mes_database
from models import DeviceInfo
from utils import Log


class Monitor(ABC):
    status = {}
    vnedc_db = None
    scada_db = None
    mes_db = None
    MACHINE_MAPPING = {}

    def __init__(self):
        self.vnedc_db = vnedc_database()
        self.scada_db = scada_database()
        self.mes_db = mes_database()
        self.status = self.get_status_define()
        self.MACHINE_MAPPING = self.get_machine_mapping()

    @abstractmethod
    def monitor(self):
        pass

    @abstractmethod
    def stop(self):
        pass


    def get_machine_mapping(self):
        sql = """
            SELECT distinct COUNTING_MACHINE, MES_MACHINE
            FROM [PMG_DEVICE].[dbo].[COUNTING_DATA_MACHINE]
        """
        results = self.scada_db.select_sql_dict(sql)
        results = {item['COUNTING_MACHINE']: item['MES_MACHINE'] for item in results}
        return results


    def get_status_define(self):
        sql = """
            SELECT status_code,[desc] FROM [LKEDC].[dbo].[spiderweb_monitor_status]
        """
        results = self.vnedc_db.select_sql_dict(sql)
        results = {item['status_code']: item['desc'] for item in results}
        return results

    def get_device_list(self, device_type):

        sql = f"""SELECT c.id, mt.type_name monitor_type, dt.type_name device_type, device_name, ip_address, port,
                    plant, enable, status_code status, status_update_at,comment, c.update_at,c.update_by_id update_by, c.device_group,
                    c.attr1,c.attr2,c.attr3,c.attr4,c.attr5
                    FROM [LKEDC].[dbo].[spiderweb_monitor_device_list] c
                    JOIN [LKEDC].[dbo].[spiderweb_monitor_type] mt on c.monitor_type_id = mt.id
                    JOIN [LKEDC].[dbo].[spiderweb_device_type] dt on c.device_type_id = dt.id
                    JOIN [LKEDC].[dbo].[spiderweb_monitor_status] s on c.status_id = s.status_code and dt.type_name='{device_type}'
                    WHERE enable = 'Y' and (GETDATE() > CONVERT(DATETIME, stop_before, 103) or stop_before ='' or stop_before is null)"""
        rows = self.vnedc_db.select_sql_dict(sql)

        devices = [
            DeviceInfo(id=row['id'], monitor_type=row['monitor_type'], device_type=row['device_type'],  device_name=row['device_name'],
                       ip_address=row['ip_address'], port=row['port'], plant=row['plant'], enable=row['enable'],
                       status=row['status'], status_update_at=row['status_update_at'], comment=row['comment'],
                       update_at=row['update_at'], update_by=row['update_by'],
                       attr1=row['attr1'], attr2=row['attr2'], attr3=row['attr3'], attr4=row['attr4'], attr5=row['attr5'])
            for row in rows]
        return devices

    def update_device_status(self, id, status_id):
        sql = f"""
           update [LKEDC].[dbo].[spiderweb_monitor_device_list] set status_id = '{status_id}', status_update_at = GETDATE() 
           where id = {id}
           """
        self.vnedc_db.execute_sql(sql)

    def get_device_status(self, action, device):
        status, msg = action(device)
        return status, msg

    def wecom_log(self, device, status, msg):
        # if device.wecom:
        #     pass
        Log.write(self.vnedc_db, device.device_type, msg, status, device.id)

    def execute(self, action, device):
        status, msg = self.get_device_status(action, device)
        self.update_device_status(device.id, status)
        if str(status).startswith('E') and device.status.startswith('S'):
            self.wecom_log(device, status, msg)
        return status, msg