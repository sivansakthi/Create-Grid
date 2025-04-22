import os
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAction, QDialog, QMessageBox, QDialogButtonBox  # Import QDialogButtonBox
from qgis.core import (
    QgsProject,
    QgsFeature,
    QgsGeometry,
    QgsField,
    QgsVectorLayer,
    QgsPointXY,
)
from qgis.PyQt.QtCore import QVariant
from PyQt5.QtGui import QIcon

from .CreateGridPlugin_dialog import CreateGridPluginDialog


class CreateGridPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.dialog = None
        self.actions = []
        self.menu = "&Create Grid"

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None,
    ):
        existing_action = next((a for a in self.actions if a.text() == text), None)
        if existing_action:
            return existing_action

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)
        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)
        return action

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, "icon.png")
        if os.path.exists(icon_path):
            self.add_action(icon_path, "Create Grid", self.run)

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)
        self.actions = []

    def run_2(self):
        if not self.dialog:
            self.dialog = CreateGridPluginDialog(self, self.iface.mainWindow())  # Pass iface.mainWindow() as the parent
        result = self.dialog.exec_()
        if result == QDialog.Accepted:
            pass  # The task will now be handled inside the dialog

    def run(self):
        if self.dialog and self.dialog.isVisible():
            self.dialog.raise_()
            self.dialog.activateWindow()
            return

        if not self.dialog:
            self.dialog = CreateGridPluginDialog(self, self.iface.mainWindow())  # Pass iface.mainWindow() as the parent
        self.dialog.show()
        

    def run_1(self):
        if not self.dialog:
            self.dialog = CreateGridPluginDialog()
        result = self.dialog.exec_()
        if result == QDialog.Accepted:
            self.handle_task()

    def handle_task(self):
        try:
            # Reset the progress bar
            self.dialog.progressBar.setValue(0)
            
            out_path = self.dialog.get_out_path()

            # Validate output path
            if not out_path or not os.path.isdir(os.path.dirname(out_path)):
                QMessageBox.warning(None, "Invalid Output Path", "Please provide a valid output file path.")
                return

            if self.dialog.radioButtonAddAdjacency.isChecked():
                # Update adjacency fields in an existing grid layer
                existing_grid_layer_name = self.dialog.get_existing_grid_layer()
                grid_field_name = self.dialog.get_existing_grid_field()

                if not existing_grid_layer_name or not grid_field_name:
                    QMessageBox.warning(None, "Update Grid", "Please select a valid layer and field.")
                    return

                grid_layers = QgsProject.instance().mapLayersByName(existing_grid_layer_name)
                if not grid_layers:
                    QMessageBox.warning(None, "Update Grid", f"Layer '{existing_grid_layer_name}' not found.")
                    return

                grid_layer = grid_layers[0]
                self.assign_adjacency_from_existing_layer(grid_layer, grid_field_name, out_path)
                QMessageBox.information(None, "Task Completed", "Adjacency updated successfully and report saved.")
            else:
                # Create a new grid as a memory layer
                selected_layer_name = self.dialog.get_selected_layer()
                length = self.dialog.get_length()
                width = self.dialog.get_width()

                if not selected_layer_name or length <= 0 or width <= 0:
                    QMessageBox.warning(None, "Create Grid", "Please provide valid inputs.")
                    return

                self.create_new_grid(selected_layer_name, length, width, out_path)
                QMessageBox.information(None, "Task Completed", "New grid created successfully and report saved.")
        finally:
            # Re-enable the OK button and ensure progress bar is at 100%
            self.dialog.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)
            self.dialog.progressBar.setValue(100)


            

    def handle_task_1(self):
        # Reset the progress bar
        self.dialog.progressBar.setValue(0)
        
        out_path = self.dialog.get_out_path()

        # Validate output path
        if not out_path or not os.path.isdir(os.path.dirname(out_path)):
            QMessageBox.warning(None, "Invalid Output Path", "Please provide a valid output file path.")
            return

        if self.dialog.radioButtonAddAdjacency.isChecked():
            # Update adjacency fields in an existing grid layer
            existing_grid_layer_name = self.dialog.get_existing_grid_layer()
            grid_field_name = self.dialog.get_existing_grid_field()

            if not existing_grid_layer_name or not grid_field_name:
                QMessageBox.warning(None, "Update Grid", "Please select a valid layer and field.")
                return

            grid_layers = QgsProject.instance().mapLayersByName(existing_grid_layer_name)
            if not grid_layers:
                QMessageBox.warning(None, "Update Grid", f"Layer '{existing_grid_layer_name}' not found.")
                return

            grid_layer = grid_layers[0]
            self.assign_adjacency_from_existing_layer(grid_layer, grid_field_name, out_path)
            #self.dialog.progressBar.setValue(100)  # Task completed
            QMessageBox.information(None, "Task Completed", "Adjacency updated successfully and report saved.")
        else:
            # Create a new grid as a memory layer
            selected_layer_name = self.dialog.get_selected_layer()
            length = self.dialog.get_length()
            width = self.dialog.get_width()

            if not selected_layer_name or length <= 0 or width <= 0:
                QMessageBox.warning(None, "Create Grid", "Please provide valid inputs.")
                return

            self.create_new_grid(selected_layer_name, length, width, out_path)
            QMessageBox.information(None, "Task Completed", "New grid created successfully and report saved.")


    def assign_adjacency_from_existing_layer(self, grid_layer, grid_field_name, out_path):
        """
        Assign adjacency attributes to an existing grid layer and save the result to a text file.
        """
        print("\nStarting adjacency assignment for existing layer...\n")

        adjacency_fields = [
            "Left", "Top_Left", "Top", "Top_Right",
            "Right", "Bottom_Right", "Bottom", "Bottom_Left"
        ]

        existing_fields = [field.name() for field in grid_layer.fields()]
        missing_fields = [field for field in adjacency_fields if field not in existing_fields]
        if missing_fields:
            print(f"Adding missing fields: {missing_fields}")
            grid_layer.dataProvider().addAttributes([QgsField(field, QVariant.String) for field in missing_fields])
            grid_layer.updateFields()

        features = {feat[grid_field_name]: feat for feat in grid_layer.getFeatures()}
        print(f"Total features in grid_layer: {len(features)}\n")

        grid_layer.startEditing()

        total_features = len(features)
        processed_features = 0

        for feature in grid_layer.getFeatures():
            grid_no = feature[grid_field_name]
            print(f"Processing feature with {grid_field_name}: {grid_no}")

            row, col = self.parse_grid_label(grid_no)
            print(f"Row: {row}, Column: {col}")

            neighbors = {
                "Left": self.generate_grid_label(row, col - 1),
                "Top_Left": self.generate_grid_label(row - 1, col - 1),
                "Top": self.generate_grid_label(row - 1, col),
                "Top_Right": self.generate_grid_label(row - 1, col + 1),
                "Right": self.generate_grid_label(row, col + 1),
                "Bottom_Right": self.generate_grid_label(row + 1, col + 1),
                "Bottom": self.generate_grid_label(row + 1, col),
                "Bottom_Left": self.generate_grid_label(row + 1, col - 1),
            }

            updated_attrs = {}
            for field, neighbor in neighbors.items():
                if neighbor in features:
                    updated_attrs[field] = features[neighbor][grid_field_name]
                else:
                    updated_attrs[field] = ""

            for field, value in updated_attrs.items():
                if field in feature.fields().names():
                    feature.setAttribute(field, value)

            grid_layer.updateFeature(feature)

            processed_features += 1
            progress = int((processed_features / total_features) * 100)
            self.dialog.progressBar.setValue(progress)

        grid_layer.commitChanges()
        grid_layer.triggerRepaint()

        if out_path:
            self.export_grid_to_txt(grid_layer, out_path, grid_field_name)

        print("\nAdjacency assignment for existing layer completed.\n")
        self.dialog.progressBar.setValue(100)





    def assign_adjacency_from_existing_layer_1(self, grid_layer, grid_field_name, out_path):
        """
        Assign adjacency attributes to an existing grid layer and save the result to a text file.
        """
        print("\nStarting adjacency assignment for existing layer...\n")

        # Required adjacency fields
        adjacency_fields = [
            "Left", "Top_Left", "Top", "Top_Right",
            "Right", "Bottom_Right", "Bottom", "Bottom_Left"
        ]

        # Check and add missing adjacency fields
        existing_fields = [field.name() for field in grid_layer.fields()]
        missing_fields = [field for field in adjacency_fields if field not in existing_fields]
        if missing_fields:
            print(f"Adding missing fields: {missing_fields}")
            grid_layer.dataProvider().addAttributes([QgsField(field, QVariant.String) for field in missing_fields])
            grid_layer.updateFields()

        # Create a dictionary to map grid_field_name values to features
        features = {feat[grid_field_name]: feat for feat in grid_layer.getFeatures()}
        print(f"Total features in grid_layer: {len(features)}\n")

        # Start an editing session
        grid_layer.startEditing()

        total_features = len(features)
        processed_features = 0

        for feature in grid_layer.getFeatures():
            grid_no = feature[grid_field_name]
            print(f"Processing feature with {grid_field_name}: {grid_no}")

            # Parse grid label to row and column
            row, col = self.parse_grid_label(grid_no)
            print(f"Row: {row}, Column: {col}")

            # Determine adjacent grid numbers
            neighbors = {
                "Left": self.generate_grid_label(row, col - 1),
                "Top_Left": self.generate_grid_label(row - 1, col - 1),
                "Top": self.generate_grid_label(row - 1, col),
                "Top_Right": self.generate_grid_label(row - 1, col + 1),
                "Right": self.generate_grid_label(row, col + 1),
                "Bottom_Right": self.generate_grid_label(row + 1, col + 1),
                "Bottom": self.generate_grid_label(row + 1, col),
                "Bottom_Left": self.generate_grid_label(row + 1, col - 1),
            }

            # Update feature attributes with neighbor grid numbers
            updated_attrs = {}
            for field, neighbor in neighbors.items():
                if neighbor in features:
                    updated_attrs[field] = features[neighbor][grid_field_name]
                else:
                    updated_attrs[field] = ""  # Use an empty string for missing neighbors

            # Apply the updates to the feature
            for field, value in updated_attrs.items():
                if field in feature.fields().names():
                    feature.setAttribute(field, value)

            grid_layer.updateFeature(feature)

            # Update progress bar
            processed_features += 1
            progress = int((processed_features / total_features) * 100)
            self.dialog.progressBar.setValue(progress)

        # Commit changes
        grid_layer.commitChanges()
        grid_layer.triggerRepaint()

        # Export adjacency results to a text file
        self.export_grid_to_txt(grid_layer, out_path, grid_field_name)
        print("\nAdjacency assignment for existing layer completed.\n")
        self.dialog.progressBar.setValue(100)  # Ensure progress bar is set to 100% at the end


    def create_new_grid(self, layer_name, length, width, out_path):
        boundary_layers = QgsProject.instance().mapLayersByName(layer_name)
        if not boundary_layers:
            QMessageBox.warning(None, "Create Grid", f"Layer '{layer_name}' not found.")
            return
        boundary_layer = boundary_layers[0]

        crs = boundary_layer.crs()
        grid_layer = QgsVectorLayer("Polygon?crs=" + crs.authid(), "Generated Grid", "memory")
        if not grid_layer.isValid():
            QMessageBox.warning(None, "Create Grid", "Failed to create memory layer.")
            return

        provider = grid_layer.dataProvider()
        provider.addAttributes([
            QgsField("GridNo", QVariant.String),
            QgsField("Left", QVariant.String),
            QgsField("Top_Left", QVariant.String),
            QgsField("Top", QVariant.String),
            QgsField("Top_Right", QVariant.String),
            QgsField("Right", QVariant.String),
            QgsField("Bottom_Right", QVariant.String),
            QgsField("Bottom", QVariant.String),
            QgsField("Bottom_Left", QVariant.String),
        ])
        grid_layer.updateFields()

        self.generate_grid(boundary_layer, grid_layer, length, width)
        QgsProject.instance().addMapLayer(grid_layer)
        self.export_grid_to_txt(grid_layer, out_path)
        QMessageBox.information(None, "Create Grid", "Grid created successfully and saved to file.")

    def generate_grid(self, boundary_layer, grid_layer, length, width):
        features = []
        provider = grid_layer.dataProvider()

        xmin, ymin, xmax, ymax = boundary_layer.extent().toRectF().getCoords()
        x_start, y_start = xmin, ymax
        row_number = 0

        total_rows = int((ymax - ymin) // length) + 1
        total_progress_steps = total_rows  # Adjust if needed
        

        while y_start > ymin:
            col_number = 0
            x_pos = x_start

            while x_pos < xmax:
                points = [
                    QgsPointXY(x_pos, y_start),
                    QgsPointXY(x_pos + width, y_start),
                    QgsPointXY(x_pos + width, y_start - length),
                    QgsPointXY(x_pos, y_start - length),
                    QgsPointXY(x_pos, y_start),
                ]
                grid_geom = QgsGeometry.fromPolygonXY([points])
                grid_label = f"{chr(65 + row_number)}{col_number + 1}"
                feature = QgsFeature(grid_layer.fields())
                feature.setGeometry(grid_geom)
                feature.setAttribute("GridNo", grid_label)
                features.append(feature)
                x_pos += width
                col_number += 1

            y_start -= length
            row_number += 1

            # Update progress bar
            progress = int((row_number / total_progress_steps) * 100)
            self.dialog.progressBar.setValue(progress)
            

        provider.addFeatures(features)
        self.assign_adjacency_from_existing_layer(grid_layer, "GridNo", None)

    def parse_grid_label_1(self, grid_label):
        row = ord(grid_label[0].upper()) - ord("A")
        col = int(grid_label[1:]) - 1
        return row, col

    def parse_grid_label_2(self, grid_label):
        """
        Parse a grid label (e.g., 'AA1') into row and column indices.
        """
        import re

        match = re.match(r"([A-Z]+)(\d+)", grid_label)
        if not match:
            return -1, -1

        col_label, row_label = match.groups()
        col = 0
        for char in col_label:
            col = col * 26 + (ord(char.upper()) - ord("A") + 1)
        col -= 1  # Convert to 0-based index

        row = int(row_label) - 1  # Convert to 0-based index
        return row, col

    def parse_grid_label(self, grid_label):
        """
        Parse a grid label (e.g., 'A1', 'AA2') into row and column indices.
        Handles cases where either alphabetic or numeric parts are missing.
        """
        # Remove any invalid characters (non-alphabetic and non-numeric)
        grid_label = ''.join(filter(lambda x: x.isalnum(), grid_label))

        # Separate the alphabetic and numeric parts of the label
        alpha_part = ''.join(filter(str.isalpha, grid_label))
        num_part = ''.join(filter(str.isdigit, grid_label))

        # Handle missing alphabetic part (default to 'A')
        if not alpha_part:
            alpha_part = 'A'

        # Handle missing numeric part (default to '1')
        if not num_part:
            num_part = '1'

        # Calculate the column index from the alphabetic part
        col = 0
        for char in alpha_part:
            col = col * 26 + (ord(char.upper()) - ord('A') + 1)
        col -= 1  # Make it 0-based

        # Calculate the row index from the numeric part
        row = int(num_part) - 1  # Make it 0-based

        return row, col


    def generate_grid_label(self, row, col):
        if row < 0 or col < 0:
            return None

        def column_label(index):
            label = ""
            while index >= 0:
                label = chr(index % 26 + ord("A")) + label
                index = index // 26 - 1
            return label

        col_label = column_label(col)
        label = f"{col_label}{row + 1}"
        print(f"Row: {row}, Column: {col}, Generated Label: {label}")
        return label




    def export_grid_to_txt(self, vector_layer, out_path, grid_field_name=None):
        """
        Export the grid layer's attributes (including adjacency) to a text file.
        """
        # Validate output path
        if not out_path or not os.path.isdir(os.path.dirname(out_path)):
            print("Invalid output path. Skipping export.")
            return

        field_names = ["GridNo", "Left", "Top_Left", "Top", "Top_Right", "Right", "Bottom_Right", "Bottom", "Bottom_Left"]

        try:
            with open(out_path, "w", encoding="utf-8") as f:
                # Write header
                f.write(",".join(field_names) + "\n")
                # Write each feature
                for feature in vector_layer.getFeatures():
                    row = [feature[field] if feature[field] is not None else "" for field in field_names]
                    f.write(",".join(row) + "\n")
            print(f"Adjacency report saved to {out_path}")
        except Exception as e:
            print(f"Error exporting grid to text file: {e}")

