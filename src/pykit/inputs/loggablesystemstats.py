from hal import (
    CAN_GetCANStatus,
    getBrownedOut,
    getBrownoutVoltage,
    getCPUTemp,
    getComments,
    getCommsDisableCount,
    getFPGAButton,
    getFPGARevision,
    getFPGAVersion,
    getRSLState,
    getSerialNumber,
    getSystemActive,
    getSystemTimeValid,
    getTeamNumber,
    getUserActive3V3,
    getUserActive5V,
    getUserActive6V,
    getUserCurrent3V3,
    getUserCurrent5V,
    getUserCurrent6V,
    getUserCurrentFaults3V3,
    getUserCurrentFaults5V,
    getUserCurrentFaults6V,
    getUserVoltage3V3,
    getUserVoltage5V,
    getUserVoltage6V,
    getVinCurrent,
    getVinVoltage,
)
from ntcore import NetworkTableInstance
from pykit.logtable import LogTable


class LoggedSystemStats:
    lastNTRemoteIds: set[str] = set()

    @classmethod
    def saveToTable(cls, table: LogTable):
        # for some reason these return tuples of length 2, take the first element
        table.put("FPGAVersion", getFPGAVersion()[0])
        table.put("FPGARevision", getFPGARevision()[0])
        table.put("SerialNumber", getSerialNumber())
        table.put("Comments", getComments())
        table.put("TeamNumber", getTeamNumber())
        table.put("FPGAButton", getFPGAButton()[0])
        table.put("SystemActive", getSystemActive()[0])
        table.put("BrownedOut", getBrownedOut()[0])
        table.put("CommsDisabledCount", getCommsDisableCount()[0])
        table.put("RSLState", getRSLState()[0])
        table.put("SystemTimeValid", getSystemTimeValid()[0])

        table.put("BatteryVoltage", getVinVoltage()[0])
        table.put("BatteryCurrent", getVinCurrent()[0])

        table.put("3v3Rail/Voltage", getUserVoltage3V3()[0])
        table.put("3v3Rail/Current", getUserCurrent3V3()[0])
        table.put("3v3Rail/Active", getUserActive3V3()[0])
        table.put("3v3Rail/CurrentFaults", getUserCurrentFaults3V3()[0])

        table.put("5vRail/Voltage", getUserVoltage5V()[0])
        table.put("5vRail/Current", getUserCurrent5V()[0])
        table.put("5vRail/Active", getUserActive5V()[0])
        table.put("5vRail/CurrentFaults", getUserCurrentFaults5V()[0])

        table.put("6vRail/Voltage", getUserVoltage6V()[0])
        table.put("6vRail/Current", getUserCurrent6V()[0])
        table.put("6vRail/Active", getUserActive6V()[0])
        table.put("6vRail/CurrentFaults", getUserCurrentFaults6V()[0])

        table.put("BrownoutVoltage", getBrownoutVoltage()[0])
        table.put("CPUTempCelsius", getCPUTemp()[0])

        canbusStatus = CAN_GetCANStatus()
        (
            percentBusUtilization,
            busOffCount,
            txFullCount,
            receiveErrorCount,
            transmitErrorCount,
            errorStatus,
        ) = canbusStatus

        table.put("CANBus/PercentBusUtilization", percentBusUtilization)
        table.put("CANBus/BusOffCount", busOffCount)
        table.put("CANBus/TxFullCount", txFullCount)
        table.put("CANBus/ReceiveErrorCount", receiveErrorCount)
        table.put("CANBus/TransmitErrorCount", transmitErrorCount)
        table.put("CANBus/ErrorStatus", errorStatus)

        ntClientsTable = table.getSubTable("NTClients")

        ntConnections = NetworkTableInstance.getDefault().getConnections()

        ntRemoteIds = set()
        for connection in ntConnections:
            if connection.remote_id in LoggedSystemStats.lastNTRemoteIds:
                LoggedSystemStats.lastNTRemoteIds.remove(connection.remote_id)
            ntRemoteIds.add(connection.remote_id)

            ntClientTable = ntClientsTable.getSubTable(connection.remote_id)

            ntClientTable.put("Connected", True)
            ntClientTable.put("IPAddress", connection.remote_ip)
            ntClientTable.put("RemotePort", connection.remote_port)
            ntClientTable.put("ProtocolVersion", connection.protocol_version)

        # Mark disconnected clients
        for remoteId in LoggedSystemStats.lastNTRemoteIds:
            ntClientTable = ntClientsTable.getSubTable(remoteId)
            ntClientTable.put("Connected", False)

        LoggedSystemStats.lastNTRemoteIds = ntRemoteIds
