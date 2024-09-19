from memory_profiler import profile

@profile
def memory_intensive_function():
    big_data = []
    for i in range(1000):
        large_list = [x for x in range(1000)]
        big_data.append(large_list)
    return "Done"

if __name__ == '__main__':
    print("Using memory_profiler")
    memory_intensive_function()



