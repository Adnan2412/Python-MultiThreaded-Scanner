import socket
import threading
from queue import Queue
import time

# SETTINGS
TARGET = "scanme.nmap.org"  # Change this to your target IP
START_PORT = 1
END_PORT = 1000            # Scanning 1-1000 for speed
THREAD_COUNT = 50          # How many threads (workers) to run at once

# Thread-safe queue to hold the ports we need to scan
queue = Queue()
open_ports = []

def get_banner(s):
    """
    Attempts to grab the service banner (version info) from the port.
    """
    try:
        # Receive up to 1024 bytes of data
        return s.recv(1024).decode().strip()
    except:
        return "Unknown Service"

def scan_port(port):
    """
    Tries to connect to a specific port. If successful, grabs the banner.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2) # Don't wait forever if port is unresponsive
        
        # Try to connect
        result = s.connect_ex((TARGET, port))
        
        if result == 0:
            # Connection successful! Now try to grab the banner.
            # We need a new socket object for receiving data reliably
            # or we can reuse 's' if we handle it carefully. 
            # For simplicity, we just mark it open here.
            
            # To actually grab banner, we need a full connection:
            try:
                s_banner = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s_banner.settimeout(2)
                s_banner.connect((TARGET, port))
                banner = get_banner(s_banner)
                s_banner.close()
            except:
                banner = "Could not grab banner"
                
            print(f"[+] Port {port} is OPEN : {banner}")
            open_ports.append(port)
        
        s.close()
    except Exception as e:
        pass

def worker():
    """
    The worker thread function. It pulls a port from the queue and scans it.
    """
    while not queue.empty():
        port = queue.get()
        scan_port(port)
        queue.task_done()

def run_scanner():
    print(f"Scanning target: {TARGET}")
    print(f"Scanning ports: {START_PORT} to {END_PORT}")
    print(f"Threads: {THREAD_COUNT}")
    print("-" * 50)
    
    start_time = time.time()

    # 1. Fill the queue with port numbers
    for port in range(START_PORT, END_PORT + 1):
        queue.put(port)

    # 2. Create and start threads
    thread_list = []
    for _ in range(THREAD_COUNT):
        thread = threading.Thread(target=worker)
        thread_list.append(thread)

    for thread in thread_list:
        thread.start()

    # 3. Wait for all threads to finish
    for thread in thread_list:
        thread.join()

    end_time = time.time()
    print("-" * 50)
    print(f"Scan completed in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    run_scanner()
