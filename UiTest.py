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
activetab = {}
activetabuser = {}
SOCKET_LIST_user = {} #Store les utilisateurs en ligne

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
        # Set up the GUI
        #self.console = tk.Button(master, text='Done', command=endCommand)
        #self.console.pack()
        # La fenetre dispose de quatre elements.
        self.groupchatdisplay = Frame(master,bg ="grey", width=200, height=600, padx=0, pady=0)
        self.groupchatdisplay.pack(side=LEFT,fill=Y) #on utilise pack pour faire le setup du panel

        self.userchatdisplay = Frame(master,bg="green", width=200, height=600, padx=1, pady=0)
        self.userchatdisplay.pack(side=LEFT,fill=Y)

        #self.chatdisplay = Frame(master, bg="blue",   width=400, height=550)
        self.chatdisplay = ttk.Notebook(master)
        self.f1 = ttk.Frame(self.chatdisplay)   # first page, which would get widgets gridded into it
        self.chatdisplay.add(self.f1, text='All')
        self.chatdisplay.pack(side=TOP, fill=BOTH, expand =1)

        self.textentry = Frame(master, bg="red", width=400, height=50)
        self.textentry.pack(side=BOTTOM, fill=X, expand=0)

        Grid.columnconfigure(self.groupchatdisplay, 0, weight=1)
        Grid.rowconfigure(self.groupchatdisplay, 0, weight=1)
        self.ListboxChat = Listbox(self.groupchatdisplay,bg = "#8FA1CB")
        self.ListboxChat.grid(row=0,column = 0, sticky=N+S+E+W) #on ajoute une ligne specifiquement pour Grid car sinon cela genere un objet vide pour ListboxChat.

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
        self.EntryText.bind('<Return>', self.callback) #On defini une fonction call back pour gerer l evenement ENTER

    #Callback du TextBox. On recupere le texte et on le serialise pour l envoyer sur le server.
    def callback(self,event):

        msg = (self.EntryText.get())
        #Get selected tab
        selectedtab = self.chatdisplay.index(self.chatdisplay.select()) + 1
        if "-invite" in msg:
            msg = msg.strip('-invite ')
            if (msg in SOCKET_LIST_user.keys()):
                activetabuser[selectedtab].append(msg)
                print(activetabuser)
                #broadcast user added to the chat room
                mymsg = cMessage("userchatroom+",str(s.getsockname()[0]) + " "+ str(s.getsockname()[1]), activetabuser[selectedtab],self.getchatid(selectedtab), mip + " joined the conversation")
                sjson = json.dumps(mymsg.__dict__)
                s.send(bytes(sjson,'UTF-8'))
        else:
            if selectedtab != 1:
                #mymsg = cMessage("message",str(s.getsockname()[0]) + " "+ str(s.getsockname()[1]), activetabuser[selectedtab],"Chatname pending", msg)
                mymsg = cMessage("message",str(s.getsockname()[0]) + " "+ str(s.getsockname()[1]), activetabuser[selectedtab],self.getchatid(selectedtab), msg)
            else:
                #mymsg = cMessage("message",str(s.getsockname()[0]) + " "+ str(s.getsockname()[1]), "All","Chatname pending", msg)
                mymsg = cMessage("message",str(s.getsockname()[0]) + " "+ str(s.getsockname()[1]), "All",self.getchatid(selectedtab), msg)
            sjson = json.dumps(mymsg.__dict__)
            s.send(bytes(sjson,'UTF-8'))
            #On donne l'id unique du chat en question et on stream l'idchat + le message
            self.queue.put(json.loads(sjson)) #vieil artefact pourri.
        self.EntryText.delete(0, 'end') #On efface le text dans la textbox
    def dbhandler(self,event):
        #######Need to check whether the user is alone in a chat room or not. If yes, select the tab to avoid creating a new chat room
        #self.ListboxUser.config(state=DISABLED)

        ids = self.ListboxUser.selection_get()
        gen = str(random.randint(0,100000))
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
            activetabuser[self.chatdisplay.index("end")] = [ids]
            self.chatdisplay.select(self.chatdisplay.index("end")-1)


    def getchatid(self,selectedtab):
        for cc in activetab.keys():
            if(int(activetab[cc]) == int(selectedtab)):
                return cc

    #la GUI etant syncrone, on recupere dans le Thread principal les elements de la queue. On ne peut acceder aux elements de l'UI que par cette voie.
    def processIncoming(self):
        while self.queue.qsize():
            try:
                msg = self.queue.get(0)
                selectedtab = self.chatdisplay.index(self.chatdisplay.select()) + 1
                if msg["msgtype"] == "message":
                    if (str(s.getsockname()[0]) + " " + str(s.getsockname()[1])) == str(msg["provenance"]): #display message in own window [Me]
                        if msg["destinataire"] == "All":
                            ww = self.chatdisplay.winfo_children()[0].winfo_children()[0] #if message has been sent to all tabs
                        else:
                            #ww = self.chatdisplay.winfo_children()[activetab[msg["destinataire"][0]]-1].winfo_children()[0] #else select active tab
                            ww = self.chatdisplay.winfo_children()[activetab[self.getchatid(selectedtab)]-1].winfo_children()[0]
                        ww.insert(END, '[Me]\t\t' + str(msg["msg"]+"\n"))
                        self.DisplayText.see(END)

                    elif msg["destinataire"] == "All":
                        #self.chatdisplay.select(0)
                        ww = self.chatdisplay.winfo_children()[0].winfo_children()[0]
                        ww.insert(END, "[" + str(msg["provenance"]) + "]\t\t" + str(msg["msg"]+ "\n"))
                        ww.see(END)
                    else:
                        self.processMessage(msg)
                        #self.DisplayText.insert(END, "[" + str(msg["provenance"]) + "]\t\t" + str(msg["msg"]+ "\n"))

                elif msg["msgtype"] == "userconnect":
                    #recuperer la fenetre main pour afficher l info
                    self.ListboxUser.insert(END, msg["provenance"] ) #+ "|" + str(msg["msg"])
                    self.DisplayText.insert(END, '=== SERVER === ' + msg["msg"] + " connected\n")
                elif msg["msgtype"] == "userdisconnect":
                    #recuperer la fenetre main pour recuperer l info
                    for i, listbox_entry in enumerate(self.ListboxUser.get(0, END)):
                        if str(listbox_entry) == str(msg["provenance"]):
                            self.ListboxUser.delete(i)
                            self.DisplayText.insert(END, '=== SERVER === ' + str(msg["provenance"]) + " disconnected - bye bye\n")
                elif msg["msgtype"] == "listuser":
                    for keyf in msg["msg"]:
                        self.ListboxUser.insert(END, keyf ) #+ "|" + str(msg["msg"][keyf])
                elif msg["msgtype"] == "userchatroom+":
                    self.processMessage(msg)
                    #else:
                    #    for keyf in msg["destinataire"]:
                    #        if(keyf not in activetabuser[activetab[msg["chatname"]]]):
                    #            activetabuser[activetab[msg["chatname"]]].append(keyf)
                else:
                    print ("errroooooorrrr")
            except queue.Empty:
                # one ne devrait pas avoir ce cas.
                pass

    #action sur les tabs.
    def processMessage(self,msg):
        #Look for existing tab
        #if msg["provenance"] in activetab:
        if msg["chatname"] in activetab:
            #Activate tab or flash it
            #ww = self.chatdisplay.winfo_children()[activetab[msg["provenance"]]-1].winfo_children()[0]
            ww = self.chatdisplay.winfo_children()[activetab[msg["chatname"]]-1].winfo_children()[0]
            ww.insert(END, "[" + str(msg["provenance"]) + "]\t\t" + str(msg["msg"]+ "\n"))
            ww.see(END)
            activetabuser[self.chatdisplay.index("end")].extend([c for c in msg["destinataire"] if (c!= str(s.getsockname()[0]) + " "+ str(s.getsockname()[1]) and c not in activetabuser)])
        else:
            #Create new tab
            self.f2 = ttk.Frame(self.chatdisplay)   # second page
            #self.chatdisplay.add(self.f2, text=msg["provenance"])
            if len(msg["destinataire"])>1:
                self.chatdisplay.add(self.f2, text=msg["chatname"])
            else:
                self.chatdisplay.add(self.f2, text=msg["provenance"])
            Grid.columnconfigure(self.f2, 0, weight=1)
            Grid.rowconfigure(self.f2, 0, weight=1)
            self.DisplayText = Text(self.f2,bg = "#8FA1CB")
            self.DisplayText.grid(row=0,column = 0, sticky=N+S+E+W)
            self.DisplayText.insert(END, "[" + str(msg["provenance"]) + "]\t\t" + str(msg["msg"]+ "\n"))
            self.DisplayText.see(END)
            #activetab[msg["provenance"]] = self.chatdisplay.index("end")
            activetab[msg["chatname"]] = self.chatdisplay.index("end")
            activetabuser[self.chatdisplay.index("end")] = [c for c in msg["destinataire"] if c!= str(s.getsockname()[0]) + " "+ str(s.getsockname()[1])]
            activetabuser[self.chatdisplay.index("end")].extend([msg["provenance"]])
            #self.chatdisplay.select(self.chatdisplay.index("end")-1)


    def all_children (self,wid) :
        _list = wid.winfo_children()

        for item in _list :
            if item.winfo_children() :
                _list.extend(item.winfo_children())

        return _list

class ThreadedClient:
    def __init__(self, master):
        #Thread principal
        self.master = master

        #Creation de la queue pour la GUI
        self.queue = queue.Queue()

        #On instancie la GUI
        self.gui = GuiPart(master, self.queue, self.endApplication)

        #Toutes les operation I/O via le socket se font a travers des threads paralleles
        self.running = 1
        self.thread1 = threading.Thread(target=self.workerThread1)
        self.thread1.start()

        #On lance la fonction periodiccall qui va checker toutes les x fois par seconde si la queue possede des messages en attente.
        self.periodicCall()

    def periodicCall(self):
        self.gui.processIncoming()
        if not self.running: #en cas d'erreur
            import sys
            sys.exit(1)
        self.master.after(200, self.periodicCall) #On check toutes les 200ms

    #Thread parallel pour gerer les operations d'I/O
    def workerThread1(self):
        host = '127.0.0.1' #IP de connection au host
        port = 9009 #Port de connection
        pseudo = str(random.randint(0,1000)) #ID de l'utilisateur #sys.argv[1]



        #Connection au serveur
        try :
            s.connect((host, port))
        except :
            print ('Unable to connect')
            sys.exit()

        mip = str(s.getsockname()[0]) + " "+ str(s.getsockname()[1])
        #Stack les messages dans la queue de l'UI
        mymsg = cMessage("userconnect",s.getsockname()[1], [455,333],"Server", pseudo)
        sjson = json.dumps(mymsg.__dict__)
        s.send(bytes(sjson,'UTF-8'))
        #s.send(bytes("nick" + pseudo,'UTF-8')) #Une fois la connection etablie, on envoie le pseudo de l'utilisateur
        #self.queue.put("tcmsg+" + '=== SERVER === Connected to remote host. You can start sending messages\n')
        #self.queue.put(sjson)

        while self.running: #On boucle pour garder la connection active
            socket_list = [sys.stdin, s]
            #On recupere la liste des sockets readable, writable et en erreur.
            ready_to_read,ready_to_write,in_error = select.select(socket_list , [], [])

            #On loop sur tous les sockets qui ont des informations a recuperer i.e on lit a partir du serveur.
            for sock in ready_to_read:
                if sock == s: #on a une information du server. on traite le message
                    data = sock.recv(4096)
                    msgobj = data.decode("utf-8") #on deserialize ## il fqut deserialise le json

                    if not msgobj:
                        print ('\nDisconnected from chat server')
                        sys.exit()
                    else:
                        msg = json.loads(msgobj)
                        if msg["msgtype"] == "userdisconnect":
                            prv = msg["provenance"]
                            self.queue.put(msg)
                            if (prv) in SOCKET_LIST_user:
                                del SOCKET_LIST_user[prv]
                        elif msg["msgtype"] == "userconnect":
                            #SOCKET_LIST_user[(host,str(msg["provenance"]))] = msg["msg"]
                            SOCKET_LIST_user[msg["provenance"]] = msg["msg"]
                            self.queue.put(msg)
                        elif msg["msgtype"] == "listuser":
                            self.queue.put(msg)
                            for keyf in msg["msg"]:
                                #SOCKET_LIST_user[(keyf.split(":")[0],keyf.split(":")[1])] = msg["msg"][keyf]
                                SOCKET_LIST_user[keyf] = msg["msg"][keyf]
                        elif msg["msgtype"] == "message":
                            if((s.getsockname()[0] + " " + str(s.getsockname()[1]) in msg["destinataire"]) or msg["destinataire"] == "All"):
                                self.queue.put(msg)
                        elif msg["msgtype"] == "userchatroom+":
                            if((s.getsockname()[0] + " " + str(s.getsockname()[1]) in msg["destinataire"])):
                                self.queue.put(msg)
                        else:
                            print("stop======================================")

    def endApplication(self):
        self.running = 0


if __name__ == "__main__":
    rand = random.Random()
    root = Tk()

    client = ThreadedClient(root)
    root.title(str(s.getsockname()[0]) + " "+ str(s.getsockname()[1]))
    root.mainloop()