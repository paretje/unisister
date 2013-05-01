# Unisister
# Copyright: (C) 2013 Online - Urbanus
# Website: http://www.Online-Urbanus.be
# Last modified: 27/04/2013 by Paretje

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import wx
import gettext
from gettext import gettext as _
import locale
import config

import threading
import time
import signal
import sys
import subprocess

import os

def error_dialog(message):
	dlg = wx.MessageDialog(None, message, _('Error'), wx.OK | wx.ICON_ERROR)
	dlg.ShowModal()
	dlg.Destroy()

def get_icon(name, large=False):
	# TODO: use at least os.path.join
	# Even better would be to use, at least on linux, a more general system
	# to get the right icon (so we can use theme-specific icons!)
	if large:
		return wx.Icon(config.ICON_LOCATION_LARGE + '/' + name + '.png',
			wx.BITMAP_TYPE_PNG)
	else:
		return wx.Icon(config.ICON_LOCATION + '/' + name + '.png',
			wx.BITMAP_TYPE_PNG)

class UnisisterPreferences(wx.Frame):
	def __init__(self, task_bar):
		wx.Frame.__init__(self, None, wx.ID_ANY, _("Unisister Preferences"))
		self.task_bar = task_bar
		panel = wx.Panel(self, wx.ID_ANY)
		
		# TODO: better names?
		# TODO: Password?
		# TODO: Add hover texts where needed
		form_box = wx.BoxSizer(wx.VERTICAL)
		form = wx.FlexGridSizer(cols=2, vgap=5, hgap=50)
		form_save = wx.BoxSizer(wx.HORIZONTAL)
		form.AddGrowableCol(1, 1)
		
		self.server_address = wx.TextCtrl(panel, value=self.task_bar.config.Read('server_address'))
		form.Add(wx.StaticText(panel, label=_("Server address:")), flag=wx.ALIGN_CENTER_VERTICAL)
		form.Add(self.server_address, flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
		
		self.server_username = wx.TextCtrl(panel, value=self.task_bar.config.Read('server_username'))
		form.Add(wx.StaticText(panel, label=_("Server username:")), flag=wx.ALIGN_CENTER_VERTICAL)
		form.Add(self.server_username, flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
		
		self.server_location = wx.TextCtrl(panel, value=self.task_bar.config.Read('server_location'))
		form.Add(wx.StaticText(panel, label=_("Location on server:")), flag=wx.ALIGN_CENTER_VERTICAL)
		form.Add(self.server_location, flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
		
		self.local_location = wx.FilePickerCtrl(panel, path=self.task_bar.config.Read('local_location'))
		form.Add(wx.StaticText(panel, label=_("Local folder:")), flag=wx.ALIGN_CENTER_VERTICAL)
		form.Add(self.local_location, flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
		
		form.Add(wx.StaticText(panel, label=_("Backend:")), flag=wx.ALIGN_CENTER_VERTICAL)
		form.Add(wx.StaticText(panel, label=_("Future option")), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
		
		self.backend_location_server = wx.TextCtrl(panel, value=self.task_bar.config.Read('backend_location_server'))
		form.Add(wx.StaticText(panel, label=_("Backend location on server:")), flag=wx.ALIGN_CENTER_VERTICAL)
		form.Add(self.backend_location_server, flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
		
		self.backend_location_local = wx.FilePickerCtrl(panel, path=self.task_bar.config.Read('backend_location_local'))
		form.Add(wx.StaticText(panel, label=_("Backend location on local machine:")), flag=wx.ALIGN_CENTER_VERTICAL)
		form.Add(self.backend_location_local, flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
		
		# TODO: Add space between the two buttons
		form_save.Add(wx.Button(panel, wx.ID_CANCEL, _("Cancel")))
		form_save.Add(wx.Button(panel, wx.ID_OK, _("OK")))
		
		form_box.Add(form, 0, flag=wx.EXPAND|wx.ALL, border=10)
		form_box.Add(wx.StaticText(panel), 1)
		form_box.Add(form_save, flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, border=10)
		panel.SetSizerAndFit(form_box)
		
		# Default width is to small, so only use height
		self.SetSize((500, self.GetBestSizeTuple()[1]))
		
		self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)
		self.Bind(wx.EVT_BUTTON, self.OnOK, id=wx.ID_OK)
	
	def OnCancel(self, evt):
		self.Close(True)
	
	def OnOK(self, evt):
		self.task_bar.config.Write('server_address', self.server_address.GetValue())
		self.task_bar.config.Write('server_username', self.server_username.GetValue())
		self.task_bar.config.Write('server_location', self.server_location.GetValue())
		self.task_bar.config.Write('local_location', self.local_location.GetPath())
		#self.task_bar.config.Write('backend', self.backend.GetValue())
		self.task_bar.config.Write('backend_location_server', self.backend_location_server.GetValue())
		self.task_bar.config.Write('backend_location_local', self.backend_location_local.GetPath())
		self.task_bar.config.Flush()
		self.Close(True)

class UnisisterThread(threading.Thread):
	_bussy = False
	
	def __init__(self, task_bar):
		threading.Thread.__init__(self)
		# TODO
		# Daemon threads are abruptly stopped at shutdown. Their
		# resources (such as open files, database transactions, etc.)
		# may not be released properly. If you want your threads to stop
		# gracefully, make them non-daemonic and use a suitable
		# signalling mechanism such as an Event.
		self.deamon = False
		self.task_bar = task_bar
	
	def run(self):
		UnisisterThread._bussy = True
		# TODO: MVC!! + is absolute path avoidable?
		self.task_bar.SetIcon(get_icon(config.ICON_BUSSY), "Unisister")
		
		# In Python 3.3, subprocess.DEVNULL has been added, so use this
		# is available
		try: 
			devnull = subprocess.DEVNULL
		except AttributeError: 
			devnull = open(os.devnull, 'w')
		
		# Start backend
		if self.task_bar.config.Read('backend') == 'csync':
			wx.CallAfter(error_dialog, _("Using csync as a backend is not supported by the current version of Unisister yet."))
		else:
			arguments = []
			
			# Test if the user has set a username
			if self.task_bar.config.Read('server_username') != "":
				server_address = self.task_bar.config.Read('server_username') + '@' + self.task_bar.config.Read('server_address')
			else:
				server_address = self.task_bar.config.Read('server_address')
			
			# Test if the user has set a specific server unison executable
			if self.task_bar.config.Read('backend_location_server') != "":
				arguments += ['-servercmd', self.task_bar.config.Read('backend_location_server')]
			
			# Test if the user has set a specific local unison executable
			if self.task_bar.config.Read('backend_location_local') != "":
				unison_local = self.task_bar.config.Read('backend_location_local')
			else:
				unison_local = 'unison'
			
			# Start the unison process
			server = 'ssh://' + server_address + '/' + self.task_bar.config.Read('server_location')
			local = self.task_bar.config.Read('local_location')
			subprocess.call([unison_local, server, local, '-batch', '-prefer', server] + arguments)
		
		self.task_bar.SetIcon(get_icon(config.ICON_IDLE), "Unisister")
		UnisisterThread._bussy = False
	
	# Not very Pythonic, but a property can't be static, and I don't want
	# to use the variable directly, as I think it's quite likely this
	# would change in the future.
	# TODO: is this story true???
	@classmethod
	def is_bussy(cls):
		return cls._bussy

class UnisisterTaskBar(wx.TaskBarIcon):
	ID_SYNCH = wx.NewId()
 
	def __init__(self):
		wx.TaskBarIcon.__init__(self)
 		
 		# Load user-preferences
 		self.config = wx.Config('unisister')
 		
		# Set the icon of Unisister
		self.SetIcon(get_icon(config.ICON_IDLE), "Unisister")
 		
 		# Create Timer-object, and keep it, as it's necessarry to let in function properly (GBC?)
 		self.timer = wx.Timer(self, UnisisterTaskBar.ID_SYNCH)
 		self.Synchronisation(None)
 		
		# Bind the events
		self.Bind(wx.EVT_TASKBAR_LEFT_DOWN, self.OnTaskBarLeftClick)
		
		# TODO: Handle END_SESSION events!!
		self.Bind(wx.EVT_CLOSE, self.StopUnisister)
		self.Bind(wx.EVT_QUERY_END_SESSION, self.StopUnisister)
		self.Bind(wx.EVT_END_SESSION, self.StopUnisister)
		
		self.Bind(wx.EVT_MENU, self.StopUnisister, id=wx.ID_EXIT)
		self.Bind(wx.EVT_MENU, self.Synchronisation, id=UnisisterTaskBar.ID_SYNCH)
		self.Bind(wx.EVT_MENU, self.ShowPreferences, id=wx.ID_PROPERTIES)
		self.Bind(wx.EVT_MENU, self.AboutUnisister, id=wx.ID_ABOUT)
		
		self.Bind(wx.EVT_TIMER, self.Synchronisation, id=UnisisterTaskBar.ID_SYNCH)
		
		# Event generator in order to synchronize every n seconds
		self.timer.Start(120*1000)
 
	def CreatePopupMenu(self, evt=None):
		menu = wx.Menu()
		menu.Append(self.ID_SYNCH, _("Force Synchronisation"))
		menu.Append(wx.ID_PROPERTIES, _("Preferences"))
		menu.Append(wx.ID_ABOUT, _("About"))
		menu.AppendSeparator()
		menu.Append(wx.ID_EXIT,   _("Quit Unisister"))
		return menu

	def OnTaskBarClose(self, evt):
		self.RemoveIcon()
		self.Destroy()
 
	def OnTaskBarLeftClick(self, evt):
		menu = self.CreatePopupMenu()
		self.PopupMenu(menu)
		menu.Destroy()
	
	def StopUnisister(self, evt):
		# TODO: Is OnTaskBarClose necesarry/usefull?
		self.OnTaskBarClose(evt)
	
	def Synchronisation(self, evt):
		if not UnisisterThread.is_bussy():
			UnisisterThread(self).start()
		else:
			print _("We are already bussy synchronising!")
	
	def ShowPreferences(self, evt):
		UnisisterPreferences(self).Show()
		
	
	def AboutUnisister(self, evt):
		info = wx.AboutDialogInfo()
		info.Name = "Unisister"
		info.Version = config.VERSION
		info.Copyright = "(C) 2013 Online - Urbanus"
		info.Icon = get_icon(config.ICON_IDLE, large=True)
		info.Description = "The sister of Unison.\n" + _("Unisister is a tool to automatically synchronize your directory with a central directory, using Unison.")
		info.WebSite = ("http://www.Online-Urbanus.be", "Online - Urbanus")
		info.Developers = ["Paretje"]
		try:
			info.License = open(config.LICENSE_LOCATION).read()
		except Exception:
			info.License = _("Released under the terms of the GNU General Public License Version 3 \nSee http://www.gnu.org/licenses/gpl.html for more details.")
		wx.AboutBox(info)

def _set_localisation():
	# Code based on the code in system-config-printer v1.3.7
	try:
		locale.setlocale (locale.LC_ALL, "")
	except locale.Error:
		os.environ['LC_ALL'] = 'C'
		locale.setlocale (locale.LC_ALL, "")
	
	gettext.textdomain('unisister')
	gettext.bindtextdomain('unisister', config.LOCALEDIR)

if __name__ == "__main__":
	app = wx.App(False)
	_set_localisation()
	UnisisterTaskBar()
	app.MainLoop()
