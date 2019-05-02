# -*- coding: utf-8 -*-
"""
Created on Fri Mar  1 12:18:57 2019

@author: Robert Guggenberger
"""
# %%
from godirect import GoDirect
import pylsl
import argparse
# %%
class GoDirectDevice():
    def __init__(self):
        self.godirect = GoDirect()   
        device = self.godirect.get_device()
        device.open()
        device.start()
        #print(device.battery_level_percent)
        print(device.description)
        print(device.name)
        print(device.id.decode())
        self.device = device
        self.sensors = []
    
    def connect(self):
        self.sensors = self.device.get_enabled_sensors()       
    
    def close(self):
        self.device.stop()
        self.device.close()
        self.godirect.quit()

    def __getattr__(self, attr):
        try:            
            return getattr(self, attr)
        except:            
            return getattr(self.device, attr)
    
    def read(self):
        return self.device.read()
    
    def __str__(self):
        return str(self.device)
    # %%
def device_to_stream(device):
    fs = 1000/device.sample_period_in_milliseconds
    devtype = device.description.split('Go Direct® ')[1]
    device.connect()
    
    names = []
    units = []
    types = []
    for sensor in device.sensors:
        names.append(sensor.sensor_description)
        units.append(sensor.sensor_units)
        types.append('vernier')
        
    info = pylsl.StreamInfo(name=str(device),
                            type=devtype,
                            channel_count=len(names),                              
                            nominal_srate=fs, 
                            channel_format='float32',
                            source_id=str(device)
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
    return stream, device.sensors

def main():
    import time
    device = GoDirectDevice()
    stream, sensors = device_to_stream(device)
    # %% # publish 
    cnt = 0.
    while True:       
        time.sleep(0.001)
        if device.read():            
            stream.push_sample([sensors[0].value])                   
            sensors[0].clear() #to prevent memory issues due to unnecessary appending of sensor data
            cnt+=1
            print(cnt)

def test_plot():
    import matplotlib.pyplot as plt
    device = GoDirectDevice()
    stream, sensors = device_to_stream(device)
    print('Connected and streaming for', device)
    # %% # publish 
    values = []
    timepoints = []
    t0 = pylsl.local_clock()
    fig, axe = plt.subplots(1,1)    
    vmax = 1;
    while True:        
        if device.read():            
            stream.push_sample([sensors[0].value])       
            values.append(sensors[0].value)
            timepoints.append(pylsl.local_clock()-t0)
            vmax = max(vmax, max(values))
            if len(sensors[0].values)>=1:
                axe.cla()
                axe.plot(timepoints, values)
                axe.set_xlabel('Time in s')
                axe.set_ylabel('Force in N')
                axe.set_ylim([0, vmax])
                plt.pause(0.001)
                sensors[0].clear()
                if len(values) > 100:
                    values = values[-100:]
                    timepoints = timepoints[-100:]
# %%
if __name__ == '__main__':
    #main()
    parser = argparse.ArgumentParser(description='Stream Vernier Go-Direct with LSL')
    parser.add_argument('--noplot', action='store_true', 
                        help='do not visualize the stream')
    args = parser.parse_args() 
    if args.noplot:
        main()
    else:
        test_plot()
    
    

# %%