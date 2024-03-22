import sys
from PySide2 import QtWidgets, QtGui


class MultipleViewer(QtWidgets.QMainWindow):
    def __init__(self, play_lst: list[str], parent=None):
        super().__init__(parent)

        # Layout
        self.__vbox_layout = QtWidgets.QVBoxLayout()
        self.__grid_layout = QtWidgets.QGridLayout()
        self.__grid_layout.setSpacing(10)
        self.setContentsMargins(0, 0, 0, 0)

        # vars
        self.__play_lst = play_lst
        self.__meunbar = self.menuBar()
        self.__statusbar = self.statusBar()

        # btns

        self.__setup_widgets()
        self.__setup_ui()

    def __setup_ui(self):
        self.setWindowTitle("Nuke Player")
        central_widget = QtWidgets.QWidget()
        self.setStyleSheet(
            "color: rgb(255, 255, 255);" "background-color: rgb(70, 70, 70);"
        )

        self.__btn_play = QtWidgets.QPushButton()
        self.__btn_play.setIcon(
            QtGui.QIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        )
        self.__btn_play.setFixedSize(60, 40)
        self.__btn_stop = QtWidgets.QPushButton()
        self.__btn_stop.setIcon(
            QtGui.QIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaStop))
        )
        self.__btn_stop.setFixedSize(60, 40)
        self.__h_spacer = QtWidgets.QSpacerItem(
            200, 40, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )

        btn_hbox = QtWidgets.QHBoxLayout()
        btn_hbox.addWidget(self.__btn_play)
        btn_hbox.addWidget(self.__btn_stop)
        btn_hbox.addItem(self.__h_spacer)

        self.__vbox_layout.addLayout(self.__grid_layout)
        self.__vbox_layout.addLayout(btn_hbox)

        central_widget.setLayout(self.__vbox_layout)
        self.setCentralWidget(central_widget)

    def __setup_widgets(self):
        for idx, v_path in enumerate(self.__play_lst):
            widget = single_viewer.VideoWidget(v_path)

            frame = QtWidgets.QFrame()
            frame.setFrameShape(QtWidgets.QFrame.Panel)
            frame.setFrameShadow(QtWidgets.QFrame.Sunken)
            frame.setLineWidth(3)
            frame.setLayout(QtWidgets.QVBoxLayout())
            frame.layout().addWidget(widget)
            self.__grid_layout.addWidget(frame, int(idx // 3), int(idx % 3))
        # self.adjustSize()


test_list = [
    "/home/rapa/Downloads/test1.MOV",
    "/home/rapa/Downloads/test2.MOV",
    "/home/rapa/Downloads/test_1280 (copy).mp4",
    "/home/rapa/Downloads/test_1280 (another copy).mp4",
]
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mv = MultipleViewer(test_list)
    mv.show()
    app.exec_()
