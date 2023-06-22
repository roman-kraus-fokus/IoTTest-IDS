import time

def timestamp_in_hh_mm_ss(timestamp_in_ns):
    if timestamp_in_ns is None:
        return "None"
    return time.strftime('%H:%M:%S', time.localtime(timestamp_in_ns/1000000000))

def close_thread(t, name):
    print(f"[IDS] trying to end the {name} thread...")
    try:
        t.stop()
        print(f"[IDS] {name} thread stopped")
    except:
        print(f"[IDS] could not stop {name} thread")
    try:
        t.join()
        print(f"[IDS] {name} thread joined")
    except:
        print(f"[IDS] could not join {name} thread")

