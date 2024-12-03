import network
import socket
from machine import Pin

# Setup LED (GPIO 2) AND relays (GPIO 5 and GPIO 4)
led = Pin(2, Pin.OUT)
relay1 = Pin(5, Pin.OUT)  # GPIO 5 for Relay 1
relay2 = Pin(4, Pin.OUT)  # GPIO 4 for Relay 2

# Initialize relays and LED states
relay1.value(0)  # Start with relay OFF
relay2.value(0)
led.value(0)  # Start with LED ON

# Set up Access Point (AP mode)
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid='ESP_Hotspot', password='12345678')

print('Access Point Created')
print('Connect to Wi-Fi with SSID:', ap.config('essid'))
print('IP Address:', ap.ifconfig()[0])


# Non-blocking web page creation
def web_page():
    html = """<html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>ESP8266 Control</title>
          <style>
            body {{ font-family: Arial, sans-serif; text-align: center; }}
            button {{ padding: 10px; margin: 5px; width: 150px; }}
            h1 {{ color: #333; }}
            p {{ font-size: 18px; }}
          </style>
        <script>
            // Function to send requests to control the relays and LED
            function sendRequest(command) {
                var xhttp = new XMLHttpRequest();
                xhttp.open("GET", command, true);
                xhttp.send();
            }

            // Function to periodically refresh the status of the relays and LED
            setInterval(function() {
                getStatus();
            }, 2000);  // Refresh every 2 seconds

            function getStatus() {
                var xhttp = new XMLHttpRequest();
                xhttp.onreadystatechange = function() {
                    if (this.readyState == 4 && this.status == 200) {
                        var status = JSON.parse(this.responseText);
                        document.getElementById("led_status").innerHTML = status.led_status;
                        document.getElementById("relay1_status").innerHTML = status.relay1_status;
                        document.getElementById("relay2_status").innerHTML = status.relay2_status;
                    }
                };
                xhttp.open("GET", "/status", true);
                xhttp.send();
            }
        </script>
    </head>
    <body onload="getStatus()">
        <div class="container">
            <h1>ESP8266 Relay and LED Control</h1>

            <p class="status">LED Status: <strong id="led_status">Loading...</strong></p>
            <button onclick="sendRequest('/led/on')">Turn LED ON</button>
            <button onclick="sendRequest('/led/off')">Turn LED OFF</button>
            <br><br>
            <hr>
            <p class="status">Relay 1 Status: <strong id="relay1_status">Loading...</strong></p>
            <button onclick="sendRequest('/relay1/on')">Turn Relay 1 ON</button>
            <button onclick="sendRequest('/relay1/off')">Turn Relay 1 OFF</button>
            <br><br>
            <hr>
            <p class="status">Relay 2 Status: <strong id="relay2_status">Loading...</strong></p>
            <button onclick="sendRequest('/relay2/on')">Turn Relay 2 ON</button>
            <button onclick="sendRequest('/relay2/off')">Turn Relay 2 OFF</button>
        </div>
    </body>
    </html>"""
    return html


# API to return the status of relays and LED
def get_status_json():
    status = {
        "led_status": "ON" if led.value() == 0 else "OFF",
        "relay1_status": "ON" if relay1.value() else "OFF",
        "relay2_status": "ON" if relay2.value() else "OFF"
    }
    return status


# Web server setup
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(5)

print('Listening on', addr)

# Main loop to handle client connections
while True:
    cl, addr = s.accept()
    print('Client connected from', addr)
    try:
        request = cl.recv(1024)
        request = str(request)

        # Handle LED control
        if '/led/on' in request:
            led.value(0)  # Turn LED ON (active-low)
        elif '/led/off' in request:
            led.value(1)  # Turn LED OFF

        # Handle Relay 1 control
        if '/relay1/on' in request:
            relay1.value(1)  # Turn Relay 1 ON
        elif '/relay1/off' in request:
            relay1.value(0)  # Turn Relay 1 OFF

        # Handle Relay 2 control
        if '/relay2/on' in request:
            relay2.value(1)  # Turn Relay 2 ON
        elif '/relay2/off' in request:
            relay2.value(0)  # Turn Relay 2 OFF

        # Serve the main web page
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
