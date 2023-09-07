import psutil
import curses
import time
import sys
from collections import defaultdict

def get_process_memory_usage():
    process_memory = defaultdict(int)

    for process in psutil.process_iter(['name', 'memory_info']):
        process_info = process.info
        process_name = process_info['name']
        memory_usage_bytes = process_info['memory_info'].rss  # Resident Set Size (RSS) in bytes
        memory_usage_mb = memory_usage_bytes / 1024 / 1024  # Convert bytes to megabytes
        process_memory[process_name] += memory_usage_mb  # Add memory usage to the total for that process

    return process_memory

def is_process_responsive(process_name):
    try:
        # Check if the process with the given name exists
        for process in psutil.process_iter(attrs=['name']):
            if process.info['name'] == process_name:
                return True
        return False
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
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

    # Dictionary to store timers for highlighted rows
    row_timers = {}

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
                # Check if the row has a timer set for red highlighting
                if i in row_timers and row_timers[i] > time.time():
                    stdscr.addstr(row, 0, f"{i:<7} {process_name:<30} {memory_usage:.2f} MB",
                                  curses.A_BOLD | curses.color_pair(2))
                else:
                    stdscr.addstr(row, 0, f"{i:<7} {process_name:<30} {memory_usage:.2f} MB", curses.A_BOLD)

                # Check if the process is responsive and label it accordingly
                if is_process_responsive(process_name):
                    stdscr.addstr(row, 45, "        Responsive", curses.color_pair(1))
                else:
                    stdscr.addstr(row, 45, "        Unresponsive", curses.color_pair(2))

                row += 1

        stdscr.refresh()

        # Listen for user input (non-blocking)
        stdscr.timeout(0)
        user_input = stdscr.getch()
        if user_input == ord('0'):  # Press '0' to quit the program
            sys.exit()
        elif ord('1') <= user_input <= ord('9'):  # Check if the input is between '1' and '9'
            index_to_quit = int(chr(user_input)) - 1  # Convert ASCII code to an integer index
            if 0 <= index_to_quit < len(sorted_data):
                process_name_to_quit = sorted_data[index_to_quit][0]
                try:
                    # Terminate the process by PID (Process ID)
                    for process in psutil.process_iter(attrs=['pid', 'name']):
                        if process.info['name'] == process_name_to_quit:
                            pid = process.info['pid']
                            psutil.Process(pid).terminate()
                            
                            # Set a timer for red highlighting (5 seconds)
                            row_timers[index_to_quit + 1] = time.time() + 5
                            break
                except psutil.NoSuchProcess:
                    pass
            else:
                # If the index is out of bounds, inform the user
                stdscr.addstr(max_y - 1, 0, "No process with that index number found", curses.A_BOLD)
                stdscr.refresh()

        # Wait for 0.5 seconds (500 milliseconds) before updating again
        time.sleep(0.5)

    # Cleanup curses on program exit
    curses.endwin()

if __name__ == "__main__":
    curses.wrapper(main)
