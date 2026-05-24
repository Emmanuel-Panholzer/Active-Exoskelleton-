from tkinter import *
from tkinter.ttk import Progressbar
from tkinter import messagebox
from typing import List, Tuple, TYPE_CHECKING, Optional
import os
from Utils import MeasurementType
from FileHandler import FileHandler
from Plotting import StoredDataPlot

if TYPE_CHECKING:
    from DataStore import DataStore
    from MeasurementEngine import MeasurementEngine


class BaseMeasurementWindow:
    def __init__(self, 
                 master: Tk, 
                 typ: MeasurementType, 
                 dataStore: 'DataStore', 
                 engine: 'MeasurementEngine', 
                 titleStr: str, 
                 initialInstruction: str) -> None:
        self.master: Tk = master
        self.typ: MeasurementType = typ
        self.dataStore: 'DataStore' = dataStore
        self.engine: 'MeasurementEngine' = engine
        self.titleStr: str = titleStr
        self.initialInstruction: str = initialInstruction
        
        self.progressbar: Optional[Progressbar] = None
        self.messWindow: Toplevel
        self.startBtn: Optional[Button] = None
        self.instructionVar: StringVar = StringVar()
        self.isClosed: bool = False 
    
    def buildWindow(self) -> None:
        self.messWindow = Toplevel(self.master)
        self.messWindow.geometry("640x350") # Reduced height since image is gone
        self.messWindow.title(self.titleStr)
        
        self.messWindow.protocol("WM_DELETE_WINDOW", self.onClose)
        self.instructionVar.set(self.initialInstruction)
        
        self.startBtn = Button(self.messWindow, 
                                 text="Start Measurement", 
                                 command=self.startMeasurement, 
                                 pady=10, padx=10)
        self.startBtn.pack(anchor=CENTER, pady=(10, 0))
        
        self.progressbar = Progressbar(self.messWindow, 
                                      orient=HORIZONTAL, 
                                      length=300, 
                                      mode='determinate')
        self.progressbar.pack(pady=10, padx=10)
        self.progressbar['value'] = 0
        
        instrFrame: Frame = Frame(self.messWindow, bg='white', relief=SUNKEN, bd=2)
        instrFrame.pack(fill=X, padx=20, pady=10)
        
        Label(instrFrame, text="Instruction", font=('Arial', 24, 'bold'), fg='green', bg='white').pack(pady=(10, 0))
        Label(instrFrame, textvariable=self.instructionVar, font=('Arial', 16), fg='black', bg='white', wraplength=600).pack(pady=10, padx=20)

    def onClose(self) -> None:
        self.isClosed = True         
        self.engine.stopStream()      
        self.engine.closeStream()
        self.messWindow.destroy() 

    def buildAndOpenWindow(self) -> None:
        self.buildWindow()

    def progressTheBar(self, percentIncr: float) -> None:
        if self.progressbar and not self.isClosed:
            self.progressbar['value'] += percentIncr
            self.messWindow.update_idletasks()

    def updateInstruction(self, text: str) -> None:
        if not self.isClosed:
            self.instructionVar.set(text)
            self.messWindow.update()

    def handleSaveAndPlot(self, bufferStr: str) -> None:
        # If the window was closed mid-measurement, don't bother saving broken data
        if self.isClosed: return 

        if not bufferStr:
            messagebox.showerror("Error", "No data was recorded.")
            return

        data: List[Tuple[float, float, float, float, float, float, float]] = FileHandler.parseData(bufferStr)
        if messagebox.askyesno("Print Data", "Would you like to plot the data before saving?"):
            plotWindow: StoredDataPlot = StoredDataPlot(self.master, data, "Temp Memory View")
            plotWindow.buildAndOpenWindow()

        FileHandler.saveData(self.typ, bufferStr, self.dataStore.participantName, self.dataStore.defaultSaveDir)

    def startMeasurement(self) -> None:
        raise NotImplementedError()

# ==========================================================
# Static Hold Measurements (runSteadyRoutine)
# ==========================================================

class SteadyMeasurementWindow(BaseMeasurementWindow):
    def __init__(self, master: Tk, dataStore: 'DataStore', engine: 'MeasurementEngine') -> None:
        super().__init__(master, 
                         MeasurementType.Steady, 
                         dataStore, engine, 
                         "Static Baseline", 
                         "Keep your Arm relaxed in the resting position.")
        
    def startMeasurement(self) -> None:
        if self.progressbar and self.startBtn:
            self.progressbar['value'] = 0
            self.startBtn.config(state="disabled")
            bufferStr: str = self.engine.runSteadyRoutine(self)
            self.handleSaveAndPlot(bufferStr)
            self.startBtn.config(state="normal")

class ContractionBicepsMeasurementWindow(BaseMeasurementWindow):
    def __init__(self, master: Tk, dataStore: 'DataStore', engine: 'MeasurementEngine') -> None:
        super().__init__(master, 
                         MeasurementType.ContractionBiceps, 
                         dataStore, engine, 
                         "Isometric Contraction: Biceps", 
                         "Contract your BICEPS strongly without moving the arm.")

    def startMeasurement(self) -> None:
        if self.progressbar and self.startBtn:
            self.progressbar['value'] = 0
            self.startBtn.config(state="disabled")
            bufferStr: str = self.engine.runSteadyRoutine(self)
            self.handleSaveAndPlot(bufferStr)
            self.startBtn.config(state="normal")

class ContractionTricepsMeasurementWindow(BaseMeasurementWindow):
    def __init__(self, master: Tk, dataStore: 'DataStore', engine: 'MeasurementEngine') -> None:
        super().__init__(master, 
                         MeasurementType.ContractionTriceps, 
                         dataStore, engine, 
                         "Isometric Contraction: Triceps", 
                         "Contract your TRICEPS strongly without moving the arm.")

    def startMeasurement(self) -> None:
        if self.progressbar and self.startBtn:
            self.progressbar['value'] = 0
            self.startBtn.config(state="disabled")
            bufferStr: str = self.engine.runSteadyRoutine(self)
            self.handleSaveAndPlot(bufferStr)
            self.startBtn.config(state="normal")
            
# ==========================================================
# Parameterized Repetitive Measurements
# ==========================================================

class FastUpMeasurementWindow(BaseMeasurementWindow):
    def __init__(self, master: Tk, dataStore: 'DataStore', engine: 'MeasurementEngine') -> None:
        super().__init__(master, 
                         MeasurementType.FastUp, 
                         dataStore, engine, 
                         "Dynamic: Fast Upward Motion", 
                         "Perform 10 rapid upward lifts (concentric action).\nLower weight slowly between reps.")

    def startMeasurement(self) -> None:
        if self.progressbar and self.startBtn:
            self.progressbar['value'] = 0
            self.startBtn.config(state="disabled")
            # 10 reps, 1.0s action (fast lift), 2.5s pause (slow lower)
            bufferStr: str = self.engine.runRepetitiveRoutine(self, 10, 1.0, 2.5, 
                                                             "LIFT FAST!", 
                                                             "Lower weight slowly.",
                                                              1.0)
            self.handleSaveAndPlot(bufferStr)
            self.startBtn.config(state="normal")

class SlowUpMeasurementWindow(BaseMeasurementWindow):
    def __init__(self, master: Tk, dataStore: 'DataStore', engine: 'MeasurementEngine') -> None:
        super().__init__(master, 
                         MeasurementType.SlowUp, 
                         dataStore, engine, 
                         "Dynamic: Slow Upward Motion", 
                         "Perform 10 slow, controlled upward lifts.\nLower weight moderately between reps.")

    def startMeasurement(self) -> None:
        if self.progressbar and self.startBtn:
            self.progressbar['value'] = 0
            self.startBtn.config(state="disabled")
            # 10 reps, 4.0s action (slow lift), 2.0s pause (moderate lower)
            bufferStr: str = self.engine.runRepetitiveRoutine(self, 10, 4.0, 2.0, 
                                                             "Lift SLOWLY...", 
                                                             "Lower weight.",
                                                             1.0)
            self.handleSaveAndPlot(bufferStr)
            self.startBtn.config(state="normal")

class FastDownMeasurementWindow(BaseMeasurementWindow):
    def __init__(self, master: Tk, dataStore: 'DataStore', engine: 'MeasurementEngine') -> None:
        super().__init__(master, 
                         MeasurementType.FastDown, 
                         dataStore, engine, 
                         "Dynamic: Fast Downward Motion", 
                         "Perform 10 rapid drops (eccentric action).\nLift weight slowly back to start position.")

    def startMeasurement(self) -> None:
        if self.progressbar and self.startBtn:
            self.progressbar['value'] = 0
            self.startBtn.config(state="disabled")
            # 10 reps, 1.0s action (fast drop), 3.0s pause (lift back up)
            bufferStr: str = self.engine.runRepetitiveRoutine(self, 10, 1.0, 3.0, 
                                                             "DROP FAST!", 
                                                             "Lift weight back to top position slowly.",
                                                             1.0)
            self.handleSaveAndPlot(bufferStr)
            self.startBtn.config(state="normal")

class SlowDownMeasurementWindow(BaseMeasurementWindow):
    def __init__(self, master: Tk, dataStore: 'DataStore', engine: 'MeasurementEngine') -> None:
        super().__init__(master, 
                         MeasurementType.SlowDown, 
                         dataStore, engine, 
                         "Dynamic: Slow Downward Motion", 
                         "Perform 10 slow, controlled lowerings.\nLift weight moderately between reps.")

    def startMeasurement(self) -> None:
        if self.progressbar and self.startBtn:
            self.progressbar['value'] = 0
            self.startBtn.config(state="disabled")
            # 10 reps, 4.0s action (slow drop), 2.0s pause (lift moderate)
            bufferStr: str = self.engine.runRepetitiveRoutine(self, 10, 4.0, 2.0, 
                                                             "Lower SLOWLY...", 
                                                             "Lift weight back to top.",
                                                             1.0)
            self.handleSaveAndPlot(bufferStr)
            self.startBtn.config(state="normal")