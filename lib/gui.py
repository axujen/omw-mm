import wx


class MainWindow(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, parent=None, title="OMW Mod Manager GUI")
        self.SetMenuBar(self.create_menubar())
        self.SetStatusBar(self.create_statusbar())
        self.Show()

    def create_menubar(self):
        # -- File Menu
        filemenu = wx.Menu()

        f_install = filemenu.Append(wx.ID_OPEN, "&Install", "Install a mod")
        filemenu.AppendSeparator()
        f_about = filemenu.Append(wx.ID_ABOUT, "&About", "TODO")
        f_exit = filemenu.Append(wx.ID_EXIT, "&Quit", "Quit the program")

        self.Bind(wx.EVT_MENU, self.on_install, f_install)
        self.Bind(wx.EVT_MENU, self.on_about, f_about)
        self.Bind(wx.EVT_MENU, self.on_exit, f_exit)

        # -- Edit Menu
        editmenu = wx.Menu()

        e_settings = editmenu.Append(wx.ID_PREFERENCES, "&Settings", "Programm Settings")

        self.Bind(wx.EVT_MENU, self.on_settings, e_settings)

        # -- Menu Bar
        menubar = wx.MenuBar()
        menubar.Append(filemenu, "&File")
        menubar.Append(editmenu, "&Edit")
        return menubar

    # TODO
    def on_settings(self, event):
        pass

    def on_install(self, event):
        pass

    def on_about(self, event):
        dlg = wx.MessageDialog(self, "Aspiring Mod Manager for OpenMW!",
                               "About OMW-MM", wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def on_exit(self, event):
        self.Close(True)

    def create_statusbar(self):
        statusbar = wx.StatusBar(self)
        return statusbar
