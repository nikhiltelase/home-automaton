import network
from machine import Pin
import socket 

led = Pin(2, Pin.OUT)
led.value(0)  # Start with LED ON

# Motor control pins
motor1A = Pin(5, Pin.OUT)  # D1
motor1B = Pin(4, Pin.OUT)  # D2
motor2A = Pin(14, Pin.OUT) # D5
motor2B = Pin(12, Pin.OUT) # D6

# Functions to control car movement
def move_forward():
    motor1A.on()
    motor1B.off()
    motor2A.on()
    motor2B.off()

def move_backward():
    motor1A.off()
    motor1B.on()
    motor2A.off()
    motor2B.on()

def turn_left():
    motor1A.off()
    motor1B.on()
    motor2A.on()
    motor2B.off()

def turn_right():
    motor1A.on()
    motor1B.off()
    motor2A.off()
    motor2B.on()

def stop_car():
    motor1A.off()
    motor1B.off()
    motor2A.off()
    motor2B.off()


def create_wifi():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid="Car", password="12345678")
    print("Access Point Created")

# Web server
def start_server():
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(5)
    print("Server is running...")
    while True:
        client, addr = s.accept()
        print('Client connected from', addr)
        request = client.recv(1024)
        print("Request: ", request)
        
        # Extract command from the HTTP GET request
        if '/forward' in request:
            move_forward()
        elif '/backward' in request:
            move_backward()
        elif '/left' in request:
            turn_left()
        elif '/right' in request:
            turn_right()
        elif '/stop' in request:
            stop_car()

        # Send HTML response
        html = """<!DOCTYPE html>
<html>
  <head>
    <title>RC Car Control</title>
    <style>
      body {
       padding: 20px;
      }
      h1 {
        text-align: center;
      }
      button {
        display: block;
        margin: auto;
        margin-top: 20px;
        padding: 10px 20px;
        font-size: 20px;
        cursor: pointer;
      }
    </style>
  </head>
  <body>
    
    <div style="display: flex; justify-content: space-between">
      <div style="display: flex; gap: 2%;">
        <button onclick="fetch('/left')">Left</button
        ><button onclick="fetch('/right')">Right</button>
      </div>
        <button onclick="fetch('/stop')">Stop</button>
      <div class="display: flex">
        <button onclick="fetch('/forward')">Forward</button>
        <button onclick="fetch('/backward')">Backward</button>
    </div>
    <script>
      function fetch(url) {
        var xhttp = new XMLHttpRequest();
        xhttp.open("GET", url, true);
        xhttp.send();
      }
    </script>
  </body>
</html>
"""
        client.send("HTTP/1.1 200 OK\n")
        client.send("Content-Type: text/html\n")
        client.send("Connection: close\n\n")
        client.sendall(html)
        client.close()

# Main
try:
    create_wifi()
    start_server()
except KeyboardInterrupt:
    stop_car()
    print("Server stopped.")

