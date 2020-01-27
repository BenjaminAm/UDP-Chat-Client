def create_CL_CON_REQ(user_name):
    """
    :param user_name: user name to be sent
    :return: message of CL_CON_REQ format
    """
    b=  b"\x01" + len(user_name).to_bytes(2, "big") + bytes(user_name, "utf8")
    return b

def parse_SV_CON_REP(m):
    """
    Check if m is a SV_CON_REP message. If not, return None. If yes, check
    if connection was accepted. If yes, parse port from m and return tuple. If not, return False.
    :param m: message to be parsed
    :return: None, False, or tuple (True, port)
    """

    if m[0] == 2:
        accepted = m[1]
        if accepted == 0:
            accepted = True
        else:
            accepted = False
            return accepted
        if accepted:
            port = int(m[2:4].hex(), base=16)
            return accepted, port
    else:
        return None

def parse_SV_CON_AMSG(m):
    """
    :param m: message to be parsed
    :return: None or string user_name
    """
    if m[0] == 3:
        user_name_len = int(m[1:3].hex(), base=16)
        user_name = m[3:user_name_len+3].decode("utf8")
        return user_name
    else:
        return None

def create_CL_MSG(message):
    """
    :param message: chat message to be sent
    :return: False if len(message) is to long. Else, message in CL_MSG format
    """
    message_len = len(bytes(message, "utf8"))
    if message_len>1400:
        print("Die Nachricht an den Chat darf maximal 1400 Byte lang sein.")
        return False
    else:
        return b"\x04" + message_len.to_bytes(4, "big") + bytes(message, "utf8")

def parse_SV_AMSG(m):
    """
    :param m: message to be parsed
    :return: None or tuple (user_name, message)
    """
    if m[0] == 5:
        i=1
        user_name_len = int(m[i:i+2].hex(), base=16)
        i+=2
        user_name = m[i:i+user_name_len].decode("utf8")
        i+=user_name_len
        message_len = int(m[i:i+4].hex(), base=16)
        i+=4
        message = m[i:i+message_len].decode("utf8")
        return user_name, message
    else:
        return None

def create_CL_DISC_REQ():
    return b"\x06"

def parse_SV_DISC_REP(m):
    """
    :param m: message to be parsed
    :return: None or True
    """
    if m[0] == 7:
        return True
    else:
        return None

def parse_SV_DISC_AMSG(m):
    """
    :param m: message to be parsed
    :return: None or string user name
    """
    if m[0] == 8:
        user_name_len = int(m[1:3].hex(), base=16)
        user_name = m[3:3+user_name_len].decode("utf8")
        return user_name
    else:
        return None

def parse_SV_PING_REQ(m):
    """
    :param m: message to be parsed
    :return: None or True
    """
    if m[0] == 9:
        return True
    else:
        return None

def create_CL_PING_REP():
    return b"\x0a"

def parse_SV_MSG(m):
    """
    :param m: message to be parsed
    :return: None or server error message
    """
    if m[0] == 11:
        error_mess_len = int(m[1:5].hex(), base=16)
        error_mess = m[5:5+error_mess_len].decode("utf8")
        return error_mess
    else:
        return None