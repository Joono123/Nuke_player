import nuke
from PySide2.QtWidgets import QMainWindow, QPushButton, QLabel


class MyUI(QMainWindow):
    def __init__(self):
        super(MyUI, self).__init__()
        self.setWindowTitle("My PySide2 UI")
        self.setGeometry(100, 100, 300, 200)
        self.filepath = "/home/rapa/Downloads/test1.MOV"
        self.label = QLabel("Hello, NUKE!", self)
        self.label.setGeometry(50, 50, 200, 30)

        self.button = QPushButton("Make Node", self)
        self.button.setGeometry(100, 100, 100, 30)
        self.button.clicked.connect(self.slot)

    def slot(self):
        read = nuke.createNode("Read")
        read["file"].setValue(self.filepath)
        viewer = nuke.createNode("Viewer")
        nuke.connectViewer(0, read)


# 실행할 때만 실행되도록 설정
if __name__ == "__main__":
    # NUKE에서 MyUI를 불러오기
    ui = MyUI()
    ui.show()