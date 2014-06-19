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

import subprocess

class UnisonBackend:
	def __init__(self, sync_config):
		self.sync_config = sync_config

	def sync(self):
		# TODO: handle exceptions
		arguments = self.get_arguments()
		output = tempfile.TemporaryFile(mode='w+t')
		subprocess.call(arguments.insert(0, 'unison'), stdout=config.DEVNULL, stderr=output)

	def get_arguments(self):
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
		arguments = [server, self.sync_config['local_location']]

		# Set unison in batch mode, as to prevent it asking any questions
		arguments.append('-batch')

		# In case of any conflict, use the version of the file located
		# on the server
		# TODO: make a backup of those conflicts. The problem is that
		# unison makes a backup of everything then ...
		arguments += ['-prefer', server]

		# Synchronize timestamps
		arguments.append('-times')

		# Set unison executable location on the server
		if 'sever_backend' in self.sync_config \
		and self.sync_config['server_backend_location'] != "":
			arguments += ['-servercmd', self.sync_config['server_backend_location']]

		return arguments
