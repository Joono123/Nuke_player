import nuke
from PySide2 import QtWidgets


class Test_UI(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        w = QtWidgets.QWidget()
        self.setFixedSize(300, 150)
        vlay = QtWidgets.QVBoxLayout()
        btn = QtWidgets.QPushButton("Test")
        btn.clicked.connect(self.slot_btn)
        vlay.addWidget(btn)
        w.setLayout(vlay)
        self.setCentralWidget(w)

    def slot_btn(self):
        print("test")
        read_node = nuke.createNode(f"Read")
        read_node[f"file"].setValue("")


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    t = Test_UI()
    t.show()
    app.exec_()
