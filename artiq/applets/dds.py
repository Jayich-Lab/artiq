#!/usr/bin/env python3

import os
import asyncio
import labrad

from PyQt5 import QtGui, QtWidgets
from sipyco import pyon
from artiq.gui.tools import LayoutWidget
from artiq.applets.simple import SimpleApplet
from artiq.coredevice.comm_moninj import *
from artiq.applets.components.dds_channel import DDSChannel, DDSParameters
from config.artiq_dashboard import dashboard_config


class DDS(QtWidgets.QDockWidget):
    def __init__(self, args):
        QtWidgets.QDockWidget.__init__(self, "DDS")
        self.dataset_name = args.update_time
        self.ip = dashboard_config["ip"]
        self.cxn = labrad.connect(
            self.ip, password=os.environ["LABRADPASSWORD"])
        self.exp_read_params = {
            "arguments": {},
            "class_name": "_GetUrukulDatasets",
            "file": "experiments/misc/get_urukul_datasets.py",
            "log_level": 30,
            "repo_rev": None,
            "priority": 0
        }
        self.channels = {}
        self.gui_initialized = asyncio.Event()
        self.make_GUI()

        if "dds_display_chs" in dashboard_config:
            ad9910_names = dashboard_config["dds_display_chs"]
        else:
            ad9910_names = self.cxn.artiq_control.get_ad9910s()
        self.ad9910s = {}
        for name in ad9910_names:
            self.ad9910s[name] = pyon.decode(self.cxn.artiq_control.get_ad9910_info(name))

        ttl_names = self.cxn.artiq_control.get_ttls()
        self.ttls = {}
        for name in ttl_names:
            self.ttls[name] = pyon.decode(self.cxn.artiq_control.get_ttl_info(name))

        self.ad9910_sws = {}
        for kk in self.ad9910s:
            sw = self.ad9910s[kk]["arguments"]["sw_device"]
            sw_ch = self.ttls[sw]["arguments"]["channel"]
            self.ad9910_sws[sw_ch] = kk

        self.read_parameters()
        self.core = self.cxn.artiq_control.get_core_info("core")

        # disables core connector for now.
        #self.core_connector_task = asyncio.ensure_future(self.core_connector())

    def connect(self):
        if not self.cxn.connected:
            self.cxn = labrad.connect(
                self.ip, password=os.environ["LABRADPASSWORD"])

    def read_parameters(self):
        self.connect()
        self.cxn.artiq_control.submit_experiment(
            "main", pyon.encode(self.exp_read_params), -10)

    async def core_connector(self):
        """If the state does not update correctly, maybe some looping is needed."""
        await self.gui_initialized.wait()
        new_core_connection = CommMonInj(self.monitor_cb, self.injection_status_cb,
                                         self.disconnect_cb)
        port = 1383
        core_addr = self.core["arguments"]["host"]
        await new_core_connection.connect(core_addr, port)
        self.core_connection = new_core_connection
        for channel in self.ad9910_sws:
            self.core_connection.monitor_probe(True, channel, TTLProbe.level.value)
            self.core_connection.monitor_probe(True, channel, TTLProbe.oe.value)

    def monitor_cb(self, channel, probe, value):
        dds = self.ad9910_sws[channel]
        if not probe and dds in channels:
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
                if mods[0]["key"] == "misc.dds_update_time":
                    for channel in self.ad9910s:
                        cpld = self.ad9910s[channel]["arguments"]["cpld_device"]
                        amp = data[f"misc.{channel}.amplitude"][1]
                        att = data[f"misc.{channel}.att"][1]
                        frequency = data[f"misc.{channel}.frequency"][1]
                        phase = data[f"misc.{channel}.phase"][1]
                        state = data[f"misc.{channel}.state"][1]
                        channel_param = DDSParameters(
                            self, channel, cpld, amp, att, frequency,
                            phase, state)
                        channel_widget = DDSChannel(channel_param, self)
                        self.channels[channel] = channel_widget
                        self.grid.addWidget(channel_widget, kk, 0)
                        kk += 1
                    self.gui_initialized.set()
            else:
                for mod in mods:
                    if mod["key"] != "misc.dds_update_time":
                        value = mod["value"][1]
                        channel = mod["key"].split(".")[1]
                        if mod["key"].endswith("frequency"):
                            self.channels[channel].on_monitor_freq_changed(value)
                        if mod["key"].endswith("amplitude"):
                            self.channels[channel].on_monitor_amp_changed(value)
                        if mod["key"].endswith("att"):
                            self.channels[channel].on_monitor_att_changed(value)

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
    cxn = labrad.connect(dashboard_config["ip"],
                         password=os.environ["LABRADPASSWORD"])
    ddses = cxn.artiq_control.get_ad9910s()
    if "dds_display_chs" in dashboard_config:
        ddses = dashboard_config["dds_display_chs"]
    cxn.disconnect()
    for channel in ddses:
        for item in ["amplitude", "att", "frequency", "phase", "state"]:
            applet.add_dataset(name=f"dds_{channel}_{item}", help=None, required=False,
                               default=f"misc.{channel}.{item}")
    applet.run()

if __name__ == "__main__":
    main()
