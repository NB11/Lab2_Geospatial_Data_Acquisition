import logging

import serial

import numpy as np


# ========= Global Variables for the utilies =========
TERMINATION_STRING = '\r\n'
LOGGER_NAME = 'GDAq_Lab2_Logger'


# ========= Logging Functionality =========
def setup_logger(file_name: str, level: int | str = logging.DEBUG) -> logging.Logger:
    """Configure a logger that both logs to file and to the command line

    Args:
        file_name: str
            Name of the file to write to
        level:
            Log level to use for logging. This is identical for the console and file handlers

    Returns:
        logger: logging.Logger

    """
    # Initialises the logger
    logger = logging.Logger(LOGGER_NAME)
    logger.setLevel(level)

    # Defines the format that each log message will be printed as
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Create a file handler to write logs to a file
    file_handler = logging.FileHandler(file_name)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    # Create a stream handler to print logs to the console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# ========= GeoCOM Request/Response Functions =========

def send_request(
        tps_connection: serial.Serial,
        rpc_code: int,
        parameters: list | tuple = (),
        transaction_id: int = None
):
    """Generic function for sending tps commands via a request

    Args:
        tps_connection: Active connection object to the TPS
        rpc_code: Command RPC ID
        parameters: Supplementary parameters for the specific command
        transaction_id: Support for Transaction ID parameter where required by the GeoCOM command

    Returns:
        None

    """
    # Convert transaction_id to a string
    tr_id: str = "" if transaction_id is None else str(transaction_id)

    # Create the parameters string component
    parameters: str = ",".join(str(parameter) for parameter in parameters)

    # Create the full request string
    request_string: bytes = f"%R1Q,{rpc_code}{tr_id}:{parameters}{TERMINATION_STRING}".encode("ascii")

    # Send the request via the serial communication "write" method
    tps_connection.write(request_string)
    return


def get_response(tps_connection: serial.Serial) -> tuple[int, list[str], int]:
    """Function to get the response message stored in the buffer

    Also performs basic checks

    Args:
        tps_connection: Active connection object to the TPS

    Returns:
        rpc_return_code: int
        parameters: list[str]
        transaction_id: int

    Exceptions:
        ConnectionError: If the TPS returned a Communication Error code
        ValueError: If there was an error from the TPS which returned a non-zero return code

    """
    # Extract the returned values as the next line from the buffer
    response = tps_connection.readline()

    # In the case it is empty, return an error
    if not response:
        raise ConnectionError("Failed to receive a response message.")

    # Split the response message string into a returned header and parameters components
    header_part, parameters_part = response.split(b":", 1)

    # Get the specific components from the header and parameters parts
    communication_return_code, transaction_id = _get_response_header(header_part)
    rpc_return_code, parameters = _get_response_parameters(parameters_part)

    return rpc_return_code, parameters, transaction_id, communication_return_code


def _get_response_header(header: bytes) -> tuple[int, int|None]:
    """Gets the response string and returns the communication return code and transaction code (if exists)

    Args:
        header: bytes
            Byte string containing the start of the response message

    Returns:
        communication_return_code: int
        transaction_id: int|None

    """
    header_parts = header.split(b',')

    # Get the header components
    if len(header_parts) == 2:
        reply_type, communication_return_code = header_parts
        transaction_id = None

    elif len(header_parts) == 3:
        reply_type, communication_return_code, transaction_id = header_parts


    else:
        raise ValueError(f"Invalid number of header components received in the response. "
                         f"Expected 2 or 3, received {len(header_parts)}")

    if reply_type != b'%R1P':
        raise ValueError(f"Response is not of the correct GeoCOM reply type 1.")

    transaction_id = None if transaction_id is None else int(transaction_id)

    return int(communication_return_code), transaction_id


def _get_response_parameters(raw_parameters: bytes) -> tuple[int, list[str]]:
    """Gets the returned parameters from the byte string and converts them to regular strings

    Args:
        raw_parameters: bytes
            Byte string containing the parameters from the response

    Returns:
        return_code: int
        parameters_as_string: list[str]
    """
    # Remove any of the termination string that may be at the end of the response
    parameters = raw_parameters.rstrip(TERMINATION_STRING.encode('ascii'))

    # split the remaining parts into a return code id value and values is a list of byte type objects
    return_code, *params_list = parameters.split(b',')

    # Convert the byte type objects to human-readable string values
    parameters_as_string: list[str] = [param.decode('ascii') for param in params_list]

    return int(return_code), parameters_as_string


# ========= Angle Conversion Functions =========
def gon2rad(angle):
    """Converts from gon / gradians to radians"""
    return angle * np.pi / 200


def rad2gon(angle):
    """Convert from radians to gon / gradians"""
    return angle * 200 / np.pi


def deg2rad(angles):
    """Converts from decimal degrees to radians"""
    return np.deg2rad(angles)


def rad2deg(angles):
    """Converts from radians to decimal degrees"""
    return np.rad2deg(angles)
