import network
import socket
from machine import Pin

# Set up Access Point
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid='ESP_Hotspot', password='12345678')

print('Access Point Created')
print('Connect to Wi-Fi with SSID:', ap.config('essid'))
print('IP Address:', ap.ifconfig()[0])

# Set up the LED (using GPIO 2, adjust based on your board)
led = Pin(2, Pin.OUT)
led.value(1)

# Create a web server
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)

print('Listening on', addr)

while True:
    cl, addr = s.accept()
    print('Client connected from', addr)
    request = cl.recv(1024)
    request = str(request)

    # Handle requests to control the LED
    if 'GET /led/on' in request:
        led.value(0)  # Turn LED on
    elif 'GET /led/off' in request:
        led.value(1)  # Turn LED off

    # Determine the current LED status
    if led.value() == 0:
        status = 'on'
    else:
        status = 'off'

    # Prepare the HTML response
    response = f"""HTTP/1.1 200 OK
    Content-Type: text/html

    <html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Light Control</title>
    <style>
      body {{
        font-family: Arial, sans-serif;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        height: 100vh;
        margin: 0;
        background-color: #f4f4f9;
      }}
      h1 {{
        color: #333;
      }}
      button {{
        background-color: #007bff;
        color: white;
        padding: 10px 20px;
        margin: 10px;
        border: none;
        border-radius: 5px;
        font-size: 16px;
        cursor: pointer;
      }}
      button:hover {{
        background-color: #0056b3;
      }}
    </style>
  </head>
  <body>
    <h1>Control Your Light</h1>
    <h2>Light is {status}</h2>
    <a href="/led/on"><button id="lightOn">Turn On</button></a>
    <a href="/led/off"><button id="lightOff">Turn Off</button></a>
  </body>
</html>
    """
    # Send the response back to the client
    cl.send(response)
    cl.close()

