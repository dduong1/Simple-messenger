# chat_server.py
import tkinter as tk
import sys
import socket
import select
import json
import threading

HOST = '127.0.0.1'
SOCKET_LIST = []
SOCKET_LIST_user = {}
RECV_BUFFER = 4096
PORT = 9009


class cMessage(object):
    def __init__(self,msgtype, provenance, destinataire, chatname,msg):
        self.msgtype = msgtype
        self.provenance = provenance
        self.destinataire = destinataire
        self.chatname = chatname
        self.msg = msg

def chat_server():

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)

    # add server socket object to the list of readable connections
    SOCKET_LIST.append(server_socket)
    SOCKET_LIST_user[(HOST,PORT)] = "Server"

    print ("Chat server started on port " + str(PORT) + '  ' +str(HOST))

    while 1:

        # get the list sockets which are ready to be read through select
        # 4th arg, time_out  = 0 : poll and never block
        ready_to_read,ready_to_write,in_error = select.select(SOCKET_LIST,[],[],0)

        for sock in ready_to_read:
            # a new connection request recieved
            if sock == server_socket:
                sockfd, addr = server_socket.accept()
                SOCKET_LIST.append(sockfd)

                print ("Client (%s, %s) connected" % addr)

                #We stream all new users
                tmpdict = {}

                for keyf in SOCKET_LIST_user.keys():
                    tmpdict [(str(keyf[0]) + " "+ str(keyf[1]))] =  SOCKET_LIST_user[keyf]
                #sjson = json.dumps(tmpdict)
                mymsg = cMessage("listuser",PORT, sockfd.getpeername(),"Server", tmpdict)
                #sjson = json.dumps(mymsg.__dict__)

                broadcast(server_socket, sockfd, mymsg,0)
                #Update socket list with new user
                SOCKET_LIST_user[addr] = ""



            # a message from a client, not a new connection
            else:
                # process data recieved from client,
                try:
                    # receiving data from the socket.
                    data = sock.recv(RECV_BUFFER)
                    msg = data.decode("utf-8")
                    tmp = (sock.getpeername()[0]) + " " + str(sock.getpeername()[1])

                    #Process incoming
                    if msg:
                        # there is something in the socket
                        msg = json.loads(msg)

                        if msg['msgtype'] == "exitserv" :
                            server_socket.close()
                            sys.exit()
                        elif msg['msgtype'] == "userconnect":
                            SOCKET_LIST_user[sock.getpeername()] = msg['msg']
                            mymsg = cMessage("userconnect",tmp, PORT,"Server", msg['msg'])
                            broadcast(server_socket, sock, mymsg,1)
                        elif msg['msgtype'] == "message":
                            mymsg = cMessage("message",tmp, msg["destinataire"],msg["chatname"], msg['msg'])
                            broadcast(server_socket, sock, mymsg,1)
                        elif msg['msgtype'] == "userchatroom+":
                            mymsg = cMessage("userchatroom+",tmp, msg["destinataire"],msg["chatname"], msg['msg'])
                            broadcast(server_socket, sock, mymsg,1)
                        else:
                            print("errrroooorrrrrrrrr")
                            break;

                    else:
                        #remove the socket that's broken
                        if sock in SOCKET_LIST:
                            SOCKET_LIST.remove(sock)
                            del SOCKET_LIST_user[sock.getpeername()]

                        mymsg = cMessage("userdisconnect",tmp, PORT,"SERVER", "disconnected")
                        broadcast(server_socket, sock, mymsg,1)
                # exception
                except:
                    print (sys.exc_info()[0])
                    broadcast(server_socket, sock, "Client (%s, %s) is offline\n" % addr,1)
                    if sock in SOCKET_LIST:
                        SOCKET_LIST.remove(sock)
                        del SOCKET_LIST_user[sock.getpeername()]
                    continue

    server_socket.close()

# broadcast chat messages to all connected clients
def broadcast (server_socket, sock, message, msgtype):
    #message = bytes(message,'UTF-8')
    sjson = json.dumps(message.__dict__)
    for socket in SOCKET_LIST:
        # send the message to all peers
        if msgtype ==1:
            if socket != server_socket and socket != sock :
                try :
                    socket.send(bytes(sjson, 'utf-8'))
                except :
                    # broken socket connection
                    socket.close()
                    # broken socket, remove it
                    if socket in SOCKET_LIST:
                        SOCKET_LIST.remove(socket)
                        del SOCKET_LIST_user[socket.getpeername()]
        # send message to self
        else:
            if socket != server_socket and socket == sock :
                try :
                    socket.send(bytes(sjson, 'utf-8'))
                except :
                    # broken socket connection
                    socket.close()
                    # broken socket, remove it
                    if socket in SOCKET_LIST:
                        SOCKET_LIST.remove(socket)
                        del SOCKET_LIST_user[socket.getpeername()]

class ThreadedClient:
    def __init__(self, master):
        self.master = master
        self.running = 1
        self.thread1 = threading.Thread(target=self.workerThread1)
        self.thread1.daemon = True
        self.thread1.start()


    def workerThread1(self):
        chat_server()

    def endApplication(self):
        self.running = 0



if __name__ == "__main__":


    root = tk.Tk()
    root.title("Server status")
    tk.Button(root, text="Server is running").pack()
    client = ThreadedClient(root)
    tk.mainloop()
    sys.exit(client.endApplication())