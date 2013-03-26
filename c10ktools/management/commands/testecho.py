import random

import tulip

from django.core.management.base import NoArgsCommand

from c10ktools.clients.tulip import connect_websocket


class Command(NoArgsCommand):

    CLIENTS = 10000
    DELAY = 60
    ECHO_URL = 'ws://localhost:8000/test/ws/'

    def handle_noargs(self, **options):
        self.count = 0
        connections = [self.test_echo() for _ in range(self.CLIENTS)]
        tulip.get_event_loop().run_until_complete(tulip.wait(connections))
        assert self.count == 0

    @tulip.coroutine
    def test_echo(self):

        # Distribute the connections a bit
        yield from tulip.sleep(2 * self.DELAY * random.random())
        ws = yield from connect_websocket(self.ECHO_URL)

        self.count += 1
        if self.count % (self.CLIENTS * 3 // self.DELAY) == 0:
            print("> {:5} connections".format(self.count))
        if self.count == self.CLIENTS:
            print()
            print("{} clients are connected!".format(self.count))
            print()

        messages = []
        messages.append((yield from ws.read_message()))
        yield from tulip.sleep(self.DELAY)
        ws.write_message('Spam?')
        messages.append((yield from ws.read_message()))
        yield from tulip.sleep(self.DELAY)
        ws.write_message('Eggs!')
        messages.append((yield from ws.read_message()))
        yield from tulip.sleep(self.DELAY)
        ws.write_message('Python.')
        messages.append((yield from ws.read_message()))
        messages.append((yield from ws.read_message()))
        assert messages == [
            "Hello!",
            "1. Spam?",
            "2. Eggs!",
            "3. Python.",
            "Goodbye!",
        ]

        ws.close()

        self.count -= 1
        if self.count % (self.CLIENTS * 3 // self.DELAY) == 0:
            print("< {:5} connections".format(self.count))
