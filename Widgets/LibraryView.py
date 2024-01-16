
import os
from typing import List, Union

from PyQt5.QtWidgets import QFrame, QGridLayout, QSpacerItem, QVBoxLayout, QLabel, QStackedWidget, QFileDialog, QWidget, QScrollArea, QSizePolicy, QHBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QMovie

from Widgets.components.BytesEncoder import base64_to_bytes, bytes_to_pixmap
from Widgets.components.CardWidget import CardWidget
from Widgets.components.DataTypes import CardMetadata
from Widgets.components.XMLGenerator import XMLGenerator

class LibraryView(QFrame):

    update_library_requested = pyqtSignal()
    edit_card_requested = pyqtSignal(object)
    delete_card_requested = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.xml_generator = XMLGenerator()
        self.set_up_ui()

    def set_up_ui(self):
        #self.setStyleSheet("background-color: red")
        
        self.setFrameStyle(QFrame.Panel | QFrame.Sunken)

        self.gen_layout = QVBoxLayout(self)
        self.control_layout = QHBoxLayout()

        self.refresh_button = QPushButton("Refresh", self)
        self.refresh_button.clicked.connect(self.update)
        self.control_layout.addWidget(self.refresh_button)

        self.export_button = QPushButton("Экспорт", self)
        self.export_button.clicked.connect(self.on_export_clicked)
        self.control_layout.addWidget(self.export_button)

        self.scroll_stack = QStackedWidget(self)
        self.scroll_area = QScrollArea(self)
        
        self.loading_label = QLabel(self)
        self.loading_animation = QMovie(r"assets/loading_animation.gif")
        self.loading_label.setMovie(self.loading_animation)

        self.scroll_stack.addWidget(self.scroll_area)
        self.scroll_stack.addWidget(self.loading_label)
        self.scroll_stack.setCurrentIndex(0)

        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        #self.scroll_area.setStyleSheet("background-color: yellow")
        self.scrollable_widget = QWidget(self.scroll_area)
        #self.scrollable_widget.setStyleSheet("background-color: green")
        self.grid_layout = QGridLayout(self.scrollable_widget)
        self.scroll_area.setWidget(self.scrollable_widget)

        self.gen_layout.addLayout(self.control_layout)
        self.gen_layout.addWidget(self.scroll_stack)
        self.setLayout(self.gen_layout)

    def update(self):
        self.set_loading(True)
        self.update_library_requested.emit()

    def set_loading(self, is_loading: bool):
        if is_loading:
            self.scroll_stack.setCurrentIndex(1)
            self.loading_label.resize(self.scroll_area.size())
            self.loading_label.setStyleSheet(self.scrollable_widget.styleSheet())
            self.loading_animation.start()
        else:
            self.scroll_stack.setCurrentIndex(0)
            self.loading_animation.stop()

        self.refresh_button.setEnabled(not is_loading)
        self.export_button.setEnabled(not is_loading)

    def set_updated_data(self, cards: List[CardMetadata]):
        if not cards:
            print("Cannot update library view")
            return
        self.clear_grid()

        pos = 0
        for card in cards:
            if not card.card_image:
                print(f"Skipped card [{card.id}]: no image")
                continue
            card_widget = CardWidget(card, self)
            card_widget.edit_card_requested.connect(self.edit_card_requested)
            card_widget.delete_card_requested.connect(self.delete_card_requested)
            card_widget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            self.grid_layout.addWidget(card_widget, pos//5, pos%5)
            pos+=1
            
        
        self.scrollable_widget.setMinimumWidth(self.scroll_area.width())
        self.scrollable_widget.setMinimumHeight(self.scroll_area.height())
        print("Library view updated")
        self.set_loading(False)

    def clear_grid(self):
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    
    def on_export_clicked(self):
        card_widgets = []
        for card in range(self.grid_layout.count()):
            item = self.grid_layout.itemAt(card)
            if item.widget() is not None:
                card_widgets.append(item.widget())
        if card_widgets:
            directory_path = QFileDialog.getExistingDirectory(None, "Выберите папку", ".", )
            if directory_path:
                for card in card_widgets:
                    img = bytes_to_pixmap(card.metadata.card_image)
                    img.save(os.path.join(directory_path, card.metadata.name + ".png"))
                # Windows only
                os.startfile(directory_path)
        
        meta_list = []
        for card_widget in card_widgets:
            meta = card_widget.metadata
            meta.card_image = None
            meta.picture = None
            meta_list.append(meta)
        self.xml_generator.generate_xml_library(meta_list)

    def resizeEvent(self, a0) -> None:
        self.scrollable_widget.resize(self.scroll_area.size())
        return super().resizeEvent(a0)
