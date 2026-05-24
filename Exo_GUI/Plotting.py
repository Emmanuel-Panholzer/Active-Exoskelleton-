from tkinter import *
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from typing import Iterable, List, Tuple, Optional, Union, Any, TYPE_CHECKING
from collections import deque
import math
from Utils import UIDefaults

if TYPE_CHECKING:
    from MeasurementEngine import MeasurementEngine

class BasePlot:
    def __init__(self, master: Tk) -> None:
        self.master: Tk = master
        self.hasServoControls: bool = True
        self.refreshTime: int = UIDefaults.plotRefreshTimeMs
        self.isPlotting: bool = False
        
        self.windowSizeVar: StringVar = StringVar(value=UIDefaults.plotWindowSize)
        self.windowSize: int = int(UIDefaults.plotWindowSize)
        
        # Local Plot Settings
        self.bicIsRolling: IntVar = IntVar(value=UIDefaults.muscleIsRolling) 
        self.triIsRolling: IntVar = IntVar(value=UIDefaults.muscleIsRolling)
        self.bicWinVar: StringVar = StringVar(value=UIDefaults.muscleMavRmsWindow)
        self.triWinVar: StringVar = StringVar(value=UIDefaults.muscleMavRmsWindow)
        
        # Global Simulation & Arduino Settings
        self.simulatedVar: IntVar = IntVar(value=0)
        self.weightVar: StringVar = StringVar(value=UIDefaults.weightFactor)
        self.thresholdVar: StringVar = StringVar(value=UIDefaults.threshold)
        self.speedMultVar: StringVar = StringVar(value=UIDefaults.speedMultiplier)
        self.arduinoWinVar: StringVar = StringVar(value=UIDefaults.arduinoWindow)
        self.arduinoRollingVar: IntVar = IntVar(value=UIDefaults.arduinoRolling)
        
        self.simulatedAngle: float = 90.0
        self.fullSimulatedAngles: List[float] = []
        self.lastSimParams: Optional[Tuple[str, str, str, int]] = None
        
        self.bicNetData: List[float] = []
        self.triNetData: List[float] = []
        
        self.bicEnables: List[IntVar] = [IntVar(value=v) for v in UIDefaults.bicepsEnableDefaults]
        self.triEnables: List[IntVar] = [IntVar(value=v) for v in UIDefaults.tricepsEnableDefaults]

        self.bicModes: List[StringVar] = [StringVar(value="ACTUAL"), StringVar(value="ACTUAL"), StringVar(value="ACTUAL")]
        self.triModes: List[StringVar] = [StringVar(value="ACTUAL"), StringVar(value="ACTUAL"), StringVar(value="ACTUAL")]
        
        self.bicAxisConfigs: List[Tuple[StringVar, StringVar]] = []
        self.triAxisConfigs: List[Tuple[StringVar, StringVar]] = []

        self.xStorage: Optional[Union[List[float], deque]] = None
        self.y1Storage: Optional[Union[List[float], deque]] = None
        self.y2Storage: Optional[Union[List[float], deque]] = None
        self.y3Storage: Optional[Union[List[float], deque]] = None
        self.y4Storage: Optional[Union[List[float], deque]] = None
        self.y5Storage: Optional[Union[List[float], deque]] = None
        self.y6Storage: Optional[Union[List[float], deque]] = None
        self.y7Storage: Optional[Union[List[float], deque]] = None
        self.nrOfSamples: int = 0
        
        self.plotWindow: Optional[Toplevel] = None
        self.windowFrame: Optional[Frame] = None
        self.axisContainer: Optional[Frame] = None
        self.plotFigure: Optional[Figure] = None
        self.plot: Optional[FigureCanvasTkAgg] = None

        self.ax1: Optional[Axes] = None
        self.ax2: Optional[Axes] = None
        self.ax3: Optional[Axes] = None
        self.axNetBic: Optional[Axes] = None
        self.line1: Optional[Line2D] = None
        self.line2: Optional[Line2D] = None
        self.line3: Optional[Line2D] = None
        self.lineNetBic: Optional[Line2D] = None
        
        self.ax4: Optional[Axes] = None
        self.ax5: Optional[Axes] = None
        self.ax6: Optional[Axes] = None
        self.axNetTri: Optional[Axes] = None
        self.line4: Optional[Line2D] = None
        self.line5: Optional[Line2D] = None
        self.line6: Optional[Line2D] = None
        self.lineNetTri: Optional[Line2D] = None

    def initStorageContainers(self) -> None: raise NotImplementedError()
    def addButtons(self, parent: Frame) -> None: raise NotImplementedError()
    def getNextPoints(self) -> List[Tuple[float, float, float, float, float, float, float]]: raise NotImplementedError()
    def updateLines(self) -> None: raise NotImplementedError()

    def onWindowSizeEnter(self, event: Any = None) -> None: self.doPlot()
    def onAxisLimitEnter(self, event: Any = None) -> None: 
        self.updateScale()
        if self.plot: self.plot.draw_idle()
    def onRmsEnter(self, event: Any = None) -> None:
        self.updateLines()
        self.updateScale()
        if self.plot: self.plot.draw_idle()
    def onCheckboxChange(self) -> None:
        self.rebuildPlot()
        if self.xStorage is not None and len(self.xStorage) > 0:
            self.updateLines()
            self.updateScale()
        if self.plot: self.plot.draw_idle()

    def sendParamsToArduino(self) -> None:
        if hasattr(self, 'engine') and self.engine.serialMgr.isConnected():
            try:
                w: float = float(self.weightVar.get())
                t: float = float(self.thresholdVar.get())
                s: float = float(self.speedMultVar.get())
                win: int = int(self.arduinoWinVar.get())
                isRoll: int = self.arduinoRollingVar.get()
                self.engine.serialMgr.sendParameters(w, t, s, win, isRoll)
            except ValueError:
                pass

    def buildAndOpenWindow(self) -> None:
        self.plotWindow = Toplevel(self.master)
        self.plotWindow.geometry("1400x850") 
        self.windowFrame = Frame(self.plotWindow)
        self.windowFrame.pack(fill="both", expand=True)
        
        self.axisContainer = Frame(self.windowFrame)
        self.axisContainer.pack(fill="x", pady=5, padx=5)

        globalFrame = Frame(self.axisContainer)
        globalFrame.pack(fill="x", pady=2)
        Label(globalFrame, text="Plot Window Size:", font=("Arial", 10, "bold")).pack(side=LEFT, padx=(5, 2))
        winSizeEntry = Entry(globalFrame, textvariable=self.windowSizeVar, width=8)
        winSizeEntry.pack(side=LEFT)
        winSizeEntry.bind("<Return>", self.onWindowSizeEnter)

        self.addButtons(globalFrame)

        controlsFrame = Frame(self.axisContainer)
        controlsFrame.pack(fill="x", pady=5)
        
        bicFrame = LabelFrame(controlsFrame, text="Biceps Settings (Top Graph)", fg="blue", font=("Arial", 10, "bold"))
        bicFrame.pack(side=LEFT, fill="both", expand=True, padx=2)
        self.bicAxisConfigs = self.buildMuscleControls(bicFrame, self.bicModes, self.bicEnables, self.bicWinVar, self.bicIsRolling, UIDefaults.bicepsAxisDefaults)
        
        triFrame = LabelFrame(controlsFrame, text="Triceps Settings (Bottom Graph)", fg="red", font=("Arial", 10, "bold"))
        triFrame.pack(side=LEFT, fill="both", expand=True, padx=2)
        self.triAxisConfigs = self.buildMuscleControls(triFrame, self.triModes, self.triEnables, self.triWinVar, self.triIsRolling, UIDefaults.tricepsAxisDefaults)

        displayFrame = Frame(self.windowFrame)
        displayFrame.pack(fill="both", expand=True)
        
        graphFrame = Frame(displayFrame)
        graphFrame.pack(side=LEFT, fill="both", expand=True)
        
        if self.hasServoControls:
            angleFrame = Frame(displayFrame, width=220, relief="sunken", bd=2)
            angleFrame.pack(side=RIGHT, fill="y", padx=5, pady=5)
            
            Label(angleFrame, text="Servo Angle", font=("Arial", 14, "bold")).pack(pady=(10, 5))
            self.angleCanvas = Canvas(angleFrame, width=150, height=150, bg="#f0f0f0", highlightthickness=0)
            self.angleCanvas.pack()
            self.angleCanvas.create_arc(25, 25, 125, 125, start=-90, extent=180, outline="gray", style=ARC, width=4)
            self.angleLine = self.angleCanvas.create_line(75, 75, 125, 75, fill="red", width=5)
            self.angleText = self.angleCanvas.create_text(75, 130, text="90.0°", font=("Arial", 16, "bold"))

            Checkbutton(angleFrame, text="Simulated", variable=self.simulatedVar, font=("Arial", 10, "bold"), command=self.onRmsEnter).pack(pady=(5, 5))
            
            ctrls = Frame(angleFrame)
            ctrls.pack(fill="x", padx=10)

            Label(ctrls, text="Weight Factor:").grid(row=0, column=0, sticky="w", pady=2)
            Entry(ctrls, textvariable=self.weightVar, width=8).grid(row=0, column=1, sticky="e", pady=2)

            Label(ctrls, text="Threshold:").grid(row=1, column=0, sticky="w", pady=2)
            Entry(ctrls, textvariable=self.thresholdVar, width=8).grid(row=1, column=1, sticky="e", pady=2)

            Label(ctrls, text="Speed Mult:").grid(row=2, column=0, sticky="w", pady=2)
            Entry(ctrls, textvariable=self.speedMultVar, width=8).grid(row=2, column=1, sticky="e", pady=2)

            Checkbutton(ctrls, text="Arduino Rolling", variable=self.arduinoRollingVar, font=("Arial", 9, "bold")).grid(row=3, column=0, columnspan=2, sticky="w", pady=(10, 2))
            Label(ctrls, text="Arduino Win:").grid(row=4, column=0, sticky="w", pady=2)
            Entry(ctrls, textvariable=self.arduinoWinVar, width=8).grid(row=4, column=1, sticky="e", pady=2)

            Button(ctrls, text="Send to Exoskeleton", bg="#cce6ff", command=self.sendParamsToArduino).grid(row=5, column=0, columnspan=2, pady=(15, 5), sticky="we")

            for child in ctrls.winfo_children():
                if isinstance(child, Entry):
                    child.bind("<Return>", self.onRmsEnter)

        self.plotFigure = Figure(figsize=(8, 6), dpi=100)
        self.plotFigure.subplots_adjust(left=0.08, right=0.80) 
        self.plot = FigureCanvasTkAgg(self.plotFigure, master=graphFrame)
        self.plot.get_tk_widget().pack(fill="both", expand=True)

        self.rebuildPlot()
        self.plotWindow.after(self.refreshTime, self.updatePlot)

    def buildMuscleControls(self, parent: Frame, modeVars: List[StringVar], enables: List[IntVar], winVar: StringVar, isRollingVar: IntVar, axisDefaultsDict: dict) -> List[Tuple[StringVar, StringVar]]:
        topBar = Frame(parent)
        topBar.pack(fill="x", padx=5, pady=2)

        Label(topBar, text="Enable Lines:").pack(side=LEFT)
        Checkbutton(topBar, text="RAW", variable=enables[0], command=self.onCheckboxChange).pack(side=LEFT)
        Checkbutton(topBar, text="Fil", variable=enables[1], command=self.onCheckboxChange).pack(side=LEFT)
        Checkbutton(topBar, text="Abs", variable=enables[2], command=self.onCheckboxChange).pack(side=LEFT)
        Checkbutton(topBar, text="Net", variable=enables[3], command=self.onCheckboxChange).pack(side=LEFT)
        
        Label(topBar, text="MAV/RMS Window:").pack(side=LEFT, padx=(15, 2))
        winEntry = Entry(topBar, textvariable=winVar, width=5)
        winEntry.pack(side=LEFT)
        winEntry.bind("<Return>", self.onRmsEnter)
        Checkbutton(topBar, text="Rolling Window", variable=isRollingVar, command=self.onRmsEnter).pack(side=LEFT, padx=(5, 0))

        colFrame = Frame(parent)
        colFrame.pack(fill="x")
        
        configs = []
        labels = ["RAW", "Filtered", "Absolute", "Net Force"]
        for i, label in enumerate(labels):
            col = Frame(colFrame, bd=1, relief="sunken", padx=5, pady=5)
            col.pack(side=LEFT, expand=True, fill="x", padx=2, pady=2)

            topRow = Frame(col)
            topRow.pack(fill="x")
            Label(topRow, text=label, font=("Arial", 9, "bold")).pack(side=LEFT)
            
            if label == "Net Force":
                Label(topRow, text=" ").pack(side=RIGHT) 
            else:
                OptionMenu(topRow, modeVars[i], "ACTUAL", "MAV", "RMS", command=self.onRmsEnter).pack(side=RIGHT)

            botRow = Frame(col)
            botRow.pack(fill="x", pady=(5, 0))
            
            # THE FIX: Extract the specific default Min/Max from the dictionary using the label
            defaultMin, defaultMax = axisDefaultsDict.get(label, ("", ""))
            
            minVar = StringVar(value=defaultMin)
            maxVar = StringVar(value=defaultMax)
            
            Label(botRow, text="Min:").pack(side=LEFT)
            minEntry = Entry(botRow, textvariable=minVar, width=5)
            minEntry.pack(side=LEFT)
            minEntry.bind("<Return>", self.onAxisLimitEnter)

            Label(botRow, text="Max:").pack(side=LEFT, padx=(5,0))
            maxEntry = Entry(botRow, textvariable=maxVar, width=5)
            maxEntry.pack(side=LEFT)
            maxEntry.bind("<Return>", self.onAxisLimitEnter)

            configs.append((minVar, maxVar))
        return configs

    def updateAngleVisualizer(self, current_angle: float) -> None:
        rad = math.radians(current_angle - 90)
        x = 75 + 50 * math.cos(rad)
        y = 75 - 50 * math.sin(rad) 
        
        self.angleCanvas.coords(self.angleLine, 75, 75, x, y)
        self.angleCanvas.itemconfig(self.angleText, text=f"{current_angle:.1f}°")

    def doPlot(self) -> None:
        try: self.windowSize = int(self.windowSizeVar.get())
        except ValueError: 
            self.windowSize = 5000
            self.windowSizeVar.set("5000")
        self.rebuildPlot()
        self.initStorageContainers()
        self.isPlotting = True

    def stopPlot(self) -> None: 
        self.isPlotting = False

    def rebuildPlot(self) -> None:
        if not self.plotFigure: return
        self.plotFigure.clear()
        
        self.ax1 = self.plotFigure.add_subplot(211)
        if not self.bicEnables[0].get(): self.ax1.get_yaxis().set_visible(False)
        
        self.ax2 = self.ax1.twinx() if self.bicEnables[1].get() else None
        self.ax3 = self.ax1.twinx() if self.bicEnables[2].get() else None
        self.axNetBic = self.ax1.twinx() if self.bicEnables[3].get() else None
        
        if self.ax3: self.ax3.spines["right"].set_position(("outward", 60))
        if self.axNetBic: self.axNetBic.spines["right"].set_position(("outward", 120))

        self.ax4 = self.plotFigure.add_subplot(212, sharex=self.ax1)
        if not self.triEnables[0].get(): self.ax4.get_yaxis().set_visible(False)
        
        self.ax5 = self.ax4.twinx() if self.triEnables[1].get() else None
        self.ax6 = self.ax4.twinx() if self.triEnables[2].get() else None
        self.axNetTri = self.ax4.twinx() if self.triEnables[3].get() else None
        
        if self.ax6: self.ax6.spines["right"].set_position(("outward", 60))
        if self.axNetTri: self.axNetTri.spines["right"].set_position(("outward", 120))

        if self.bicEnables[0].get():
            self.ax1.set_ylabel("RAW", color="blue", fontweight='bold')
            self.ax1.tick_params(axis='y', colors='blue')
        if self.ax2:
            self.ax2.set_ylabel("Filtered", color="green", fontweight='bold')
            self.ax2.tick_params(axis='y', colors='green')
        if self.ax3:
            self.ax3.set_ylabel("Absolute", color="red", fontweight='bold')
            self.ax3.tick_params(axis='y', colors='red')
        if self.axNetBic:
            self.axNetBic.set_ylabel("Net Force", color="magenta", fontweight='bold')
            self.axNetBic.tick_params(axis='y', colors='magenta')

        if self.triEnables[0].get():
            self.ax4.set_ylabel("RAW", color="blue", fontweight='bold')
            self.ax4.tick_params(axis='y', colors='blue')
        if self.ax5:
            self.ax5.set_ylabel("Filtered", color="green", fontweight='bold')
            self.ax5.tick_params(axis='y', colors='green')
        if self.ax6:
            self.ax6.set_ylabel("Absolute", color="red", fontweight='bold')
            self.ax6.tick_params(axis='y', colors='red')
        if self.axNetTri:
            self.axNetTri.set_ylabel("Net Force", color="magenta", fontweight='bold')
            self.axNetTri.tick_params(axis='y', colors='magenta')

        self.line1 = self.ax1.plot([], [], lw=2, color="blue", label="RAW")[0]
        self.line2 = self.ax2.plot([], [], lw=2, color="green", label="Filtered")[0] if self.ax2 else None
        self.line3 = self.ax3.plot([], [], lw=2, color="red", label="Absolute")[0] if self.ax3 else None
        self.lineNetBic = self.axNetBic.plot([], [], lw=2, color="magenta", label="Net Force")[0] if self.axNetBic else None

        self.line4 = self.ax4.plot([], [], lw=2, color="blue", label="RAW")[0]
        self.line5 = self.ax5.plot([], [], lw=2, color="green", label="Filtered")[0] if self.ax5 else None
        self.line6 = self.ax6.plot([], [], lw=2, color="red", label="Absolute")[0] if self.ax6 else None
        self.lineNetTri = self.axNetTri.plot([], [], lw=2, color="magenta", label="Net Force")[0] if self.axNetTri else None

        self.ax1.set_title("Biceps Activity")
        self.ax4.set_title("Triceps Activity")
        self.ax4.set_xlabel("Sample Index")

        linesBic: List[Line2D] = [l for l in [self.line1 if self.bicEnables[0].get() else None, self.line2, self.line3, self.lineNetBic] if l]
        if linesBic: self.ax1.legend(linesBic, [l.get_label() for l in linesBic], loc='upper left', fontsize='small')

        self.cursorLineBic = self.ax1.axvline(x=0, color='gray', linestyle='--', alpha=0.8, visible=False)
        self.cursorLineTri = self.ax4.axvline(x=0, color='gray', linestyle='--', alpha=0.8, visible=False)
        self.cursorTextBic = self.ax1.text(0.02, 0.70, '', transform=self.ax1.transAxes, bbox=dict(facecolor='white', alpha=0.9, edgecolor='gray'), verticalalignment='top', visible=False)
        self.cursorTextTri = self.ax4.text(0.02, 0.85, '', transform=self.ax4.transAxes, bbox=dict(facecolor='white', alpha=0.9, edgecolor='gray'), verticalalignment='top', visible=False)

        if self.plot:
            self.plot.mpl_connect("motion_notify_event", self.onMouseHover)
            self.plot.mpl_connect("axes_leave_event", self.hideCursor)

        if self.plot: self.plot.draw()

    def onMouseHover(self, event: Any) -> None:
        if not event.inaxes or event.xdata is None:
            self.hideCursor()
            return

        activeLine = None
        if self.bicEnables[0].get() and getattr(self, 'line1', None): activeLine = self.line1
        elif self.bicEnables[1].get() and getattr(self, 'line2', None): activeLine = self.line2
        elif self.bicEnables[2].get() and getattr(self, 'line3', None): activeLine = self.line3
        elif self.bicEnables[3].get() and getattr(self, 'lineNetBic', None): activeLine = self.lineNetBic
        elif self.triEnables[0].get() and getattr(self, 'line4', None): activeLine = self.line4

        if not activeLine: return
        xs = activeLine.get_xdata()
        if len(xs) == 0: return

        idx = min(range(len(xs)), key=lambda i: abs(xs[i] - event.xdata))
        actualX = xs[idx]

        self.cursorLineBic.set_xdata([actualX, actualX])
        self.cursorLineBic.set_visible(True)
        self.cursorLineTri.set_xdata([actualX, actualX])
        self.cursorLineTri.set_visible(True)

        tBic = [f"Sample: {int(actualX)}"]
        if self.bicEnables[0].get() and getattr(self, 'line1', None) and len(self.line1.get_ydata()) > idx: tBic.append(f"RAW: {self.line1.get_ydata()[idx]:.3f}")
        if self.bicEnables[1].get() and getattr(self, 'line2', None) and len(self.line2.get_ydata()) > idx: tBic.append(f"Fil: {self.line2.get_ydata()[idx]:.3f}")
        if self.bicEnables[2].get() and getattr(self, 'line3', None) and len(self.line3.get_ydata()) > idx: tBic.append(f"Abs: {self.line3.get_ydata()[idx]:.3f}")
        if self.bicEnables[3].get() and getattr(self, 'lineNetBic', None) and len(self.lineNetBic.get_ydata()) > idx: tBic.append(f"Net: {self.lineNetBic.get_ydata()[idx]:.3f}")
        self.cursorTextBic.set_text("\n".join(tBic))
        self.cursorTextBic.set_visible(True)

        tTri = [f"Sample: {int(actualX)}"]
        if self.triEnables[0].get() and getattr(self, 'line4', None) and len(self.line4.get_ydata()) > idx: tTri.append(f"RAW: {self.line4.get_ydata()[idx]:.3f}")
        if self.triEnables[1].get() and getattr(self, 'line5', None) and len(self.line5.get_ydata()) > idx: tTri.append(f"Fil: {self.line5.get_ydata()[idx]:.3f}")
        if self.triEnables[2].get() and getattr(self, 'line6', None) and len(self.line6.get_ydata()) > idx: tTri.append(f"Abs: {self.line6.get_ydata()[idx]:.3f}")
        if self.triEnables[3].get() and getattr(self, 'lineNetTri', None) and len(self.lineNetTri.get_ydata()) > idx: tTri.append(f"Net: {self.lineNetTri.get_ydata()[idx]:.3f}")
        self.cursorTextTri.set_text("\n".join(tTri))
        self.cursorTextTri.set_visible(True)

        if self.plot: self.plot.draw_idle()

    def hideCursor(self, event: Any = None) -> None:
        if getattr(self, 'cursorLineBic', None):
            self.cursorLineBic.set_visible(False)
            self.cursorLineTri.set_visible(False)
            self.cursorTextBic.set_visible(False)
            self.cursorTextTri.set_visible(False)
            if self.plot: self.plot.draw_idle()

    def updatePlot(self) -> None:
        if not self.plotWindow or not self.plotWindow.winfo_exists():
            return
            
        if self.isPlotting and self.xStorage is not None:
            points = self.getNextPoints()
            for y1, y2, y3, y4, y5, y6, y7 in points:
                self.xStorage.append(float(self.nrOfSamples))
                self.y1Storage.append(y1)
                self.y2Storage.append(y2)
                self.y3Storage.append(y3)
                self.y4Storage.append(y4)
                self.y5Storage.append(y5)
                self.y6Storage.append(y6)
                self.y7Storage.append(y7)
                self.nrOfSamples += 1
            
            self.updateLines()
            self.updateScale()
                
            if self.plot: self.plot.draw()
            
        self.plotWindow.after(self.refreshTime, self.updatePlot)

    def updateScale(self) -> None:
        if self.bicEnables[0].get() and self.ax1 and self.y1Storage:
            self.applyAxisScale(0, self.ax1, self.y1Storage, self.bicAxisConfigs)
        if self.bicEnables[1].get() and self.ax2 and self.y2Storage:
            self.applyAxisScale(1, self.ax2, self.y2Storage, self.bicAxisConfigs)
        if self.bicEnables[2].get() and self.ax3 and self.y3Storage:
            self.applyAxisScale(2, self.ax3, self.y3Storage, self.bicAxisConfigs)
        if self.bicEnables[3].get() and getattr(self, 'axNetBic', None) and getattr(self, 'bicNetData', None):
            self.applyAxisScale(3, self.axNetBic, self.bicNetData, self.bicAxisConfigs)
            
        if self.triEnables[0].get() and self.ax4 and self.y4Storage:
            self.applyAxisScale(0, self.ax4, self.y4Storage, self.triAxisConfigs)
        if self.triEnables[1].get() and self.ax5 and self.y5Storage:
            self.applyAxisScale(1, self.ax5, self.y5Storage, self.triAxisConfigs)
        if self.triEnables[2].get() and self.ax6 and self.y6Storage:
            self.applyAxisScale(2, self.ax6, self.y6Storage, self.triAxisConfigs)
        if self.triEnables[3].get() and getattr(self, 'axNetTri', None) and getattr(self, 'triNetData', None):
            self.applyAxisScale(3, self.axNetTri, self.triNetData, self.triAxisConfigs)

    def applyAxisScale(self, idx: int, axis: Axes, data: Iterable[float], configs: List[Tuple[StringVar, StringVar]]) -> None:
        dataList: List[float] = list(data)
        if not dataList: return
        try:
            mnEntry: str = configs[idx][0].get()
            mxEntry: str = configs[idx][1].get()
            low: float = float(mnEntry) if mnEntry else min(dataList)
            hig: float = float(mxEntry) if mxEntry else max(dataList)
            if low == hig: low, hig = low - 0.1, hig + 0.1
            axis.set_ylim(low, hig)
        except (ValueError, TypeError): 
            axis.set_ylim(min(dataList), max(dataList))
    
    def calculateRMS(self, data: List[float], windowSize: int, isRolling: bool) -> List[float]:
        if not data: return []
        rmsValues: List[float] = [0.0] * len(data)
        
        if isRolling:
            sumSq: float = 0.0
            for i, val in enumerate(data):
                sumSq += float(val) ** 2
                if i >= windowSize: sumSq = max(0.0, sumSq - (float(data[i - windowSize]) ** 2))
                rmsValues[i] = math.sqrt(sumSq / min(i + 1, windowSize))
        else:
            for i in range(0, len(data), windowSize):
                chunk = data[i:i+windowSize]
                val = math.sqrt(sum(float(v) ** 2 for v in chunk) / len(chunk))
                for j in range(i, i + len(chunk)):
                    rmsValues[j] = val

        return rmsValues
    
    def calculateMAV(self, data: List[float], windowSize: int, isRolling: bool) -> List[float]:
        if not data: return []
        mavValues: List[float] = [0.0] * len(data)
        
        if isRolling:
            sumAbs: float = 0.0
            for i, val in enumerate(data):
                sumAbs += abs(float(val))
                if i >= windowSize: sumAbs = max(0.0, sumAbs - abs(float(data[i - windowSize])))
                mavValues[i] = sumAbs / min(i + 1, windowSize)
        else:
            for i in range(0, len(data), windowSize):
                chunk = data[i:i+windowSize]
                val = sum(abs(float(v)) for v in chunk) / len(chunk)
                for j in range(i, i + len(chunk)):
                    mavValues[j] = val

        return mavValues

    def calculateNetForce(self, bicMav: List[float], triMav: List[float], weight: float) -> List[float]:
        return [b - (t * weight) for b, t in zip(bicMav, triMav)]


class RealTimePlot(BasePlot):
    def __init__(self, master: Tk, engine: 'MeasurementEngine') -> None:
        super().__init__(master)
        self.engine: 'MeasurementEngine' = engine
        self.initStorageContainers()

    def buildAndOpenWindow(self) -> None:
        super().buildAndOpenWindow()
        self.plotWindow.protocol("WM_DELETE_WINDOW", self.onClose)

    def onClose(self) -> None:
        self.isPlotting = False 
        try:
            self.engine.stopStream()
        except Exception:
            pass
        if self.plotWindow:
            self.plotWindow.destroy()
            self.plotWindow = None

    def addButtons(self, parent: Frame) -> None:
        Button(parent, text="Start Stream", bg="#a4eab1", command=self.doPlot).pack(side=LEFT, padx=10)
        Button(parent, text="Stop Stream", bg="#ffb3b3", command=self.stopPlot).pack(side=LEFT)

    def doPlot(self) -> None:
        super().doPlot()
        self.simulatedAngle = 90.0
        self.engine.startStream()
        
    def stopPlot(self) -> None: 
        super().stopPlot()
        self.engine.stopStream()

    def initStorageContainers(self) -> None:
        self.xStorage = deque(maxlen=self.windowSize)
        self.y1Storage = deque(maxlen=self.windowSize)
        self.y2Storage = deque(maxlen=self.windowSize)
        self.y3Storage = deque(maxlen=self.windowSize)
        self.y4Storage = deque(maxlen=self.windowSize)
        self.y5Storage = deque(maxlen=self.windowSize)
        self.y6Storage = deque(maxlen=self.windowSize)
        self.y7Storage = deque(maxlen=self.windowSize)
        self.nrOfSamples = 0

    def getNextPoints(self) -> List[Tuple[float, float, float, float, float, float, float]]:
        return self.engine.getRealtimeChunk()

    def updateLines(self) -> None:
        if self.xStorage is None: return
        xs: List[float] = list(self.xStorage)
        
        bicWinStr = self.bicWinVar.get()
        triWinStr = self.triWinVar.get()
        bicWin = int(bicWinStr) if bicWinStr.isdigit() else 50
        triWin = int(triWinStr) if triWinStr.isdigit() else 50
        
        def getProc(storage: deque, mode: StringVar, win: int, isRolling: bool) -> List[float]: 
            data = list(storage)
            if mode.get() == "RMS": 
                return self.calculateRMS(data, win, isRolling)
            elif mode.get() == "MAV": 
                return self.calculateMAV(data, win, isRolling)
            return data

        if self.bicEnables[0].get() and getattr(self, 'line1', None): 
            self.line1.set_data(xs, getProc(self.y1Storage, self.bicModes[0], bicWin, bool(self.bicIsRolling.get())))
        if self.bicEnables[1].get() and getattr(self, 'line2', None): 
            self.line2.set_data(xs, getProc(self.y2Storage, self.bicModes[1], bicWin, bool(self.bicIsRolling.get())))
        if self.bicEnables[2].get() and getattr(self, 'line3', None): 
            self.line3.set_data(xs, getProc(self.y3Storage, self.bicModes[2], bicWin, bool(self.bicIsRolling.get())))
            
        if self.triEnables[0].get() and getattr(self, 'line4', None): 
            self.line4.set_data(xs, getProc(self.y4Storage, self.triModes[0], triWin, bool(self.triIsRolling.get())))
        if self.triEnables[1].get() and getattr(self, 'line5', None): 
            self.line5.set_data(xs, getProc(self.y5Storage, self.triModes[1], triWin, bool(self.triIsRolling.get())))
        if self.triEnables[2].get() and getattr(self, 'line6', None): 
            self.line6.set_data(xs, getProc(self.y6Storage, self.triModes[2], triWin, bool(self.triIsRolling.get())))

        if self.bicEnables[3].get() or self.triEnables[3].get() or self.simulatedVar.get():
            try: globalWeight: float = float(self.weightVar.get())
            except ValueError: globalWeight = 1.0

            bicMavData: List[float] = self.calculateMAV(list(self.y3Storage), bicWin, bool(self.bicIsRolling.get()))
            triMavData: List[float] = self.calculateMAV(list(self.y6Storage), triWin, bool(self.triIsRolling.get()))
            
            netForceData: List[float] = self.calculateNetForce(bicMavData, triMavData, globalWeight)

            if self.bicEnables[3].get() and getattr(self, 'lineNetBic', None):
                self.bicNetData = netForceData
                self.lineNetBic.set_data(xs, self.bicNetData)

            if self.triEnables[3].get() and getattr(self, 'lineNetTri', None):
                self.triNetData = netForceData
                self.lineNetTri.set_data(xs, self.triNetData)

            if self.simulatedVar.get():
                try: speed: float = float(self.speedMultVar.get())
                except ValueError: speed = 0.01
                try: thresh: float = float(self.thresholdVar.get())
                except ValueError: thresh = 40.0

                if len(netForceData) > 0:
                    latestForce: float = netForceData[-1]
                    if abs(latestForce) > thresh:
                        self.simulatedAngle += latestForce * speed
                        self.simulatedAngle = max(0.0, min(180.0, self.simulatedAngle))
                self.updateAngleVisualizer(self.simulatedAngle)
            else:
                if len(self.y7Storage) > 0:
                    self.updateAngleVisualizer(self.y7Storage[-1])
        else:
            if not self.simulatedVar.get() and len(self.y7Storage) > 0:
                self.updateAngleVisualizer(self.y7Storage[-1])
        
        if xs and getattr(self, 'ax1', None): self.ax1.set_xlim(xs[0], xs[-1])


class StoredDataPlot(BasePlot):
    def __init__(self, master: Tk, data: List[Tuple[float, float, float, float, float, float, float]], fileName: str) -> None:
        super().__init__(master)
        self.hasServoControls = False
        self.data = data
        self.fileName: str = fileName
        self.lastBicRmsWindow: int = -1
        self.lastTriRmsWindow: int = -1
        
        self.initStorageContainers()
        for y1, y2, y3, y4, y5, y6, y7 in self.data:
            if isinstance(self.xStorage, list):
                self.xStorage.append(float(self.nrOfSamples))
                self.y1Storage.append(y1)
                self.y2Storage.append(y2)
                self.y3Storage.append(y3)
                self.y4Storage.append(y4)
                self.y5Storage.append(y5)
                self.y6Storage.append(y6)
                self.y7Storage.append(y7)
                self.nrOfSamples += 1
                
        self.viewStart: int = 0
        self.viewSize: int = len(self.data)
        self.windowSizeVar.set(str(self.viewSize))
        self.scrollbar: Optional[Scrollbar] = None

    def initStorageContainers(self) -> None:
        self.xStorage, self.y1Storage, self.y2Storage, self.y3Storage = [], [], [], []
        self.y4Storage, self.y5Storage, self.y6Storage, self.y7Storage = [], [], [], []
        self.nrOfSamples = 0
        
    def getNextPoints(self) -> List[Tuple[float, float, float, float, float, float, float]]: 
        return []

    def buildAndOpenWindow(self) -> None:
        super().buildAndOpenWindow()
        
        fileFrame = Frame(self.axisContainer)
        fileFrame.pack(fill="x", pady=(5, 2))
        Label(fileFrame, text="Viewing File:").pack(side=LEFT)
        fileEntry = Entry(fileFrame, width=70)
        fileEntry.insert(0, self.fileName)
        fileEntry.config(state='readonly')
        fileEntry.pack(side=LEFT, fill="x", expand=True, padx=5)

        self.scrollbar = Scrollbar(self.windowFrame, orient=HORIZONTAL, command=self.onScroll)
        self.scrollbar.pack(fill="x")
        self.updateScrollbar()
        self.doPlot()

    def addButtons(self, parent: Frame) -> None: 
        Button(parent, text="Update Data View", bg="#cce6ff", command=self.doPlot).pack(side=LEFT, padx=10)

    def doPlot(self) -> None:
        try: self.viewSize = max(1, min(int(self.windowSizeVar.get()), len(self.data)))
        except ValueError: self.viewSize = 5000
        self.windowSizeVar.set(str(self.viewSize))
        self.rebuildPlot()
        self.updateLines()
        self.updateScale()
        self.updateScrollbar()
        if self.plot: self.plot.draw()

    def updatePlot(self) -> None: pass

    def updateLines(self) -> None:
        if not isinstance(self.xStorage, list): return
        endIdx: int = self.viewStart + self.viewSize
        xs: List[float] = self.xStorage[self.viewStart:endIdx]
        
        bicWinStr = self.bicWinVar.get()
        triWinStr = self.triWinVar.get()
        bicWin = int(bicWinStr) if bicWinStr.isdigit() else 50
        triWin = int(triWinStr) if triWinStr.isdigit() else 50

        currentBicRolling = bool(self.bicIsRolling.get())
        currentTriRolling = bool(self.triIsRolling.get())

        recalcBic = (self.lastBicRmsWindow != bicWin) or (getattr(self, 'lastBicRolling', None) != currentBicRolling)
        recalcTri = (self.lastTriRmsWindow != triWin) or (getattr(self, 'lastTriRolling', None) != currentTriRolling)

        if recalcBic:
            self.fR1 = self.calculateRMS(self.y1Storage, bicWin, currentBicRolling)
            self.fR2 = self.calculateRMS(self.y2Storage, bicWin, currentBicRolling)
            self.fR3 = self.calculateRMS(self.y3Storage, bicWin, currentBicRolling)
            self.fM1 = self.calculateMAV(self.y1Storage, bicWin, currentBicRolling)
            self.fM2 = self.calculateMAV(self.y2Storage, bicWin, currentBicRolling)
            self.fM3 = self.calculateMAV(self.y3Storage, bicWin, currentBicRolling)
            self.lastBicRmsWindow = bicWin
            self.lastBicRolling = currentBicRolling
            
        if recalcTri:
            self.fR4 = self.calculateRMS(self.y4Storage, triWin, currentTriRolling)
            self.fR5 = self.calculateRMS(self.y5Storage, triWin, currentTriRolling)
            self.fR6 = self.calculateRMS(self.y6Storage, triWin, currentTriRolling)
            self.fM4 = self.calculateMAV(self.y4Storage, triWin, currentTriRolling)
            self.fM5 = self.calculateMAV(self.y5Storage, triWin, currentTriRolling)
            self.fM6 = self.calculateMAV(self.y6Storage, triWin, currentTriRolling)
            self.lastTriRmsWindow = triWin
            self.lastTriRolling = currentTriRolling
        
        def proc(fRaw: List[float], fRms: List[float], fMav: List[float], mode: StringVar) -> List[float]: 
            if mode.get() == "RMS": return fRms[self.viewStart:endIdx]
            elif mode.get() == "MAV": return fMav[self.viewStart:endIdx]
            return fRaw[self.viewStart:endIdx]

        if self.bicEnables[0].get() and getattr(self, 'line1', None): 
            self.line1.set_data(xs, proc(self.y1Storage, self.fR1, self.fM1, self.bicModes[0]))
        if self.bicEnables[1].get() and getattr(self, 'line2', None): 
            self.line2.set_data(xs, proc(self.y2Storage, self.fR2, self.fM2, self.bicModes[1]))
        if self.bicEnables[2].get() and getattr(self, 'line3', None): 
            self.line3.set_data(xs, proc(self.y3Storage, self.fR3, self.fM3, self.bicModes[2]))
            
        if self.triEnables[0].get() and getattr(self, 'line4', None): 
            self.line4.set_data(xs, proc(self.y4Storage, self.fR4, self.fM4, self.triModes[0]))
        if self.triEnables[1].get() and getattr(self, 'line5', None): 
            self.line5.set_data(xs, proc(self.y5Storage, self.fR5, self.fM5, self.triModes[1]))
        if self.triEnables[2].get() and getattr(self, 'line6', None): 
            self.line6.set_data(xs, proc(self.y6Storage, self.fR6, self.fM6, self.triModes[2]))

        if self.bicEnables[3].get() or self.triEnables[3].get():
            try: globalWeight: float = float(self.weightVar.get())
            except ValueError: globalWeight = 1.0

            bicMavSlice: List[float] = self.fM3[self.viewStart:endIdx]
            triMavSlice: List[float] = self.fM6[self.viewStart:endIdx]

            if self.bicEnables[3].get() and getattr(self, 'lineNetBic', None):
                self.bicNetData = self.calculateNetForce(bicMavSlice, triMavSlice, globalWeight)
                self.lineNetBic.set_data(xs, self.bicNetData)

            if self.triEnables[3].get() and getattr(self, 'lineNetTri', None):
                self.triNetData = self.calculateNetForce(bicMavSlice, triMavSlice, globalWeight)
                self.lineNetTri.set_data(xs, self.triNetData)
            
        if getattr(self, 'ax1', None): self.ax1.set_xlim(float(self.viewStart), float(self.viewStart + self.viewSize))

    def onScroll(self, *args: Any) -> None:
        total: int = len(self.data)
        if total <= self.viewSize: return
        oldStart: int = self.viewStart
        if args[0] == "moveto": self.viewStart = int(float(args[1]) * total)
        elif args[0] == "scroll": self.viewStart += int(args[1]) * int(self.viewSize * 0.1)
        self.viewStart = max(0, min(self.viewStart, total - self.viewSize))
        if self.viewStart != oldStart:
            self.updateLines()
            self.updateScrollbar()
            if self.plot: self.plot.draw_idle()

    def updateScrollbar(self) -> None:
        if self.scrollbar:
            total: int = len(self.data)
            if total <= self.viewSize: self.scrollbar.set(0.0, 1.0)
            else: self.scrollbar.set(self.viewStart / total, (self.viewStart + self.viewSize) / total)