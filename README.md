# Electromyography (EMG) Exoskeleton Suite

This repository contains the software suite developed for my BSc thesis: an active electric elbow exoskeleton based on the EduExo Maker platform. It features real-time 1000Hz biomechanical data acquisition (via ESP32), high-speed integer-based motor control, and a custom Python GUI for measurement and parameter tuning.

## Hardware Setup
* **Microcontroller:** ESP32 (Dual-core, 240 MHz, 12-bit ADC)
* **Sensors:** Dry electrode single-channel EMG (Biceps & Triceps)
* **Actuator:** High-torque digital servo 
* **Power Architecture:** External bench supply.

## 1. Arduino Firmware (`/Arduino`)
The C++ firmware (`Exoskelleton_Controll_And_Measurement_Send.ino`) handles continuous 1000Hz analog reading, digital filtering, net-force calculation, and precise PWM servo control.

### Required Arduino Libraries
Before compiling, install the following via the Arduino Library Manager:
* **`ESP32Servo`** (by Kevin Harrington): Required for hardware-timer PWM control on the ESP32.

## 2. Python Measurement UI (`/Python`)
The Tkinter desktop application allows for real-time Matplotlib data visualization, automated measurement routines (e.g., Isometric Contractions, Concentric Lifts), and remote parameter tuning of the exoskeleton without re-flashing the ESP32.

### Local Setup (Virtual Environment)
It is highly recommended to run this suite within a Python virtual environment to manage dependencies safely.

**1. Create and activate the virtual environment:**
```bash
# On Windows:
python -m venv venv
venv\Scripts\activate

# On macOS/Linux:
python -m venv venv
source venv/bin/activate

**2. Install requirements**
pip install -r requirements.txt

**3. Launch the application:**
python Main.py

