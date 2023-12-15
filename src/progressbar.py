"""
Progress Bar Module.
"""
import sys, os
from io import StringIO
import time
from typing import Iterable

class ProgressBar:
    """
    Progress bar. lets go.
    """
    def __init__(self, items: int | Iterable) -> None:
        """
        Create the progress bar.

        Accepts either the amount of items or the iterable the bar is for. Supplying a list will automatically
        set the max value to the list's length.
        """
        if isinstance(items, list):
            self.MAX = len(items)
        else:
            self.MAX = items

        # Standard Output holder.        
        self.__STDOUT = None
        # StringIO holder.
        self.__IO = None

        self.__last_io = []

    def __enter__(self):
        # Save whatever stdout is so we can restore it later.
        self.__STDOUT = sys.stdout

        # Change stdout to a fake output so we can capture all requests.
        self.__IO = StringIO()
        sys.stdout = self.__IO

        # Return ourself to expose ProgressBar.
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore stdout to whatever it was before.
        sys.stdout = self.__STDOUT

    def bar(self, title="", empty="-", fill="=", size: int | None = None):
        """
        The actual progress bar.

        Uses whatever its parent ProgressBar's MAX value is as the expected item count.
        
        Example
        ---
        >>> from time import sleep
        >>> from progressbar import ProgressBar
        >>> with ProgressBar(40) as bar:
        >>>     for i in bar.bar("bar :D "):
        >>>         print(f"Iteration: {i}")
        >>>         print("Hello, world!")
        >>>     sleep(0.1)
        
        ---
        @title: (str) Displayed in front of the progress bar.
        @empty: (str) The character(s) to use for empty spaces. Defaults to `-`
        @fill: (str) The character(s) to use for filled spaces. Defaults to `=`
        @size: (int/None) Force the size of the bar. If not supplied, the bar will attempt to dynamically resize
        as it progresses. Note that setting this manually can cause issues 
        and crashes if the bar is too big for the terminal.
        """
        count = len(range(self.MAX))
        start = time.time()

        def show(j, size):
            """
            Internal function.

            This does the actual work of creating the bar and handling any outside printing.

            Size has to be supplied because Python is confused otherwise.
            """

            remaining = ((time.time() - start) / j) * (count - j)

            mins, sec = divmod(remaining, 60)

            # Assemble the end string for the final bar.
            time_str = f"{int(mins):02}:{sec:05.2f}"
            end_str = f"{j}/{count} est: {time_str}"
            
            if not size:
                # Determine the size of the bar dynamically.
                size = (os.get_terminal_size().columns-2) - len(end_str) - len(title) - (len(fill)+len(empty))
            
            x = int(size*j/count)

            # Check if external things have been printed.
            current_io = []

            # force every line to be unique, so we only print them once.
            for i, msg in enumerate(self.__IO.getvalue().split("\n")[:-1]):
                # i is just the index of the message since StringIO doesn't purge old ones
                newmsg = f"{i}__{msg}"
                if newmsg not in current_io and newmsg:
                    current_io.append(newmsg)

            if current_io != self.__last_io:
                # Clear the line, in case the progress bar is occupying it. 
                print("\r\033[K", file=self.__STDOUT, end="\r")
                
                for msg in current_io:
                    if msg not in self.__last_io:
                        print(msg.split("__", 1)[1], file=self.__STDOUT)
                
                self.__last_io = current_io


            final_str = f"{title}[{fill*x}{(empty*(size-x))}] " + end_str
            if len(final_str) > os.get_terminal_size().columns:
                raise ValueError("Width larger than console!")
            print(final_str, end="", file=self.__STDOUT, flush=True)

        for i, item in enumerate(range(self.MAX)):
            yield item
            show(i+1, size)
        print("\n", end="", flush=True, file=self.__STDOUT)
