from tkinter import *
from tkinter import messagebox, filedialog
from tkinter.ttk import Notebook, Combobox
import os
from typing import List, Any, Optional, Tuple  # <-- Tuple added here
from DataStore import DataStore
from SerialManager import SerialManager
from MeasurementEngine import MeasurementEngine
from FileHandler import FileHandler
from MeasurementWindows import *
from Plotting import RealTimePlot, StoredDataPlot

class MainWindow:
    def __init__(self, root: Tk, dataStore: DataStore, serialMgr: SerialManager, engine: MeasurementEngine) -> None:
        self.root: Tk = root
        self.dataStore: DataStore = dataStore
        self.serialMgr: SerialManager = serialMgr
        self.engine: MeasurementEngine = engine

        self.root.geometry("640x600") 
        self.root.title("EMG Measurement and Analysis Tool")

        self.tabContainer: Notebook = Notebook(self.root)
        self.messTab: Frame = Frame(self.tabContainer)
        self.anaTab: Frame = Frame(self.tabContainer)
        
        self.tabContainer.add(self.messTab, text="Measurement")
        self.tabContainer.add(self.anaTab, text="Analysis")
        self.tabContainer.pack(expand=True, fill=BOTH)

        self.patFieldVar: StringVar = StringVar()
        self.patFieldVar.trace_add("write", lambda *args: self.dataStore.setParticipant(self.patFieldVar.get()))

        self.analysisFileVars: List[StringVar] = []
        self.analysisFullPaths: List[str] = []
        
        self.configButtons: List[Button] = []

        self.buildMeasurementTab()
        self.buildAnalysisTab()

    def buildMeasurementTab(self) -> None:
        mainFrame: Frame = Frame(self.messTab, padx=10, pady=10)
        mainFrame.pack(fill="both", expand=True)

        configFrame: Frame = LabelFrame(mainFrame, text="Hardware Configuration", padx=5, pady=5)
        configFrame.pack(fill=X, pady=(0, 10))

        Label(configFrame, text="Comport").grid(row=0, column=0, sticky="w")
        self.comCombo: Combobox = Combobox(configFrame, values=self.dataStore.getAvailablePorts(), width=40, state="normal")
        self.comCombo.grid(row=1, column=0, sticky="w")
        self.comCombo.bind("<<ComboboxSelected>>", self.onConfigChanged)
       
        Label(configFrame, text="BaudRate").grid(row=0, column=1, sticky="w", padx=20)
        self.baudCombo: Combobox = Combobox(configFrame, values=self.dataStore.baudrateList, width=15, state="normal")
        self.baudCombo.grid(row=1, column=1, padx=20, sticky="w")
        self.baudCombo.bind("<<ComboboxSelected>>", self.onConfigChanged)
        self.baudCombo.set(str(self.dataStore.selectedBaudrate))

        patFrame: Frame = Frame(mainFrame)
        patFrame.pack(fill=X, pady=10)
        Label(patFrame, text="Participant Name:", font=('TkDefaultFont', 12)).pack(side=LEFT)
        Entry(patFrame, textvariable=self.patFieldVar, width=40).pack(side=LEFT, padx=10)

        actionsFrame: LabelFrame = LabelFrame(mainFrame, text="Measurement Actions", padx=10, pady=10)
        actionsFrame.pack(fill=BOTH, expand=True)
        
        gridFrame: Frame = Frame(actionsFrame)
        gridFrame.pack(anchor=CENTER)

        self.createMeasurementRow(gridFrame, 0, "Realtime Monitor (No Save)", self.startRealtime, font=('Arial', 12, 'bold'))
        self.createMeasurementRow(gridFrame, 1, "Baseline (Relaxed)", self.startSteady)
        self.createMeasurementRow(gridFrame, 2, "Isometric Contraction: Biceps", self.startContractionBiceps)
        self.createMeasurementRow(gridFrame, 3, "Isometric Contraction: Triceps", self.startContractionTriceps)
        self.createMeasurementRow(gridFrame, 4, "Concentric: Fast Up", self.startFastUp)
        self.createMeasurementRow(gridFrame, 5, "Concentric: Slow Up", self.startSlowUp)
        self.createMeasurementRow(gridFrame, 6, "Eccentric: Fast Down", self.startFastDown)
        self.createMeasurementRow(gridFrame, 7, "Eccentric: Slow Down", self.startSlowDown)

    def createMeasurementRow(self, parent: Frame, row: int, labelTxt: str, commandFunc: Any, font: Tuple[str, int, str] = ('Arial', 12)) -> None:
        Label(parent, text=labelTxt, font=font).grid(row=row, column=0, sticky="w", pady=5)
        btn: Button = Button(parent, text="Launch", width=12, command=commandFunc, state="disabled")
        btn.grid(row=row, column=1, sticky="w", padx=20, pady=5)
        self.configButtons.append(btn)

    def onConfigChanged(self, event: Any = None) -> None:
        self.dataStore.setPort(self.comCombo.get())
        self.dataStore.setBaudrate(self.baudCombo.get())
        
        state: str = "normal" if self.dataStore.selectedPort and self.dataStore.selectedBaudrate else "disabled"
        for btn in self.configButtons:
            btn.config(state=state)

    def establishConnection(self) -> bool:
        if self.serialMgr.isConnected(): 
            return True
            
        success: bool = self.serialMgr.connect(self.dataStore.selectedPort, self.dataStore.selectedBaudrate)
        if not success: 
            messagebox.showwarning("Error", "Could not open Serial Connection.\nCheck port and settings.")
        return success

    def startSteady(self) -> None:
        if self.establishConnection(): SteadyMeasurementWindow(self.root, self.dataStore, self.engine).buildAndOpenWindow()

    def startContractionBiceps(self) -> None:
        if self.establishConnection(): ContractionBicepsMeasurementWindow(self.root, self.dataStore, self.engine).buildAndOpenWindow()

    def startContractionTriceps(self) -> None:
        if self.establishConnection(): ContractionTricepsMeasurementWindow(self.root, self.dataStore, self.engine).buildAndOpenWindow()
    def startFastUp(self) -> None:
        
        if self.establishConnection(): FastUpMeasurementWindow(self.root, self.dataStore, self.engine).buildAndOpenWindow()

    def startSlowUp(self) -> None:
        if self.establishConnection(): SlowUpMeasurementWindow(self.root, self.dataStore, self.engine).buildAndOpenWindow()

    def startFastDown(self) -> None:
        if self.establishConnection(): FastDownMeasurementWindow(self.root, self.dataStore, self.engine).buildAndOpenWindow()

    def startSlowDown(self) -> None:
        if self.establishConnection(): SlowDownMeasurementWindow(self.root, self.dataStore, self.engine).buildAndOpenWindow()

    def startRealtime(self) -> None:
        if self.establishConnection(): RealTimePlot(self.root, self.engine).buildAndOpenWindow()

    def buildAnalysisTab(self) -> None:
        frame: Frame = Frame(self.anaTab, padx=20, pady=20)
        frame.pack(fill="both", expand=True)
        Label(frame, text="Stored Data Analysis", font=('Arial', 16, 'bold')).pack(anchor=W, pady=(0, 15))

        fileFrame: Frame = Frame(frame)
        fileFrame.pack(fill=X)

        for i in range(4):
            row: Frame = Frame(fileFrame, pady=5)
            row.pack(fill=X)
            
            fileVar: StringVar = StringVar()
            self.analysisFileVars.append(fileVar)
            self.analysisFullPaths.append("")

            Entry(row, textvariable=fileVar, width=60).pack(side=LEFT, padx=5)
            Button(row, text="Browse", width=10, command=lambda idx=i: self.browseForFile(idx)).pack(side=LEFT, padx=5)
            Button(row, text="Plot", width=10, command=lambda idx=i: self.plotStoredData(idx)).pack(side=LEFT, padx=5)

    def browseForFile(self, index: int) -> None:
        filePath: str = filedialog.askopenfilename(title="Select stored txt file", filetypes=[("Text Files", "*.txt")])
        if filePath:
            self.analysisFileVars[index].set(os.path.basename(filePath))
            self.analysisFullPaths[index] = filePath

    def plotStoredData(self, index: int) -> None:
        fileName: str = self.analysisFileVars[index].get()
        filePath: str = self.analysisFullPaths[index]
        
        if not filePath:
            messagebox.showwarning("Error", "Please select a file first.")
            return

        try:
            data = FileHandler.loadData(filePath)
            if not data:
                messagebox.showwarning("Error", "File contains no valid data.")
                return
            StoredDataPlot(self.root, data, fileName).buildAndOpenWindow()
        except Exception as e:
            messagebox.showwarning("Error", f"Failed to load file:\n{e}")