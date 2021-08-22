import grpc
from concurrent import futures

import chat_pb2
import chat_pb2_grpc

from google.protobuf import empty_pb2

# server port number
PORT = 4504


class ChatServer(chat_pb2_grpc.ChatServer):
    """
    Chat server class.
    Multiple clients can connect to the server and send chat messages at the same time.
    """

    def __init__(self):
        # list to store chat log
        self.chatLog = []
        self.chatFile = open('chat_log.txt', 'w')
        self.chatFile.close()
        # load chat log from text file when the server starts up
        self.parseLog()

        # self.clearLog() # uncomment this line to clear chat log

    def sendMessage(self, request, context):
        """
        Called when client sends a message.
        Add client's username and text message to chat log.

        :param request: Letter sent from client, which contains sender's name and text message
        :return: Empty value is returned to client.
        """
        self.chatLog.append(request)
        self.chatFile = open('chat_log.txt', 'a')
        self.chatFile.write(str(request))
        self.chatFile.close()
        return empty_pb2.Empty()

    def receiveMessage(self, request, context):
        """
        Called by all clients to sync chat log with chat server.
        When a new message is sent from client, return the message to all clients.

        :param request: Empty value for request.
        :return: A sequence of Letter, which contains sender's name and text message. Letter is returned line by line
        """
        # keep track of already sent messages
        line = 0
        # infinite loop to keep track on if there is a new message
        while True:
            if line < len(self.chatLog):
                # yield resumes the method from here after each return
                yield self.chatLog[line]
                # read the next line
                line += 1

    def parseLog(self):
        """
        Read chat log from the text file so previous chats are reflected everytime the server starts up.
        """
        self.chatFile = open('chat_log.txt', 'r')

        while True:
            letter = chat_pb2.Letter()
            line = self.chatFile.readline()
            if line == '':
                break
            # read name if the line starts with 'n'
            if line[0] == 'n':
                letter.name = self.parseLetter(line)

            line = self.chatFile.readline()
            if line == '':
                break
            # read text if the line starts with 'm'
            if line[0] == 'm':
                letter.text = self.parseLetter(line)

            self.chatLog.append(letter)

        self.chatFile.close()

    def parseLetter(self, line):
        """
        Parse string stream to get name or text as needed.

        :param line: A line (string) of chat log file.
        :return: name or text of Letter type
        """
        if line[0] == 'n':
            return line[7:-2]
        elif line[0] == 'm':
            return line[10:-2]
        else:
            return ''

    def clearLog(self):
        """
        Clear chat log file. Debugging method.
        """
        self.chatFile = open('chat_log.txt', 'r+')
        self.chatFile.truncate(0)

def serve():
    """
    Run chat server.
    """
    # max_workers defines the maximum number of rpc connection to the server at a time
    # for each client app at least 2 channels are required (sendMessage and receiveMessage)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=20))
    chat_pb2_grpc.add_ChatServerServicer_to_server(ChatServer(), server)
    server.add_insecure_port('[::]:' + str(PORT))
    server.start()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:  # Ctrl+C to terminate on terminal
        server.stop(0)


if __name__ == '__main__':
    print("Starting chat server...")
    serve()
