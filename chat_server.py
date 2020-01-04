import asyncio

class ChatServer:

    def __init__(self):
        self.writers = []

    async def forward(self, writer, addr, message):
        # iterate over writer objects in self.writers list
        for w in self.writers:
            # writer objects (from which the message didn't come) write message out
            if w != writer:
                w.write(f"{addr!r}: {message!r}\n".encode('utf-8'))

    async def handle(self, reader, writer):
        # add writer to list of writers
        self.writers.append(writer)
        # get addr from writer object
        addr = writer.get_extra_info('peername')
        # format string
        message = f"{addr!r} is connected !!!!"
        print(message)
        # pass to self.forward, and free up while you wait
        await self.forward(writer, addr, message)
        
        # run server
        while True:
            # wait for reader to load data
            data = await reader.read(100)
            # decode bytes to utf-8
            message = data.decode('utf-8').strip()
            # pass to forward, and free up while you wait
            await self.forward(writer, addr, message)
            # call writer.drain() to write from the loops' buffer, 
            # and free up while you wait for it to run
            await writer.drain()
            # if client text == 'exit', break loop; stop server
            if message == "exit":
                message = f"{addr!r} wants to close the connection."
                print(message)
                self.forward(writer, "Server", message)
                break
        # if server stopped, clean up
        self.writers.remove(writer)
        writer.close()

    async def main(self):
        # start server; pass self.handle() as a callback
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