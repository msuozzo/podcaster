import unittest
import os


if __name__ == "__main__":
    os.environ.setdefault('VLC_PLUGIN_PATH', '/Applications/VLC.app/Contents/MacOS/plugins/')
    suite = unittest.defaultTestLoader.discover("tests")
    unittest.TextTestRunner(verbosity=2).run(suite)
