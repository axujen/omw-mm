#!/usr/bin/env python2.7
import wx
from lib.gui import MainWindow

if __name__ == "__main__":
    app = wx.App(True)
    frame = MainWindow()
    app.MainLoop()
