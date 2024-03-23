#!/usr/bin/env python
# encoding=utf-8

# author        :   Juno Park
# created date  :   2024.03.03
# modified date :   2024.03.23
# description   :   Nuke_player에 삽입되는 Single_viewer 클래스


import os.path
import sys

sys.path.append("/home/rapa/libs_nuke")
import time
from PySide2 import QtWidgets, QtCore, QtGui, QtMultimediaWidgets, QtMultimedia

sys.path.append("/home/rapa/workspace/python/Nuke_player")
from library.qt import library as qt_lib
from library.NP_Utils import NP_Utils


class Thread_Updater(QtCore.QThread):
    # 슬라이더 업데이트를 위한 스레드
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
            print("\033[31m스레드 정상 종료\033[0m")


class VideoWidget(QtWidgets.QWidget):
    def __init__(self, playlist: list[str], parent=None):
        super().__init__(parent)

        # vars
        self.path_lst = playlist
        self.__dp_idx = 1
        self.__NP_Util = NP_Utils

        # Set UI
        self.setWindowTitle("Single Viewer")
        self.setAcceptDrops(True)
        qt_lib.QtLibs.center_on_screen(self)

        self.__init_ui()
        self.__connections()
        self.current_fps = self.__get_current_video_fps()

        self.__player.play()

        # Set Thread
        self.__slider_updater = Thread_Updater(self.__player, self)
        self.__slider_updater.pos_updated.connect(self.__update_slider_position)
        self.__slider_updater.dur_updated.connect(self.__slot_label_info)
        self.__slider_updater.start()

    def __init_ui(self) -> None:
        """
        UI 생성 및 메인 위젯 설정
        """
        self.setStyleSheet(
            "color: rgb(255, 255, 255);" "background-color: rgb(70, 70, 70);"
        )

        # 플레이어 설정
        self.__player = QtMultimedia.QMediaPlayer(
            None, QtMultimedia.QMediaPlayer.VideoSurface
        )

        # 플레이 리스트 등록
        self.__play_lst = QtMultimedia.QMediaPlaylist()
        self.__add_play_lst(self.path_lst)
        self.__player.setPlaylist(self.__play_lst)

        # 위젯 설정
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
        self.__btn_loop = QtWidgets.QPushButton()
        self.__btn_mode = QtWidgets.QPushButton("time")
        self.__btn_fullscreen = QtWidgets.QPushButton()
        self.__btn_mode.setFont(font)
        self.__btn_loop.setFixedSize(35, 25)
        self.__btn_mode.setFixedSize(35, 25)
        self.__btn_fullscreen.setFixedSize(25, 25)
        self.__btn_open.setFocusPolicy(QtCore.Qt.NoFocus)
        self.__btn_play.setFocusPolicy(QtCore.Qt.NoFocus)
        self.__btn_next.setFocusPolicy(QtCore.Qt.NoFocus)
        self.__btn_prev.setFocusPolicy(QtCore.Qt.NoFocus)
        self.__btn_stop.setFocusPolicy(QtCore.Qt.NoFocus)
        self.__btn_loop.setFocusPolicy(QtCore.Qt.NoFocus)
        self.__btn_mode.setFocusPolicy(QtCore.Qt.NoFocus)
        self.__btn_fullscreen.setFocusPolicy(QtCore.Qt.NoFocus)
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
        self.__btn_loop.setIcon(
            self.style().standardIcon(QtWidgets.QStyle.SP_BrowserReload)
        )
        self.__btn_fullscreen.setIcon(
            QtGui.QIcon(
                "/home/rapa/workspace/python/Nuke_player/resource/png/fullscreen.png"
            )
        )

        self.__btn_loop.setCheckable(True)
        self.__btn_loop.setChecked(False)

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
        self.__label_dp_idx = QtWidgets.QLabel(f"1 / {len(self.path_lst)}")
        self.__label_dp_idx.setFont(font2)

        # frame
        self.__overlay_frame = QtWidgets.QFrame()
        self.__overlay_frame.setStyleSheet("background-color: rgba(0, 0, 255, 100);")
        self.__overlay_frame.setGeometry(v_widget.geometry())
        self.__overlay_frame.hide()

        # layout
        hbox = QtWidgets.QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        # hbox.addWidget(self.__btn_open)
        hbox.addWidget(self.__btn_prev)
        hbox.addWidget(self.__btn_play)
        hbox.addWidget(self.__btn_stop)
        hbox.addWidget(self.__btn_next)
        hbox.addWidget(self.__label_current_time)
        hbox.addWidget(self.__slider)
        hbox.addWidget(self.__label_remain_time)
        hbox.addWidget(self.__btn_loop)
        hbox.addWidget(self.__btn_mode)
        hbox.addWidget(self.__btn_fullscreen)
        hbox_2 = QtWidgets.QHBoxLayout()
        hbox_2.addWidget(self.__label_filename)
        hbox_2.addItem(self.h_spacer)
        hbox_2.addWidget(self.__label_dp_idx)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox_2)
        vbox.addWidget(v_widget)
        vbox.addLayout(hbox)
        vbox.addWidget(self.__overlay_frame)

        self.__player.setVideoOutput(v_widget)
        self.__overlay_frame.raise_()

        self.setLayout(vbox)

        self.__update_file_path_label()

    def __connections(self) -> None:
        """
        UI 상호작용에 따른 시그널을 슬롯에 연결
        """
        # btns
        self.__btn_play.clicked.connect(self.__slot_play_video)
        self.__btn_stop.clicked.connect(self.__slot_stop_video)
        self.__btn_next.clicked.connect(self.__slot_next_video)
        self.__btn_prev.clicked.connect(self.__slot_prev_video)
        self.__btn_mode.clicked.connect(self.__slot_dp_mode)
        self.__btn_fullscreen.clicked.connect(self.__slot_fullscreen)

        # player
        self.__player.stateChanged.connect(self.__slot_state_changed)
        self.__player.positionChanged.connect(self.__slot_pos_changed)
        self.__player.durationChanged.connect(self.__slot_duration_changed)

        # slider
        self.__slider.sliderMoved.connect(self.__slot_slider_moved)

        # playlist
        self.__play_lst.currentIndexChanged.connect(self.__update_file_path_label)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """
        :param event: 키보드 입력 이벤트
        :return: 키보드 입력에 따른 이벤트 처리
        """
        if event.key() in [QtCore.Qt.Key_Space, QtCore.Qt.Key_Up, QtCore.Qt.Key_K]:
            self.__slot_play_video()
        elif event.key() in [QtCore.Qt.Key_Right, QtCore.Qt.Key_L]:
            self.__slot_next_video()
        elif event.key() in [QtCore.Qt.Key_Left, QtCore.Qt.Key_J]:
            self.__slot_prev_video()
        elif event.key() in [QtCore.Qt.Key_Down, QtCore.Qt.Key_Q]:
            self.__slot_stop_video()
        elif event.key() == QtCore.Qt.Key_R:
            self.__btn_loop.click()
        elif event.key() == QtCore.Qt.Key_V:
            self.__slot_dp_mode()
        elif event.key() == QtCore.Qt.Key_F11:
            self.__slot_fullscreen()
        elif event.key() == QtCore.Qt.Key_Escape:
            self.close()
        else:
            event.ignore()

    def dragEnterEvent(self, event) -> None:
        """
        드래그 중인 정보가 Url인지 검증
        """
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        """
        드롭된 정보가 Url인지 검증
        """
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        """
        드래그 중인 정보가 Url인지 검증
        """
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            # self.__overlay_frame.show()
        else:
            event.ignore()

    def mousePressEvent(self, event) -> None:
        """
        :param event: 마우스가 눌리면 발생하는 이벤트
        마우스의 왼쪽 버튼이 눌린 경우 드래그에 Url정보를 설정
        """
        if event.button() == QtCore.Qt.LeftButton:
            drag = QtGui.QDrag(self)
            mime_data = QtCore.QMimeData()
            mime_data.setUrls([QtCore.QUrl(self.path_lst[self.__dp_idx - 1])])
            drag.setMimeData(mime_data)
            drag.exec_(QtCore.Qt.CopyAction)
            # self.__overlay_frame.show()

    def closeEvent(self, event):
        """
        UI 종료 시 플레이어를 정지하고 슬라이더 업데이트 스레드를 종료
        """
        if self.__player.state() in [
            QtMultimedia.QMediaPlayer.PlayingState,
            QtMultimedia.QMediaPlayer.PausedState,
            QtMultimedia.QMediaPlayer.StoppedState,
        ]:
            self.__player.stop()
            self.__slider_updater.stop()
            self.__slider_updater.wait()
        event.accept()

    def __get_current_video_fps(self) -> float:
        """
        :return: 현재 재생 중인 영상의 프레임 정보를 소수점 아래 3자리까지 반환
        """
        current_media = self.__player.currentMedia()
        # 재생 중인 미디어가 있는지 확인
        if current_media.isNull():
            print("\033[31mERROR: 현재 미디어가 없음\033[0m")
            return 0
        else:
            current_url = current_media.canonicalUrl().toLocalFile()
            fps = round(self.__NP_Util.get_video_fps(current_url), 3)
            return fps

    def __add_play_lst(self, playlist: list[str]) -> None:
        """
        :param playlist: 비디오 파일 경로가 담긴 리스트
        리스트로 받은 파일 경로가 로컬에 존재하는 파일인지 확인하여 플레이리스트에 추가
        """
        for f_path in playlist:
            # 파일이 존재하는지 검증
            if not os.path.exists(f_path):
                print(f"\033[31mERROR: {f_path}가 존재하지 않음\033[0m")
                return
            f_info = QtCore.QFileInfo(f_path)
            # 파일 정보가 존재하는지 검증
            if not f_info.exists():
                print(f"\033[31mERROR: {f_info}가 존재하지 않음\033[0m")
                return
            # 파일 주소값을 절대 경로로 가져옴
            url = QtCore.QUrl.fromLocalFile(f_info.absoluteFilePath())
            self.__play_lst.addMedia(QtMultimedia.QMediaContent(url))
        print(f"\033[32m플레이 리스트: {playlist}\033[0m")

    @QtCore.Slot(int)
    def __update_slider_position(self, position: int) -> None:
        """
        :param position: 플레이어의 현재 포지션
        플레이어가 재생 중일 때 슬라이더의 값을 업데이트
        """
        self.__slider.setValue(position)

    def __update_file_path_label(self) -> None:
        """
        현재 재생 중인 파일의 경로를 UI에 업데이트
        """
        current_file = self.path_lst[self.__play_lst.currentIndex()]
        self.__label_filename.setText(f"Current File: {current_file}")

    def __slot_fullscreen(self) -> None:
        """
        플레이어가 현재 전체화면이 아닌 경우 전체화면으로, 그렇지 않은 경우 원래대로 설정함
        """
        if not self.isFullScreen():
            self.showFullScreen()
        else:
            self.showNormal()

    def __slot_dp_mode(self) -> None:
        """
        표시 형식 버튼을 누르면 텍스트 변경
        """
        if self.__btn_mode.text() == "fps":
            self.__btn_mode.setText("time")
        else:
            self.__btn_mode.setText("fps")

    def __slot_next_video(self) -> None:
        """
        플레이리스트의 다음 영상을 재생
        """
        current_idx = self.__play_lst.currentIndex()
        # 영상이 재생목록의 마지막인 경우 return
        if not self.__play_lst.currentIndex() < len(self.path_lst) - 1:
            print("\033[31mERROR: 재생 목록의 마지막 영상입니다.\033[0m")
            return
        self.__play_lst.setCurrentIndex(current_idx + 1)
        self.current_fps = self.__get_current_video_fps()
        self.__dp_idx += 1
        self.__label_dp_idx.setText(f"{self.__dp_idx} / {len(self.path_lst)}")
        self.__player.setPosition(0)

    def __slot_prev_video(self) -> None:
        """
        플레이리스트의 이전 영상을 재생
        """
        current_idx = self.__play_lst.currentIndex()
        current_pos: int = self.__player.position()
        current_time: QtCore.QTime = QtCore.QTime(0, 0).addMSecs(current_pos)
        # 현재 영상이 플레이 리스트의 첫 번째인 경우 에러 발생
        if not self.__play_lst.currentIndex() > 0:
            # 현재 재생 시점이 일정 시간이 지난 경우 현재 영상을 처음부터 재생
            if 0 < current_time.second():
                self.__player.stop()
                self.__player.play()
            else:
                print("\033[31mERROR: 재생 목록의 첫 번째 영상입니다.\033[0m")
                self.__player.setPosition(0)
                self.__player.pause()
                self.__slider.setValue(0)
        else:
            # 현재 재생 시점이 일정 시간이 지난 경우 현재 영상을 처음부터 재생
            if 0 < current_time.second():
                self.__player.stop()
                self.__player.play()
                return
            else:
                # 플레이리스트의 이전 영상을 재생하고 UI 업데이트
                self.__play_lst.setCurrentIndex(current_idx - 1)
                self.current_fps = self.__get_current_video_fps()
                self.__dp_idx -= 1
                self.__label_dp_idx.setText(f"{self.__dp_idx} / {len(self.path_lst)}")

    def __slot_stop_video(self) -> None:
        """
        stop 버튼이 클릭된 경우 player의 포지션을 0으로 만들고 정지
        """
        self.__player.setPosition(0)
        self.__player.stop()

    def __slot_play_video(self) -> None:
        """
        play버튼을 클릭한 경우 player가 재생 중이면 일시정지, 그렇지 않으면 재생
        """
        if self.__player.state() == QtMultimedia.QMediaPlayer.PlayingState:
            self.__player.pause()
        else:
            self.__player.play()

    def __slot_state_changed(self, ste) -> None:
        """
        :param ste: 현재 플레이어의 상태 (재생 or 일시정지 or 정지)
        :return:
        """
        # 재생 중에는 play 아이콘을 pause아이콘으로 변경
        if ste == QtMultimedia.QMediaPlayer.PlayingState:
            self.__btn_play.setIcon(
                self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause)
            )

        else:
            self.__btn_play.setIcon(
                self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay)
            )
        # 영상이 정지되었을 때 loop 버튼이 체크 상태라면 영상을 처음부터 다시 재생
        if ste == QtMultimedia.QMediaPlayer.StoppedState:
            if self.__btn_loop.isChecked():
                self.__player.setPosition(0)
                self.__player.play()
                self.__btn_play.setIcon(
                    self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause)
                )

    def __slot_pos_changed(self, pos) -> None:
        """
        :param pos: player의 position값
        현재 영상의 재생 구간이 바뀔 경우 slider도 그에 맞게 업데이트
        """
        self.__slider.setValue(pos)

    def __slot_duration_changed(self, duration) -> None:
        """
        :param duration: 영상의 길이
        현재 재생 중인 영상이 바뀔 경우 slider의 범위를 재설정
        """
        self.__slider.setRange(0, duration)

    def __slot_slider_moved(self, pos) -> None:
        """
        :param pos: slider가 이동한 위치의 position값
        슬라이더를 조작하면 영상의 재생 구간을 업데이트
        """
        self.__player.setPosition(pos)

    def __slot_label_info(self) -> None:
        """
        현재 영상의 총 시간, 남은 시간, 현재 시간을 표시 계산하여 label에 업데이트
        표시 형식 변경시 시간 대신 fps를 표시
        """
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

    # ###################################### LEGACY ##########################################

    def __slot_open_file_legacy(self) -> None:
        """
        파일 탐색기를 열어 영상을 직접 선택 및 재생할 수 있음, 현재 사용하지 않음
        """
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

    # ########################################################################################


# TEST
t_path = ["/home/rapa/Downloads/test1.MOV"]
t_path_str = "/home/rapa/Downloads/test1.MOV"

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    vid = VideoWidget(t_path)
    vid.show()
    sys.exit(app.exec_())
