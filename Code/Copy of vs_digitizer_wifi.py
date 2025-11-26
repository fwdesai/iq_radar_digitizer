import array, time
import machine
from machine import Pin
import rp2
from rp2 import PIO, StateMachine, asm_pio
import sys
import struct
import asyncio
import aioble
import bluetooth
import network
import usocket as socket
import time


# GPIO pins 16-19, 27 are free for other use
# Variables to set
###################################################################################
filtered_out = True
no_latency_out = False
data_out = 2                   # options 0 for write to file, 1 for bluetooth, 2 for wifi
FILE = 'test.txt'
data = open(FILE, 'w')

SSID = 'StanfordStudents'       # network name and password for wifi data transfer
PASSWORD = 'Wolfson1176'

decimation = 4096				# options here are 256, 1024, 4096, 16384 (ignore if filtered_out = 0)
duration = 20
###################################################################################
# LEAVE THESE VARIABLES UNCHANGED
fs = int(200e3)
N = (fs / decimation) * duration * 2
buffer = []


# PINS FOR THE INTERFACE WITH THE ADCs
RDLB_1 = Pin(0, Pin.OUT)
RDLA_1 = Pin(1, Pin.OUT)
BUSY_1 = Pin(2, Pin.IN)
SDOB_1 = Pin(3, Pin.IN)
SCKB_1 = Pin(4, Pin.OUT)
SCKA = Pin(5, Pin.OUT)
SDOA = Pin(6, Pin.IN)



SYNC = Pin(9, Pin.OUT)
MCLK = Pin(10, Pin.OUT)
SDOB_2 = Pin(11, Pin.IN)
SCKB_2 = Pin(12, Pin.OUT)
DRL_2 = Pin(13, Pin.IN, Pin.PULL_DOWN)

SEL1 = Pin(14, Pin.IN)
SEL0 = Pin(15, Pin.IN)

RDLA_2 = Pin(20, Pin.OUT)
BUSY_2 = Pin(21, Pin.IN)
RDLB_2 = Pin(22, Pin.OUT)
DRL_1 = Pin(26, Pin.IN, Pin.PULL_DOWN)

# POWER GOOD PIN ON THE REGULATOR
#PG_REG = Pin(28, Pin.IN)

# State Machine Frequency
sm_freq = int(100e6)

###################################################################################

################################## BLUETOOTH SETUP ################################
if (data_out == 1):
    print('Data out over bluetooth')
    # bluetooth setup code
    ble_name = "iq_digitizer"
    ble_svc_uuid = bluetooth.UUID(0x181A)
    print(ble_svc_uuid)
    ble_characteristic_uuid = bluetooth.UUID(0x2A6E)
    ble_appearance = 0x0300
    ble_advertising_interval = 300
    ble_service = aioble.Service(ble_svc_uuid)
    ble_characteristic = aioble.Characteristic(
        ble_service,
        ble_characteristic_uuid,
        read=True,
        notify=True)
    aioble.register_services(ble_service)
elif(data_out == 2):
# WIFI setup code here
    print('Data out over wifi')
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    while not wlan.isconnected():
        pass

    print('Connection')
    print('Wifi Connected')
    print(wlan.ifconfig()[0])

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((wlan.ifconfig()[0], 12345))
    print('server is listening')

else:
    if (data_out != 0):
        print(f"The variable data_out is set to an invalid value of {data_out}. Please fix.\n")
        sys.exit()
    else:
        print('Data output to file')

async def ble_task():
    while True:
        async with await aioble.advertise(
            ble_advertising_interval,
            name=ble_name,
            services=[ble_svc_uuid],
            appearance=ble_appearance) as connection:
            print('Connection from', connection.device)
            sm5.active(1)
            sm0.active(1)
            sm2.active(1)
            sm3.active(1)
            sm1.active(1)
            
            # Start the data sending task
            try:
                await send_data(connection)
            finally:
                # Stop state machines when disconnected
                sm5.active(0)
                sm0.active(0)
                sm2.active(0)
                sm3.active(0)
                sm1.active(0)

async def send_data(connection):
    try:
        sample_count = 0
        while connection.is_connected():
            if not connection.is_connected():
                break
            val = sm1.get()  # This blocks until data is available
            
            if val is not None:
                # Pack as little-endian signed integer and notify client
                packet = struct.pack('<i', val)
                ble_characteristic.notify(connection, packet)
                sample_count += 1
                
            else:
                print("Warning: sm1.get() returned None")
                await asyncio.sleep_ms(1)  # Small delay if no data
                
    except Exception as e:
        print(f"send_data error: {e}")


            
async def main():
    task1 = asyncio.create_task(ble_task())
    await task1


###################################################################################


if (filtered_out == no_latency_out):
    print('Please choose only 1 of filtered_out and no_latency_out')
    
if (filtered_out and not no_latency_out):
    print('filtered')
    RDLB_1.value(1)
    RDLB_2.value(1)
    #RDLA_1.value(0)
    #RDLA_2.value(0)
elif (not filtered_out and no_latency_out):
    print('no latency output')
    RDLA_1.value(1)
    RDLA_2.value(1)
    #RDLB_1.value(0)
    #RDLB_2.value(0)


#Set the decimation for the ADCs based on the decimation variable above
###################################################################################
if decimation == 256:
    print('in 256')
    pass
elif decimation == 1024:
    print('in 1024')
    pass
elif decimation == 4096:
    print('in 4096')
    pass
elif decimation == 16384:
    print('in 16384')
    pass
else:
    print(f'{decimation} is an invalid entry for the decimation variable. Please correct if you intend do use the filtered ouput')
    if filtered_out:
        print('Program terminating')
        sys.exit()
###################################################################################

if filtered_out:
    print(f'Using the filtered output with decimation factor of {decimation}.')
else:
    print('Using the no latency ouput.')



############################## STATE MACHINE FUNCTIONS ############################
# MCLK Function
@rp2.asm_pio(set_init=PIO.OUT_LOW)
def sync_mclk():
    #inital sync pulse
    #set(pins, 0b01)
    #nop() [1]
    #set(pins, 0b00)
    
    wrap_target()
    
    set(pins, 1)
    nop() [4]
    set(pins, 0)
    
    
    nop()		[31]
    nop()		[31]
    nop()		[31]
    nop()		[31]
    nop()		[31]
    nop()		[31]
    nop()		[31]
    nop()		[31]
    nop()		[31]
    nop()		[31]
    nop()		[31]
    nop()		[31]
    nop()		[31]
    nop()		[31]
    nop() 		[31]
    nop()		[12]
    
    wrap()
    

# DRL Function
# using drl from ADC 2, ie gpio 13
@rp2.asm_pio(set_init=PIO.OUT_LOW)
def sync_drl():
    wrap_target()
    wait(1, pin, 0)
    wait(0, pin, 0)
    irq(0)
    set(pins, 1) [2]
    set(pins, 0)
    wrap()

    
#@rp2.asm_pio(set_init=(PIO.OUT_LOW, PIO.OUT_LOW))    
@rp2.asm_pio(set_init=PIO.OUT_LOW, in_shiftdir=PIO.SHIFT_LEFT, autopush=True, push_thresh=32)
def scka_sdoa():
    
    wrap_target()
    wait(1, irq, 1) [5]
    
    
    
    set(x, 31)
    label('loop 1')
    set(pins, 1) [1]
    in_	(pins, 1)				#replace with a read instruction when do the actual in
    set(pins, 0) 
    jmp(x_dec, 'loop 1')
    
    irq(2)
    wait(1, irq, 5) [3]
    
    set(x, 31)
    label('loop 2')
    set(pins, 1) [1]
    in_(pins, 1)				#replace with a read instruction when do the actual in
    set(pins, 0) 
    jmp(x_dec, 'loop 2')
    
    irq(3)
    wrap()
    
    

@rp2.asm_pio(set_init=PIO.OUT_HIGH)
def rdla_1():
    wrap_target()
    wait(1, irq, 0)
    set(pins, 0)
    irq(1)
    
    wait(1, irq, 2)
    set(pins, 1)
    irq(4)					# added this
    wrap()
    

@rp2.asm_pio(set_init=PIO.OUT_HIGH)
def rdla_2():
    wrap_target()
    irq(clear, 3)
    wait(1, irq, 4) [1]
    set(pins,0)
    
    irq(5)
    wait(1, irq, 3) [1]
    set(pins, 1)
    
    wrap()

############################## Start Sequence ############################

def to_signed(val, bits):
    """Convert unsigned integer to signed integer with given bit width."""
    if val & (1 << (bits - 1)):  # if sign bit is set
        val -= 1 << bits
    return val

def clean_up_sm():
    try:
        sm5.active(0)
        sm2.active(0) 
        sm0.active(0)
        sm3.active(0)
        sm1.active(0)
    except:
        pass

sm5 = StateMachine(5, sync_mclk, freq=sm_freq, set_base=MCLK)
sm0 = StateMachine(0, sync_drl, freq=sm_freq, set_base=SYNC, in_base=DRL_1)
sm1 = StateMachine(1, scka_sdoa, freq=sm_freq, set_base=SCKA, in_base=SDOA)
sm2 = StateMachine(2, rdla_1, freq=sm_freq, set_base=RDLA_1)
sm3 = StateMachine(3, rdla_2, freq=sm_freq, set_base=RDLA_2)


sm5.active(1)
sm0.active(1)
sm2.active(1)
sm3.active(1)
sm1.active(1)
  
                
RDLA_1.value(1)
RDLA_2.value(1)
SCKA.value(0)

sm0.exec("irq(clear, 0)")
sm0.exec("irq(clear, 1)")
sm0.exec("irq(clear, 2)")
sm0.exec("irq(clear, 3)")
sm0.exec("irq(clear, 4)")
sm0.exec("irq(clear, 5)")

if (data_out == 0):
    t0 = time.ticks_ms()
    for _ in range(N):
        raw = sm1.get()
        val = to_signed(raw, 32)
        buffer.append(val * -1)


    sm5.active(0)
    sm0.active(0)
    sm2.active(0)
    sm3.active(0)
    sm1.active(0)


    t1 = time.ticks_ms()
    elapsed = time.ticks_diff(t1, t0) / 1000
    print(elapsed)



    for v in buffer:
        data.write(str(v) + '\n')
elif (data_out == 1):
    asyncio.run(main())
else:
    # start wifi stremaing data
    request, c_addr = server_socket.recvfrom(1024)
    print('client request', request.decode())
    print('client address', c_addr)
    
    finished = 'FINISHED'

    for _ in range(N):
        raw = sm1.get()
        val = to_signed(raw, 32)
        server_socket.sendto(str(val).encode(), c_addr)
    
    server_socket.sendto(finished.encode(), c_addr)

    sm5.active(0)
    sm0.active(0)
    sm2.active(0)
    sm3.active(0)
    sm1.active(0)

data.close()



    

 
 

