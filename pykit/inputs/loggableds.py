from wpilib import DriverStation
from wpilib.simulation import DriverStationSim

from pykit.logtable import LogTable


class LoggedDriverStation:
    """A dataclass for holding Driver Station I/O data."""

    def saveToTable(self, table: LogTable):
        """Saves the current Driver Station data to the log table."""
        table.put("AllianceStation", DriverStation.getLocation())
        table.put("EventName", DriverStation.getEventName())
        table.put("GameSpecificMessage", DriverStation.getGameSpecificMessage())
        table.put("MatchNumber", DriverStation.getMatchNumber())
        table.put("ReplayNumber", DriverStation.getReplayNumber())
        table.put("MatchType", DriverStation.getMatchType())
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
            joystickTable.put("POVs", povValues)

            axisCount = DriverStation.getStickAxisCount(i)
            axisValues = []
            axisTypes = []
            for j in range(axisCount):
                axisValues.append(DriverStation.getStickAxis(i, j))
                axisTypes.append(DriverStation.getJoystickAxisType(i, j))

            joystickTable.put("AxesValues", axisValues)
            joystickTable.put("AxisTypes", axisTypes)

    def loadFromTable(self, table: LogTable):
        DriverStationSim.setAllianceStationId(
            table.get("AllianceStation", DriverStation.Alliance.kRed1)
        )
        DriverStationSim.setEventName(table.get("EventName", ""))
        DriverStationSim.setGameSpecificMessage(table.get("GameSpecificMessage", ""))
        DriverStationSim.setMatchNumber(table.get("MatchNumber", 0))
        DriverStationSim.setReplayNumber(table.get("ReplayNumber", 0))
        DriverStationSim.setMatchType(table.get("MatchType", 0))
        DriverStationSim.setMatchTime(table.get("MatchTime", -1.0))

        DriverStationSim.setEnabled(table.get("Enabled", False))
        DriverStationSim.setAutonomous(table.get("Autonomous", False))
        DriverStationSim.setTest(table.get("Test", False))
        DriverStationSim.setEStopped(table.get("EmergencyStop", False))
        DriverStationSim.setFmsAttached(table.get("FMSAttached", False))
        DriverStationSim.setDsAttached(table.get("DSAttached", False))
        for i in range(DriverStation.kJoystickPorts):
            joystickTable = table.getSubTable(f"Joystick{i}")

            buttonValues = joystickTable.get("ButtonValues", 0)
            DriverStationSim.setJoystickButtons(i, buttonValues)

            povValues = joystickTable.get("POVs", [])
            DriverStationSim.setJoystickPOVCount(i, len(povValues))
            for j in range(len(povValues)):
                DriverStationSim.setJoystickPOV(i, j, povValues[j])

            axisValues = joystickTable.get("AxesValues", [])
            axisTypes = joystickTable.get("AxisTypes", [])

            DriverStationSim.setJoystickAxisCount(i, len(axisValues))
            for j in range(len(axisValues)):
                DriverStationSim.setJoystickAxis(i, j, axisValues[j])
                DriverStationSim.setJoystickAxisType(i, j, axisTypes[j])

        if DriverStation.isDSAttached():
            DriverStationSim.notifyNewData()
