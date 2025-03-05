from datetime import datetime, timedelta


class AOIDeviceAction():
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
        msg = ""
        status = "S01"

        sql = f"""
                    SELECT CONVERT(varchar(30), od.Cdt, 121) AS last_time, od.OKQty, od.NGQty, wo.ProductItem
                    FROM [PMG_DEVICE].[dbo].[OpticalDevice] od
                    join [PMG_DEVICE].[dbo].[COUNTING_DATA_MACHINE] cdm
                    on cdm.COUNTING_MACHINE =  od.DeviceId
                    join [PMGMES].[dbo].[PMG_DML_DataModelList] dml
                    on dml.name = cdm.MES_MACHINE and dml.DataModelTypeId = 'DMT000003'
                    join [PMGMES].[dbo].[PMG_MES_WorkOrder] wo
                    on wo.MachineId = dml.id
                    AND wo.StartDate > cast(GETDATE()-1 as Date) AND wo.EndDate is null
                    AND ProductItem not like 'V S%'
                    WHERE od.DeviceId = '{device_name}'
                    ORDER BY od.Cdt DESC
                    OFFSET 0 ROWS FETCH NEXT 1 ROWS ONLY;
                """
        try:
            rows = self.scada_db.select_sql_dict(sql)
            # print(rows)
            # print(str(rows[0]['ProductItem'][:3]))

            if len(rows) > 0:
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
        return status, msg

    def Over_AOI_NG_Rate(self, device):
        device_name = device.device_name
        msg = ""
        status = "S01"

        sql = f"""
        select job_frequency from [LKEDC].[dbo].[spiderweb_device_type] where type_name = 'AOI DEVICE'
        """

        try:
            rows = self.vnedc_db.select_sql_dict(sql)

            job_frequency = rows[0]['job_frequency']

            sql = f"""
                select DeviceId, CAST(sum(NGQty) AS float)/(sum(OKQty)+sum(NGQty))*100 ng_rate
                from [PMG_DEVICE].[dbo].[OpticalDevice] where DeviceId = '{device_name}'
                and Cdt between DATEADD(SECOND, -{job_frequency}, GETDATE()) and GETDATE()
                group by DeviceId HAVING SUM(NGQty) > 0
            """
            rows = self.scada_db.select_sql_dict(sql)
            if len(rows) > 0:
                if float(rows[0]['ng_rate']) > 3:
                    status = "E02"
                    msg = f"Optical Error Rate > 3%"

        except Exception as e:
            print(e)
            status = "E99"
            msg = e
        return status, msg

