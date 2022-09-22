class DepthCounter:
    def __init__(self):
        self.count = 0

    async def __aenter__(self):
        self.count += 1

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.count -= 1
