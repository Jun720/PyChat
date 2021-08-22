import grpc
import threading
import os

import chat_pb2
import chat_pb2_grpc

import tkinter as tk
import tkinter.scrolledtext as st
import tkinter.messagebox as mb

from google.protobuf import empty_pb2

# server port number
PORT = 4504


class ChatClient(tk.Tk):
    """
    Chat application class with GUI.
    Set each part of GUI as instance attribute so it's easy to modify them.
    """
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.title("Chat")
        self.username = ""
        self.setMenuBar()
        self.setChatFrame()
        self.setNameFrame()

        # connect to chat server
        channel = grpc.insecure_channel('localhost:' + str(PORT))
        self.stub = chat_pb2_grpc.ChatServerStub(channel)
        # run a new thread to sync chat log with the server
        self.receiveThread = threading.Thread(target=self.receive)
        self.receiveThread.start()

    def setMenuBar(self):
        """
        Setup a menu bar GUI.
        """
        self.menuBar = tk.Menu()
        self.config(menu=self.menuBar)

        self.menuFile = tk.Menu(self.menuBar, tearoff=0)
        self.menuBar.add_cascade(label="File", menu=self.menuFile)

        self.menuFile.add_command(label="Change username", command=self.setNewName)
        self.menuFile.add_command(label="Clear", command=self.clearLog)
        self.menuFile.add_command(label="Exit", command=self.exit)

    def setChatFrame(self):
        """
        Setup a frame and widgets for chat page GUI.
        This will be the main page viewed by the user.
        """
        self.chatFrame = tk.Frame()
        self.chatFrame.grid(row=0, column=0, sticky="nsew")
        # Setup widgets
        self.chatLog = st.ScrolledText(self.chatFrame)
        self.chatLog.configure(state='disable')
        self.chatLog.pack()

        self.inputForm = tk.Entry(self.chatFrame)
        self.inputForm.bind("<Return>", self.send)
        self.inputForm.pack(ipadx=100)

        self.sendButton = tk.Button(self.chatFrame, text="Send")
        self.sendButton.bind("<1>", self.send)
        self.sendButton.pack()

    def setNameFrame(self):
        """
        Setup a frame and widgets for name input page GUI.
        This will be the start page viewed by the user when the app lunches.
        """
        self.askNameFrame = tk.Frame()
        self.askNameFrame.grid(row=0, column=0, sticky="nsew")
        # Setup widgets
        self.askNameLabel = tk.Label(self.askNameFrame, text="Enter your name:")
        self.askNameLabel.pack()

        self.nameEntry = tk.Entry(self.askNameFrame)
        self.nameEntry.bind('<Return>', self.setName)
        self.nameEntry.focus_force()
        self.nameEntry.pack()

        self.nameButton = tk.Button(self.askNameFrame, text="OK")
        self.nameButton.bind("<1>", self.setName)
        self.nameButton.pack()

    def setName(self, event):
        """
        Get username from entry box.
        The username will be used to identify message sender.
        The entry box will be unseen afterwards.

        :param event: GUI event when Enter key is pressed.
        """
        name = self.nameEntry.get()
        if name != "":
            self.username = name
            self.chatFrame.tkraise()
            self.inputForm.focus_force()
            self.title("Chat [" + self.username + "]")

    def send(self, event):
        """
        Send a letter to chat server. A letter contains sender's name and text message.
        The text message is what entered in entry box.

        :param event: GUI event when Enter key is pressed or 'send' button is clicked.
        """
        text = self.inputForm.get()
        if text != "":
            letter = chat_pb2.Letter()
            letter.name = self.username
            letter.text = text
            # call the server method
            self.stub.sendMessage(letter)
            self.inputForm.delete(0, 'end')

    def receive(self):
        """
        Send an empty request to the server and receive chat letter, which contains sender's name and text message.
        Display received messages on the GUI.

        :raises: If server is no found, pop a message box asking if to reconnect or exit.
        """
        try:
            # call the server method and receive letter from the server line by line
            for letter in self.stub.receiveMessage(empty_pb2.Empty()):
                # set chat message area writable and set it back after chat log sync
                self.chatLog.configure(state='normal')
                self.chatLog.insert('end', letter.name + ": " + letter.text + "\n")
                self.chatLog.configure(state='disable')
                self.chatLog.see('end')
        except:
            # pop message window to ask if reconnect or not
            retry = mb.askretrycancel("Error", "Server not found")
            if retry:
                self.receive()
            else:
                self.exit()

    def exit(self):
        """
        Exit from the entire application.
        """
        os._exit(1)

    def setNewName(self):
        """
        Allow the user to set a new username.
        """
        self.askNameFrame.tkraise()

    def clearLog(self):
        """
        Clear chat log on the GUI. The actual log is saved on chat server and kept unchanged.
        """
        self.chatLog.configure(state='normal')
        self.chatLog.delete(1.0, 'end')
        self.chatLog.configure(state='disable')


if __name__ == '__main__':
    app = ChatClient()
    app.mainloop()
    os._exit(0)
