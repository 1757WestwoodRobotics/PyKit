from wpimath.system.plant import DCMotor
from pathplannerlib.config import ModuleConfig, RobotConfig
from constants.math import kMetersPerInch

kMaxSpeedMetersPerSecond = 4.0
kTrackWidth = 26 * kMetersPerInch

kPigeonCanId = 9
kLeftLeaderCanId = 1
kLeftFollowerCanId = 2
kRightLeaderCanId = 3
kRightFollowerCanId = 4

kCurrentLimit = 60.0
kWheelRadius = 3 * kMetersPerInch
kMotorReduction = 10.71
kLeftInverted = False
kRightInverted = True
kGearbox = DCMotor.CIM(2)

kRealKp = 0.0
kRealKd = 0.0
kRealKs = 0.0
kRealKv = 0.1

kSimKp = 0.0
kSimKd = 0.0
kSimKs = 0.0
kSimKv = 0.227

kRobotMassKg = 74.088
kRobotMOI = 6.883
kWheelCOF = 1.2

kPPConfig = RobotConfig(
    kRobotMassKg,
    kRobotMOI,
    ModuleConfig(
        kWheelRadius,
        kMaxSpeedMetersPerSecond,
        kWheelCOF,
        kGearbox.withReduction(kMotorReduction),
        kCurrentLimit,
        2,
    ),
    [],
    kTrackWidth,
)
