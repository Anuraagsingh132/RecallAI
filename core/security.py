class PayloadTooLargeError(Exception):
    pass

class MaxBodySizeMiddleware:
    """
    ASGI Middleware that strictly enforces a maximum request body size
    without buffering the payload into memory or blocking the event loop.
    It reads chunks incrementally from the ASGI stream and severs the
    connection if the cumulative sum exceeds the maximum allowed size.
    """
    def __init__(self, app, max_size: int):
        self.app = app
        self.max_size = max_size

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # 1. Quick check on Content-Length header (if present)
        # Prevents even starting the stream if header already admits it's too big
        content_length = None
        for name, value in scope.get("headers", []):
            if name.lower() == b"content-length":
                try:
                    content_length = int(value)
                except ValueError:
                    pass
                break
        
        if content_length is not None and content_length > self.max_size:
            await self.send_413(send)
            return

        # 2. Incremental stream validation for missing/spoofed Content-Length
        # or chunked transfer encoding
        total_bytes = 0
        response_started = False

        async def wrapped_send(message):
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        async def wrapped_receive():
            nonlocal total_bytes
            message = await receive()
            if message["type"] == "http.request":
                chunk_size = len(message.get("body", b""))
                total_bytes += chunk_size
                if total_bytes > self.max_size:
                    raise PayloadTooLargeError()
            return message

        try:
            await self.app(scope, wrapped_receive, wrapped_send)
        except PayloadTooLargeError:
            if not response_started:
                await self.send_413(send)
            else:
                # Response already started by the app before limit was reached
                raise

    async def send_413(self, send):
        await send({
            "type": "http.response.start",
            "status": 413,
            "headers": [
                (b"content-type", b"application/json"),
                (b"connection", b"close")
            ]
        })
        await send({
            "type": "http.response.body",
            "body": b'{"detail": "Payload Too Large"}',
            "more_body": False
        })
