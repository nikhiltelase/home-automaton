import network
from machine import Pin, PWM
import socket

# Motor control pins setup
motor1 = PWM(Pin(0))
motor2 = PWM(Pin(1))
motor3 = PWM(Pin(2))
motor4 = PWM(Pin(3))

for motor in [motor1, motor2, motor3, motor4]:
    motor.freq(1000)

led = Pin("LED", Pin.OUT)
led.value(1)

# Global variables
speed1 = speed2 = speed3 = speed4 = 100
motor_state = "off"
led_state = "on"

def create_wifi():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid='Pico_Hotspot', password='12345678')
    print('Access Point Created')
    print('SSID:', ap.config('essid'))
    print('IP:', ap.ifconfig()[0])

def emergency_stop():
    global speed1, speed2, speed3, speed4, motor_state
    speed1 = speed2 = speed3 = speed4 = 0
    motor1.duty_u16(0)
    motor2.duty_u16(0)
    motor3.duty_u16(0)
    motor4.duty_u16(0)
    motor_state = "off"

def motor_on():
    global motor_state
    motor1.duty_u16(speed1 * 64)
    motor2.duty_u16(speed2 * 64)
    motor3.duty_u16(speed3 * 64)
    motor4.duty_u16(speed4 * 64)
    motor_state = "on"

def motor_off():
    global motor_state
    motor1.duty_u16(0)
    motor2.duty_u16(0)
    motor3.duty_u16(0)
    motor4.duty_u16(0)
    motor_state = "off"

def increase_speed(motor):
    global speed1, speed2, speed3, speed4
    speed_map = {1: 'speed1', 2: 'speed2', 3: 'speed3', 4: 'speed4'}
    if motor in speed_map and globals()[speed_map[motor]] < 1023:
        globals()[speed_map[motor]] += 100
    motor_on()

def decrease_speed(motor):
    global speed1, speed2, speed3, speed4
    speed_map = {1: 'speed1', 2: 'speed2', 3: 'speed3', 4: 'speed4'}
    if motor in speed_map and globals()[speed_map[motor]] > 0:
        globals()[speed_map[motor]] -= 100
    motor_on()

def web_page():
    html = f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Motor Control</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; }}
            button {{ padding: 10px; margin: 5px; width: 150px; }}
            .emergency {{ 
                background-color: red;
                color: white;
                font-weight: bold;
                padding: 20px;
                width: 200px;
                margin: 20px auto;
                border-radius: 10px;
            }}
            h1 {{ color: #333; }}
            p {{ font-size: 18px; }}
        </style>
    </head>
    <body>
        <h1>Motor Control</h1>
        <button class="emergency" onclick="location.href='/emergency'">EMERGENCY STOP</button>
        <p>LED: <strong>{led_state}</strong></p>
        <button onclick="location.href='/led/on'">LED ON</button>
        <button onclick="location.href='/led/off'">LED OFF</button>
        <br/>
        <button onclick="location.href='/motor/on'">START ALL MOTORS</button>
        <button onclick="location.href='/motor/off'">STOP ALL MOTORS</button>
        <br/>
        <h2>Motor 1 Speed: {speed1}</h2>
        <button onclick="location.href='/motor1/speed/up'">Increase Speed</button>
        <button onclick="location.href='/motor1/speed/down'">Decrease Speed</button>
        <br/>
        <h2>Motor 2 Speed: {speed2}</h2>
        <button onclick="location.href='/motor2/speed/up'">Increase Speed</button>
        <button onclick="location.href='/motor2/speed/down'">Decrease Speed</button>
        <br/>
        <h2>Motor 3 Speed: {speed3}</h2>
        <button onclick="location.href='/motor3/speed/up'">Increase Speed</button>
        <button onclick="location.href='/motor3/speed/down'">Decrease Speed</button>
        <br/>
        <h2>Motor 4 Speed: {speed4}</h2>
        <button onclick="location.href='/motor4/speed/up'">Increase Speed</button>
        <button onclick="location.href='/motor4/speed/down'">Decrease Speed</button>
    </body>
    </html>
    """
    return html

def web_server():
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(5)

    while True:
        cl, addr = s.accept()
        request = cl.recv(1024).decode('utf-8')

        if '/emergency' in request:
            emergency_stop()
        elif '/motor1/speed/up' in request:
            increase_speed(1)
        elif '/motor1/speed/down' in request:
            decrease_speed(1)
        elif '/motor2/speed/up' in request:
            increase_speed(2)
        elif '/motor2/speed/down' in request:
            decrease_speed(2)
        elif '/motor3/speed/up' in request:
            increase_speed(3)
        elif '/motor3/speed/down' in request:
            decrease_speed(3)
        elif '/motor4/speed/up' in request:
            increase_speed(4)
        elif '/motor4/speed/down' in request:
            decrease_speed(4)
        elif '/motor/on' in request:
            motor_on()
        elif '/motor/off' in request:
            motor_off()
        elif '/led/on' in request:
            led.value(1)
            led_state = "on"
        elif '/led/off' in request:
            led.value(0)
            led_state = "off"

        response = web_page()
        cl.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n')
        cl.sendall(response)
        cl.close()

def setup():
    create_wifi()
    web_server()

setup()