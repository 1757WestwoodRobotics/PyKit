from ntcore import NetworkTableInstance, StringArraySubscriber

from pykit.logtable import LogTable


class AlertLogger:
    groups: list[str] = []
    errorSubscribers: dict[str, StringArraySubscriber] = {}
    warningSubscribers: dict[str, StringArraySubscriber] = {}
    infoSubscribers: dict[str, StringArraySubscriber] = {}

    @classmethod
    def periodic(cls, outputTable: LogTable) -> None:
        """
        Periodically checks for new alerts and logs them.
        """
        for group in cls.groups:
            outputTable.put(f"{group}/.type", "Alerts")
            if group not in cls.errorSubscribers:
                cls.errorSubscribers[group] = (
                    NetworkTableInstance.getDefault()
                    .getStringArrayTopic(f"/SmartDashboard/{group}/errors")
                    .subscribe([])
                )
            if group not in cls.warningSubscribers:
                cls.warningSubscribers[group] = (
                    NetworkTableInstance.getDefault()
                    .getStringArrayTopic(f"/SmartDashboard/{group}/warnings")
                    .subscribe([])
                )
            if group not in cls.infoSubscribers:
                cls.infoSubscribers[group] = (
                    NetworkTableInstance.getDefault()
                    .getStringArrayTopic(f"/SmartDashboard/{group}/info")
                    .subscribe([])
                )
            outputTable.put(f"{group}/errors", cls.errorSubscribers[group].get())
            outputTable.put(f"{group}/warnings", cls.warningSubscribers[group].get())
            outputTable.put(f"{group}/info", cls.infoSubscribers[group].get())

    @classmethod
    def registerGroup(cls, group: str) -> None:
        """
        Registers a new alert group to monitor.

        :param group: The name of the alert group.
        """
        if group not in cls.groups:
            cls.groups.append(group)
