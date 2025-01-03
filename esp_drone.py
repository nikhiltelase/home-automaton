import network

from machine import Pin, PWM

import socket

import json



# Motor control pins setup

motor1_in1 = PWM(Pin(5), freq=1000)   

motor2_in3 = PWM(Pin(14), freq=1000)  

motor3_in1 = PWM(Pin(4), freq=1000)   

motor4_in3 = PWM(Pin(12), freq=1000)  



# Onboard LED setup

led = Pin(2, Pin.OUT)

led.value(0)



motor_speeds = {

    "motor1": 100,

    "motor2": 100,

    "motor3": 100,

    "motor4": 100

}

motors_state = "off"

led_state = "on"



def create_wifi():

    ap = network.WLAN(network.AP_IF)

    ap.active(True)

    ap.config(essid='ESP_Hotspot', password='12345678')

    print('Access Point Created')

    print('IP Address:', ap.ifconfig()[0])



def motors_on():

    global motors_state

    motor1_in1.duty(motor_speeds["motor1"])

    motor2_in3.duty(motor_speeds["motor2"])

    motor3_in1.duty(motor_speeds["motor3"])

    motor4_in3.duty(motor_speeds["motor4"])

    motors_state = "on"



def motors_off():

    global motors_state

    motor1_in1.duty(0)

    motor2_in3.duty(0)

    motor3_in1.duty(0)

    motor4_in3.duty(0)

    motors_state = "off"



def adjust_motor_speed(motor_num, new_speed):

    global motor_speeds

    try:

        new_speed = max(0, min(1023, int(new_speed)))

        motor_speeds[f"motor{motor_num}"] = new_speed

        if motors_state == "on":

            if motor_num == 1: motor1_in1.duty(new_speed)

            elif motor_num == 2: motor2_in3.duty(new_speed)

            elif motor_num == 3: motor3_in1.duty(new_speed)

            elif motor_num == 4: motor4_in3.duty(new_speed)

        return True

    except:

        return False



def adjust_all_speeds(increment):

    for i in range(1, 5):

        current_speed = motor_speeds[f"motor{i}"]

        new_speed = max(0, min(1023, current_speed + increment))

        adjust_motor_speed(i, new_speed)



def web_page():

    html = f"""

    <html>

    <head>

        <meta name="viewport" content="width=device-width, initial-scale=1">

        <title>Motor Control</title>

        <style>

            body {{ font-family: Arial, sans-serif; text-align: center; }}

            button {{ padding: 10px; margin: 5px; width: 150px; }}

            .motor-control {{ 

                border: 1px solid #ccc; 

                margin: 10px; 

                padding: 10px;

                border-radius: 5px;

            }}

            .speed-input {{

                width: 80px;

                margin: 5px;

                padding: 8px;

                font-size: 16px;

                text-align: center;

            }}

            .speed-label {{

                font-weight: bold;

                margin-right: 10px;

            }}

            .set-button {{

                padding: 5px 15px;

                margin-left: 10px;

                background-color: #4CAF50;

                color: white;

                border: none;

                border-radius: 4px;

                cursor: pointer;

            }}

        </style>

        <script>

            function updateStatus() {{

                fetch('/status')

                .then(response => response.json())

                .then(data => {{

                    document.getElementById('motorsState').innerText = data.motors_state;

                    document.getElementById('ledStatus').innerText = data.led_status;

                    

                    // Only update displayed speeds, not input values

                    for (let i = 1; i <= 4; i++) {{

                        document.getElementById(`motor${{i}}Speed`).innerText = data[`motor${{i}}_speed`];

                    }}

                }});

            }}

            

            function controlMotors(action) {{

                fetch('/motors/' + action)

                .then(() => updateStatus());

            }}



            function controlLED(action) {{

                fetch('/led/' + action)

                .then(() => updateStatus());

            }}



            function setSpeed(motorNum) {{

                const input = document.getElementById(`speed${{motorNum}}`);

                let speed = parseInt(input.value) || 0;

                

                // Clamp value between 0 and 1023

                speed = Math.max(0, Math.min(1023, speed));

                input.value = speed;

                

                fetch(`/adjust/${{motorNum}}/${{speed}}`)

                .then(response => updateStatus());

            }}



            function adjustAllSpeeds(increment) {{

                fetch(`/adjust_all/${{increment}}`)

                .then(() => updateStatus());

            }}



            // Initialize updates

            document.addEventListener('DOMContentLoaded', function() {{

                updateStatus();

                setInterval(updateStatus, 500);

            }});

        </script>

    </head>

    <body>

        <h1>Motor Control</h1>

        

        <div class="motor-control">

            <p>LED Status: <span id="ledStatus">{led_state}</span></p>

            <button onclick="controlLED('on')">LED ON</button>

            <button onclick="controlLED('off')">LED OFF</button>

        </div>



        <div class="motor-control">

            <p>Motors State: <span id="motorsState">{motors_state}</span></p>

            <button onclick="controlMotors('on')">All Motors ON</button>

            <button onclick="controlMotors('off')">All Motors OFF</button>

            <br>

            <button onclick="adjustAllSpeeds(100)">Increase All</button>

            <button onclick="adjustAllSpeeds(-100)">Decrease All</button>

        </div>



        <div class="motor-control">

            <h3>Motor Speeds (0-1023)</h3>

            <div>

                <span class="speed-label">Motor 1:</span>

                <input type="number" id="speed1" class="speed-input" min="0" max="1023" value="0">

                <button class="set-button" onclick="setSpeed(1)">Set</button>

                <span>Current: <span id="motor1Speed">{motor_speeds['motor1']}</span></span>

            </div>

            <br>

            <div>

                <span class="speed-label">Motor 2:</span>

                <input type="number" id="speed2" class="speed-input" min="0" max="1023" value="0">

                <button class="set-button" onclick="setSpeed(2)">Set</button>

                <span>Current: <span id="motor2Speed">{motor_speeds['motor2']}</span></span>

            </div>

            <br>

            <div>

                <span class="speed-label">Motor 3:</span>

                <input type="number" id="speed3" class="speed-input" min="0" max="1023" value="0">

                <button class="set-button" onclick="setSpeed(3)">Set</button>

                <span>Current: <span id="motor3Speed">{motor_speeds['motor3']}</span></span>

            </div>

            <br>

            <div>

                <span class="speed-label">Motor 4:</span>

                <input type="number" id="speed4" class="speed-input" min="0" max="1023" value="0">

                <button class="set-button" onclick="setSpeed(4)">Set</button>

                <span>Current: <span id="motor4Speed">{motor_speeds['motor4']}</span></span>

            </div>

        </div>

    </body>

    </html>

    """

    return html



def get_status_json():

    return json.dumps({

        "motors_state": motors_state,

        "led_status": led_state,

        "motor1_speed": motor_speeds["motor1"],

        "motor2_speed": motor_speeds["motor2"],

        "motor3_speed": motor_speeds["motor3"],

        "motor4_speed": motor_speeds["motor4"]

    })



def web_server():

    global led_state

    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]

    s = socket.socket()

    s.bind(addr)

    s.listen(5)



    while True:

        cl, addr = s.accept()

        try:

            request = str(cl.recv(1024))



            if '/motors/on' in request:

                motors_on()

            elif '/motors/off' in request:

                motors_off()

            elif '/adjust/' in request:

                parts = request.split('/adjust/')[1].split('/')

                motor_num = int(parts[0])

                speed = int(parts[1].split(' ')[0])

                adjust_motor_speed(motor_num, speed)

            elif '/adjust_all/' in request:

                increment = int(request.split('/adjust_all/')[1].split(' ')[0])

                adjust_all_speeds(increment)

            elif '/led/on' in request:

                led.value(0)

                led_state = 'on'

            elif '/led/off' in request:

                led.value(1)

                led_state = 'off'



            if '/status' in request:

                cl.send('HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n')

                cl.sendall(get_status_json())

            else:

                cl.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n')

                cl.sendall(web_page())



        except Exception as e:

            print('Error:', e)

        finally:

            cl.close()



def setup():

    create_wifi()

    web_server()



setup()