# asyncio-chat-server

To use: 
    Prerequisite: a local, running instance of https://github.com/jeff-vincent/language-processing-api

1. Clone the repo
2. Install Python3.7 (if not already installed)
3. From within the repo, run `pipenv shell`
4. Then, from within your newly created virtualenv, run: `python chat_server.py`
5. Open several other terminals, and from within them, run: `telnet 127.0.0.1 8888`
6. Set usernames, language preferences and begin messaging. 
7. To access a current user list, type: `/users`
8. To send a direct message to one other chat member, type: `/dm :recipient username: your message...`
9. To check the sentiment of a given message, type: `/sentiment message...`
