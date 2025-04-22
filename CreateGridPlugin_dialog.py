from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QMessageBox

from PyQt5 import uic
from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QFileDialog, QMessageBox
)
from qgis.core import QgsProject
import os


from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QMessageBox
from PyQt5 import uic
from qgis.core import QgsProject
import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'CreateGridPlugin_dialog_base.ui'))

class CreateGridPluginDialog(QDialog, FORM_CLASS):
    def __init__(self, plugin, parent=None):
        super(CreateGridPluginDialog, self).__init__(parent)
        self.setupUi(self)
        self.plugin = plugin  # Store the plugin reference

        # Populate layers in both combo boxes
        self.populate_layers()

        # Connect signals for layer selection changes
        self.existingGridLayerComboBox.currentIndexChanged.connect(self.populate_fields)

        # OK / Cancel
        self.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(self.ok_button_clicked)
        self.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.reject)

        # Connect the browse button
        self.browseButton.clicked.connect(self.browse_output_path)

    def populate_layers(self):
        """
        Populate the layer combo boxes with polygon layers.
        - layerComboBox: For selecting the boundary polygon layer.
        - existingGridLayerComboBox: For selecting an existing grid layer.
        """
        layers = QgsProject.instance().mapLayers().values()
        for layer in layers:
            if layer.type() == layer.VectorLayer and layer.geometryType() == 2:  # Polygon layers
                self.layerComboBox.addItem(layer.name())
                self.existingGridLayerComboBox.addItem(layer.name())

        # Populate fields for the initially selected existing grid layer
        self.populate_fields()

    def populate_fields(self):
        """
        Populate the existingGridLayerComboBox_2 with field names from the selected existing grid layer.
        """
        self.existingGridLayerComboBox_2.clear()  # Clear the existing items

        # Get the selected layer name
        layer_name = self.existingGridLayerComboBox.currentText()
        if not layer_name:
            return

        # Find the layer in the project
        layer = QgsProject.instance().mapLayersByName(layer_name)
        if not layer:
            return
        layer = layer[0]  # Get the first layer matching the name

        # Populate the combo box with field names
        fields = layer.fields()
        for field in fields:
            self.existingGridLayerComboBox_2.addItem(field.name())

    def browse_output_path(self):
        """Open a file dialog to pick the output text file path."""
        # Default file name
        default_name = os.path.join(os.path.expanduser("~"), "grid_output.txt")

        file_path, _ = QFileDialog.getSaveFileName(self, "Save as text", default_name, "Text Files (*.txt)")
        if file_path:
            self.outPathLineEdit.setText(file_path)

    def ok_button_clicked_1(self):
        self.accept()

    def ok_button_clicked(self):
        """Handle OK button click without closing the dialog."""
        # Disable the button to prevent further clicks during processing
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
        self.progressBar.setValue(0)  # Reset progress bar

        # Call the plugin's task handler
        self.plugin.handle_task()
        

    def get_length(self):
        """Return length as a float."""
        try:
            return float(self.lengthlineEdit.text())
        except ValueError:
            return 0.0  # Default to 0 if invalid

    def get_width(self):
        """Return width as a float."""
        try:
            return float(self.widthlineEdit.text())
        except ValueError:
            return 0.0  # Default to 0 if invalid

    def get_out_path(self):
        """Return the chosen path for saving the text file."""
        return self.outPathLineEdit.text().strip()

    def get_selected_layer(self):
        """Return the selected layer name for creating a new grid."""
        return self.layerComboBox.currentText()

    def get_existing_grid_layer(self):
        """Return the selected existing grid layer name."""
        return self.existingGridLayerComboBox.currentText()

    def get_existing_grid_field(self):
        """Return the selected field name for the existing grid."""
        return self.existingGridLayerComboBox_2.currentText()
