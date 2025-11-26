import asyncio
import struct
from bleak import BleakClient, BleakScanner
from collections import deque
import time


# BLE configuration - must match the transmitter
BLE_NAME = "iq_digitizer"
BLE_SVC_UUID = "0000181a-0000-1000-8000-00805f9b34fb"  # Environmental Sensing
BLE_CHARACTERISTIC_UUID = "00002a6e-0000-1000-8000-00805f9b34fb"  # Temperature
FILE = 'bt_bh_2.txt'


duration = 20
fs = 200000
decimation = 1024
N = int((fs / decimation) * duration * 2)

def to_signed(val, bits):
    """Convert unsigned integer to signed integer with given bit width."""
    if val & (1 << (bits - 1)):  # if sign bit is set
        val -= 1 << bits
    return val

class BLEDataReceiver:
    def __init__(self, max_buffer_size=10000):
        self.client = None
        self.data_buffer = deque(maxlen=max_buffer_size)
        self.is_connected = False
        self.receive_count = 0
        self.target_packets = N
        
    async def scan_for_device(self, timeout=80.0):
        """Scan for the BLE device by name"""
        print(f"Scanning for device '{BLE_NAME}'...")
        
        devices = await BleakScanner.discover(timeout=timeout)
        for device in devices:
            if device.name == BLE_NAME:
                print(f"Found device: {device.name} ({device.address})")
                return device
        
        print(f"Device '{BLE_NAME}' not found")
        return None
    
    def notification_handler(self, sender, data):
        """Handle incoming BLE notifications"""
        try:
            # Unpack little-endian signed integer
            if len(data) == 4:  # struct.pack('<i') creates 4 bytes
                val = struct.unpack('<i', data)[0]
                
                # Store only the integer value (negated)
                self.data_buffer.append(val * -1)
                
                self.receive_count += 1
                
                # Print every 100th packet to show activity
                if self.receive_count % 100 == 0:
                    print(f"Received {self.receive_count}/{self.target_packets} packets, latest value: {val * -1}")
            else:
                print(f"Unexpected data length: {len(data)} bytes")
                
        except Exception as e:
            print(f"Error processing notification: {e}")
    
    async def connect_and_receive(self):
        """Connect to device and start receiving data"""
        device = await self.scan_for_device()
        if not device:
            return False
        
        try:
            async with BleakClient(device.address) as client:
                self.client = client
                self.is_connected = True
                print(f"Connected to {device.name}")
                print(f"Target: {self.target_packets} packets")
                
                # Subscribe to notifications
                await client.start_notify(BLE_CHARACTERISTIC_UUID, self.notification_handler)
                print("Subscribed to notifications")
                start_time = time.time()
                
                # Keep receiving until we have N packets
                try:
                    while self.receive_count < self.target_packets:
                        await asyncio.sleep(0.1)
                        
                    end_time = time.time()
                    print(f"\nTarget of {self.target_packets} packets reached!")
                    print("Saving data automatically...")
                    print(f'Duration = {end_time - start_time}')
                
                except KeyboardInterrupt:
                    print("\nReceiving interrupted by user")
                
                finally:
                    # Stop notifications
                    await client.stop_notify(BLE_CHARACTERISTIC_UUID)
                    print("Stopped notifications")

                    # Always save data if we have any
                    if len(self.data_buffer) > 0:
                        self.save_data_to_file(FILE)
                    
        except Exception as e:
            print(f"Connection error: {e}")
            return False
        
        finally:
            self.is_connected = False
            print("Disconnected")
            
        return True
    
    def get_data_array(self):
        """Return received data as a list"""
        return list(self.data_buffer)
    
    def get_values_array(self):
        """Return the integer values as a list (same as get_data_array since we only store integers)"""
        return list(self.data_buffer)
    
    def clear_buffer(self):
        """Clear the data buffer"""
        self.data_buffer.clear()
        self.receive_count = 0
        print("Data buffer cleared")
    
    def save_data_to_file(self, filename="ble_data.txt"):
        """Save received data to a text file"""
        try:
            with open(filename, 'w') as f:
                for item in self.data_buffer:
                    f.write(str(item) + '\n')

            print(f"Data saved to {filename}")
            return True
            
        except Exception as e:
            print(f"Error saving data: {e}")
            return False









async def main():
    """Main function to run the receiver"""
    receiver = BLEDataReceiver(max_buffer_size=50000)
    
    print("BLE Data Receiver Starting...")
    print(f"Will collect {N} packets then automatically stop")
    print("Press Ctrl+C to stop early")
    
    try:
        success = await receiver.connect_and_receive()
        
        if success and len(receiver.data_buffer) > 0:
            print(f"\nReceived {len(receiver.data_buffer)} total packets")
            
            # Data was already saved automatically in connect_and_receive()
            print('Data automatically saved to received_ble_data.txt')
            
            # Example: Print first few packets
            print("\nFirst 5 packets:")
            for i, item in enumerate(list(receiver.data_buffer)[:5]):
                print(f"  {i+1}: value={item}")
            
            # Get just the values as an array
            values = list(receiver.data_buffer)
            print(f"Values array length: {len(values)}")
            if values:
                print(f"Value range: {min(values)} to {max(values)}")
        
    except KeyboardInterrupt:
        print("\nShutdown requested")
    
    except Exception as e:
        print(f"Error in main: {e}")

if __name__ == "__main__":
    asyncio.run(main())