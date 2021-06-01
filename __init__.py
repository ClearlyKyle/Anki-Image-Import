from aqt import mw
from aqt.utils import showInfo, qconnect
from aqt.qt import *
import time


class AnkiImageImport(QDialog):
    # _signal = pyqtSignal(int)
    def __init__(self):
        QDialog.__init__(self, parent=mw)
        # super(AnkiImageImport, self).__init__()

        self.CreateFormGroupBox()

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.StartButtonFunction)
        buttonBox.rejected.connect(lambda: self.close())

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.formGroupBox)
        mainLayout.addWidget(buttonBox)

        self.setFixedWidth(300)
        self.setFixedHeight(200)

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
        self.subdirectory_checkbox.toggled.connect(self.SubDirCheckBoxClicked)
        hbox.addWidget(self.subdirectory_checkbox, 0, Qt.AlignCenter)
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

        self.GetFilePaths(self.folderpath)

        self.subdirectory_checkbox.setEnabled(True)

    def GetFilePaths(self, folder_path):
        self.image_paths = []
        for path, subdirs, files in os.walk(folder_path):
            for image_name in files:
                if image_name.lower().endswith((".png", ".jpg", ".jpeg")):
                    self.image_paths.append(os.path.join(path, image_name))

            if self.subdirectory_checkbox.isChecked() is False:
                break

        self.formGroupBox.setTitle("{} images found".format(len(self.image_paths)))

    def SubDirCheckBoxClicked(self):
        if self.folderpath == "":
            return  # No path selected

        self.subdirectory_checkbox.setEnabled(False)
        self.GetFilePaths(self.folderpath)
        self.subdirectory_checkbox.setEnabled(True)

    def UpdateFields(self):
        self.fields_comboBox.clear()

        selected_model = mw.col.models.byName(self.model_comboBox.currentText())

        # list of fields for selected note type
        fields = mw.col.models.fieldNames(selected_model)
        self.fields_comboBox.addItems(fields)

    def StartButtonFunction(self):
        selected_deck = self.deck_comboBox.currentText()
        selected_model = self.model_comboBox.currentText()
        selected_field = self.fields_comboBox.currentText()

        # Set the model
        set_model = mw.col.models.byName(selected_model)
        mw.col.decks.current()["mid"] = set_model["id"]

        # Get the deck
        self.deck = mw.col.decks.byName(selected_deck)

        # Fields
        fields = mw.col.models.fieldMap(set_model)
        self.field_index = fields[selected_field][0]

        # Open Progress Bar window
        self.hide()
        ProgressWindow(self.deck, self.field_index, self.image_paths)
        self.show()
        


class ProgressWindow(QDialog):
    def __init__(self, deck, field_index, image_paths):
        QDialog.__init__(self, parent=mw)

        self.setWindowTitle("Progress")

        self.pbar = QProgressBar(self)
        self.pbar.setValue(0)

        self.resize(300, 100)

        self.vbox = QVBoxLayout()
        self.vbox.addWidget(self.pbar)
        self.setLayout(self.vbox)

        self.deck = deck
        self.field_index = field_index
        self.image_paths = image_paths

        self.show()

        self.StartProcess()

    def StartProcess(self):
        progressbar_steps = 100 / len(self.image_paths)

        for idx, image_path in enumerate(self.image_paths):
            # Write image to collection.media folder and return its new Filename
            new_filename = mw.col.media.add_file(image_path)

            # Create a new Note to add image to
            new_note = mw.col.newNote()
            new_note.model()["did"] = self.deck["id"]

            image_field = '<img src="' + new_filename + '" />'
            new_note.fields[self.field_index] = image_field

            mw.col.addNote(new_note)

            # progressbar.setValue(idx * progressbar_steps)
            self.progress_update((idx + 1) * progressbar_steps)

            time.sleep(0.1)

        mw.col.save()

    def GoToMainWindow(self):
        self.window = AnkiImageImport()
        self.window.show()
        self.close()

    def progress_update(self, msg):
        self.pbar.setValue(msg)
        showInfo("PROGRESS\n{}".format(msg))
        if self.pbar.value() == 100:
            self.pbar.setValue(0)
            self.close()


def StartApplication() -> None:
    dialog = AnkiImageImport()
    dialog.exec_()


action = QAction("Image Loader", mw)
qconnect(action.triggered, StartApplication)
mw.form.menuTools.addAction(action)
