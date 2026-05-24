import os
from datetime import datetime
from tkinter import filedialog, messagebox
from typing import List, Tuple
from Utils import MeasurementType

class FileHandler:
    @staticmethod
    def parseData(content: str) -> List[Tuple[float, float, float, float, float, float, float]]:
        data: List[Tuple[float, float, float, float, float, float, float]] = []
        
        # Split the giant string
        packets: List[str] = content.split(";")
        
        for packet in packets:
            # Check for at least 3 commas (which means 4 values)
            if packet.count(",") >= 3:
                try:
                    parts: List[str] = packet.split(",")
                    y1Bic: float = float(parts[0]) # RAW Biceps
                    y2Bic: float = float(parts[1]) # Fil Biceps
                    y1Tri: float = float(parts[2]) # RAW Triceps
                    y2Tri: float = float(parts[3]) # Fil Triceps
                    
                    # Backwards compatibility: If old file doesn't have an angle, default to 90.0
                    angle: float = float(parts[4]) if len(parts) > 4 else 90.0
                    
                    # Return : BicRaw, BicFil, BicAbs, TriRaw, TriFil, TriAbs, Angle
                    data.append((y1Bic, y2Bic, abs(y2Bic), y1Tri, y2Tri, abs(y2Tri), angle))
                except ValueError:
                    # Ignore errors
                    pass
                    
        return data

    @staticmethod
    def loadData(path: str) -> List[Tuple[float, float, float, float, float, float, float]]:
        with open(path, "r") as file:
            content: str = file.read().replace("\n", "").replace("\r", "")
            return FileHandler.parseData(content)

    @staticmethod
    def saveData(typ: MeasurementType, dataStr: str, participant: str, defaultDir: str) -> str:
        os.makedirs(defaultDir, exist_ok=True)
        timestamp: str = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        defName: str = f"{participant}_{typ.name}_{timestamp}.txt"
        
        file: str = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=defName,
            initialdir=defaultDir,
            filetypes=[("Text Files", "*.txt")]
        )
        if file:
            try:
                with open(file, "w", encoding="utf-8") as f:
                    f.write(dataStr)
                messagebox.showinfo("Success", f"File saved to:\n{file}")
                return file
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file:\n{e}")
        return ""