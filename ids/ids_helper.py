
def close_thread(t, name):
    print(f"trying to end the {name} thread...")
    try:
        t.stop()
        print(f"{name} thread stopped")
    except:
        print(f"could not stop {name} thread")
    try:
        t.join()
        print(f"{name} thread joined")
    except:
        print(f"could not join {name} thread")

