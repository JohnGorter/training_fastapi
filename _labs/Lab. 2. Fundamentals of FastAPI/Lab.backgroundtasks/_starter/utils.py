import asyncio
import sys
import time
from fastapi import UploadFile
from mymail import sendEmail

background_tasks_set: set[asyncio.Task] = set()

async def start_external_process(image:UploadFile):
    async def process_file_in_worker_process(args):
        process = await asyncio.create_subprocess_exec(
                sys.executable,
                "external_process.py",
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        _ = await process.communicate()
        if process.returncode == 0:
            await sendEmail("test@me.nl", "test@you.nl", "image processing complete!", "Your image is processed!")

    print(f"handing processing file off to external process")
    task = asyncio.create_task(process_file_in_worker_process([str(image.size)]))
    background_tasks_set.add(task)
    task.add_done_callback(background_tasks_set.discard)

# your code here
async def process_file_in_background():
    print(f"processing file in background")
    time.sleep(3)
    await sendEmail("test@me.nl", "test@you.nl", "image processing complete!", "Your image is processed!")

