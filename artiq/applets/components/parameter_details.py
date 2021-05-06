from PyQt5 import QtWidgets, QtGui, QtCore
from artiq.gui.tools import LayoutWidget

_type_to_class = {}  # placeholder


class ParameterDetails(QtWidgets.QDialog):
    @classmethod
    def from_parameter(cls, client, collection, name, parameter):
        _type = parameter.type
        return _type_to_class[_type](client, collection, name, parameter)

    def __init__(self, client, collection, name, parameter):
        super().__init__(
            client,
            QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.WindowTitleHint \
            | QtCore.Qt.WindowCloseButtonHint)
        self.setWindowTitle(collection + "." + name)
        self.client = client
        self.collection = collection
        self.name = name
        self.parameter = parameter

    def gui_parameter_changed(self):
        self.client.connect()
        self.client.cxn.parameter_database.set_raw_value(
            self.collection, self.name, self.parameter.raw_value)
        lineedit = self.client.param_lineedits[self.collection][self.name]
        lineedit.remote_parameter_changed(self.parameter.raw_value)


class FloatDetails(ParameterDetails):
    def __init__(self, client, collection, name, parameter):
        ParameterDetails.__init__(self, client, collection, name, parameter)
        self._make_GUI()
        self._set_GUI_values()

    def _make_GUI(self):
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        labelfont = QtGui.QFont('Arial', 10)
        spinboxfont = QtGui.QFont('Arial', 12)

        label = QtWidgets.QLabel("Minimum")
        label.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                            QtWidgets.QSizePolicy.Fixed)
        label.setFont(labelfont)
        grid.addWidget(label, 0, 0)

        self.min = QtWidgets.QDoubleSpinBox()
        self.min.setMinimum(-1e12)
        self.min.setMaximum(1e12)
        self.min.setFont(spinboxfont)
        self.min.setKeyboardTracking(False)
        grid.addWidget(self.min, 1, 0)

        label = QtWidgets.QLabel("Maximum")
        label.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                            QtWidgets.QSizePolicy.Fixed)
        label.setFont(labelfont)
        grid.addWidget(label, 0, 1)

        self.max = QtWidgets.QDoubleSpinBox()
        self.max.setMinimum(-1e12)
        self.max.setMaximum(1e12)
        self.max.setFont(spinboxfont)
        self.max.setKeyboardTracking(False)
        grid.addWidget(self.max, 1, 1)

        label = QtWidgets.QLabel("Digits")
        label.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                            QtWidgets.QSizePolicy.Fixed)
        label.setFont(labelfont)
        grid.addWidget(label, 0, 2)

        self.digits = QtWidgets.QSpinBox()
        self.digits.setMinimum(0)
        self.digits.setMaximum(12)
        self.digits.setFont(spinboxfont)
        self.digits.setKeyboardTracking(False)
        grid.addWidget(self.digits, 1, 2)

        label = QtWidgets.QLabel("Unit")
        label.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                            QtWidgets.QSizePolicy.Fixed)
        label.setFont(labelfont)
        grid.addWidget(label, 2, 0)

        self.unit = QtWidgets.QLineEdit()
        self.unit.setFont(spinboxfont)
        grid.addWidget(self.unit, 3, 0)

        label = QtWidgets.QLabel("Scale")
        label.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                            QtWidgets.QSizePolicy.Fixed)
        label.setFont(labelfont)
        grid.addWidget(label, 2, 1)

        self.scale = QtWidgets.QDoubleSpinBox()
        self.scale.setMinimum(-1e12)
        self.scale.setMaximum(1e12)
        self.scale.setDecimals(12)
        self.scale.setFont(spinboxfont)
        self.scale.setKeyboardTracking(False)
        grid.addWidget(self.scale, 3, 1)

    def _set_GUI_values(self):
        value, (min, max), digits, unit, scale = self.parameter.raw_value
        if unit != "":
            suffix = " " + unit
        else:
            suffix = ""
        suffix = suffix.replace("u", "\u00B5")

        self.min.setValue(min)
        self.min.setDecimals(digits)
        self.min.setSuffix(suffix)
        self.max.setValue(max)
        self.max.setDecimals(digits)
        self.max.setSuffix(suffix)
        self.digits.setValue(digits)
        self.unit.setText(unit)
        self.scale.setValue(scale)
        self.min.valueChanged.connect(self.set_min)
        self.max.valueChanged.connect(self.set_max)
        self.digits.valueChanged.connect(self.set_digits)
        self.unit.editingFinished.connect(self.set_unit)
        self.scale.valueChanged.connect(self.set_scale)

    def set_min(self, min):
        self.parameter.set_min(min)
        self.gui_parameter_changed()

    def set_max(self, max):
        self.parameter.set_max(max)
        self.gui_parameter_changed()

    def set_digits(self, digits):
        self.parameter.set_digits(digits)
        self.gui_parameter_changed()

    def set_unit(self):
        self.parameter.set_unit_and_scale(self.unit.text(), self.scale.value())
        self.gui_parameter_changed()

    def set_scale(self, scale):
        self.parameter.set_unit_and_scale(self.unit.text(), scale)
        self.gui_parameter_changed()


class ScanDetails(ParameterDetails):
    def __init__(self, client, collection, name, parameter):
        ParameterDetails.__init__(self, client, collection, name, parameter)
        self._make_GUI()
        self._set_GUI_values()

    def _make_GUI(self):
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        labelfont = QtGui.QFont('Arial', 10)
        spinboxfont = QtGui.QFont('Arial', 12)

        label = QtWidgets.QLabel("Minimum")
        label.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                            QtWidgets.QSizePolicy.Fixed)
        label.setFont(labelfont)
        grid.addWidget(label, 0, 0)

        self.min = QtWidgets.QDoubleSpinBox()
        self.min.setMinimum(-1e12)
        self.min.setMaximum(1e12)
        self.min.setFont(spinboxfont)
        self.min.setKeyboardTracking(False)
        grid.addWidget(self.min, 1, 0)

        label = QtWidgets.QLabel("Maximum")
        label.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                            QtWidgets.QSizePolicy.Fixed)
        label.setFont(labelfont)
        grid.addWidget(label, 0, 1)

        self.max = QtWidgets.QDoubleSpinBox()
        self.max.setMinimum(-1e12)
        self.max.setMaximum(1e12)
        self.max.setFont(spinboxfont)
        self.max.setKeyboardTracking(False)
        grid.addWidget(self.max, 1, 1)

        label = QtWidgets.QLabel("Digits")
        label.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                            QtWidgets.QSizePolicy.Fixed)
        label.setFont(labelfont)
        grid.addWidget(label, 0, 2)

        self.digits = QtWidgets.QSpinBox()
        self.digits.setMinimum(0)
        self.digits.setMaximum(12)
        self.digits.setFont(spinboxfont)
        self.digits.setKeyboardTracking(False)
        grid.addWidget(self.digits, 1, 2)

        label = QtWidgets.QLabel("Unit")
        label.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                            QtWidgets.QSizePolicy.Fixed)
        label.setFont(labelfont)
        grid.addWidget(label, 2, 0)

        self.unit = QtWidgets.QLineEdit()
        self.unit.setFont(spinboxfont)
        grid.addWidget(self.unit, 3, 0)

        label = QtWidgets.QLabel("Scale")
        label.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                            QtWidgets.QSizePolicy.Fixed)
        label.setFont(labelfont)
        grid.addWidget(label, 2, 1)

        self.scale = QtWidgets.QDoubleSpinBox()
        self.scale.setMinimum(-1e12)
        self.scale.setMaximum(1e12)
        self.scale.setDecimals(12)
        self.scale.setFont(spinboxfont)
        self.scale.setKeyboardTracking(False)
        grid.addWidget(self.scale, 3, 1)

    def _set_GUI_values(self):
        (start, stop, steps), (min, max), random, digits, unit, scale = self.parameter.raw_value
        if unit != "":
            suffix = " " + unit
        else:
            suffix = ""
        suffix = suffix.replace("u", "\u00B5")

        self.min.setValue(min)
        self.min.setDecimals(digits)
        self.min.setSuffix(suffix)
        self.max.setValue(max)
        self.max.setDecimals(digits)
        self.max.setSuffix(suffix)
        self.digits.setValue(digits)
        self.unit.setText(unit)
        self.scale.setValue(scale)
        self.min.valueChanged.connect(self.set_min)
        self.max.valueChanged.connect(self.set_max)
        self.digits.valueChanged.connect(self.set_digits)
        self.unit.editingFinished.connect(self.set_unit)
        self.scale.valueChanged.connect(self.set_scale)

    def set_min(self, min):
        self.parameter.set_min(min)
        self.gui_parameter_changed()

    def set_max(self, max):
        self.parameter.set_max(max)
        self.gui_parameter_changed()

    def set_digits(self, digits):
        self.parameter.set_digits(digits)
        self.gui_parameter_changed()

    def set_unit(self):
        self.parameter.set_unit_and_scale(self.unit.text(), self.scale.value())
        self.gui_parameter_changed()

    def set_scale(self, scale):
        self.parameter.set_unit_and_scale(self.unit.text(), scale)
        self.gui_parameter_changed()


_type_to_class = {
    "float": FloatDetails,
    #"selection": SelectionDetails,
    "scan": ScanDetails,
    #"nickname_selection": NicknameSelectionDetails,
    #"list": ListDetails
}
