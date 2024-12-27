import machine
import network
import socket
import time
import math

# Constants
I2C_CLK_FREQ = 400000  # 400kHz
IMU_ADDRESS = 0x68  # Address for MPU6050 IMU sensor
APSSID = "PicoW"
APPSW = "password"
UDP_PKT_MAX_SIZE = 16
localPort = 8888

# PID gain and limit settings
pid_p_gain_roll = 2.05
pid_i_gain_roll = 0.013
pid_d_gain_roll = 11.0
pid_max_roll = 300

pid_p_gain_pitch = pid_p_gain_roll
pid_i_gain_pitch = pid_i_gain_roll
pid_d_gain_pitch = pid_d_gain_roll
pid_max_pitch = pid_max_roll

pid_p_gain_yaw = 8.5
pid_i_gain_yaw = 0.005
pid_d_gain_yaw = 0.0
pid_max_yaw = 300

auto_level = True

# Global variables
receiver_input_channel = [0, 0, 0, 0]
gyro_axis_cal = [0, 0, 0, 0]
gyro_axis = [0, 0, 0, 0]
acc_axis = [0, 0, 0, 0]
angle_pitch = 0
angle_roll = 0
gyro_angles_set = False

# Setup I2C
i2c = machine.I2C(0, scl=machine.Pin(22), sda=machine.Pin(21), freq=I2C_CLK_FREQ)

# Setup WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(APSSID, APPSW)

while not wlan.isconnected():
    time.sleep(0.5)

# Setup UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', localPort))

# Setup motors
motors = [machine.PWM(machine.Pin(pin), freq=500, duty=0) for pin in [18, 13, 28, 1]]

# Function to read gyro data
def read_gyro():
    global gyro_axis, acc_axis
    data = i2c.readfrom_mem(IMU_ADDRESS, 0x3B, 14)
    acc_axis[1] = int.from_bytes(data[0:2], 'big')
    acc_axis[2] = int.from_bytes(data[2:4], 'big')
    acc_axis[3] = int.from_bytes(data[4:6], 'big')
    gyro_axis[1] = int.from_bytes(data[8:10], 'big')
    gyro_axis[2] = int.from_bytes(data[10:12], 'big')
    gyro_axis[3] = int.from_bytes(data[12:14], 'big')

# Function to set gyro registers
def set_gyro_registers():
    i2c.writeto_mem(IMU_ADDRESS, 0x6B, b'\x00')
    i2c.writeto_mem(IMU_ADDRESS, 0x1B, b'\x08')
    i2c.writeto_mem(IMU_ADDRESS, 0x1C, b'\x10')
    i2c.writeto_mem(IMU_ADDRESS, 0x1A, b'\x03')

# Function to calculate PID
def calculate_pid():
    global pid_output_roll, pid_output_pitch, pid_output_yaw
    pid_error_temp = 0
    pid_i_mem_roll = 0
    pid_last_roll_d_error = 0
    pid_output_roll = 0

    pid_error_temp = receiver_input_channel[0] - angle_roll
    pid_i_mem_roll += pid_i_gain_roll * pid_error_temp
    if pid_i_mem_roll > pid_max_roll:
        pid_i_mem_roll = pid_max_roll
    elif pid_i_mem_roll < -pid_max_roll:
        pid_i_mem_roll = -pid_max_roll

    pid_output_roll = pid_p_gain_roll * pid_error_temp + pid_i_mem_roll + pid_d_gain_roll * (pid_error_temp - pid_last_roll_d_error)
    if pid_output_roll > pid_max_roll:
        pid_output_roll = pid_max_roll
    elif pid_output_roll < -pid_max_roll:
        pid_output_roll = -pid_max_roll

    pid_last_roll_d_error = pid_error_temp

    pid_error_temp = receiver_input_channel[1] - angle_pitch
    pid_i_mem_pitch = 0
    pid_last_pitch_d_error = 0
    pid_output_pitch = 0

    pid_i_mem_pitch += pid_i_gain_pitch * pid_error_temp
    if pid_i_mem_pitch > pid_max_pitch:
        pid_i_mem_pitch = pid_max_pitch
    elif pid_i_mem_pitch < -pid_max_pitch:
        pid_i_mem_pitch = -pid_max_pitch

    pid_output_pitch = pid_p_gain_pitch * pid_error_temp + pid_i_mem_pitch + pid_d_gain_pitch * (pid_error_temp - pid_last_pitch_d_error)
    if pid_output_pitch > pid_max_pitch:
        pid_output_pitch = pid_max_pitch
    elif pid_output_pitch < -pid_max_pitch:
        pid_output_pitch = -pid_max_pitch

    pid_last_pitch_d_error = pid_error_temp

    pid_error_temp = receiver_input_channel[2] - gyro_axis[3]
    pid_i_mem_yaw = 0
    pid_last_yaw_d_error = 0
    pid_output_yaw = 0

    pid_i_mem_yaw += pid_i_gain_yaw * pid_error_temp
    if pid_i_mem_yaw > pid_max_yaw:
        pid_i_mem_yaw = pid_max_yaw
    elif pid_i_mem_yaw < -pid_max_yaw:
        pid_i_mem_yaw = -pid_max_yaw

    pid_output_yaw = pid_p_gain_yaw * pid_error_temp + pid_i_mem_yaw + pid_d_gain_yaw * (pid_error_temp - pid_last_yaw_d_error)
    if pid_output_yaw > pid_max_yaw:
        pid_output_yaw = pid_max_yaw
    elif pid_output_yaw < -pid_max_yaw:
        pid_output_yaw = -pid_max_yaw

    pid_last_yaw_d_error = pid_error_temp

# Setup routine
def setup():
    global gyro_axis_cal
    set_gyro_registers()
    for _ in range(2000):
        read_gyro()
        gyro_axis_cal[1] += gyro_axis[1]
        gyro_axis_cal[2] += gyro_axis[2]
        gyro_axis_cal[3] += gyro_axis[3]
        time.sleep(0.004)
    gyro_axis_cal = [x / 2000 for x in gyro_axis_cal]

# Main loop
def loop():
    global angle_pitch, angle_roll, gyro_angles_set
    while True:
        data, _ = sock.recvfrom(UDP_PKT_MAX_SIZE)
        if data:
            receiver_input_channel[0] = int.from_bytes(data[0:2], 'big')
            receiver_input_channel[1] = int.from_bytes(data[2:4], 'big')
            receiver_input_channel[2] = int.from_bytes(data[4:6], 'big')
            receiver_input_channel[3] = int.from_bytes(data[6:8], 'big')

        read_gyro()
        # Calculate angles from gyro data
        angle_pitch += gyro_axis[1] * 0.0000611
        angle_roll += gyro_axis[2] * 0.0000611

        # Compensate for drift with accelerometer data
        acc_total_vector = math.sqrt((acc_axis[1] * acc_axis[1]) + (acc_axis[2] * acc_axis[2]) + (acc_axis[3] * acc_axis[3]))
        angle_pitch_acc = math.asin(acc_axis[2] / acc_total_vector) * 57.296
        angle_roll_acc = math.asin(acc_axis[1] / acc_total_vector) * -57.296

        if gyro_angles_set:
            angle_pitch = angle_pitch * 0.9996 + angle_pitch_acc * 0.0004
            angle_roll = angle_roll * 0.9996 + angle_roll_acc * 0.0004
        else:
            angle_pitch = angle_pitch_acc
            angle_roll = angle_roll_acc
            gyro_angles_set = True

        # Calculate PID output
        calculate_pid()

        # Control motors
        motors[0].duty(int(1500 + pid_output_roll - pid_output_pitch + pid_output_yaw))
        motors[1].duty(int(1500 - pid_output_roll - pid_output_pitch - pid_output_yaw))
        motors[2].duty(int(1500 - pid_output_roll + pid_output_pitch + pid_output_yaw))
        motors[3].duty(int(1500 + pid_output_roll + pid_output_pitch - pid_output_yaw))

setup()
loop()
