#!/usr/bin/env python
from podcaster.operations import Controller

import os


class Podcaster(object):
    def __init__(self):
        self.controller = Controller('.podcaster.db')

    def run(self):
        self.controller.update_podcasts(lambda: None)
        current_menu = self.controller.all_podcasts
        while current_menu is not None:
            print
            current_menu = current_menu()

if __name__ == '__main__':
    os.environ.setdefault('VLC_PLUGIN_PATH', '/Applications/VLC.app/Contents/MacOS/plugins/')
    Podcaster().run()
