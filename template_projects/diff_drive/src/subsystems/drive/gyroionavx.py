from wpimath.geometry import Rotation2d
from subsystems.drive.gyroio import GyroIO
from navx import AHRS

from constants.math import kRadiansPerDegree


class GyroIONavX(GyroIO):
    def __init__(self) -> None:
        self.navx = AHRS.create_spi()

    def updateInputs(self, inputs: GyroIO.GyroIOInputs) -> None:
        inputs.connected = self.navx.isConnected()
        inputs.yawPosition = Rotation2d.fromDegrees(-self.navx.getAngle())
        inputs.yawVelocityDegPerSec = -self.navx.getRawGyroZ() * kRadiansPerDegree
