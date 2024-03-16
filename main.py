#!/usr/bin/env python
# encoding=utf-8
# author        : Juno Park
# created date  : 2024.02.26
# modified date : 2024.02.26
# description   :

# TODO: 누크 연동 시 Crash 발생하는 현상 수정 필요
# TODO: UI에서 드래그가 되지 않는 것 수정 필요
# TODO: View에서 우클릭 시 컨텍스트 메뉴가 발생하지 않음
# TODO: Pushbutton에 아이콘이 적용되지 않음
# TODO: slider 클릭 시 해당 부분으로 영상 포지션 이동
# TODO: QWidget::paintEngine: Should no longer be called 에러 처리 필요 >> 무시해도 된다고 함


import sys
import importlib
import os

os.environ["NUKE_INTERACTIVE"] = "1"
import nuke
import shutil
import atexit
import pathlib
import mimetypes
import platform

sys.path.append("/home/rapa/workspace/python/Nuke_player/muliple_viewer.py")
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
        self.thumb_dir = os.path.join(self.home_dir, ".NP_thumbnails")  # -> 숨김 상태로 생성

        # 해당 디렉토리가 없을 경우 생성
        self.__NP_util.NP_Utils.make_dir(self.thumb_dir)

        self.__file_data = dict()  # {인덱스: 원본 파일 경로}의 형태로 데이터 저장
        self.__file_lst = list()
        self.__thumb_lst = list()  # 썸네일 디렉토리 내의 파일 경로를 리스트로 저장
        self.__play_lst = list()  # 선택된 파일의 경로를 인덱스로 저장
        self.__play_lst_basename = list()

        # 모델 설정
        self.__itemview_model = NP_model.NP_ItemModel(self.__thumb_lst, self.__file_lst)
        self.__item_listview.setModel(self.__itemview_model)
        self.__listview_model = NP_model.NP_ListModel(self.__play_lst)
        self.__text_listview.setModel(self.__listview_model)

        # Init set
        self.__set_ui()
        self.__connection()

        self.__item_listview.setIconSize(QtCore.QSize(229, 109))

        # 프로그램 종료 시 임시파일 삭제
        atexit.register(self.__cleanup)

    def __cleanup(self) -> None:
        """
        프로그램이 종료될 때 임시 디렉토리를 삭제
        """
        try:
            shutil.rmtree(self.thumb_dir)
            print(f"\033[32m\n임시 디렉토리 '{self.thumb_dir}'가 성공적으로 삭제되었습니다.\033[0m")
        except Exception as err:
            print(
                f"\033[31m\nERROR: 임시 디렉토리 '{self.thumb_dir}'를 삭제하는 동안 오류가 발생했습니다:\033[0m",
                err,
            )

    def __set_ui(self) -> None:
        """
        메인 UI 요소 생성 및 설정
        """
        # fonts
        font_1 = QtGui.QFont("Sans Serif", 10)
        font_2 = QtGui.QFont("Sans Serif", 8)
        font_3 = QtGui.QFont("Sans Serif", 10)
        self.setFont(font_1)

        # widget
        widget_1 = QtWidgets.QWidget()
        vbox_1 = QtWidgets.QVBoxLayout()
        vbox_2 = QtWidgets.QVBoxLayout()

        # btns
        hbox_btn = QtWidgets.QHBoxLayout()
        self.__adjust_size_1 = QtWidgets.QPushButton("", self)
        self.__adjust_size_2 = QtWidgets.QPushButton("", self)
        self.__adjust_size_3 = QtWidgets.QPushButton("", self)
        self.__adjust_size_1.setIcon(
            QtGui.QIcon("/home/rapa/workspace/python/Nuke_player/resource/png/1x1.png")
        )
        self.__adjust_size_2.setIcon(
            QtGui.QIcon("/home/rapa/workspace/python/Nuke_player/resource/png/2x2.png")
        )
        self.__adjust_size_3.setIcon(
            QtGui.QIcon("/home/rapa/workspace/python/Nuke_player/resource/png/3x3.png")
        )

        self.__adjust_size_1.setFixedSize(25, 25)
        self.__adjust_size_2.setFixedSize(25, 25)
        self.__adjust_size_3.setFixedSize(25, 25)
        self.h_spacer = QtWidgets.QSpacerItem(
            200, 25, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
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
        self.__lineEdit_debug.setFont(font_2)
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
        label_list.setFont(font_3)

        hbox_btn.addWidget(self.__adjust_size_1)
        hbox_btn.addWidget(self.__adjust_size_2)
        hbox_btn.addWidget(self.__adjust_size_3)
        hbox_btn.addWidget(self.__lineEdit_debug)
        # hbox_btn.addItem(self.h_spacer)
        hbox_btn.addWidget(self.__btn_import)
        hbox_btn.addWidget(self.__btn_play)

        hbox_checkBox.addWidget(check_label)
        hbox_checkBox.addWidget(self.__check_viewer)

        vbox_1.addWidget(self.__item_listview)
        vbox_1.addLayout(hbox_checkBox)
        vbox_1.addLayout(hbox_btn)
        vbox_2.addWidget(label_list)
        vbox_2.addWidget(self.__text_listview)
        main_hbox = QtWidgets.QHBoxLayout()
        main_hbox.addLayout(vbox_1)
        main_hbox.addLayout(vbox_2)

        # set widget
        self.setFixedSize(840, 480)
        widget_1.setLayout(main_hbox)
        self.setCentralWidget(widget_1)
        qt_lib.QtLibs.center_on_screen(self)
        self.setWindowTitle("Nuke Player")
        self.setStyleSheet(
            "color: rgb(255, 255, 255);" "background-color: rgb(70, 70, 70);"
        )

    def __connection(self) -> None:
        """
        UI 상호작용 시 시그널 발생
        """
        # 버튼 클릭 시 시그널 발생
        self.__adjust_size_1.clicked.connect(lambda: self.__update_icon_size(2, 75))
        self.__adjust_size_2.clicked.connect(lambda: self.__update_icon_size(3, 51))
        self.__adjust_size_3.clicked.connect(lambda: self.__update_icon_size(4, 40))
        self.__btn_play.clicked.connect(self.__slot_play_videos)
        self.__btn_import.clicked.connect(self.__slot_import_on_nuke)

        # 드래그 or 드랍 시 시그널 발생
        self.__item_listview.dragEnterEvent = self.__dragEnter_items
        self.__item_listview.dragMoveEvent = self.__dragMove_items
        self.__item_listview.dropEvent = self.__drop_items
        # self.__text_listview.dragEnterEvent = self.__dragEnter_list
        # self.__text_listview.dragMoveEvent = self.__dragMove_list
        # self.__text_listview.dropEvent = self.__drop_list
        # self.__text_listview.mousePressEvent = self.__mouseDrag_list

        # 우클릭 시 컨텍스트 메뉴 발생
        self.__item_listview.customContextMenuRequested.connect(self.__slot_context)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == QtCore.Qt.Key_F1:
            self.__adjust_size_1.click()
        elif event.key() == QtCore.Qt.Key_F2:
            self.__adjust_size_2.click()
        elif event.key() == QtCore.Qt.Key_F3:
            self.__adjust_size_3.click()
        elif event.key() == QtCore.Qt.Key_V:
            if self.__check_viewer.isChecked():
                print("v")
                self.__check_viewer.setChecked(False)
            else:
                print("V")
                self.__check_viewer.setChecked(True)
        elif event.key() == QtCore.Qt.Key_I:
            self.__slot_import_on_nuke()
        elif event.key() in [
            QtCore.Qt.Key_Enter,
            QtCore.Qt.Key_Return,
            QtCore.Qt.Key_P,
        ]:
            self.__slot_play_videos()

    def __mouseDrag_list(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            drag = QtGui.QDrag(self)
            mime_data = QtCore.QMimeData()
            mime_data.setText("hi")
            drag.setMimeData(mime_data)
            drag.exec_(QtCore.Qt.MoveAction)

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

    def __drop_items(self, event: QtGui.QDropEvent) -> None:
        """
        ListView내에서 드롭되었을 경우 해당 데이터의 URL(파일 경로)을
        딕셔너리에 저장 후 각 파일의 썸네일을 추출하여 임시 디렉토리에 저장
        모델에서 데이터를 다시 로드하여 UI를 새로 불러옴
        """
        self.__lineEdit_debug.setText("파일 로드 중")
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            urls = event.mimeData().urls()

            # 1개 이상의 파일이 드롭 되는 경우, idx와 url을 딕셔너리에 저장
            for idx, url in enumerate(urls):
                file_path = url.toLocalFile()
                url_str = url.toString()
                # 드롭한 파일이 비디오 형식이 맞는지 확인
                if not self.__is_file_video(url_str):
                    print(f"\033[31mERROR: '{file_path}'는 지원하지 않는 형식입니다.\033[0m")
                    return
                else:
                    pass
                # 딕셔너리 안에 이미 파일 경로가 존재할 경우
                if file_path in self.__file_data.values():
                    print(f"\033[31mERROR: '{file_path}'가 이미 등록되었습니다.\033[0m")
                    continue

                # 등록 순으로 idx를 부여하기 위함
                if idx in self.__file_data.keys():
                    last_idx = list(self.__file_data.keys())[-1]
                    self.__file_data[last_idx + 1] = file_path

                # 최초 등록 시
                else:
                    self.__file_data[idx] = file_path
            # 썸네일 추출
            self.__extract_thumbnails()

            # 썸네일 디렉토리의 파일 검색 후 모델 새로고침
            self.__thumb_lst = list(
                map(
                    lambda x: x.as_posix(),
                    sys_lib.System.get_files_lst(pathlib.Path(self.thumb_dir), ".jpg"),
                )
            )
            self.__file_lst = list(self.__file_data.values())
            self.__itemview_model = NP_model.NP_ItemModel(
                self.__thumb_lst, self.__file_lst
            )
            self.__item_listview.setModel(self.__itemview_model)
            # print(f'\033[32m{self.__file_data}\n파일 불러오기 완료\033[0m')

            # 아이템 선택 시 시그널 발생
            self.__item_listview.selectionModel().selectionChanged.connect(
                self.__slot_icon_idxs
            )
            self.__lineEdit_debug.setText("로드 완료")
            event.acceptProposedAction()
        else:
            event.ignore()

    def __is_file_video(self, file_path: str) -> bool:
        """
        :param file_path: 파일 경로
        :return: 해당 파일이 비디오 형식이면 True, 그렇지 않으면 False를 반환
        """
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is not None and mime_type.startswith("video"):
            return True
        else:
            return False

    def __extract_thumbnails(self) -> None:
        """
        ffmpeg 모듈을 활용하여 영상에서 썸네일 추출.
        임시 썸네일 폴더에 '.jpg'확장자로 썸네일 저장
        """
        for idx, f_path in self.__file_data.items():
            base_name = os.path.splitext(os.path.basename(f_path))[0]
            file_name = self.thumb_dir + "/" + base_name + ".jpg"
            if os.path.exists(file_name):
                continue
            # self.__NP_util.NP_Utils.extract_thumbnail(f_path, file_name, '1920x1080')
            self.__NP_util.NP_Utils.extract_thumbnail_subprocess(
                f_path, file_name, "1920x1080"
            )

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
            act_1.triggered.connect(lambda: self.__slot_open_in_dir(idx))
            menu.exec_(self.__item_listview.mapToGlobal(point))

    def __slot_open_in_dir(self, index):
        video_dir = os.path.dirname(self.__file_lst[index.row()])
        if not os.path.isdir(video_dir):
            print("올바르지 않은 접근입니다")
            self.__lineEdit_debug.setText("ERROR: 올바르지 않은 접근입니다")
            return
        if not os.path.exists(video_dir):
            self.__lineEdit_debug.setText("ERROR: 존재하지 않는 디렉토리입니다")
            return

        if platform.system() == "Linux":
            os.system(f'xdg-open "{video_dir}"')
        elif platform.system() == "Windows":
            os.system(f'explorer "{video_dir}"')
        elif platform.system() == "Darwin":
            os.system(f'open "{video_dir}"')

    def __slot_icon_idxs(
        self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection
    ) -> None:
        # 선택된 아이템을 리스트에 추가
        for idx in selected.indexes():
            if not idx.isValid():
                continue
            f_path = self.__file_data.get(idx.row())
            if f_path not in self.__play_lst:
                if len(self.__play_lst) > 11:
                    print("재생 목록은 최대 12개까지 추가할 수 있습니다.")
                    self.__lineEdit_debug.setText("재생 목록은 최대 12개까지 추가할 수 있습니다.")
                    return
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

        self.__listview_model = NP_model.NP_ListModel(self.__play_lst)
        self.__text_listview.setModel(self.__listview_model)
        if len(self.__play_lst_basename):
            self.__lineEdit_debug.setText(
                f'선택된 파일: {", ".join(self.__play_lst_basename)}'
            )
            if len(self.__lineEdit_debug.text()) > 60:
                self.__lineEdit_debug.setText(
                    f"선택된 파일: {self.__play_lst_basename[0]} 외 "
                    f"{len(self.__play_lst_basename) - 1}개"
                )
        else:
            self.__lineEdit_debug.setText("재생할 영상을 선택하세요.")

    def __slot_play_videos(self):
        if len(self.__play_lst):
            if self.__check_viewer.isChecked():
                self.__mult_vw = muliple_viewer.MultipleViewer(self.__play_lst)
                self.__mult_vw.show()
                # self.setDisabled(True)
                # if self.__mult_vw.close():
                #     self.setEnabled(True)
            else:
                self.__sing_vw = self.__NP_util.VideoWidget(self.__play_lst)
                self.__sing_vw.show()
        else:
            self.__lineEdit_debug.setText("ERROR: 재생할 영상이 선택되지 않았습니다")
            qt_lib.QtLibs.error_dialog("ERROR", "재생할 영상이 선택되지 않았습니다.")
            return

    def __slot_import_on_nuke(self):
        if len(self.__play_lst):
            for v_path in self.__play_lst:
                read_node = nuke.createNode("Read")
                read_node["file"].fromUserText(v_path)
                print(v_path)
        else:
            self.__lineEdit_debug.setText("ERROR: 삽입할 영상이 선택되지 않았습니다")
            qt_lib.QtLibs.error_dialog("ERROR", "삽입할 영상이 선택되지 않았습니다.")
            return

    def __update_icon_size(self, aspect, adjust) -> None:
        main_size = self.size()
        icon_w = int(main_size.width() / aspect - adjust)
        icon_h = int(main_size.height() / aspect - adjust)
        self.__item_listview.setIconSize(QtCore.QSize(icon_w, icon_h))
        if aspect == 2:
            self.__item_listview.setFont(QtGui.QFont("Sans Serif", 11))
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


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    NP = Nuke_Player()
    NP.show()
    app.exec_()
