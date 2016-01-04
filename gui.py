import config

import zope.event

from gi.repository import Gtk
from gi.repository import GLib

from gettext import gettext as _

class UnisisterStatusIcon(Gtk.StatusIcon):
	def __init__(self, model, controller):
		Gtk.StatusIcon.__init__(self)

		self.model = model
		self.controller = controller

		self.set_from_icon_name(config.ICON_IDLE)
		# TODO: Use of name and title? set_visisble?
		self.set_name('unisister')
		self.set_title('Unisister')
		self.set_tooltip_text('Unisister')

		self._init_menu()
		self.connect('popup-menu', self.popup_menu)

		zope.event.subscribers.append(self.update_icon)
		self.controller.start_timer()

	def _init_menu(self):
		self.menu = Gtk.Menu()

		self.menu_item_sync = Gtk.MenuItem(_("Force Synchronisation"))
		self.menu_item_sync.connect('activate', lambda _: self.controller.synchronize_all())

		#self.menu_item_pref = Gtk.MenuItem(_("Preferences"))
		#self.menu_item_pref.connect('activate', self.preferences)

		self.menu_item_about = Gtk.MenuItem(_("About"))
		self.menu_item_about.connect('activate', show_about_dialog)

		self.menu_item_quit = Gtk.MenuItem(_("Quit"))
		self.menu_item_quit.connect('activate', self.quit)

		self.menu.append(self.menu_item_sync)
		#self.menu.append(self.menu_item_pref)
		self.menu.append(self.menu_item_about)
		self.menu.append(self.menu_item_quit)
		self.menu.show_all()

	def update_icon(self, state):
		if state.code == 'started':
			GLib.idle_add(self.set_from_icon_name, config.ICON_BUSSY)
			GLib.idle_add(self.set_tooltip_text, 'Unisister\n' + _("Synchronizing %s")%', '.join(self.model.busy))
		elif len(self.model.busy) == 0:
			GLib.idle_add(self.set_from_icon_name, config.ICON_IDLE)
			GLib.idle_add(self.set_tooltip_text, 'Unisister')
		else:
			GLib.idle_add(self.set_tooltip_text, 'Unisister\n' + _("Synchronizing %s")%', '.join(self.model.busy))

	def popup_menu(self, icon, button, time):
		self.menu.popup(None, None, Gtk.StatusIcon.position_menu, self, button, time)

	def quit(self, widget):
		self.controller.stop_timer()
		Gtk.main_quit()

def show_about_dialog(widget):
	dialog = Gtk.AboutDialog()

	dialog.set_program_name("Unisister")
	dialog.set_logo_icon_name(config.ICON_IDLE)
	dialog.set_comments("The sister of Unison.\n" + _("Unisister is a tool to automatically synchronize your directory with a central directory, using Unison."))
	dialog.set_version(config.VERSION)
	dialog.set_authors(config.AUTHORS)
	dialog.set_license_type(Gtk.License.GPL_3_0)

	dialog.run()
	dialog.destroy()
