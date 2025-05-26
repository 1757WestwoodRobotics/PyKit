from pykit.autolog import autolog
from dataclasses import dataclass
from wpilib import DriverStation


@autolog
@dataclass
class DSIO:
    """A dataclass for holding Driver Station I/O data."""

    enabled: bool = False
    alliance: str = "kBlue"
    isAuto: bool = False

    def update(self):
        """Updates the fields with the current Driver Station data."""
        ds = DriverStation.getInstance()
        self.enabled = ds.isEnabled()
        self.alliance = ds.getAlliance().name
        self.isAuto = ds.isAutonomous()
