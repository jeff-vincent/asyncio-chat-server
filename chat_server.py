import asyncio

class ChatServer:

    def __init__(self):
        self.writers = []
        self.users = {}

    async def forward(self, writer, addr, message):
        # iterate over writer objects in self.writers list
        for w in self.writers:
            # writer objects (from which the message didn't come) write message out
            # as utf-8 bytes which the client will decode
            if w != writer:
                w.write(f"{self.users[addr]!r}: {message!r}\n".encode('utf-8'))

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

    async def handle(self, reader, writer):
        # add writer to list of writers
        self.writers.append(writer)
        # get addr from writer
        addr = writer.get_extra_info('peername')
        username = await self.set_username(reader, writer, addr)
        message = f"Username: {username!r} added."
        print(message)
        # pass to self.forward, and free up while you wait
        await self.forward(writer, addr, message)
        
        # set reader to listen for incoming messages
        while True:
            # wait for reader to load data
            data = await reader.read(100)
            # decode bytes to utf-8
            message = data.decode().strip()
            # pass to forward, and free up while you wait
            await self.forward(writer, addr, message)
            # call writer.drain() to write from [clear] the loops' buffer, 
            # and free up while you wait
            await writer.drain()
            # if client text == 'exit', break loop; 
            # stop reader from listening
            if message == "exit":
                message = f"{addr!r} wants to close the connection."
                print(message)
                self.forward(writer, "Server", message)
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
        print(f'Serving on {addr}')
        # use "async with" to clean up should the server be stopped abruptly
        async with server:
            await server.serve_forever()

chat_server = ChatServer()
asyncio.run(chat_server.main())
