import asyncio
import random
import datetime
import logging
from config import HOST, PORT, DATE_FORMAT, TIME_FORMAT


class Server:
    def __init__(self):
        self.host = HOST
        self.port = PORT
        self.clients = {}
        self.message_count = 0
        self.client_counter = 0

        logging.basicConfig(
            level=logging.INFO,
            format="%(levelname)s - %(message)s",
            filename="logs/server.log",
            filemode="a",
        )

    async def handle_client(self, reader, writer):
        self.client_counter += 1
        client_id = self.client_counter
        self.clients[client_id] = writer

        try:
            while True:
                data = await reader.readline()
                if not data:
                    break
                message = data.decode().strip()
                current_time = datetime.datetime.now()
                received_date = current_time.strftime(DATE_FORMAT)
                received_time = current_time.strftime(TIME_FORMAT)
                await self.process_message(
                    message, writer, received_date, received_time, client_id
                )
        finally:
            del self.clients[client_id]
            writer.close()

    async def process_message(
        self, message, writer, received_date, received_time, client_id
    ):
        ignore = random.randint(1, 10) == 1
        response_time = datetime.datetime.now().strftime(TIME_FORMAT)

        if ignore:
            logging.info(
                "%s; %s; %s; (проигнорировано)",
                received_date,
                received_time,
                message,
            )
            return

        request_number = message.strip("[] PING")
        await asyncio.sleep(random.uniform(0.1, 1.0))
        response = f"[{self.message_count}/{request_number}] PONG ({client_id})"
        writer.write(response.encode() + b"\n")
        await writer.drain()

        logging.info(
            "%s; %s; %s; %s; %s",
            received_date,
            received_time,
            message,
            response_time,
            response,
        )
        self.message_count += 1

    async def send_keepalive(self):
        while True:
            await asyncio.sleep(5)
            for client_id, writer in self.clients.items():
                response = f"[{self.message_count}] keepalive"
                writer.write(response.encode() + b"\n")
                await writer.drain()
                logging.info(
                    "%s; %s; %s",
                    datetime.datetime.now().strftime(DATE_FORMAT),
                    datetime.datetime.now().strftime(TIME_FORMAT),
                    response,
                )
                self.message_count += 1


async def main():
    server = Server()
    server_task = asyncio.create_task(server.send_keepalive())

    server_coroutine = asyncio.start_server(
        server.handle_client, server.host, server.port
    )
    server = await server_coroutine
    print(f"Server started on {server.sockets[0].getsockname()}")

    await server_task


asyncio.run(main())
