#!/usr/bin/env python
# encoding=utf-8
# author        : Juno Park
# created date  : 2024.02.26
# modified date : 2024.02.26
# description   : subprocess 및 ffmpeg을 활용한 썸네일 제작 VLC로 영상 재생

# ffmpeg 모듈 설치: https://computingforgeeks.com/how-to-install-ffmpeg-on-centos-rhel-8/#google_vignette
# ffmpeg-python : pip install ffmpeg-python

import sys
import os.path
import subprocess

sys.path.append("/home/rapa/anaconda3/lib/python3.11/site-packages")
import ffmpeg

sys.path.append("/home/rapa/anaconda3/lib/python3.11/site-packages")
import cv2
import time
from PySide2 import QtWidgets, QtCore, QtGui, QtMultimediaWidgets, QtMultimedia

sys.path.append("/home/rapa/workspace/python/Nuke_player")
from library.qt import library as qt_lib


class NP_Utils:
    def __init__(self):
        pass

    @staticmethod
    def extract_thumbnail(video_path: str, output_path: str, size: str):
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"File {video_path} not found.")
        (
            ffmpeg.input(video_path, ss="00:00:01")
            .filter("scale", size)
            .output(output_path, vframes=1)
            .run(capture_stdout=True, capture_stderr=True)
        )

    @staticmethod
    def extract_thumbnail_subprocess(video_path: str, output_path: str, size: str):
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"File {video_path} not found.")

        cmd = [
            "ffmpeg",
            "-ss",
            "00:00:01",
            "-i",
            video_path,
            "-vf",
            f"scale={size}",
            "-vframes",
            "1",
            output_path,
        ]

        # ffmpeg 실행
        try:
            subprocess.run(cmd, capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")

    @staticmethod
    def make_dir(dir_path: str):
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"\033[32m" f"임시 디렉토리 '{dir_path}'가 생성되었습니다" f"\033[0m")
        else:
            pass

    @staticmethod
    def open_with_vlc(video_path: str, vlc_path: str = "/usr/bin/vlc"):
        if not os.path.exists(vlc_path):
            raise FileNotFoundError(f"VLC doesn't exist current path.")
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"File {video_path} not found")
        subprocess.Popen([vlc_path, video_path], shell=True)

    @staticmethod
    def get_video_fps(video_path: str):
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        return fps


###########################################################################################


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
        self.running = False


class VideoPlayerThread(QtCore.QThread):
    video_loaded = QtCore.Signal()
    video_finished = QtCore.Signal()

    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path
        self.player = QtMultimedia.QMediaPlayer(
            None, QtMultimedia.QMediaPlayer.VideoSurface
        )
        self.player.setMedia(
            QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(video_path))
        )
        self.player.mediaStatusChanged.connect(self.handle_media_status_changed)

    def run(self):
        self.player.play()

    def handle_media_status_changed(self, status):
        if status == QtMultimedia.QMediaPlayer.LoadedMedia:
            self.video_loaded.emit()
        elif status == QtMultimedia.QMediaPlayer.EndOfMedia:
            self.video_finished.emit()


class VideoWidget(QtWidgets.QWidget):
    def __init__(self, playlist: list[str], parent=None):
        super().__init__(parent)

        # vars
        self.playlst = playlist
        self.video_threads = list()

        # Set UI
        self.setWindowTitle("Nuke Player")

        self.__init_ui()
        self.__connections()
        self.current_fps = self.__get_current_video_fps()

        self.__player.play()

    def __init_ui(self):
        self.setStyleSheet(
            "color: rgb(255, 255, 255);" "background-color: rgb(70, 70, 70);"
        )

        # 플레이어 설정
        self.__player = QtMultimedia.QMediaPlayer(
            None, QtMultimedia.QMediaPlayer.VideoSurface
        )

        # 플레이 리스트 등록
        self.__play_lst = QtMultimedia.QMediaPlaylist()
        self.__add_play_lst(self.playlst)
        self.__player.setPlaylist(self.__play_lst)

        # 위젯 설정
        self.overlay_widget = QtWidgets.QWidget()
        v_widget = QtMultimediaWidgets.QVideoWidget()
        v_widget.setMinimumSize(800, 450)
        v_widget.setStyleSheet("background-color: rgb(0, 0, 0);")

        # fonts
        font = QtGui.QFont("Sans Serif", 8)
        font2 = QtGui.QFont("Sans Serif", 9)
        font2.setBold(True)

        # btns
        self.__btn_open = QtWidgets.QPushButton()
        self.__btn_open.setFixedSize(50, 25)
        self.__btn_play = QtWidgets.QPushButton()
        self.__btn_stop = QtWidgets.QPushButton()
        self.__btn_next = QtWidgets.QPushButton()
        self.__btn_prev = QtWidgets.QPushButton()
        self.__btn_mode = QtWidgets.QPushButton("time")
        self.__btn_mode.setFont(font)
        self.__btn_mode.setFixedSize(35, 25)
        self.__btn_open.setFocusPolicy(QtCore.Qt.NoFocus)
        self.__btn_play.setFocusPolicy(QtCore.Qt.NoFocus)
        self.__btn_next.setFocusPolicy(QtCore.Qt.NoFocus)
        self.__btn_prev.setFocusPolicy(QtCore.Qt.NoFocus)
        self.__btn_stop.setFocusPolicy(QtCore.Qt.NoFocus)
        self.__btn_mode.setFocusPolicy(QtCore.Qt.NoFocus)
        self.__btn_open.setIcon(
            self.style().standardIcon(QtWidgets.QStyle.SP_DirOpenIcon)
        )
        self.__btn_play.setIcon(
            self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay)
        )
        self.__btn_stop.setIcon(
            self.style().standardIcon(QtWidgets.QStyle.SP_MediaStop)
        )
        self.__btn_next.setIcon(
            self.style().standardIcon(QtWidgets.QStyle.SP_MediaSkipForward)
        )
        self.__btn_prev.setIcon(
            self.style().standardIcon(QtWidgets.QStyle.SP_MediaSkipBackward)
        )

        # slider
        self.__slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.__slider.setRange(0, 0)
        self.__slider.setFocusPolicy(QtCore.Qt.NoFocus)

        # label
        self.__label_remain_time = QtWidgets.QLabel()
        self.__label_remain_time.setAlignment(QtCore.Qt.AlignCenter)
        self.__label_remain_time.setText("00:00:00")
        self.__label_remain_time.setFont(font)

        self.__label_current_time = QtWidgets.QLabel()
        self.__label_current_time.setAlignment(QtCore.Qt.AlignCenter)
        self.__label_current_time.setText("00:00:00 / 00:00:00")
        self.__label_current_time.setFont(font)

        self.__label_filename = QtWidgets.QLabel("Current File: ")
        self.__label_filename.setFont(font2)
        self.h_spacer = QtWidgets.QSpacerItem(
            200, 25, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        self.__label_dp_idx = QtWidgets.QLabel(f"1 / {len(self.playlst)}")
        self.__label_dp_idx.setFont(font2)

        # layout
        hbox = QtWidgets.QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(self.__btn_open)
        hbox.addWidget(self.__btn_prev)
        hbox.addWidget(self.__btn_play)
        hbox.addWidget(self.__btn_stop)
        hbox.addWidget(self.__btn_next)
        hbox.addWidget(self.__label_current_time)
        hbox.addWidget(self.__slider)
        hbox.addWidget(self.__label_remain_time)
        hbox.addWidget(self.__btn_mode)
        hbox_2 = QtWidgets.QHBoxLayout()
        hbox_2.addWidget(self.__label_filename)
        hbox_2.addItem(self.h_spacer)
        hbox_2.addWidget(self.__label_dp_idx)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox_2)
        vbox.addWidget(v_widget)
        vbox.addLayout(hbox)

        self.__player.setVideoOutput(v_widget)

        self.setLayout(vbox)

        self.__update_file_path_label()

    def __connections(self):
        self.__btn_open.clicked.connect(self.__slot_open_file)
        self.__btn_play.clicked.connect(self.__slot_play_video)
        self.__btn_stop.clicked.connect(self.__slot_stop_video)
        self.__btn_next.clicked.connect(self.__slot_next_video)
        self.__btn_prev.clicked.connect(self.__slot_prev_video)
        self.__btn_mode.clicked.connect(self.__slot_dp_mode)

        self.__player.stateChanged.connect(self.__slot_state_changed)
        self.__player.positionChanged.connect(self.__slot_pos_shanged)
        self.__player.durationChanged.connect(self.__slot_duration_changed)

        self.__slider.sliderMoved.connect(self.__slot_slider_moved)
        # self.__slider.sliderPressed.connect(self.__slot_slider_pressed)

        self.__play_lst.currentIndexChanged.connect(self.__update_file_path_label)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() in [QtCore.Qt.Key_Space, QtCore.Qt.Key_Up, QtCore.Qt.Key_K]:
            # self.__btn_play.click()
            self.__slot_play_video()
        elif event.key() in [QtCore.Qt.Key_Right, QtCore.Qt.Key_L]:
            # self.__btn_next.click()
            self.__slot_next_video()
        elif event.key() in [QtCore.Qt.Key_Left, QtCore.Qt.Key_J]:
            # self.__btn_prev.click()
            self.__slot_prev_video()
        elif event.key() in [QtCore.Qt.Key_Down, QtCore.Qt.Key_Q]:
            # self.__btn_stop.click()
            self.__slot_stop_video()
        else:
            event.ignore()

    def closeEvent(self, event):
        if self.__player.state() in [
            QtMultimedia.QMediaPlayer.PlayingState,
            QtMultimedia.QMediaPlayer.PausedState,
        ]:
            self.__player.stop()
            self.__slider_updater.stop()
            self.__slider_updater.wait()
            print("\033[32m스레드 정상 종료\033[0m")
        event.accept()

    def resizeEvent(self, event):
        pass

    def __get_current_video_fps(self):
        current_media = self.__player.currentMedia()
        if current_media.isNull():
            print("\033[31mERROR: 현재 미디어가 없음\033[0m")
        else:
            current_url = current_media.canonicalUrl().toLocalFile()
            # print(current_url)
            fps = round(self.__NP_Util.get_video_fps(current_url), 3)
            # print(f"fps: {fps}")
            return fps

    def __add_play_lst(self, playlist: list[str]):
        for f_path in playlist:
            f_info = QtCore.QFileInfo(f_path)
            if f_info.exists():
                url = QtCore.QUrl.fromLocalFile(f_info.absoluteFilePath())
                self.__play_lst.addMedia(QtMultimedia.QMediaContent(url))
        print(f"\033[32m플레이 리스트: {playlist}\033[0m")

    @QtCore.Slot(int)
    def __update_slider_position(self, position):
        self.__slider.setValue(position)

    def __update_file_path_label(self):
        current_file = self.playlst[self.__play_lst.currentIndex()]
        self.__label_filename.setText(f"Current File: {current_file}")

    def __slot_dp_mode(self):
        if self.__btn_mode.text() == "fps":
            self.__btn_mode.setText("time")
            # print("출력 형식: 시간")
        else:
            self.__btn_mode.setText("fps")
            # current_media = self.__player.currentMedia()
            # url = current_media.canonicalUrl().toLocalFile()
            # fps = round(self.__NP_Util.get_video_fps(url), 3)
            # print(f"출력 형식: {fps}프레임")

    def __slot_open_file(self):
        filename, etc = QtWidgets.QFileDialog.getOpenFileName(self, "Open Video")

        if filename != "":
            self.__player.setMedia(
                QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(filename))
            )
            self.__btn_play.setEnabled(True)
            self.__btn_play.setStyleSheet("background-color: rgb(80,80,80);")
            self.__btn_stop.setEnabled(True)
            self.__btn_stop.setStyleSheet("background-color: rgb(80,80,80);")
            print(f"Loaded: {filename}")

    def __slot_next_video(self):
        current_idx = self.__play_lst.currentIndex()
        if self.__play_lst.currentIndex() < len(self.playlst) - 1:
            self.__play_lst.setCurrentIndex(current_idx + 1)
            self.current_fps = self.__get_current_video_fps()
            self.__dp_idx += 1
            self.__label_dp_idx.setText(f"{self.__dp_idx} / {len(self.playlst)}")
            # print("다음 영상을 재생합니다.")
            # self.__player.play()
            self.__player.setPosition(0)
        else:
            print("\033[31mERROR: 재생 목록의 마지막 영상입니다.\033[0m")
            return

    def __slot_prev_video(self):
        current_idx = self.__play_lst.currentIndex()
        current_pos: int = self.__player.position()
        current_time: QtCore.QTime = QtCore.QTime(0, 0).addMSecs(current_pos)
        if self.__play_lst.currentIndex() > 0:
            if 0 < current_time.second():
                self.__player.stop()
                self.__player.play()
                return
                # print("영상의 맨 앞으로 이동합니다.")
            else:
                self.__play_lst.setCurrentIndex(current_idx - 1)
                self.current_fps = self.__get_current_video_fps()
                self.__dp_idx -= 1
                self.__label_dp_idx.setText(f"{self.__dp_idx} / {len(self.playlst)}")
                # print("이전 영상을 재생합니다.")
                # self.__player.play()
        else:
            if 0 < current_time.second():
                self.__player.stop()
                self.__player.play()
                # print("영상의 맨 앞으로 이동합니다.")
            else:
                print("\033[31mERROR: 재생 목록의 첫 번째 영상입니다.\033[0m")
                self.__player.setPosition(0)
                self.__player.pause()
                self.__slider.setValue(0)

    def __slot_stop_video(self):
        self.__player.setPosition(0)
        self.__player.stop()
        # print("정지")

    def __slot_play_video(self):
        if self.__player.state() == QtMultimedia.QMediaPlayer.PlayingState:
            self.__player.pause()
            # print("일시정지")
        else:
            self.__player.play()
            # print("재생")

    def __slot_state_changed(self, ste):
        if ste == QtMultimedia.QMediaPlayer.PlayingState:
            self.__btn_play.setIcon(
                self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause)
            )

        else:
            self.__btn_play.setIcon(
                self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay)
            )

    def __slot_pos_shanged(self, pos):
        self.__slider.setValue(pos)

    def __slot_duration_changed(self, duration):
        self.__slider.setRange(0, duration)
        # self.__player.pause()

    def __slot_slider_pressed(self):
        pos = self.__slider.value()
        self.__player.setPosition(pos)

    def __slot_slider_moved(self, pos):
        self.__player.setPosition(pos)

    def __slot_label_info(self):
        # 플레이어의 포지션 값
        total_pos = self.__player.duration()
        current_pos = self.__player.position()
        remain_pos = total_pos - current_pos + 1000

        # 포지션 값을 QTime으로 변환
        total_time = QtCore.QTime(0, 0).addMSecs(total_pos)
        current_time = QtCore.QTime(0, 0).addMSecs(current_pos)
        remain_time = QtCore.QTime(0, 0).addMSecs(remain_pos)

        # 포지션 값을 프레임 단위로 변환
        total_frames = int((total_pos / 1000) * self.current_fps)
        current_frames = int((current_pos / 1000) * self.current_fps)
        remain_frames = total_frames - current_frames

        # QTime값을 시간:분:초 형식으로 변환
        total_time_str = total_time.toString("hh:mm:ss")
        current_time_str = current_time.toString("hh:mm:ss")
        remain_time_str = remain_time.toString("hh:mm:ss")

        if self.__btn_mode.text() == "fps":
            self.__label_remain_time.setText(str(remain_frames))
            self.__label_current_time.setText(f"{current_frames} / {total_frames}")
        elif self.__btn_mode.text() == "time":
            self.__label_remain_time.setText(remain_time_str)
            self.__label_current_time.setText(f"{current_time_str} / {total_time_str}")


t_path = ["/home/rapa/Downloads/test1.MOV"]

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    vid = VideoWidget(t_path)
    vid.show()
    sys.exit(app.exec_())
