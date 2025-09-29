import serial

# Open TPS port
TPS_port = serial.Serial(port="COM7",baudrate=115200,timeout=60)
if TPS_port.isOpen():
    print("Port is connected")
    # Communication with the instrument
    # Request - send a command to the total station
    # request_id: %RIQ,2107:
    request = "%R1Q,2107:\r\n".encode("ascii")
    TPS_port.write(request)
    # Reply - read response data into the sting-variable out
    response = TPS_port.readline()
    # Extract the returned values
    header, parameters = response.split(b":", 1)
    # Request | Reply | Extract
    # Request | Reply | Extract
    # ...
    # Close TPS port
    TPS_port.close()
if not TPS_port.isOpen():
    print("Port is disconnected")
