import time
from aqt import mw
from aqt.utils import showInfo, qconnect
from aqt.qt import *


class DragAndDropLabel(QLabel):

    def __init__(self, title, parent):
        super().__init__(title, parent)

        self.setAcceptDrops(True)

        self.paths = []

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    def printAllPaths(self):
        print("number of paths = {}".format(len(self.paths)))
        for p in self.paths:
            print(p)

    def dropEvent(self, e):
        for url in e.mimeData().urls():
            if url.toString().lower().endswith((".png", ".jpg", ".jpeg")):
                if(url.toLocalFile() not in self.paths):
                    self.paths.append(url.toLocalFile())
                else:
                    print("File already added!")
            else:
                print("Not a supported file format (\".png\", \".jpg\", \".jpeg\")")

        self.setText("Number of Images added: {}".format(len(self.paths)))
        # self.printAllPaths()

    def getPaths(self):
        return self.paths


class AnkiImageImport(QDialog):
    def __init__(self):
        super(AnkiImageImport, self).__init__()

        self.folderpath = ""
        self.image_paths = []

        self.deck = None
        self.field_index = None

        self.CreateFormGroupBox()

        self.setFixedWidth(500)
        self.setFixedHeight(300)

        # self.setLayout(mainLayout)
        self.setWindowTitle("Anki Picture Importer - Settings")

    def CreateFormGroupBox(self):
        self.resize(800, 600)

        main_layout = QHBoxLayout()

        self.formGroupBox = QGroupBox("Settings")
        self.formGroupBox.setMaximumSize(QSize(225, 300))  # (w, h)
        self.formGroupBox.setMinimumSize(QSize(225, 0))
        layout = QFormLayout()

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

        self.formGroupBox.setLayout(layout)

        # Now added the left side to the MAIN_LAYOUT
        main_layout.addWidget(self.formGroupBox, 30)

        # ---------------------------------------------------
        # RIGHT SIDE

        self.RIGHT_groupbox = QGroupBox("Method")
        verticalInnerLayout = QVBoxLayout()
        self.RIGHT_groupbox.setLayout(verticalInnerLayout)

        ##

        # UPPER option - load with folder path
        find_folder_btn = QPushButton("...")
        find_folder_btn.clicked.connect(self.GetFile)
        find_folder_btn.setMaximumWidth(20)

        self.file_path_box = QLineEdit()
        self.file_path_box.setReadOnly(True)
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel("Folder:"))
        hbox.addWidget(self.file_path_box)
        hbox.addWidget(find_folder_btn)
        # Add Folder path option to RIGH box
        verticalInnerLayout.addLayout(hbox)

        # search sub directory checkbox
        self.subdirectory_checkbox = QCheckBox("Search Subdirectories")
        self.subdirectory_checkbox.setChecked(False)
        self.subdirectory_checkbox.toggled.connect(self.SubDirCheckBoxClicked)
        # add sub directory checkbox
        verticalInnerLayout.addWidget(self.subdirectory_checkbox)

        # buttons to save and reset folder options
        add_folder_button = QPushButton('Add')
        add_folder_button.setMaximumWidth(50)
        add_folder_button.clicked.connect(self.FolderAdd)

        reset_folder_button = QPushButton('Reset')
        reset_folder_button.setMaximumWidth(50)
        reset_folder_button.clicked.connect(self.ResetFolderPaths)

        hbox = QHBoxLayout()
        self.number_of_images_in_folder_label = QLabel("")
        hbox.addWidget(self.number_of_images_in_folder_label)
        hbox.addWidget(add_folder_button, Qt.AlignRight)
        hbox.addWidget(reset_folder_button, Qt.AlignRight)

        # Add start and reset buttons to RIGH box
        verticalInnerLayout.addLayout(hbox)

        # Add LINE between top and lower options
        line = QFrame()
        line.setGeometry(QRect(60, 110, 751, 20))
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        verticalInnerLayout.addWidget(line)

        # Add LOWER Widget
        self.dragdrop_label = DragAndDropLabel("Drag Files here..", self)
        self.dragdrop_label.setStyleSheet("\
            border-style: dashed;\
            border-width: 2px;\
            border-color: blue;\
            text-align: center;\
        ")
        self.dragdrop_label.setAlignment(Qt.AlignCenter)
        #dragdrop_label.resize(300, 150)

        # Add Upper Widget
        verticalInnerLayout.addWidget(self.dragdrop_label)

        # create add and reset buttons for drag and drop options
        add_dd_button = QPushButton('Add')
        add_dd_button.setMaximumWidth(50)
        add_dd_button.clicked.connect(self.DragAndDropAdd)

        reset_dd_button = QPushButton('Reset')
        reset_dd_button.setMaximumWidth(50)
        reset_dd_button.clicked.connect(self.ResetDragAndDrop)

        hbox = QHBoxLayout()
        self.number_of_images_in_dd_label = QLabel("")
        hbox.addWidget(self.number_of_images_in_dd_label)
        hbox.addWidget(add_dd_button, Qt.AlignRight)
        hbox.addWidget(reset_dd_button, Qt.AlignRight)
        verticalInnerLayout.addLayout(hbox)

        # Add to main
        # Add the right side to the main layout
        main_layout.addWidget(self.RIGHT_groupbox, 70)

        self.setLayout(main_layout)

    def DragAndDropAdd(self):
        if not self.dragdrop_label.paths:
            print("No images to add...")
            return None

        self.image_paths = self.dragdrop_label.paths
        self.CreateCardsFromImagePaths()

    def ResetDragAndDrop(self):
        print("Resetting Drag and Drop Image paths")
        self.dragdrop_label.paths = []
        self.dragdrop_label.setText("Drag Files here..")

    def FolderAdd(self):
        if self.folderpath == "":
            print("No path selected...")
            return None  # No path selected

        self.CreateCardsFromImagePaths()

    def ResetFolderPaths(self):
        print("Clear current folder paths...")
        self.folderpath = ""
        self.image_paths = []
        self.file_path_box.clear()
        self.number_of_images_in_folder_label.setText("")

    def GetFile(self):
        self.subdirectory_checkbox.setEnabled(False)

        # Get path to Image Folder
        self.folderpath = QFileDialog.getExistingDirectory(self, "Select Folder")
        # showInfo("folderpath\n{}".format(self.folderpath))

        if self.folderpath == "":
            print("No file selected...")
            self.subdirectory_checkbox.setEnabled(True)
            return None  # No path selected

        self.file_path_box.setText(self.folderpath)

        self.GetFilePathsFromFolder(self.folderpath)

        self.subdirectory_checkbox.setEnabled(True)

    def GetFilePathsFromFolder(self, folder_path):
        self.image_paths = []
        for path, subdirs, files in os.walk(folder_path):
            for image_name in files:
                if image_name.lower().endswith((".png", ".jpg", ".jpeg")):
                    print(image_name)
                    self.image_paths.append(
                        os.path.join(path, image_name))

            if self.subdirectory_checkbox.isChecked() is False:
                break

        self.number_of_images_in_folder_label.setText(
            "{} images found".format(len(self.image_paths)))

    def SubDirCheckBoxClicked(self):
        if self.folderpath == "":
            return  # No path selected

        self.subdirectory_checkbox.setEnabled(False)
        self.GetFilePathsFromFolder(self.folderpath)
        self.subdirectory_checkbox.setEnabled(True)

    def UpdateFields(self):
        self.fields_comboBox.clear()

        selected_model = mw.col.models.byName(
            self.model_comboBox.currentText())

        # list of fields for selected note type
        fields = mw.col.models.fieldNames(selected_model)
        self.fields_comboBox.addItems(fields)

    def CreateCardsFromImagePaths(self):
        if not self.image_paths:
            print("No files to add..")
            return

        print(self.image_paths)

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

        # Start Processing New Cards
        # self.hide()
        self.GenerateNewCards()
        # self.show()

    def GenerateNewCards(self):
        # remove "?" hint button
        progress = QProgressDialog(self, Qt.WindowTitleHint)
        progress.setWindowModality(Qt.ApplicationModal)
        progress.setLabelText("Generating Cards from Images...")
        progress.setMaximum(100)
        # time delay before showing progress bar
        progress.setMinimumDuration(2000)
        progress.setCancelButton(None)      # remove cancel button
        progress.setMinimumWidth(350)       # window width
        progress.setAutoClose(True)         # close after 100%

        # progress.setValue(0)
        # progress.setValue(1)
        # progress.setValue(0)

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
            progress.setValue((idx + 1) * progressbar_steps)

            if progress.wasCanceled():
                break

            # time.sleep(0.05)

        mw.col.save()
        showInfo("Sucess!")


def StartApplication() -> None:
    dialog = AnkiImageImport()
    dialog.exec_()


action = QAction("Image Loader", mw)
qconnect(action.triggered, StartApplication)
mw.form.menuTools.addAction(action)
