import logging
import serial
from typing import Self
from datetime import datetime



from utility_functions import *

# ===== Script Global Variables =====
GENERAL_CFG = {
    'port': 'COM5',     # PC port name
    'baud': 115200,     # Baud rate
    'timeout': 120,   # Timeout in seconds
    'log_file': f"{str(datetime.now().date()).replace('-', '_')}_GDAq_Lab2.log",
}

DEVICE_CFG = {
    'height': 99.99     # Instrument Height
}

TARGET_CFG = {
    'prism_type': 0,
    'prism_height': 123.456,
}


logger = setup_logger(GENERAL_CFG['log_file'], logging.DEBUG)


class TPSConnection(serial.Serial):
    def __enter__(self) -> Self:
        if not self.is_open:
            raise IOError("Serial port open failed")
        else:
            logger.info(f'TPS port is open')

        return self

    def __exit__(self, exc_type, exc_value, traceback, /):

        self.execute(2008, parameters=[0, 0])    # Stop all measurements
        tps.execute(2020, parameters=[2,])       # Set to standard meas.

        self.close()
        if not self.is_open:
            logger.info(f'TPS port is closed')

    def execute(self,
                rpc_code: int,
                parameters: list | tuple = (),
                transaction_id: int|None = None):
        # Sends the request
        send_request(self, rpc_code, parameters, transaction_id)

        # Gets the response
        rpc_return_code, parameters, transaction_id, communication_return_code = get_response(self)

        # Check the communication was OK
        if communication_return_code != 0:
            raise ConnectionError(
                f'GeoCOM ran into a communications error with error code: {communication_return_code}.\n'
                f'Check the GeoCOM documentation for more info.'
            )

        # Check if another error was raised
        if rpc_return_code != 0:
            raise ValueError(
                f'GeoCOM error produced with error code: {rpc_return_code} - refer to documentation for more info.'
            )

        return rpc_return_code, parameters, transaction_id, communication_return_code


if __name__ == '__main__':

    with TPSConnection(port=GENERAL_CFG['port'],
                       baudrate=GENERAL_CFG['baud'],
                       timeout=GENERAL_CFG['timeout']) as tps:

        return_code, values, tran_id, comm_code = tps.execute(17022)
        logger.info(f"Target Type: {values}")               # Prism or Reflectorless

        return_code, values, tran_id, comm_code = tps.execute(17031)
        logger.info(f"Prism Type: {values}")                # ID and name

        return_code, values, tran_id, comm_code = tps.execute(6021)
        logger.info(f"Lock status: {values}")

        return_code, values, tran_id, comm_code = tps.execute(2011)
        logger.info(f"Get height: {values}")

        return_code, values, tran_id, comm_code = tps.execute(2009)
        logger.info(f"Get Station: {values}")

        return_code, values, tran_id, comm_code = tps.execute(2021)
        logger.info(f"Get EDM Mode: {values}")

        return_code, values, tran_id, comm_code = tps.execute(2107)
        hz, v = float(values[0]), float(values[1])
        logger.info(f'Hz = {rad2gon(hz) :.4f} [gon]; V = {rad2gon(v) :.4f} [gon]')

#       Turn station
        Hz_temp, V_temp = 300.0000, 100.0000
        logger.info("AUT_MakePositioning - turning the telescope to a specified position (Hz=%sgon, V=%sgon) \n")
        return_code, params, tran_id, comm_code = tps.execute(rpc_code = 9027, parameters=[gon2rad(Hz_temp), gon2rad(V_temp)])

