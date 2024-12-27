import network
from machine import Pin, PWM
import socket

led = Pin(2, Pin.OUT)
led.value(0)  # led on when power the board

# Motor control pins setup
motor1_in1 = PWM(Pin(12), freq=1000)   # Front Left
motor2_in3 = PWM(Pin(13), freq=1000)  # Front Right
motor3_in1 = PWM(Pin(15), freq=1000)   # Back Left
motor4_in3 = PWM(Pin(14), freq=1000)  # Back Right

# Create UDP socket
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_socket.bind(('0.0.0.0', 50000))

# Constants for joystick value conversion
JOYSTICK_MIN = 1000
JOYSTICK_MAX = 2000
JOYSTICK_MID = 1500
PWM_MIN = 0
PWM_MAX = 1023
PWM_MID = 511

def setup_wifi_ap():
    """Create WiFi Access Point"""
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid='Drone_Control', password='12345678')
    print('Access Point Created')
    print('SSID:', ap.config('essid'))
    print('IP Address:', ap.ifconfig()[0])

def parse_udp_packet(data):
    """Parse UDP packet in format '15001500150015000'"""
    try:
        packet = data.decode().strip()
        if len(packet) != 16:  # Checking correct packet length
            return None
            
        # Extract values for both joysticks
        left_x = int(packet[0:4])    # First 4 digits
        left_y = int(packet[4:8])    # Next 4 digits
        right_x = int(packet[8:12])  # Next 4 digits
        right_y = int(packet[12:16]) # Last 4 digits
        
        return left_x, left_y, right_x, right_y
    except:
        return None

def map_value(value, in_min, in_max, out_min, out_max):
    """Map value from one range to another"""
    return (value - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

def control_motors(left_x, left_y, right_x, right_y):
    """Control motors based on both joysticks values"""
    # Map joystick values (1000-2000) to PWM values (0-1023)
    # For left joystick - main movement control
    thrust = map_value(left_y, JOYSTICK_MIN, JOYSTICK_MAX, PWM_MIN, PWM_MAX)
    rotation = map_value(left_x, JOYSTICK_MIN, JOYSTICK_MAX, -PWM_MID, PWM_MID)
    
    # For right joystick - fine adjustment/trim
    trim_x = map_value(right_x, JOYSTICK_MIN, JOYSTICK_MAX, -100, 100)
    trim_y = map_value(right_y, JOYSTICK_MIN, JOYSTICK_MAX, -100, 100)
    
    # Calculate motor speeds
    fl_speed = thrust - rotation + trim_y - trim_x  # Front Left
    fr_speed = thrust + rotation + trim_y + trim_x  # Front Right
    bl_speed = thrust - rotation - trim_y - trim_x  # Back Left
    br_speed = thrust + rotation - trim_y + trim_x  # Back Right
    
    # Constrain values between 0 and 1023
    fl_speed = max(0, min(1023, fl_speed))
    fr_speed = max(0, min(1023, fr_speed))
    bl_speed = max(0, min(1023, bl_speed))
    br_speed = max(0, min(1023, br_speed))
    
    # Apply motor speeds
    motor1_in1.duty(fl_speed)
    motor2_in3.duty(fr_speed)
    motor3_in1.duty(bl_speed)
    motor4_in3.duty(br_speed)

def main():
    # Setup WiFi access point
    setup_wifi_ap()
    print("Waiting for UDP commands on port 50000...")
    
    while True:
        try:
            # Receive UDP data
            data, addr = udp_socket.recvfrom(64)
            
            # Parse joystick values
            joystick_values = parse_udp_packet(data)
            
            if joystick_values:
                left_x, left_y, right_x, right_y = joystick_values
                control_motors(left_x, left_y, right_x, right_y)
            else:
                # Invalid packet - stop motors
                control_motors(JOYSTICK_MID, JOYSTICK_MID, JOYSTICK_MID, JOYSTICK_MID)
                
        except Exception as e:
            print("Error:", e)
            # If there's an error, stop motors
            control_motors(JOYSTICK_MID, JOYSTICK_MID, JOYSTICK_MID, JOYSTICK_MID)

if __name__ == "__main__":
    main()