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

VERSION = "0.2"
ICON_IDLE = "network-idle"
ICON_BUSSY = "network-transmit-receive"
AUTHORS = ["Paretje"]
LOCALEDIR = "/usr/share/locale"
SYNCS = "~/.config/unisister/syncs.ini"
TIMER_TICK = 60

# In Python 3.3, subprocess.DEVNULL has been added, so use this if available
try:
	DEVNULL = subprocess.DEVNULL
except AttributeError:
	DEVNULL = open(os.devnull, 'w')
