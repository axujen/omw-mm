# -*- coding: UTF-8 -*-
import wx
import sys
import pickle

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
        f_save = filemenu.Append(wx.ID_SAVE, "&Save", "Save changes")
        filemenu.AppendSeparator()
        f_about = filemenu.Append(wx.ID_ABOUT, "&About", "TODO")
        f_exit = filemenu.Append(wx.ID_EXIT, "&Quit", "Quit the program")

        self.Bind(wx.EVT_MENU, self.OnInstall, f_install)
        self.Bind(wx.EVT_MENU, self.OnSave, f_save)
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

    def _save(self):
        # Update plugins load order
        plugins = []
        for plugin in self.plugins_tab.items:
            if plugin.is_enabled:
                plugins.append(plugin)
        self.omw_cfg.plugins = plugins

        self.omw_cfg.write()

    # TODO
    def OnSave(self, event):
        self._save()

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
    def __init__(self, parent, items):
        super(ListPanel, self).__init__(parent)

        # -- List
        self.items = items
        self.list = ListCtrl(self, style=wx.LC_REPORT,
                             useAlternateBackColors=False,
                             rowFormatter=self._row_formatter)

        self.sizer = wx.BoxSizer()
        self.sizer.Add(self.list, 1, flag=wx.EXPAND | wx.GROW)
        self.SetSizerAndFit(self.sizer)

        # -- Order of items
        self._column_order = ColumnDefn("#", valueGetter=self.GetItemOrder,
                                        stringConverter=lambda x: str(x) if x != float("inf") else "")
        # -- Right click menu
        self.rmenu = None
        self.list.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

        # Global color definitions
        self.color_enabled = "#cce6ff"  # Blue
        self.color_disabled = "#ffffe6"  # Light Yellow
        self.color_warning = "#ff8533"  # Orange

        # Min width for space filling columns
        self._min_width = 250

        # Drag and Drop
        self._drop_target = SelectionDropTarget(self.list, self.OnDrop)
        self.list.SetDropTarget(self._drop_target)
        self.list.Bind(wx.EVT_LIST_BEGIN_DRAG, self.OnDrag)

    def GetItemOrder(self, item):
        return self.items.index(item) + 1

    # -- Drag and Drop
    def OnDrag(self, event):
        # Only drag and drop when sorting by load order
        sort_column = self.list.GetSortColumn()
        if not sort_column == self._column_order and self.list.sortAscending:
            return

        selection = self._get_drag_selection()
        if not selection:
            return
        indexes = tuple(self.items.index(i) for i in selection)
        data = wx.CustomDataObject("ListSelection%d" % self.list.GetId())
        data.SetData(pickle.dumps(indexes))

        dropSource = wx.DropSource(self.list)
        dropSource.SetData(data)
        dropSource.DoDragDrop(True)

    def OnDrop(self, index, selection):
        if selection:
            # Keep the selection in its original order
            items = sorted([self.list[i] for i in selection],
                           key=lambda i: self.items.index(i))

            # Compensensate for python list shifting when inserting to the right
            if self.items.index(items[0]) < index:
                index -= len(items)

            # Insert the drop selection
            self.items = [i for i in self.items if i not in items]
            self.items[index:index] = items

            # Refresh view
            self.list.SetSortColumn(self._column_order, resortNow=True)
            self.list.RefreshObjects(self.items)

            # Preserve selection
            self.list.SelectObjects(items)

    # -- Context Menu
    def OnContextMenu(self, event):
        pos = self.ScreenToClient(event.GetPosition())
        self.rmenu = wx.Menu()
        menu_items = self._context_menu_items()

        if menu_items:
            for item in menu_items:
                menu_item = self.rmenu.AppendItem(item)
                self._bind_menu_item(menu_item)
        else:
            self.rmenu.Append(wx.ID_NO, "Unimplemented!")

        self.PopupMenu(self.rmenu, pos)
        self.rmenu.Destroy()

        # Refresh items after an event
        self.list.RefreshObjects(self.items)

    def _bind_menu_item(self, item):
        label = item.GetItemLabel()
        handler = getattr(self, "OnContextMenu" + label, None)

        if callable(handler):
            self.Bind(wx.EVT_MENU, handler, item)
        else:
            wx.MessageBox("OnContextMenu%s No Implemented!" % label)

    # -- Subclass Overload
    # Implement these methods in subclasses
    def _context_menu_items(self):
        """Create a tuple of wx.MenuItem for the context menu

        :returns: (tuple)
        """
        return ()

    # Overload this method to filter the selection (disabled plugins)
    def _get_drag_selection(self):
        return self.list.GetSelectedObjects()

    def _row_formatter(self, row, item):
        pass


class ModsPanel(ListPanel):
    """Mods Tab"""
    def __init__(self, parent, items):
        ListPanel.__init__(self, parent, items)
        # -- Columns
        column_name = ColumnDefn("Name", valueGetter="name")
        column_path = ColumnDefn("Path", valueGetter="path", isSpaceFilling=True,
                                 minimumWidth=self._min_width)

        self.list.SetColumns((column_name, column_path))
        self.list.column_primary = column_name

        # -- Entries
        self.list.SetObjects(items)

    def _context_menu_items(self):
        m_uninstall = wx.MenuItem(id=wx.ID_DELETE, text="Uninstall", help="Uninstall selected mods.")

        return (m_uninstall,)


class PluginsPanel(ListPanel):
    """Plugins Tab"""
    def __init__(self, parent, items):
        ListPanel.__init__(self, parent, items)
        # -- Columns
        self._column_state = ColumnDefn("✓", isSearchable=False,
                                  checkStateGetter="is_enabled",
                                  checkStateSetter=self.TogglePlugin)
        column_name = ColumnDefn("Name", valueGetter="name")
        column_mod = ColumnDefn("Mod", valueGetter="mod", isSpaceFilling=True,
                                minimumWidth=self._min_width,
                                stringConverter=lambda x: x.name if x else "")

        self.list.InstallCheckStateColumn(self._column_state)
        self.list.SetColumns((self._column_state, self._column_order, column_name, column_mod))
        self.list.column_primary = column_name

        # -- Entries
        self.list.SetObjects(items)
        self.list.AutoSizeColumns()

    # Disabled Plugins have no load order
    def GetItemOrder(self, plugin):
        if plugin.is_enabled:
            return self.items.index(plugin) + 1
        else:
            return float('inf')

    def PluginEnable(self, plugin):
        index = self.items.index(plugin)
        self.items[index].enable()

    def PluginDisable(self, plugin):
        index = self.items.index(plugin)
        self.items[index].disable()

    def TogglePlugin(self, plugin, state):
        if plugin.is_enabled:
            self.PluginDisable(plugin)
        else:
            self.PluginEnable(plugin)

    def _get_drag_selection(self):
        selection = [p for p in self.list.GetSelectedObjects() if p.is_enabled]
        return selection

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


# -- Controls
class ListDropScrollerMixin(object):
    """Automatic scrolling for ListCtrls for use when using drag and drop.

    This mixin is used to automatically scroll a list control when
    approaching the top or bottom edge of a list.  Currently, this
    only works for lists in report mode.

    Add this as a mixin in your list, and then call processListScroll
    in your DropTarget's OnDragOver method.  When the drop ends, call
    finishListScroll to clean up the resources (i.e. the wx.Timer)
    that the dropscroller uses and make sure that the insertion
    indicator is erased.

    The parameter interval is the delay time in milliseconds between
    list scroll steps.

    If indicator_width is negative, then the indicator will be the
    width of the list.  If positive, the width will be that number of
    pixels, and zero means to display no indicator.
    """
    def __init__(self, interval=200, width=-1):
        """Don't forget to call this mixin's init method in your List.

        Interval is in milliseconds.
        """
        self._auto_scroll_timer = None
        self._auto_scroll_interval = interval
        self._auto_scroll = 0
        self._auto_scroll_save_y = -1
        self._auto_scroll_save_width = width
        self.Bind(wx.EVT_TIMER, self.OnAutoScrollTimer)

    def _startAutoScrollTimer(self, direction=0):
        """Set the direction of the next scroll, and start the
        interval timer if it's not already running.
        """
        if self._auto_scroll_timer is None:
            self._auto_scroll_timer = wx.Timer(self, wx.TIMER_ONE_SHOT)
            self._auto_scroll_timer.Start(self._auto_scroll_interval)
        self._auto_scroll = direction

    def _stopAutoScrollTimer(self):
        """Clean up the timer resources.
        """
        self._auto_scroll_timer = None
        self._auto_scroll = 0

    def _getAutoScrollDirection(self, index):
        """Determine the scroll step direction that the list should
        move, based on the index reported by HitTest.
        """
        first_displayed = self.GetTopItem()

        if first_displayed == index:
            # If the mouse is over the first index...
            if index > 0:
                # scroll the list up unless...
                return -1
            else:
                # we're already at the top.
                return 0
        elif index >= first_displayed + self.GetCountPerPage() - 1:
            # If the mouse is over the last visible item, but we're
            # not at the last physical item, scroll down.
            return 1
        # we're somewhere in the middle of the list.  Don't scroll
        return 0

    def getDropIndex(self, x, y, index=None, flags=None):
        """Find the index to insert the new item, which could be
        before or after the index passed in.
        """
        if index is None:
            index, flags = self.HitTest((x, y))

        if index == wx.NOT_FOUND:  # not clicked on an item
            # Empty list or below last item
            if (flags &
               (wx.LIST_HITTEST_NOWHERE | wx.LIST_HITTEST_ABOVE | wx.LIST_HITTEST_BELOW)):
                index = sys.maxint  # append to end of list
            elif (self.GetItemCount() > 0):
                if y <= self.GetItemRect(0).y:  # clicked just above first item
                    index = 0  # append to top of list
                else:
                    index = self.GetItemCount() + 1  # append to end of list
        else:  # clicked on an item
            # Get bounding rectangle for the item the user is dropping over.
            rect = self.GetItemRect(index)
            # NOTE: On all platforms, the y coordinate used by HitTest
            # is relative to the scrolled window.  There are platform
            # differences, however, because on GTK the top of the
            # vertical scrollbar stops below the header, while on MSW
            # the top of the vertical scrollbar is equal to the top of
            # the header.  The result is the y used in HitTest and the
            # y returned by GetItemRect are offset by a certain amount
            # on GTK.  The HitTest's y=0 in GTK corresponds to the top
            # of the first item, while y=0 on MSW is in the header.

            # From Robin Dunn: use GetMainWindow on the list to find
            # the actual window on which to draw
            if self != self.GetMainWindow():
                y += self.GetMainWindow().GetPositionTuple()[1]

            # If the user is dropping into the lower half of the rect,
            # we want to insert _after_ this item.
            if y >= (rect.y + rect.height / 2):
                index = index + 1

        return index

    def processListScroll(self, x, y):
        """Main handler: call this with the x and y coordinates of the
        mouse cursor as determined from the OnDragOver callback.

        This method will determine which direction the list should be
        scrolled, and start the interval timer if necessary.
        """
        index, flags = self.HitTest((x, y))

        direction = self._getAutoScrollDirection(index)
        if direction == 0:
            self._stopAutoScrollTimer()
        else:
            self._startAutoScrollTimer(direction)

        drop_index = self.getDropIndex(x, y, index=index, flags=flags)
        count = self.GetItemCount()
        if drop_index >= count:
            rect = self.GetItemRect(count - 1)
            y = rect.y + rect.height + 1
        else:
            rect = self.GetItemRect(drop_index)
            y = rect.y

        # From Robin Dunn: on GTK & MAC the list is implemented as
        # a subwindow, so have to use GetMainWindow on the list to
        # find the actual window on which to draw
        if self != self.GetMainWindow():
            y -= self.GetMainWindow().GetPositionTuple()[1]

        if self._auto_scroll_save_y == -1 or self._auto_scroll_save_y != y:
            if self._auto_scroll_save_width < 0:
                self._auto_scroll_save_width = rect.width
            dc = self._getIndicatorDC()
            self._eraseIndicator(dc)
            dc.DrawLine(0, y, self._auto_scroll_save_width, y)
            self._auto_scroll_save_y = y

    def finishListScroll(self):
        """Clean up timer resource and erase indicator.
        """
        self._stopAutoScrollTimer()
        self._eraseIndicator()

    def OnAutoScrollTimer(self, evt):
        """Timer event handler to scroll the list in the requested
        direction.
        """
        if self._auto_scroll == 0:
            # clean up timer resource
            self._auto_scroll_timer = None
        else:
            dc = self._getIndicatorDC()
            self._eraseIndicator(dc)
            if self._auto_scroll < 0:
                self.EnsureVisible(self.GetTopItem() + self._auto_scroll)
                self._auto_scroll_timer.Start()
            else:
                self.EnsureVisible(self.GetTopItem() + self.GetCountPerPage())
                self._auto_scroll_timer.Start()
        evt.Skip()

    def _getIndicatorDC(self):
        dc = wx.ClientDC(self.GetMainWindow())
        dc.SetPen(wx.Pen(wx.WHITE, 3))
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.SetLogicalFunction(wx.XOR)
        return dc

    def _eraseIndicator(self, dc=None):
        if dc is None:
            dc = self._getIndicatorDC()
        if self._auto_scroll_save_y >= 0:
            # erase the old line
            dc.DrawLine(0, self._auto_scroll_save_y,
                        self._auto_scroll_save_width, self._auto_scroll_save_y)
        self._auto_scroll_save_y = -1


class ListCtrl(ObjectListView, ListDropScrollerMixin):
    def __init__(self, *args, **kwargs):
        ObjectListView.__init__(self, *args, **kwargs)
        ListDropScrollerMixin.__init__(self, interval=200)
        self.SEARCH_KEYSTROKE_DELAY = 0
        self._column_primay = None

    @property
    def column_primary(self):
        return self._column_primary

    @column_primary.setter
    def column_primary(self, column):
        self._column_primary = column

    # Allow setting the primary column in self._column_primary
    def GetPrimaryColumnIndex(self):
        if self._column_primary:
            return self.columns.index(self._column_primary)
        else:
            return super(ListCtrl, self).GetPrimaryColumnIndex()

    # --- Bugfixes and tweaks for ObjectListView
    # Fix int to string comparison bug in ObjectListView, TODO: Submit bug report
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

    # Tweak checkbox location in ObjectListView
    def _InitializeCheckBoxImages(self):
        """
        Initialize some checkbox images for use by this control.
        """
        def _makeBitmap(state, size):
            if 'phoenix' in wx.PlatformInfo:
                bitmap = wx.Bitmap(size, size)
            else:
                bitmap = wx.EmptyBitmap(size, size)
            dc = wx.MemoryDC(bitmap)
            dc.Clear()

            # On Linux, the Renderer draws the checkbox too low
            if wx.Platform == "__WXGTK__":
                xOrigin = yOrigin = -2
            else:
                xOrigin = yOrigin = 0
            wx.RendererNative.Get().DrawCheckBox(
                self, dc, (xOrigin, yOrigin, size, size),
                state)
            dc.SelectObject(wx.NullBitmap)
            return bitmap

        def _makeBitmaps(name, state):
            self.AddNamedImages(
                name, _makeBitmap(
                    state, 16), _makeBitmap(
                    state, 32))

        # If there isn't a small image list, make one
        if self.smallImageList is None:
            self.SetImageLists()

        _makeBitmaps(ObjectListView.NAME_CHECKED_IMAGE, wx.CONTROL_CHECKED)
        _makeBitmaps(ObjectListView.NAME_UNCHECKED_IMAGE, wx.CONTROL_CURRENT)
        _makeBitmaps(
            ObjectListView.NAME_UNDETERMINED_IMAGE,
            wx.CONTROL_UNDETERMINED)


# -- Drag and Drop
class SelectionDropTarget(wx.PyDropTarget):
    def __init__(self, listctrl, callback):
        wx.PyDropTarget.__init__(self)

        self._callback = callback
        self._listctrl = listctrl

        self._data = wx.CustomDataObject("ListSelection%d" % listctrl.GetId())
        self.SetDataObject(self._data)

    def OnData(self, x, y, d):
        self.scroll_finish()
        if self.GetData():
            selection = pickle.loads(self._data.GetData())
            index = self._listctrl.getDropIndex(x, y)
            self._callback(index, selection)

        # What is d and what does it do? Who knows ask one of the wxpython devs
        return d

    # -- Auto scrolling
    def scroll_finish(self):
        self._listctrl.finishListScroll()

    def OnLeave(self):
        self.scroll_finish()

    def OnDrop(self, x, y):
        self.scroll_finish()
        return True

    def OnDragOver(self, x, y, d):
        self._listctrl.processListScroll(x, y)
        return d
