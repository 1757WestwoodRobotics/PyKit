from hal import AllianceStationID
from wpilib import DriverStation
from wpilib.simulation import DriverStationSim

from pykit.logtable import LogTable
from pykit.logvalue import LogValue


class LoggedDriverStation:
    """A dataclass for holding Driver Station I/O data."""

    @classmethod
    def saveToTable(cls, table: LogTable):
        """Saves the current Driver Station data to the log table."""
        alliance = DriverStation.getAlliance()
        location = DriverStation.getLocation()
        station = (
            0
            if location is None or alliance is None
            else (location + (3 if alliance == DriverStation.Alliance.kBlue else 0))
        )
        table.put("AllianceStation", station)
        table.put("EventName", DriverStation.getEventName())
        table.put("GameSpecificMessage", DriverStation.getGameSpecificMessage())
        table.put("MatchNumber", DriverStation.getMatchNumber())
        table.put("ReplayNumber", DriverStation.getReplayNumber())
        table.put("MatchType", DriverStation.getMatchType().value)
        table.put("MatchTime", DriverStation.getMatchTime())

        table.put("Enabled", DriverStation.isEnabled())
        table.put("Autonomous", DriverStation.isAutonomous())
        table.put("Test", DriverStation.isTest())
        table.put("EmergencyStop", DriverStation.isEStopped())
        table.put("FMSAttached", DriverStation.isFMSAttached())
        table.put("DSAttached", DriverStation.isDSAttached())

        for i in range(DriverStation.kJoystickPorts):
            joystickTable = table.getSubTable(f"Joystick{i}")
            joystickTable.put("Name", DriverStation.getJoystickName(i).strip())
            joystickTable.put("Type", DriverStation.getJoystickType(i))
            joystickTable.put("Xbox", DriverStation.getJoystickIsXbox(i))
            joystickTable.put("ButtonCount", DriverStation.getStickButtonCount(i))
            joystickTable.put("ButtonValues", DriverStation.getStickButtons(i))

            povCount = DriverStation.getStickPOVCount(i)
            povValues = []
            for j in range(povCount):
                povValues.append(DriverStation.getStickPOV(i, j))
            joystickTable.putValue(
                "POVs", LogValue.withType(LogValue.LoggableType.IntegerArray, povValues)
            )

            axisCount = DriverStation.getStickAxisCount(i)
            axisValues = []
            axisTypes = []
            for j in range(axisCount):
                axisValues.append(DriverStation.getStickAxis(i, j))
                axisTypes.append(DriverStation.getJoystickAxisType(i, j))

            joystickTable.putValue(
                "AxesValues",
                LogValue.withType(LogValue.LoggableType.DoubleArray, axisValues),
            )
            joystickTable.put("AxisTypes", axisTypes)

    @classmethod
    def loadFromTable(cls, table: LogTable):
        DriverStationSim.setAllianceStationId(
            AllianceStationID(
                table.get("AllianceStation", AllianceStationID.kRed1.value)
            )
        )
        DriverStationSim.setEventName(table.get("EventName", ""))
        DriverStationSim.setGameSpecificMessage(table.get("GameSpecificMessage", ""))
        DriverStationSim.setMatchNumber(table.get("MatchNumber", 0))
        DriverStationSim.setReplayNumber(table.get("ReplayNumber", 0))
        DriverStationSim.setMatchType(
            DriverStation.MatchType(table.get("MatchType", 0))
        )
        DriverStationSim.setMatchTime(table.get("MatchTime", -1.0))

        DriverStationSim.setEnabled(table.get("Enabled", False))
        DriverStationSim.setAutonomous(table.get("Autonomous", False))
        DriverStationSim.setTest(table.get("Test", False))
        DriverStationSim.setEStop(table.get("EmergencyStop", False))
        DriverStationSim.setFmsAttached(table.get("FMSAttached", False))
        dsAttached = table.get("DSAttached", False)
        DriverStationSim.setDsAttached(dsAttached)
        for i in range(DriverStation.kJoystickPorts):
            joystickTable = table.getSubTable(f"Joystick{i}")
            # print(joystickTable.getDoubleArray("AxesValues", []))

            buttonValues = joystickTable.get("ButtonValues", 0)
            DriverStationSim.setJoystickButtons(i, buttonValues)

            povValues = joystickTable.get("POVs", [])
            DriverStationSim.setJoystickPOVCount(i, len(povValues))
            for j, pov in enumerate(povValues):
                DriverStationSim.setJoystickPOV(i, j, pov)

            axisValues = joystickTable.get("AxesValues", [])
            axisTypes = joystickTable.get("AxisTypes", [])

            DriverStationSim.setJoystickAxisCount(i, len(axisValues))
            for j, (axis_val, axis_type) in enumerate(zip(axisValues, axisTypes)):
                DriverStationSim.setJoystickAxis(i, j, axis_val)
                DriverStationSim.setJoystickAxisType(i, j, axis_type)

        if dsAttached:
            DriverStationSim.notifyNewData()
