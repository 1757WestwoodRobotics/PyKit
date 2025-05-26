class LoggableInputs:
    def toLog(table: LogTable):
        raise NotImplementedError("needs to be implemented by subclass")

    def fromLog(table: LogTable):
        raise NotImplementedError("needs to be implemented by subclass")
