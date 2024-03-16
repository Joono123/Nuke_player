import sys
import single_viewer
from PySide2 import QtWidgets, QtGui, QtCore, QtMultimedia
from library.qt import library as qt_lib


class MultipleViewer(QtWidgets.QWidget):
    def __init__(self, play_lst: list[str], parent=None):
        super().__init__(parent)

        # Layout
        self.__vbox_layout = QtWidgets.QVBoxLayout()
        self.__grid_layout = QtWidgets.QGridLayout()
        self.__grid_layout.setSpacing(10)

        # vars
        self.__play_lst = play_lst
        # self.__meunbar = self.menuBar()
        # self.__statusbar = self.statusBar()
        self.__widget_data = dict()

        # btns
        self.__setup_widgets()
        self.__setup_ui()
        self.__connections()

    def closeEvent(self, event):
        for w in self.__widget_data.values():
            w: single_viewer.VideoWidget
            if w.update_thread.isRunning():
                w.slot_stop_video()
                w.update_thread.stop()
            print(f"\033[31m스레드 정상 종료: {w.wid}\033[0m")
        event.accept()

    def __connections(self):
        self.__btn_play.clicked.connect(self.__slot_play_all)
        self.__btn_pause.clicked.connect(self.__slot_pause_all)
        self.__btn_stop.clicked.connect(self.__slot_stop_all)
        self.__btn_mode.clicked.connect(self.__slot_change_dp)
        self.__btn_loop.clicked.connect(self.__slot_set_loop)

    def __setup_ui(self):
        # self.setFixedSize(1440, 810)
        self.setWindowTitle("Multiple Viewer")
        # central_widget = QtWidgets.QWidget()
        self.setStyleSheet(
            "color: rgb(255, 255, 255);" "background-color: rgb(70, 70, 70);"
        )

        # btns
        self.__btn_play = QtWidgets.QPushButton()
        self.__btn_pause = QtWidgets.QPushButton()
        self.__btn_stop = QtWidgets.QPushButton()
        self.__btn_mode = QtWidgets.QPushButton("tc")
        self.__btn_loop = QtWidgets.QPushButton()
        self.__btn_play.setIcon(
            QtGui.QIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        )
        self.__btn_pause.setIcon(
            QtGui.QIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause))
        )
        self.__btn_stop.setIcon(
            QtGui.QIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaStop))
        )
        self.__btn_loop.setIcon(
            QtGui.QIcon(self.style().standardIcon(QtWidgets.QStyle.SP_BrowserReload))
        )
        self.__btn_play.setFixedSize(100, 30)
        self.__btn_pause.setFixedSize(100, 30)
        self.__btn_stop.setFixedSize(100, 30)
        self.__btn_mode.setFixedSize(50, 30)
        self.__btn_loop.setFixedSize(50, 30)
        self.__btn_play.setToolTip("Play All Videos")
        self.__btn_pause.setToolTip("Pause All Videos")
        self.__btn_stop.setToolTip("Stop All Videos")
        self.__btn_mode.setToolTip("Change Display Format")
        self.__btn_loop.setToolTip("Set Loop")

        self.__btn_loop.setCheckable(True)
        self.__btn_loop.setChecked(False)

        # spacer
        self.__h_spacer = QtWidgets.QSpacerItem(
            200, 30, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        self.__h_spacer2 = QtWidgets.QSpacerItem(
            260, 30, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )

        __h_line = QtWidgets.QFrame()
        __h_line.setFrameShape(QtWidgets.QFrame.HLine)
        __h_line.setFrameShadow(QtWidgets.QFrame.Sunken)

        btn_hbox = QtWidgets.QHBoxLayout()
        btn_hbox.addItem(self.__h_spacer2)
        btn_hbox.addWidget(self.__btn_play)
        btn_hbox.addWidget(self.__btn_pause)
        btn_hbox.addWidget(self.__btn_stop)
        btn_hbox.addWidget(self.__btn_mode)
        btn_hbox.addWidget(self.__btn_loop)
        btn_hbox.addItem(self.__h_spacer)

        self.__vbox_layout.addLayout(self.__grid_layout)
        self.__vbox_layout.addWidget(__h_line)
        self.__vbox_layout.addLayout(btn_hbox)

        # central_widget.setLayout(self.__vbox_layout)
        self.setLayout(self.__vbox_layout)

    def __setup_widgets(self):
        for idx, v_path in enumerate(self.__play_lst):
            self.widget = single_viewer.VideoWidget(v_path)
            self.widget.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
            )

            self.__frame = QtWidgets.QFrame()
            self.__frame.setFrameShape(QtWidgets.QFrame.Panel)
            self.__frame.setFrameShadow(QtWidgets.QFrame.Raised)
            self.__frame.setLineWidth(3)
            self.__frame.setLayout(QtWidgets.QVBoxLayout())
            self.__frame.layout().addWidget(self.widget)
            self.__frame.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
            )
            self.__widget_data[self.widget.wid] = self.widget
            if len(self.__play_lst) <= 4:
                # widget.setMinimumSize(720, 480)
                self.__grid_layout.addWidget(self.__frame, int(idx // 2), int(idx % 2))
            elif 4 < len(self.__play_lst) <= 9:
                # self.widget.setMinimumSize(320, 180)
                self.__grid_layout.addWidget(self.__frame, int(idx // 3), int(idx % 3))
            elif 9 < len(self.__play_lst):
                # self.widget.setMinimumSize(224, 126)
                self.__grid_layout.addWidget(self.__frame, int(idx // 4), int(idx % 4))

        rows = self.__grid_layout.rowCount()
        for row in range(rows):
            self.__grid_layout.setRowStretch(row, 1)
        cols = self.__grid_layout.columnCount()
        for col in range(cols):
            self.__grid_layout.setRowStretch(col, 1)

    def __slot_set_loop(self):
        if self.__btn_loop.isChecked():
            for w in self.__widget_data.values():
                w: single_viewer.VideoWidget
                w.btn_loop.setChecked(True)
        else:
            for w in self.__widget_data.values():
                w: single_viewer.VideoWidget
                w.btn_loop.setChecked(False)

    def __slot_change_dp(self):
        if self.__btn_mode.text() == "fps":
            self.__btn_mode.setText("tc")
        elif self.__btn_mode.text() == "tc":
            self.__btn_mode.setText("fps")
        for w in self.__widget_data.values():
            w: single_viewer.VideoWidget
            if self.__btn_mode.text() == "tc":
                w.btn_mode.setText("tc")
            elif self.__btn_mode.text() == "fps":
                w.btn_mode.setText("fps")

    def __slot_play_all(self):
        for w in self.__widget_data.values():
            w: single_viewer.VideoWidget
            w.player.play()
            self.__btn_play.setEnabled(False)
            self.__btn_pause.setEnabled(True)

    def __slot_pause_all(self):
        for w in self.__widget_data.values():
            w: single_viewer.VideoWidget
            w.player.pause()
            self.__btn_play.setEnabled(True)
            self.__btn_pause.setEnabled(False)

    def __slot_stop_all(self):
        for w in self.__widget_data.values():
            w: single_viewer.VideoWidget
            w.player.stop()
            self.__btn_play.setEnabled(True)
            self.__btn_pause.setEnabled(False)

    @property
    def get_dp_mode(self) -> str:
        return self.__btn_mode.text()


# test_list = [
#     "/home/rapa/Downloads/test1.MOV",
#     "/home/rapa/Downloads/test2.MOV",
#     "/home/rapa/Downloads/test_1280 (copy).mp4",
#     "/home/rapa/Downloads/test_1280 (another copy).mp4",
#     "/home/rapa/Downloads/test_1280 (another copy).mp4",
#     "/home/rapa/Downloads/test_1280 (another copy).mp4",
#     "/home/rapa/Downloads/test_1280 (another copy).mp4",
#     "/home/rapa/Downloads/test_1280 (another copy).mp4",
#     "/home/rapa/Downloads/test_1280 (another copy).mp4",
#     # "/home/rapa/Downloads/test_1280 (another copy).mp4",
# ]
# if __name__ == "__main__":
#     app = QtWidgets.QApplication(sys.argv)
#     mv = MultipleViewer(test_list)
#     mv.show()
#     app.exec_()
