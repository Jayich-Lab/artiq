#!/usr/bin/env python3

from PyQt5 import QtGui, QtWidgets
from artiq.gui.tools import LayoutWidget
from artiq.applets.simple import SimpleApplet
from labrad import connect
from sipyco.pc_rpc import AsyncioClient as RPCClient
import asyncio
from config.artiq_dashboard import dashboard_config
import os


class PMT(QtWidgets.QDockWidget):
    def __init__(self, args):
        QtWidgets.QDockWidget.__init__(self, "PMT")
        self.dataset_name = args.dataset
        self.ip = dashboard_config["ip"]
        self.cxn = None
        self.rid = None
        self.make_GUI()
        self.run_pmt = {
            "arguments": {},
            "class_name": "_PMT",
            "file": "experiments/misc/pmt.py",
            "log_level": 30,
            "repo_rev": None,
            "priority": -20
        }
        self.get_experiment_run_status()

    def connect(self):
        if self.cxn is None:
            self.cxn = connect(self.ip,
                               password=os.environ["LABRADPASSWORD"])

    def data_changed(self, data, mods):
        try:
            n = float(data[self.dataset_name][1])
        except (KeyError, ValueError, TypeError):
            n = "---"
        self.qlcd.display(n)

    def get_mode(self):
        self.connect()
        p = self.cxn.parametervault
        is_differential = p.get_parameter("pmt", "differential_mode")
        return is_differential

    def get_detect_time(self):
        self.connect()
        p = self.cxn.parametervault
        detect_time = p.get_parameter("pmt", "detect_time_ms") * 1e-3
        return detect_time

    def make_GUI(self):
        font = QtGui.QFont('Arial', 15)
        grid = LayoutWidget()
        self.setWidget(grid)
        self.qlcd = QtWidgets.QLCDNumber()
        self.qlcd.setDigitCount(4)
        self.qlcd.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                QtWidgets.QSizePolicy.Expanding)
        grid.addWidget(self.qlcd, 0, 0, 1, 1)

        label = QtWidgets.QLabel("Mode: ")
        label.setFont(font)
        grid.addWidget(label, 1, 0)
        self.combo = QtWidgets.QComboBox()
        self.combo.addItem("normal")
        self.combo.addItem("differential")
        self.combo.setFont(font)
        is_differential = self.get_mode()
        if is_differential:
            self.combo.setCurrentIndex(1)
        else:
            self.combo.setCurrentIndex(0)
        self.combo.setSizeAdjustPolicy(self.combo.AdjustToContents)
        self.combo.setFrame(False)
        self.combo.currentIndexChanged.connect(self.on_mode_changed)
        grid.addWidget(self.combo, 1, 1)

        label = QtWidgets.QLabel("Time: ")
        label.setFont(font)
        grid.addWidget(label, 2, 0)
        self.spinbox = QtWidgets.QDoubleSpinBox()
        self.spinbox.setFont(font)
        self.spinbox.setDecimals(3)
        self.spinbox.setMinimum(0.001)
        self.spinbox.setMaximum(10.)
        detect_time = self.get_detect_time()
        self.spinbox.setValue(detect_time)
        self.spinbox.setSingleStep(.1)
        self.spinbox.setKeyboardTracking(False)
        self.spinbox.valueChanged.connect(self.on_detect_time_changed)
        grid.addWidget(self.spinbox, 2, 1)

        self.button = QtWidgets.QPushButton("Start")
        self.button.setFont(font)
        self.button.clicked.connect(self.on_button_clicked)
        self.button.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                  QtWidgets.QSizePolicy.Expanding)
        self.button.setCheckable(True)
        grid.addWidget(self.button, 0, 1)

    def on_button_clicked(self, checked):
        asyncio.ensure_future(self._on_button_clicked(checked))

    async def _on_button_clicked(self, checked):
        if checked:
            self.rid = await self.parent.submit_experiment(
                "main", self.run_pmt, priority=-20)
            self.button.setText("stop")
        else:
            self.button.setText("start")
            if self.rid is not None:
                await self.parent.request_terminate_experiment(self.rid)
                self.rid = None

    def on_mode_changed(self, idx):
        self.connect()
        p = self.cxn.parametervault
        p.set_parameter("pmt", "differential_mode", (idx == 1))

    def on_detect_time_changed(self, val):
        self.connect()
        p = self.cxn.parametervault
        p.set_parameter("pmt", "detect_time_ms", val * 1e3)

    def get_experiment_run_status(self):
        asyncio.ensure_future(self._get_experiment_run_status())

    async def _get_experiment_run_status(self):
        status = await self.parent.get_scheduler_status()
        running = False
        for kk in status:
            if status[kk]["expid"]["class_name"] == "_PMT":
                running = True
                self.rid = kk
                break
        if running:
            self.button.setChecked(True)
            self.button.setText("stop")

def main():
    applet = SimpleApplet(PMT)
    applet.add_dataset("dataset", "dataset to show", False,
                       default="pmt.last_counts")
    applet.run()

if __name__ == "__main__":
    main()
