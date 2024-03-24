#!/usr/bin/env python
# encoding=utf-8

# author        :   Juno Park
# created date  :   2024.03.05
# modified date :   2024.03.23
# description   :   Nuke_player에 삽입되는 Multiple_viewer 클래스


import sys
import importlib
from library.player import multiple_viewer_parent
from PySide2 import QtWidgets, QtGui, QtCore

importlib.reload(multiple_viewer_parent)


class MultipleViewer(QtWidgets.QWidget):
    def __init__(self, play_lst: list[str], parent=None):
        super().__init__(parent)
        self.setWindowModality(QtCore.Qt.WindowModal)

        # Layout
        self.__vbox_layout = QtWidgets.QVBoxLayout()
        self.__grid_layout = QtWidgets.QGridLayout()
        self.__grid_layout.setSpacing(10)

        # vars
        self.__play_lst = play_lst
        self.__widget_data = dict()

        # btns
        self.__setup_widgets()
        self.__setup_ui()
        self.__connections()

    def closeEvent(self, event) -> None:
        """
        멀티 뷰어 종료 시 각 싱글 뷰어의 스레드 종료 후 창 닫음
        """
        for w in self.__widget_data.values():
            w: multiple_viewer_parent.VideoWidget
            if w.update_thread.isRunning():
                w.slot_stop_video()
                w.update_thread.stop()
            print(f"\033[31m스레드 정상 종료: {w.wid}\033[0m")
        event.accept()

    def keyPressEvent(self, event) -> None:
        """
        :param event: 키보드 입력 시 발생하는 이벤트
        키보드 입력에 따른 이벤트 처리
        """
        if event.key() in [QtCore.Qt.Key_Right, QtCore.Qt.Key_L]:
            self.__btn_play.click()
        elif event.key() in [QtCore.Qt.Key_Down, QtCore.Qt.Key_K]:
            self.__btn_pause.click()
        elif event.key() in [QtCore.Qt.Key_Left, QtCore.Qt.Key_J]:
            self.__btn_stop.click()
        elif event.key() == QtCore.Qt.Key_M:
            self.__btn_mode.click()
        elif event.key() == QtCore.Qt.Key_P:
            self.__btn_loop.click()

    def __connections(self) -> None:
        """
        UI 상호작용 시 발생하는 시그널을 슬롯에 연결
        """
        self.__btn_play.clicked.connect(self.__slot_play_all)
        self.__btn_pause.clicked.connect(self.__slot_pause_all)
        self.__btn_stop.clicked.connect(self.__slot_stop_all)
        self.__btn_mode.clicked.connect(self.__slot_change_dp)
        self.__btn_loop.clicked.connect(self.__slot_set_loop)

    def __setup_ui(self) -> None:
        """
        멀티 뷰어 UI 세팅 및 메인 위젯 설정
        """
        self.setWindowTitle("Multiple Viewer")
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
        self.__btn_play.setFocusPolicy(QtCore.Qt.NoFocus)
        self.__btn_pause.setFocusPolicy(QtCore.Qt.NoFocus)
        self.__btn_stop.setFocusPolicy(QtCore.Qt.NoFocus)
        self.__btn_mode.setFocusPolicy(QtCore.Qt.NoFocus)
        self.__btn_loop.setFocusPolicy(QtCore.Qt.NoFocus)

        self.__btn_loop.setCheckable(True)
        self.__btn_loop.setChecked(False)

        # spacer
        __h_spacer = QtWidgets.QSpacerItem(
            260, 30, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )

        __h_line = QtWidgets.QFrame()
        __h_line.setFrameShape(QtWidgets.QFrame.HLine)
        __h_line.setFrameShadow(QtWidgets.QFrame.Sunken)

        btn_hbox = QtWidgets.QHBoxLayout()
        btn_hbox.addItem(__h_spacer)
        btn_hbox.addWidget(self.__btn_play)
        btn_hbox.addWidget(self.__btn_pause)
        btn_hbox.addWidget(self.__btn_stop)
        btn_hbox.addWidget(self.__btn_mode)
        btn_hbox.addWidget(self.__btn_loop)

        self.__vbox_layout.addLayout(self.__grid_layout)
        self.__vbox_layout.addWidget(__h_line)
        self.__vbox_layout.addLayout(btn_hbox)

        self.setLayout(self.__vbox_layout)

    def __setup_widgets(self) -> None:
        """
        플레이리스트의 수 만큼 뷰어를 구성하여 UI생성 및 재배치
        """
        for idx, v_path in enumerate(self.__play_lst):
            self.widget = multiple_viewer_parent.VideoWidget(v_path)
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
            if len(self.__play_lst) == 2:
                self.widget.label_path.setFont(QtGui.QFont("Sans Serif", 10))
                self.widget.label_fps.setFont(QtGui.QFont("Sans Serif", 10))
                self.__grid_layout.addWidget(self.__frame, int(idx // 2), int(idx % 2))
                self.setFixedSize(1211, 495)
            elif 2 < len(self.__play_lst) <= 4:
                self.widget.label_path.setFont(QtGui.QFont("Sans Serif", 10))
                self.widget.label_fps.setFont(QtGui.QFont("Sans Serif", 10))
                self.__grid_layout.addWidget(self.__frame, int(idx // 2), int(idx % 2))
                self.setFixedSize(1026, 828)
            elif 4 < len(self.__play_lst) <= 6:
                self.widget.label_path.setFont(QtGui.QFont("Sans Serif", 9))
                self.widget.label_fps.setFont(QtGui.QFont("Sans Serif", 9))
                self.widget.label_remain_time.setFont(QtGui.QFont("Sans Serif", 7))
                self.widget.label_current_time.setFont(QtGui.QFont("Sans Serif", 7))
                self.__grid_layout.addWidget(self.__frame, int(idx // 3), int(idx % 3))
                self.setFixedSize(1416, 787)
            elif 6 < len(self.__play_lst) <= 9:
                self.widget.label_path.setFont(QtGui.QFont("Sans Serif", 9))
                self.widget.label_fps.setFont(QtGui.QFont("Sans Serif", 9))
                self.widget.label_remain_time.setFont(QtGui.QFont("Sans Serif", 7))
                self.widget.label_current_time.setFont(QtGui.QFont("Sans Serif", 7))
                self.__grid_layout.addWidget(self.__frame, int(idx // 3), int(idx % 3))
                self.setFixedSize(1170, 962)
            elif 9 < len(self.__play_lst):
                self.widget.label_path.setFont(QtGui.QFont("Sans Serif", 8))
                self.widget.label_fps.setFont(QtGui.QFont("Sans Serif", 8))
                self.widget.label_remain_time.setFont(QtGui.QFont("Sans Serif", 6))
                self.widget.label_current_time.setFont(QtGui.QFont("Sans Serif", 6))
                self.__grid_layout.addWidget(self.__frame, int(idx // 4), int(idx % 4))
                self.setFixedSize(1452, 970)

        # 각 행과 열의 간격을 동일하게 설정
        rows = self.__grid_layout.rowCount()
        for row in range(rows):
            self.__grid_layout.setRowStretch(row, 1)
        cols = self.__grid_layout.columnCount()
        for col in range(cols):
            self.__grid_layout.setColumnStretch(col, 1)

    def __slot_set_loop(self) -> None:
        """
        멀티 뷰어의 loop 버튼 클릭 시 모든 싱글 뷰어의 loop버튼 동작
        """
        if self.__btn_loop.isChecked():
            for w in self.__widget_data.values():
                w: multiple_viewer_parent.VideoWidget
                w.btn_loop.setChecked(True)
        else:
            for w in self.__widget_data.values():
                w: multiple_viewer_parent.VideoWidget
                w.btn_loop.setChecked(False)

    def __slot_change_dp(self) -> None:
        """
        멀티 뷰어의 표시 형식 버튼 클릭 시 모든 표시 형식 버튼 동작
        """
        if self.__btn_mode.text() == "fps":
            self.__btn_mode.setText("tc")
        elif self.__btn_mode.text() == "tc":
            self.__btn_mode.setText("fps")

        for w in self.__widget_data.values():
            w: multiple_viewer_parent.VideoWidget
            if self.__btn_mode.text() == "tc":
                w.btn_mode.setText("tc")
            elif self.__btn_mode.text() == "fps":
                w.btn_mode.setText("fps")

    def __slot_play_all(self) -> None:
        """
        멀티 뷰어의 play 버튼 클릭 시 모든 싱글 뷰어 재생
        """
        for w in self.__widget_data.values():
            w: multiple_viewer_parent.VideoWidget
            w.player.play()

    def __slot_pause_all(self) -> None:
        """
        멀티 뷰어의 pause 버튼 클릭 시 모든 싱글 뷰어 일시정지
        """
        for w in self.__widget_data.values():
            w: multiple_viewer_parent.VideoWidget
            w.player.pause()

    def __slot_stop_all(self) -> None:
        """
        멀티 뷰어의 stop 버튼 클릭 시 모든 싱글 뷰어 정지
        """
        for w in self.__widget_data.values():
            w: multiple_viewer_parent.VideoWidget
            w.player.stop()


# TEST
test_list = [
    "/home/rapa/Downloads/test1.MOV",
    "/home/rapa/Downloads/test2.MOV",
    "/home/rapa/Downloads/test_1280 (copy).mp4",
    "/home/rapa/Downloads/test_1280 (another copy).mp4",
    "/home/rapa/Downloads/test_1280 (another copy).mp4",
    "/home/rapa/Downloads/test_1280 (another copy).mp4",
    "/home/rapa/Downloads/test_1280 (another copy).mp4",
    "/home/rapa/Downloads/test_1280 (another copy).mp4",
    "/home/rapa/Downloads/test_1280 (another copy).mp4",
    "/home/rapa/Downloads/test_1280 (another copy).mp4",
]
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mv = MultipleViewer(test_list)
    mv.show()
    app.exec_()
