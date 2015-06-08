"""Utilities for testing
"""
from contextlib import contextmanager
from random import randint
import os


@contextmanager
def chdir(path):
    """On enter: Change the current directory to `path`
    On exit: Change the current directory to the original currdir

    path - the directory path to which the curdir should be changed
    """
    last_dir = os.path.abspath(os.curdir)
    os.chdir(path)
    yield
    os.chdir(last_dir)


def _remove_all(path):
    """Removes all files and directories beneath (but not including) `path`
    """
    for dirpath, dirnames, fnames in os.walk(path, topdown=False):
        for fname in fnames:
            os.remove(os.path.join(dirpath, fname))
        for dirname in dirnames:
            os.rmdir(os.path.join(dirpath, dirname))


class TempDir(object):
    """Context manager class intended to perform the following:
        - create a temporary directory
        - change to it
        -- yield
        - remove the temporary directory and its contents
        - return to the directory at the time of enter

    There are also methods for non-context-manager use of enter and exit functionality.

    expect_clean - if true, raise an exception if, on exit, the directory is
                    non-empty
    """
    TEMP_ROOT = os.path.abspath('/tmp')
    def __init__(self, expect_clean=False):
        self._enter_dir = None
        self._temp_dir = None
        self.expect_clean = expect_clean

    @staticmethod
    def _get_temp_dirname():
        """Return a possible random directory path under the system's temp directory.
        NOTE: No guarantee is made regarding the returned path's state on the
        system (may already exist)
        """
        rand_hex = hex(randint(0, 0xffffffff)).split('x')[1]
        rand_dir_name = '_' + rand_hex
        return os.path.join(TempDir.TEMP_ROOT, rand_dir_name)

    @staticmethod
    def _get_temp_dir():
        """Return a random directory path under the system's temp directory
        that is guaranteed to not exist.
        """
        exists = True
        while exists:
            rand_path = TempDir._get_temp_dirname()
            exists = os.path.exists(rand_path)
        return rand_path

    def __enter__(self):
        if self._temp_dir is not None or self._enter_dir is not None:
            raise Exception('Currently in a temporary directory (exit not called)')

        self._temp_dir = os.path.abspath(TempDir._get_temp_dir())
        os.mkdir(self._temp_dir)
        self._enter_dir = os.path.abspath(os.curdir)
        os.chdir(self._temp_dir)

    def enter(self):
        """Change to a temporary directory
        """
        self.__enter__()

    def __exit__(self, type_, value, traceback):
        if self._temp_dir is None or self._enter_dir is None:
            raise Exception('Not in a temporary directory (enter not called)')
        # Make damn sure we're not about delete anything non-temp
        elif os.path.commonprefix((TempDir.TEMP_ROOT, self._temp_dir)) != TempDir.TEMP_ROOT and \
                self._temp_dir != TempDir.TEMP_ROOT:
            raise Exception('Current directory "%s" not a temporary directory' % self._temp_dir)

        os.chdir(self._enter_dir)
        if os.listdir(self._temp_dir) and self.expect_clean:
            raise Exception('Temp dir at \'%s\' not empty: {%s}' %
                    (self._temp_dir, ', '.join(os.listdir(self._temp_dir))))
        _remove_all(self._temp_dir)
        os.rmdir(self._temp_dir)

        self._enter_dir = None
        self._temp_dir = None

    def exit(self):
        """Exit the temporary directory, delete it, and change the directory
        back to the one from which enter was called.
        """
        self.__exit__(None, None, None)

    @staticmethod
    def decorator(func, *args, **kwargs):
        """Function decorator that wraps a function in a `TempDir` instance.
        Accepts arguments to the `TempDir` constructor

        expect_clean - if true, raise an exception if, on return, the temp
                        directory is non-empty
        """
        def _with_temp_dir(*fargs, **fkwargs):
            """Closure calling `func` from within the context manager"""
            with TempDir(*args, **kwargs):
                return func(*fargs, **fkwargs)
        return _with_temp_dir
