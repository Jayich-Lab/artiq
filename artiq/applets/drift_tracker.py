#!/usr/bin/env python3

import os
import asyncio
import labrad

from PyQt5 import QtGui, QtWidgets, QtCore
from sipyco import pyon
from artiq.gui.tools import LayoutWidget
from artiq.applets.simple import SimpleApplet
from artiq.applets.components.drift_tracker_channel import \
    DriftTrackerChannel, DriftTrackerParameters
from config.artiq_dashboard import dashboard_config


class DriftTracker(QtWidgets.QDockWidget):
    def __init__(self, args):
        QtWidgets.QDockWidget.__init__(self, "Drift Tracker")
        self.ip = dashboard_config["ip"]
        self.cxn = labrad.connect(
            self.ip, password=os.environ["LABRADPASSWORD"])
        self.channels = {}
        self.gui_initialized = asyncio.Event()
        self.drift_trackers = self.cxn.drift_tracker_server.list_drift_trackers()
        self.make_GUI()

    def connect(self):
        if not self.cxn.connected:
            self.cxn = labrad.connect(
                self.ip, password=os.environ["LABRADPASSWORD"])

    def data_changed(self, data, mods):
        pass

    def make_GUI(self):
        """TO DO: QListWidget should be changed to QListView.

        QListWidget does not support editable content, so bugs may happen.
        Additional, with QListView it is possible to populate Widgets vertically first
        and then wrap to the next column.
        """
        font = QtGui.QFont('Arial', 15)
        self.grid = QtWidgets.QListWidget()
        self.grid.setFlow(QtWidgets.QListView.LeftToRight)
        self.grid.setResizeMode(QtWidgets.QListView.Adjust)
        self.grid.setViewMode(QtWidgets.QListView.IconMode)
        self.setWidget(self.grid)
        for kk in self.drift_trackers:
            self.connect()
            raw_dt = self.cxn.drift_tracker_server.get_raw_drift_tracker(kk)
            channel_param = DriftTrackerParameters(
                self, kk, *tuple(raw_dt))
            channel_widget = DriftTrackerChannel(channel_param, self)
            self.channels[kk] = channel_widget

            item = QtWidgets.QListWidgetItem()
            item.setSizeHint(channel_widget.sizeHint())
            self.grid.setGridSize(channel_widget.sizeHint())
            self.grid.addItem(item)
            self.grid.setItemWidget(item, channel_widget)

def main():
    applet = SimpleApplet(DriftTracker)
    applet.run()

if __name__ == "__main__":
    main()
