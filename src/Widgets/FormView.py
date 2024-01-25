from PyQt5.QtWidgets import QLineEdit, QLabel, QApplication, QTextEdit, QVBoxLayout, QComboBox, QFrame, QHBoxLayout, QPushButton, QSpinBox, QFormLayout, QSizePolicy
from PyQt5.QtCore import pyqtSignal

from DataTypes import CardMetadata, CardType, ClassType, Rarity
from Widgets.components.ButtonGroup import ExclusiveButtonGroup
from Widgets.components.FormLabel import FormLabel

class FormView(QFrame):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.set_up_ui()
        self.set_up_connections()
            
    def set_up_connections(self):
        self.cardtype_button_group.button_clicked.connect(self.toggle_form_widgets)

    def set_up_ui(self):
        self.gen_layout = QVBoxLayout()
        self.layout_inlay1 = QHBoxLayout()

        self.layout_inlay_mana = QVBoxLayout()
        self.layout_inlay_attack = QVBoxLayout()
        self.layout_inlay_health = QVBoxLayout()
        

        self.cardtype_button_group = ExclusiveButtonGroup(4, r":icons\typeicons", 0, 0, self)
        self.cardtype_button_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        # TODO: implement weapon and hero generator
        self.cardtype_button_group.buttons[2].setEnabled(False)
        self.cardtype_button_group.buttons[3].setEnabled(False)

        self.class_button_group = ExclusiveButtonGroup(10, r":icons\classicons", 0, 1, self)

        self.name_label = FormLabel("Название карты", self)
        self.name_form = QLineEdit(self)
        self.name_form.setPlaceholderText('Название карты')

        self.description_label = FormLabel("Описание карты", self)
        self.description_form = QTextEdit(self)
        self.description_form.setPlaceholderText('Описание')
        self.description_form.setMaximumHeight(200)

        self.mana_label = FormLabel("Стоимсть", self)
        self.mana_form = QSpinBox(self)
        self.mana_form.setRange(0, 99)

        self.attack_label = FormLabel("Атака", self)
        self.attack_form = QSpinBox(self)
        self.attack_form.setRange(0, 99)

        self.health_label = FormLabel("Здоровье", self)
        self.health_form = QSpinBox(self)
        self.health_form.setRange(0, 99)

        self.rarity_label = FormLabel("Редкость", self)
        self.rarity_form = QComboBox(self)
        self.rarity_form.addItems(list(map(str.capitalize, Rarity._member_names_)))

        self.tribe_label = FormLabel("Раса", self)
        self.tribe_form = QLineEdit(self)
        self.tribe_form.setPlaceholderText("Раса")

        ###

        self.gen_layout.addWidget(self.cardtype_button_group)
        self.gen_layout.addWidget(self.class_button_group)

        self.gen_layout.addWidget(self.name_label)
        self.gen_layout.addWidget(self.name_form)
        self.gen_layout.addSpacing(15)

        self.gen_layout.addWidget(self.description_label)
        self.gen_layout.addWidget(self.description_form)
        self.gen_layout.addSpacing(15)

        self.layout_inlay_mana.addWidget(self.mana_label)
        self.layout_inlay_mana.addWidget(self.mana_form)

        self.layout_inlay_attack.addWidget(self.attack_label)
        self.layout_inlay_attack.addWidget(self.attack_form)

        self.layout_inlay_health.addWidget(self.health_label)
        self.layout_inlay_health.addWidget(self.health_form)

        self.gen_layout.addWidget(self.rarity_label)
        self.gen_layout.addWidget(self.rarity_form)
        self.gen_layout.addSpacing(15)

        self.layout_inlay1.addLayout(self.layout_inlay_mana)
        self.layout_inlay1.addLayout(self.layout_inlay_attack)
        self.layout_inlay1.addLayout(self.layout_inlay_health)
        self.gen_layout.addLayout(self.layout_inlay1)
        self.gen_layout.addSpacing(15)
        
        self.gen_layout.addWidget(self.tribe_label)
        self.gen_layout.addWidget(self.tribe_form)

        self.gen_layout.addStretch()


        self.setLayout(self.gen_layout)

    def get_form_data(self) -> dict:
        data = {
            "name": self.name_form.text(),
            "description": self.description_form.toPlainText(),
            "manacost": self.mana_form.value(),
            "rarity": self.rarity_form.currentIndex() + 1,
            "cardtype": self.cardtype_button_group.get_checked_button_index() + 1,
            "classtype": self.class_button_group.get_checked_button_index() + 1,
            "attack": self.attack_form.value(),
            "health": self.health_form.value(),
            "tribe": self.tribe_form.text(),
        }

        return data
    
    def toggle_form_widgets(self):
        cardtype = self.cardtype_button_group.get_checked_button_index() + 1

        if cardtype == CardType.MINION:
            self.attack_form.setEnabled(True)
            self.health_form.setEnabled(True)

        elif cardtype == CardType.SPELL:
            self.attack_form.setEnabled(False)
            self.health_form.setEnabled(False)

    def reset(self):
        self.name_form.setText("")
        self.description_form.setText("")
        self.attack_form.setValue(0)
        self.health_form.setValue(0)
        self.mana_form.setValue(0)
        self.rarity_form.setCurrentIndex(0)
        self.tribe_form.setText("")