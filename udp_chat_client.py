import getopt
import sys
import socket as s
import ipaddress as ip
import select
from threading import Thread
import udp_messages as mess


class UdpChatClient:

    LISTEN = False
    socket = None
    server_ip = ""
    server_port = 0
    user_name = ""
    server_name = "bones.informatik.uos.de"
    chat_port = 0

    @staticmethod
    def exit_with_usage():
        usage = """Programm in folgender Weise starten:
                    python3 udp_chat_client.py –s <serv_addr> -p <serv_port> -u <user>
    
                    Die Parameter stehen für:
                    -s <serv_addr> Hostname/IPv4 Adresse des Chat-Servers zu dem die Verbindung aufgebaut werden soll.
                    -p <serv_port> Port auf dem der Chat-Server auf eingehende Verbindungen wartet.
                    -u <user> Benutzername, der im Chat sichtbar sein soll. Für den Benutzernamen
                    sind lediglich alphanumerische Zeichen und keine Sonderzeichen erlaubt. Maximale Länge des Namens sind 20 Zeichen"""
        print(usage)
        sys.exit(1)

    def parse_arguments(self, argv):
        try:
            opts, args = getopt.getopt(argv, "s:p:u:")
        except getopt.GetoptError:
            UdpChatClient.exit_with_usage()
        for opt, arg in opts:
            if opt == '-s':
                self.server_ip = arg
                try:  # check if arg is valid IP address
                    ip.ip_address(self.server_ip)
                except ValueError:
                    print("Ungültige IP Adresse.")
                    UdpChatClient.exit_with_usage()
            elif opt == "-p":
                try:
                    self.server_port = int(arg) #Port is unsigned 16 bit int
                except ValueError:
                    print("Ungültiger Port.")
                    UdpChatClient.exit_with_usage()
                if self.server_port > 65535 or self.server_port < 0:
                    print("Ungültiger Port.")
                    UdpChatClient.exit_with_usage()
            elif opt == "-u":
                self.user_name = arg
                if len(self.user_name) > 20:
                    print("Benutzername darf maximal 20 Zeichen lang sein.")
                    UdpChatClient.exit_with_usage()
                    sys.exit(1)

    def establish_conn(self):
        """
        :return: If connection was accepted, return True, else return None
        """
        CL_CON_REQ = mess.create_CL_CON_REQ(self.user_name)
        print("Verbinde als %s zu Server %s (%s) auf Port %d" % (self.user_name, self.server_name, self.server_ip, self.server_port))
        ready = False
        data = ""

        for i in range(3):
            self.socket.sendto(CL_CON_REQ, (self.server_ip, self.server_port))
            ready = select.select([self.socket], [], [], 5)
            if ready[0]:
                data = self.socket.recv(1024)
                return self.route_handlers(data)
                break

        if not ready[0]:
            print("Verbindung fehlgeschlagen. Server antwortet nicht.")
            return None

    def send_chat_message(self, message):
        CL_MSG = mess.create_CL_MSG(message)
        self.socket.sendto(CL_MSG, (self.server_ip, self.chat_port))
        return

    def disconnect_from_server(self):
        CL_DISC_REQ = mess.create_CL_DISC_REQ()
        print("Beende die Verbindung zu Server %s (%s)." % (self.server_name, self.server_ip))
        ready = False
        data = ""
        global LISTEN
        LISTEN = False

        for i in range(3):
            self.socket.sendto(CL_DISC_REQ, (self.server_ip, self.chat_port))
            ready = select.select([self.socket], [], [], 5)
            if ready[0]:
                data = self.socket.recv(1024)
                break

        if not ready[0]:
            print("Verbindung nicht erfolgreich beendet. Timeout.")
            sys.exit(0)
        else:
            parsed_mess = mess.parse_SV_DISC_REP(data)
            if parsed_mess == None:
                print("Nachricht war nicht im SV_DISC_REP Format.")
            elif parsed_mess:
                print("Verbindung erfolgreich beendet.")
                sys.exit(0)

    def listen(self):
        global LISTEN
        LISTEN = True
        while LISTEN:
            ready = select.select([self.socket], [], [])
            if ready[0]:
                if LISTEN == False:
                    break
                data = self.socket.recv(2048)
                self.route_handlers(data)

    # region Handlers
    def route_handlers(self, m):
        """
        Route server messages to appropriate handlers
        :param m: the datagram
        :return: the return type of the handler called
        """
        id = m[0]
        handlers = {
            2: self.handle_con_rep,
            3: self.handle_con_amsg,
            5: self.handle_amsg,
            7: self.handle_disc_rep,
            8: self.handle_disc_amsg,
            9: self.handle_ping_req,
            11: self.handle_msg
        }
        return handlers[id](m)

    def handle_con_rep(self, m):
        parsed_mess = mess.parse_SV_CON_REP(m)
        if parsed_mess == False:
            print("Verbindung abgelehnt.")
            return None
        elif parsed_mess[0]:
            port = int(parsed_mess[1])
            print("Verbindung akzeptiert. Der Port für die weitere Kommunikation lautet %d." % port)
            self.chat_port = port
            return True

    def handle_con_amsg(self, m):
        connected_user = mess.parse_SV_CON_AMSG(m)
        print("%s hat den Chat betreten." % connected_user)

    def handle_amsg(self, m):
        user, message = mess.parse_SV_AMSG(m)
        print("%s: %s" % (user, message))

    def handle_disc_rep(self, m):
        """
        Is called only for SV_DISC_REP that were not preceded by a CL_DISC_REQ
        :param m:
        :return:
        """
        if mess.parse_SV_DISC_REP(m):
            print("Verbindung zum Server beendet. Timeout.")
        sys.exit(0)

    def handle_disc_amsg(self, m):
        user = mess.parse_SV_DISC_AMSG(m)
        print("%s hat den Chat verlassen." % user)

    def handle_ping_req(self, m):
        if mess.parse_SV_PING_REQ(m):
            rep = mess.create_CL_PING_REP()
            self.socket.sendto(rep, (self.server_ip, self.chat_port))

    def handle_msg(self, m):
        message = mess.parse_SV_MSG(m)
        print("#server#: %s" % message)
    # endregion


def main(argv):
    #check if format of argv is correct
    if len(argv) != 6:
        UdpChatClient.exit_with_usage()

    client = UdpChatClient()
    # fill client variables according to cmd input
    client.parse_arguments(argv)

    # Create UDP socket and add to shared queue for multiple processes
    client.socket = s.socket(family=s.AF_INET, type=s.SOCK_DGRAM)

    # establish connection. Proceed only if connection was successfully established
    conn_established = client.establish_conn()
    if not conn_established:
        sys.exit(1)
    # start listening thread. This thread listens for incoming data and then routes the input to the correct handler
    listen_thread = Thread(target=client.listen, daemon=True)
    listen_thread.start()

    # loop for user input. If user types in "/disconnect", the client will disconnect via CL_DISC_REQ
    # else the client will send the input as chat message to the server, provided its not too long
    while True:
        user_input = input("")
        if len(bytes(user_input, "utf8")) > 1400:
            user_input = input("Maximale Nachrichtenlänge 1400 Bytes. Bitte kürzere Nachricht eingeben: ")
        if user_input == "/disconnect":
            client.disconnect_from_server()
            break
        client.send_chat_message(user_input)


if __name__ == '__main__':
    main(sys.argv[1:])



