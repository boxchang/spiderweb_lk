class SAPDataStatusAction():
    vnedc_db = None
    scada_db = None
    status = None

    def __init__(self, obj):
        self.vnedc_db = obj.vnedc_db
        self.scada_db = obj.scada_db
        self.status = obj.status

    # Check if there is no data for a long time
    def CheckDataStatus(self, device):
        device_name = device.device_name
        msg = ""
        status = "S01"

        try:
            # 判斷小票資料上傳ERP失敗
            if device_name == 'WORK_IN_PROCESS':
                sql = f"""
                        select top 120 
                        IIF(CHARINDEX('nbr',r.WorkCenterName)>0, 'nbr', 'pvc') as WorkCentertype, 
                        r.WorkOrderId, r.id runId, r.LineName, r.Period,
                        d.*, p.StorageLocation
                        from [PMGMES].[dbo].PMG_MES_WorkInProcessDetail d (nolock) inner join [PMGMES].[dbo].PMG_MES_WorkInProcess p (nolock) on d.WorkInProcessId=p.id
                        inner join [PMGMES].[dbo].PMG_MES_RunCard r (nolock) on p.RunCardId=r.id
                        where d.PrintType='ticket' and d.CreationTime BETWEEN DATEADD(HOUR, -2, GETDATE()) AND DATEADD(HOUR, -1, GETDATE())
                        and ( D.IsERP=0 or D.ErpSTATUS != 'S' )
                        order by D.IsERP desc, WorkCentertype, r.WorkOrderId, D.PrintDate desc
                                                    """
                rows = self.scada_db.select_sql_dict(sql)

                if len(rows) != 0:
                    status = "E08"
                    msg = rows[0]['ErpMESSAGE']

            # 判斷二級品資料上傳ERP失敗
            elif device_name == 'FAULTY_DETAIL':
                sql = f"""
                        SELECT LotNo, EmployeeId
                        FROM [PMGMES].[dbo].[PMG_MES_FaultyDetail]
                        WHERE ErpSTATUS != 'S'
                        AND ErpReturnDate BETWEEN DATEADD(HOUR, -2, GETDATE()) AND DATEADD(HOUR, -1, GETDATE())
                        """
                rows = self.scada_db.select_sql_dict(sql)

                if len(rows) != 0:
                    status = "E08"
                    msg = rows[0]['ErpMESSAGE']

            # 判斷廢品資料上傳ERP失敗
            elif device_name == 'SCRAP_DETAIL':
                sql = f"""
                        select LotNo, EmployeeId
                        from [PMGMES].[dbo].[PMG_MES_ScrapDetail]
                        where ErpSTATUS != 'S' 
                        AND ErpReturnDate BETWEEN DATEADD(HOUR, -2, GETDATE()) AND DATEADD(HOUR, -1, GETDATE())
                        """
                rows = self.scada_db.select_sql_dict(sql)

                if len(rows) != 0:
                    status = "E08"
                    msg = rows[0]['ErpMESSAGE']
            elif device_name == 'DATA_DOUBLE':
                sql = """
                            SELECT CONVERT(VARCHAR(19), CreationTime, 120) AS xx,RuncardId, count(*)
                              FROM [PMGMES].[dbo].[PMG_MES_WorkInProcess] where CreationTime > GETDATE() - 1
                              group by CONVERT(VARCHAR(19), CreationTime, 120),RuncardId having count(*) > 1
                            """
                rows = self.scada_db.select_sql_dict(sql)
                if len(rows) != 0:
                    status = "E12"
                    runcard = rows[0]['RuncardId']
                    msg = f"{runcard} data is duplicated in SAP, please check!"

        except Exception as e:
            print(e)
            status = "E99"
            msg = e

        return status, msg