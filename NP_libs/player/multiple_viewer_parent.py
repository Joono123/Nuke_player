#!/usr/bin/env python
# encoding=utf-8

# author        :   Juno Park
# created date  :   2024.03.05
# modified date :   2024.03.23
# description   :   Nuke_player에 삽입되는 Multiple_viewer의 부모 클래스


import sys
import os
import time
import importlib

# sys.path.append("/home/rapa/libs_nuke")
import uuid
from PySide2 import QtWidgets, QtGui, QtMultimediaWidgets, QtCore, QtMultimedia
from NP_libs import NP_Utils
from NP_libs.qt import library as qt_lib
from NP_libs.player import single_viewer

importlib.reload(NP_Utils)
importlib.reload(qt_lib)
importlib.reload(single_viewer)


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


class VideoWidget(QtWidgets.QWidget):
    mode_changed = QtCore.Signal(str)
    update_slider_pos = QtCore.Signal(int, int)

    def __init__(self, video_path: str, parent=None):
        super().__init__(parent)

        # vars
        self.__wid = uuid.uuid4().hex
        self.__video_path = video_path
        self.__NP_Util = NP_Utils
        self.__single_viewer = single_viewer

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

    def dragEnterEvent(self, event) -> None:
        """
        드래그된 정보에 url이 존재하는지 검증
        """
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        """
        드롭된 정보에 url이 존재하는지 검증
        """
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        """
        드래그 중인 정보에 url이 존재하는지 검증
        """
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def mousePressEvent(self, event) -> None:
        """
        드래그 시 mime_data에 파일 url을 저장
        """
        if event.button() == QtCore.Qt.LeftButton:
            drag = QtGui.QDrag(self)
            mime_data = QtCore.QMimeData()
            mime_data.setUrls([QtCore.QUrl(self.__video_path)])
            drag.setMimeData(mime_data)
            drag.exec_(QtCore.Qt.CopyAction)

    def closeEvent(self, event) -> None:
        """
        UI 종료 시 플레이어 정지 및 스레드 종료
        """
        self.player.stop()
        self.update_thread.stop()
        print(f"\033[31m스레드 정상 종료: {self.__wid}\033[0m")
        event.accept()

    def __init_ui(self) -> None:
        """
        UI 생성 및 메인 위젯 설정
        """
        self.setStyleSheet(
            "color: rgb(255, 255, 255);" "background-color: rgb(70, 70, 70);"
        )

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
        v_widget.setStyleSheet("background-color: rgb(0, 0, 0);")

        # fonts
        font = QtGui.QFont("Sans Serif", 8)
        font2 = QtGui.QFont("Sans Serif", 9)
        font3 = QtGui.QFont("Sans Serif", 15)
        font2.setBold(True)

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
        self.label_path.setText(f"{os.path.basename(self.__video_path)}")
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

    def __connections(self) -> None:
        """
        UI 상호작용에 따른 시그널을 슬롯에 연결
        """
        self.__btn_play.clicked.connect(self.slot_play_video)
        self.__btn_stop.clicked.connect(self.slot_stop_video)
        self.btn_mode.clicked.connect(self.slot_changed_mode)
        self.btn_fullscreen.clicked.connect(self.slot_detach_viewer)
        self.__slider.sliderMoved.connect(self.__slot_slider_moved)
        self.player.stateChanged.connect(self.__slot_state_changed)
        self.player.positionChanged.connect(self.__slot_pos_shanged)
        self.player.durationChanged.connect(self.__slot_duration_changed)

    def slot_detach_viewer(self) -> None:
        """
        detach 버튼 클릭 시 영상을 싱글 뷰어에서 재생
        """
        self.player.stop()
        vw = self.__single_viewer.VideoWidget([self.__video_path])
        vw.show()

    def slot_stop_video(self) -> None:
        """
        stop 버튼 클릭 시 플레이어 포지션 초기화 및 정지
        """
        self.player.setPosition(0)
        self.player.stop()

    def slot_play_video(self) -> None:
        """
        play 버튼 클릭 시 재생 중이면 일시정지, 그렇지 않으면 재생
        """
        if self.player.state() == QtMultimedia.QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def __slot_state_changed(self, ste: QtMultimedia.QMediaPlayer.state) -> None:
        """
        :param ste: 플레이어의 현재 상태 (재생 중 or 일시정지 or 정지)
        플레이어의 상태가 변경될 경우 UI 갱신,
        loop버튼이 체크 상태일 때 플레이어가 정지되면 영상을 처음부터 다시 재생
        """
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

    def __slot_slider_moved(self, pos: QtWidgets.QSlider.pos) -> None:
        """
        :param pos: 슬라이더의 position 값
        슬라이더를 조작할 경우 플레이어의 재생 구간을 업데이트
        """
        self.player.setPosition(pos)

    def __slot_pos_shanged(self, pos: QtMultimedia.QMediaPlayer.position) -> None:
        """
        :param pos: 플레이어의 현재 재생 구간
        플레이어의 재생 구간이 변경될 경우 슬라이더 업데이트
        """
        self.__slider.setValue(pos)

    def __slot_duration_changed(
        self, duration: QtMultimedia.QMediaPlayer.duration
    ) -> None:
        """
        :param duration: 현재 재생 중인 영상의 길이
        영상이 변경될 경우 슬라이더의 범위를 업데이트
        """
        self.__slider.setRange(0, duration)

    def __add_play_lst(self) -> None:
        """
        파일 경로가 유효한지 확인 후 플레이리스트에 추가
        """
        v_path = self.__video_path
        f_info = QtCore.QFileInfo(v_path)
        if not os.path.exists(v_path):
            print(f"\033[31mERROR: 존재하지 않는 파일 >> {v_path}")
            return
        if not f_info.exists():
            print(f"\033[31mERROR: 유효하지 않은 시도 >> {f_info}")
            return
        url = QtCore.QUrl.fromLocalFile(f_info.absoluteFilePath())
        self.__play_lst.addMedia(QtMultimedia.QMediaContent(url))
        print(f"\033[32m로딩 완료: {v_path}\033[0m")

    @property
    def wid(self) -> str:
        """
        :return: 현재 클래스의 id를 반환
        """
        return self.__wid

    @QtCore.Slot(int)
    def __update_slider_position(
        self, position: QtMultimedia.QMediaPlayer.position
    ) -> None:
        """
        :param position: 플레이어의 현재 재생 구간
        :return: 스레드에서 정해진 간격으로 슬라이더를 업데이트
        """
        self.__slider.setValue(position)

    def slot_changed_mode(self) -> None:
        """
        표시 형식 버튼의 텍스트를 변경
        """
        if self.btn_mode.text() == "tc":
            self.btn_mode.setText("fps")
        elif self.btn_mode.text() == "fps":
            self.btn_mode.setText("tc")

    @QtCore.Slot(int)
    def slot_label_info(self) -> None:
        """
        설정된 표시 형식에 따라 시간 혹은 fps를 스레드에서 정해진 간격으로 업데이트
        """
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
            # pass
            self.label_remain_time.setText(f"{total_frames}")
            self.label_current_time.setText(f"{current_frames}")
        elif self.btn_mode.text() == "tc":
            self.label_remain_time.setText(f"{total_time_str}")
            self.label_current_time.setText(f"{current_time_str}")

    def __get_current_video_fps(self) -> int:
        """
        현재 재생 중인 파일의 fps를 소수점 아래 3자리까지 반환
        """
        current_media = self.player.currentMedia()
        if current_media.isNull():
            print("\033[31mERROR: 현재 미디어가 없음\033[0m")
            return 0
        else:
            current_url = current_media.canonicalUrl().toLocalFile()
            fps = round(self.__NP_Util.NP_Utils.get_video_fps(current_url), 3)
            return fps


test_path = "/home/rapa/Downloads/test1.MOV"

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    _vw = VideoWidget(test_path)
    _vw.show()
    app.exec_()
