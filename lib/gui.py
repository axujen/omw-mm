import wx
import core
from ObjectListView import ObjectListView, ColumnDefn


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

        # -- List
        self.list = ObjectListView(self, style=wx.LC_REPORT | wx.LC_HRULES, useAlternateBackColors=False)

        self.sizer = wx.BoxSizer()
        self.sizer.Add(self.list, 1, flag=wx.EXPAND | wx.GROW)
        self.SetSizerAndFit(self.sizer)

        # -- Right click menu
        self.rmenu = None
        self.list.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

    def OnContextMenu(self, event):
        pos = self.ScreenToClient(event.GetPosition())
        self.rmenu = wx.Menu()
        menu_items = self._context_menu_items()
        if menu_items:
            for item in menu_items:
                self.rmenu.AppendItem(item)
                self.Bind(wx.EVT_MENU, self.OnContextMenuItem, item)
        else:
            self.rmenu.Append(wx.ID_NO, "Unimplemented!")

        self.PopupMenu(self.rmenu, pos)
        self.rmenu.Destroy()

    def OnContextMenuItem(self, event):
        label = self.rmenu.FindItemById(event.GetId()).GetText().replace(" ", "_")
        callback = getattr(self, "OnContextMenu" + label, None)

        if callable(callback):
            callback(event)
        else:
            wx.MessageBox("OnContextMenu%s No Implemented!" % label)

    # Implement these methods in subclasses
    def _context_menu_items(self):
        """Create a tuple of wx.MenuItem for the context menu

        :returns: (tuple)
        """
        return ()


class ModsPanel(ListPanel):
    """Mods Tab"""
    def __init__(self, parent, mods):
        super(ModsPanel, self).__init__(parent)
        self._mods = mods

        self.list.SetColumns([
            ColumnDefn("Name", valueGetter="get_name"),
            ColumnDefn("Path", valueGetter="get_path")])

        self.list.SetObjects(self._mods)


class PluginsPanel(ListPanel):
    """Plugins Tab"""
    def __init__(self, parent, plugins):
        super(PluginsPanel, self).__init__(parent)
        self._plugins = plugins

        # -- Columns
        column_order = ColumnDefn("#", valueGetter="get_order", checkStateGetter="is_enabled", checkStateSetter=self.TogglePlugin, fixedWidth=50)
        column_name = ColumnDefn("Name", valueGetter="get_name")
        column_mod = ColumnDefn("Mod", valueGetter="get_mod", stringConverter=lambda x: x.get_name())
        self.list.InstallCheckStateColumn(column_order)
        self.list.SetColumns((column_order, column_name, column_mod))

        # -- Entries
        self.list.SetObjects(self._plugins)
        self.list.AutoSizeColumns()

    def Refresh(self):
        self.list.SetObjects(self._plugins)

    def EnablePlugin(self, plugin):
        index = self._plugins.index(plugin)
        self._plugins[index].enable()
        self.Refresh()

    def DisablePlugin(self, plugin):
        index = self._plugins.index(plugin)
        self._plugins[index].disable()
        self.Refresh()

    def TogglePlugin(self, plugin, state):
        index = self._plugins.index(plugin)
        if plugin.is_enabled():
            self._plugins[index].disable()
        else:
            self._plugins[index].enable()

        self.Refresh()

    # -- Context Menu
    def _context_menu_items(self):
        enable = wx.MenuItem(id=wx.ID_ANY, text="Enable", help="Enable Selected Plugins")
        disable = wx.MenuItem(id=wx.ID_ANY, text="Disable", help="Disable Selected Plugins")

        return (enable, disable)

    def OnContextMenuEnable(self, event):
        selection = self.list.GetSelectedObjects()
        if selection:
            for plugin in selection:
                if not plugin.is_enabled():
                    self.EnablePlugin(plugin)

    def OnContextMenuDisable(self, event):
        selection = self.list.GetSelectedObjects()
        if selection:
            for plugin in selection:
                if plugin.is_enabled():
                    self.DisablePlugin(plugin)
