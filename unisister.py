#!/usr/bin/python
# Unisister
# Copyright: (C) 2013 Online - Urbanus
# Website: http://www.Online-Urbanus.be
# Last modified: 19/06/2013 by Paretje

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

import threading
import subprocess
import os
import tempfile

import config

def error_dialog(message):
	"""Display a dialog showing the given error message."""
	dlg = wx.MessageDialog(None, message, _('Error'), wx.OK | wx.ICON_ERROR)
	dlg.ShowModal()
	dlg.Destroy()

def get_icon(name, large=False):
	"""
	Get the icon specified by the name given, in the location specified in
	the config.
	
	When the large flag is True, we will look in the path specified in the 
	config as the path where the larger icons are located.
	"""
	# TODO: use theme-specific icons
	if large:
		return wx.Icon(os.path.join(config.ICON_LOCATION_LARGE,
			name + '.png'), wx.BITMAP_TYPE_PNG)
	else:
		return wx.Icon(os.path.join(config.ICON_LOCATION,
			name + '.png'), wx.BITMAP_TYPE_PNG)

def show_notification(title, description=None):
	# TODO: use a more cross-platform solution
	# TODO: description optional?
	import pynotify
	pynotify.init("Basics")		# TODO: Correct?
	pynotify.Notification(title, description).show()

class UnisisterPreferences(wx.Frame):
	backends = ['unison']
	
	def __init__(self, task_bar):
		wx.Frame.__init__(self, None, wx.ID_ANY, _("Unisister Preferences"))
		self.task_bar = task_bar
		panel = wx.Panel(self, wx.ID_ANY)
		
		# TODO: better names?
		# TODO: Passwords using gpg-agent?
		# TODO: Add hover texts where needed
		form_box = wx.BoxSizer(wx.VERTICAL)
		form = wx.FlexGridSizer(cols=2, vgap=5, hgap=25)
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
		
		# Hmmm, seems like a bug in wxPython. The DirPickerCtrl doesn't
		# seem to work, so we simply use the standard TextCtrl widget.
		self.local_location = wx.TextCtrl(panel, value=self.task_bar.config.Read('local_location'))
		form.Add(wx.StaticText(panel, label=_("Local folder:")), flag=wx.ALIGN_CENTER_VERTICAL)
		form.Add(self.local_location, flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
		
		self.interval = wx.TextCtrl(panel, value=self.task_bar.config.Read('interval'))
		form.Add(wx.StaticText(panel, label=_("Syncing interval:")), flag=wx.ALIGN_CENTER_VERTICAL)
		form.Add(self.interval, flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
		
		self.backend = wx.Choice(panel, choices=UnisisterPreferences.backends)
		self.backend.SetSelection(self.get_current_backend_id())
		form.Add(wx.StaticText(panel, label=_("Backend:")), flag=wx.ALIGN_CENTER_VERTICAL)
		form.Add(self.backend, flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
		
		self.backend_location_server = wx.TextCtrl(panel, value=self.task_bar.config.Read('backend_location_server'))
		form.Add(wx.StaticText(panel, label=_("Backend location on server:")), flag=wx.ALIGN_CENTER_VERTICAL)
		form.Add(self.backend_location_server, flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
		
		self.backend_location_local = wx.FilePickerCtrl(panel, path=self.task_bar.config.Read('backend_location_local'))
		form.Add(wx.StaticText(panel, label=_("Backend location on local machine:")), flag=wx.ALIGN_CENTER_VERTICAL)
		form.Add(self.backend_location_local, flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
		
		form_save.Add(wx.Button(panel, wx.ID_CANCEL, _("Cancel")), flag=wx.ALL, border=10)
		form_save.Add(wx.Button(panel, wx.ID_OK, _("OK")), flag=wx.ALL, border=10)
		
		form_box.Add(form, 0, flag=wx.EXPAND|wx.ALL, border=10)
		form_box.Add(wx.StaticText(panel), 1)
		form_box.Add(form_save, flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, border=5)
		panel.SetSizerAndFit(form_box)
		
		# The calculated width is a bit small, so we only use the height
		self.SetSize((500, self.GetBestSizeTuple()[1]))
		
		self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)
		self.Bind(wx.EVT_BUTTON, self.OnOK, id=wx.ID_OK)
	
	def OnCancel(self, evt):
		self.Close(True)
	
	def OnOK(self, evt):
		# Stop the timer, so it certainly doesn't start when changing
		# the configuration.
		self.task_bar.timer.Stop()
		
		# Primary preferences
		self.task_bar.config.Write('server_address', self.server_address.GetValue())
		self.task_bar.config.Write('server_username', self.server_username.GetValue())
		self.task_bar.config.Write('server_location', self.server_location.GetValue())
		self.task_bar.config.Write('local_location', self.local_location.GetValue())
		
		# Test if the interval has been changed
		try:
			new_interval = int(self.interval.GetValue())
			self.task_bar.config.WriteInt('interval', new_interval)
		except ValueError:
			# TODO: Show error
			return
		
		# Backend preferences
		self.task_bar.config.Write('backend', UnisisterPreferences.backends[self.backend.GetSelection()])
		self.task_bar.config.Write('backend_location_server', self.backend_location_server.GetValue())
		self.task_bar.config.Write('backend_location_local', self.backend_location_local.GetPath())
		self.task_bar.config.Flush()
		self.Close(True)
		if self.task_bar.timer_should_be_running:
			self.task_bar.start_timer()
	
	def get_current_backend_id(self):
		try:
			return UnisisterPreferences.backends.index(self.task_bar.config.Read('backend'))
		except:
			# Get unison backend by default
			return UnisisterPreferences.backends.index('unison')

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
		self.task_bar.SetIcon(get_icon(config.ICON_BUSSY), "Unisister\nSynchronizing")
		
		# In Python 3.3, subprocess.DEVNULL has been added, so use this
		# if available
		try: 
			self.devnull = subprocess.DEVNULL
		except AttributeError: 
			self.devnull = open(os.devnull, 'w')
		
		# Start backend
		if self.task_bar.config.Read('backend') == 'csync':
			wx.CallAfter(error_dialog, _("Using csync as a backend is not supported by the current version of Unisister yet, but there is an intention to implement this later."))
		else:
			self.unison_backend()
		
		self.task_bar.SetIcon(get_icon(config.ICON_IDLE), "Unisister")
		UnisisterThread._bussy = False
	
	def unison_backend(self, prefer='', arguments=[]):
		# Test if the needed configuration is set
		if self.task_bar.config.Read('server_address') == "" \
		or self.task_bar.config.Read('local_location') == "" \
		or not os.path.isdir(self.task_bar.config.Read('local_location')):
			wx.CallAfter(self.no_configuration)
			return
		
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
		
		# Server address
		server = 'ssh://' + server_address + '/' + self.task_bar.config.Read('server_location')
		
		# Test if there is a specific prefer argument set given
		if prefer == '':
			prefer = server
		
		# Start the unison process
		# TODO: handle exceptions
		output = tempfile.TemporaryFile(mode='w+t')
		subprocess.call([unison_local, server, self.task_bar.config.Read('local_location'), '-batch', '-prefer', server] + arguments, stdout=self.devnull, stderr=output)
		
		# Look if there is something to tell ...
		output.seek(0)
		last_line = output.readlines()[-1].strip()
		if last_line == 'Nothing to do: replicas have not changed since last sync.':
			pass
		elif last_line == 'or invoke Unison with -ignorearchives flag.':
			# Somehow, the archive files have got corrupted. Try to fix it.
			print _("Somehow, the archive files have got corrupted. We are trying to fix it!")
			# TODO: do this better!
			# TODO: make it optional, as it could be a risque?
			self.unison_backend(prefer='newer', arguments=['-ignorearchives'])
		elif last_line == 'Please delete lock files as appropriate and try again.':
			lock_file = re.sub(r'The file (.+) on host .* should be deleted', r'\1', output.readlines()[-2].strip())
			os.unlink(lock_file)
			# TODO: Delete lockfile automatically
			#print _("There is a lockfile blocking unison.")
			#print lock_file + " deleted"
			show_notification("There is a lockfile blocking unison.", description="Please delete " + lock_file)
		elif last_line[0:12] == 'Fatal error:':
			show_notification(last_line[13:])
		else:
			show_notification(_("Synchronisation completed"), description=last_line)
	
	def no_configuration(self):
		self.task_bar.timer.Stop()
		error_dialog(_("Unisister has not been properly configurated. Open the preferences and fill in the necesarry and correct configuration."))
		self.task_bar.ShowPreferences(None)
	
	# Not very Pythonic, but a property can't be static, and I don't want
	# to use the variable directly, as I think it's quite likely this
	# would change in the future.
	# TODO: is this story true???
	@classmethod
	def is_bussy(cls):
		return cls._bussy

class UnisisterTaskBar(wx.TaskBarIcon):
	ID_SYNCH = wx.NewId()
	timer_should_be_running = True
 
	def __init__(self):
		wx.TaskBarIcon.__init__(self)
 		
 		# Load user-preferences
 		self.config = wx.Config('unisister')
 		
		# Set the icon of Unisister
		self.SetIcon(get_icon(config.ICON_IDLE), "Unisister")
 		
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
		
 		# Create Timer-object, and keep it, as it's necessarry to let in function properly (GBC?)
 		self.timer = wx.Timer(self, UnisisterTaskBar.ID_SYNCH)
		self.start_timer()
 
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
	
	def start_timer(self):
		self.Synchronisation(None)
		if self.config.ReadInt('interval') > 0:
			self.timer.Start(self.config.ReadInt('interval')*1000)
		else:
			self.timer.Start(120*1000)

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
