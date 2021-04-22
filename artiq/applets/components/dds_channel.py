from PyQt5 import QtWidgets, QtGui, QtCore
from artiq.gui.tools import LayoutWidget
from copy import deepcopy
import asyncio


class DDSParameters:
    def __init__(self, client, channel, cpld, amplitude, att, frequency, phase, state):
        self.client = client
        self.channel = channel
        self.cpld = cpld
        self._amplitude = amplitude
        self._att = att
        self._frequency = frequency
        self._phase = phase
        self._state = state
        self._change_dds_param = {
            "arguments": {},
            "class_name": "_SetUrukulParameters",
            "file": "experiments/misc/set_urukul_parameters.py",
            "log_level": 30,
            "repo_rev": None,
            "priority": -10
        }

    @property
    def amplitude(self):
        return self._amplitude

    @property
    def att(self):
        return self._att

    @property
    def frequency(self):
        return self._frequency

    @property
    def phase(self):
        return self._phase

    @property
    def state(self):
        return self._state

    def set_amplitude(self, value, update=True):
        if value != self._amplitude and update:
            command = [(self.channel, "amplitude", value)]
            self._change_dds(command)
        self._amplitude = value

    def set_att(self, value, update=True):
        if value != self._att and update:
            command = [(self.channel, "att", value)]
            self._change_dds(command)
        self._att = value

    def set_frequency(self, value, update=True):
        if value != self._frequency and update:
            command = [(self.channel, "frequency", value)]
            self._change_dds(command)
        self._frequency = value

    def set_phase(self, value, update=True):
        if value != self._phase and update:
            command = [(self.channel, "phase", value)]
            self._change_dds(command)
        self._phase = value

    def set_state(self, value, update=True):
        if value != self._state and update:
            command = [(self.channel, "state", value)]
            self._change_dds(command)
        self._state = value

    def _change_dds(self, command):
        params = deepcopy(self._change_dds_param)
        params["arguments"]["updates"] = str(command)
        asyncio.ensure_future(self._change_dds_worker(params))

    async def _change_dds_worker(self, params):
        self.rid = await self.client.submit_experiment(
            "main", params, priority=-10)


class DDSDetail(QtWidgets.QDialog):
    def __init__(self, dds_parameters, parent=None):
        self.dds_parameters = dds_parameters
        super().__init__(parent)
        self.make_GUI()
        self.initialize_connections()

    def make_GUI(self):
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        labelfont = QtGui.QFont('Arial', 10)
        spinboxfont = QtGui.QFont('Arial', 15)

        label = QtWidgets.QLabel(f"CPLD: {self.dds_parameters.cpld}")
        label.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                            QtWidgets.QSizePolicy.Fixed)
        label.setFont(labelfont)
        grid.addWidget(label, 0, 0)

        label = QtWidgets.QLabel("Att (dB)")
        label.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                            QtWidgets.QSizePolicy.Fixed)
        label.setFont(labelfont)
        grid.addWidget(label, 1, 0)

        self.att_box = QtWidgets.QDoubleSpinBox()
        self.att_box.setDecimals(1)
        self.att_box.setMinimum(-31.5)
        self.att_box.setMaximum(0.)
        self.att_box.setSingleStep(0.5)
        self.att_box.setFont(spinboxfont)
        self.att_box.setKeyboardTracking(False)
        self.att_box.setValue(-self.dds_parameters.att)
        grid.addWidget(self.att_box, 2, 0)

    def initialize_connections(self):
        self.att_box.valueChanged.connect(self.on_widget_att_changed)

    def on_widget_att_changed(self, val):
        self.dds_parameters.set_att(-val)


class DDSChannel(QtWidgets.QGroupBox):
    def __init__(self, dds_parameters, parent=None):
        self.dds_parameters = dds_parameters
        super().__init__(parent)
        self.make_GUI()
        self.initialize_connections()

    def make_GUI(self):
        titlefont = QtGui.QFont('Arial', 16)
        labelfont = QtGui.QFont('Arial', 10)
        buttonfont = QtGui.QFont('Arial', 15)
        spinboxfont = QtGui.QFont('Arial', 15)
        
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                           QtWidgets.QSizePolicy.Fixed)

        label = QtWidgets.QLabel(self.dds_parameters.channel)
        label.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                            QtWidgets.QSizePolicy.Fixed)
        label.setAlignment(QtCore.Qt.AlignHCenter)
        label.setFont(titlefont)
        grid.addWidget(label, 0, 0, 1, 3)

        label = QtWidgets.QLabel("Frequency (MHz)")
        label.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                            QtWidgets.QSizePolicy.Fixed)
        label.setFont(labelfont)
        grid.addWidget(label, 1, 0)

        label = QtWidgets.QLabel("Amplitude")
        label.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                            QtWidgets.QSizePolicy.Fixed)
        label.setFont(labelfont)
        grid.addWidget(label, 1, 1)

        self.freq_box = QtWidgets.QDoubleSpinBox()
        self.freq_box.setDecimals(3)
        self.freq_box.setMinimum(1.0)
        self.freq_box.setMaximum(500.0)
        self.freq_box.setSingleStep(0.1)
        self.freq_box.setFont(spinboxfont)
        self.freq_box.setKeyboardTracking(False)
        MHz_to_Hz = 1.e6
        self.freq_box.setValue(self.dds_parameters.frequency / MHz_to_Hz)
        grid.addWidget(self.freq_box, 2, 0)

        self.amp_box = QtWidgets.QDoubleSpinBox()
        self.amp_box.setDecimals(5)
        self.amp_box.setMinimum(0.0)
        self.amp_box.setMaximum(1.0)
        self.amp_box.setSingleStep(0.01)
        self.amp_box.setFont(spinboxfont)
        self.amp_box.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                   QtWidgets.QSizePolicy.Preferred)
        self.amp_box.setKeyboardTracking(False)
        self.amp_box.setValue(self.dds_parameters.amplitude)
        grid.addWidget(self.amp_box, 2, 1)

        self.switch_button = QtWidgets.QPushButton("o")
        self.switch_button.setFont(buttonfont)
        self.switch_button.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                         QtWidgets.QSizePolicy.Fixed)
        self.switch_button.setCheckable(True)
        if self.dds_parameters.state:
            self.switch_button.setChecked(self.dds_parameters.state)
            self.set_switch_button_text(self.dds_parameters.state)
        grid.addWidget(self.switch_button, 2, 2)

    def initialize_connections(self):
        self.freq_box.valueChanged.connect(self.on_widget_freq_changed)
        self.amp_box.valueChanged.connect(self.on_widget_amp_changed)
        self.switch_button.clicked.connect(self.on_widget_switch_changed)

    def on_widget_freq_changed(self, val):
        MHz_to_Hz = 1.e6
        self.dds_parameters.set_frequency(val * MHz_to_Hz)

    def on_widget_amp_changed(self, val):
        self.dds_parameters.set_amplitude(val)

    def on_widget_switch_changed(self, checked):
        self.dds_parameters.set_state(checked)
        self.set_switch_button_text(checked)

    def on_monitor_freq_changed(self, val):
        MHz_to_Hz = 1.e6
        self.freq_box.blockSignals(True)
        self.freq_box.setValue(val / MHz_to_Hz)
        self.freq_box.blockSignals(False)
        self.dds_parameters.set_frequency(val, False)

    def on_monitor_amp_changed(self, val):
        self.amp_box.blockSignals(True)
        self.amp_box.setValue(val)
        self.amp_box.blockSignals(False)
        self.dds_parameters.set_amplitude(val, False)

    def on_monitor_att_changed(self, val):
        self.dds_parameters.set_att(val, False)

    def on_monitor_switch_changed(self, checked):
        self.switch_button.blockSignals(True)
        self.switch_button.setChecked(checked)
        self.switch_button.blockSignals(False)
        self.set_switch_button_text(checked)
        self.dds_parameters.set_state(checked, False)

    def set_switch_button_text(self, checked):
        if checked:
            self.switch_button.setText("I")
        else:
            self.switch_button.setText("o")

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu()
        details_action = menu.addAction("Details")
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == details_action:
            self.show_details()

    def show_details(self):
        self.details = DDSDetail(self.dds_parameters)
        self.details.exec_()


if __name__ == "__main__":
    import sys
    from asyncqt import QEventLoop

    app = QtWidgets.QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    with loop:
        client = None
        channel = "urukul0_ch0"
        cpld = "urukul0"
        amplitude = 0.
        att = 0.
        frequency = 1.
        phase = 0.
        state = True
        p = DDSParameters(client, channel, cpld, amplitude, att, frequency, phase, state)
        w = DDSChannel(p)
        w.show()
        loop.run_forever()
