from typing import Callable
from commands2 import Command, Subsystem, cmd
from pykit.logger import Logger

from subsystems.roller.rollerio import RollerIO


class Roller(Subsystem):
    def __init__(self, io: RollerIO) -> None:
        self.io = io
        self.inputs = RollerIO.RollerIOInputs()

    def periodic(self) -> None:
        self.io.updateInputs(self.inputs)
        Logger.processInputs("Roller", self.inputs)

    def runPercent(self, percent: float) -> Command:
        return cmd.runEnd(
            lambda: self.io.setVoltage(percent * 12.0),
            lambda: self.io.setVoltage(0.0),
            self,
        )

    def runTeleop(
        self, forward: Callable[[], float], reverse: Callable[[], float]
    ) -> Command:
        def execute() -> None:
            volts = (forward() - reverse()) * 12.0
            self.io.setVoltage(volts)

        return cmd.runEnd(
            execute,
            lambda: self.io.setVoltage(0.0),
            self,
        )
