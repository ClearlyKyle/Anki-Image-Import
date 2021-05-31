from aqt import mw
from aqt.utils import showInfo, qconnect
from aqt.qt import *
import time


class AnkiImageImport(QDialog):
    # _NumGridRows = 3
    # _NumButtons = 4

    # setting  the fixed width of window
    _width = 300
    _height = 200

    _signal = pyqtSignal(int)

    def __init__(self):
        QDialog.__init__(self, parent=mw)
        # super(AnkiImageImport, self).__init__()

        self.CreateFormGroupBox()

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.StartButtonFunction)
        buttonBox.rejected.connect(self.OnReject)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.formGroupBox)
        mainLayout.addWidget(buttonBox)

        self.setFixedWidth(self._width)
        self.setFixedHeight(self._height)

        self.setLayout(mainLayout)
        self.setWindowTitle("Anki Picture Importer - Settings")

    def CreateFormGroupBox(self):
        self.formGroupBox = QGroupBox("Settings")
        layout = QFormLayout()

        btn = QPushButton("...")
        btn.clicked.connect(self.GetFile)
        btn.setMaximumWidth(20)
        hbox = QHBoxLayout()

        # Folder path
        self.file_path_box = QLineEdit()
        self.file_path_box.setReadOnly(True)
        hbox.addWidget(self.file_path_box)
        hbox.addWidget(btn)

        layout.addRow(QLabel("Folder:"), hbox)

        # Decks
        self.deck_comboBox = QComboBox()
        self.deck_names = [x.name for x in mw.col.decks.all_names_and_ids()]
        self.deck_comboBox.addItems(self.deck_names)
        layout.addRow(QLabel("Deck:"), self.deck_comboBox)

        # Model
        self.model_comboBox = QComboBox()
        self.model_names = [x.name for x in mw.col.models.all_names_and_ids()]
        self.model_comboBox.addItems(self.model_names)
        layout.addRow(QLabel("Model:"), self.model_comboBox)

        # Fields
        self.fields_comboBox = QComboBox()
        layout.addRow(QLabel("Field:"), self.fields_comboBox)
        self.model_comboBox.currentTextChanged.connect(self.UpdateFields)
        self.UpdateFields()

        # Check Boxes
        hbox = QHBoxLayout()
        self.subdirectory_checkbox = QCheckBox("Search Subdirectories")
        self.subdirectory_checkbox.setChecked(False)
        hbox.addWidget(self.subdirectory_checkbox, 0, Qt.AlignRight)
        # r2 = QCheckBox("Delete")
        # hbox.addWidget(r2, 0)
        layout.addRow(hbox)

        self.formGroupBox.setLayout(layout)

    def GetFile(self):
        self.subdirectory_checkbox.setEnabled(False)

        # Get path to Image Folder
        self.folderpath = QFileDialog.getExistingDirectory(self, "Select Folder")
        # showInfo("folderpath\n{}".format(self.folderpath))

        if self.folderpath == "":
            return  # No path selected

        self.file_path_box.setText(self.folderpath)

        self.image_paths = []

        for path, subdirs, files in os.walk(self.folderpath):
            for image_name in files:
                if image_name.lower().endswith((".png", ".jpg", ".jpeg")):
                    self.image_paths.append(os.path.join(path, image_name))

            if self.subdirectory_checkbox.isChecked() is False:
                break

        self.formGroupBox.setTitle("{} images found".format(len(self.image_paths)))
        self.subdirectory_checkbox.setEnabled(True)

    def UpdateFields(self):
        self.fields_comboBox.clear()

        selected_model = mw.col.models.byName(self.model_comboBox.currentText())

        # list of fields for selected note type
        fields = mw.col.models.fieldNames(selected_model)
        self.fields_comboBox.addItems(fields)

    def StartButtonFunction(self):
        # if self.duplicate_checkbox.isChecked():
        #    showInfo("{}".format("Check Box Is True"))

        selected_deck = self.deck_comboBox.currentText()
        selected_model = self.model_comboBox.currentText()
        selected_field = self.fields_comboBox.currentText()

        # Set the model
        set_model = mw.col.models.byName(selected_model)
        mw.col.decks.current()["mid"] = set_model["id"]
        # showInfo("MODEL\n{}".format(set_model))

        # Get the deck
        deck = mw.col.decks.byName(selected_deck)
        # showInfo("DECK\n{}".format(deck))

        # Fields
        fields = mw.col.models.fieldMap(set_model)
        field_index = fields[selected_field][0]

        # Open Progress Bar window
        progressbar = ProgressWindow()
        progressbar.show()

        self.hide()  # hide options window

        progressbar_steps = 100 / len(self.image_paths)

        for idx, image_path in enumerate(self.image_paths):
            # Write image to collection.media folder and return its new Filename
            new_filename = mw.col.media.add_file(image_path)

            # Create a new Note to add image to
            new_note = mw.col.newNote()
            new_note.model()["did"] = deck["id"]

            image_field = '<img src="' + new_filename + '" />'
            new_note.fields[field_index] = image_field

            mw.col.addNote(new_note)

            # self._signal.emit(idx)
            progressbar.setValue(idx * progressbar_steps)
            time.sleep(1)
            QApplication.processEvents()

        mw.col.save()
        progressbar.close()
        self.show()

    def OnReject(self):
        self.close()


class ProgressWindow(QDialog):
    def __init__(self):
        QDialog.__init__(self, parent=mw)

        self.setWindowTitle("Progress")

        self.pbar = QProgressBar(self)
        self.pbar.setValue(0)

        self.resize(300, 100)

        self.vbox = QVBoxLayout()
        self.vbox.addWidget(self.pbar)
        self.setLayout(self.vbox)

        self.show()

    def setValue(self, val):
        self.pbar.setValue(val)


# class Thread(QThread):
#    progress_update = QtCore.Signal(int) # or pyqtSignal(int)

#    def __init__(self):
#        QThread.__init__(self)

#    def __del__(self):
#        self.wait()

#    def run(self):
#        for i in range(100):
#            time.sleep(0.1)
#            self._signal.emit(i)


def StartApplication() -> None:
    dialog = AnkiImageImport()
    dialog.exec_()


action = QAction("Image Loader", mw)
qconnect(action.triggered, StartApplication)
mw.form.menuTools.addAction(action)
