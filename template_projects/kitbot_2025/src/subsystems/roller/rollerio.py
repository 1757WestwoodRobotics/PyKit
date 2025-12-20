from dataclasses import dataclass
from pykit.autolog import autolog


class RollerIO:
    @autolog
    @dataclass
    class RollerIOInputs:
        positionRad: float = 0.0
        velocityRadPerSec: float = 0.0
        appliedVolts: float = 0.0
        currentAmps: float = 0.0

    def updateInputs(self, inputs: RollerIOInputs) -> None:
        pass

    def setVoltage(self, volts: float) -> None:
        pass
