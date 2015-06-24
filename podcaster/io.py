"""IO interfaces
"""
import signal
import sys


class TimeoutError(BaseException):
    """Indicates a timeout
    """
    pass


class BaseIO(object):
    """An IO interface
    """
    def input_(self, prompt_str=''):
        """Prompt the user for string input and return the result.

        prompt_str: The string to display while prompting the user
        """
        raise NotImplementedError

    def write(self, str_):
        """Write the string `str_` to the IO output
        """
        raise NotImplementedError

    def print_(self, *args):
        """Write each element of `args` to the IO output with a trailing newline
        """
        raise NotImplementedError

    def flush(self):
        """Ensure all output is flushed from internal buffers
        """
        raise NotImplementedError


class BaseAsyncIO(BaseIO):
    """Enhance BaseIO with an interface for asynchronous input
    """
    def async_input(self, prompt_str):
        """If the user responds within some number of seconds (as determined by
            the subclass implementation), return the user's input
        Else, return None

        prompt_str:  The string to display while prompting the user
        """
        raise NotImplementedError


class CmdLineIO(BaseIO):
    """A command line IO interface utilizing the standard streams
    """
    def __init__(self):
        super(CmdLineIO, self).__init__()
        self._out = sys.stdout

    def input_(self, prompt_str=''):
        return raw_input(prompt_str)

    def write(self, str_):
        return self._out.write(str_)

    def print_(self, *args):
        self.write(' '.join(map(str, args)))
        self.write('\n')

    def flush(self):
        self._out.flush()


class AsyncCmdLineIO(CmdLineIO, BaseAsyncIO):
    """Provide an asynchronous input function using the UNIX-specific `signal` package.
    """
    def __init__(self, timeout=1):
        super(AsyncCmdLineIO, self).__init__()
        self.timeout = timeout
        # register interrupt handler
        def cb_interrupt(signum, frame):
            """Raise a TimeoutError if SIGALRM is encountered
            """
            if signum == signal.SIGALRM:
                raise TimeoutError()
        signal.signal(signal.SIGALRM, cb_interrupt)

    def async_input(self, prompt_str):
        """
        WARNING: `prompt_str` will be re-displayed each time this function is called.
            To avoid printing the prompt multiple times, make sure subsequent
            calls are made with an empty ('') argument
        """
        signal.alarm(self.timeout)
        try:
            input_ = self.input_(prompt_str)
        except TimeoutError:
            return None
        else:
            # disable alarm
            signal.alarm(0)
            return input_
