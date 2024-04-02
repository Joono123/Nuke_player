#!/usr/bin/env python
# encoding=utf-8

# author        :   Juno Park
# created date  :   2024.03.03
# modified date :   2024.03.23
# description   :   누크에서 작업을 시작하기 전, 다양한 소스를 동시에 확인하는 것에 어려움이 있는데,
#                   이러한 불편함을 해소하고자, 유저 친화적인 플레이어를 제작.
#                   드래그앤드랍으로 간편하게 소스를 등록하고, 영상을 재생하며,
#                   소스를 확인하는 동시에 Nuke의 Read 노드로 불러오는 것이 가능함.
#
# 현재 확인된 위험 :   파일을 드롭하고 썸네일을 추출하는 도중 취소하게 되면 썸네일 추출은 중단되지만,
#                   파일 정보는 리스트 및 딕셔너리에 들어가게 됨.
#                   간헐적으로 point error가 발생하며 프로그램이 강제 종료됨
#
# 추가하고자 하는 기능 : 샷그리드와 연동하여 소스 불러오기, 소스 버전 관리,


import importlib
import os
import subprocess
import sys

os.environ["NUKE_INTERACTIVE"] = "1"
try:
    import nuke
except ModuleNotFoundError as err:
    print(f"\033[31mNuke Import Error: {err}\033[0m")
import pathlib
import platform

sys.path.append("/home/rapa/workspace/python/Nuke_player")
from PySide2 import QtWidgets, QtGui, QtCore
from view import NP_view
from model import NP_model
from NP_libs.qt import library as qt_lib
from NP_libs.system import library as sys_lib
from NP_libs import NP_Utils

importlib.reload(NP_view)
importlib.reload(NP_model)
importlib.reload(NP_Utils)
importlib.reload(qt_lib)
importlib.reload(sys_lib)


class Image_2_Video_Thread(QtCore.QThread):
    thread_finished = QtCore.Signal()

    def __init__(self, file_path: str, thumbnail_dir: str, ext: str):
        super().__init__()
        self.__file_path = file_path
        self.__thumb_dir = thumbnail_dir
        self.__ext = ext
        self.__NP_util = NP_Utils
        self.__name = os.path.basename(self.__file_path)

    def run(self):
        self.__dropped_dir()
        self.thread_finished.emit()

    def __dropped_dir(self):
        self.__output = self.__NP_util.NP_Utils.images_to_video(
            self.__file_path, self.__thumb_dir, self.__ext, self.__name
        )

    def stop(self):
        self.quit()
        self.wait(10000)

    def cancel(self):
        os.remove(self.__output)


class Extract_Tuhmbnails_Thread(QtCore.QThread):
    thumbnail_extract = QtCore.Signal()
    thread_finished = QtCore.Signal()

    def __init__(self, file_data: dict, thumbnail_dir: str):
        super().__init__()
        self.__file_data = file_data
        self.__thumb_dir = thumbnail_dir
        self.__NP_util = NP_Utils
        self.__canceled = False

    def run(self):
        for idx, f_path in self.__file_data.items():
            if self.__canceled:
                break
            base_name = os.path.splitext(os.path.basename(f_path))[0]
            file_name = os.path.join(self.__thumb_dir, base_name + ".jpg")
            # 썸네일이 이미 존재하는 경우 넘어감
            if os.path.exists(file_name):
                continue
            # 썸네일 추출
            try:
                self.__NP_util.NP_Utils.extract_thumbnail(f_path, file_name, "1280x720")
                self.thumbnail_extract.emit()
            except Exception as err:
                print(f"\033[31mERROR:{file_name} >> {err}\033[0m")
        self.thread_finished.emit()

    def stop(self):
        self.quit()
        self.wait(10000)
        print("\n\033[31m백그라운드 스레드 정상 종료\033[0m")

    def cancel(self):
        self.__canceled = True
        print(f"\033[31m파일 로드 중단\033[0m")


class LoadingDialog(QtWidgets.QProgressDialog):
    # 파일 드롭 시 발생하는 다이얼로그
    def __init__(self, total_files: int, text: str, cancel_btn=True, parent=None):
        super().__init__(parent)
        self.setWindowTitle("File Loading")
        self.setLabelText(text)
        self.setFixedSize(300, 100)
        self.setRange(0, total_files)
        self.setValue(0)
        self.setFont(QtGui.QFont("Sans Serif", 10))
        self.setStyleSheet(
            "color: rgb(255, 255, 255);" "background-color: rgb(70, 70, 70);"
        )
        self.setModal(True)
        # 캔슬버튼 유무 설정
        if cancel_btn is None:
            self.setCancelButton(None)
            self.setFixedSize(300, 80)

    # progress 값을 증가시킴
    def increase_value(self):
        self.setValue(self.value() + 1)

    def reject(self):
        self.canceled.emit()
        super().reject()


class LoadingDialog_loop(QtWidgets.QProgressDialog):
    # 뷰어 실행 시 발생하는 다이얼로그
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Viewer Playing")
        self.setLabelText("뷰어가 실행 중입니다,\n동시에 하나의 플레이어만 사용하는 것을 권장합니다.")
        self.setFixedSize(320, 120)
        self.setCancelButtonText("Ok")
        self.setRange(0, 0)
        self.setFont(QtGui.QFont("Sans Serif", 10))
        self.setStyleSheet(
            "color: rgb(255, 255, 255);" "background-color: rgb(70, 70, 70);"
        )
        self.setModal(True)


class Nuke_Player(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 변수 설정
        self.__NP_util = NP_Utils
        self.__item_listview = NP_view.NP_ItemView()
        self.__text_listview = NP_view.NP_ListView()

        # 썸네일을 임시 저장할 상대경로 설정
        self.current_dir = os.path.dirname(os.path.realpath(__file__))
        self.home_dir = os.path.expanduser("~")
        self.__thumb_dir = os.path.join(self.home_dir, ".NP_temp")  # 숨김 상태로 생성
        self.__sequence_dir = os.path.join(self.__thumb_dir, "sequence")
        self.__temp_file = os.path.join(
            self.__thumb_dir, "playlist.txt"
        )  # -> 플레이리스트를 작성할 임시 파일

        # 해당 디렉토리가 없을 경우 생성
        self.__NP_util.NP_Utils.make_dirs(self.__thumb_dir)
        self.__NP_util.NP_Utils.make_dirs(self.__sequence_dir)

        self.__file_data = dict()  # {인덱스: 원본 파일 경로}의 형태로 데이터 저장
        self.__file_lst = list()  # file_data의 value값을 리스트로 저장
        self.__thumb_lst = list()  # 썸네일 디렉토리 내의 파일 경로를 리스트로 저장
        self.__play_lst = list()  # 선택된 파일의 경로를 인덱스로 저장
        self.__play_lst_basename = list()  # 파일 경로의 basename만 저장

        # 모델 설정
        self.__itemview_model = NP_model.NP_ItemModel(self.__thumb_lst, self.__file_lst)
        self.__item_listview.setModel(self.__itemview_model)
        self.__textview_model = NP_model.NP_ListModel(self.__play_lst)
        self.__text_listview.setModel(self.__textview_model)

        # Init set
        self.setWindowIcon(
            QtGui.QIcon(
                "/home/rapa/workspace/python/Nuke_player/resource/png/video-player.ico"
            )
        )
        self.__set_ui()
        self.__set_menu()
        self.__connection()

        self.__item_listview.setIconSize(QtCore.QSize(229, 109))

    def __set_ui(self) -> None:
        """
        메인 UI 요소 생성 및 설정
        """
        # Icon_pixmap
        self.__icon_error = (
            "/home/rapa/workspace/python/Nuke_player/resource/png/error.png"
        )
        self.__icon_info = (
            "/home/rapa/workspace/python/Nuke_player/resource/png/information.png"
        )

        # fonts
        self.font_1 = QtGui.QFont("Sans Serif", 10)
        self.font_2 = QtGui.QFont("Sans Serif", 8)
        self.font_3 = QtGui.QFont("Sans Serif", 10)
        self.setFont(self.font_1)

        # widget
        widget_1 = QtWidgets.QWidget()
        vbox_1 = QtWidgets.QVBoxLayout()
        vbox_2 = QtWidgets.QVBoxLayout()

        # btns
        hbox_btn = QtWidgets.QHBoxLayout()
        hbox_chg_idx = QtWidgets.QHBoxLayout()
        self.__btn_icon_size_1 = QtWidgets.QPushButton("", self)
        self.__btn_icon_size_2 = QtWidgets.QPushButton("", self)
        self.__btn_icon_size_3 = QtWidgets.QPushButton("", self)
        self.__btn_idx_up = QtWidgets.QPushButton()
        self.__btn_idx_down = QtWidgets.QPushButton()
        self.__btn_icon_size_1.setIcon(
            QtGui.QIcon("/home/rapa/workspace/python/Nuke_player/resource/png/1x1.png")
        )
        self.__btn_icon_size_2.setIcon(
            QtGui.QIcon("/home/rapa/workspace/python/Nuke_player/resource/png/2x2.png")
        )
        self.__btn_icon_size_3.setIcon(
            QtGui.QIcon("/home/rapa/workspace/python/Nuke_player/resource/png/3x3.png")
        )
        self.__btn_idx_up.setIcon(
            QtGui.QIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowUp))
        )
        self.__btn_idx_down.setIcon(
            QtGui.QIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowDown))
        )
        self.__btn_icon_size_1.setCheckable(True)
        self.__btn_icon_size_2.setCheckable(True)
        self.__btn_icon_size_3.setCheckable(True)
        self.__btn_icon_size_1.setChecked(False)
        self.__btn_icon_size_2.setChecked(True)
        self.__btn_icon_size_3.setChecked(False)

        self.__btn_icon_size_1.setFixedSize(25, 25)
        self.__btn_icon_size_2.setFixedSize(25, 25)
        self.__btn_icon_size_3.setFixedSize(25, 25)

        self.__btn_play = QtWidgets.QPushButton("Play")
        self.__btn_play.setFixedSize(70, 25)
        self.__btn_import = QtWidgets.QPushButton("Import")
        self.__btn_import.setFixedSize(70, 25)

        self.__btn_icon_size_1.setToolTip("Set Icon Size Maximum (F1)")
        self.__btn_icon_size_2.setToolTip("Set Icon Size Normal (F2)")
        self.__btn_icon_size_3.setToolTip("Set Icon Size Minimum (F3)")
        self.__btn_play.setToolTip("Play Playlist in Viewer (P)")
        self.__btn_import.setToolTip("Import File into Nuke (I)")

        # lineEdit
        self.__lineEdit_debug = QtWidgets.QLineEdit("파일을 등록하세요")
        self.__lineEdit_debug.setFont(self.font_2)
        self.__lineEdit_debug.setEnabled(False)
        self.__lineEdit_debug.setAlignment(QtCore.Qt.AlignVCenter)
        self.__lineEdit_debug.setStyleSheet(
            "color: rgb(255, 255, 255);" "background-color: rgba(0, 0, 0, 0);"
        )
        # checkBox
        hbox_checkBox = QtWidgets.QHBoxLayout()
        hbox_checkBox.setAlignment(QtCore.Qt.AlignRight)
        check_label = QtWidgets.QLabel("Multiple Viewer")
        self.__check_viewer = QtWidgets.QCheckBox()
        self.__check_viewer.setChecked(True)
        self.__check_viewer.setToolTip("Choose Viewer (V)")
        check_label.setToolTip("Choose Viewer (V)")

        # labels
        label_list = QtWidgets.QLabel("Selected Playlist")
        label_list.setAlignment(QtCore.Qt.AlignCenter)
        label_list.setFont(self.font_3)

        # spacer
        h_spacer = QtWidgets.QSpacerItem(
            200, 25, QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )

        # set layouts
        hbox_btn.addWidget(self.__btn_icon_size_1)
        hbox_btn.addWidget(self.__btn_icon_size_2)
        hbox_btn.addWidget(self.__btn_icon_size_3)
        hbox_btn.addWidget(self.__lineEdit_debug)
        hbox_btn.addWidget(self.__btn_import)
        hbox_btn.addWidget(self.__btn_play)

        hbox_checkBox.addWidget(check_label)
        hbox_checkBox.addWidget(self.__check_viewer)

        hbox_chg_idx.addWidget(label_list)
        hbox_chg_idx.addItem(h_spacer)
        hbox_chg_idx.addWidget(self.__btn_idx_up)
        hbox_chg_idx.addWidget(self.__btn_idx_down)

        vbox_1.addWidget(self.__item_listview)
        vbox_1.addLayout(hbox_checkBox)
        vbox_1.addLayout(hbox_btn)
        vbox_2.addLayout(hbox_chg_idx)
        vbox_2.addWidget(self.__text_listview)
        main_hbox = QtWidgets.QHBoxLayout()
        main_hbox.addLayout(vbox_1)
        main_hbox.addLayout(vbox_2)

        # set widget
        self.setFixedSize(840, 480)
        # self.setSizePolicy(
        #     QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        # )
        widget_1.setLayout(main_hbox)
        self.setCentralWidget(widget_1)
        qt_lib.QtLibs.center_on_screen(self)
        self.setWindowTitle("Nuke Player")
        self.setStyleSheet(
            "color: rgb(255, 255, 255);" "background-color: rgb(70, 70, 70);"
        )

    def __set_menu(self) -> None:
        """
        메뉴바 생성 및 메뉴 관리
        """
        # menu
        menubar = QtWidgets.QMenuBar()
        menu_file = menubar.addMenu("File")
        menu_help = menubar.addMenu("Help")
        self.file_1 = QtWidgets.QAction("Open in Files", self)
        self.file_2 = QtWidgets.QAction("Quit", self)
        self.help_1 = QtWidgets.QAction("What's this?", self)
        self.help_2 = QtWidgets.QAction("Keyboard Shortcut", self)
        self.file_1.setShortcut(QtGui.QKeySequence("Ctrl+F"))
        self.file_2.setShortcut(QtGui.QKeySequence("Ctrl+Q"))
        self.help_1.setShortcut(QtGui.QKeySequence("Ctrl+W"))
        self.help_2.setShortcut(QtGui.QKeySequence("Ctrl+K"))
        menu_help.addAction(self.help_1)
        menu_help.addAction(self.help_2)
        menu_file.addAction(self.file_1)
        menu_file.addAction(self.file_2)
        # menubar QSS
        menubar.setStyleSheet(
            """
            QMenuBar {
                background-color: rgb(55, 55, 55);
                border: 1px solid #303030;
                font-family: Sans Serif;
                font-size: 12px;
            }

            QMenuBar::item {
                background-color: transparent;
                color: white;
                padding: 4px 10px;
            }

            QMenuBar::item:selected {
                background-color: rgb(30, 30, 30);
            }
            """
        )

        # menu QSS
        menu_help.setStyleSheet(
            """
            QMenu {
                background-color: rgb(50, 50, 50);
                color: white;
                border: 1px solid #303030;
                font-family: Sans Serif;
                font-size: 12px;
            }

            QMenu::item {
                background-color: transparent;
                color: white;
                border: 1px solid #303030;
                padding: 6px 20px;
            }

            QMenu::item:selected {
                background-color: rgb(30, 30, 30);
            }
            """
        )
        menu_file.setStyleSheet(
            """
            QMenu {
                background-color: rgb(50, 50, 50);
                color: white;
                border: 1px solid #303030;
                font-family: Sans Serif;
                font-size: 12px;
            }

            QMenu::item {
                background-color: transparent;
                color: white;
                border: 1px solid #303030;
                padding: 6px 20px;
            }

            QMenu::item:selected {
                background-color: rgb(30, 30, 30);
            }
            """
        )

        self.setMenuBar(menubar)

    def __connection(self) -> None:
        """
        UI 상호작용 시 시그널 발생
        """
        # 버튼 클릭 시 시그널 발생
        self.__btn_icon_size_1.clicked.connect(
            lambda: self.__slot_adjust_icon_size(2, 75)
        )
        self.__btn_icon_size_2.clicked.connect(
            lambda: self.__slot_adjust_icon_size(3, 51)
        )
        self.__btn_icon_size_3.clicked.connect(
            lambda: self.__slot_adjust_icon_size(4, 40)
        )
        self.__btn_play.clicked.connect(self.__slot_play_videos)
        self.__btn_import.clicked.connect(self.__slot_import_on_nuke)
        self.__btn_idx_up.clicked.connect(lambda: self.__slot_chg_text_idx("up"))
        self.__btn_idx_down.clicked.connect(lambda: self.__slot_chg_text_idx("down"))

        # 드래그 or 드랍 시 시그널 발생
        self.__item_listview.dragEnterEvent = self.__dragEnter_items
        self.__item_listview.dragMoveEvent = self.__dragMove_items
        self.__item_listview.dropEvent = self.__drop_items

        # 우클릭 시 컨텍스트 메뉴 발생
        self.__item_listview.customContextMenuRequested.connect(self.__slot_context)

        # 메뉴 선택 시 시그널 발생
        self.file_1.triggered.connect(self.__slot_menu_file1)
        self.file_2.triggered.connect(self.close)
        self.help_1.triggered.connect(lambda: self.__slot_menu_help(0))
        self.help_2.triggered.connect(lambda: self.__slot_menu_help(1))

    def closeEvent(self, event) -> None:
        """
        :param event: 메인 UI 종료 이벤트
        메인 UI 종료 시 임시 디렉토리 삭제
        """
        self.__NP_util.NP_Utils.remove_dirs(self.__thumb_dir)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """
        :param event: 키보드 입력 이벤트
        키보드 입력에 대한 이벤트 처리
        """
        if event.key() == QtCore.Qt.Key_F1:
            self.__btn_icon_size_1.click()
        elif event.key() == QtCore.Qt.Key_F2:
            self.__btn_icon_size_2.click()
        elif event.key() == QtCore.Qt.Key_F3:
            self.__btn_icon_size_3.click()
        elif event.key() == QtCore.Qt.Key_Delete:
            self.__slot_del_file()
        elif event.key() == QtCore.Qt.Key_V:
            if self.__check_viewer.isChecked():
                self.__check_viewer.setChecked(False)
            else:
                self.__check_viewer.setChecked(True)
        elif event.key() == QtCore.Qt.Key_I:
            self.__slot_import_on_nuke()
        elif event.key() in [
            QtCore.Qt.Key_Enter,
            QtCore.Qt.Key_Return,
            QtCore.Qt.Key_P,
        ]:
            self.__slot_play_videos()

    def __dragEnter_items(self, event: QtGui.QDragEnterEvent) -> None:
        """
        ListView로 마우스가 드래그 상태로 들어온 경우
        이벤트의 데이터에 URL이 포함되었는지 검증
        """
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def __dragMove_items(self, event: QtGui.QDragMoveEvent) -> None:
        """
        ListView에서 마우스가 드래그 상태로 움직이는 경우
        이벤트의 데이터에 URL이 포함되었는지 검증
        """
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def __drop_items(self, event: QtGui.QDropEvent) -> None:
        """
        ListView내에서 드롭되었을 경우 해당 데이터의 URL(파일 경로)을
        딕셔너리에 저장 후 각 파일의 썸네일을 추출하여 임시 디렉토리에 저장하고
        모델에서 데이터를 다시 로드하여 UI를 새로 불러옴
        썸네일 추출의 경우 스레드를 통해 백그라운드에서 진행
        """
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            urls = event.mimeData().urls()

            # 파일 경로 저장
            for idx, url in enumerate(urls):
                file_path = url.toLocalFile()
                url_str = url.toString()
                # 드롭된 아이템이 디렉토리인 경우
                if os.path.isdir(file_path):
                    self.__dropped_dir(file_path)
                    return

                # 파일 유형이 영상이 맞는지 확인
                elif not self.__NP_util.NP_Utils.is_file_video(url_str):
                    print(f"\033[31mERROR: '{file_path}'는 지원하지 않는 형식입니다.\033[0m")
                    ext = os.path.splitext(os.path.basename(file_path))[1]
                    self.__slot_messagebox("File Type", ext)
                    return

                # 파일이 이미 등록되어 있는지 확인
                if file_path in self.__file_data.values():
                    # print(f"\033[31mERROR: '{file_path}'가 이미 등록되었습니다.\033[0m")
                    continue

                # 딕셔너리에 {인덱스: 파일 경로}의 형태로 데이터 저장
                if idx in self.__file_data.keys():
                    last_idx = list(self.__file_data.keys())[-1]
                    self.__file_data[last_idx + 1] = file_path
                # 인덱스가 이미 존재하는 경우 파일경로 덮어쓰기
                else:
                    self.__file_data[idx] = file_path

            # 썸네일 추출 스레드 생성 및 실행
            self.__thumb_thread = Extract_Tuhmbnails_Thread(
                self.__file_data, self.__thumb_dir
            )
            self.__thumb_thread.thumbnail_extract.connect(self.__extract_finished)
            self.__thumb_thread.finished.connect(self.__thread_stopped)
            self.__thumb_thread.start()

            # 로딩 다이얼로그 생성 및 실행
            self.__loading_dialog = LoadingDialog(len(urls), "파일을 로드 중입니다.")
            self.__loading_dialog.setWindowModality(QtCore.Qt.ApplicationModal)
            self.__loading_dialog.canceled.connect(
                self.__thumb_thread.cancel
            )  # -> 다이얼로그를 닫을 경우 스레드 중단
            self.__thumb_thread.thumbnail_extract.connect(
                self.__loading_dialog.increase_value
            )  # -> 썸네일이 추출될 때마다 진행도 업데이트
            self.__loading_dialog.show()

            event.acceptProposedAction()
        else:
            event.ignore()

    def __dropped_dir(self, dir_path: str) -> None:
        """
        :param dir_path: 드롭된 directory의 로컬 경로
        디렉토리가 등록된 경우, 해당 디렉토리에 이미지 시퀀스가 존재하면 이미지 시퀀스를 영상으로 변환하여
        임시 디렉토리에 저장함
        """
        # 이미지 시퀀스
        sequence = self.__NP_util.NP_Utils.is_image_sequence(dir_path)
        # 이미지 확장자명
        if not len(sequence):
            return
        ext = os.path.splitext(os.path.basename(sequence[0]))[1]
        missing_num = self.__NP_util.NP_Utils.exist_missing_numbers(dir_path, ext)
        # 시퀀스에 비어있는 이미지가 있는지 확인
        if missing_num:
            self.__slot_messagebox("Missing", missing_num)
            return
        # 디렉토리에 시퀀스 이외의 파일이 존재하는 지 확인
        for file in os.listdir(dir_path):
            if file not in sequence:
                self.__slot_messagebox("Sequence", file)
                return
        # 이미 등록된 디렉토리의 경우 return
        real_path = os.path.join(
            self.__sequence_dir, os.path.basename(dir_path) + ".mp4"
        )
        if real_path in self.__file_data.values():
            return

        self.__loading_dialog_ = LoadingDialog(0, "시퀀스를 비디오로 변환 중입니다.", None)
        self.__loading_dialog_.show()
        self.__convert_thread = Image_2_Video_Thread(dir_path, self.__sequence_dir, ext)
        self.__convert_thread.thread_finished.connect(self.__thread_finished)
        self.__convert_thread.start()

    def __thread_finished(self) -> None:
        """
        시퀀스 변환 스레드 종료 후 데이터 저장 및 썸네일 생성, UI 새로고침
        """
        self.__convert_thread.stop()
        self.__convert_thread.wait()
        self.__loading_dialog_.hide()

        for file in os.listdir(self.__sequence_dir):
            new_seq = os.path.join(self.__sequence_dir, file)
            if not self.__file_data:
                self.__file_data[0] = new_seq
            else:
                if new_seq in self.__file_data.values():
                    continue
                last_idx = max(self.__file_data.keys())
                new_idx = last_idx + 1
                self.__file_data[new_idx] = new_seq

        # 썸네일 추출 스레드 생성 및 실행
        self.__seq_thumb_thread = Extract_Tuhmbnails_Thread(
            self.__file_data, self.__thumb_dir
        )
        self.__seq_thumb_thread.thumbnail_extract.connect(self.__extract_finished)
        self.__seq_thumb_thread.finished.connect(self.__seq_thread_stopped)
        self.__seq_thumb_thread.start()

        # 로딩 다이얼로그 생성 및 실행
        self.__seq_loading_dialog = LoadingDialog(0, "파일을 로드 중입니다.")
        self.__seq_loading_dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        # self.__seq_loading_dialog.canceled.connect(
        #     self.__seq_loading_dialog_cancel
        # )  # -> 다이얼로그를 닫을 경우 스레드 중단
        self.__seq_loading_dialog.show()

    def __seq_thread_stopped(self) -> None:
        """
        스레드가 종료된 후 로딩 다이얼로그 숨김, 시그널 초기화
        """
        self.__seq_loading_dialog.hide()

        # 아이템 선택 시 시그널 발생
        self.__item_listview.selectionModel().selectionChanged.connect(
            self.__slot_selection_item
        )

    def __thread_stopped(self) -> None:
        """
        스레드가 종료된 후 로딩 다이얼로그 숨김, 시그널 초기화
        """
        self.__loading_dialog.hide()

        # 아이템 선택 시 시그널 발생
        self.__item_listview.selectionModel().selectionChanged.connect(
            self.__slot_selection_item
        )

    def __extract_finished(self) -> None:
        """
        썸네일이 추출될 때마다 모델을 업데이트하고 UI를 새로고침 함
        """
        # 썸네일 디렉토리의 파일 검색 후 모델 새로고침
        self.__thumb_lst = list(
            map(
                lambda x: x.as_posix(),
                sys_lib.System.get_files_lst(pathlib.Path(self.__thumb_dir), ".jpg"),
            )
        )
        self.__file_lst = list(self.__file_data.values())
        self.__itemview_model = NP_model.NP_ItemModel(self.__thumb_lst, self.__file_lst)
        self.__item_listview.setModel(self.__itemview_model)

        # 로딩 바 종료
        self.__lineEdit_debug.setText("파일을 선택하세요")

    def __slot_del_file(self) -> None:
        """
        선택된 아이템의 데이터 및 썸네일 파일 삭제 후 모델 갱신
        """
        del_lst = []
        # 아이템이 선택되지 않은 경우 예외 처리
        if not self.__play_lst:
            self.__lineEdit_debug.setText("ERROR: 삭제할 파일이 선택되지 않았습니다")
            self.__slot_messagebox("Delete")
            return
        selected_idx = self.__item_listview.selectedIndexes()
        for f_path in self.__play_lst[:]:
            # 리스트에 추가
            del_lst.append(os.path.basename(f_path))
            # 썸네일 삭제
            thumbs = os.path.splitext(os.path.basename(f_path))[0] + ".jpg"
            thumbs_path = os.path.join(self.__thumb_dir, thumbs)
            dir_path = os.path.join(
                self.__sequence_dir,
                os.path.splitext(os.path.basename(f_path))[0] + ".mp4",
            )
            # 파일이 존재하는지 검증
            if not os.path.exists(thumbs_path):
                self.__lineEdit_debug.setText("ERROR: 삭제할 파일이 존재하지 않습니다")
                self.__slot_messagebox("File")
                return
            # 썸네일 제거
            os.remove(thumbs_path)
            if os.path.exists(dir_path):
                os.remove(dir_path)
            # 썸네일 리스트 초기화
            self.__thumb_lst.remove(thumbs_path)
            # 파일 데이터 초기화
            self.__file_data = self.__NP_util.NP_Utils.delete_key_from_value(
                self.__file_data, f_path
            )
            # 파일 리스트 초기화
            self.__file_lst = list(self.__file_data.values())
            for idx in selected_idx:
                # 모델 Row값 삭제
                self.__itemview_model.removeRow(idx.row())
                # 선택 초기화
                self.__item_listview.clearSelection()
                # 플레이 리스트 초기화
                self.__play_lst.clear()
                # UI 새로고침
                self.__itemview_model.layoutChanged.emit()
        self.__lineEdit_debug.setText(f"{len(del_lst)}개 항목 삭제됨")

    def __slot_chg_text_idx(self, move: str) -> None:
        """
        :param move: 순서를 변경할 방향
        플레이 리스트의 순서를 위, 아래로 변경
        """
        selected_indexes = self.__text_listview.selectionModel().selectedIndexes()
        # 아이템이 선택되지 않은 경우 예외 처리
        if not selected_indexes:
            self.__lineEdit_debug.setText("ERROR: 순서를 변경할 파일을 선택하세요")
            self.__slot_messagebox("Move")
            return

        select_idx = selected_indexes[0].row()
        # 위로 이동하는 버튼을 누른 경우
        if move == "up":
            # 선택한 아이템의 인덱스가 0일 경우 예외 처리
            if select_idx == 0:
                return
            # 플레이 리스트의 순서 변경
            self.__play_lst[select_idx - 1], self.__play_lst[select_idx] = (
                self.__play_lst[select_idx],
                self.__play_lst[select_idx - 1],
            )
            # 플레이리스트를 텍스트 파일로 작성
            with open(self.__temp_file, "w") as fp:
                for path in self.__play_lst:
                    fp.write("%s\n" % path)
            # 모델 갱신 후 아이템 재선택
            self.__textview_model = NP_model.NP_ListModel(self.__play_lst)
            self.__text_listview.setModel(self.__textview_model)
            # 인덱스가 존재하는지 검증
            if select_idx is not None:
                model_index = self.__textview_model.index(select_idx - 1, 0)
                self.__text_listview.selectionModel().setCurrentIndex(
                    model_index, QtCore.QItemSelectionModel.ClearAndSelect
                )
        # 아래로 이동하는 버튼을 누른 경우
        elif move == "down":
            # 선택한 아이템의 인덱스가 마지막일 경우 예외 처리
            if select_idx == len(self.__play_lst) - 1:
                return
            # 플레이 리스트의 순서 변경
            self.__play_lst[select_idx], self.__play_lst[select_idx + 1] = (
                self.__play_lst[select_idx + 1],
                self.__play_lst[select_idx],
            )
            # 플레이리스트를 텍스트 파일로 작성
            with open(self.__temp_file, "w") as fp:
                for path in self.__play_lst:
                    fp.write("%s\n" % path)
            # 모델 갱신 후 아이템 재선택
            self.__textview_model = NP_model.NP_ListModel(self.__play_lst)
            self.__text_listview.setModel(self.__textview_model)
            # 인덱스가 존재하는지 검증
            if select_idx is not None:
                model_index = self.__textview_model.index(select_idx + 1, 0)
                self.__text_listview.selectionModel().setCurrentIndex(
                    model_index, QtCore.QItemSelectionModel.ClearAndSelect
                )

    def __slot_messagebox(self, error: str, description=None) -> None:
        """
        :param error: 에러 코드
        에러 코드를 인자로 받아 특정 에러를 메시지 박스로 발생시킴
        Close 버튼만 존재
        """
        box = self.__NP_util.CustomMessageBox(self.__icon_error)
        box.setWindowTitle(f"{error} Error")
        if error == "Play":
            box.setText("\n재생할 파일을 선택하세요.")
            box.exec_()
        elif error == "Import":
            box.setText("\n삽입할 파일을 선택하세요.")
            box.exec_()
        elif error in ["Open", "Delete"]:
            box.setText("\n파일이 선택되지 않았습니다.")
            box.exec_()
        elif error == "Directory":
            box.setText("\n디렉토리가 존재하지 않습니다.")
            box.exec_()
        elif error == "File":
            box.setText("\n파일이 존재하지 않습니다.")
            box.exec_()
        elif error == "Move":
            box.setText("\n순서를 변경할 파일을 선택하세요.")
            box.exec_()
        elif error == "Playlist":
            box.setText("\n멀티 뷰어는 최대 12개의 영상까지만 재생할 수 있습니다.")
            box.exec_()
        elif error == "Nuke":
            box.setText("\n해당 기능은 Nuke에서 실행 시 작동합니다.")
            box.exec_()
        elif error == "File Type":
            box.setText(f"\n'{description}'은(는) 지원하지 않는 형식입니다.")
            box.exec_()
        elif error == "Missing":
            box.setText(f"이미지 시퀀스에 {description}이(가) 존재하지 않습니다.")
            box.exec_()
        elif error == "Sequence":
            box.setText(f"시퀀스 이외의 파일 {description}이(가) 존재합니다.")
            box.exec_()

    def __slot_play_alert(self, error) -> bool:
        """
        :param error: 에러 코드
        에러 코드를 인자로 받아 특정 에러를 메시지 박스로 발생시킴
        Ignore 선택 시 True, No 선택 시 False
        """
        if error == "Resolution":
            box = self.__NP_util.QuestionMessageBox(self.__icon_error)
            box.setWindowTitle("Resolution Warning")
            box.setText(
                "\n고해상도 영상을 멀티 뷰어로 재생할 경우 프레임 드랍이 발생할 수 있습니다." "\n싱글 뷰어로 재생하는 것을 권장합니다."
            )
            res = box.exec_()
            if res:
                return True
            else:
                return False

    def __slot_menu_help(self, idx: int) -> None:
        """
        Help 메뉴 클릭 시 커스텀 메시지 박스 발생
        """
        if idx == 0:
            box = self.__NP_util.CustomMessageBox(self.__icon_info)
            box.setWindowTitle("Multiple Video Player")
            box.setText(
                "\n"
                "드래그 앤 드롭을 활용해 영상 등록 후\n"
                "손 쉽게 노드 생성이 가능한 멀티 비디오 플레이어\n"
                "해상도가 높은 파일의 경우 다중 재생이 어려울 수 있음"
            )
            box.exec_()
        if idx == 1:
            box = self.__NP_util.CustomMessageBox("")
            box.setWindowTitle("Keyboard Shortcut")
            box.setText(
                "                <Main UI>\n"
                "[F1 ~ F3]            아이콘 크기 조절\n"
                "[Delete]              등록된 영상 삭제\n"
                "[V]                      체크박스 선택/해제\n"
                "[I]                       노드 삽입\n"
                "[Enter, P]            영상 재생\n"
                "\n"
                "           <Single Viewer>\n"
                "[Up, Space, K]    재생 / 일시정지\n"
                "[Right, L]            맨 끝으로 이동\n"
                "[Left, J]               맨 앞으로 이동\n"
                "[Down, Q]           정지\n"
                "[R]                      반복 재생\n"
                "[V]                      표시 형식 변경\n"
                "[F11]                  전체 화면\n"
                "[Esc]                   창 닫기\n"
                "\n"
                "          <Multiple Viewer>\n"
                "[L, Right]            재생\n"
                "[K, Down]           일시정지\n"
                "[J, Left]               정지\n"
                "[M]                     표시 형식 변경\n"
                "[P]                      반복 재생"
            )
            box.exec_()

    def __slot_context(self, point) -> None:
        """
        :param point: 우클릭이 발생한 지점
        리스트뷰의 아이템을 선택 후 우클릭 시 발생하는 context menu설정
        """
        idx = self.__item_listview.indexAt(point)
        if idx.isValid():
            menu = QtWidgets.QMenu()
            font = QtGui.QFont("Sans Serif", 8)
            menu.setStyleSheet(
                """
                QMenu {
                    color: rgb(255, 255, 255);
                    background-color: rgb(70, 70, 70);
                    border: 3px rgb(30, 30, 30);
                }
                QMenu::item {
                    padding: 4px 8px;
                    background-color: transparent;
                    color: rgb(255, 255, 255);
                }
                QMenu::item:selected {
                    background-color: rgb(30, 80, 230);
                    color: rgb(255, 255, 255);
                }
            """
            )
            menu.setFont(font)
            act_1 = menu.addAction("Open in Files")
            act_2 = menu.addAction("Delete")
            act_1.triggered.connect(self.__slot_menu_file1)
            act_2.triggered.connect(self.__slot_del_file)
            menu.exec_(self.__item_listview.mapToGlobal(point))

    def __slot_menu_file1(self) -> None:
        """
        File 탭의 Open in Files 메뉴를 선택하면 선택된 아이템이 존재하는 경로를 파일탐색기로 띄움
        이미 열려있는 경로의 경우 중복하여 열리지 않음
        """
        opened_dir = []  # -> 열린 디렉토리 경로를 저장

        # 선택된 아이템이 있는지 검증
        if not len(self.__play_lst):
            self.__lineEdit_debug.setText("ERROR: 파일이 선택되지 않았습니다")
            self.__slot_messagebox("Open")
            return
        for f_path in self.__play_lst:
            video_dir = os.path.dirname(f_path)
            # 경로의 유형이 디렉토리가 맞는지 검증
            if not os.path.isdir(video_dir):
                self.__lineEdit_debug.setText("ERROR: 올바르지 않은 접근입니다")
                self.__slot_messagebox("Directoty")
                return
            # 존재하는 경로인지 검증
            if not os.path.exists(video_dir):
                self.__lineEdit_debug.setText("ERROR: 존재하지 않는 디렉토리입니다")
                self.__slot_messagebox("Directoty")
                return

            # 이미 열린 디렉토리인지 검증
            if video_dir in opened_dir:
                continue

            # 사용 중인 OS에 따라 작동하도록 설정
            if platform.system() == "Linux":
                os.system(f'xdg-open "{video_dir}"')
            elif platform.system() == "Windows":
                os.system(f'explorer "{video_dir}"')
            elif platform.system() == "Darwin":
                os.system(f'open "{video_dir}"')

            # 정상적으로 열린 디렉토리 경로를 리스트에 추가
            opened_dir.append(video_dir)

    def __slot_selection_item(
        self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection
    ) -> None:
        """
        :param selected: 선택된 아이템 데이터
        :param deselected: 선택해제된 아이템 데이터
        리스트뷰에서 선택된 아이템을 플레이리스트에 추가, 선택이 해제되면 제거
        """
        # 선택된 아이템을 리스트에 추가
        for idx in selected.indexes():
            if not idx.isValid():
                continue
            f_path = self.__file_data.get(idx.row())
            if f_path not in self.__play_lst:
                self.__play_lst.append(f_path)
                self.__play_lst_basename.append(os.path.basename(f_path))
                # 플레이리스트를 텍스트 파일로 작성
                with open(self.__temp_file, "w") as fp:
                    for path in self.__play_lst:
                        fp.write("%s\n" % path)

        # 선택이 해제된 아이템을 리스트에서 제거
        for idx in deselected.indexes():
            if not idx.isValid():
                continue
            f_path = self.__file_data.get(idx.row())
            if f_path in self.__play_lst:
                self.__play_lst.remove(f_path)
                self.__play_lst_basename.remove(os.path.basename(f_path))
                # 플레이리스트를 텍스트 파일로 작성
                with open(self.__temp_file, "w") as fp:
                    for path in self.__play_lst:
                        fp.write("%s\n" % path)

        self.__textview_model = NP_model.NP_ListModel(self.__play_lst)

        # 텍스트 선택 시 시그널 발생
        self.__text_listview.setModel(self.__textview_model)

    def __slot_play_videos(self) -> None:
        """
        play 버튼을 누르면 선택된 아이템과 체크박스 선택 여부에 따라 플레이어 실행
        """
        # 플레이 리스트가 없는 경우 예외 처리
        if not len(self.__play_lst):
            self.__lineEdit_debug.setText("ERROR: 재생할 영상이 선택되지 않았습니다")
            self.__slot_messagebox("Play")
            return

        # 멀티 뷰어가 선택되었으나 선택된 아이템이 1개인 경우 싱글 뷰어로 실행
        if self.__check_viewer.isChecked() and len(self.__play_lst) == 1:
            self.__exec_viewer("sv")
            self.__playing = LoadingDialog_loop()
            self.__playing.setWindowModality(QtCore.Qt.ApplicationModal)
            self.__playing.show()

        # 멀티 뷰어가 선택되지 않으면 싱글 뷰어로 실행
        elif not self.__check_viewer.isChecked():
            self.__exec_viewer("sv")
            self.__playing = LoadingDialog_loop()
            self.__playing.setWindowModality(QtCore.Qt.ApplicationModal)
            self.__playing.show()

        # 멀티 뷰어가 선택되고 아이템이 2개 이상인 경우 멀티 뷰어로 실행
        elif self.__check_viewer.isChecked() and len(self.__play_lst) > 1:
            # 플레이 리스트가 13개 이상인 경우 return
            if len(self.__play_lst) > 12:
                self.__lineEdit_debug.setText("멀티 뷰어는 최대 12개의 영상까지 지원합니다")
                self.__slot_messagebox("Playlist")
                return

            # 4k 이상의 해상도를 가진 파일의 수 확인
            over_lst = []
            for f_path in self.__play_lst:
                (
                    total_pixel,
                    width,
                    height,
                ) = self.__NP_util.NP_Utils.get_video_resolution(f_path)
                if total_pixel > 8294000 or (width > 3000 and height > 2000):
                    over_lst.append(total_pixel)

            # 4k 해상도의 영상을 멀티 뷰어로 재생하는 경우 알림 발생
            if len(over_lst) and len(self.__play_lst) > 1:
                # 사용자가 재생을 거부했을 경우 return
                if not self.__slot_play_alert("Resolution"):
                    return

            self.__exec_viewer("mv")
            self.__playing = LoadingDialog_loop()
            self.__playing.setWindowModality(QtCore.Qt.ApplicationModal)
            self.__playing.show()

    # @staticmethod
    def __exec_viewer(self, viewer: str):
        if viewer == "sv":
            subprocess.Popen("/home/rapa/workspace/python/Nuke_player/NP_SV")
            # sv = self.current_dir + "/NP_libs/player/single_viewer.py"
            # subprocess.Popen(["python3", sv])

        else:
            subprocess.Popen("/home/rapa/workspace/python/Nuke_player/NP_MV")
            # mv = self.current_dir + "/NP_libs/player/multiple_viewer.py"
            # subprocess.Popen(["python3", mv])

    def __slot_import_on_nuke(self) -> None:
        """
        선택된 영상을 누크에서 일정한 간격의 Read 노드로 삽입
        """
        # 아이템이 선택되었는지 검증
        if not len(self.__play_lst):
            self.__lineEdit_debug.setText("ERROR: 삽입할 영상이 선택되지 않았습니다")
            self.__slot_messagebox("Import")
            return

        node_gap = 100  # -> 노드 간 간격
        x_position = 100  # -> X 포지션
        y_position = 0  # -> Y 포지션
        for v_path in self.__play_lst:
            # 스크립트가 Nuke에서 실행되지 않은 경우 예외처리
            try:
                read_node = nuke.createNode("Read")
                read_node["file"].fromUserText(v_path)
                # 노드 위치 설정
                read_node.setXpos(x_position)
                read_node.setYpos(y_position)
                # 다음 노드의 Y 위치 설정
                x_position += node_gap
            except AttributeError as err:
                self.__lineEdit_debug.setText("ERROR: 해당 기능은 Nuke에서 실행 시 작동합니다.")
                self.__slot_messagebox("Nuke")
                return

    def __slot_adjust_icon_size(self, aspect, adjust) -> None:
        """
        :param aspect: 전체 위젯 크기 대비 비율
        :param adjust: 미세 조정을 위한 값
        크기 조정 버튼에 따른 아이콘 크기 재설정 및 활성화/비활성화
        """
        main_size = self.size()
        # 아이콘 사이즈 설정
        icon_w = int(main_size.width() / aspect - adjust)
        icon_h = int(main_size.height() / aspect - adjust)
        self.__item_listview.setIconSize(QtCore.QSize(icon_w, icon_h))

        # 아이콘 사이즈 별 UI 설정
        if aspect == 2:
            self.__item_listview.setFont(QtGui.QFont("Sans Serif", 11))
            self.__btn_icon_size_1.setEnabled(False)
            self.__btn_icon_size_2.setEnabled(True)
            self.__btn_icon_size_3.setEnabled(True)
            self.__btn_icon_size_1.setChecked(True)
            self.__btn_icon_size_2.setChecked(False)
            self.__btn_icon_size_3.setChecked(False)
        elif aspect == 3:
            self.__item_listview.setFont(QtGui.QFont("Sans Serif", 9))
            self.__btn_icon_size_1.setEnabled(True)
            self.__btn_icon_size_2.setEnabled(False)
            self.__btn_icon_size_3.setEnabled(True)
            self.__btn_icon_size_1.setChecked(False)
            self.__btn_icon_size_2.setChecked(True)
            self.__btn_icon_size_3.setChecked(False)
        elif aspect == 4:
            self.__item_listview.setFont(QtGui.QFont("Sans Serif", 7))
            self.__btn_icon_size_1.setEnabled(True)
            self.__btn_icon_size_2.setEnabled(True)
            self.__btn_icon_size_3.setEnabled(False)
            self.__btn_icon_size_1.setChecked(False)
            self.__btn_icon_size_2.setChecked(False)
            self.__btn_icon_size_3.setChecked(True)

    @property
    def file_data(self) -> dict:
        """
        스레드에서 정보를 이용하기 위한 getter
        :return: self.__file_data Getter
        """
        return self.__file_data

    @property
    def thumb_dir(self):
        """
        스레드에서 정보를 이용하기 위한 getter
        :return: self.__thumb_dir Getter
        """
        return self.__thumb_dir


################################## NUKE ########################################

#
# def getNukeMainWindow():
#     for obj in QtWidgets.QApplication.topLevelWidgets():
#         if obj.metaObject().className() == "Foundry::UI::DockMainWindow":
#             return obj
#     return None
#
#
# # Main 클래스 인스턴스를 반환하는 팩토리 함수
# def createMainPanel():
#     # Nuke의 메인 윈도우를 부모로 사용하여 Main 인스턴스 생성
#     widget = Nuke_Player(parent=getNukeMainWindow())
#     widget.setObjectName("MyCustomPanel")  # 옵션: 패널의 고유 이름 설정
#     return widget
#
#
# # Nuke 패널로 등록
# panelId = "uk.co.thefoundry.Main"
# nukescripts.panels.registerWidgetAsPanel(
#     "createMainPanel", "My Custom Panel", panelId  # 팩토리 함수 이름  # 패널의 표시 이름
# )
#
# # Nuke 메뉴에 패널 추가
# nuke.menu("Nuke").addCommand(
#     "Custom Tools/Nuke Player",
#     lambda: nukescripts.panels.restorePanel(panelId),  # 패널 복원 또는 생성
# )

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    NP = Nuke_Player()
    NP.show()
    app.exec_()
