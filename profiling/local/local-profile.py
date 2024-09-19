import tracemalloc

def memory_intensive_function():
    # Simulate memory usage
    big_data = []
    for i in range(1000):
        large_list = [x for x in range(10000)]
        big_data.append(large_list)
    return "Done"

# Start tracing memory allocations
tracemalloc.start()

# Before the function execution
snapshot1 = tracemalloc.take_snapshot()

# Call the function that uses memory
memory_intensive_function()

# After the function execution
snapshot2 = tracemalloc.take_snapshot()

# Compare the snapshots
stats = snapshot2.compare_to(snapshot1, 'lineno')

# Display top memory allocations
for stat in stats[:10]:  # Top 10 memory-consuming lines
    print(stat)
