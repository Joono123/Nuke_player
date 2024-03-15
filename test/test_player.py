#!/usr/bin/env python
# encoding=utf-8

# author        : Juno Park
# created date  : 2024.03.04
# modified date : 2024.03.04
# description   :


import sys
from PySide2 import QtWidgets, QtCore, QtGui, QtMultimediaWidgets, QtMultimedia
from library.qt import library as qt_lib


class VideoWidget(QtWidgets.QWidget):
    def __init__(self, playlist: list[str]):
        super().__init__()
        self.setWindowTitle("Video Player")
        qt_lib.QtLibs.center_on_screen(self)
        self.init_ui()
        self.connections()
        self.__playlist = playlist

    def init_ui(self):
        self.setStyleSheet("color: rgb(255, 255, 255);"
                           "background-color: rgb(70, 70, 70);")
        self.player = QtMultimedia.QMediaPlayer(None, QtMultimedia.QMediaPlayer.VideoSurface)
        self.play_lst = QtMultimedia.QMediaPlaylist()
        self.__add_play_lst(self.play_lst)
        self.player.setPlaylist(self.play_lst)

        v_widget = QtMultimediaWidgets.QVideoWidget()
        v_widget.setFixedSize(800, 450)
        v_widget.setStyleSheet('background-color: rgb(0, 0, 0);')

        # btns
        self.btn_open = QtWidgets.QPushButton()
        self.btn_open.setFixedSize(50, 25)
        self.btn_play = QtWidgets.QPushButton()
        self.btn_stop = QtWidgets.QPushButton()
        self.btn_stop.setEnabled(False)
        self.btn_play.setEnabled(False)
        self.btn_open.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DirOpenIcon))
        self.btn_play.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        self.btn_stop.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaStop))

        # slider
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setRange(0, 0)

        # label
        font = QtGui.QFont("Sans Serif", 8)
        self.label_remain_time = QtWidgets.QLabel()
        self.label_remain_time.setAlignment(QtCore.Qt.AlignCenter)
        # self.label_remain_time.setFixedWidth(60)
        self.label_remain_time.setText("00:00:00")
        self.label_remain_time.setFont(font)
        self.label_current_time = QtWidgets.QLabel()
        self.label_current_time.setAlignment(QtCore.Qt.AlignCenter)
        # self.label_current_time.setFixedWidth(125)
        self.label_current_time.setText("00:00:00 / 00:00:00")
        self.label_current_time.setFont(font)

        hbox = QtWidgets.QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)

        hbox.addWidget(self.btn_open)
        hbox.addWidget(self.btn_play)
        hbox.addWidget(self.btn_stop)
        hbox.addWidget(self.label_current_time)
        hbox.addWidget(self.slider)
        hbox.addWidget(self.label_remain_time)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(v_widget)
        vbox.addLayout(hbox)

        self.player.setVideoOutput(v_widget)

        self.setLayout(vbox)

    def connections(self):
        self.btn_open.clicked.connect(self.open_file)
        self.btn_play.clicked.connect(self.play_video)
        self.btn_stop.clicked.connect(self.stop_video)
        self.player.stateChanged.connect(self.state_changed)
        self.player.positionChanged.connect(self.pos_changed)
        self.player.durationChanged.connect(self.duration_changed)
        self.slider.sliderMoved.connect(self.set_pos)

    def __add_play_lst(self, playlist: list[str]):
        for f_path in playlist:
            f_info = QtCore.QFileInfo(f_path)
            if f_info.exists():
                url = QtCore.QUrl.fromLocalFile(f_info.absoluteFilePath())
                self.play_lst.addMedia(QtMultimedia.QMediaContent(url))
                print(f"플레이 리스트: {self.play_lst}")

    def closeEvent(self, event):
        if self.player.state() in [QtMultimedia.QMediaPlayer.PlayingState,
                                   QtMultimedia.QMediaPlayer.PausedState]:
            self.player.stop()
            print('Player Stopped')
        event.accept()

    def open_file(self):
        filename, etc = QtWidgets.QFileDialog.getOpenFileName(self, "Open Video")

        if filename != '':
            self.player.setMedia(QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(filename)))
            self.btn_play.setEnabled(True)
            self.btn_play.setStyleSheet("background-color: rgb(80,80,80);")
            self.btn_stop.setEnabled(True)
            self.btn_stop.setStyleSheet("background-color: rgb(80,80,80);")
            print(f'Loaded: {filename}')

    def stop_video(self):
        self.slider.setValue(0)
        self.player.stop()

    def play_video(self):
        if self.player.state() == QtMultimedia.QMediaPlayer.PlayingState:
            self.player.pause()

        else:
            self.player.play()

    def state_changed(self, ste):
        if self.player.state() == QtMultimedia.QMediaPlayer.PlayingState:
            self.btn_play.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause))

        else:
            self.btn_play.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))

    def pos_changed(self, pos):
        self.slider.setValue(pos)
        self.update_remain_time()

    def duration_changed(self, duration):
        self.slider.setRange(0, duration)

    def set_pos(self, pos):
        self.player.setPosition(pos)

    def update_remain_time(self):
        total_duration = self.player.duration()
        current_pos = self.player.position()
        remain_time = total_duration - current_pos

        remain_time_str = QtCore.QTime(0, 0).addMSecs(remain_time).toString("hh:mm:ss")
        current_time_str = QtCore.QTime(0, 0).addMSecs(current_pos).toString("hh:mm:ss")
        total_time_str = QtCore.QTime(0, 0).addMSecs(total_duration).toString("hh:mm:ss")
        self.label_remain_time.setText(remain_time_str)
        self.label_current_time.setText(current_time_str + '/' + total_time_str)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    vid = VideoWidget(['/home/rapa/Downloads/test2.MOV'])
    vid.show()
    sys.exit(app.exec_())
