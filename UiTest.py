from tkinter import *
from tkinter import ttk
import time
import threading
import random
import queue

import sys
import socket
import select
import json


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(2)
host = "0.0.0.0"
mip = ""
activetab = {} #Store all created tabs {chatid:tabid}
activetabuser = {} #Store all users in each tabs {tabid:userid}
SOCKET_LIST_user = {} #Store all online users with their pseudo
pseudo = ""
#Define the object message which is the main object for transferring message
class cMessage(object):
    def __init__(self,msgtype, provenance, destinataire, chatname,msg):
        self.msgtype = msgtype
        self.provenance = provenance
        self.destinataire = destinataire
        self.chatname = chatname
        self.msg = msg

class GuiPart:
    def __init__(self, master, queue, endCommand):
        self.montext=StringVar()
        self.parent = master
        self.queue = queue
        #Set up the GUI
        #The GUI has 4 main elements
        self.userchatdisplay = Frame(master,bg="green", width=200, height=600, padx=1, pady=0)
        self.userchatdisplay.pack(side=LEFT,fill=Y)

        self.groupchatdisplay = Frame(master,bg ="grey", width=200, height=600, padx=0, pady=0)
        self.groupchatdisplay.pack(side=LEFT,fill=Y) #We use pack to setup the elements

        self.chatdisplay = ttk.Notebook(master)
        self.f1 = ttk.Frame(self.chatdisplay)
        self.chatdisplay.add(self.f1, text='All')
        self.chatdisplay.bind_all("<<NotebookTabChanged>>", self.tabChangedEvent)
        self.chatdisplay.pack(side=TOP, fill=BOTH, expand =1)

        self.textentry = Frame(master, bg="red", width=400, height=50)
        self.textentry.pack(side=BOTTOM, fill=X, expand=0)

        Grid.columnconfigure(self.groupchatdisplay, 0, weight=1)
        Grid.rowconfigure(self.groupchatdisplay, 0, weight=1)
        self.ListboxChat = Listbox(self.groupchatdisplay,bg = "#8FA1CB")
        self.ListboxChat.grid(row=0,column = 0, sticky=N+S+E+W) #We need to seperate grid otherwise return NONE object

        Grid.columnconfigure(self.userchatdisplay, 0, weight=1)
        Grid.rowconfigure(self.userchatdisplay, 0, weight=1)
        self.ListboxUser = Listbox(self.userchatdisplay,bg = "#8FA1CB")
        self.ListboxUser.grid(row=0,column = 0, sticky=N+S+E+W)
        self.ListboxUser.bind('<Double-Button-1>', self.dbhandler)

        Grid.columnconfigure(self.f1, 0, weight=1)
        Grid.rowconfigure(self.f1, 0, weight=1)
        self.DisplayText = Text(self.f1,bg = "#8FA1CB")
        self.DisplayText.grid(row=0,column = 0, sticky=N+S+E+W)

        Grid.columnconfigure(self.textentry, 0, weight=1)
        Grid.rowconfigure(self.textentry, 0, weight=1)
        self.EntryText = Entry(self.textentry)
        self.EntryText.grid(row=0,column = 0, sticky=N+S+E+W)
        self.EntryText.bind('<Return>', self.callback) #Return key event

    #Callback for tab changed event
    def tabChangedEvent(self,event):
        selectedtab = self.chatdisplay.index(self.chatdisplay.select()) + 1
        self.ListboxChat.delete(0, END)
        if(selectedtab != 1):
            for cc in activetabuser[selectedtab]:
                if(cc in SOCKET_LIST_user.keys()):
                    tmp = SOCKET_LIST_user[cc]
                    self.ListboxChat.insert(END,tmp)

    #Textbox callback, manage the information sent to Server
    def callback(self,event):

        msg = (self.EntryText.get())
        #Get selected tab
        selectedtab = self.chatdisplay.index(self.chatdisplay.select()) + 1
        if "-invite" in msg: #if we invite a new user.
            msg = msg.strip('-invite ')
            if (self.getIPbyName(msg) in SOCKET_LIST_user.keys()):
                activetabuser[selectedtab].append(self.getIPbyName(msg))
                #print(activetabuser)
                #broadcast user added to the chat room
                mymsg = cMessage("userchatroom+",str(s.getsockname()[0]) + " "+ str(s.getsockname()[1]), activetabuser[selectedtab],self.getchatid(selectedtab), msg + " joined the conversation")
                sjson = json.dumps(mymsg.__dict__)
                s.send(bytes(sjson,'UTF-8'))
        else: #Process all other message
            if selectedtab != 1:
                mymsg = cMessage("message",str(s.getsockname()[0]) + " "+ str(s.getsockname()[1]), activetabuser[selectedtab],self.getchatid(selectedtab), msg)
            else: #Specific for the Server Tab
                mymsg = cMessage("message",str(s.getsockname()[0]) + " "+ str(s.getsockname()[1]), "All",self.getchatid(selectedtab), msg)
            sjson = json.dumps(mymsg.__dict__)
            s.send(bytes(sjson,'UTF-8'))
            self.queue.put(json.loads(sjson)) #old hack because the objet is JSON
        self.EntryText.delete(0, 'end') #On efface le text dans la textbox

    #Generate a new tab on double click
    def dbhandler(self,event):
        #######Need to check whether the user is alone in a chat room or not. If yes, select the tab to avoid creating a new chat room


        ids = self.ListboxUser.selection_get() #Get the IP of the person we talk to
        if ids != "Server":
            gen = str(random.randint(0,100000)) #Generate a random Chat ID
            if("9009" not in self.ListboxUser.selection_get() and gen not in activetab.keys()):
                self.f2 = ttk.Frame(self.chatdisplay)   # second page
                #self.chatdisplay.add(self.f2, text=ids)
                self.chatdisplay.add(self.f2, text=ids)
                Grid.columnconfigure(self.f2, 0, weight=1)
                Grid.rowconfigure(self.f2, 0, weight=1)
                self.DisplayText = Text(self.f2,bg = "#8FA1CB")
                self.DisplayText.grid(row=0,column = 0, sticky=N+S+E+W)
                #activetab[ids] = self.chatdisplay.index("end")
                activetab[gen] = self.chatdisplay.index("end")
                activetabuser[self.chatdisplay.index("end")] = [self.getIPbyName(ids)]#[ids]
                self.chatdisplay.select(self.chatdisplay.index("end")-1)

    #Get chat id based on the selected tab
    def getchatid(self,selectedtab):
        for cc in activetab.keys():
            if(int(activetab[cc]) == int(selectedtab)):
                return cc
    def getIPbyName(self,cname):
        for keyf in SOCKET_LIST_user.keys():
            if SOCKET_LIST_user[keyf] == cname:
                return keyf

    #To access the GUI, we take advantage of the queue option
    def processIncoming(self):
        while self.queue.qsize():
            try:
                msg = self.queue.get(0) #getting the initial message (JSON)
                selectedtab = self.chatdisplay.index(self.chatdisplay.select()) + 1

                #Message dispatch by msgtype
                if msg["msgtype"] == "message":
                    if (str(s.getsockname()[0]) + " " + str(s.getsockname()[1])) == str(msg["provenance"]): #display message in own window [Me]
                        if msg["destinataire"] == "All":
                            ww = self.chatdisplay.winfo_children()[0].winfo_children()[0] #if message has been sent to all tabs
                        else:
                            ww = self.chatdisplay.winfo_children()[activetab[self.getchatid(selectedtab)]-1].winfo_children()[0] #else redirect the message to the correct tab
                        ww.insert(END, '[Me]\t\t' + str(msg["msg"]+"\n"))
                        ww.see(END)

                    elif msg["destinataire"] == "All":
                        ww = self.chatdisplay.winfo_children()[0].winfo_children()[0]
                        ww.insert(END, "[" + SOCKET_LIST_user[str(msg["provenance"])] + "]\t\t" + str(msg["msg"]+ "\n"))
                        ww.see(END)
                    else:
                        self.processMessage(msg)

                elif msg["msgtype"] == "userconnect":
                    self.ListboxUser.insert(END, msg["msg"] )
                    ww = self.chatdisplay.winfo_children()[0].winfo_children()[0]
                    ww.insert(END, '=== SERVER === ' + msg["msg"] + " connected\n")
                elif msg["msgtype"] == "userdisconnect":
                    for i, listbox_entry in enumerate(self.ListboxUser.get(0, END)):
                        if str(listbox_entry) == SOCKET_LIST_user[(msg["provenance"])]:
                            self.ListboxUser.delete(i)
                            ww = self.chatdisplay.winfo_children()[0].winfo_children()[0]
                            ww.insert(END, '=== SERVER === ' + SOCKET_LIST_user[(msg["provenance"])] + " disconnected - bye bye\n")
                            del SOCKET_LIST_user[(msg["provenance"])]
                            break

                elif msg["msgtype"] == "listuser":
                    for keyf in msg["msg"]:
                        self.ListboxUser.insert(END, msg['msg'][keyf] )
                elif msg["msgtype"] == "userchatroom+":
                    self.processMessage(msg)
                else:
                    print ("errroooooorrrr")
            except queue.Empty:
                pass

    #Processing message
    def processMessage(self,msg):
        #Look for existing tab
        if msg["chatname"] in activetab:
            #Activate tab or flash it
            ww = self.chatdisplay.winfo_children()[activetab[msg["chatname"]]-1].winfo_children()[0]
            ww.insert(END, "[" + SOCKET_LIST_user[str(msg["provenance"])] + "]\t\t" + str(msg["msg"]+ "\n"))
            ww.see(END)

            activetabuser[self.chatdisplay.index("end")].extend([c for c in msg["destinataire"] if (c!= str(s.getsockname()[0]) + " "+ str(s.getsockname()[1]) and c not in activetabuser[self.chatdisplay.index("end")])])
        #Or create new tab
        else:
            self.f2 = ttk.Frame(self.chatdisplay)   # second page
            if len(msg["destinataire"])>1:
                self.chatdisplay.add(self.f2, text=msg["chatname"])
            else:
                self.chatdisplay.add(self.f2, text=SOCKET_LIST_user[msg["provenance"]])
            Grid.columnconfigure(self.f2, 0, weight=1)
            Grid.rowconfigure(self.f2, 0, weight=1)
            self.DisplayText = Text(self.f2,bg = "#8FA1CB")
            self.DisplayText.grid(row=0,column = 0, sticky=N+S+E+W)
            self.DisplayText.insert(END, "[" + SOCKET_LIST_user[str(msg["provenance"])] + "]\t\t" + str(msg["msg"]+ "\n"))
            self.DisplayText.see(END)
            activetab[msg["chatname"]] = self.chatdisplay.index("end")
            activetabuser[self.chatdisplay.index("end")] = [c for c in msg["destinataire"] if c!= str(s.getsockname()[0]) + " "+ str(s.getsockname()[1])]
            activetabuser[self.chatdisplay.index("end")].extend([msg["provenance"]])

    def all_children (self,wid) :
        _list = wid.winfo_children()

        for item in _list :
            if item.winfo_children() :
                _list.extend(item.winfo_children())

        return _list

class ThreadedClient:
    def __init__(self, master):
        #Thread to create connection
        self.master = master

        #Opening queue for message streaming
        self.queue = queue.Queue()

        self.gui = GuiPart(master, self.queue, self.endApplication)

        #All I/O operation will be threaded
        self.running = 1
        self.thread1 = threading.Thread(target=self.workerThread1)
        self.thread1.daemon = True
        self.thread1.start()

        #Periodicall call is used to pick up the messages
        self.periodicCall()

    def periodicCall(self):
        self.gui.processIncoming()
        if not self.running:
            import sys
            sys.exit(1)
        self.master.after(200, self.periodicCall) #Check every 200ms

    #I/O Thread
    def workerThread1(self):
        host = '127.0.0.1' #Host IP
        port = 9009 #Host PORT




        #Connection au serveur
        try :
            s.connect((host, port))
        except :
            print ('Unable to connect')
            sys.exit()

        mip = str(s.getsockname()[0]) + " "+ str(s.getsockname()[1])
        #Stack messages in the UI queue
        mymsg = cMessage("userconnect",s.getsockname()[1], [455,333],"Server", pseudo)
        sjson = json.dumps(mymsg.__dict__)
        s.send(bytes(sjson,'UTF-8'))
        #self.queue.put("tcmsg+" + '=== SERVER === Connected to remote host. You can start sending messages\n')
        #self.queue.put(sjson)

        while self.running: #Loop to keep the connection alive
            socket_list = [sys.stdin, s]
            #We pull the socket information
            ready_to_read,ready_to_write,in_error = select.select(socket_list , [], [])

            #We look at what needs to be fetched on each socket
            for sock in ready_to_read:
                if sock == s: #We process the message
                    data = sock.recv(4096)
                    msgobj = data.decode("utf-8") #we deserialize

                    #if the message is empty, there is probably a problem in the connectionm we disconnect
                    if not msgobj:
                        print ('\nDisconnected from chat server')
                        sys.exit()
                    #Else message processing
                    else:
                        msg = json.loads(msgobj)
                        if msg["msgtype"] == "userdisconnect":
                            prv = msg["provenance"]
                            self.queue.put(msg)

                        elif msg["msgtype"] == "userconnect":
                            SOCKET_LIST_user[msg["provenance"]] = msg["msg"]
                            self.queue.put(msg)
                        elif msg["msgtype"] == "listuser":
                            self.queue.put(msg)
                            for keyf in msg["msg"]:
                                SOCKET_LIST_user[keyf] = msg["msg"][keyf]
                        elif msg["msgtype"] == "message":
                            if((s.getsockname()[0] + " " + str(s.getsockname()[1]) in msg["destinataire"]) or msg["destinataire"] == "All"):
                                self.queue.put(msg)
                        elif msg["msgtype"] == "userchatroom+":
                            if((s.getsockname()[0] + " " + str(s.getsockname()[1]) in msg["destinataire"])):
                                self.queue.put(msg)
                        else:
                            print("stop======================================")
                            pass

    def endApplication(self):
        self.running = 0


if __name__ == "__main__":
    rand = random.Random()
    root = Tk()
    pseudolist = ['Boyd','Reanna','Susanna','Kenisha','Trinh','Rosalba','Carole','Stephani','Gidget','Hong','Toshia','Lahoma','Candyce','Darell','Hayden','Jeneva','Tijuana','Song','Pasquale','Samella','Jocelyn','Bruce','Esmeralda','Rheba','Bradford','Von','Cleveland','Bobbye','Madelaine','Chase','Leonila','Tanesha','Euna','Cassaundra','Mervin','Elisabeth','Jeanine','Barbar','Inga','Clementina','Doris','Mikaela','Mandy','Lucien','Marx','Carl','Angelo','Ashleigh','Dani','Leota']
    pseudo = pseudolist[random.randint(0,49)] + str(random.randint(0,1000))#User PSEUDO is random

    client = ThreadedClient(root)
    root.title("https://github.com/dduong1/Simple-messenger        " + pseudo)
    root.mainloop()