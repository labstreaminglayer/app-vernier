## Verniersl

This is a command-line-interface to collect data from a Godirect device and stream it via labstreaming layer.

The app is written in python 3.

# Installation


```
pip install vernier-lsl
```

You can install the development version with
```
git clone https://github.com/labstreaminglayer/app-vernier
cd app-vernier
pip install -e .
pip install -r requirements.txt
```
The app wraps ```pylsl``` and ```godirect``` from Vernier (https://github.com/VernierST/godirect-py). The latter wraps hidapi for USB and vernierpygatt for BLE. On linux, compilation of the wheels for hidapi required libusb and libudev.

## Usage

```
usage: vernier-lsl [-h] [--scan] [--enable ENABLE]
                 [--serial_number SERIAL_NUMBER] [--order_code ORDER_CODE]
                 [--number NUMBER] [--mode MODE]

Stream Vernier Go-Direct with LSL

optional arguments:
  -h, --help            show this help message and exit
  --scan                report the available devices
  --enable ENABLE       which channels do enable: List
  --serial_number SERIAL_NUMBER
                        The serial number (eg. OK2001B3) of the desired
                        device. Streams are then limited to a single device
  --order_code ORDER_CODE
                        The order code (eg. GDX-ACC for an accelerometer) of
                        the desired device. Can find and stream more than one
                        device
  --number NUMBER       How many devices are expected, aborts otherwise.
                        Helpful as sometimes, one connection might be lost,
                        and we would start streaming then anyways. Defaults to
                        1
  --mode MODE           Whether the devices are to be searched and connected
                        over "usb", "ble" or "any". Defaults to "usb"
```

### Example

The terminology of Go Direct device can be confusing, as the device itself can be called a sensor, while each device has a set of individual sensors which can be turned on or off. Some of them are turned on by default. Check which devices are available, and show their available sensors, and which of there are enabled by default:

```
vernier-lsl --scan
```

Find a Go Direct (C) Acceleration Sensor, enable the default sensors and stream it

```
vernier-lsl --order_code GDX-ACC
```

Find a specific Go Direct (C) Acceleration Sensor, enable the x,y, andz axis acceleration sensors and stream it

```
vernier-lsl --enable "[X-axis acceleration, Y-axis acceleration, Z-axis acceleration]" --order_code GDX-ACC --serial_number 0H101754
```

Find exactly two Hand Dynamometers, enable force sensors and stream them.

```
vernier-lsl --enable Force --order_code GDX-HD --number 2
```

# Supported devices

The toolbox was developed and tested on the USB interface for the GDX-HD Hand Dynamometer, the GDX-ACC accelerometer, and the GDX-RB Respiration Belt. Vernier has a large variety of sensor devices (https://www.vernier.com/products/sensors/go-direct-sensors/). Some have quirks, e.g. for the GDX-ACC the sensors channel indices were set up wrong. So, pop a note if another device works (or doesn't)!

# Bluetooth
I have also implemented BLE support, but this requires a Bluegiga BLED112 Bluetooth® Low Energy Dongle, see also: https://github.com/VernierST/godirect-py/issues/5 Please note that in the meantime, starting with godirect-py v1.0.5, godirect has implememted the bleak backend. I have not tested this.
