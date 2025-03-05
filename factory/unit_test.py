from factory.factory_equipment import CountingDeviceMonitor, AOIDeviceMonitor, ScadaPLCMonitor
from factory.key_device import KeyDeviceMonitor
from factory.mes_data_status import MesDataStatusMonitor
from factory.sap_data_status import SapDataStatusMonitor
from factory.wecom import WecomMonitor

m = CountingDeviceMonitor()
m.monitor()

# m = AOIDeviceMonitor()
# m.monitor()

# m = ScadaPLCMonitor()
# m.monitor()

# m = MesDataStatusMonitor()
# m.monitor()

# m = KeyDeviceMonitor()
# m.monitor()

# m = WecomMonitor()
# m.monitor()

# m = SapDataStatusMonitor()
# m.monitor()