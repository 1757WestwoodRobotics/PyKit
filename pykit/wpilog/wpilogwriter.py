import os
import random
import datetime
from tempfile import gettempdir

from typing import TYPE_CHECKING

from hal import MatchType
from wpilib import DataLogManager, RobotBase, RobotController
from pykit.logdatareciever import LogDataReciever
from pykit.logger import Logger
from pykit.logtable import LogTable
from pykit.logvalue import LogValue
from pykit.wpilog import wpilogconstants

if TYPE_CHECKING:
    from wpiutil.log import DataLog


ASCOPE_FILENAME = "ascope-log-path.txt"


class WPILOGWriter(LogDataReciever):
    """Writes a LogTable to a .wpilog file."""

    log: "DataLog"
    defaultPathRio: str = "/U/logs"
    defaultPathSim: str = "pyLogs"

    folder: str
    filename: str
    randomIdentifier: str
    dsAttachedTime: int = 0
    autoRename: bool
    logDate: datetime.datetime | None
    logMatchText: str

    isOpen: bool = False
    lastTable: LogTable
    timestampId: int
    entryIds: dict[str, int]
    entryTypes: dict[str, LogValue.LoggableType]
    entryUnits: dict[str, str]

    def __init__(self, filename: str | None = None):
        path = self.defaultPathSim if RobotBase.isSimulation() else self.defaultPathRio

        self.randomIdentifier = f"{random.randint(0, 0xFFFF):04X}"

        self.folder = os.path.abspath(
            os.path.dirname(filename) if filename is not None else path
        )
        self.filename = (
            os.path.basename(filename)
            if filename is not None
            else f"pykit_{self.randomIdentifier}.wpilog"
        )
        self.autoRename = False

    def start(self):
        # create folder if necessary
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)

        # delete log if it exists

        # create a new log
        fullPath = os.path.join(self.folder, self.filename)
        print(f"[WPILogWriter] Creating WPILOG file at {fullPath}")
        # DataLogManager.stop()  # ensure its fully stopped
        if os.path.exists(fullPath):
            print("[WPILogWriter] File exists, overwriting")
            os.remove(fullPath)
        DataLogManager.stop()
        DataLogManager.start(self.folder, self.filename)
        print(DataLogManager.getLogDir())
        DataLogManager.logNetworkTables(False)
        self.log = DataLogManager.getLog()
        # self.log = DataLogWriter(fullPath, wpilogconstants.extraHeader)

        self.isOpen = True
        self.timestampId = self.log.start(
            self.timestampKey,
            LogValue.LoggableType.Integer.getWPILOGType(),
            wpilogconstants.entryMetadata,
            0,
        )
        self.lastTable = LogTable(0)

        self.entryIds: dict[str, int] = {}
        self.entryTypes: dict[str, LogValue.LoggableType] = {}
        self.entryUnits: dict[str, str] = {}
        self.logDate = None
        self.logMatchText = f"pykit_{self.randomIdentifier}"

    def end(self):
        print("[WPILogWriter] Shutting down")
        self.log.flush()
        self.log.stop()

        if RobotBase.isSimulation() and Logger.isReplay():
            # open ascope
            fullpath = os.path.join(gettempdir(), ASCOPE_FILENAME)
            if not os.path.exists(gettempdir()):
                return
            fullLogPath = os.path.abspath(os.path.join(self.folder, self.filename))
            print(f"Sending {fullLogPath} to AScope")
            with open(fullpath, "w", encoding="utf-8") as f:
                f.write(fullLogPath)

        # DataLogManager.stop()

    def putTable(self, table: LogTable):
        if not self.isOpen:
            return
        if self.autoRename:
            # rename log if necessary
            if self.logDate is None:
                if (
                    table.get("DriverStation/DSAttached", False)
                    and table.get("SystemStats/SystemTimeValid", False)
                ) or RobotBase.isSimulation():
                    if self.dsAttachedTime == 0:
                        self.dsAttachedTime = RobotController.getFPGATime() / 1e6
                    elif (
                        RobotController.getFPGATime() / 1e6 - self.dsAttachedTime
                    ) > 5 or RobotBase.isSimulation():
                        self.logDate = datetime.datetime.now()
                else:
                    self.dsAttachedTime = 0

                matchType: MatchType
                match table.get("DriverStation/MatchType", 0):
                    case 1:
                        matchType = MatchType.practice
                    case 2:
                        matchType = MatchType.qualification
                    case 3:
                        matchType = MatchType.elimination
                    case _:
                        matchType = MatchType.none

                if self.logMatchText == "" and matchType != MatchType.none:
                    match matchType:
                        case MatchType.practice:
                            self.logMatchText = "p"
                        case MatchType.qualification:
                            self.logMatchText = "q"
                        case MatchType.elimination:
                            self.logMatchText = "e"
                        case _:
                            self.logMatchText = "u"
                    self.logMatchText += str(table.get("DriverStation/MatchNumber", 0))

                # update filename
                filename = "pykit_"
                if self.logDate is not None:
                    filename += self.logDate.strftime("%Y%m%d_%H%M%S")
                else:
                    filename += self.randomIdentifier
                eventName = (
                    table.get("DriverStation/EventName", "").lower().replace(" ", "_")
                )
                if eventName != "":
                    filename += f"_{eventName}"
                if self.logMatchText != "":
                    filename += f"_{self.logMatchText}"
                filename += ".wpilog"
                if self.filename != filename:
                    print(f"[WPILogWriter] Renaming log to {filename}")
                    # DataLogManager.stop()
                    # self.log.stop()
                    self.log.stop()
                    fullPath = os.path.join(self.folder, self.filename)
                    if os.path.exists(fullPath):
                        print(f"[WPILogWriter] Old file removed ({self.filename})")
                        os.remove(fullPath)

                    # DataLogManager.logNetworkTables(False)
                    DataLogManager.stop()
                    DataLogManager.start(self.folder, filename)
                    self.log = DataLogManager.getLog()
                    # self.log = DataLogWriter(fullPath)
                    # self.log._startFile()
                    self.timestampId = self.log.start(
                        "/Timestamp",
                        LogValue.LoggableType.Integer.getWPILOGType(),
                        wpilogconstants.entryMetadata,
                        0,
                    )
                    self.filename = filename

        # write timestamp
        self.log.appendInteger(
            self.timestampId, table.getTimestamp(), table.getTimestamp()
        )

        # get new and old data
        newMap = table.getAll()
        oldMap = self.lastTable.getAll()

        # encode fields
        for key, newValue in newMap.items():
            fieldType = newValue.log_type
            appendData = False

            if key not in self.entryIds:  # new field
                entryId = self.log.start(
                    key,
                    newValue.getWPILOGType(),
                    wpilogconstants.entryMetadata,
                    table.getTimestamp(),
                )
                self.entryIds[key] = entryId
                self.entryTypes[key] = newValue.log_type
                self.entryUnits[key] = ""

                appendData = True
            elif newValue != oldMap.get(key):  # existing field changed
                appendData = True

            # check if type changed
            elif newValue.log_type != self.entryTypes[key]:
                print(
                    f"[WPILOGWriter] Type of {key} changed from "
                    f"{self.entryTypes[key]} to {newValue.log_type}, skipping log"
                )
                continue

            if appendData:
                entryId = self.entryIds[key]
                match fieldType:
                    case LogValue.LoggableType.Raw:
                        self.log.appendRaw(
                            entryId, newValue.value, table.getTimestamp()
                        )
                    case LogValue.LoggableType.Boolean:
                        self.log.appendBoolean(
                            entryId, newValue.value, table.getTimestamp()
                        )
                    case LogValue.LoggableType.Integer:
                        self.log.appendInteger(
                            entryId, newValue.value, table.getTimestamp()
                        )
                    case LogValue.LoggableType.Float:
                        self.log.appendFloat(
                            entryId, newValue.value, table.getTimestamp()
                        )
                    case LogValue.LoggableType.Double:
                        self.log.appendDouble(
                            entryId, newValue.value, table.getTimestamp()
                        )
                    case LogValue.LoggableType.String:
                        self.log.appendString(
                            entryId, newValue.value, table.getTimestamp()
                        )
                    case LogValue.LoggableType.BooleanArray:
                        self.log.appendBooleanArray(
                            entryId, newValue.value, table.getTimestamp()
                        )
                    case LogValue.LoggableType.IntegerArray:
                        self.log.appendIntegerArray(
                            entryId, newValue.value, table.getTimestamp()
                        )
                    case LogValue.LoggableType.FloatArray:
                        self.log.appendFloatArray(
                            entryId, newValue.value, table.getTimestamp()
                        )
                    case LogValue.LoggableType.DoubleArray:
                        self.log.appendDoubleArray(
                            entryId, newValue.value, table.getTimestamp()
                        )
                    case LogValue.LoggableType.StringArray:
                        self.log.appendStringArray(
                            entryId, newValue.value, table.getTimestamp()
                        )

        self.log.flush()
        self.lastTable = table
