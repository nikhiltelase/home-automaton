import network
from machine import Pin, PWM
import socket

# Motor control pins setup
motor1_in1 = PWM(Pin(5), freq=1000)  # D1 -> Motor 1 IN1
motor2_in3 = PWM(Pin(14), freq=1000)  # D5 -> Motor 3 IN3
motor3_in1 = PWM(Pin(4), freq=1000)  # D2 -> Motor 2 IN1
motor4_in3 = PWM(Pin(12), freq=1000)  # D6 -> Motor 4 IN3

# Onboard LED setup (GPIO2 -> D4)
led = Pin(2, Pin.OUT)
led.value(0)  # led on when power the board

# Set default motor speed and state
speed = 100  # PWM duty cycle (range: 0-1023)
motor_state = "off"  # Motors are initially off
led_state = "on"  # LED is initially on


def create_wifi():
    # Set up Access Point (AP mode)
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid='ESP_Hotspot', password='12345678')
    print('Access Point Created')
    print('Connect to Wi-Fi with SSID:', ap.config('essid'))
    print('IP Address:', ap.ifconfig()[0])


# Motor control functions
def motor_on():
    global motor_state
    motor1_in1.duty(speed)
    motor2_in3.duty(speed)
    motor3_in1.duty(speed)
    motor4_in3.duty(speed)
    motor_state = "on"


def motor_off():
    global motor_state, speed
    speed = 100
    motor1_in1.duty(0)
    motor2_in3.duty(0)
    motor3_in1.duty(0)
    motor4_in3.duty(0)
    motor_state = "off"


def increase_speed():
    global speed
    if speed < 923:
        speed += 100
    else:
        speed = 1023  # Ensure it doesn't exceed max
    motor_on()


def decrease_speed():
    global speed
    if speed > 100:
        speed -= 100
    else:
        speed = 0  # Ensure it doesn't go below 0
    motor_on()


# HTML page for web interface with JavaScript
def web_page():
    global led_state
    html = f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Motor Control</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; }}
            button {{ padding: 10px; margin: 5px; width: 150px; }}
            h1 {{ color: #333; }}
            p {{ font-size: 18px; }}
          </style>
        <script>
            let motorSpeed = {speed};
            let motorState = '{motor_state}';

            function updateStatus() {{
                fetch('/status')
                .then(response => response.json())
                .then(data => {{
                    document.getElementById('status').innerText = data.status;
                    document.getElementById('speed').innerText = data.speed;
                    document.getElementById('ledStatus').innerText = data.led_status;
                    motorSpeed = data.speed;  // Update motorSpeed from server data
                    motorState = data.status;  // Update motorState from server data
                }});
            }}
            
            function controlMotor(action) {{
                fetch('/motor/' + action)
                .then(() => {{
                    updateStatus(); // Update the status after controlling motor
                }});
            }}

            function controlLED(action) {{
                fetch('/led/' + action)
                .then(() => {{
                    updateStatus(); // Update the status after controlling LED
                }});
            }}

            function changeSpeed(action, increment) {{
                if (motorState === 'on') {{
                     if (motorSpeed + increment <= 1023 && motorSpeed + increment >= 0) {{
                        fetch('/speed/' + action)
                        .then(() => {{
                            motorSpeed += increment;
                            document.getElementById('speed').innerText = motorSpeed;
                        }});
                    }}
                }} else {{
                        alert("Motor is OFF! Turn it ON first.");
                }}
                
            }}
        </script>
    </head>
    <body onload="updateStatus()">
        <h1>Motor Control</h1>
        <p>LED: <span id="ledStatus">{led_state}</span></p>
        <button onclick="controlLED('on')">LED ON</button>
        <button onclick="controlLED('off')">LED OFF</button>
        <br/>
        <p>Status: <span id="status">{motor_state}</span></p>
        <button onclick="controlMotor('on')">Turn Motors ON</button>
        <button onclick="controlMotor('off')">Turn Motors OFF</button>
        <br/>
        <p>Speed: <span id="speed">{speed}</span></p>
        <button onclick="changeSpeed('up', 100)">Increase Speed</button>
        <button onclick="changeSpeed('down', -100)">Decrease Speed</button>
    </body>
    </html>
    """
    return html


def get_status_json():
    # Send current status as JSON
    status = {
        "status": motor_state,
        "speed": speed,
        "led_status": led_state
    }
    return status


# Web server handler
def web_server():
    global led_state
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(5)

    while True:
        cl, addr = s.accept()  # Accept incoming connection
        print('Client connected from', addr)
        try:
            request = cl.recv(1024)  # Receive the client's request
            request = str(request)

            # Motor control logic based on URL parameters
            if '/motor/on' in request:
                motor_on()
            elif '/motor/off' in request:
                motor_off()
            elif '/speed/up' in request:
                increase_speed()
            elif '/speed/down' in request:
                decrease_speed()
            elif '/led/on' in request:
                led.value(0)  # LED ON (active low)
                led_state = 'on'
            elif '/led/off' in request:
                led.value(1)  # LED OFF (inactive high)
                led_state = 'off'

            # Send back the HTML response
                # Parse request path
            if '/status' in request:
                response = get_status_json()
                cl.send('HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n')
                cl.sendall(str(response).replace("'", '"'))  # Send JSON response
            else:
                response = web_page()
                cl.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n')
                cl.sendall(response)
        except OSError as e:
            print('Error:', e)
        finally:
            cl.close()


def setup():
    create_wifi()
    web_server()


setup()
