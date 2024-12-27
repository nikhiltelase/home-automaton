import network
from machine import Pin, PWM
import socket
import json
import time

# Motor control pins setup
try:
    motor1 = PWM(Pin(0))  # Front left
    motor2 = PWM(Pin(1))  # Front right
    motor3 = PWM(Pin(2))  # Back left
    motor4 = PWM(Pin(3))  # Back right
    
    for motor in [motor1, motor2, motor3, motor4]:
        motor.freq(1000)
        motor.duty_u16(0)
except Exception as e:
    print(f"Motor initialization error: {e}")
    raise

led = Pin("LED", Pin.OUT)
led.value(1)

# Global variables with safety limits
MAX_SPEED = 1023
MIN_SPEED = 0
SPEED_STEP = 100
INITIAL_SPEED = 100

speeds = {
    'motor1': INITIAL_SPEED,
    'motor2': INITIAL_SPEED,
    'motor3': INITIAL_SPEED,
    'motor4': INITIAL_SPEED
}
motor_state = "off"
led_state = "on"
last_error = None

def create_wifi():
    try:
        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        ap.config(essid='Pico_Drone', password='12345678')
        
        timeout = 0
        while not ap.active() and timeout < 10:
            time.sleep(1)
            timeout += 1
            
        if not ap.active():
            raise Exception("WiFi AP failed to start")
            
        print(f'SSID: Pico_Drone\nIP: {ap.ifconfig()[0]}')
        return ap
    except Exception as e:
        global last_error
        last_error = f"WiFi error: {str(e)}"
        raise

def validate_speed(speed):
    return max(MIN_SPEED, min(MAX_SPEED, speed))

def apply_motor_speeds():
    if motor_state == "on":
        try:
            motor1.duty_u16(int(speeds['motor1'] * 64))
            motor2.duty_u16(int(speeds['motor2'] * 64))
            motor3.duty_u16(int(speeds['motor3'] * 64))
            motor4.duty_u16(int(speeds['motor4'] * 64))
        except Exception as e:
            global last_error
            last_error = f"Motor control error: {str(e)}"
            emergency_stop()

def emergency_stop():
    try:
        for motor in [motor1, motor2, motor3, motor4]:
            motor.duty_u16(0)
        for key in speeds:
            speeds[key] = 0
        global motor_state
        motor_state = "off"
    except Exception as e:
        global last_error
        last_error = f"Emergency stop error: {str(e)}"

def start_all_motors():
    try:
        global motor_state
        motor_state = "on"
        # Start motors in sequence for stability
        for motor_key in ['motor3', 'motor4', 'motor1', 'motor2']:  # Back motors first
            speeds[motor_key] = INITIAL_SPEED
            time.sleep(0.2)  # Small delay between motor starts
        apply_motor_speeds()
    except Exception as e:
        global last_error
        last_error = f"Start motors error: {str(e)}"
        emergency_stop()

def adjust_speed(motor_num, direction):
    try:
        motor_key = f'motor{motor_num}'
        current_speed = speeds[motor_key]
        new_speed = current_speed + (SPEED_STEP if direction == 'up' else -SPEED_STEP)
        speeds[motor_key] = validate_speed(new_speed)
        apply_motor_speeds()
    except Exception as e:
        global last_error
        last_error = f"Speed adjustment error: {str(e)}"

def web_page():
    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Drone Control</title>
        <style>
            body {{ font-family: Arial; text-align: center; background-color: #f0f0f0; }}
            .emergency {{ 
                background-color: #ff0000;
                color: white;
                font-weight: bold;
                padding: 20px;
                width: 200px;
                margin: 20px auto;
                border-radius: 10px;
                border: none;
                cursor: pointer;
            }}
            .control-panel {{
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: white;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }}
            .motor-group {{
                margin: 20px;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }}
            button {{
                padding: 10px;
                margin: 5px;
                width: 150px;
                border-radius: 5px;
                border: 1px solid #ddd;
                background-color: #fff;
                cursor: pointer;
            }}
            button:hover {{ background-color: #eee; }}
            .status {{ color: #666; }}
        </style>
        <script>
            function updateStatus() {{
                fetch('/status')
                    .then(response => response.json())
                    .then(data => {{
                        document.getElementById('motorState').textContent = data.motor_state;
                        document.getElementById('ledState').textContent = data.led_state;
                        for (let i = 1; i <= 4; i++) {{
                            document.getElementById(`motor${i}Speed`).textContent = data.speeds[`motor${i}`];
                        }}
                        if (data.last_error) {{
                            document.getElementById('errorMsg').textContent = data.last_error;
                        }}
                    }});
            }}
            
            function sendCommand(cmd) {{
                fetch(cmd)
                    .then(response => {{
                        updateStatus();
                    }});
            }}
            
            // Update status every second
            setInterval(updateStatus, 1000);
        </script>
    </head>
    <body onload="updateStatus()">
        <div class="control-panel">
            <h1>Drone Control Panel</h1>
            
            <button class="emergency" onclick="sendCommand('/emergency')">EMERGENCY STOP</button>
            
            <div id="errorMsg" style="color: red;"></div>
            
            <div class="status">
                <p>System Status: <span id="motorState">{motor_state}</span></p>
                <p>LED: <span id="ledState">{led_state}</span></p>
            </div>
            
            <button onclick="sendCommand('/motor/start')">START ALL MOTORS</button>
            <button onclick="sendCommand('/motor/stop')">STOP ALL MOTORS</button>
            
            <div class="motor-group">
                <h2>Motor 1 (Front Left)</h2>
                <p>Speed: <span id="motor1Speed">{speeds['motor1']}</span></p>
                <button onclick="sendCommand('/motor1/speed/up')">Increase</button>
                <button onclick="sendCommand('/motor1/speed/down')">Decrease</button>
            </div>
            
            <div class="motor-group">
                <h2>Motor 2 (Front Right)</h2>
                <p>Speed: <span id="motor2Speed">{speeds['motor2']}</span></p>
                <button onclick="sendCommand('/motor2/speed/up')">Increase</button>
                <button onclick="sendCommand('/motor2/speed/down')">Decrease</button>
            </div>
            
            <div class="motor-group">
                <h2>Motor 3 (Back Left)</h2>
                <p>Speed: <span id="motor3Speed">{speeds['motor3']}</span></p>
                <button onclick="sendCommand('/motor3/speed/up')">Increase</button>
                <button onclick="sendCommand('/motor3/speed/down')">Decrease</button>
            </div>
            
            <div class="motor-group">
                <h2>Motor 4 (Back Right)</h2>
                <p>Speed: <span id="motor4Speed">{speeds['motor4']}</span></p>
                <button onclick="sendCommand('/motor4/speed/up')">Increase</button>
                <button onclick="sendCommand('/motor4/speed/down')">Decrease</button>
            </div>
        </div>
    </body>
    </html>
    """

def handle_request(request):
    global motor_state, led_state, last_error
    try:
        if '/emergency' in request:
            emergency_stop()
        elif '/motor/start' in request:
            start_all_motors()
        elif '/motor/stop' in request:
            emergency_stop()
        elif '/speed' in request:
            parts = request.split('/')
            motor_num = int(parts[-3][-1])
            direction = parts[-1]
            adjust_speed(motor_num, direction)
        elif '/led/on' in request:
            led.value(1)
            led_state = "on"
        elif '/led/off' in request:
            led.value(0)
            led_state = "off"
            
        if '/status' in request:
            status = {
                "motor_state": motor_state,
                "speeds": speeds,
                "led_state": led_state,
                "last_error": last_error
            }
            return 'application/json', json.dumps(status)
        else:
            return 'text/html', web_page()
    except Exception as e:
        last_error = f"Request handling error: {str(e)}"
        return 'text/html', web_page()

def web_server():
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(5)
    
    while True:
        try:
            cl, addr = s.accept()
            request = cl.recv(1024).decode('utf-8')
            content_type, response = handle_request(request)
            
            cl.send(f'HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nConnection: close\r\n\r\n')
            cl.sendall(response)
            cl.close()
        except Exception as e:
            global last_error
            last_error = f"Server error: {str(e)}"
            if 'cl' in locals():
                cl.close()

def main():
    try:
        ap = create_wifi()
        web_server()
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        emergency_stop()

if __name__ == '__main__':
    main()
