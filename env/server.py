import asyncio
import websockets
import ssl
import pathlib


async def main():
    print('Hello...')
    await asyncio.sleep(2)
    print('... World')


async def hello(websocket, path):
    # receive name from client
    name = await websocket.recv()
    print(f"< {name}")

    greeting = f"Hello {name}!"
    # send a greeting
    await websocket.send(greeting)
    print(f"> {greeting}")


async def consumer(message):
    print(f'message from client: {message}')


async def consumer_handler(websocket, path):
    async for message in websocket:
        await consumer(message)


print(f'Websocket server listening on ws://localhost:8888')

start_server = websockets.serve(consumer_handler, "192.168.1.5", 8888)
asyncio.get_event_loop().run_until_complete(start_server)
# asyncio.get_event_loop().run_forever()


# ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
# localhost_pem = pathlib.Path(__file__).with_name('localhost.pem')
# ssl_context.load_cert_chain(localhost_pem)
# start_server = websockets.serve(
# 	hello, 'localhost', 8765, ssl=ssl_context
# )
