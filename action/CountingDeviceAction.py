from datetime import datetime, timedelta
import re

class CountingDeviceAction():
    vnedc_db = None
    scada_db = None
    status = None
    MACHINE_MAPPING = {}

    def __init__(self, obj):
        self.vnedc_db = obj.vnedc_db
        self.scada_db = obj.scada_db
        self.status = obj.status
        self.MACHINE_MAPPING = obj.MACHINE_MAPPING

    # Check if there is no data for a long time
    def IsOverTime(self, device):
        msg = ""
        status = "S01"
        speed = 220
        device_name = device.device_name
        today = datetime.today().strftime('%Y-%m-%d')

        sql = f"""      
            WITH WO AS (
            SELECT distinct COUNTING_MACHINE
              FROM [PMG_DEVICE].[dbo].[COUNTING_DATA_MACHINE] c
              LEFT JOIN [PMGMES].[dbo].[PMG_MES_RunCard] r on r.MachineName = c.MES_MACHINE
              LEFT JOIN [PMGMES].[dbo].[PMG_MES_WorkOrder] w on r.WorkOrderId = w.Id
              where r.InspectionDate = '{today}' and COUNTING_MACHINE = '{device_name}'
              )
            
            SELECT last_time, Speed
                FROM (
                    SELECT TOP 1 CreationTime as last_time, Speed
                    FROM [PMG_DEVICE].[dbo].[COUNTING_DATA] c 
                    JOIN WO w on w.COUNTING_MACHINE = c.MachineName
                    WHERE MachineName = '{device_name}'
                    ORDER BY CreationTime DESC
                ) AS LatestRow
                UNION ALL
                SELECT * 
                FROM (
                    SELECT TOP 1 CreationTime as last_time, Speed
                    FROM [PMG_DEVICE].[dbo].[COUNTING_DATA] c 
                    JOIN WO w on w.COUNTING_MACHINE = c.MachineName
                    WHERE MachineName = '{device_name}'
                        AND Qty2 > 0
                    ORDER BY CreationTime DESC
                ) AS LatestNonNullRow;
            
            """
        try:

            rows = self.scada_db.select_sql_dict(sql)

            if len(rows) == 2:
                given_time = datetime.strptime(rows[0]['last_time'][:-1], '%Y-%m-%d %H:%M:%S.%f')
                given_time2 = datetime.strptime(rows[1]['last_time'][:-1], '%Y-%m-%d %H:%M:%S.%f')
                current_time = datetime.now()
                time_difference = current_time - given_time
                time_difference2 = current_time - given_time2

                if time_difference > timedelta(minutes=30) or time_difference2 > timedelta(minutes=30):
                    status = "E01"
                    given_time = given_time.replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
                    msg = f"The last time is {given_time} already over 30 mins"
                else:
                    last_null = datetime.strptime(rows[0]['last_time'][:-1], '%Y-%m-%d %H:%M:%S.%f')
                    last_time = datetime.strptime(rows[1]['last_time'][:-1], '%Y-%m-%d %H:%M:%S.%f')
                    last_value = rows[1]['Speed']

                    if last_value is None or (last_value > 0 and last_time - last_null > timedelta(minutes=30)):  # 最後有值的機速大於0，且Null值的時間差超過30分鐘才判斷異常
                        status = "E01"
                        last_null = last_null.replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
                        msg = f"NULL from {last_null}"
                    else:
                        if rows[0]['Speed'] is None:
                            # status = "E10"
                            # msg = f"{device_name} speed is None"
                            pass
                        elif int(rows[0]['Speed']) > speed:
                            status = "E09"
                            msg = f"{device_name} speed is > 220"

        except Exception as e:
            print(e)
            status = "E99"
            msg = e

        return status, msg

    def NoIPQC(self, device):
        msg = "Success"
        status = "S01"  # Default to "Success"
        device_name = device.device_name  # NBR_CountingMachine_1B
        machine_name = self.MACHINE_MAPPING[device_name]  # VN_GD_NBR1_L03

        today = datetime.today().strftime('%Y-%m-%d')
        wo_sql = f"""
                    WITH Machine AS (
                        SELECT *
                        FROM [PMGMES].[dbo].[PMG_DML_DataModelList] dl
                        WHERE dl.DataModelTypeId = 'DMT000003'
                    ),
                    WorkOrderCheck AS (
                        SELECT 
                            dml.Id AS MachineID,
                            dml.Name AS MachineName,
                            wo.Id AS WorkOrderId,
                            woi.LineId AS LineId
                        FROM 
                            Machine dml
                        LEFT JOIN 
                            [PMGMES].[dbo].[PMG_MES_WorkOrder] wo 
                            ON dml.Id = wo.MachineId
                            AND wo.StartDate IS NOT NULL
                            AND wo.StartDate BETWEEN CONVERT(DATETIME, '{today} 05:30:00', 120) 
                                            AND CONVERT(DATETIME, DATEADD(SECOND, -1, CONVERT(DATETIME, DATEADD(DAY, 1, '{today}') + ' 05:30:00', 120)), 120)
                        LEFT JOIN 
                            [PMGMES].[dbo].[PMG_MES_WorkOrderInfo] woi 
                            ON wo.Id = woi.WorkOrderId
                        WHERE 
                            dml.Name LIKE '%{machine_name}%'
                    )
                    SELECT 
                        distinct(WorkOrderId)
                    FROM 
                        WorkOrderCheck
                """

        condition = self.scada_db.select_sql_dict(wo_sql)
        match_condition = True if len(condition) > 1 or condition[0]['WorkOrderId'] is not None else False
        if match_condition == True:
            try:
                sql_counting = f"""
                            SELECT SUM(Qty2) as qty
                            FROM [PMG_DEVICE].[dbo].[COUNTING_DATA] cd
                            JOIN [PMG_DEVICE].[dbo].[COUNTING_DATA_MACHINE] cm on cd.MachineName = cm.COUNTING_MACHINE
                            WHERE cm.MES_MACHINE = '{machine_name}'
                              AND CreationTime BETWEEN 
                                    CAST(FORMAT(DATEADD(HOUR, -2, GETDATE()), 'yyyy-MM-dd HH:00:00') AS DATETIME)
                              AND 
                                    CAST(FORMAT(DATEADD(HOUR, -2, GETDATE()), 'yyyy-MM-dd HH:59:59') AS DATETIME)
                              AND Qty2 IS NOT NULL;
                            """
                counting_data = self.scada_db.select_sql_dict(sql_counting)

                sql_check_ipqc = f"""
                            WITH CheckData AS (
                                -- Lọc dữ liệu thực tế từ bảng dựa trên giờ trước đó
                                SELECT 
                                    COUNT(*) AS ValidDataCount
                                FROM [PMGMES].[dbo].[PMG_MES_IPQCInspectingRecord] ipqc
                                JOIN [PMGMES].[dbo].[PMG_MES_RunCard] r
                                    ON ipqc.RunCardId = r.Id
                                WHERE r.InspectionDate = CONVERT(date, GETDATE())  -- Chỉ kiểm tra ngày hiện tại
                                    AND Period = DATEPART(HOUR, DATEADD(hour, -2, GETDATE()))  -- Kiểm tra giờ trước đó
                                    AND OptionName = 'Weight'
                                    AND MachineName = '{machine_name}'
                                    --AND LineName = 'B2'
                            )
                            -- So sánh dữ liệu thực tế với Period của giờ trước đó
                            SELECT 
                                DATEPART(HOUR, DATEADD(hour, -2, GETDATE())) AS ExpectedPeriod,
                                CASE 
                                    WHEN cd.ValidDataCount IS NULL OR cd.ValidDataCount = 0 THEN 'Missing data'  -- Nếu không có dữ liệu
                                    ELSE 'Data exists'  -- Nếu có dữ liệu
                                END AS Status
                            FROM CheckData cd;
                            """
                qc = self.scada_db.select_sql_dict(sql_check_ipqc)
                temp = ""
                # current_hour = int(datetime.now().hour - timedelta(hours=1))
                if str(qc[0]["Status"]) == "Missing data":
                    if counting_data[0]["qty"] != None:
                        if int(counting_data[0]["qty"]) > 1000:
                            status = "E11"
                            Period = qc[0]["ExpectedPeriod"]
                            msg = f"Period {Period} No IPQC but have Machine online"
            except Exception as e:
                status = "E99"
                msg = f"Error while checking IPQC for {device.device_name}: {str(e)}"
        else:
            status = 'S01'
            msg = 'Machine stopped'
        return status, msg

    def ModelLostQtyCheck(self, device):
        msg = "Success"
        status = "S01"  # Default to "Success"
        device_name = device.device_name

        try:
            # 目前只有NBR看板有顯示缺模率
            sql = f"""
              SELECT *
              FROM [PMG_DEVICE].[dbo].[COUNTING_DATA] where MachineName = '{device_name}'
              and CreationTime between DATEADD(MINUTE, -10, GETDATE()) and GETDATE()
              and MachineName like '%NBR%'
            """
            raws = self.scada_db.select_sql_dict(sql)

            for data in raws:
                if data['ModelLostQty'] is not None and float(data['Qty2']) > 0 and float(data['ModelLostQty']) < 0:
                    status = "E16"
                    msg = f"ModelLostQty is not correct, please check"
                    break
        except Exception as e:
            status = "E99"
            msg = f"Error while ModelLostQtyCheck for {device.device_name}: {str(e)}"

        return status, msg