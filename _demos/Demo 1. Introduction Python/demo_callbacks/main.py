import time


def run_washing_machine():
    print("1. Washing machine started...")
    time.sleep(3)  # Blocks execution completely for 3 seconds
    print("2. Washing machine finished!")


def sweep_floor():
    print("3. Sweeping the floor...")
    time.sleep(1)
    print("4. Floor swept!")


print("--- SYNCHRONOUS START ---")
start_time = time.time()

# Must wait for laundry to finish before sweeping can even begin
run_washing_machine()
sweep_floor()

print(f"Total time taken: {round(time.time() - start_time, 2)} seconds\n")