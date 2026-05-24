from enum import Enum, auto

class MeasurementType(Enum):
    Steady = auto()
    ContractionBiceps = auto() 
    ContractionTriceps = auto()
    FastUp = auto()
    SlowUp = auto()
    FastDown = auto()
    SlowDown = auto()

class CommunicationProtocol(Enum):
    Handshake = 'H'
    HandshakeBack = 'B'
    Measurement = 'M'
    Stop = 'S'
    UpdateParams = 'P'
    MsgEnd = '#'
    Error = 'E'

class UIDefaults:
    # DataStore Defaults
    defaultBaudrate: int = 2000000
    defaultSaveDir: str = "Exo_GUI/MeasurementData"
    
    # Plotting Display Defaults
    plotRefreshTimeMs: int = 10
    plotWindowSize: str = "1500"
    muscleMavRmsWindow: str = "50"
    muscleIsRolling: int = 0

    # Checkbox Defaults: [RAW, Filtered, Absolute, Net Force]
    # 1 = Visible , 0 = Hidden 
    bicepsEnableDefaults = [1, 1, 1, 1]
    tricepsEnableDefaults = [1, 1, 1, 1]

    # Axis Limit Defaults (Format: "Min", "Max")
    # Empty string "" = Auto-scale
    bicepsAxisDefaults = {
        "RAW":      ("", ""),
        "Filtered": ("", ""),
        "Absolute": ("", ""),
        "Net Force": ("-50", "50")
    }
    
    tricepsAxisDefaults = {
        "RAW":      ("10", "5860"),
        "Filtered": ("", ""),
        "Absolute": ("", ""),
        "Net Force": ("", "")
    }
    
    # Exoskeleton Simulation & Arduino Defaults
    weightFactor: str = "1.8"
    threshold: str = "28.0"
    speedMultiplier: str = "0.32"
    arduinoWindow: str = "50"
    arduinoRolling: int = 0