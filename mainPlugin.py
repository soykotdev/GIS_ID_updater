from . import resources_rc  

from qgis.core import QgsProject, QgsVectorLayer, QgsField, QgsGeometry, Qgis
from PyQt5.QtCore import QVariant, Qt
from qgis.gui import QgsMapTool
from qgis.utils import iface
from PyQt5.QtGui import QCursor, QIcon
from PyQt5.QtWidgets import QAction, QComboBox, QVBoxLayout, QWidget, QSpinBox, QLabel, QPushButton, QHBoxLayout

class SequentialIDUpdater(QgsMapTool):
    def __init__(self, layer, field_name, start_number):
        super().__init__(iface.mapCanvas())
        self.layer = layer
        self.field_name = field_name
        self.current_number = start_number
        iface.mapCanvas().setCursor(QCursor(Qt.CrossCursor))
        print("Tool activated with starting number:", self.current_number)

    def canvasPressEvent(self, event):
        point = self.toLayerCoordinates(self.layer, event.pos())
        point_geom = QgsGeometry.fromPointXY(point)

        closest_feature = None
        min_dist = float("inf")

        for feature in self.layer.getFeatures():
            dist = feature.geometry().distance(point_geom)
            if dist < min_dist:
                min_dist = dist
                closest_feature = feature

        if closest_feature:
            self.layer.startEditing()
            try:
                self.layer.changeAttributeValue(
                    closest_feature.id(),
                    self.layer.fields().indexFromName(self.field_name),
                    self.current_number
                )
                self.current_number += 1
                self.layer.commitChanges()
                iface.mapCanvas().refresh()
                print(f"Updated feature ID to {self.current_number - 1}.")
            except Exception as e:
                self.layer.rollBack()
                print(f"An error occurred: {e}")
        else:
            print("No feature found close to the clicked point.")

class GIS_Snake_Plugin:
    def __init__(self):
        self.action = QAction(QIcon(":/icons/icon.png"), "GIS Snake", iface.mainWindow())
        self.action.triggered.connect(self.run)
        iface.addToolBarIcon(self.action)

        self.stop_action = QAction(QIcon(":/icons/stop.png"), "Stop Tool", iface.mainWindow())
        self.stop_action.triggered.connect(self.stop_tool)
        iface.addToolBarIcon(self.stop_action)

        self.widget = None
        self.tool = None

    def initGui(self):
        self.action.setEnabled(True)
        self.stop_action.setEnabled(True)
        
    def run(self):
        layers = [layer for layer in QgsProject.instance().mapLayers().values() if isinstance(layer, QgsVectorLayer)]
        
        if not layers:
            iface.messageBar().pushWarning("Warning", "No vector layers found!")
            return
        
        self.layer_combo = QComboBox()
        self.layer_combo.addItems([layer.name() for layer in layers])

        self.field_combo = QComboBox()
        self.layer_combo.currentIndexChanged.connect(self.populate_fields)
        
        self.start_number_spinbox = QSpinBox()
        self.start_number_spinbox.setMinimum(1)
        self.start_number_spinbox.setMaximum(1000000)
        self.start_number_spinbox.setValue(1)

        start_button = QPushButton("Start Tool")
        start_button.clicked.connect(self.start_tool)
        
        self.widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Select Layer:"))
        layout.addWidget(self.layer_combo)
        layout.addWidget(QLabel("Select Field:"))
        layout.addWidget(self.field_combo)
        layout.addWidget(QLabel("Start Number:"))
        layout.addWidget(self.start_number_spinbox)
        layout.addWidget(start_button)
        
        copyright_layout = QHBoxLayout()
        copyright_label = QLabel("©: Soykot Hossain, Jr. GIS analyst")
        copyright_layout.addStretch()
        copyright_layout.addWidget(copyright_label)
        copyright_layout.addStretch()
        layout.addLayout(copyright_layout)
        
        self.widget.setLayout(layout)
        self.widget.resize(300, 220)
        self.widget.show()

        self.populate_fields()
        
    def populate_fields(self):
        selected_layer_name = self.layer_combo.currentText()
        selected_layer = QgsProject.instance().mapLayersByName(selected_layer_name)[0]
        fields = [field.name() for field in selected_layer.fields()]
        self.field_combo.clear()
        self.field_combo.addItems(fields)

    def start_tool(self):
        print("Start Tool button clicked")
        
        selected_layer_name = self.layer_combo.currentText()
        selected_field_name = self.field_combo.currentText()
        start_number = self.start_number_spinbox.value()

        selected_layer = QgsProject.instance().mapLayersByName(selected_layer_name)[0]
        
        self.tool = SequentialIDUpdater(selected_layer, selected_field_name, start_number)
        iface.mapCanvas().setMapTool(self.tool)

        print("Map tool set")
        self.widget.hide()
    
    def stop_tool(self):
        print("Stop Tool button clicked")
        if self.tool:
            iface.mapCanvas().unsetMapTool(self.tool)
            self.tool = None
        iface.messageBar().pushMessage("GIS Snake", "Tool has been stopped", level=Qgis.Info)

    def unload(self):
        iface.removeToolBarIcon(self.action)
        iface.removeToolBarIcon(self.stop_action)
