class LoggedNetworkInput:
    prefix: str = "NetworkInputs"

    def __init__(self) -> None:
        pass

    def periodic(self):
        pass

    @staticmethod
    def removeSlash(key: str):
        if key.startswith("/"):
            return key[1:]
        return key
