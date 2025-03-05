from monitor import Monitor
from utils import Log
import os
import requests
import time

class WecomMonitor(Monitor):
    def monitor(self):
        time.sleep(3)
        self.send_msg(self.vnedc_db)
        print(f"Start WeCom message")

    def stop(self):
        print(f"Stopping WeCom message")


    def send_wecom(self, msg):
        print('Send message')
        path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        wecom_file = os.path.join(path, "dt_wecom_key.config")
        url = ''  # Add Wecom GD_MES group key
        if os.path.exists(wecom_file):
            with open(wecom_file, 'r') as file:
                url = file.read().strip()
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": '',
                # "mentioned_list": ["@all"],
            }
        }
        data["markdown"]["content"] = msg
        r = requests.post(url, headers=headers, json=data)
        return r.json()

    def send_msg(self, vnedc_db):
        comment = ""
        msg = ""

        sql = f"""
                SELECT min(smdlog.id) as id, smdlog.func_name, smdlog.comment, smdlist.device_name,
                smdlog.status_code_id error_status, smdlist.status_id current_status, smdlog.notice_flag, smdlog.recover_msg,
                case 
                    when smdlog.status_code_id = smdlist.status_id then 1
                    else 0
                end as code
                FROM [LKEDC].[dbo].[spiderweb_monitor_device_log] smdlog
                JOIN [LKEDC].[dbo].[spiderweb_monitor_device_list] smdlist
                on smdlog.device_id = smdlist.id and smdlist.device_name = smdlist.device_name
                where smdlog.recover_msg is NULL and (GETDATE() > CONVERT(DATETIME, stop_before, 103) or stop_before ='')
				group by smdlog.func_name, smdlog.comment, smdlist.device_name,
                smdlog.status_code_id , smdlist.status_id , smdlog.notice_flag, smdlog.recover_msg             
                """
        try:
            rows = vnedc_db.select_sql_dict(sql)
            if len(rows) > 0:
                for row in rows:
                    if str(row['notice_flag']) == 'False':
                        Log.update_log_flag(vnedc_db, row['id'])

                    if 's' in str(row['current_status']).lower():
                        Log.update_recover_flag(vnedc_db, row['id'])
                    else:
                        tmp = """[Issue #{row_id}]\t[**{device_type}**]\t[**{device_name}**]\t{comment}\n"""
                        comment = row['comment']
                        msg += tmp.format(row_id=row['id'], device_type=row['func_name'], device_name=row['device_name'], comment=comment)

            if len(msg) > 0:
                self.send_wecom(msg)

        except Exception as e:
            print(f"Wecom {e}")

