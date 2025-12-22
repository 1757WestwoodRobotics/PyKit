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
    """
    A data receiver that writes log data to a `.wpilog` file.

    This class handles the creation and writing of log files in the standard
    WPILib format, including automatic file naming and handling of data types.
    """

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

    def __init__(self, filename: str | None = None) -> None:
        """
        Initializes the WPILOGWriter.

        :param filename: The path to the `.wpilog` file. If None, a default path is used,
                         and the file is named with a random identifier.
        """
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

    def start(self) -> None:
        """
        Initializes the writer by creating the log file and preparing to write data.
        """
        # Create folder if necessary
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)

        # Initialize the WPILOG file
        fullPath = os.path.join(self.folder, self.filename)
        print(f"[WPILogWriter] Creating WPILOG file at {fullPath}")
        if os.path.exists(fullPath):
            print("[WPILogWriter] File exists, overwriting")
            os.remove(fullPath)
        if not RobotBase.isReal():
            DataLogManager.stop()
        try:
            DataLogManager.start(self.folder, self.filename)
        except PermissionError as e:
            print(f"Failed to open WPILOG file! ({e})")
            return
        print(DataLogManager.getLogDir())
        DataLogManager.logNetworkTables(False)
        self.log = DataLogManager.getLog()

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

    def end(self) -> None:
        """
        Closes the log file and performs cleanup.
        In simulation, it can also trigger AdvantageScope to open the log.
        """
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

    def putTable(self, table: LogTable) -> None:
        """
        Writes a `LogTable` to the `.wpilog` file.

        This method handles automatic file renaming, writing timestamp and data entries,
        and ensures that data is only written when it changes.

        :param table: The `LogTable` to write.
        """
        if not self.isOpen:
            return
        if self.autoRename:
            # Auto-rename log file based on timestamp and match info
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

                # Build match text prefix (p/q/e + match number)
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

                # Generate new filename with timestamp, event, and match info
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
                    # Rename log file by closing current and opening new
                    print(f"[WPILogWriter] Renaming log to {filename}")
                    self.log.stop()
                    fullPath = os.path.join(self.folder, self.filename)
                    if os.path.exists(fullPath):
                        print(f"[WPILogWriter] Old file removed ({self.filename})")
                        os.remove(fullPath)

                    DataLogManager.stop()
                    DataLogManager.start(self.folder, filename)
                    self.log = DataLogManager.getLog()
                    self.timestampId = self.log.start(
                        "/Timestamp",
                        LogValue.LoggableType.Integer.getWPILOGType(),
                        wpilogconstants.entryMetadata,
                        0,
                    )
                    self.filename = filename

        # Write timestamp entry
        self.log.appendInteger(
            self.timestampId, table.getTimestamp(), table.getTimestamp()
        )

        # Get current and previous data for change detection
        newMap = table.getAll()
        oldMap = self.lastTable.getAll()

        # Write changed entries to log
        for key, newValue in newMap.items():
            fieldType = newValue.log_type
            fieldUnit = newValue.unit
            appendData = False

            # Register new field or detect changes
            if key not in self.entryIds:
                # New field - create entry in log
                entryId = self.log.start(
                    key,
                    newValue.getWPILOGType(),
                    (
                        wpilogconstants.entryMetadata
                        if fieldUnit is None
                        else wpilogconstants.entryMetadataUnits.replace(
                            "$UNITSTR", fieldUnit
                        )
                    ),
                    table.getTimestamp(),
                )
                self.entryIds[key] = entryId
                self.entryTypes[key] = newValue.log_type
                if fieldUnit is not None:
                    self.entryUnits[key] = fieldUnit

                appendData = True
            elif newValue != oldMap.get(key):
                # Existing field changed - log new value
                appendData = True

            # Detect and warn about type changes
            elif newValue.log_type != self.entryTypes[key]:
                print(
                    f"[WPILOGWriter] Type of {key} changed from "
                    f"{self.entryTypes[key]} to {newValue.log_type}, skipping log"
                )
                continue

            if appendData:
                entryId = self.entryIds[key]
                # check if unit changed
                if fieldUnit is not None and self.entryUnits.get(key) != fieldUnit:
                    self.log.setMetadata(
                        entryId,
                        wpilogconstants.entryMetadataUnits.replace(
                            "$UNITSTR", fieldUnit
                        ),
                        table.getTimestamp(),
                    )
                    self.entryUnits[key] = fieldUnit
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
