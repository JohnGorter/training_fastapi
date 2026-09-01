import asyncio


def main():
    print("Hello from demo-async!")
    import asyncio
    asyncio.run(download())


async def download():
    print("Downloading data...")
    await asyncio.sleep(2)  # Simulate a download delay

if __name__ == "__main__":
    main()
