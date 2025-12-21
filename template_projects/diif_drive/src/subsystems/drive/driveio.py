from dataclasses import dataclass, field
from pykit.autolog import autolog


class DriveIO:
    @autolog
    @dataclass
    class DriveIOInputs:
        leftPositionRad: float = 0.0
        leftVelocityRadPerSec: float = 0.0
        leftAppliedVolts: float = 0.0
        leftCurrentAmps: list[float] = field(default_factory=list)

        rightPositionRad: float = 0.0
        rightVelocityRadPerSec: float = 0.0
        rightAppliedVolts: float = 0.0
        rightCurrentAmps: list[float] = field(default_factory=list)

    def updateInputs(self, inputs: DriveIOInputs) -> None:
        pass

    def setVoltage(self, leftVolts: float, rightVolts: float) -> None:
        pass

    def setVelocity(
        self,
        leftRadPerSec: float,
        rightRadPerSec: float,
        leftFFVolts: float,
        rightFFVolts: float,
    ) -> None:
        pass
