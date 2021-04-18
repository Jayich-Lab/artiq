#!/usr/bin/env python3

from PyQt5 import QtGui, QtWidgets
from artiq.gui.tools import LayoutWidget
from artiq.applets.simple import SimpleApplet
from artiq.coredevice.comm_moninj import *
from labrad import connect
from sipyco.pc_rpc import AsyncioClient as RPCClient
import asyncio
from config.artiq_dashboard import dashboard_config
from artiq_exps.utilities.devices import Devices
from artiq.applets.components.dds_channel import DDSChannel, DDSParameters
import os
import time


class DDS(QtWidgets.QDockWidget):
    def __init__(self, args):
        QtWidgets.QDockWidget.__init__(self, "DDS")
        self.dataset_name = args.update_time
        self.ip = dashboard_config["ip"]
        self.cxn = None
        self.exp_read_params = {
            "arguments": {},
            "class_name": "_GetUrukulDatasets",
            "file": "experiments/misc/get_urukul_datasets.py",
            "log_level": 30,
            "repo_rev": None,
            "priority": -10
        }
        self.channels = {}
        self.gui_initialized = asyncio.Event()
        self.make_GUI()
        asyncio.ensure_future(self._read_parameters())
        self.ad9910s = Devices().ad9910s
        self.ttls = Devices().ttls
        self.ad9910_sws = {}
        for kk in self.ad9910s:
            sw = self.ad9910s[kk]["arguments"]["sw_device"]
            sw_ch = self.ttls[sw]["arguments"]["channel"]
            self.ad9910_sws[sw_ch] = kk
        self.core_connector_task = asyncio.ensure_future(self.core_connector())

    def connect(self):
        if self.cxn is None:
            self.cxn = connect(self.ip,
                               password=os.environ["LABRADPASSWORD"])

    async def core_connector(self):
        await self.gui_initialized.wait()
        new_core_connection = CommMonInj(self.monitor_cb, self.injection_status_cb,
                                         self.disconnect_cb)
        port = 1383
        core_addr = Devices().cores["core"]["arguments"]["host"]
        await new_core_connection.connect(core_addr, port)
        self.core_connection = new_core_connection
        for channel in self.ad9910_sws:
            self.core_connection.monitor_probe(True, channel, TTLProbe.level.value)
            self.core_connection.monitor_probe(True, channel, TTLProbe.oe.value)

    def monitor_cb(self, channel, probe, value):
        dds = self.ad9910_sws[channel]
        if not probe:
            self.channels[dds].on_monitor_switch_changed(bool(value))

    def injection_status_cb(self, channel, override, value):
        return

    def disconnect_cb(self):
        return

    def data_changed(self, data, mods):
        """Does not work when running as an applet."""
        kk = 0
        if mods[0]["action"] == "setitem":
            if not self.gui_initialized.is_set():
                for channel in self.ad9910s:
                    cpld = self.ad9910s[channel]["arguments"]["cpld_device"]
                    amp = data[f"misc.{channel}.amplitude"][1]
                    att = data[f"misc.{channel}.att"][1]
                    frequency = data[f"misc.{channel}.frequency"][1]
                    phase = data[f"misc.{channel}.phase"][1]
                    state = data[f"misc.{channel}.state"][1]
                    channel_param = DDSParameters(
                        self.parent, channel, cpld, amp, att, frequency,
                        phase, state)
                    channel_widget = DDSChannel(channel_param, self)
                    self.channels[channel] = channel_widget
                    self.grid.addWidget(channel_widget, kk, 0)
                    kk += 1
                self.gui_initialized.set()
            else:
                for channel in self.ad9910s:
                    frequency = data[f"misc.{channel}.frequency"][1]
                    self.channels[channel].on_monitor_freq_changed(frequency)
                    amp = data[f"misc.{channel}.amplitude"][1]
                    self.channels[channel].on_monitor_amp_changed(amp)
                    att = data[f"misc.{channel}.att"][1]
                    self.channels[channel].on_monitor_att_changed(amp)
                    # do not change the state here.

    def make_GUI(self):
        font = QtGui.QFont('Arial', 15)
        self.grid = LayoutWidget()
        self.setWidget(self.grid)

    async def _read_parameters(self):
        await self.parent.submit_experiment(
            "main", self.exp_read_params, priority=-10)

def main():
    applet = SimpleApplet(DDS)
    applet.add_dataset(name="update_time", help=None, required=False,
                       default="misc.dds_update_time")
    applet.run()

if __name__ == "__main__":
    main()
