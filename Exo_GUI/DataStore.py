from serial.tools.list_ports import comports
from serial.tools.list_ports_common import ListPortInfo
from typing import List
from Utils import UIDefaults

class DataStore:
    def __init__(self) -> None:
        self.baudrateList: List[str] = ["9600", "19200", "38400", "57600", "115200", "2000000"]
        self.selectedBaudrate: int = UIDefaults.defaultBaudrate
        self.selectedPort: str = ""
        self.participantName: str = ""
        self.defaultSaveDir: str = UIDefaults.defaultSaveDir

    def getAvailablePorts(self) -> List[str]:
        ports: List[ListPortInfo] = comports()
        return [f"{p.name} {p.description} pid:{p.pid}" for p in ports]

    def setPort(self, portStr: str) -> None:
        self.selectedPort = portStr.split(" ")[0] if portStr else ""

    def setBaudrate(self, baudStr: str) -> None:
        self.selectedBaudrate = int(baudStr)
        
    def setParticipant(self, name: str) -> None:
        self.participantName = name