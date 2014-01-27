#!/usr/bin/python
# Unisister
# Copyright: (C) 2013-2014 Online - Urbanus
# Website: http://www.Online-Urbanus.be
# Last modified: 21/01/2014 by Paretje

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

from gi.repository import Gtk
from gi.repository import Notify

import gettext
from gettext import gettext as _
import locale

import threading
import subprocess
import os
import tempfile

import config

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

# TODO: Is this still needed?
def show_notification(title, description=None):
	Notify.Notification(title, description).show()

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

class UnisisterStatusIcon(Gtk.StatusIcon):
	def __init__(self):
		Gtk.StatusIcon.__init__(self)
		self.set_from_icon_name(config.ICON_IDLE)
		self.set_name('unisister')
		self.set_title('Unisister')

def set_localisation():
	# Code based on the code in system-config-printer v1.3.7
	try:
		locale.setlocale (locale.LC_ALL, "")
	except locale.Error:
		os.environ['LC_ALL'] = 'C'
		locale.setlocale (locale.LC_ALL, "")
	
	gettext.textdomain('unisister')
	gettext.bindtextdomain('unisister', config.LOCALEDIR)

if __name__ == "__main__":
	set_localisation()
	Notify.init("Unisister")
	status = UnisisterStatusIcon()
	Gtk.main()
	Notify.uninit();
