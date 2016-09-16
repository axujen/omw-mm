# -*- coding: UTF-8 -*-
import wx
import wx.lib.mixins.listctrl as listmix
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
        self.mods_tab = ModsPanel(self.notebook, omw_cfg.mods)
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
class ListCtrl(ObjectListView, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, style, useAlternateBackColors, rowFormatter):
        ObjectListView.__init__(self, parent, style=style,
                                useAlternateBackColors=useAlternateBackColors,
                                rowFormatter=rowFormatter)
        listmix.ListCtrlAutoWidthMixin.__init__(self)

    # Fix int to string comparison, TODO: Submit bug report
    def _HandleTypingEvent(self, evt):
        import string
        import time
        if self.GetItemCount() == 0 or self.GetColumnCount() == 0:
            return False

        if evt.GetModifiers() != 0 and evt.GetModifiers() != wx.MOD_SHIFT:
            return False

        if evt.GetKeyCode() > wx.WXK_START:
            return False

        if evt.GetKeyCode() in (wx.WXK_BACK, wx.WXK_DELETE):
            self.searchPrefix = u""
            return True

        # On which column are we going to compare values? If we should search on the
        # sorted column, and there is a sorted column and it is searchable, we use that
        # one, otherwise we fallback to the primary column
        if self.typingSearchesSortColumn and self.GetSortColumn(
        ) and self.GetSortColumn().isSearchable:
            searchColumn = self.GetSortColumn()
        else:
            searchColumn = self.GetPrimaryColumn()

        # On Linux, GetUnicodeKey() always returns 0 -- on my 2.8.7.1
        # (gtk2-unicode)
        if isinstance(evt.GetUnicodeKey(), int):
            uniChar = chr(evt.GetKeyCode())
        else:
            uniChar = evt.GetUnicodeKey()
        if uniChar not in string.printable:
            return False

        # On Linux, evt.GetTimestamp() isn't reliable so use time.time()
        # instead
        timeNow = time.time()
        if (timeNow - self.whenLastTypingEvent) > self.SEARCH_KEYSTROKE_DELAY:
            self.searchPrefix = uniChar
        else:
            self.searchPrefix += uniChar
        self.whenLastTypingEvent = timeNow

        # self.__rows = 0
        self._FindByTyping(searchColumn, self.searchPrefix)
        # print "Considered %d rows in %2f secs" % (self.__rows, time.time() -
        # timeNow)

        return True


class ListPanel(wx.Panel):
    """Generic class for list tabs (mods/plugins)"""
    def __init__(self, parent):
        super(ListPanel, self).__init__(parent)

        # -- List
        self.list = ListCtrl(self, style=wx.LC_REPORT,
                             useAlternateBackColors=False,
                             rowFormatter=self._row_formatter)

        self.sizer = wx.BoxSizer()
        self.sizer.Add(self.list, 1, flag=wx.EXPAND | wx.GROW)
        self.SetSizerAndFit(self.sizer)

        # -- Right click menu
        self.rmenu = None
        self.list.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

        # Global color definitions
        self.color_enabled = "#cce6ff"  # Blue
        self.color_disabled = "#ffffe6"  # Light Yellow
        self.color_warning = "#ff8533"  # Orange

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

    def _row_formatter(self, row, item):
        pass


class ModsPanel(ListPanel):
    """Mods Tab"""
    def __init__(self, parent, mods):
        super(ModsPanel, self).__init__(parent)
        self._mods = mods

        self.list.SetColumns([
            ColumnDefn("#", valueGetter="order", fixedWidth=28),
            ColumnDefn("Name", valueGetter="name"),
            ColumnDefn("Path", valueGetter="path")])

        self.list.SetObjects(self._mods)

    def _context_menu_items(self):
        m_uninstall = wx.MenuItem(id=wx.ID_DELETE, text="Uninstall", help="Uninstall selected mods.")

        return (m_uninstall,)


class PluginsPanel(ListPanel):
    """Plugins Tab"""
    def __init__(self, parent, plugins):
        super(PluginsPanel, self).__init__(parent)
        self._plugins = plugins

        # -- Columns
        column_state = ColumnDefn("✓", checkStateGetter="is_enabled", checkStateSetter=self.TogglePlugin, fixedWidth=24)
        column_order = ColumnDefn("#", valueGetter="order")
        column_name = ColumnDefn("Name", valueGetter="name")
        column_mod = ColumnDefn("Mod", valueGetter="mod", stringConverter=lambda x: x.name if x else "")
        self.list.InstallCheckStateColumn(column_state)
        self.list.SetColumns((column_state, column_order, column_name, column_mod))

        # -- Entries
        self.list.SetObjects(self._plugins)
        self.list.AutoSizeColumns()
        # self.Refresh()

    def Refresh(self):
        # self.list.RefreshObjects(self._plugins)
        # self.list.RefreshObjects()
        # self.list.SetValue(self._plugins)
        # self.list.RepopulateList()
        # self.list.AutoSizeColumns()
        # self.list.SetObjects(self._plugins)
        # self.list.AutoSizeColumns()
        # self.list.SetSortColumn(0, True)
        pass

    def PluginEnable(self, plugin):
        index = self._plugins.index(plugin)
        self._plugins[index].enable()

    def PluginDisable(self, plugin):
        index = self._plugins.index(plugin)
        self._plugins[index].disable()

    def TogglePlugin(self, plugin, state):
        if plugin.is_enabled:
            self.PluginDisable(plugin)
        else:
            self.PluginEnable(plugin)

    # -- Context Menu
    def _context_menu_items(self):
        enable = wx.MenuItem(id=wx.ID_YES, text="Enable", help="Enable selected plugins.")
        disable = wx.MenuItem(id=wx.ID_NO, text="Disable", help="Disable selected plugins.")

        return (enable, disable)

    def OnContextMenuEnable(self, event):
        selection = self.list.GetSelectedObjects()
        if selection:
            for plugin in selection:
                if not plugin.is_enabled:
                    self.PluginEnable(plugin)

    def OnContextMenuDisable(self, event):
        selection = self.list.GetSelectedObjects()
        if selection:
            for plugin in selection:
                if plugin.is_enabled:
                    self.PluginDisable(plugin)

    # -- Formatting
    def _row_formatter(self, row, item):
        if item.is_enabled:
            row.SetBackgroundColour(self.color_enabled)
        else:
            row.SetBackgroundColour(self.color_disabled)

        if item.is_orphan:
            row.SetBackgroundColour(self.color_warning)
