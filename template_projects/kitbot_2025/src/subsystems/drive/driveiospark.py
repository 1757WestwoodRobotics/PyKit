from rev import ClosedLoopSlot, SparkMax, SparkMaxConfig
from subsystems.drive.driveio import DriveIO

import driveconstants

from constants.math import kRadiansPerRevolution, kSecondsPerMinute
from util.sparkutil import tryUntilOk, ifOk, ifOkMulti


class DriveIOSpark(DriveIO):

    def __init__(self) -> None:
        self.leftLeader = SparkMax(
            driveconstants.kLeftLeaderCanId, SparkMax.MotorType.kBrushless
        )
        self.rightLeader = SparkMax(
            driveconstants.kRightLeaderCanId, SparkMax.MotorType.kBrushless
        )
        self.leftFollower = SparkMax(
            driveconstants.kLeftFollowerCanId, SparkMax.MotorType.kBrushless
        )
        self.rightFollower = SparkMax(
            driveconstants.kRightFollowerCanId, SparkMax.MotorType.kBrushless
        )

        self.leftEncoder = self.leftLeader.getEncoder()
        self.rightEncoder = self.rightLeader.getEncoder()

        self.leftController = self.leftLeader.getClosedLoopController()
        self.rightController = self.rightLeader.getClosedLoopController()

        config = SparkMaxConfig()
        config.setIdleMode(SparkMaxConfig.IdleMode.kBrake).smartCurrentLimit(
            driveconstants.kCurrentLimit
        ).voltageCompensation(12.0)
        config.closedLoop.pidf(driveconstants.kRealKp, 0.0, driveconstants.kRealKd, 0.0)
        config.encoder.positionConversionFactor(
            kRadiansPerRevolution / driveconstants.kMotorReduction
        ).velocityConversionFactor(
            kRadiansPerRevolution / kSecondsPerMinute / driveconstants.kMotorReduction
        ).uvwMeasurementPeriod(
            10
        ).uvwAverageDepth(
            2
        )

        config.inverted(driveconstants.kLeftInverted)
        tryUntilOk(
            5,
            lambda: self.leftLeader.configure(
                config,
                SparkMax.ResetMode.kResetSafeParameters,
                SparkMax.PersistMode.kPersistParameters,
            ),
        )

        config.inverted(driveconstants.kRightInverted)
        tryUntilOk(
            5,
            lambda: self.rightLeader.configure(
                config,
                SparkMax.ResetMode.kResetSafeParameters,
                SparkMax.PersistMode.kPersistParameters,
            ),
        )

        config.inverted(driveconstants.kLeftInverted).follow(self.leftLeader)
        tryUntilOk(
            5,
            lambda: self.leftFollower.configure(
                config,
                SparkMax.ResetMode.kResetSafeParameters,
                SparkMax.PersistMode.kPersistParameters,
            ),
        )

        config.inverted(driveconstants.kRightInverted).follow(self.rightLeader)
        tryUntilOk(
            5,
            lambda: self.rightFollower.configure(
                config,
                SparkMax.ResetMode.kResetSafeParameters,
                SparkMax.PersistMode.kPersistParameters,
            ),
        )

    def updateInputs(self, inputs: DriveIO.DriveIOInputs) -> None:
        ifOk(
            self.leftLeader,
            self.leftEncoder.getPosition,
            lambda v: setattr(inputs, "leftPositionRad", v),
        )
        ifOk(
            self.leftLeader,
            self.leftEncoder.getVelocity,
            lambda v: setattr(inputs, "leftVelocityRadPerSec", v),
        )
        ifOkMulti(
            self.leftLeader,
            [self.leftLeader.getAppliedOutput, self.leftLeader.getBusVoltage],
            lambda multiResults: setattr(
                inputs,
                "leftAppliedVolts",
                multiResults[0] * multiResults[1],
            ),
        )
        ifOkMulti(
            self.leftLeader,
            [self.leftLeader.getOutputCurrent, self.leftFollower.getOutputCurrent],
            lambda multiResults: setattr(
                inputs,
                "leftCurrentAmps",
                [multiResults[0], multiResults[1]],
            ),
        )

        ifOk(
            self.rightLeader,
            self.rightEncoder.getPosition,
            lambda v: setattr(inputs, "rightPositionRad", v),
        )
        ifOk(
            self.rightLeader,
            self.rightEncoder.getVelocity,
            lambda v: setattr(inputs, "rightVelocityRadPerSec", v),
        )
        ifOkMulti(
            self.rightLeader,
            [self.rightLeader.getAppliedOutput, self.rightLeader.getBusVoltage],
            lambda multiResults: setattr(
                inputs,
                "rightAppliedVolts",
                multiResults[0] * multiResults[1],
            ),
        )
        ifOkMulti(
            self.rightLeader,
            [self.rightLeader.getOutputCurrent, self.rightFollower.getOutputCurrent],
            lambda multiResults: setattr(
                inputs,
                "rightCurrentAmps",
                [multiResults[0], multiResults[1]],
            ),
        )

    def setVoltage(self, leftVolts: float, rightVolts: float) -> None:
        self.leftLeader.setVoltage(leftVolts)
        self.rightLeader.setVoltage(rightVolts)

    def setVelocity(
        self,
        leftRadPerSec: float,
        rightRadPerSec: float,
        leftFFVolts: float,
        rightFFVolts: float,
    ) -> None:
        self.leftController.setReference(
            leftRadPerSec,
            SparkMax.ControlType.kVelocity,
            ClosedLoopSlot.kSlot0,
            leftFFVolts,
        )
        self.rightController.setReference(
            rightRadPerSec,
            SparkMax.ControlType.kVelocity,
            ClosedLoopSlot.kSlot0,
            rightFFVolts,
        )
