import time
from typing import List, Tuple, TYPE_CHECKING
from SerialManager import SerialManager
from Utils import CommunicationProtocol
from FileHandler import FileHandler

if TYPE_CHECKING:
    from MeasurementWindows import BaseMeasurementWindow

class MeasurementEngine:
    def __init__(self, serialManager: SerialManager) -> None:
        self.serialMgr: SerialManager = serialManager
        self._streamBuffer: str = ""

    def startStream(self) -> None:
        if self.serialMgr.isConnected():
            self.serialMgr.serial.reset_input_buffer()
            self._streamBuffer = ""
            self.serialMgr.sendCommand(CommunicationProtocol.Measurement)

    def stopStream(self) -> None:
        if self.serialMgr.isConnected():
            self.serialMgr.sendCommand(CommunicationProtocol.Stop)
            self.serialMgr.readData(timeout=1.0)
    
    def closeStream(self) -> None:
        if self.serialMgr.isConnected():
            self.serialMgr.disconnect()

    # Note the updated Type Hint to expect 7 floats!
    def getRealtimeChunk(self) -> List[Tuple[float, float, float, float, float, float, float]]:
        if not self.serialMgr.isConnected(): 
            return []
            
        new_data = self.serialMgr.readAvailable()
        if not new_data:
            return []
            
        self._streamBuffer += new_data
        packets = self._streamBuffer.split(";")
        self._streamBuffer = packets.pop() 
        
        if not packets:
            return []
            
        to_parse = ";".join(packets) + ";"
        return FileHandler.parseData(to_parse)

    def runSteadyRoutine(self, window: 'BaseMeasurementWindow') -> str:
        duration: float = 5.0
        percent: float = 100.0 / (duration / 0.05) 
        buffer: str = ""
        
        if self.serialMgr.handshake():
            self.serialMgr.sendCommand(CommunicationProtocol.Measurement) 
            start: float = time.time()
            
            while time.time() - start <= duration:
                if window.isClosed: break # Stop immediately if window is closed
                
                buffer += self.serialMgr.readAvailable()
                window.progressTheBar(percent)
                window.messWindow.update()
                time.sleep(0.05) 
                
            self.serialMgr.sendCommand(CommunicationProtocol.Stop) 
            buffer += self.serialMgr.readData(timeout=1.0) 
            window.progressTheBar(100.0)
            
        return buffer

    def runRepetitiveRoutine(self, window: 'BaseMeasurementWindow', reps: int, recordDuration: float, pauseDuration: float, actionText: str, pauseText: str, preActionPause: float = 1.0) -> str:
        percentPerRep: float = 100.0 / float(reps)
        buffer: str = ""

        if self.serialMgr.handshake():
            for i in range(reps):
                if window.isClosed: break # Stop immediately if window is closed
                
                repInfo: str = f"Rep {i+1}/{reps}: "
                
                window.updateInstruction(repInfo + pauseText)
                startPause: float = time.time()
                while time.time() < startPause + pauseDuration:
                    if window.isClosed: return buffer
                    window.messWindow.update()
                    time.sleep(0.05)

                window.updateInstruction(repInfo + "Get Ready...")
                if window.isClosed: break
                time.sleep(preActionPause)

                window.updateInstruction(repInfo + actionText)
                self.serialMgr.sendCommand(CommunicationProtocol.Measurement)
                
                startRec: float = time.time()
                while time.time() <= startRec + recordDuration:
                    if window.isClosed: break # Stop recording if closed
                    
                    buffer += self.serialMgr.readAvailable()
                    window.messWindow.update() 
                    time.sleep(0.02)
                
                self.serialMgr.sendCommand(CommunicationProtocol.Stop)
                buffer += self.serialMgr.readData(timeout=1.0) 
                
                window.progressTheBar(percentPerRep)
            
            window.updateInstruction("Measurement Complete!")
            
        return buffer