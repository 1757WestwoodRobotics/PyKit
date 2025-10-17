from wpilib import DriverStation

from pykit.logtable import LogTable


class DSIO:
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
            js = DriverStation.getJoystickAxes(i)
            table.put(f"Joystick{i}/Axes", js)

            btns = DriverStation.getJoystickButtons(i)
            table.put(f"Joystick{i}/Buttons", btns)

            povs = DriverStation.getJoystickPOVs(i)
            table.put(f"Joystick{i}/POVs", povs)
