import sys
import os
import time

sys.path.append("/home/rapa/libs_nuke")
import cv2
import uuid
from PySide2 import QtWidgets, QtGui, QtMultimediaWidgets, QtCore, QtMultimedia
from library import NP_Utils
from library.qt import library as qt_lib


class Thread_Updater(QtCore.QThread):
    pos_updated = QtCore.Signal(int)
    dur_updated = QtCore.Signal(int)

    def __init__(self, player: QtMultimedia.QMediaPlayer, widget):
        super().__init__()
        self.player = player
        self.widget = widget
        self.running = True
        self.mutex = QtCore.QMutex()

    def run(self):
        pos = 0
        dur = 0
        while self.running:
            self.mutex.lock()
            if self.player.state() == QtMultimedia.QMediaPlayer.PlayingState:
                pos = self.player.position()
                dur = self.player.duration()
            self.mutex.unlock()
            self.pos_updated.emit(pos)
            self.dur_updated.emit(dur)
            time.sleep(0.01)

    def stop(self):
        if self.running:
            self.running = False
            self.quit()
            self.wait(10000)


# 파일 경로를 받아 영상을 재생
class VideoWidget(QtWidgets.QWidget):
    mode_changed = QtCore.Signal(str)
    update_slider_pos = QtCore.Signal(int, int)

    def __init__(self, video_path: str, parent=None):
        super().__init__(parent)

        # vars
        self.__wid = uuid.uuid4().hex
        self.__video_path = video_path
        self.__NP_Util = NP_Utils

        # Set UI
        self.setWindowTitle("Nuke Player")
        qt_lib.QtLibs.center_on_screen(self)

        self.__init_ui()
        self.__connections()
        self.__current_fps = self.__get_current_video_fps()

        # self.player.play()

        # Set Thread
        self.update_thread = Thread_Updater(self.player, self)
        self.update_thread.pos_updated.connect(self.__update_slider_position)
        self.update_thread.dur_updated.connect(self.slot_label_info)
        self.update_thread.start()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            # print(event.mimeData().urls())
            # self.__overlay_frame.hide()
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            # self.__overlay_frame.hide()
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            # self.setCursor(self.custom_cursor)
            # print(event.mimeData().urls())
            # self.__overlay_frame.show()
            event.acceptProposedAction()
        else:
            event.ignore()

    # def dragLeaveEvent(self, event):
    #     self.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
    #     self.__overlay_frame.show()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            drag = QtGui.QDrag(self)
            mime_data = QtCore.QMimeData()
            mime_data.setUrls([QtCore.QUrl(self.__video_path)])
            drag.setMimeData(mime_data)
            drag.exec_(QtCore.Qt.CopyAction)
            # self.setCursor(self.custom_cursor)

    # def mouseReleaseEvent(self, event):
    #     if event.button() == QtCore.Qt.LeftButton:
    #         self.__overlay_frame.hide()

    def closeEvent(self, event):
        self.player.stop()
        self.update_thread.stop()
        print(f"\033[31m스레드 정상 종료: {self.__wid}\033[0m")
        event.accept()

    def __init_ui(self):
        self.setStyleSheet(
            "color: rgb(255, 255, 255);" "background-color: rgb(70, 70, 70);"
        )
        self.setAcceptDrops(True)

        # 플레이어 설정
        self.player = QtMultimedia.QMediaPlayer(
            None, QtMultimedia.QMediaPlayer.VideoSurface
        )

        # 플레이 리스트 등록
        self.__play_lst = QtMultimedia.QMediaPlaylist()
        self.__add_play_lst()
        self.player.setPlaylist(self.__play_lst)

        # 위젯 설정
        v_widget = QtMultimediaWidgets.QVideoWidget()
        self.setMinimumSize(400, 225)
        v_widget.setStyleSheet("background-color: rgb(0, 0, 0);")

        # fonts
        font = QtGui.QFont("Sans Serif", 8)
        font2 = QtGui.QFont("Sans Serif", 9)
        font3 = QtGui.QFont("Sans Serif", 15)
        font2.setBold(True)

        # cursor
        self.label_cursor = QtWidgets.QLabel("Custom Cursor")
        self.label_cursor.setStyleSheet("color: white; background-color: black;")
        self.label_cursor.setAlignment(QtCore.Qt.AlignCenter)

        pixmap = QtGui.QPixmap(100, 50)
        pixmap.fill(QtCore.Qt.transparent)

        painter = QtGui.QPainter(pixmap)
        self.label_cursor.render(painter, QtCore.QPoint(0, 0))
        painter.end()

        # 커스텀 커서 생성
        self.custom_cursor = QtGui.QCursor(pixmap)

        # 일반 커서 설정
        self.setCursor(QtCore.Qt.ArrowCursor)

        # btns
        self.__btn_play = QtWidgets.QPushButton()
        self.__btn_stop = QtWidgets.QPushButton()
        self.btn_mode = QtWidgets.QPushButton("tc")
        self.btn_loop = QtWidgets.QPushButton()
        self.btn_fullscreen = QtWidgets.QPushButton()
        self.__btn_play.setIcon(
            self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay)
        )
        self.__btn_stop.setIcon(
            self.style().standardIcon(QtWidgets.QStyle.SP_MediaStop)
        )
        self.btn_loop.setIcon(
            self.style().standardIcon(QtWidgets.QStyle.SP_BrowserReload)
        )
        self.btn_fullscreen.setIcon(
            QtGui.QIcon(
                "/home/rapa/workspace/python/Nuke_player/resource/png/detach_screen.png"
            )
        )
        self.btn_mode.setFont(font)
        self.btn_mode.setFixedSize(25, 25)
        self.btn_loop.setFixedSize(25, 25)
        self.btn_fullscreen.setFixedSize(25, 25)

        self.btn_loop.setCheckable(True)
        self.btn_loop.setChecked(False)

        # labels
        self.label_frame = QtWidgets.QFrame()
        self.label_frame.setFrameShape(QtWidgets.QFrame.Panel)
        self.label_frame.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.label_frame.setLineWidth(2)
        self.label_frame.setLayout(QtWidgets.QHBoxLayout())
        self.label_path = QtWidgets.QLabel()
        self.label_path.setText(f"Current File: {os.path.basename(self.__video_path)}")
        label_spacer = QtWidgets.QSpacerItem(
            200, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        self.label_fps = QtWidgets.QLabel()
        self.label_fps.setText(f"{self.__get_current_video_fps()}fps")

        self.label_frame.layout().addWidget(self.label_path)
        self.label_frame.layout().addItem(label_spacer)
        self.label_frame.layout().addWidget(self.label_fps)

        self.label_remain_time = QtWidgets.QLabel()
        self.label_remain_time.setAlignment(QtCore.Qt.AlignCenter)
        self.label_remain_time.setText("00:00:00")
        self.label_remain_time.setFont(font)

        self.label_current_time = QtWidgets.QLabel()
        self.label_current_time.setAlignment(QtCore.Qt.AlignCenter)
        self.label_current_time.setText("00:00:00 / 00:00:00")
        self.label_current_time.setFont(font)

        # Overlay Frame(test)
        # label_overlay = QtWidgets.QLabel("Drop on NUKE")
        # label_overlay.setFont(font3)
        self.__overlay_frame = QtWidgets.QFrame(self)
        self.__overlay_frame.setLayout(QtWidgets.QVBoxLayout())
        self.__overlay_frame.layout().setAlignment(QtCore.Qt.AlignCenter)
        # self.__overlay_frame.layout().addWidget(label_overlay)
        self.__overlay_frame.setStyleSheet("background-color: rgba(50, 50, 255, 70);")
        self.__overlay_frame.setGeometry(v_widget.geometry())
        self.__overlay_frame.hide()

        # slider
        self.__slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.__slider.setRange(0, 0)

        self.checkbox = QtWidgets.QCheckBox()

        # 위젯이 포커스 되는 것을 막음
        self.__btn_play.setFocusPolicy(QtCore.Qt.NoFocus)
        self.__btn_stop.setFocusPolicy(QtCore.Qt.NoFocus)
        self.btn_mode.setFocusPolicy(QtCore.Qt.NoFocus)
        self.btn_loop.setFocusPolicy(QtCore.Qt.NoFocus)
        self.btn_fullscreen.setFocusPolicy(QtCore.Qt.NoFocus)
        self.checkbox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.__btn_play.setFocusPolicy(QtCore.Qt.NoFocus)
        self.__btn_stop.setFocusPolicy(QtCore.Qt.NoFocus)
        self.label_path.setFocusPolicy(QtCore.Qt.NoFocus)
        self.__slider.setFocusPolicy(QtCore.Qt.NoFocus)

        # layouts
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.__btn_play)
        hbox.addWidget(self.__btn_stop)
        hbox.addWidget(self.label_current_time)
        hbox.addWidget(self.__slider)
        hbox.addWidget(self.label_remain_time)
        hbox.addWidget(self.btn_loop)
        hbox.addWidget(self.btn_mode)
        hbox.addWidget(self.btn_fullscreen)
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.label_frame)
        vbox.addWidget(v_widget)
        vbox.addLayout(hbox)

        self.player.setVideoOutput(v_widget)
        self.setLayout(vbox)
        self.__overlay_frame.raise_()

    def __connections(self):
        self.__btn_play.clicked.connect(self.slot_play_video)
        self.__btn_stop.clicked.connect(self.slot_stop_video)
        self.btn_mode.clicked.connect(self.slot_changed_mode)
        self.btn_fullscreen.clicked.connect(self.slot_fullscreen)
        self.__slider.sliderMoved.connect(self.__slot_slider_moved)
        self.player.stateChanged.connect(self.__slot_state_changed)
        self.player.positionChanged.connect(self.__slot_pos_shanged)
        self.player.durationChanged.connect(self.__slot_duration_changed)

    def slot_fullscreen(self):
        # if not self.isFullScreen():
        #     self.showFullScreen()
        # else:
        #     self.showNormal()
        vw = self.__NP_Util.VideoWidget([self.__video_path])
        vw.show()

    def slot_stop_video(self):
        self.player.setPosition(0)
        self.player.stop()
        # print("정지")

    def slot_play_video(self):
        if self.player.state() == QtMultimedia.QMediaPlayer.PlayingState:
            self.player.pause()
            # print("일시정지")
        else:
            self.player.play()
            # print("재생")

    def __slot_state_changed(self, ste):
        # 영상이 끝난 경우, loop 버튼이 눌려 있으면 영상을 다시 재생함

        if ste == QtMultimedia.QMediaPlayer.PlayingState:
            self.__btn_play.setIcon(
                self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause)
            )
        else:
            self.__btn_play.setIcon(
                self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay)
            )
        if ste == QtMultimedia.QMediaPlayer.StoppedState:
            if self.btn_loop.isChecked():
                self.player.setPosition(0)
                self.player.play()
                self.__btn_play.setIcon(
                    self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause)
                )

    def __slot_slider_moved(self, pos):
        self.player.setPosition(pos)

    def __slot_pos_shanged(self, pos):
        self.__slider.setValue(pos)

    def __slot_duration_changed(self, duration):
        self.__slider.setRange(0, duration)

    def __add_play_lst(self):
        v_path = self.__video_path
        f_info = QtCore.QFileInfo(v_path)
        if f_info.exists():
            url = QtCore.QUrl.fromLocalFile(f_info.absoluteFilePath())
            self.__play_lst.addMedia(QtMultimedia.QMediaContent(url))
            print(f"\033[32m로딩 완료: {v_path}\033[0m")
        else:
            print(f"\033[31mERROR: 존재하지 않는 파일 >> {v_path}")

    @property
    def wid(self) -> str:
        return self.__wid

    @QtCore.Slot(int)
    def __update_slider_position(self, position):
        self.__slider.setValue(position)

    def slot_changed_mode(self):
        if self.btn_mode.text() == "tc":
            self.btn_mode.setText("fps")
        elif self.btn_mode.text() == "fps":
            self.btn_mode.setText("tc")

    @QtCore.Slot(int)
    def slot_label_info(self):
        # 플레이어의 포지션 값
        total_pos = self.player.duration()
        current_pos = self.player.position()
        remain_pos = total_pos - current_pos + 1000

        # 포지션 값을 QTime으로 변환
        total_time = QtCore.QTime(0, 0).addMSecs(total_pos)
        current_time = QtCore.QTime(0, 0).addMSecs(current_pos)
        remain_time = QtCore.QTime(0, 0).addMSecs(remain_pos)

        # 포지션 값을 프레임 단위로 변환
        total_frames = int((total_pos / 1000) * self.__current_fps)
        current_frames = int((current_pos / 1000) * self.__current_fps)
        remain_frames = total_frames - current_frames

        # QTime값을 시간:분:초 형식으로 변환
        total_time_str = total_time.toString("hh:mm:ss")
        current_time_str = current_time.toString("hh:mm:ss")
        remain_time_str = remain_time.toString("hh:mm:ss")

        if self.btn_mode.text() == "fps":
            self.label_remain_time.setText(str(remain_frames))
            self.label_current_time.setText(f"{current_frames} / {total_frames}")
        elif self.btn_mode.text() == "tc":
            self.label_remain_time.setText(remain_time_str)
            self.label_current_time.setText(f"{current_time_str} / {total_time_str}")

    def __get_current_video_fps(self):
        current_media = self.player.currentMedia()
        if current_media.isNull():
            print("\033[31mERROR: 현재 미디어가 없음\033[0m")
        else:
            current_url = current_media.canonicalUrl().toLocalFile()
            fps = round(self.get_video_fps(current_url), 3)
            return fps

    @staticmethod
    def get_video_fps(video_path: str):
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        return fps


test_path = "/home/rapa/Downloads/test1.MOV"

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    _vw = VideoWidget(test_path)
    _vw.show()
    app.exec_()
