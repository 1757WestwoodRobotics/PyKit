import os
from enum import Enum
from wpilib import RobotBase


class RobotModes(Enum):
    """Enum for robot modes."""

    REAL = 1
    SIMULATION = 2
    REPLAY = 3


kSimMode = (
    RobotModes.REPLAY
    if "LOG_PATH" in os.environ and os.environ["LOG_PATH"] != ""
    else RobotModes.SIMULATION
)
kRobotMode = RobotModes.REAL if RobotBase.isReal() else kSimMode

kRobotFrequency = 50
kRobotPeriod = 1.0 / kRobotFrequency
