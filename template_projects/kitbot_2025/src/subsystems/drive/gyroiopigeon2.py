from phoenix6 import BaseStatusSignal
from phoenix6.configs import Pigeon2Configuration
from phoenix6.hardware.pigeon2 import Pigeon2
from wpimath.geometry import Rotation2d

from subsystems.drive.gyroio import GyroIO
from subsystems.drive import driveconstants

from constants import kRobotFrequency
from constants.math import kRadiansPerDegree


class GyroIOPigeon2(GyroIO):
    def __init__(self) -> None:
        self.pigeon = Pigeon2(driveconstants.kPigeonCanId)
        self.pigeon.configurator.apply(Pigeon2Configuration())
        self.pigeon.set_yaw(0.0)

        self.yaw = self.pigeon.get_yaw()
        self.yaw_velocity = self.pigeon.get_angular_velocity_z_world()

        BaseStatusSignal.set_update_frequency_for_all(
            kRobotFrequency,
            self.yaw,
            self.yaw_velocity,
        )
        self.pigeon.optimize_bus_utilization()

    def updateInputs(self, inputs: GyroIO.GyroIOInputs) -> None:
        inputs.connected = BaseStatusSignal.refresh_all(
            self.yaw,
            self.yaw_velocity,
        ).is_ok()

        inputs.yawPosition = Rotation2d.fromDegrees(self.yaw.value_as_double)
        inputs.yawVelocityDegPerSec = (
            self.yaw_velocity.value_as_double * kRadiansPerDegree
        )
