from wpilib import PowerDistribution

from pykit.logtable import LogTable


class LoggedPowerDistribution:

    moduleId: int
    moduleType: PowerDistribution.ModuleType
    distribution: PowerDistribution

    instance: "LoggedPowerDistribution | None" = None

    def __init__(
        self,
        moduleId: int = 1,
        moduleType: PowerDistribution.ModuleType = PowerDistribution.ModuleType.kRev,
    ) -> None:
        """
        Creates a logged power distribution instance.

        :param moduleId: The ID of the power distribution module.
        :param moduleType: The type of the power distribution module.
        """
        self.moduleId = moduleId
        self.moduleType = moduleType

        self.distribution = PowerDistribution(self.moduleId, self.moduleType)

    @classmethod
    def getInstance(
        cls,
    ) -> "LoggedPowerDistribution":
        """
        Gets the singleton instance of the logged power distribution.

        :param moduleId: The ID of the power distribution module.
        :param moduleType: The type of the power distribution module.
        :return: The singleton instance of the logged power distribution.
        """
        if cls.instance is None:
            cls.instance = LoggedPowerDistribution()
        return cls.instance

    def saveToTable(self, table: LogTable):
        table.put("Voltage", self.distribution.getVoltage())
        table.put("TotalCurrent", self.distribution.getTotalCurrent())
        table.put("TotalPower", self.distribution.getTotalPower())
        table.put("TotalEnergy", self.distribution.getTotalEnergy())
        table.put("Temperature", self.distribution.getTemperature())

        channelCurrets = []
        for channel in range(self.distribution.getNumChannels()):
            channelCurrets.append(self.distribution.getCurrent(channel))

        table.put("ChannelCurrentsList", channelCurrets)
        table.put("ChannelCurrentsTotal", sum(channelCurrets))
