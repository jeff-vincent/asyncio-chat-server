import asyncio

class ChatServer:

    def __init__(self):
        self.writers = []

    async def forward(self, writer, addr, message):
        for w in self.writers:
            if w != writer:
                w.write(f"{addr!r}: {message!r}\n".encode('utf-8'))

    async def handle(self, reader, writer):
        self.writers.append(writer)
        addr = writer.get_extra_info('peername')
        message = f"{addr!r} is connected !!!!"
        print(message)
        await self.forward(writer, addr, message)
        while True:
            data = await reader.read(100)
            message = data.decode().strip()
            await self.forward(writer, addr, message)
            await writer.drain()
            if message == "exit":
                message = f"{addr!r} wants to close the connection."
                print(message)
                self.forward(writer, "Server", message)
                break
        self.writers.remove(writer)
        writer.close()

    async def main(self):
        server = await asyncio.start_server(
            self.handle, '127.0.0.1', 8888)

        addr = server.sockets[0].getsockname()
        print(f'Serving on {addr}')
        async with server:
            await server.serve_forever()

chat_server = ChatServer()
asyncio.run(chat_server.main())