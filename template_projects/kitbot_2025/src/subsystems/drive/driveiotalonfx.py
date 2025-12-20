from phoenix6.configs import TalonFXConfiguration
from phoenix6.configs.talon_fx_configs import InvertedValue, NeutralModeValue
from phoenix6.controls.follower import Follower
from phoenix6.controls.velocity_voltage import VelocityVoltage
from phoenix6.controls.voltage_out import VoltageOut
from phoenix6.hardware.core.core_talon_fx import BaseStatusSignal
from phoenix6.hardware.talon_fx import TalonFX
from subsystems.drive.driveio import DriveIO

from constants import kRobotFrequency
from constants.math import kRadiansPerRevolution

import driveconstants
from util.phoenixutil import tryUntilOk


class DriveIOTalonFX(DriveIO):
    voltageRequest: VoltageOut = VoltageOut(0)
    velocityRequest: VelocityVoltage = VelocityVoltage(0)

    def __init__(self) -> None:
        self.leftLeader = TalonFX(driveconstants.kLeftLeaderCanId)
        self.leftFollower = TalonFX(driveconstants.kLeftFollowerCanId)
        self.rightLeader = TalonFX(driveconstants.kRightLeaderCanId)
        self.rightFollower = TalonFX(driveconstants.kRightFollowerCanId)

        config = TalonFXConfiguration()
        config.current_limits.supply_current_limit = driveconstants.kCurrentLimit
        config.current_limits.supply_current_limit_enable = True
        config.motor_output.neutral_mode = NeutralModeValue.BRAKE
        config.feedback.sensor_to_mechanism_ratio = driveconstants.kMotorReduction
        config.slot0.k_p = driveconstants.kRealKp
        config.slot0.k_d = driveconstants.kRealKd

        config.motor_output.inverted = (
            InvertedValue.CLOCKWISE_POSITIVE
            if driveconstants.kLeftInverted
            else InvertedValue.COUNTER_CLOCKWISE_POSITIVE
        )

        tryUntilOk(5, lambda: self.leftLeader.configurator.apply(config, 0.25))
        tryUntilOk(5, lambda: self.leftFollower.configurator.apply(config, 0.25))

        config.motor_output.inverted = (
            InvertedValue.CLOCKWISE_POSITIVE
            if driveconstants.kRightInverted
            else InvertedValue.COUNTER_CLOCKWISE_POSITIVE
        )

        tryUntilOk(5, lambda: self.rightLeader.configurator.apply(config, 0.25))
        tryUntilOk(5, lambda: self.rightFollower.configurator.apply(config, 0.25))

        self.leftFollower.set_control(Follower(self.leftLeader.device_id, False))
        self.rightFollower.set_control(Follower(self.rightLeader.device_id, False))

        self.leftPosition = self.leftLeader.get_position()
        self.leftVelocity = self.leftLeader.get_velocity()
        self.leftAppliedVolts = self.leftLeader.get_motor_voltage()
        self.leftLeaderCurrent = self.leftLeader.get_supply_current()
        self.leftFollowerCurrent = self.leftFollower.get_supply_current()

        self.rightPosition = self.rightLeader.get_position()
        self.rightVelocity = self.rightLeader.get_velocity()
        self.rightAppliedVolts = self.rightLeader.get_motor_voltage()
        self.rightLeaderCurrent = self.rightLeader.get_supply_current()
        self.rightFollowerCurrent = self.rightFollower.get_supply_current()

        BaseStatusSignal.set_update_frequency_for_all(
            kRobotFrequency,
            self.leftPosition,
            self.leftVelocity,
            self.leftAppliedVolts,
            self.leftLeaderCurrent,
            self.leftFollowerCurrent,
            self.rightPosition,
            self.rightVelocity,
            self.rightAppliedVolts,
            self.rightLeaderCurrent,
            self.rightFollowerCurrent,
        )
        self.leftLeader.optimize_bus_utilization()
        self.leftFollower.optimize_bus_utilization()
        self.rightLeader.optimize_bus_utilization()
        self.rightFollower.optimize_bus_utilization()

    def updateInputs(self, inputs: DriveIO.DriveIOInputs) -> None:
        BaseStatusSignal.refresh_all(
            self.leftPosition,
            self.leftVelocity,
            self.leftAppliedVolts,
            self.leftLeaderCurrent,
            self.leftFollowerCurrent,
            self.rightPosition,
            self.rightVelocity,
            self.rightAppliedVolts,
            self.rightLeaderCurrent,
            self.rightFollowerCurrent,
        )

        inputs.leftPositionRad = (
            self.leftPosition.value_as_double * kRadiansPerRevolution
        )
        inputs.leftVelocityRadPerSec = (
            self.leftVelocity.value_as_double * kRadiansPerRevolution
        )
        inputs.leftAppliedVolts = self.leftAppliedVolts.value_as_double
        inputs.leftCurrentAmps = [
            self.leftLeaderCurrent.value_as_double,
            self.leftFollowerCurrent.value_as_double,
        ]

        inputs.rightPositionRad = (
            self.rightPosition.value_as_double * kRadiansPerRevolution
        )
        inputs.rightVelocityRadPerSec = (
            self.rightVelocity.value_as_double * kRadiansPerRevolution
        )
        inputs.rightAppliedVolts = self.rightAppliedVolts.value_as_double
        inputs.rightCurrentAmps = [
            self.rightLeaderCurrent.value_as_double,
            self.rightFollowerCurrent.value_as_double,
        ]

    def setVoltage(self, leftVolts: float, rightVolts: float) -> None:
        self.leftLeader.set_control(self.voltageRequest.with_output(leftVolts))
        self.rightLeader.set_control(self.voltageRequest.with_output(rightVolts))

    def setVelocity(
        self,
        leftRadPerSec: float,
        rightRadPerSec: float,
        leftFFVolts: float,
        rightFFVolts: float,
    ) -> None:
        self.leftLeader.set_control(
            self.velocityRequest.with_velocity(leftRadPerSec).with_feed_forward(
                leftFFVolts
            )
        )
        self.rightLeader.set_control(
            self.velocityRequest.with_velocity(rightRadPerSec).with_feed_forward(
                rightFFVolts
            )
        )
