from datetime import datetime, timedelta

class MESDataStatusAction():
    vnedc_db = None
    scada_db = None
    mes_db = None
    status = None

    def __init__(self, obj):
        self.vnedc_db = obj.vnedc_db
        self.scada_db = obj.scada_db
        self.mes_db = obj.mes_db
        self.status = obj.status

    # Check if there is no data for a long time
    def CheckDataStatus(self, device):
        device_name = device.device_name
        table_name = device.attr1
        msg = ""
        status = "S01"

        startDate = datetime.today().date() - timedelta(days=1)
        endDate = datetime.today().date()

        missingIPQCStandardValue = []
        missingSCADAStandardValue = []
        try:
            if device_name == 'THICKNESS_DATA':
                sql = f"""
                        SELECT RunCardId, DeviceId UserId, Cdt data_time
                        FROM [PMG_DEVICE].[dbo].[ThicknessDeviceData] td
                        JOIN [PMGMES].[dbo].[PMG_MES_RunCard] r on td.RunCardId = r.Id
                        WHERE Cdt >= DATEADD(HOUR, -2, GETDATE()) AND Cdt <= DATEADD(HOUR, -1, GETDATE()) AND MES_STATUS = 'E'
                            """
                rows = self.scada_db.select_sql_dict(sql)

                if len(rows) > 0:
                    comment = [row['RunCardId'] for row in rows]
                    status = "E04"
                    msg = ', '.join(comment)

            elif device_name == 'WEIGHT_DATA':
                # 有工單派送 + 檢驗項目有重量 才檢查
                sql = f"""
                SELECT LotNo as RuncardId, UserId, CreationDate as data_time
                FROM [PMG_DEVICE].[dbo].[WeightDeviceData] wd
                JOIN [PMGMES].[dbo].[PMG_MES_RunCard] r on wd.LotNo = r.Id COLLATE SQL_Latin1_General_CP1_CS_AS
                JOIN [PMGMES].[dbo].[PMG_MES_RunCard_IPQCInspectIOptionMapping] m on m.RunCardId = r.Id and GroupType = 'Weight'
                JOIN [PMGMES].[dbo].[PMG_MES_WorkOrder] w on w.Id = r.WorkOrderId and w.StartDate < CreationDate
                where MES_STATUS = 'E' and CreationDate >= DATEADD(HOUR, -2, GETDATE()) AND CreationDate <= DATEADD(HOUR, -1, GETDATE())
                            """
                rows = self.scada_db.select_sql_dict(sql)

                if len(rows) > 0:
                    comment = [row['RuncardId'] for row in rows]
                    status = "E05"
                    msg = ', '.join(comment)

            elif device_name == 'SCRAP_DATA':

                current_hour = datetime.now().hour
                today = datetime.now().strftime('%Y%m%d')

                if current_hour in [10, 11, 12]:

                    sql = f"""
                    WITH machs AS (
                    select * from [PMGMES].[dbo].[PMG_DML_DataModelList] where DataModelTypeId = 'DMT000003'
                    and [Name] not in ('VN_GD_PVC2_L13', 'VN_GD_PVC2_L14', 'VN_GD_PVC2_L15', 
                    'VN_GD_PVC2_L16', 'VN_GD_PVC2_L17', 'VN_GD_PVC2_L18', 'VN_GD_PVC2_L19', 
                    'VN_GD_PVC2_L20', 'VN_GD_PVC2_L21', 'VN_GD_PVC2_L22')
                    ),
                    scrap AS (
                    SELECT r.*
                      FROM [PMGMES].[dbo].[PMG_MES_Scrap] s,  [PMGMES].[dbo].[PMG_MES_RunCard] r
                      where s.CreationTime between CONVERT(DATETIME, '{today} 08:00:00', 120) and CONVERT(DATETIME, '{today} 12:59:59', 120)
                      and s.RunCardId = r.Id and s.ActualQty > 300
                    
                    )
                    
                    select Abbreviation from machs m
                    LEFT JOIN scrap s on m.Name = s.MachineName
                    where s.Id is null order by Abbreviation
                    """

                    rows = self.scada_db.select_sql_dict(sql)

                    if len(rows) > 0:
                        comment = [row['Abbreviation'] for row in rows]
                        status = "E13"
                        msg = ', '.join(comment)
                        msg = f"{msg} not ready at peroid {current_hour}"
            elif '_STANDARD' in device_name:
                if 'NBR' in device_name:
                    sql = f"""
                        SELECT DISTINCT PartNo, ProductItem
                        FROM [PMGMES].[dbo].[PMG_MES_WorkOrder]
                        WHERE CreationTime BETWEEN CONVERT(DATETIME, '{startDate} 06:00:00', 120)
                        AND CONVERT(DATETIME, '{endDate} 05:59:59', 120)
                        AND SAP_FactoryDescr LIKE '%NBR%' AND Status=1
                            """

                elif 'PVC' in device_name:
                    sql = f"""
                        SELECT DISTINCT PartNo, ProductItem
                        FROM [PMGMES].[dbo].[PMG_MES_WorkOrder]
                        WHERE CreationTime BETWEEN CONVERT(DATETIME, '{startDate} 06:00:00', 120)
                        AND CONVERT(DATETIME, '{endDate} 05:59:59', 120)
                        AND SAP_FactoryDescr LIKE '%PVC%' AND Status=1
                            """

                partNoItems = self.scada_db.select_sql_dict(sql)
                partNoItems_list = [value['PartNo'] for value in partNoItems]
                productItems = [value['ProductItem'] for value in partNoItems]

                for index, partNo in enumerate(partNoItems_list):
                    if 'IPQC' in device_name:
                        sql_ipqc = f"""
                            SELECT PartNo FROM {table_name}
                            WHERE PartNo = '{partNo}'
                        """
                        if not self.scada_db.select_sql_dict(sql_ipqc):
                            missingIPQCStandardValue.append([partNo, productItems[index]])

                        if len(missingIPQCStandardValue) > 0:
                            for item in missingIPQCStandardValue:
                                status = 'E14'
                                msg = f"{item[0]} ({item[1]}) Need to set IPQC standard values"
                                return status, msg

                    if 'SCADA' in device_name:
                        sql_scada = f"""
                            SELECT PartNo FROM {table_name}
                            WHERE PartNo = '{partNo}'
                        """
                        if not self.scada_db.select_sql_dict(sql_scada):
                            missingSCADAStandardValue.append([partNo, productItems[index]])

                        if len(missingSCADAStandardValue) > 0:
                            for item in missingSCADAStandardValue:
                                status = 'E15'
                                msg = f"{item[0]} ({item[1]}) Need to set SCADA standard values"
                                return status, msg

        except Exception as e:
            print(e)
            status = "E99"
            msg = e

        return status, msg
