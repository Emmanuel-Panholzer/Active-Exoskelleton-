import time
from serial import Serial, SerialException
from Utils import CommunicationProtocol

class SerialManager:
    def __init__(self) -> None:
        self.serial: Serial = Serial()
        self.serial.timeout = 0

    def connect(self, port: str, baud: int) -> bool:
        self.disconnect()
        self.serial.port = port
        self.serial.baudrate = baud
        try:
            self.serial.open()
            return True
        except SerialException:
            self.disconnect()
            return False

    def disconnect(self) -> bool:
        try:
            if self.serial.is_open:
                self.serial.close()
            return True
        except SerialException:
            return False

    def isConnected(self) -> bool:
        return self.serial.is_open

    def sendCommand(self, cmd: CommunicationProtocol) -> None:
        val: str = str(cmd.value) + "#"
        self.serial.write(val.encode('utf-8'))

    # NEW: Updated to take windowSize and isRolling
    def sendParameters(self, weight: float, threshold: float, speed: float, windowSize: int, isRolling: int) -> None:
        if self.isConnected():
            wInt: int = int(weight * 1000)
            tInt: int = int(threshold * 1000)
            sInt: int = int(speed * 1000)
            cmdStr: str = f"{CommunicationProtocol.UpdateParams.value}{wInt},{tInt},{sInt},{windowSize},{isRolling}#"
            self.serial.write(cmdStr.encode('utf-8'))

    def readAvailable(self) -> str:
        if self.isConnected() and self.serial.in_waiting > 0:
            chunk: bytes = self.serial.read(self.serial.in_waiting)
            return chunk.decode('utf-8', errors='replace')
        return ""

    def readData(self, timeout: float = 2.0) -> str:
        endChar: int = ord('#')
        buffer: bytearray = bytearray()
        start: float = time.time()
        
        while True:
            chunk: bytes = self.serial.read(self.serial.in_waiting or 1)
            if chunk:
                pos: int = chunk.find(endChar)
                if pos != -1:
                    buffer.extend(chunk[:pos])
                    return buffer.decode('utf-8', errors='replace')
                buffer.extend(chunk)
            if time.time() - start > timeout:
                return buffer.decode('utf-8', errors='replace')

    def handshake(self) -> bool:
        if not self.isConnected(): 
            return False
        self.serial.reset_input_buffer() 
        self.sendCommand(CommunicationProtocol.Handshake)
        msg: str = self.readData()
        return msg == CommunicationProtocol.HandshakeBack.value