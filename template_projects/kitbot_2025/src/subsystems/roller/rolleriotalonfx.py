from phoenix6 import BaseStatusSignal
from phoenix6.configs import TalonFXConfiguration
from phoenix6.configs.talon_fx_configs import NeutralModeValue
from phoenix6.controls import VoltageOut
from phoenix6.hardware.talon_fx import TalonFX
from subsystems.roller.rollerio import RollerIO
from subsystems.roller import rollerconstants

from util.phoenixutil import tryUntilOk

from constants import kRobotFrequency
from constants.math import kRadiansPerRevolution


class RollerIOTalonFX(RollerIO):
    voltageRequest: VoltageOut = VoltageOut(0)

    def __init__(self) -> None:
        self.rollerMotor = TalonFX(rollerconstants.kRollerCanId)

        config = TalonFXConfiguration()
        config.current_limits.supply_current_limit = rollerconstants.kCurrentLimit
        config.current_limits.supply_current_limit_enable = True
        config.motor_output.neutral_mode = NeutralModeValue.BRAKE

        tryUntilOk(5, lambda: self.rollerMotor.configurator.apply(config, 0.25))

        self.positionRot = self.rollerMotor.get_position()
        self.velocityRotPerSec = self.rollerMotor.get_velocity()
        self.appliedVolts = self.rollerMotor.get_motor_voltage()
        self.supplyCurrent = self.rollerMotor.get_supply_current()

        BaseStatusSignal.set_update_frequency_for_all(
            kRobotFrequency,
            self.positionRot,
            self.velocityRotPerSec,
            self.appliedVolts,
            self.supplyCurrent,
        )
        self.rollerMotor.optimize_bus_utilization()

    def updateInputs(self, inputs: RollerIO.RollerIOInputs) -> None:
        BaseStatusSignal.refresh_all(
            self.positionRot,
            self.velocityRotPerSec,
            self.appliedVolts,
            self.supplyCurrent,
        )
        inputs.positionRad = self.positionRot.value_as_double * kRadiansPerRevolution
        inputs.velocityRadPerSec = (
            self.velocityRotPerSec.value_as_double * kRadiansPerRevolution
        )
        inputs.appliedVolts = self.appliedVolts.value_as_double
        inputs.currentAmps = self.supplyCurrent.value_as_double

    def setVoltage(self, volts: float) -> None:
        self.rollerMotor.set_control(self.voltageRequest.with_output(volts))
