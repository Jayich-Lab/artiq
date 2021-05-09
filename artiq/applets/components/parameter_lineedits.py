from PyQt5 import QtWidgets, QtGui, QtCore
from artiq.gui.tools import LayoutWidget

_type_to_class = {}  # placeholder


class ParameterLineEdit(QtWidgets.QWidget):
    @classmethod
    def from_parameter(cls, client, collection, name, parameter):
        _type = parameter.type
        return _type_to_class[_type](client, collection, name, parameter)

    def __init__(self, client, collection, name, parameter):
        self.client = client
        self.collection = collection
        self.name = name
        self.parameter = parameter

    def gui_parameter_changed(self):
        self.client.connect()
        self.client.cxn.parameter_database.set_raw_value(
            self.collection, self.name, self.parameter.raw_value)

    def wheelEvent(self, *args, **kwargs):
        """Prevent widgets from interacting with mouse wheel."""
        pass

    def remote_parameter_changed(self, raw_value):
        raise NotImplementedError()


class BoolLineEdit(QtWidgets.QCheckBox, ParameterLineEdit):
    def __init__(self, client, collection, name, parameter):
        ParameterLineEdit.__init__(self, client, collection, name, parameter)
        QtWidgets.QCheckBox.__init__(self)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setCheckState(self.param_state)
        self.stateChanged.connect(self.set_param_state)
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignVCenter)
        self.setLayout(layout)

    @property
    def param_state(self):
        if self.parameter.parsed_value:
            return QtCore.Qt.Checked
        else:
            return QtCore.Qt.Unchecked

    def set_param_state(self, state):
        if state != self.param_state:
            self.parameter.set_value(state == QtCore.Qt.Checked)
            self.gui_parameter_changed()

    def remote_parameter_changed(self, raw_value):
        self.parameter.set_raw_value(raw_value)
        self.blockSignals(True)
        self.setCheckState(self.param_state)
        self.blockSignals(False)


class StringLineEdit(QtWidgets.QLineEdit, ParameterLineEdit):
    def __init__(self, client, collection, name, parameter):
        ParameterLineEdit.__init__(self, client, collection, name, parameter)
        QtWidgets.QLineEdit.__init__(self)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setText(self.param_text)
        self.editingFinished.connect(self.set_param_text)
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignVCenter)
        self.setLayout(layout)

    @property
    def param_text(self):
        return self.parameter.parsed_value

    def set_param_text(self):
        text = self.text()
        if text != self.param_text:
            self.parameter.set_value(text)
            self.gui_parameter_changed()

    def remote_parameter_changed(self, raw_value):
        self.parameter.set_raw_value(raw_value)
        self.blockSignals(True)
        self.setText(self.param_text)
        self.blockSignals(False)


class FloatLineEdit(QtWidgets.QDoubleSpinBox, ParameterLineEdit):
    def __init__(self, client, collection, name, parameter):
        ParameterLineEdit.__init__(self, client, collection, name, parameter)
        QtWidgets.QDoubleSpinBox.__init__(self)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setKeyboardTracking(False)
        self._set_GUI_values()
        self.valueChanged.connect(self.set_param_value)
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignVCenter)
        self.setLayout(layout)

    def _set_GUI_values(self):
        value, (min, max), digits, unit, scale = self.parameter.raw_value
        self.setValue(value)
        self.setMinimum(min)
        self.setMaximum(max)
        self.setDecimals(digits)
        self.setSingleStep(10**(-digits))
        if unit != "":
            suffix = " " + unit
        else:
            suffix = ""
        suffix = suffix.replace("u", "\u00B5")
        self.setSuffix(suffix)

    @property
    def param_value(self):
        value, (min, max), digits, unit, scale = self.parameter.raw_value
        return value

    def set_param_value(self, value):
        if value != self.param_value:
            self.parameter.set_value(value)
            self.gui_parameter_changed()

    def remote_parameter_changed(self, raw_value):
        self.parameter.set_raw_value(raw_value)
        self.blockSignals(True)
        self._set_GUI_values()
        self.blockSignals(False)


class IntLineEdit(QtWidgets.QSpinBox, ParameterLineEdit):
    def __init__(self, client, collection, name, parameter):
        ParameterLineEdit.__init__(self, client, collection, name, parameter)
        QtWidgets.QSpinBox.__init__(self)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setKeyboardTracking(False)
        self.setValue(self.param_value)
        self.setMinimum(-2147483648)
        self.setMaximum(2147483647)
        self.valueChanged.connect(self.set_param_value)
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignVCenter)
        self.setLayout(layout)

    @property
    def param_value(self):
        return self.parameter.parsed_value

    def set_param_value(self, value):
        if value != self.param_value:
            self.parameter.set_value(value)
            self.gui_parameter_changed()

    def remote_parameter_changed(self, raw_value):
        self.parameter.set_raw_value(raw_value)
        self.blockSignals(True)
        self.setValue(self.param_value)
        self.blockSignals(False)


class SelectionLineEdit(QtWidgets.QComboBox, ParameterLineEdit):
    def __init__(self, client, collection, name, parameter):
        ParameterLineEdit.__init__(self, client, collection, name, parameter)
        QtWidgets.QComboBox.__init__(self)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setSizeAdjustPolicy(self.AdjustToMinimumContentsLength)
        self.setFrame(False)
        self._set_GUI_values()
        self.currentIndexChanged.connect(self.set_param_selected)

    def _set_GUI_values(self):
        selected, selections = self.parameter.raw_value
        selected_idx = 0
        self.clear()
        for kk, selection in enumerate(selections):
            if selected == selection:
                selected_idx = kk
            self.addItem(selection)
        self.setCurrentIndex(selected_idx)

    @property
    def param_value(self):
        return self.parameter.parsed_value

    def set_param_selected(self, idx):
        value = self.currentText()
        if value != self.param_value:
            self.parameter.set_selected(value)
            self.gui_parameter_changed()

    def remote_parameter_changed(self, raw_value):
        self.parameter.set_raw_value(raw_value)
        self.blockSignals(True)
        self._set_GUI_values()
        self.blockSignals(False)


class ScanLineEdit(ParameterLineEdit):
    def __init__(self, client, collection, name, parameter):
        ParameterLineEdit.__init__(self, client, collection, name, parameter)
        QtWidgets.QWidget.__init__(self)
        self._set_GUI()

    def _set_double_spinbox(self, spinbox, digits, unit):
        spinbox.setDecimals(digits)
        spinbox.setKeyboardTracking(False)
        spinbox.setSingleStep(10**(-digits))
        if unit != "":
            suffix = " " + unit
        else:
            suffix = ""
        suffix = suffix.replace("u", "\u00B5")
        spinbox.setSuffix(suffix)

    def _set_GUI(self):
        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        label = QtWidgets.QLabel("Start")
        label.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                            QtWidgets.QSizePolicy.Fixed)
        layout.addWidget(label, 0, 0)
        self.start = QtWidgets.QDoubleSpinBox()
        self.start.valueChanged.connect(self.set_param_start)
        self.start.wheelEvent = lambda event: None
        layout.addWidget(self.start, 1, 0)

        label = QtWidgets.QLabel("Stop")
        label.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                            QtWidgets.QSizePolicy.Fixed)
        layout.addWidget(label, 0, 1)
        self.stop = QtWidgets.QDoubleSpinBox()
        self.stop.valueChanged.connect(self.set_param_stop)
        self.stop.wheelEvent = lambda event: None
        layout.addWidget(self.stop, 1, 1)

        label = QtWidgets.QLabel("Center")
        label.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                            QtWidgets.QSizePolicy.Fixed)
        layout.addWidget(label, 2, 0)
        self.center = QtWidgets.QDoubleSpinBox()
        self.center.valueChanged.connect(self.set_param_center)
        self.center.wheelEvent = lambda event: None
        layout.addWidget(self.center, 3, 0)

        label = QtWidgets.QLabel("Span")
        label.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                            QtWidgets.QSizePolicy.Fixed)
        layout.addWidget(label, 2, 1)
        self.span = QtWidgets.QDoubleSpinBox()
        self.span.valueChanged.connect(self.set_param_span)
        self.span.wheelEvent = lambda event: None
        layout.addWidget(self.span, 3, 1)

        label = QtWidgets.QLabel("Resolution")
        label.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                            QtWidgets.QSizePolicy.Fixed)
        layout.addWidget(label, 0, 2)
        self.resolution = QtWidgets.QDoubleSpinBox()
        self.resolution.valueChanged.connect(self.set_param_resolution)
        self.resolution.wheelEvent = lambda event: None
        layout.addWidget(self.resolution, 1, 2)

        label = QtWidgets.QLabel("Steps")
        label.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                            QtWidgets.QSizePolicy.Fixed)
        layout.addWidget(label, 0, 3)
        self.steps = QtWidgets.QSpinBox()
        self.steps.valueChanged.connect(self.set_param_steps)
        self.steps.wheelEvent = lambda event: None
        layout.addWidget(self.steps, 1, 3)

        self.random = QtWidgets.QCheckBox("Randomize")
        self.random.stateChanged.connect(self.set_param_random)
        layout.addWidget(self.random, 3, 2, 1, 2)

        self._set_GUI_values()

    def _set_GUI_values(self):
        (start, stop, steps), (min, max), random, digits, unit, scale = self.parameter.raw_value

        self.start.setValue(start)
        self.start.setMinimum(min)
        self.start.setMaximum(max)
        self._set_double_spinbox(self.start, digits, unit)

        self.stop.setValue(stop)
        self.stop.setMinimum(min)
        self.stop.setMaximum(max)
        self._set_double_spinbox(self.stop, digits, unit)

        self.center.setValue((start + stop) / 2.)
        self.center.setMinimum(min)
        self.center.setMaximum(max)
        self._set_double_spinbox(self.center, digits, unit)

        self.span.setValue(abs(stop - start))
        self.span.setMinimum(min - max)
        self.span.setMaximum(max - min)
        self._set_double_spinbox(self.span, digits, unit)

        self.resolution.setValue(abs(stop - start) / (steps - 1))
        self.resolution.setMinimum(0.)
        self.resolution.setMaximum(max - min)
        self._set_double_spinbox(self.resolution, digits, unit)

        self.steps.setValue(steps)
        self.steps.setKeyboardTracking(False)
        self.steps.setMinimum(2)
        self.steps.setMaximum(1000000)

        if random:
            self.random.setCheckState(QtCore.Qt.Checked)
        else:
            self.random.setCheckState(QtCore.Qt.Unchecked)

    def set_param_start(self, value):
        (start, stop, steps), (min, max), random, digits, unit, scale = self.parameter.raw_value
        if value != start:
            self.parameter.set_start(value)
            self.gui_parameter_changed()
            self.remote_parameter_changed(self.parameter.raw_value)

    def set_param_stop(self, value):
        (start, stop, steps), (min, max), random, digits, unit, scale = self.parameter.raw_value
        if value != stop:
            self.parameter.set_stop(value)
            self.gui_parameter_changed()
            self.remote_parameter_changed(self.parameter.raw_value)

    def set_param_center(self, value):
        (start, stop, steps), (min, max), random, digits, unit, scale = self.parameter.raw_value
        span = self.span.value()
        new_start = value - span / 2.
        if new_start < min:
            new_start = min
        elif new_start > max:
            new_start = max
        new_stop = value + span / 2.
        if new_stop < min:
            new_stop = min
        elif new_stop > max:
            new_stop = max
        if new_start != start or new_stop != stop:
            self.parameter.set_start(new_start)
            self.parameter.set_stop(new_stop)
            self.gui_parameter_changed()
            self.remote_parameter_changed(self.parameter.raw_value)

    def set_param_span(self, value):
        (start, stop, steps), (min, max), random, digits, unit, scale = self.parameter.raw_value
        center = self.center.value()
        new_start = center - value / 2.
        if new_start < min:
            new_start = min
        elif new_start > max:
            new_start = max
        new_stop = center + value / 2.
        if new_stop < min:
            new_stop = min
        elif new_stop > max:
            new_stop = max
        if new_start != start or new_stop != stop:
            self.parameter.set_start(new_start)
            self.parameter.set_stop(new_stop)
            self.gui_parameter_changed()
            self.remote_parameter_changed(self.parameter.raw_value)

    def set_param_resolution(self, value):
        (start, stop, steps), (min, max), random, digits, unit, scale = self.parameter.raw_value
        if value > abs(stop - start):
            value = abs(stop - start)
        if value == 0:
            value = 10**(-digits)
        new_steps = int(abs((stop - start) / value)) + 1
        if new_steps < 2:
            new_steps = 2
        if new_steps != steps:
            self.parameter.set_steps(new_steps)
            self.gui_parameter_changed()
            self.remote_parameter_changed(self.parameter.raw_value)

    def set_param_steps(self, value):
        (start, stop, steps), (min, max), random, digits, unit, scale = self.parameter.raw_value
        if value != steps:
            self.parameter.set_steps(value)
            self.gui_parameter_changed()
            self.remote_parameter_changed(self.parameter.raw_value)

    def set_param_random(self, value):
        (start, stop, steps), (min, max), random, digits, unit, scale = self.parameter.raw_value
        if value != random:
            self.parameter.set_random(value == QtCore.Qt.Checked)
            self.gui_parameter_changed()
            self.remote_parameter_changed(self.parameter.raw_value)

    def remote_parameter_changed(self, raw_value):
        self.parameter.set_raw_value(raw_value)
        self.start.blockSignals(True)
        self.stop.blockSignals(True)
        self.center.blockSignals(True)
        self.span.blockSignals(True)
        self.resolution.blockSignals(True)
        self.steps.blockSignals(True)
        self.random.blockSignals(True)
        self._set_GUI_values()
        self.start.blockSignals(False)
        self.stop.blockSignals(False)
        self.center.blockSignals(False)
        self.span.blockSignals(False)
        self.resolution.blockSignals(False)
        self.steps.blockSignals(False)
        self.random.blockSignals(False)


class NicknameSelectionLineEdit(QtWidgets.QComboBox, ParameterLineEdit):
    def __init__(self, client, collection, name, parameter):
        ParameterLineEdit.__init__(self, client, collection, name, parameter)
        QtWidgets.QComboBox.__init__(self)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setSizeAdjustPolicy(self.AdjustToMinimumContentsLength)
        self.setFrame(False)
        self._set_GUI_values()
        self.currentIndexChanged.connect(self.set_param_selected)

    def _set_GUI_values(self):
        selected, selections = self.parameter.raw_value
        selected_idx = 0
        self.clear()
        for kk, (nickname, data) in enumerate(selections):
            if selected == nickname:
                selected_idx = kk
            self.addItem(nickname)
        self.setCurrentIndex(selected_idx)

    @property
    def param_value(self):
        return self.parameter.raw_value[0]

    def set_param_selected(self, idx):
        value = self.currentText()
        if value != self.param_value:
            self.parameter.set_selected(value)
            self.gui_parameter_changed()

    def remote_parameter_changed(self, raw_value):
        self.parameter.set_raw_value(raw_value)
        self.blockSignals(True)
        self._set_GUI_values()
        self.blockSignals(False)


class ListLineEdit(QtWidgets.QLineEdit, ParameterLineEdit):
    def __init__(self, client, collection, name, parameter):
        ParameterLineEdit.__init__(self, client, collection, name, parameter)
        QtWidgets.QLineEdit.__init__(self)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setText(self.param_text)
        self.editingFinished.connect(self.set_param_text)
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignVCenter)
        self.setLayout(layout)

    @property
    def param_text(self):
        return str(self.parameter.parsed_value)

    def set_param_text(self):
        text = self.text()
        if text != self.param_text:
            self.parameter.set_raw_value(eval(text))
            self.gui_parameter_changed()

    def remote_parameter_changed(self, raw_value):
        self.parameter.set_raw_value(raw_value)
        self.blockSignals(True)
        self.setText(self.param_text)
        self.blockSignals(False)


_type_to_class = {
    "bool": BoolLineEdit,
    "string": StringLineEdit,
    "float": FloatLineEdit,
    "int": IntLineEdit,
    "selection": SelectionLineEdit,
    "scan": ScanLineEdit,
    "nickname_selection": NicknameSelectionLineEdit,
    "list": ListLineEdit
}
