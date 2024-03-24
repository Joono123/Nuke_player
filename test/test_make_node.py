import nuke
from PySide2.QtWidgets import QMainWindow, QPushButton, QLabel, QVBoxLayout, QApplication
import os

class MyUI(QMainWindow):
    def __init__(self):
        super(MyUI, self).__init__()
        self.setWindowTitle("My UI")
        self.setGeometry(100, 100, 300, 200)
        v_box = QVBoxLayout()
        self.play_list = ['/home/rapa/Downloads/test1.MOV', '/home/rapa/Downloads/test2.MOV']

        self.label = QLabel("Hello, NUKE!", self)
        self.label.setGeometry(100, 50, 200, 30)

        self.button = QPushButton("Close", self)
        self.button.setGeometry(100, 150, 100, 30)
        self.button.clicked.connect(self.close)

        self.make_btn = QPushButton("Make Node", self)
        self.make_btn.setGeometry(100, 100, 100, 30)
        self.make_btn.clicked.connect(lambda x: self.load_files(self.play_list))

        self.setLayout(v_box)

    def load_files(self, file_paths):
        for idx, file_path in enumerate(file_paths):
            if os.path.exists(file_path):
                read_node = nuke.createNode(f"Read")
                read_node[f"file"].setValue(file_path)
                print(f"Loaded file: {file_path}")
            else:
                print(f"File not found: {file_path}")


if __name__ == "__main__":
    # app = QApplication([])
    ui = MyUI()
    ui.show()
    # app.exec_()
