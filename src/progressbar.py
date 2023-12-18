"""
Progress Bar Module.
"""
import sys, os
import time
import threading
from io import StringIO
from typing import Iterable

class ProgressBar:
    """
    Progress bar. lets go.
    """
    def __init__(self, items: int | Iterable, title="", empty="-", fill="=", resize: int | None = None) -> None:
        """
        The actual progress bar.

        Uses whatever its parent ProgressBar's MAX value is as the expected item count.
        
        Example
        ---
        >>> with ProgressBar(90, "Hello!", " ", "*") as bar:
        >>>     # Changes the default spinner. Accepts either a string of characters or a list.
        >>>     # bar.spinner = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        >>>     # bar.spinner = ["_", "_", "_", "-", "`", "`", "'", "´", "-", "_", "_", "_"]
        >>>     for i, item in enumerate(range(90)):
        >>>         print(f"Iteration: {i}")
        >>>         print("Hello, world!")
        >>>         sleep(0.1)
        >>>         bar.bar() # This should always be called last.
        
        args
        ---
        @items: (str) Either the amount of expected items, or the list to be iterated over.
        @title: (str) Displayed in front of the progress bar.
        @empty: (str) The character(s) to use for empty spaces. Defaults to `-`
        @fill: (str) The character(s) to use for filled spaces. Defaults to `=`
        @size: (int/None) Force the size of the bar. If not supplied, the bar will attempt to dynamically resize
        as it progresses. Note that setting this manually can cause issues 
        and crashes if the bar is too big for the terminal.
        """
        if isinstance(items, list):
            self.MAX = len(items)
        else:
            self.MAX = items

        # Public
        self.title = title
        self.empty = empty
        self.fill = fill
        self.size = 0
        self.resize = resize
        self.spinner = "/-\\|"

        # Private
        self.__running = True
        self.__count = len(range(self.MAX))
        self.__start = time.time()
        self.__index = 0
        self.__spinner_index = 0
        self.__last_io = []
        self.__STDOUT = None
        self.__IO = None

    def __show(self, j, start, count):
        """
        Internal function.

        This does the actual work of creating the bar and handling any outside printing.

        Size has to be supplied because Python is confused otherwise.
        """

        remaining = ((time.time() - start) / j) * (count - j)

        mins, sec = divmod(remaining, 60)

        # Get the current spinner, or replace it with the finish symbol.
        if self.__index != self.MAX:
            spinner = self.spinner[self.__spinner_index]
        else:
            spinner = "✓"

        # Assemble the end string for the final bar.
        time_str = f"{int(mins):02}:{sec:05.2f}"
        end_str = f"{j}/{count} est: {time_str}"

        if not self.size or os.get_terminal_size().columns > self.size:
            # Determine the size of the bar dynamically.
            self.size = (os.get_terminal_size().columns-6) - len(end_str) - len(self.title) - (len(self.fill)+len(self.empty)) - len(spinner)
        if self.resize:
            self.size = self.resize

        x = int(self.size*j/count)

        # Check if external things have been printed.
        current_io = []

        # force every line to be unique, so we only print them once.
        for i, msg in enumerate(self.__IO.getvalue().split("\n")[:-1]):
            # i is just the index of the message since StringIO doesn't purge old ones
            newmsg = f"{i}__{msg}"
            if newmsg not in current_io and newmsg:
                current_io.append(newmsg)

        # Clear the line, in case the progress bar is occupying it. 
        print("\r\033[K", file=self.__STDOUT, end="\r")
        if current_io != self.__last_io:                
            for msg in current_io:
                if msg not in self.__last_io:
                    print(msg.split("__", 1)[1], file=self.__STDOUT)
            
            self.__last_io = current_io


        final_str = f"{self.title}[{self.fill*x}{(self.empty*(self.size-x))}] {spinner} " + end_str

        self.__spinner_index += 1
        self.__spinner_index %= len(self.spinner)
        if len(final_str) > os.get_terminal_size().columns:
            return
        print(final_str, end="", file=self.__STDOUT, flush=True)

    def __loop(self):
        """
        Bar loop. Allows for the bar to update without anything actually changing.
        """
        while self.__running:
            if self.__index == self.MAX:
                self.__running = False
                break
            self.__show(self.__index+1, self.__start, self.__count)
            time.sleep(0.2)

    def __enter__(self):
        # Save whatever stdout is so we can restore it later.
        self.__STDOUT = sys.stdout

        # Change stdout to a fake output so we can capture all requests.
        self.__IO = StringIO()
        sys.stdout = self.__IO

        t = threading.Thread(target=self.__loop)
        # Dies when main thread dies.
        t.daemon = True
        t.start()

        # Return ourself to expose ProgressBar.
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore stdout to whatever it was before.
        sys.stdout = self.__STDOUT
        # Ensure our seperate thread does actually exit.
        self.__running = False

        # Ensure that we show the final value.
        self.__show(self.__index, self.__start, self.__count)
        print("\n", end="", flush=True)

    def bar(self):
        """
        Moves the bar forward one.
        """
        # self.__show(self.__index+1, self.__start, self.__count)
        self.__index += 1
