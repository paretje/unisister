# Unisister
# Copyright: (C) 2013 Online - Urbanus
# Website: http://www.Online-Urbanus.be
# Last modified: 21/04/2013 by Paretje

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
import config as cfg

import threading
import time
import signal
import sys
import subprocess

import os

class UnisisterThread(threading.Thread):
	__bussy = False
	
	def __init__(self, config):
		threading.Thread.__init__(self)
		# TODO
		# Daemon threads are abruptly stopped at shutdown. Their resources
		# (such as open files, database transactions, etc.) may not be
		# released properly. If you want your threads to stop gracefully,
		# make them non-daemonic and use a suitable signalling mechanism
		# such as an Event.
		self.deamon = False
		self._config = config
	
	def run(self):
		UnisisterThread.__bussy = True
		
		# In Python 3.3, subprocess.DEVNULL has been added, so use this is available
		try: 
			devnull = subprocess.DEVNULL
		except AttributeError: 
			devnull = open(os.devnull, 'w')
			
		subprocess.call(["unison", "server", "local", "-batch", "-prefer", "server", "-backups"])
		
		UnisisterThread.__bussy = False
	
	# Not very Pythonic, but a property can't be static, and I don't want
	# to use the variable directly, as I think it's quite likely this
	# would change in the future.
	# TODO: is this story true???
	@classmethod
	def is_bussy(cls):
		return cls.__bussy

class UnisisterConfiguration():
	def __init__(self):
		# Check if config available
		# TODO
		pass

class UnisisterTaskBar(wx.TaskBarIcon):
	ID_SYNCH = wx.NewId()
 
	def __init__(self):
		wx.TaskBarIcon.__init__(self)
 
		# Set the icon of Unisister
		# Temporally, this is the UGent Minerva favicon, due to a lack of official logo
		self.SetIcon(wx.Icon('favicon.ico', wx.BITMAP_TYPE_ICO), "Unisister")
 		
		# Before we can even think about the actual synchronisation, we need to initialize
		# the config object
		# TODO: create actual object
		self._config = UnisisterConfiguration()
		
 		# Create Timer-object, and keep it, as it's necessarry to let it function properly (GBC?)
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
			UnisisterThread(self._config).start()
		else:
			print _("We are already bussy synchronising!")
	
	def ShowPreferences(self, evt):
		pass
	
	def AboutUnisister(self, evt):
		info = wx.AboutDialogInfo()
		info.Name = "Unisister"
		info.Version = cfg.VERSION
		info.Copyright = "(C) 2013 Online - Urbanus"
		info.Icon = wx.Icon('favicon.ico', wx.BITMAP_TYPE_ICO)
		info.Description = "The sister of Unison.\n" + _("Unisister is a tool to automatically synchronize your directory with a central directory, using Unison.")
		info.WebSite = ("http://www.Online-Urbanus.be", "Online - Urbanus")
		info.Developers = ["Paretje"]
		try:
			info.License = open(cfg.LICENSE_LOCATION).read()
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
	gettext.bindtextdomain('unisister', cfg.LOCALEDIR)

if __name__ == "__main__":
	app = wx.App(False)
	_set_localisation()
	UnisisterTaskBar()
	app.MainLoop()
