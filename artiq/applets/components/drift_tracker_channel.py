import asyncio
from time import time

from copy import deepcopy
from PyQt5 import QtWidgets, QtGui, QtCore
from sipyco import pyon
from artiq.gui.tools import LayoutWidget


class DriftTrackerParameters:
    def __init__(self, parent, label, detuning_factor, aom_center, drift_rate, start_time):
        self.parent = parent
        self.label = label
        self._detuning_factor = detuning_factor
        self._aom_center = aom_center
        self._drift_rate = drift_rate
        self._start_time = start_time

    @property
    def detuning_factor(self):
        return self._detuning_factor

    @property
    def aom_center_with_drift(self):
        aom_center = self._aom_center
        aom_center += self._drift_rate * (time() - self._start_time)
        return aom_center

    @property
    def aom_center(self):
        return self._aom_center

    @property
    def drift_rate(self):
        return self._drift_rate

    @property
    def start_time(self):
        return self._start_time

    def set_detuning_factor(self, value, update=True):
        if value != self._detuning_factor and update:
            self.parent.connect()
            self.parent.cxn.drift_tracker_server.set_detuning_factor(
                self.label, value)
        self._detuning_factor = value

    def set_aom_center(self, value, update=True):
        if value != self._aom_center and update:
            self.parent.connect()
            self.parent.cxn.drift_tracker_server.set_aom_center(
                self.label, value)
        self._aom_center = value

    def set_drift_rate(self, value, update=True):
        if value != self._drift_rate and update:
            self.parent.connect()
            self.parent.cxn.drift_tracker_server.set_drift_rate(
                self.label, value)
        self._drift_rate = value


class DriftTrackerDetail(QtWidgets.QDialog):
    def __init__(self, dt_params, parent=None):
        self.dt_params = dt_params
        super().__init__(parent)
        self.make_GUI()
        self.initialize_connections()

    def make_GUI(self):
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        labelfont = QtGui.QFont('Arial', 10)
        spinboxfont = QtGui.QFont('Arial', 15)

        label = QtWidgets.QLabel(f"Label: {self.dt_params.label}")
        label.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                            QtWidgets.QSizePolicy.Fixed)
        label.setFont(labelfont)
        grid.addWidget(label, 0, 0)

        label = QtWidgets.QLabel("Detuning Factor")
        label.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                            QtWidgets.QSizePolicy.Fixed)
        label.setFont(labelfont)
        grid.addWidget(label, 1, 0)

        self.detuning_factor_box = QtWidgets.QDoubleSpinBox()
        self.detuning_factor_box.setDecimals(0)
        self.detuning_factor_box.setMinimum(-4.)
        self.detuning_factor_box.setMaximum(4.)
        self.detuning_factor_box.setSingleStep(1.)
        self.detuning_factor_box.setFont(spinboxfont)
        self.detuning_factor_box.setKeyboardTracking(False)
        self.detuning_factor_box.setValue(self.dt_params.detuning_factor)
        grid.addWidget(self.detuning_factor_box, 2, 0)

        label = QtWidgets.QLabel("Drift Rate (Hz/s)")
        label.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                            QtWidgets.QSizePolicy.Fixed)
        label.setFont(labelfont)
        grid.addWidget(label, 1, 1)

        self.drift_rate_box = QtWidgets.QDoubleSpinBox()
        self.drift_rate_box.setDecimals(2)
        self.drift_rate_box.setMinimum(-100000.)
        self.drift_rate_box.setMaximum(100000.)
        self.drift_rate_box.setSingleStep(0.1)
        self.drift_rate_box.setFont(spinboxfont)
        self.drift_rate_box.setKeyboardTracking(False)
        self.drift_rate_box.setValue(self.dt_params.drift_rate)
        grid.addWidget(self.drift_rate_box, 2, 1)

    def initialize_connections(self):
        self.detuning_factor_box.valueChanged.connect(self.on_widget_detuning_factor_changed)
        self.drift_rate_box.valueChanged.connect(self.on_widget_drift_rate_changed)

    def on_widget_detuning_factor_changed(self, val):
        self.dt_params.set_detuning_factor(val)

    def on_widget_drift_rate_changed(self, val):
        self.dt_params.set_drift_rate(val)


class DriftTrackerChannel(QtWidgets.QGroupBox):
    def __init__(self, dt_params, parent=None):
        self.dt_params = dt_params
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

        label = QtWidgets.QLabel(self.dt_params.label)
        label.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                            QtWidgets.QSizePolicy.Fixed)
        label.setAlignment(QtCore.Qt.AlignHCenter)
        label.setFont(titlefont)
        grid.addWidget(label, 0, 0, 1, 2)

        label = QtWidgets.QLabel("AOM Center (MHz)")
        label.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                            QtWidgets.QSizePolicy.Fixed)
        label.setFont(labelfont)
        grid.addWidget(label, 1, 0)

        self.freq_box = QtWidgets.QDoubleSpinBox()
        self.freq_box.setDecimals(6)
        self.freq_box.setMinimum(1.0)
        self.freq_box.setMaximum(500.0)
        self.freq_box.setSingleStep(0.001)
        self.freq_box.setFont(spinboxfont)
        self.freq_box.setKeyboardTracking(False)
        MHz_to_Hz = 1.e6
        self.freq_box.setValue(self.dt_params.aom_center_with_drift / MHz_to_Hz)
        grid.addWidget(self.freq_box, 2, 0)

        self.update_button = QtWidgets.QPushButton("Update")
        self.update_button.setFont(buttonfont)
        self.update_button.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                         QtWidgets.QSizePolicy.Fixed)
        grid.addWidget(self.update_button, 2, 1)

    def initialize_connections(self):
        self.freq_box.valueChanged.connect(self.on_widget_freq_changed)
        self.update_button.clicked.connect(self.on_widget_update_clicked)

    def on_widget_freq_changed(self, val):
        MHz_to_Hz = 1.e6
        self.dt_params.set_aom_center(val * MHz_to_Hz)

    def on_widget_update_clicked(self, checked):
        MHz_to_Hz = 1.e6
        self.freq_box.blockSignals(True)
        self.freq_box.setValue(self.dt_params.aom_center_with_drift / MHz_to_Hz)
        self.freq_box.blockSignals(False)

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu()
        details_action = menu.addAction("Details")
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == details_action:
            self.show_details()

    def show_details(self):
        self.details = DriftTrackerDetail(self.dt_params)
        self.details.exec_()
