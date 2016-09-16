#!/usr/bin/env python2.7
from lib.gui import GUI
from lib.omw import ConfigFile
from lib.config import config

if __name__ == "__main__":
    omw_cfg = ConfigFile(config.get("General", "openmw_cfg"))
    gui = GUI(omw_cfg)
    gui.Run()
