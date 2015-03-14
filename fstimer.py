#!/usr/bin/env python3

import fstimer.timer
from gi.repository import Gtk

if __name__ == '__main__':
    pytimer = fstimer.timer.PyTimer()
    settings = Gtk.settings_get_default()
    settings.props.Gtk_button_images = True
    Gtk.main()
