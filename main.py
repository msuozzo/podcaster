#!/usr/bin/env python  #pylint: disable=missing-docstring
from podcaster.main import Podcaster

import os


os.environ.setdefault('VLC_PLUGIN_PATH', '/Applications/VLC.app/Contents/MacOS/plugins/')
Podcaster().run()
