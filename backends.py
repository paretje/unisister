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

import os
import tempfile
import subprocess
import re

class UnisonBackend:
	def __init__(self, sync_config):
		self.sync_config = sync_config

	def sync(self):
		# TODO: handle exceptions
		self._init_arguments()
		self._sync()
		result_code, data = self._interpret_output()

		# If archive is corrupt, synchronize again using -ignorearchives
		if result_code == 'corrupt':
			self.arguments.append('-ignorearchives')
			self._sync()
			result_code, data = self._interpret_output()

		# TODO: sent event to controller with result_code and data
	
	def _sync(self):
		self.output = tempfile.TemporaryFile(mode='w+t')
		subprocess.call(['unison'] + self.arguments, stdout=config.DEVNULL, stderr=output)

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
		# TODO: make a backup of those conflicts. The problem is that
		# unison makes a backup of everything then ...
		self.arguments += ['-prefer', server]

		# Synchronize timestamps
		self.arguments.append('-times')

		# Set unison executable location on the server
		if 'sever_backend' in self.sync_config \
		and self.sync_config['server_backend_location'] != "":
			self.arguments += ['-servercmd', self.sync_config['server_backend_location']]

	def _interpret_results(self, output):
		output.seek(0)
		last_line = output.readlines()[-1].strip()
		if last_line == 'Nothing to do: replicas have not changed since last sync.':
			return ('nothing', None)
		elif last_line == 'or invoke Unison with -ignorearchives flag.':
			return ('corrupt')
		elif last_line == 'Please delete lock files as appropriate and try again.':
			lock_file = re.sub(r'The file (.+) on host .* should be deleted', r'\1', output.readlines()[-2].strip())
			return ('lock', lock_file)
		elif last_line[0:12] == 'Fatal error:':
			return ('error', last_line[13:])
		else:
			# TODO: interprete values?
			return ('ok', last_line)
