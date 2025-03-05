from datetime import datetime, timedelta


class ScadaPLCAction():
    vnedc_db = None
    scada_db = None
    status = None

    def __init__(self, obj):
        self.vnedc_db = obj.vnedc_db
        self.scada_db = obj.scada_db
        self.status = obj.status

    # Check if there is no data for a long time
    def IsOverTime(self, device):
        device_name = device.device_name
        table_name = device.attr1
        msg = ""
        status = "S01"

        try:
            if 'NBR' in device_name:
                sql = f"""
                            SELECT CONVERT(varchar(30), max(datetime), 121) AS last_time
                            FROM {table_name}
                        """

            elif 'PVC' in device_name:
                sql = f"""
                            SELECT max(CreationTime) as last_time
                            FROM [PMG_DEVICE].[dbo].[PVC_MACHINE_DATA]
                            where MachineName = '{device_name}' AND FT2 is not null
                        """
            rows = self.scada_db.select_sql_dict(sql)

            if rows[0]['last_time'] is not None:
                given_time = datetime.strptime(rows[0]['last_time'][:-1], '%Y-%m-%d %H:%M:%S.%f')
                current_time = datetime.now()
                time_difference = current_time - given_time

                if time_difference > timedelta(minutes=30):
                    status = "E01"
                    given_time = given_time.replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
                    msg = f"The last time is {given_time} already over 30 mins"

        except Exception as e:
            print(e)
            status = "E99"
            msg = e
        return status, msg