from typing import Callable
from commands2 import Command, cmd
from wpilib import Timer
from wpilib.drive import DifferentialDrive

from subsystems.drive.drive import Drive
from util.helpfulmath import deadband

from subsystems.drive import driveconstants


class DriveCommands:
    deadband: float = 0.1
    ff_ramp_rate: float = 0.1  # volts / sec

    @staticmethod
    def arcadeDrive(
        drive: Drive,
        forward: Callable[[], float],
        rotation: Callable[[], float],
    ) -> Command:
        def run():
            fwd = deadband(forward(), DriveCommands.deadband)
            rot = deadband(rotation(), DriveCommands.deadband)

            speeds = DifferentialDrive.arcadeDriveIK(fwd, rot, True)
            drive.runClosedLoopParameters(
                speeds.left * driveconstants.kMaxSpeedMetersPerSecond,
                speeds.right * driveconstants.kMaxSpeedMetersPerSecond,
            )

        return cmd.run(run, drive).withName("Arcade Drive")

    @staticmethod
    def feedForwardCharacterization(drive: Drive) -> Command:
        velocitySamples: list[float] = []
        voltageSamples: list[float] = []
        timer = Timer()

        def setup():
            velocitySamples.clear()
            voltageSamples.clear()
            timer.restart()

        def run():
            voltage = timer.get() * DriveCommands.ff_ramp_rate
            drive.runOpenLoop(voltage, voltage)
            velocitySamples.append(drive.getCharacterizationVelocity())
            voltageSamples.append(voltage)

        def end(_interrupted: bool):
            n = len(velocitySamples)
            sumX = sum(velocitySamples)
            sumY = sum(voltageSamples)
            sumXY = sum(velocitySamples[i] * voltageSamples[i] for i in range(n))
            sumX2 = sum(v**2 for v in velocitySamples)
            kS = (sumY * sumX2 - sumX * sumXY) / (n * sumX2 - sumX * sumX)
            kV = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX)

            print("************************************************************")
            print(f"Feed Forward Characterization Results: \nkS = {kS}\nkV = {kV}")

        return (
            cmd.runOnce(setup)
            .andThen(cmd.run(run, drive).withName("FeedForwardCharacterization"))
            .finallyDo(end)
        )
