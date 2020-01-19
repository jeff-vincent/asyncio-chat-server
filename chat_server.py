import asyncio

class Color:
 RED = '\033[91m'
 GREEN = '\033[92m'
 YELLOW = '\033[93m'
 BLUE = '\033[94m'
 PURPLE = '\033[95m'
 TEAL = '\033[96m'
 END_COLOR = '\033[00m'

class User:

    def __init__(self, reader, writer, addr):
        self.reader = reader
        self.writer = writer
        self.addr = addr
        self.username = ''
        self.print_color = ''


class ChatServer:

    def __init__(self):
        self.users = []
        self.write_queue = asyncio.Queue()
        self.last_print_color_assigned = ''

    def printColor(self, string, color):
        print('{} {}\033[00m'.format(color, string))

    async def forward(self, user, message):
        # iterate over writer objects in self.writers list
        sender = user
        for user in self.users:
            if user != sender:

                await self.write_queue.put(user.writer.write(
                f"{sender.print_color}{sender.username!r}: {message!r}{Color.END_COLOR}\n"
                .encode('utf-8')))

    async def announce(self, message):
        # announcements go to er body
        for user in self.users:
            await self.write_queue.put(user.writer.write(
            f"***{message!r}***\n"
            .encode('utf-8')))

    async def get_print_color(self):
        if self.last_print_color_assigned == Color.TEAL:
            self.last_print_color_assigned = Color.RED
            return Color.RED
        elif self.last_print_color_assigned == Color.RED:
            self.last_print_color_assigned = Color.GREEN
            return Color.GREEN
        elif self.last_print_color_assigned == Color.GREEN:
            self.last_print_color_assigned = Color.YELLOW
            return Color.YELLOW
        elif self.last_print_color_assigned == Color.YELLOW:
            self.last_print_color_assigned = Color.BLUE
            return Color.BLUE
        elif self.last_print_color_assigned == Color.BLUE:
            self.last_print_color_assigned = Color.PURPLE
            return Color.PURPLE
        else:
            self.last_print_color_assigned = Color.TEAL
            return Color.TEAL


    async def create_user(self, reader, writer, addr):

        user = User(reader, writer, addr)
        # promt new user for username  
        user.writer.write(bytes
        ('What username would you like to use? ','utf-8'))
        # wait for reader to read user response
        data = await user.reader.read(100)
        user.username = data.decode().strip()
        user.print_color = await self.get_print_color()

        # add to self.user dict
        self.users.append(user)
        
        # tidy up
        await writer.drain()
        return user

    async def get_users(self, writer):
        user_list = []
        # iterate over users dict to build list
        for user in self.users:
            user_list.append(user.username)
        # format string with user list
        message = f"Current users: {', '.join(user_list)!r}"
        # write it out
        writer.write(bytes(message + '\n', 'utf-8'))
        # tidy up
        await writer.drain()

    async def client_check(self, reader, writer):
        message = bytes('Press Enter again to quit,or enter any other value to remain online:... \n', 'utf-8')
        writer.write(message)
        data = await reader.read(100)
        response = data.decode().strip()
        await writer.drain()
        return response

    async def send_dm(self, user, message):
        try:

            sender = user

            # get recipient_name & associated writer
            for user in self.users:
                if f":{user.username}:" in message:
                    recipient_name = user.username
                    writer2 = user.writer

            # clean up the message
            message = message.replace('/dm', '')
            message = message.replace(f":{recipient_name}:", '').strip()
            # send it        
            await self.write_queue.put(writer2.write(bytes
            (f"**DM FROM {sender.username}: {message}\n", 'utf-8')))
            # clean up
            await writer2.drain()
        except Exception as e:
            print(str(e))


    async def handle(self, reader, writer):

        # get addr from writer
        addr = writer.get_extra_info('peername')
        new_user = await self.create_user(reader, writer, addr)
        message = f"{new_user.username} joined!"
        
        await self.write_queue.put(message)
        # pass to announce, and free up while you wait
        await self.announce(message)
        
        # set reader to listen for incoming messages
        while True:
            # wait for reader to load data
            data = await new_user.reader.read(100)
            # decode bytes to utf-8
            message = data.decode().strip()

            # expose method for users to get current user list
            if message == "/users":
                await self.get_users(new_user.writer)
                # dont send <message> anywhere else
                continue

            # expose method for sending a DM
            if message.startswith('/dm'):
                await self.send_dm(new_user, message)
                continue

            # catch closed terminal bug
            if message == '':
                response = await self.client_check(reader, writer)
                if response == '':
                    break

            # pass to forward, and free up while you wait
            else:
                await self.forward(new_user, message)
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
        self.users.remove(new_user)
        new_user.writer.close()

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
