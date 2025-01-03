import network
from machine import Pin, PWM
import socket

# Motor control pins setup
motor1A = Pin(5, Pin.OUT)  # D1
motor1B = Pin(4, Pin.OUT)  # D2
motor2A = Pin(14, Pin.OUT)  # D5
motor2B = Pin(12, Pin.OUT)  # D6

# PWM for speed control
pwm1 = PWM(motor1A, freq=1000)
pwm2 = PWM(motor2A, freq=1000)
speed = 512  # Default speed (0-1023)

# Onboard LED setup
led = Pin(2, Pin.OUT)
led.value(0)

# Wi-Fi Access Point
def create_wifi():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid='RC Car', password='12345678')
    print('Access Point Created')
    print('IP Address:', ap.ifconfig()[0])

# Motor control functions
def move_forward():
    motor1B.off()
    motor2B.off()
    pwm1.duty(speed)
    pwm2.duty(speed)

def move_backward():
    motor1A.off()
    motor2A.off()
    motor1B.on()
    motor2B.on()

def turn_left():
    motor1A.off()
    pwm2.duty(speed)

def turn_right():
    motor2A.off()
    pwm1.duty(speed)

def stop_car():
    pwm1.duty(0)
    pwm2.duty(0)
    motor1B.off()
    motor2B.off()

def increase_speed():
    global speed
    speed = min(1023, speed + 100)  # Increment speed, max 1023
    print(f"Speed increased to: {speed}")

def decrease_speed():
    global speed
    speed = max(0, speed - 100)  # Decrement speed, min 0
    print(f"Speed decreased to: {speed}")

# Web server
def web_server():
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(5)
    print("Server is running...")

    while True:
        cl, addr = s.accept()
        request = str(cl.recv(1024))

        # Extract command from the HTTP GET request
        if 'GET /forward' in request:
            move_forward()
        elif 'GET /backward' in request:
            move_backward()
        elif 'GET /left' in request:
            turn_left()
        elif 'GET /right' in request:
            turn_right()
        elif 'GET /stop' in request:
            stop_car()
        elif 'GET /accelerate' in request:
            increase_speed()
        elif 'GET /brake' in request:
            decrease_speed()

        # Enhanced HTML UI
        html = """<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RC Car Control</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            margin: 0;
            padding: 0;
            display: flex;
        }
        .controls {
            display: grid;
            grid-template-areas:
                ". forward ."
                "left stop right"
                ". backward .";
            gap: 10px;
            justify-content: center;
            align-items: center;
            margin: 20px;
        }
        .controls button {
            width: 80px;
            height: 80px;
            font-size: 16px;
            font-weight: bold;
            border: 2px solid #000;
            border-radius: 10px;
            background-color: #f0f0f0;
            margin-left: 20%;
        }
        .controls button:active {
            background-color: #ccc;
        }
        .accelerate-brake {
            margin-top: 20%;
            margin-left: 15%;
            
        }
        .accelerate-brake button {
            width: 120px;
            height: 50px;
            font-size: 16px;
            margin: 0 10px;
            border: 2px solid #000;
            border-radius: 10px;
            background-color: #f0f0f0;
        }
        .accelerate-brake button:active {
            background-color: #ccc;
        }
    </style>
</head>
<body>
    
    <div class="controls">
        <button onclick="sendCommand('/forward')" style="grid-area: forward;">⬆️</button>
        <button onclick="sendCommand('/left')" style="grid-area: left;">⬅️</button>
        <button onclick="sendCommand('/stop')" style="grid-area: stop;">🟥</button>
        <button onclick="sendCommand('/right')" style="grid-area: right;">➡️</button>
        <button onclick="sendCommand('/backward')" style="grid-area: backward;">⬇️</button>
    </div>
    <div class="accelerate-brake">
        <button onclick="sendCommand('/accelerate')">Accelerate</button>
        <button onclick="sendCommand('/brake')">Brake</button>
    </div>
    <script>
        function sendCommand(command) {
            fetch(command).catch(err => console.log("Error:", err));
        }
    </script>
</body>
</html>
"""
        cl.send("HTTP/1.1 200 OK\n")
        cl.send("Content-Type: text/html\n")
        cl.send("Connection: close\n\n")
        cl.sendall(html)
        cl.close()

# Setup function
def setup():
    create_wifi()
    web_server()

setup()


