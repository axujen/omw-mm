import wx
import core


class GUI(wx.App):
    def __init__(self, omw_cfg, redirect=False, filename=None):
        super(GUI, self).__init__(redirect, filename)
        self.frame = MainWindow(omw_cfg)
        self.omw_cfg = omw_cfg

    def Run(self):
        self.frame.Show()
        self.MainLoop()


class MainWindow(wx.Frame):
    """Main Window"""

    def __init__(self, omw_cfg):
        super(MainWindow, self).__init__(parent=None, title="OMW Mod Manager GUI")
        self.omw_cfg = omw_cfg

        # -- Menu and statusbar
        self.SetMenuBar(self._create_menubar())
        self.SetStatusBar(self._create_statusbar())

        # -- Tabs
        # self.panel = wx.Panel
        self.notebook = wx.Notebook(self)

        # Mods Tab
        self.mods_tab = ModsPanel(self.notebook, omw_cfg.get_mods())
        self.notebook.AddPage(self.mods_tab, "Mods")

        # Plugins Tab
        self.plugins_tab = PluginsPanel(self.notebook, core.get_plugins(omw_cfg))
        self.notebook.AddPage(self.plugins_tab, "Plugins")

    def _create_menubar(self):
        # -- File Menu
        filemenu = wx.Menu()

        f_install = filemenu.Append(wx.ID_OPEN, "&Install", "Install a mod")
        filemenu.AppendSeparator()
        f_about = filemenu.Append(wx.ID_ABOUT, "&About", "TODO")
        f_exit = filemenu.Append(wx.ID_EXIT, "&Quit", "Quit the program")

        self.Bind(wx.EVT_MENU, self.OnInstall, f_install)
        self.Bind(wx.EVT_MENU, self.OnAbout, f_about)
        self.Bind(wx.EVT_MENU, self.OnExit, f_exit)

        # -- Edit Menu
        editmenu = wx.Menu()

        e_settings = editmenu.Append(wx.ID_PREFERENCES, "&Settings", "Programm Settings")

        self.Bind(wx.EVT_MENU, self.OnSettings, e_settings)

        # -- Menu Bar
        menubar = wx.MenuBar()
        menubar.Append(filemenu, "&File")
        menubar.Append(editmenu, "&Edit")
        return menubar

    def _create_statusbar(self):
        statusbar = wx.StatusBar(self)
        return statusbar

    # TODO
    def OnSettings(self, event):
        pass

    def OnInstall(self, event):
        pass

    def OnAbout(self, event):
        dlg = wx.MessageDialog(self, "Aspiring Mod Manager for OpenMW!",
                               "About OMW-MM", wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def OnExit(self, event):
        self.Close(True)


# -- Tabs
class ListPanel(wx.Panel):
    """Generic class for list tabs (mods/plugins)"""
    def __init__(self, parent):
        super(ListPanel, self).__init__(parent)
        self.list = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_HRULES)
        self.sizer = wx.BoxSizer()
        self.sizer.Add(self.list, 1, flag=wx.EXPAND | wx.GROW)
        self.SetSizerAndFit(self.sizer)

    def PostInit(self):
        for col in range(self.list.GetColumnCount()):
            self.list.SetColumnWidth(col, -1)

    def AppendColumn(self, title):
        self.list.InsertColumn(self.list.GetColumnCount(), title, width=wx.LIST_AUTOSIZE)


class ModsPanel(ListPanel):
    """Mods Tab"""
    def __init__(self, parent, mods):
        super(ModsPanel, self).__init__(parent)
        self._mods = mods

        # -- Columns
        self.AppendColumn("#")
        self.AppendColumn("Name")
        self.AppendColumn("Path")

        # -- Entries
        for mod in self._mods:
            entry = (mod.get_order(), mod.get_name(), mod.get_path())
            self.list.Append(entry)

        self.PostInit()


class PluginsPanel(ListPanel):
    """Plugins Tab"""
    def __init__(self, parent, plugins):
        super(PluginsPanel, self).__init__(parent)
        self._plugins = plugins

        # -- Columns
        self.AppendColumn("#")
        self.AppendColumn("Name")
        self.AppendColumn("Mod")

        # -- Entries
        for plugin in self._plugins:
            if plugin.is_enabled():
                entry = (plugin.get_order(), plugin.get_name(), plugin.get_mod().get_name())
            else:
                entry = ("-", plugin.get_name(), plugin.get_mod().get_name())

            self.list.Append(entry)

        self.PostInit()
