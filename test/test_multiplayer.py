from PySide2 import QtWidgets, QtGui, QtCore, QtMultimedia, QtMultimediaWidgets
from NP_libs.system import library as sys_lib
from NP_libs.qt import library as qt_lib


class MultiVideo_Thread(QtCore.QThread):
    def __init__(self, video_path):
        super().__init__()
        self.__video_path = video_path


class VideoPlayer(QtWidgets.QWidget):
    def __init__(self, playlist: list[str], parent=None):
        super().__init__(parent)

        self.__v_paths: list[str] = playlist
        self.setWindowTitle("Multi Player")
        self.setMinimumSize(1280, 720)
        self.vbox = QtWidgets.QVBoxLayout()

        qt_lib.QtLibs.center_on_screen(self)
        self.__set_font()
        self.__add_top_ui()
        # self.__init_ui()

        self.setLayout(self.vbox)

    # def __init_ui(self):
    #     for idx, video in enumerate(self.__v_paths):
    #         self.__player = QtMultimedia.QMediaPlayer(
    #             None, QtMultimedia.QMediaPlayer.VideoSurface
    #         )
    #         self.__playlist = QtMultimedia.QMediaPlaylist()
    #         self.__add_playlist(video)
    #         self.__player.setPlaylist(self.__playlist)
    #
    #         v_widget = QtMultimediaWidgets.QVideoWidget()
    #         v_widget.setMinimumSize(800, 450)
    #         v_widget.setStyleSheet("background-color: rgb(0, 0, 0);")
    #
    #         vbox = QtWidgets.QVBoxLayout()
    #         vbox.addWidget(v_widget)
    #
    #         self.__player.setVideoOutput(v_widget)
    #         self.setLayout(vbox)
    #         self.__player.play()

    def __set_font(self):
        self.font_1 = QtGui.QFont("Sans Serif", 12)
        self.font_1.setBold(True)
        self.font_2 = QtGui.QFont("Sans Serif", 9)
        self.font_3 = QtGui.QFont("Sans Serif", 7)

    def __add_top_ui(self):
        self.__label_title = QtWidgets.QLabel("Multiple Viewer")
        self.__label_title.setFont(self.font_1)
        self.__h_spacer = QtWidgets.QSpacerItem(
            200, 25, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        self.__label_cnt = QtWidgets.QLabel("10")
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.__label_title)
        hbox.addItem(self.__h_spacer)
        hbox.addWidget(self.__label_cnt)

        self.vbox.addLayout(hbox)

    def __add_playlist(self, video_path: str):
        v_info = QtCore.QFileInfo(video_path)
        if v_info.exists():
            url = QtCore.QUrl.fromLocalFile(v_info.absoluteFilePath())
            self.__playlist.addMedia(QtMultimedia.QMediaContent(url))


if __name__ == "__main__":
    playlist = ["/home/rapa/Downloads/test1.MOV", "/home/rapa/Downloads/test2.MOV"]
    app = QtWidgets.QApplication([])
    vp = VideoPlayer(playlist)
    vp.show()
    app.exec_()
