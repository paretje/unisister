# Unisister
# Copyright: (C) 2013-2014 Online - Urbanus
# Website: http://www.Online-Urbanus.be
# Last modified: 19/06/2014 by Paretje

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

import config

import zope.event

import os
import tempfile
import threading
import subprocess
import re

class UnisisterBackendsController:
	def __init__(self, model):
		self.model = model

	def start_timer(self):
		self.synchronize_all()
		self.timer = threading.Timer(config.TIMER_TICK, self.timer_tick)
		self.timer.start()

	def stop_timer(self):
		self.timer.cancel()

	def timer_tick(self):
		sync_config = self.model.sync_config
		for sync in sync_config:
			# TODO: Synchronization?
			self.model.last_sync[sync] += config.TIMER_TICK
			if sync_config[sync]['interval'] > 0 and self.model.last_sync[sync] >= sync_config[sync]['interval']:
				self._start_synchronization(sync, sync_config[sync])
		self.timer = threading.Timer(config.TIMER_TICK, self.timer_tick)
		self.timer.start()

	def synchronize_all(self):
		sync_config = self.model.sync_config
		for sync in sync_config:
			self._start_synchronization(sync, sync_config[sync])

	def _start_synchronization(self, sync, sync_config):
		# TODO: synchronize?
		if sync not in self.model.busy:
			self.model.busy.add(sync)
			self.model.last_sync[sync] = 0
			zope.event.notify(StateEvent(sync, 'started'))
			available[sync_config['backend']](sync, sync_config).start()

class StateEvent:
	def __init__(self, sync, state_code, data=None):
		self.sync = sync
		self.code = state_code
		self.data = data

class UnisonBackend(threading.Thread):
	def __init__(self, sync, sync_config):
		threading.Thread.__init__(self)
		# Daemon threads are abruptly stopped at shutdown. Their
		# resources (such as open files, database transactions, etc.)
		# may not be released properly. If you want your threads to stop
		# gracefully, make them non-daemonic and use a suitable
		# signalling mechanism such as an Event.
		self.deamon = False

		self.sync = sync
		self.sync_config = sync_config

	def run(self):
		# TODO: handle exceptions
		self._init_arguments()
		self._sync()
		state = self._interpret_output()

		# If archive is corrupt, synchronize again using -ignorearchives
		if state.code == 'corrupt':
			self.arguments.append('-ignorearchives')
			self._sync()
			state = self._interpret_output()
		zope.event.notify(state)

	def _sync(self):
		self.output = tempfile.TemporaryFile(mode='w+t')
		subprocess.call(['unison'] + self.arguments, stdout=config.DEVNULL, stderr=self.output)

	def _init_arguments(self):
		# Test if the required configuration is set and valid
		if 'server_address' not in self.sync_config \
		or self.sync_config['server_address'] == "" \
		or 'server_location' not in self.sync_config \
		or self.sync_config['server_location'] == "" \
		or 'local_location' not in self.sync_config \
		or self.sync_config['local_location'] == "" \
		or not os.path.isdir(self.sync_config['local_location']):
			# TODO: return exception which should be catched to show
			# a message
			return None

		# Construct server url
		server = 'ssh://'
		if 'server_username' in self.sync_config \
		and self.sync_config['server_username'] != "":
			server += self.sync_config['server_username'] + '@'
		server += self.sync_config['server_address']
		server += '/' + self.sync_config['server_location']

		# Set basic arguments
		self.arguments = [server, self.sync_config['local_location']]

		# Set unison in batch mode, as to prevent it asking any questions
		self.arguments.append('-batch')

		# In case of any conflict, use the version of the file located
		# on the server
		self.arguments += ['-prefer', server]

		# If available, use -copyonconflict
		try:
			if '-copyonconflict' in subprocess.run(['unison', '-help'], stdout=subprocess.PIPE, universal_newlines=True).stdout:
				self.arguments.append('-copyonconflict')
		except AttributeError:
			if '-copyonconflict' in subprocess.check_output('unison -help ; exit 0', universal_newlines=True, shell=True):
				self.arguments.append('-copyonconflict')


		# Synchronize timestamps
		self.arguments.append('-times')

		# Set unison executable location on the server
		if 'server_backend_location' in self.sync_config \
		and self.sync_config['server_backend_location'] != "":
			self.arguments += ['-servercmd', self.sync_config['server_backend_location']]

	def _interpret_output(self):
		self.output.seek(0)
		last_line = self.output.readlines()[-1].strip()
		if last_line[0:14] == 'Nothing to do:':
			return StateEvent(self.sync, 'nothing', None)
		elif last_line == 'or invoke Unison with -ignorearchives flag.':
			return StateEvent(self.sync, 'corrupt')
		elif last_line == 'Please delete lock files as appropriate and try again.':
			lock_file = re.sub(r'The file (.+) on host .* should be deleted', r'\1', self.output.readlines()[-2].strip())
			return StateEvent(self.sync, 'lock', lock_file)
		elif last_line[0:12] == 'Fatal error:':
			return StateEvent(self.sync, 'error', last_line[13:])
		else:
			# TODO: interprete values?
			return StateEvent(self.sync, 'done', last_line)

available = {'unison': UnisonBackend}
