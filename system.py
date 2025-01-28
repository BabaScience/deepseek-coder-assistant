import psutil

def print_system_stats():
    print(f"Memory usage: {psutil.virtual_memory().percent}%")
    print(f"CPU usage: {psutil.cpu_percent()}%")
    if torch.cuda.is_available():
        print(f"GPU memory: {torch.cuda.memory_allocated()/1e9:.2f} GB used")

print_system_stats()