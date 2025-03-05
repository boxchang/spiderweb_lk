from database import vnedc_database
from models import DeviceType

class Log(object):
    def write(vnedc_db, func_name, comment, status_code_id, device_id):
        try:
            sql = f"""
            INSERT INTO [dbo].[spiderweb_monitor_device_log] (func_name, comment, update_at,notice_flag, device_id, status_code_id)
            VALUES ('{func_name}', '{comment}', GETDATE(), 0, {device_id},'{status_code_id}')
            """
            vnedc_db.execute_sql(sql)

        except Exception as e:
            print(f"Error while logging: {e}")

    def update_log_flag(vnedc_db, id):
        sql = f"""
            update [LKEDC].[dbo].[spiderweb_monitor_device_log] set notice_flag = 1 where id = {id}
        """
        vnedc_db.execute_sql(sql)

    def update_recover_flag(vnedc_db, id):
        sql = f"""
            update [LKEDC].[dbo].[spiderweb_monitor_device_log] set recover_msg = 1 where id = {id}
        """
        vnedc_db.execute_sql(sql)

class Utils(object):

    def get_device_type_list(self):
        db = vnedc_database()
        sql = f"""SELECT [type_name]
                      ,[job_frequency]
                      ,[update_at]
                      ,[update_by_id]
                  FROM [LKEDC].[dbo].[spiderweb_device_type]"""
        rows = db.select_sql_dict(sql)

        device_types = [
            DeviceType(type_name=row['type_name'], job_frequency=row['job_frequency'], update_at=row['update_at'], update_by=row['update_by_id']) for
            row in
            rows]

        return device_types
