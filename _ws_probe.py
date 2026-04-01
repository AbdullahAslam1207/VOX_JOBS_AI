import asyncio
import json
import websockets

async def main():
    uri = 'ws://127.0.0.1:8000/ws/mock_interview_voice'
    async with websockets.connect(uri) as ws:
        print('connected')
        print('recv1', await ws.recv())
        await ws.send(json.dumps({'action': 'start_interview', 'target_field': 'Backend Engineer', 'max_rounds': 3}))
        for _ in range(4):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(msg, bytes):
                    print('recv bytes', len(msg))
                else:
                    print('recv text', msg)
            except Exception as ex:
                print('timeout/error', ex)
                break

asyncio.run(main())
