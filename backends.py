#!/usr/bin/python
# Unisister
# Copyright: (C) 2013-2014 Online - Urbanus
# Website: http://www.Online-Urbanus.be
# Last modified: 20/05/2014 by Paretje

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

import threading

def start_unison_backend(icon, task):
	UnisonBackend.tasks.add(task)
	if len(UnisonBackend.tasks) > 0:
		print _("There can only be one unison backend running at a time. It's in the queue.")
	else:
		UnisonBackend(icon).start()

backends = {'unison', start_unison_backend}
def start_backend(icon, task):
	backends[task](icon, task)

class UnisonBackend(threading.Thread):
	tasks = {}
	
	def __init__(self, icon):
		threading.Thread.__init__(self)
		self.icon = icon

	def run(self):
		pass
