import asyncio
import websockets

async def hello():
	HOST = 'localhost'
	PORT = 8888
	uri = f"ws://{HOST}:{PORT}"

	async with websockets.connect(uri) as websocket:
		name = input("what's you name ? ")

		await websocket.send(name)
		print(f"> {name}")

		greeting = await websocket.recv()
		print(f"< {greeting}")

asyncio.get_event_loop().run_until_complete(hello())
