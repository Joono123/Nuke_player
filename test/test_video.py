from PySide2 import QtWidgets, QtGui, QtCore, QtMultimediaWidgets, QtMultimedia


class VideoWidget(QtMultimediaWidgets.QVideoWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        palette = self.palette()
        palette.setColor(QtGui.QPalette.Window, QtCore.Qt.black)
        self.setPalette(palette)
        self.setAttribute(QtCore.Qt.WA_OpaquePaintEvent)


class VideoPlayer(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('To - Juno Park')
        self.__video_widget = VideoWidget(self)

        ###################################################
        self.__btn_open = QtWidgets.QPushButton('open')
        self.__btn_play = QtWidgets.QPushButton('play')
        self.__btn_stop = QtWidgets.QPushButton('stop')

        __hbox_layout_btns = QtWidgets.QHBoxLayout()
        __hbox_layout_btns.addWidget(self.__btn_open)
        __hbox_layout_btns.addWidget(self.__btn_play)
        __hbox_layout_btns.addWidget(self.__btn_stop)

        __vbox_layout = QtWidgets.QVBoxLayout()
        __vbox_layout.addWidget(self.__video_widget)
        __vbox_layout.addLayout(__hbox_layout_btns)

        self.setLayout(__vbox_layout)
        ###################################################

        self.__player = QtMultimedia.QMediaPlayer()
        self.__player.setVideoOutput(self.__video_widget)
        self.__playlist = QtMultimedia.QMediaPlaylist()
        self.__playlist.setCurrentIndex(0)
        self.__player.setPlaylist(self.__playlist)

        # connect
        self.__connections()

    def __connections(self):
        self.__btn_play.clicked.connect(self.__slot_play_btn)

    def closeEvent(self, event):
        if self.__player.state() in [QtMultimedia.QMediaPlayer.PlayingState, QtMultimedia.QMediaPlayer.PausedState]:
            self.__player.stop()
        event.accept()

    def __add_playlist(self, fpath_lst: list):
        for fpath in fpath_lst:
            finfo = QtCore.QFileInfo(fpath)
            if finfo.exists():
                url = QtCore.QUrl.fromLocalFile(finfo.absoluteFilePath())
                self.__playlist.addMedia(QtMultimedia.QMediaContent(url))
    @QtCore.Slot(bool)
    def __slot_play_btn(self):
        self.__add_playlist(['/home/rapa/Downloads/test_1280.mp4',])
        self.__player.play()
        print('play')


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    vp = VideoPlayer()
    vp.show()
    app.exec_()
