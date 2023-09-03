import wmi
import curses
import time
from collections import defaultdict

def get_process_memory_usage():
    f = wmi.WMI()
    process_memory = defaultdict(int)

    for process in f.Win32_Process():
        process_name = process.Name
        memory_usage_bytes = int(process.WorkingSetSize)  # Convert to integer for bytes
        memory_usage_mb = memory_usage_bytes / 1024 / 1024  # Convert bytes to megabytes
        process_memory[process_name] += memory_usage_mb  # Add memory usage to the total for that process

    return process_memory

def is_process_responsive(process):
    try:
        # Try to get the CPU usage of the process
        process.GetOwner()
        return True
    except Exception:
        return False

def main(stdscr):
    curses.initscr()
    curses.curs_set(0)
    stdscr.clear()
    stdscr.refresh()

    # Initialize colors
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Responsive text color
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)  # Unresponsive text color

    # Get terminal dimensions
    max_y, max_x = stdscr.getmaxyx()

    while True:
        process_memory = get_process_memory_usage()
        sorted_data = sorted(process_memory.items(), key=lambda x: x[1], reverse=True)

        # Clear the screen
        stdscr.clear()

        # Display data starting from row 1
        row = 1

        # Print the header with formatting
        stdscr.addstr(0, 0, "Index   Process Name               Memory Usage (MB)",
                      curses.A_BOLD | curses.A_UNDERLINE)

        # Iterate through the sorted data and print in columns, limiting rows
        for i, (process_name, memory_usage) in enumerate(sorted_data, start=1):
            if row < max_y - 1:  # Ensure it fits within the terminal
                stdscr.addstr(row, 0, f"{i:<7} {process_name:<30} {memory_usage:.2f} MB", curses.A_BOLD)

                # Check if the process is responsive and label it accordingly
                process = wmi.WMI().Win32_Process(Name=process_name)
                if is_process_responsive(process[0]):
                    stdscr.addstr(row, 45, "        Responsive", curses.color_pair(1))
                else:
                    stdscr.addstr(row, 45, "        Unresponsive", curses.color_pair(2))

                row += 1

        stdscr.refresh()

        # Wait for 0.5 seconds (500 milliseconds) before updating again
        time.sleep(0.5)

    # Cleanup curses on program exit
    curses.endwin()

if __name__ == "__main__":
    curses.wrapper(main)
