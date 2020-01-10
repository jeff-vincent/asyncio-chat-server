import asyncio

class Color:
 RED = '\033[91m'
 GREEN = '\033[92m'
 YELLOW = '\033[93m'
 BLUE = '\033[94m'
 PURPLE = '\033[95m'
 TEAL = '\033[96m'
 END_COLOR = '\033[00m'


class ChatServer:

    def __init__(self):
        self.writers = []
        self.users = {}
        self.write_queue = asyncio.Queue()

    def printColor(self, string, color):
        print('{} {}\033[00m'.format(color, string))

    async def forward(self, writer, addr, message):
        # iterate over writer objects in self.writers list
        for w in self.writers:
            # writer objects (from which the message didn't come) write message out
            # as utf-8 bytes which the client will decode
            if w != writer:
                await self.write_queue.put(w.write(
                f"{self.users[addr]!r}: {message!r}\n"
                .encode('utf-8')))

    async def announce(self, message):
        # announcements go to er body
        for w in self.writers:
            await self.write_queue.put(w.write(
            f"***{message!r}***\n"
            .encode('utf-8')))

    async def set_username(self, reader, writer, addr):
        # promt new user for username  
        writer.write(bytes('What username would you like to use? ','utf-8'))
        # wait for reader to read user response
        data = await reader.read(100)
        # handle bytes stuff
        username = data.decode().strip()
        # add to self.user dict
        self.users[addr] = username
        
        # tidy up
        await writer.drain()
        return username

    async def get_users(self, writer):
        user_list = []
        # iterate over users dict to build list
        for addr, username in self.users.items():
            user_list.append(username)
        # format string with user list
        message = f"Current users: {', '.join(user_list)!r}"
        # write it out
        writer.write(bytes(message + '\n', 'utf-8'))
        # tidy up
        await writer.drain()

    async def client_check(self, reader, writer):
        message = bytes("""Press Enter again to quit, 
        or enter any other value to remain online:... \n""", 'utf-8')
        writer.write(message)
        data = await reader.read(100)
        response = data.decode().strip()
        await writer.drain()
        return response

    async def send_dm(self, addr, message):
        try:
            # get sender
            for address, username in self.users.items():
                if address == addr:
                    sender = username

            # get recipient_name & associated writer
            for address, username in self.users.items():
                if f":{username}:" in message:
                    recipient_name = username
                    for w in self.writers:
                        if w.get_extra_info('peername') == address:
                            writer2 = w

            # clean up the message
            message = message.replace('/dm', '')
            message = message.replace(f":{recipient_name}:", '').strip()
            # send it        
            await self.write_queue.put(writer2.write(bytes(f"{Color.PURPLE}**DM FROM {sender}: {message}{Color.END_COLOR}\n", 'utf-8')))
            # clean up
            await writer2.drain()
        except Exception as e:
            print(str(e))


    async def handle(self, reader, writer):
        # add writer to list of writers
        self.writers.append(writer)
        # get addr from writer
        addr = writer.get_extra_info('peername')
        username = await self.set_username(reader, writer, addr)
        message = f"{username!r} joined!"
        print(message)
        await self.write_queue.put(message)
        # pass to announce, and free up while you wait
        await self.announce(message)
        
        # set reader to listen for incoming messages
        while True:
            # wait for reader to load data
            data = await reader.read(100)
            # decode bytes to utf-8
            message = data.decode().strip()

            # expose method for users to get current user list
            if message == "/users":
                await self.get_users(writer)
                # dont send <message> anywhere else
                continue

            # expose method for sending a DM
            if message.startswith('/dm'):
                await self.send_dm(addr, message)
                continue

            # catch closed terminal bug
            if message == '':
                response = await self.client_check(reader, writer)
                if response == '':
                    break

            # pass to forward, and free up while you wait
            else:
                await self.forward(writer, addr, message)
            # call writer.drain() to write from [clear] the loops' buffer, 
            # and free up while you wait
            await writer.drain()

            # if client text == 'exit', break loop; 
            # stop reader from listening
            if message == "exit":
                message = f"{addr!r} wants to close the connection."
                print(message)
                await self.forward(writer, "Server", message)
                break

        # if reader is stopped, clean up by removing writer from list of writers
        self.writers.remove(writer)
        writer.close()

    async def main(self):
        # start server; pass self.handle as a callback 
        # NOTE: the absence of parens -- asyncio calls it directly
        server = await asyncio.start_server(
            self.handle, '127.0.0.1', 8888)

        # claim first socketname for server
        addr = server.sockets[0].getsockname()
        self.printColor(f'Serving on {addr}', Color.TEAL)

        # use "async with" to clean up should the server be stopped abruptly
        async with server:
            await server.serve_forever()


if __name__ == '__main__':
    chat_server = ChatServer()
    asyncio.run(chat_server.main())
