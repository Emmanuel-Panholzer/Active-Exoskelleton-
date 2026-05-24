from tkinter import Tk
from DataStore import DataStore
from SerialManager import SerialManager
from MeasurementEngine import MeasurementEngine
from MainWindow import MainWindow

if __name__ == "__main__":
    # 1. Create Core Systems
    serialMgr = SerialManager()

    # 2. Build and Launch UI
    root = Tk()
    app = MainWindow(root, DataStore(), serialMgr, MeasurementEngine(serialMgr))
    root.mainloop()