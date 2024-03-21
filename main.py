#!/usr/bin/env python
# encoding=utf-8
# author        : Juno Park
# created date  : 2024.02.26
# modified date : 2024.03.21
# description   : 누크에서 작업을 시작하기 전, 다양한 소스를 동시에 확인하는 것에 어려움이 있는데,
#                 이러한 불편함을 해소하고자, 유저 친화적인 플레이어를 제작.
#                 드래그앤드랍으로 간편하게 소스를 등록하고, 영상을 재생하며,
#                 소스를 확인하는 동시에 DCC툴의 노드로 불러오는 것이 가능함.

import sys
import importlib
import os

os.environ["NUKE_INTERACTIVE"] = "1"
import nuke
import shutil
import pathlib
import mimetypes
import platform

sys.path.append("/home/rapa/workspace/python/Nuke_player")
import muliple_viewer

from PySide2 import QtWidgets, QtGui, QtCore

from view import NP_view
from model import NP_model
from library.qt import library as qt_lib
from library.system import library as sys_lib
from library import NP_Utils

importlib.reload(NP_view)
importlib.reload(NP_model)
importlib.reload(NP_Utils)
importlib.reload(qt_lib)
importlib.reload(sys_lib)
importlib.reload(muliple_viewer)


class FileProcessingThread(QtCore.QThread):
    thumbnail_extract = QtCore.Signal()
    finished = QtCore.Signal()

    def __init__(self, file_data: dict, thumbnail_dir: str):
        super().__init__()
        self.__file_data = file_data
        self.__thumb_dir = thumbnail_dir
        self.__NP_util = NP_Utils
        self.__cancled = False

    def run(self):
        total_files = len(self.__file_data)
        completed = 0
        for idx, f_path in self.__file_data.items():
            if self.__cancled:
                break
            base_name = os.path.splitext(os.path.basename(f_path))[0]
            file_name = self.__thumb_dir + "/" + base_name + ".jpg"
            if os.path.exists(file_name):
                completed += 1
                continue
            self.__NP_util.NP_Utils.extract_thumbnail(f_path, file_name, "1280x720")
            self.thumbnail_extract.emit()
            completed += 1
            if total_files == completed:
                break
        self.finished.emit()

    def stop(self):
        self.quit()
        self.wait(10000)
        print("\n\033[31m백그라운드 스레드 정상 종료\033[0m")

    def cancel(self):
        self.__cancled = True
        print("\n\033[31m파일 로드 취소됨\033[0m")


class LoadingDialog(QtWidgets.QProgressDialog):
    def __init__(self, total_files, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Loading")
        self.setLabelText("파일을 로드 중입니다.")
        self.setFixedSize(300, 100)
        self.setRange(0, total_files)
        self.setValue(0)
        self.setFont(QtGui.QFont("Sans Serif", 9))
        self.setStyleSheet(
            "color: rgb(255, 255, 255);" "background-color: rgb(70, 70, 70);"
        )
        self.setModal(True)

    def increase_value(self):
        self.setValue(self.value() + 1)

    def reject(self):
        # 취소 버튼을 눌렀을 때 시그널 발생
        self.canceled.emit()
        super().reject()


class Nuke_Player(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        # 변수 설정
        self.__NP_util = NP_Utils
        self.__item_listview = NP_view.NP_ItemView()
        self.__text_listview = NP_view.NP_ListView()

        # 썸네일을 임시 저장할 상대경로 설정
        # self.current_dir = os.path.dirname(__file__)
        self.home_dir = os.path.expanduser("~")
        self.__thumb_dir = os.path.join(self.home_dir, ".NP_thumbnails")  # -> 숨김 상태로 생성

        # 해당 디렉토리가 없을 경우 생성
        self.__NP_util.NP_Utils.make_dir(self.__thumb_dir)

        self.__file_data = dict()  # {인덱스: 원본 파일 경로}의 형태로 데이터 저장
        self.__file_lst = list()  # file_data의 value값을 리스트로 저장
        self.__thumb_lst = list()  # 썸네일 디렉토리 내의 파일 경로를 리스트로 저장
        self.__play_lst = list()  # 선택된 파일의 경로를 인덱스로 저장
        self.__play_lst_basename = list()

        # 모델 설정
        self.__itemview_model = NP_model.NP_ItemModel(self.__thumb_lst, self.__file_lst)
        self.__item_listview.setModel(self.__itemview_model)
        self.__textview_model = NP_model.NP_ListModel(self.__play_lst)
        self.__text_listview.setModel(self.__textview_model)

        # Init set
        self.__set_ui()
        self.__set_menu()
        self.__connection()

        # 스레드 생성 및 실행
        self.__thumb_thread = FileProcessingThread(self.__file_data, self.__thumb_dir)
        self.__item_listview.setIconSize(QtCore.QSize(229, 109))

    def __cleanup(self) -> None:
        """
        프로그램이 종료될 때 임시 디렉토리를 삭제
        """
        try:
            shutil.rmtree(self.__thumb_dir)
            print(f"\033[32m\n임시 디렉토리 '{self.__thumb_dir}'가 성공적으로 삭제되었습니다.\033[0m")
        except Exception as err:
            print(
                f"\033[31m\nERROR: 임시 디렉토리 '{self.__thumb_dir}'를 삭제하는 동안 오류가 발생했습니다:\033[0m",
                err,
            )

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
        self.__adjust_size_1 = QtWidgets.QPushButton("", self)
        self.__adjust_size_2 = QtWidgets.QPushButton("", self)
        self.__adjust_size_3 = QtWidgets.QPushButton("", self)
        self.__btn_idx_up = QtWidgets.QPushButton()
        self.__btn_idx_down = QtWidgets.QPushButton()
        self.__adjust_size_1.setIcon(
            QtGui.QIcon("/home/rapa/workspace/python/Nuke_player/resource/png/1x1.png")
        )
        self.__adjust_size_2.setIcon(
            QtGui.QIcon("/home/rapa/workspace/python/Nuke_player/resource/png/2x2.png")
        )
        self.__adjust_size_3.setIcon(
            QtGui.QIcon("/home/rapa/workspace/python/Nuke_player/resource/png/3x3.png")
        )
        self.__btn_idx_up.setIcon(
            QtGui.QIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowUp))
        )
        self.__btn_idx_down.setIcon(
            QtGui.QIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowDown))
        )
        self.__adjust_size_1.setCheckable(True)
        self.__adjust_size_2.setCheckable(True)
        self.__adjust_size_3.setCheckable(True)
        self.__adjust_size_1.setChecked(False)
        self.__adjust_size_2.setChecked(True)
        self.__adjust_size_3.setChecked(False)

        self.__adjust_size_1.setFixedSize(25, 25)
        self.__adjust_size_2.setFixedSize(25, 25)
        self.__adjust_size_3.setFixedSize(25, 25)

        self.__btn_play = QtWidgets.QPushButton("Play")
        self.__btn_play.setFixedSize(70, 25)
        self.__btn_import = QtWidgets.QPushButton("Import")
        self.__btn_import.setFixedSize(70, 25)

        self.__adjust_size_1.setToolTip("Set Icon Size Maximum (F1)")
        self.__adjust_size_2.setToolTip("Set Icon Size Normal (F2)")
        self.__adjust_size_3.setToolTip("Set Icon Size Minimum (F3)")
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
        hbox_btn.addWidget(self.__adjust_size_1)
        hbox_btn.addWidget(self.__adjust_size_2)
        hbox_btn.addWidget(self.__adjust_size_3)
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
        widget_1.setLayout(main_hbox)
        self.setCentralWidget(widget_1)
        qt_lib.QtLibs.center_on_screen(self)
        self.setWindowTitle("Video Player")
        self.setStyleSheet(
            "color: rgb(255, 255, 255);" "background-color: rgb(70, 70, 70);"
        )

    def __set_menu(self) -> None:
        # menu
        menubar = QtWidgets.QMenuBar()
        menu_file = menubar.addMenu("File")
        menu_help = menubar.addMenu("Help")
        self.file_1 = QtWidgets.QAction("Open Directory", self)
        self.file_2 = QtWidgets.QAction("Exit", self)
        self.help_1 = QtWidgets.QAction("What's this?", self)
        self.help_2 = QtWidgets.QAction("Keyboard Shortcut", self)
        self.file_1.setShortcut(QtGui.QKeySequence("Ctrl+D"))
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
        self.__adjust_size_1.clicked.connect(
            lambda: self.__slot_adjust_icon_size(2, 75)
        )
        self.__adjust_size_1.clicked.connect(lambda: self.__adjust_size_btn(1))
        self.__adjust_size_2.clicked.connect(
            lambda: self.__slot_adjust_icon_size(3, 51)
        )
        self.__adjust_size_2.clicked.connect(lambda: self.__adjust_size_btn(2))
        self.__adjust_size_3.clicked.connect(
            lambda: self.__slot_adjust_icon_size(4, 40)
        )
        self.__adjust_size_3.clicked.connect(lambda: self.__adjust_size_btn(3))
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
        self.file_1.triggered.connect(self.__slot_open_in_dir)
        self.file_2.triggered.connect(self.close)
        self.help_1.triggered.connect(self.__slot_whats_this)
        self.help_2.triggered.connect(self.__slot_shortcut)

    def closeEvent(self, event):
        if self.__thumb_thread.isRunning():
            self.__thumb_thread.stop()
            self.__thumb_thread.wait()
        self.__cleanup()

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == QtCore.Qt.Key_F1:
            self.__adjust_size_1.click()
            self.__adjust_size_btn(1)
        elif event.key() == QtCore.Qt.Key_F2:
            self.__adjust_size_2.click()
            self.__adjust_size_btn(2)
        elif event.key() == QtCore.Qt.Key_F3:
            self.__adjust_size_3.click()
            self.__adjust_size_btn(3)
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

    def __dragEnter_list(self, event: QtGui.QDragEnterEvent) -> None:
        if event.mimeData().hasText():
            print(event.mimeData().text())
            event.acceptProposedAction()
        else:
            event.ignore()

    def __dragMove_list(self, event: QtGui.QDragMoveEvent) -> None:
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def __drop_list(self, event: QtGui.QDropEvent) -> None:
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

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

    def __drop_items(self, event: QtGui.QDropEvent):
        """
        ListView내에서 드롭되었을 경우 해당 데이터의 URL(파일 경로)을
        딕셔너리에 저장 후 각 파일의 썸네일을 추출하여 임시 디렉토리에 저장하고
        모델에서 데이터를 다시 로드하여 UI를 새로 불러옴
        썸네일 추출의 경우 스레드를 통해 백그라운드에서 진행
        """
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            urls = event.mimeData().urls()

            file_dropped = False  # 파일이 드롭되었는지 확인하기 위한 변수
            # 파일 경로 저장
            for idx, url in enumerate(urls):
                file_path = url.toLocalFile()
                url_str = url.toString()
                if not self.__is_file_video(url_str):
                    print(f"\033[31mERROR: '{file_path}'는 지원하지 않는 형식입니다.\033[0m")
                    return

                if file_path in self.__file_data.values():
                    print(f"\033[31mERROR: '{file_path}'가 이미 등록되었습니다.\033[0m")
                    continue

                if idx in self.__file_data.keys():
                    last_idx = list(self.__file_data.keys())[-1]
                    self.__file_data[last_idx + 1] = file_path
                else:
                    self.__file_data[idx] = file_path

                file_dropped = True
            if file_dropped:
                # 로딩 바 발생
                self.__loading_dialog = LoadingDialog(len(urls))
                self.__loading_dialog.setWindowModality(QtCore.Qt.ApplicationModal)
                self.__loading_dialog.canceled.connect(self.__thumb_thread.cancel)
                self.__loading_dialog.show()
                self.__thumb_thread.thumbnail_extract.connect(
                    self.__loading_dialog.increase_value
                )
                self.__thumb_thread.finished.connect(self.__extract_finished)
                self.__thumb_thread.start()

            event.acceptProposedAction()
        else:
            event.ignore()

    def __extract_finished(self):
        """
        스레드 작업 완료 후 호출되는 메서드
        썸네일 추출이 완료되면 모델을 업데이트하여 UI를 새로고침
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

        # 아이템 선택 시 시그널 발생
        self.__item_listview.selectionModel().selectionChanged.connect(
            self.__slot_selection_item
        )

        # 로딩 바 종료
        self.__loading_dialog.hide()
        self.__lineEdit_debug.setText("파일을 선택하세요")

    def __slot_del_file(self):
        """
        선택된 아이템의 데이터 삭제 후 모델 갱신
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
            if os.path.exists(thumbs_path):
                # 썸네일 제거
                os.remove(thumbs_path)
                # 썸네일 리스트 제거
                self.__thumb_lst.remove(thumbs_path)
                # 파일 데이터 제거
                self.__file_data = self.delete_key_from_value(self.__file_data, f_path)
                # 파일 리스트 재정의
                self.__file_lst = list(self.__file_data.values())
            else:
                self.__lineEdit_debug.setText("ERROR: 삭제할 파일이 존재하지 않습니다")
                self.__slot_messagebox("File")
                return

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

    def __slot_chg_text_idx(self, move: str):
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
            # 모델 갱신 후 아이템 재선택
            self.__textview_model = NP_model.NP_ListModel(self.__play_lst)
            self.__text_listview.setModel(self.__textview_model)
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
            # 모델 갱신 후 아이템 재선택
            self.__textview_model = NP_model.NP_ListModel(self.__play_lst)
            self.__text_listview.setModel(self.__textview_model)
            if select_idx is not None:
                model_index = self.__textview_model.index(select_idx + 1, 0)
                self.__text_listview.selectionModel().setCurrentIndex(
                    model_index, QtCore.QItemSelectionModel.ClearAndSelect
                )

    def __slot_messagebox(self, error: str):
        """
        :param error: 에러 코드
        에러 코드를 인자로 받아 특정 에러를 메시지 박스로 발생시킴
        Close 버튼만 존재
        """
        box = self.__NP_util.CustomMessageBox(self.__icon_error)
        box.setWindowTitle(f"{error} Error")
        if error == "Play":
            box.setText("\n재생할 파일을 선택하세요")
            box.exec_()
        elif error == "Import":
            box.setText("\n삽입할 파일을 선택하세요")
            box.exec_()
        elif error in ["Open", "Delete"]:
            box.setText("\n파일이 선택되지 않았습니다")
            box.exec_()
        elif error == "Directory":
            box.setText("\n디렉토리가 존재하지 않습니다")
            box.exec_()
        elif error == "File":
            box.setText("\n파일이 존재하지 않습니다")
            box.exec_()
        elif error == "Move":
            box.setText("\n순서를 변경할 파일을 선택하세요")
            box.exec_()
        elif error == "Playlist":
            box.setText("\n멀티 뷰어는 최대 12개의 영상까지만 재생할 수 있습니다")
            box.exec_()

    def __slot_play_alert(self, error):
        """
        :param error: 에러 코드
        에러 코드를 인자로 받아 특정 에러를 메시지 박스로 발생시킴
        Ignore, No버튼에 따라 bool 반환
        """
        if error == "Resolution":
            box = self.__NP_util.QuestionMessageBox(self.__icon_error)
            box.setWindowTitle("Resolution Warning")
            box.setText(
                "\n4K 이상의 영상을 멀티 뷰어로 재생할 경우 프레임 드랍이 발생할 수 있습니다."
                "\n싱글 뷰어로 재생하는 것을 권장합니다."
            )
            res = box.exec_()
            if res:
                return True
            else:
                return False

    def __slot_whats_this(self):
        box = self.__NP_util.CustomMessageBox(self.__icon_info)
        box.setWindowTitle("Multiple Video Player")
        box.setText(
            "\n"
            "드래그 앤 드롭을 활용해 영상 등록 후\n"
            "손 쉽게 노드 생성이 가능한 멀티 비디오 플레이어\n"
            "해상도가 높은 파일의 경우 다중 재생이 어려울 수 있음"
        )
        box.exec_()

    def __slot_shortcut(self):
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

    def __adjust_size_btn(self, num):
        if num == 1:
            self.__adjust_size_1.setChecked(True)
            self.__adjust_size_2.setChecked(False)
            self.__adjust_size_3.setChecked(False)
        elif num == 2:
            self.__adjust_size_1.setChecked(False)
            self.__adjust_size_2.setChecked(True)
            self.__adjust_size_3.setChecked(False)
        elif num == 3:
            self.__adjust_size_1.setChecked(False)
            self.__adjust_size_2.setChecked(False)
            self.__adjust_size_3.setChecked(True)

    def __slot_context(self, point):
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
            act_1 = menu.addAction("Open in Dir")
            act_2 = menu.addAction("Delete")
            # act_1.triggered.connect(lambda: self.__slot_open_in_dir(idx))
            act_1.triggered.connect(self.__slot_open_in_dir)
            act_2.triggered.connect(self.__slot_del_file)
            menu.exec_(self.__item_listview.mapToGlobal(point))

    def __slot_open_in_dir(self):
        # 열린 디렉토리의 이름을 저장
        opened_dir = []

        if not len(self.__play_lst):
            self.__lineEdit_debug.setText("ERROR: 파일이 선택되지 않았습니다")
            self.__slot_messagebox("Open")
        for f_path in self.__play_lst:
            video_dir = os.path.dirname(f_path)
            if not os.path.isdir(video_dir):
                self.__lineEdit_debug.setText("ERROR: 올바르지 않은 접근입니다")
                self.__slot_messagebox("Directoty")
                return
            if not os.path.exists(video_dir):
                self.__lineEdit_debug.setText("ERROR: 존재하지 않는 디렉토리입니다")
                self.__slot_messagebox("Directoty")
                return

            # 같은 디렉토리는 중복해서 열리지 않도록 처리
            if video_dir in opened_dir:
                continue
            if platform.system() == "Linux":
                os.system(f'xdg-open "{video_dir}"')
            elif platform.system() == "Windows":
                os.system(f'explorer "{video_dir}"')
            elif platform.system() == "Darwin":
                os.system(f'open "{video_dir}"')

            opened_dir.append(video_dir)

    def __slot_selection_item(
        self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection
    ) -> None:
        # 선택된 아이템을 리스트에 추가
        for idx in selected.indexes():
            if not idx.isValid():
                continue
            f_path = self.__file_data.get(idx.row())
            if f_path not in self.__play_lst:
                self.__play_lst.append(f_path)
                self.__play_lst_basename.append(os.path.basename(f_path))

        # 선택이 해제된 아이템을 리스트에서 제거
        for idx in deselected.indexes():
            if not idx.isValid():
                continue
            f_path = self.__file_data.get(idx.row())
            if f_path in self.__play_lst:
                self.__play_lst.remove(f_path)
                self.__play_lst_basename.remove(os.path.basename(f_path))

        self.__textview_model = NP_model.NP_ListModel(self.__play_lst)

        # 텍스트 선택 시 시그널 발생
        self.__text_listview.setModel(self.__textview_model)

    def __slot_play_videos(self):
        # 플레이 리스트가 없는 경우 예외 처리
        if len(self.__play_lst):
            pass
        else:
            self.__lineEdit_debug.setText("ERROR: 재생할 영상이 선택되지 않았습니다")
            self.__slot_messagebox("Play")
            return

        # 선택된 영상의 수 및 체크박스 선택 여부에 따라 플레이어 설정
        if self.__check_viewer.isChecked() and len(self.__play_lst) == 1:
            self.__sing_vw = self.__NP_util.VideoWidget(self.__play_lst)
            self.__sing_vw.show()

        elif not self.__check_viewer.isChecked():
            self.__sing_vw = self.__NP_util.VideoWidget(self.__play_lst)
            self.__sing_vw.show()

        # 멀티 뷰어로 재생
        elif self.__check_viewer.isChecked() and len(self.__play_lst) > 1:
            # 플레이 리스트가 13개 이상인 경우 return
            if len(self.__play_lst) > 12:
                self.__lineEdit_debug.setText("멀티 뷰어는 최대 12개의 영상까지 지원합니다")
                self.__slot_messagebox("Playlist")
                return

            # 해상도가 높은 파일의 개수 확인
            over_lst = []
            for f_path in self.__play_lst:
                total_pixel = self.__NP_util.NP_Utils.get_video_resolution(f_path)
                if total_pixel > 8294000:
                    over_lst.append(total_pixel)
            # 4k 해상도의 영상이 존재하는 경우 알림 발생
            if len(over_lst) and len(self.__play_lst) > 1:
                if not self.__slot_play_alert("Resolution"):
                    return
            self.__mult_vw = muliple_viewer.MultipleViewer(self.__play_lst)
            self.__mult_vw.show()

    def __slot_import_on_nuke(self):
        """
        선택된 영상을 누크에서 일정한 간격의 Read 노드로 삽입
        """
        if len(self.__play_lst):
            node_gap = 100
            x_position = 100
            y_position = 0
            for v_path in self.__play_lst:
                read_node = nuke.createNode("Read")
                read_node["file"].fromUserText(v_path)
                # 노드 위치 설정
                read_node.setXpos(x_position)
                read_node.setYpos(y_position)
                # 다음 노드의 Y 위치 설정
                x_position += node_gap
                print(v_path)
        else:
            self.__lineEdit_debug.setText("ERROR: 삽입할 영상이 선택되지 않았습니다")
            self.__slot_messagebox("Import")
            return

    def __slot_adjust_icon_size(self, aspect, adjust) -> None:
        """
        :param aspect: 전체 위젯 크기 대비 비율
        :param adjust: 미세 조정을 위한 값
        크기 조정 버튼에 따른 아이콘 크기 재설정
        """
        main_size = self.size()
        icon_w = int(main_size.width() / aspect - adjust)
        icon_h = int(main_size.height() / aspect - adjust)
        self.__item_listview.setIconSize(QtCore.QSize(icon_w, icon_h))
        if aspect == 2:
            self.__item_listview.setFont(QtGui.QFont("Sans Serif", 10))
            self.__adjust_size_1.setEnabled(False)
            self.__adjust_size_2.setEnabled(True)
            self.__adjust_size_3.setEnabled(True)
        elif aspect == 3:
            self.__item_listview.setFont(QtGui.QFont("Sans Serif", 9))
            self.__adjust_size_1.setEnabled(True)
            self.__adjust_size_2.setEnabled(False)
            self.__adjust_size_3.setEnabled(True)
        elif aspect == 4:
            self.__item_listview.setFont(QtGui.QFont("Sans Serif", 6))
            self.__adjust_size_1.setEnabled(True)
            self.__adjust_size_2.setEnabled(True)
            self.__adjust_size_3.setEnabled(False)

    @property
    def file_data(self):
        return self.__file_data

    @property
    def thumb_dir(self):
        return self.__thumb_dir

    @staticmethod
    def delete_key_from_value(dictionary: dict, value):
        """
        :param dictionary: 데이터를 삭제할 딕셔너리
        :param value: 찾고자 하는 value
        :return: 찾은 value가 존재하는 key값을 삭제한 후 index를 재부여한 딕셔너리
        ex) {0: 123, 1: 456, 2: 789} >>> value = 456 >>> {0: 123, 1: 789}
        """
        keys_to_del = []
        new_dict = dict()
        for key, val in dictionary.items():
            if val == value:
                keys_to_del.append(key)
        for key in keys_to_del:
            del dictionary[key]
        for idx, val in enumerate(list(dictionary.values())):
            new_dict[idx] = val
        return new_dict

    @staticmethod
    def __is_file_video(file_path: str) -> bool:
        """
        :param file_path: 파일 경로
        :return: 해당 파일이 비디오 형식이면 True, 그렇지 않으면 False를 반환
        """
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is not None and mime_type.startswith("video"):
            return True
        else:
            return False


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    NP = Nuke_Player()
    NP.show()
    app.exec_()
