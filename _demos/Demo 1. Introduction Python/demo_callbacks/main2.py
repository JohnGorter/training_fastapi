import threading
import time


def run_washing_machine(callback):
    print("1. Washing machine started in background...")
    time.sleep(3)  # Simulates background work
    result = "Clean Laundry"

    # Explicitly invoke the callback function upon task completion
    callback(result)

def sweep_floor():
    print("2. Sweeping the floor while laundry runs...")
    time.sleep(1)
    print("3. Floor swept!")


print("--- ASYNCHRONOUS START (THREADS) ---")
start_time = time.time()

# 1. Create a thread and pass the callback function as an argument
laundry_thread = threading.Thread(
    target=run_washing_machine, args=(lambda result: print(f"4. Callback Triggered: Received '{result}'. Folding clothes now!"),)
)

# 2. Start the thread (non-blocking)
laundry_thread.start()

# 3. Main thread immediately moves to sweeping without waiting
sweep_floor()

# 4. Wait for the background thread to finish before exiting
laundry_thread.join()

print(f"Total time taken: {round(time.time() - start_time, 2)} seconds")