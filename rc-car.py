import network
from machine import Pin, PWM
import socket
import gc
import uasyncio as asyncio

# Motor control pins setup
motor1A = Pin(5, Pin.OUT)  # D1
motor1B = Pin(4, Pin.OUT)  # D2
motor2A = Pin(14, Pin.OUT)  # D5
motor2B = Pin(12, Pin.OUT)  # D6

# PWM for speed control
pwm1 = PWM(motor1A, freq=1000)
pwm2 = PWM(motor2A, freq=1000)
speed = 200  # Starting speed (0-1023)
current_state = 'stop'  # Track current movement state
MAX_SPEED = 1023
SPEED_INCREMENT = 50

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

# Enhanced motor control functions with dynamic speed
def apply_motor_speed():
    if current_state == 'forward':
        motor1B.off()
        motor2B.off()
        pwm1.duty(speed)
        pwm2.duty(speed)
    elif current_state == 'backward':
        motor1A.off()
        motor2A.off()
        motor1B.on()
        motor2B.on()
        pwm1.duty(speed)
        pwm2.duty(speed)
    elif current_state == 'left':
        motor1A.off()
        pwm2.duty(speed)
    elif current_state == 'right':
        motor2A.off()
        pwm1.duty(speed)
    elif current_state == 'boost':
        motor1B.off()
        motor2B.off()
        pwm1.duty(speed)
        pwm2.duty(speed)

def start_boost():
    global current_state, speed
    current_state = 'boost'
    speed = max(200, speed)  # Set minimum starting speed for boost
    apply_motor_speed()
    return speed

def move_forward():
    global current_state
    current_state = 'forward'
    apply_motor_speed()

def move_backward():
    global current_state
    current_state = 'backward'
    apply_motor_speed()

def turn_left():
    global current_state
    current_state = 'left'
    apply_motor_speed()

def turn_right():
    global current_state
    current_state = 'right'
    apply_motor_speed()

def stop_car():
    global current_state
    current_state = 'stop'
    pwm1.duty(0)
    pwm2.duty(0)
    motor1B.off()
    motor2B.off()

def increase_speed():
    global speed
    speed = min(MAX_SPEED, speed + SPEED_INCREMENT)
    apply_motor_speed()
    return speed

def decrease_speed():
    global speed
    speed = max(0, speed - SPEED_INCREMENT * 2)
    apply_motor_speed()
    return speed

# Web server
def web_server():
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(5)
    print("Server is running...")

    while True:
        gc.collect()
        try:
            cl, addr = s.accept()
            request = str(cl.recv(1024))

            response_data = None

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
            elif 'GET /startBoost' in request:
                response_data = {"speed": start_boost()}
            elif 'GET /accelerate' in request:
                response_data = {"speed": increase_speed()}
            elif 'GET /brake' in request:
                response_data = {"speed": decrease_speed()}

            if response_data:
                response = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{str(response_data)}"
                cl.send(response)
            else:
                # Send HTML interface with updated JavaScript
                # [Previous imports and setup code remains the same until the HTML part]

                html = """<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RC Car Game Controller</title>
    <style>
        body {
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: space-between;
            background-color: #1a1a1a;
            color: white;
            font-family: Arial, sans-serif;
            height: 100vh;
            box-sizing: border-box;
            user-select: none;
        }
        .left-controls {
            display: grid;
            grid-template-areas:
                ". . ."
                "left . right"
                ". down .";
            gap: 15px;
            margin-right: 20px;
        }
        .right-controls {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        button {
            width: 80px;
            height: 80px;
            border: none;
            border-radius: 50%;
            background: linear-gradient(145deg, #2e2e2e, #1a1a1a);
            box-shadow: 5px 5px 10px #0d0d0d,
                       -5px -5px 10px #272727;
            color: #fff;
            font-size: 24px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        button:active {
            box-shadow: inset 5px 5px 10px #0d0d0d,
                       inset -5px -5px 10px #272727;
            transform: scale(0.95);
        }
        .speed-button {
            width: 120px;
            height: 120px;
            font-size: 18px;
            font-weight: bold;
            border-radius: 50%;
        }
        #boostBtn {
            background: linear-gradient(145deg, #ff4444, #cc0000);
            position: relative;
            overflow: hidden;
        }
        #boostBtn.active::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255, 255, 255, 0.3);
            animation: pulse 0.5s infinite alternate;
        }
        #brakeBtn {
            background: linear-gradient(145deg, #666666, #333333);
        }
        @keyframes pulse {
            from { opacity: 0.3; }
            to { opacity: 0.6; }
        }
        #speedometer {
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 24px;
            font-weight: bold;
            text-align: center;
            background: rgba(0, 0, 0, 0.5);
            padding: 10px 20px;
            border-radius: 20px;
        }
        .speed-bar {
            width: 200px;
            height: 10px;
            background: #333;
            border-radius: 5px;
            margin-top: 5px;
            overflow: hidden;
        }
        .speed-fill {
            height: 100%;
            width: 0%;
            background: linear-gradient(to right, #ff4444, #ff0000);
            transition: width 0.2s;
        }
    </style>
</head>
<body>
    <div id="speedometer">
        Speed: <span id="speedValue">0</span>%
        <div class="speed-bar">
            <div class="speed-fill" id="speedFill"></div>
        </div>
    </div>
    
    <div class="left-controls">
        <button onclick="sendCommand('left')" style="grid-area: left">⬅️</button>
        <button onclick="sendCommand('right')" style="grid-area: right">➡️</button>
        <button onclick="sendCommand('backward')" style="grid-area: down">⬇️</button>
    </div>

    <div class="right-controls">
        <button class="speed-button" id="boostBtn">BOOST</button>
        <button class="speed-button" id="brakeBtn">BRAKE</button>
    </div>

    <script>
        let currentSpeed = 0;
        const speedDisplay = document.getElementById('speedValue');
        const speedFill = document.getElementById('speedFill');
        const boostBtn = document.getElementById('boostBtn');
        const brakeBtn = document.getElementById('brakeBtn');
        
        function updateSpeedDisplay(speed) {
            currentSpeed = Math.floor((speed / 1023) * 100);
            speedDisplay.textContent = currentSpeed;
            speedFill.style.width = currentSpeed + '%';
        }

        function sendCommand(command) {
            fetch('/' + command)
                .then(response => {
                    if (['accelerate', 'brake', 'startBoost'].includes(command)) {
                        return response.json();
                    }
                })
                .then(data => {
                    if (data && data.speed !== undefined) {
                        updateSpeedDisplay(data.speed);
                    }
                })
                .catch(err => console.log("Error:", err));
        }

        // Enhanced Boost button handling
        let boostInterval;
        let isBoostActive = false;

        function startBoost() {
            if (!isBoostActive) {
                // Initial boost start
                sendCommand('startBoost');
            }
            isBoostActive = true;
            boostBtn.classList.add('active');
            // Continue increasing speed while held
            boostInterval = setInterval(() => {
                sendCommand('accelerate');
            }, 100);
        }

        function stopBoost() {
            isBoostActive = false;
            boostBtn.classList.remove('active');
            clearInterval(boostInterval);
            sendCommand('stop');
        }

        // Mouse events
        boostBtn.addEventListener('mousedown', startBoost);
        boostBtn.addEventListener('mouseup', stopBoost);
        boostBtn.addEventListener('mouseleave', stopBoost);

        // Touch events
        boostBtn.addEventListener('touchstart', (e) => {
            e.preventDefault();
            startBoost();
        });
        boostBtn.addEventListener('touchend', (e) => {
            e.preventDefault();
            stopBoost();
        });

        // Brake button handling
        let brakeInterval;
        brakeBtn.addEventListener('mousedown', () => {
            brakeInterval = setInterval(() => {
                sendCommand('brake');
            }, 100);
        });
        brakeBtn.addEventListener('mouseup', () => clearInterval(brakeInterval));
        brakeBtn.addEventListener('mouseleave', () => clearInterval(brakeInterval));

        brakeBtn.addEventListener('touchstart', (e) => {
            e.preventDefault();
            brakeInterval = setInterval(() => {
                sendCommand('brake');
            }, 100);
        });
        brakeBtn.addEventListener('touchend', (e) => {
            e.preventDefault();
            clearInterval(brakeInterval);
        });
    </script>
</body>
</html>
"""
                cl.send("HTTP/1.1 200 OK\r\n")
                cl.send("Content-Type: text/html\r\n")
                cl.send("Connection: close\r\n\r\n")
                cl.sendall(html)
            
            cl.close()
        except Exception as e:
            print("Connection handling error:", e)

# Setup function
def setup():
    create_wifi()
    web_server()

setup()
