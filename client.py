import asyncio
import random
import datetime
import logging
from config import HOST, PORT, LOGGING_FORMAT, DATE_FORMAT, TIME_FORMAT


class Client:
    def __init__(self, filename):
        self.host = HOST
        self.port = PORT
        self.request_count = 0
        self.filename = filename

        self.logger = logging.getLogger(f"logs/Client-{filename}")
        handler = logging.FileHandler(self.filename)
        formatter = logging.Formatter("%(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    async def connect_to_server(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        self.logger.info(f"Connected to server at {self.host}:{self.port}")

    async def send_ping(self):
        timestamp = datetime.datetime.now().strftime(LOGGING_FORMAT)
        message = f"[{self.request_count}] PING"
        self.writer.write(message.encode() + b"\n")
        await self.writer.drain()
        self.request_count += 1
        return timestamp, message

    async def receive_pong(self):
        response_time = datetime.datetime.now().strftime(TIME_FORMAT)
        response_date = datetime.datetime.now().strftime(DATE_FORMAT)
        data = await asyncio.wait_for(self.reader.readline(), timeout=1)
        response = data.decode().strip()
        return response_date, response_time, response

    async def close_connection(self):
        self.writer.close()
        await self.writer.wait_closed()
        self.logger.info("Connection closed")


async def main():
    client1 = Client("logs/client1.log")
    client2 = Client("logs/client2.log")

    await client1.connect_to_server()
    await client2.connect_to_server()

    try:
        while True:
            await asyncio.sleep(random.uniform(0.3, 3.0))
            timestamp, message = await client1.send_ping()
            while True:
                try:
                    response_date, response_time, response = await asyncio.wait_for(
                        client1.receive_pong(), timeout=1
                    )
                    if "keepalive" in response:
                        client1.logger.info(
                            "%s; %s; %s", response_date, response_time, response
                        )
                    else:
                        break
                except asyncio.TimeoutError:
                    response = "(таймаут)"
                    break
            client1.logger.info(
                    "%s; %s; %s; %s",
                    timestamp,
                    message,
                    response_time,
                    response,
                )

            await asyncio.sleep(random.uniform(0.3, 3.0))
            timestamp, message = await client2.send_ping()
            while True:
                try:
                    response_date, response_time, response = await asyncio.wait_for(
                        client2.receive_pong(), timeout=1
                    )
                    if "keepalive" not in response:
                        break
                    else:
                        client2.logger.info(
                            "%s; %s; %s", response_date, response_time, response
                        )
                except asyncio.TimeoutError:
                    response = "(таймаут)"
                    break
            if response == "(таймаут)":
                client2.logger.info("%s; %s; %s", timestamp, message, response)
            else:
                client2.logger.info(
                    "%s; %s; %s; %s",
                    timestamp,
                    message,
                    response_time,
                    response,
                )
    except KeyboardInterrupt:
        await client1.close_connection()
        await client2.close_connection()


asyncio.run(main())
