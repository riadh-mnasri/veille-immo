import asyncio

# File partagée entre le scanner et le serveur web pour les SSE
sse_queue: asyncio.Queue = asyncio.Queue()
