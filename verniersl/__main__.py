# -*- coding: utf-8 -*-
"""
Created on Fri Mar  1 12:18:57 2019

@author: Robert Guggenberger
"""
# %%
from godirect import GoDirect
import pylsl
import threading
import time
# %%
#import logging
#logging.basicConfig()
#logging.getLogger('godirect').setLevel(logging.DEBUG)
#logging.getLogger('pygatt').setLevel(logging.DEBUG)
# %%
godirect = GoDirect()

def resolve_all():
    devices = godirect.list_devices()            
    available = []
    for idx, d in enumerate(devices):
        d.open()
        info = {}
        info['order_code'] = d.order_code
        info['serial_number'] = d.serial_number        
        info['device'] = d
        available.append(info)
        d.close()
    return available

def resolve_devices(**kwargs):   
    print('Searching for device: ',kwargs)
    available = resolve_all()
    fitting = []
    for info in available:
        fits = []
        for k, v in kwargs.items():
            if v is None: 
                fits.append(True)
            else:
                fits.append(info[k] == v)
        if all(fits):
            fitting.append(info['device'])
    
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
    return {s.sensor_description:k for k,s in sensors.items()}
# %%
def device_to_stream(device):
    fs = 0# 1000/device.sample_period_in_milliseconds        
    sn = device.serial_number
    oc = device.order_code

    names = []
    units = []
    types = []
    sensors = device.get_enabled_sensors()
    for sensor in sensors:
        names.append(sensor.sensor_description)
        units.append(sensor.sensor_units)
        types.append('vernier')
        
    info = pylsl.StreamInfo(name=device.name.strip().replace(' ','_'),
                            type=oc.split('GDX-')[1].upper(),
                            channel_count=len(names),                              
                            nominal_srate=fs, 
                            channel_format='float32',
                            source_id=str(sn)
                            )
            
    acq = info.desc().append_child("acquisition")
    acq.append_child_value('manufacturer', 'Vernier')
    acq.append_child_value('model', str(device))     
    acq.append_child_value('compensated_lag', '0')
    
    channels = info.desc().append_child("channels")
    for c, u, t in zip(names, units, types):
                    channels.append_child("channel") \
                    .append_child_value("label", c) \
                    .append_child_value("unit", u) \
                    .append_child_value("type", t)   
    

    stream = pylsl.StreamOutlet(info,
                                chunk_size=0,
                                max_buffered=1)
    print('Creating', info.as_xml())
    return stream
# %%
class Outlet(threading.Thread):
    
    def __init__(self, device, enable:list=['default']):
        threading.Thread.__init__(self)
        self.device = device
        self.enable = enable
    
    def run(self):
        self.is_running = True          
        device = self.device
        available_sensors = get_available_sensors(device)
        device.open() #get_availbel        
        # enable channels        
        for e in self.enable:
            e = e.strip()
            if e == 'default':
                device.enable_default_sensors()
            try:
                device.enable_sensors([available_sensors[e]])
            except KeyError:
                print(f'Could not find {e} to enable')
            print(f'Enabling {e}')
        sensors = device.get_enabled_sensors()
        print([s.sensor_description for s in sensors], end='')
        print(' are enabled. Starting to stream now')
        stream = device_to_stream(device)        
        device.start()
        t0 = None
        def print_log(t0, dt=[], cnt=[0]):
            t1 = pylsl.local_clock()
            if t0 is not None:
                cnt[0] += 1
                dt.append(t1-t0)  
                if len(dt)>100:
                    dt = dt[-100:]
                Fs = len(dt)/sum(dt)
                print(f'#{int(cnt[0]):5} with {chunk} at {t1:4.2f} approx Fs = {Fs:4.2f}')
            return t1

        while self.is_running: # publish             
            time.sleep(0.001)              
            if device.read():  
                chunk = []
                for six, sens in enumerate(sensors):
                    chunk.append(sens.value) #TODO upgrade to sens.values
                    sens.clear() #to prevent memory issues due to unnecessary appending of sensor data
                t0 = print_log(t0)
                stream.push_sample(chunk)
                
        device.stop()
        device.close()
# %%
if __name__ == '__main__':    
    import argparse
    parser = argparse.ArgumentParser(description='Stream Vernier Go-Direct with LSL')
    parser.add_argument('--scan', action='store_true',
                        help='which channels do enable')
    parser.add_argument('--enable', default='[default]',
                        help='which channels do enable: List')
    parser.add_argument('--serial_number',
                        help='which devices to select')
    parser.add_argument('--order_code',
                        help='which devices to select')
    parser.add_argument('--number', type=int, default=1,
                        help='How many should be found. Aborts otherwise')
    args = parser.parse_args() 
    enable = args.enable.replace('[','').replace(']','').split(',')
    # 
    try:
        if args.scan:
            print('Available devices. Default sensors are marked by *.')                  
            for dev in resolve_all():
                print('---------------------------------------------------')
                print(dev['order_code'], dev['serial_number'])
                device = dev['device']
                sensors = get_available_sensors(device)
                default = get_default_sensors(device)
                for s in sensors.keys():
                    info = '*' if s in default else ' '
                    print(info, s, info)
                                
        else:     #stream those devices fitting the arguments
            devices = resolve_devices(order_code=args.order_code,
                                      serial_number=args.serial_number)
            if len(devices) != args.number:
                input(f'Found {len(devices)}, but {args.number} were requested')
                quit()
            for device in devices:
                o = Outlet(device=device, enable=enable)
                o.start()
    except OSError:
        input(f'Connection problem, please replug the USB')        
    except Exception as e:
        raise e
    finally:
        godirect.quit()

# %%
