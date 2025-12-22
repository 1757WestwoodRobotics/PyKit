from dataclasses import dataclass, field
from pykit.autolog import autolog
from wpimath.geometry import Rotation2d


class GyroIO:
    @autolog
    @dataclass
    class GyroIOInputs:
        connected: bool = False
        yawPosition: Rotation2d = field(default_factory=lambda: Rotation2d())
        yawVelocityDegPerSec: float = 0.0

    def updateInputs(self, inputs: GyroIOInputs) -> None:
        pass
