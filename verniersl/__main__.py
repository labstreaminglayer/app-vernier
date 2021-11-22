# -*- coding: utf-8 -*-
"""
Command Line Interface
----------------------
"""
from godirect import GoDirect
import pylsl
import threading
import time
from pygatt.exceptions import NotConnectedError


def close_device(device):
    if device.type == "USB":
        try:
            device.close()
        except NotConnectedError:
            print("could not connect with", device)


def open_device(device):
    if device.type == "USB":
        try:
            device.open()
        except NotConnectedError:
            print("could not connect with", device)


def resolve_all():
    available = []
    for idx, info in enumerate(iterate_available()):
        available.append(info)
    return available


def iterate_available():
    devices = godirect.list_devices()
    for idx, d in enumerate(devices):
        open_device(d)
        info = {}
        info["order_code"] = d.order_code
        info["serial_number"] = d.serial_number
        info["device"] = d
        close_device(d)
        yield info


def resolve_devices(**kwargs):
    print("Searching for device matching: ", kwargs)
    available = iterate_available()
    fitting = []
    for info in available:
        fits = []
        for k, v in kwargs.items():
            if v is None:
                fits.append(True)
            else:
                fits.append(info[k] == v)
        if all(fits):
            fitting.append(info["device"])

    if fitting:
        return fitting
    else:
        return None


def get_default_sensors(device):
    device.open()
    device.enable_default_sensors()
    sensors = get_enabled_sensors(device)
    device.close()
    return sensors


def get_enabled_sensors(device):
    sensors = device.get_enabled_sensors()
    return [s.sensor_description for s in sensors]


def get_available_sensors(device):
    device.open()
    sensors = device.list_sensors()
    device.close()
    return {s.sensor_description: k for k, s in sensors.items()}


# %%
def device_to_stream(device):
    fs = 0  # 1000/device.sample_period_in_milliseconds
    sn = device.serial_number
    oc = device.order_code

    names = []
    units = []
    types = []
    sensors = device.get_enabled_sensors()
    for sensor in sensors:
        names.append(sensor.sensor_description)
        units.append(sensor.sensor_units)
        types.append("vernier")

    info = pylsl.StreamInfo(
        name=device.name.strip().replace(" ", "_"),
        type=oc.split("GDX-")[1].upper(),
        channel_count=len(names),
        nominal_srate=fs,
        channel_format="float32",
        source_id=str(sn),
    )

    acq = info.desc().append_child("acquisition")
    acq.append_child_value("manufacturer", "Vernier")
    acq.append_child_value("model", str(device))
    acq.append_child_value("compensated_lag", "0")

    channels = info.desc().append_child("channels")
    for c, u, t in zip(names, units, types):
        channels.append_child("channel").append_child_value(
            "label", c
        ).append_child_value("unit", u).append_child_value("type", t)

    stream = pylsl.StreamOutlet(info, chunk_size=0, max_buffered=1)
    print("Creating", info.as_xml())
    return stream


class Outlet(threading.Thread):
    def __init__(self, device, enable: list = ["default"]):
        threading.Thread.__init__(self)
        self.device = device
        self.enable = enable

    def run(self):
        self.is_running = True
        device = self.device
        available_sensors = get_available_sensors(device)
        device.open()  # get_availbel
        # enable channels
        for e in self.enable:
            e = e.strip()
            if e == "default":
                device.enable_default_sensors()
            try:
                device.enable_sensors([available_sensors[e]])
            except KeyError:
                print(f"Could not find {e} to enable")
            print(f"Enabling {e}")
        sensors = device.get_enabled_sensors()
        print([s.sensor_description for s in sensors], end="")
        print(" are enabled. Starting to stream now")
        stream = device_to_stream(device)
        device.start()
        t0 = None

        def print_log(t0, dt=[], cnt=[0]):
            t1 = pylsl.local_clock()
            if t0 is not None:
                cnt[0] += 1
                dt.append(t1 - t0)
                if len(dt) > 100:
                    dt = dt[-100:]
                Fs = len(dt) / sum(dt)
                print(
                    f"#{int(cnt[0]):5} with {chunk} at {t1:4.2f} approx Fs = {Fs:4.2f}"
                )
            return t1

        while self.is_running:  # publish
            time.sleep(0.001)
            if device.read():
                chunk = []
                for six, sens in enumerate(sensors):
                    # chunk.append(sens.value)
                    chunk.extend(sens.values)
                    sens.clear()  # to prevent memory issues due to unnecessary appending of sensor data
                t0 = print_log(t0)
                stream.push_sample(chunk)

        device.stop()
        device.close()


def scan():
    "scan available devices and print information about them"
    print("Available devices. Default sensors are marked by *.")
    counter = 0
    for dev in iterate_available():
        counter += 1
        print("---------------------------------------------------")
        print(dev["order_code"], dev["serial_number"])
        device = dev["device"]
        sensors = get_available_sensors(device)
        default = get_default_sensors(device)
        for s in sensors.keys():
            info = "*" if s in default else " "
            print(info, s, info)
    if counter == 0:
        print(f"Found no devices.")
    return counter


# %%
def start_godirect(mode: str):
    global godirect
    print(f"Starting godirect in {mode} mode")

    if mode == "any":
        godirect = GoDirect()
    elif mode == "usb":
        godirect = GoDirect(use_ble=False)
    elif mode == "ble":
        godirect = GoDirect(use_usb=False)


def main():
    def do_quit():
        godirect.quit()
        quit()

    import argparse

    parser = argparse.ArgumentParser(
        description="Stream Vernier Go-Direct with LSL"
    )
    parser.add_argument(
        "--scan", action="store_true", help="report the available devices"
    )
    parser.add_argument(
        "--enable", default="[default]", help="which channels do enable: List"
    )
    parser.add_argument(
        "--serial_number",
        help="""The serial number (eg. OK2001B3) of the 
                        desired device. Streams are then limited to a single device""",
    )
    parser.add_argument(
        "--order_code",
        help="""The order code (eg. GDX-ACC for an accelerometer)
                        of the desired device. Can find and stream more than 
                        one device""",
    )
    parser.add_argument(
        "--number",
        type=int,
        default=1,
        help="""How many devices are expected, aborts otherwise. 
                        Helpful as sometimes, one connection might be lost, 
                        and we would start streaming then anyways. Defaults to 1""",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="usb",
        help='''Whether the devices are to be searched 
                        and connected over "usb", "ble" or "any". Defaults to 
                        "usb"''',
    )
    args = parser.parse_args()
    enable = args.enable.replace("[", "").replace("]", "").split(",")
    #

    try:
        start_godirect(args.mode.lower())
        if args.scan:
            scan()
        else:  # stream those devices fitting the arguments
            scan()
            devices = resolve_devices(
                order_code=args.order_code, serial_number=args.serial_number
            )
            if not devices:
                parser.print_help()
                print(f"No devices were found to stream")
            elif len(devices) != args.number:
                input(
                    f"Found {len(devices)}, but {args.number} were requested"
                )
            else:
                for device in devices:
                    o = Outlet(device=device, enable=enable)
                    o.start()
    except OSError:
        input(f"Connection problem, please replug the USB")
    except Exception as e:
        print(e)
    except ConnectionError as e:
        parser.print_help()
    finally:
        input("Press return to close....")
        # this is here because if opened on windows, terminals usually close
        # immediatly, preventing the user from reading the output of error
        # messages etc.
        do_quit()


# %%
if __name__ == "__main__":
    main()

