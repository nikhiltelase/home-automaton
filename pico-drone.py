import network
from machine import Pin, PWM
import socket

# Motor control pins setup
motor1_in1 = PWM(Pin(4))  # GPIO5 -> Motor 1 IN1
motor2_in3 = PWM(Pin(5))  # GPIO14 -> Motor 2 IN3
motor3_in1 = PWM(Pin(2))  # GPIO4 -> Motor 3 IN1
motor4_in3 = PWM(Pin(3))  # GPIO12 -> Motor 4 IN3

# Set PWM frequency
motor1_in1.freq(1000)
motor2_in3.freq(1000)
motor3_in1.freq(1000)
motor4_in3.freq(1000)

# Onboard LED setup
led = Pin("LED", Pin.OUT)
led.value(1)  # LED ON initially

# Default motor speed and state
speed = 100  # PWM duty cycle (range: 0-1023)
motor_state = "off"  # Motors are initially off
led_state = "on"  # LED is initially on


# Create Wi-Fi Access Point
def create_wifi():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid='Pico_Hotspot', password='12345678')
    print('Access Point Created')
    print('Connect to Wi-Fi with SSID:', ap.config('essid'))
    print('IP Address:', ap.ifconfig()[0])


# Motor control functions
def motor_on():
    global motor_state
    motor1_in1.duty_u16(speed * 64)
    motor2_in3.duty_u16(speed * 64)
    motor3_in1.duty_u16(speed * 64)
    motor4_in3.duty_u16(speed * 64)
    motor_state = "on"


def motor_off():
    global motor_state
    motor1_in1.duty_u16(0)
    motor2_in3.duty_u16(0)
    motor3_in1.duty_u16(0)
    motor4_in3.duty_u16(0)
    motor_state = "off"


def increase_speed():
    global speed
    if speed < 1023:
        speed += 100
        motor_on()


def decrease_speed():
    global speed
    if speed > 0:
        speed -= 100
        motor_on()


# Web page HTML
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
    </head>
    <body>
        <h1>Motor Control</h1>
        <p>LED: <strong>{led_state}</strong></p>
        <button onclick="location.href='/led/on'">LED ON</button>
        <button onclick="location.href='/led/off'">LED OFF</button>
        <br/>
        <p>Status: <strong>{motor_state}</strong></p>
        <button onclick="location.href='/motor/on'">Turn Motors ON</button>
        <button onclick="location.href='/motor/off'">Turn Motors OFF</button>
        <br/>
        <p>Speed: <strong>{speed}</strong></p>
        <button onclick="location.href='/speed/up'">Increase Speed</button>
        <button onclick="location.href='/speed/down'">Decrease Speed</button>
    </body>
    </html>
    """
    return html


# Web server handler
def web_server():
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(5)
    print('Web server running on http://', addr)

    while True:
        cl, addr = s.accept()
        print('Client connected from', addr)
        request = cl.recv(1024).decode('utf-8')
        print('Request:', request)

        # URL handling
        if '/motor/on' in request:
            motor_on()
        elif '/motor/off' in request:
            motor_off()
        elif '/speed/up' in request:
            increase_speed()
        elif '/speed/down' in request:
            decrease_speed()
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


# Setup Wi-Fi and start server
def setup():
    create_wifi()
    web_server()


setup()

