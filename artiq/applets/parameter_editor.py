#!/usr/bin/env python3

import os
import asyncio
import labrad

from functools import partial
from PyQt5 import QtGui, QtWidgets, QtCore
from sipyco import pyon
from artiq.gui.tools import LayoutWidget
from artiq.applets.simple import SimpleApplet
from config.artiq_dashboard import dashboard_config
from artiq.applets.components.parameter_lineedits import ParameterLineEdit
from artiq.applets.components.parameter_details import ParameterDetails
from pydux.lib.control.servers.parameter_database.parameter_types import Parameter


class ParameterEditor(QtWidgets.QDockWidget):
    def __init__(self, args):
        QtWidgets.QDockWidget.__init__(self, "Drift Tracker")
        self.ip = dashboard_config["ip"]
        self.cxn = labrad.connect(
            self.ip, password=os.environ["LABRADPASSWORD"])
        self.load_all_parameters()
        self.set_GUI_constants()
        self.make_GUI()

    def set_GUI_constants(self):
        light_gray = 248
        self.bg_light = QtGui.QColor(light_gray, light_gray, light_gray)
        dark_gray = 228
        self.bg_dark = QtGui.QColor(dark_gray, dark_gray, dark_gray)

    def load_all_parameters(self):
        self.params = {}
        self.param_lineedits = {}
        collections = self.cxn.parameter_database.list_collections()
        for collection in collections:
            self.params[collection] = {}
            self.param_lineedits[collection] = {}
            parameters = self.cxn.parameter_database.list_parameters(collection)
            for parameter in parameters:
                raw = self.cxn.parameter_database.get_raw_form(collection, parameter)
                self.params[collection][parameter] = Parameter.from_raw_form(raw)
                self.param_lineedits[collection][parameter] = ParameterLineEdit.from_parameter(
                    self, collection, parameter, self.params[collection][parameter])

    def connect(self):
        if not self.cxn.connected:
            self.cxn = labrad.connect(
                self.ip, password=os.environ["LABRADPASSWORD"])

    def data_changed(self, data, mods):
        pass

    def make_collection_item(self, collection):
        item = QtWidgets.QTreeWidgetItem()
        item.setText(0, collection)
        font = QtGui.QFont()
        font.setBold(True)
        item.setFont(0, font)
        item.setBackground(0, self.bg_light)
        item.setBackground(1, self.bg_light)
        item.setFlags(item.flags() ^ QtCore.Qt.ItemIsSelectable)
        for kk, parameter in enumerate(sorted(self.params[collection].keys())):
            child = QtWidgets.QTreeWidgetItem([parameter, None])
            if kk % 2 == 0:
                child.setBackground(0, self.bg_light)
            else:
                child.setBackground(0, self.bg_dark)
            item.addChild(child)
            size = QtCore.QSize()
            size.setHeight(15)
            child.setSizeHint(0, size)
            child.setBackground(1, self.bg_light)
            child.widget_content = self.param_lineedits[collection][parameter]
            self.table.setItemWidget(child, 1, self.param_lineedits[collection][parameter])
        return item

    def open_menu(self, position):
        menu = QtWidgets.QMenu()
        reload_action = menu.addAction("Reload registry")
        details_action = menu.addAction("Details")
        action =menu.exec_(self.table.viewport().mapToGlobal(position))
        if action == reload_action:
            self.connect()
            self.cxn.parameter_database.load_registry()
        elif action == details_action:
            self.show_details()

    def show_details(self):
        try:
            sitem = self.table.selectedItems()[0]
            name = sitem.text(0)
            collection = sitem.parent().text(0)
            details = ParameterDetails.from_parameter(
                self, collection, name, self.params[collection][name])
            details.exec_()
        except Exception as e:
            pass

    def make_GUI(self):
        font = QtGui.QFont('Arial', 15)
        grid = LayoutWidget()
        self.setWidget(grid)
        self.table = QtWidgets.QTreeWidget()
        self.table.setColumnCount(2)
        self.table.setHeaderLabels(["Name", "Value"])
        self.table.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.table.header().setStretchLastSection(False)
        self.table.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_menu)
        self.table.setIndentation(10)
        grid.addWidget(self.table, 0, 0)
        p = QtGui.QPalette()
        p.setColor(9, QtGui.QColor(248,248,248))
        self.setPalette(p)

        for collection in sorted(self.params.keys()):
            collection_item = self.make_collection_item(collection)
            self.table.addTopLevelItem(collection_item)

def main():
    applet = SimpleApplet(ParameterEditor)
    applet.run()

if __name__ == "__main__":
    main()
