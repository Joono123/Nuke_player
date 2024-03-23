#!/usr/bin/env python
# encoding=utf-8

# author        :   Juno Park
# created date  :   2024.03.03
# modified date :   2024.03.23
# description   :   mvc 패턴으로 구성된 Nuke_player의 model 역할을 하는 클래스
#                   Item을 관리하는 ListView의 model과 Text를 관리하는 ListView의 model로 구성됨

import os
from PySide2 import QtCore, QtGui


class NP_ItemModel(QtCore.QAbstractListModel):  # -> Item과 관련된 데이터를 관리하는 model
    def __init__(self, thumb_path_lst: list[str], video_path: list[str], parent=None):
        super().__init__(parent)
        self.__thumb_path_lst = thumb_path_lst  # 썸네일 경로가 담긴 리스트
        self.__video_path_lst = video_path      # 영상 경로가 담긴 리스트

    def data(self, index, role=QtCore.Qt.DisplayRole):
        # 아이템의 썸네일 표시
        if role == QtCore.Qt.DecorationRole:
            if 0 <= index.row() < len(self.__thumb_path_lst):
                pixmap = QtGui.QPixmap(self.__thumb_path_lst[index.row()])
                icon = QtGui.QIcon(pixmap)
                return icon
        # 아이템의 이름을 텍스트로 표시
        elif role == QtCore.Qt.DisplayRole:
            if 0 <= index.row() < len(self.__thumb_path_lst):
                file_name = os.path.splitext(
                    os.path.basename(self.__thumb_path_lst[index.row()])
                )[0]
                return file_name
        # 아이템의 툴팁 표시
        elif role == QtCore.Qt.ToolTipRole:
            file_path = f"{self.__video_path_lst[index.row()]}"
            return file_path
        return None

    def rowCount(self, parent=...) -> int:
        """
        :return: 썸네일의 수를  int로 반환
        """
        return len(self.__thumb_path_lst)


class NP_ListModel(QtCore.QAbstractListModel):  # -> 플레이리스트를 관리하는 model
    def __init__(self, video_path: list[str], parent=None):
        super().__init__(parent)
        self.__video_path_lst = video_path  # 영상 경로가 담긴 리스트

    def data(self, index, role=QtCore.Qt.DisplayRole):
        # 파일 경로의 basename을 텍스트로 표시
        if role == QtCore.Qt.DisplayRole:
            if 0 <= index.row() < len(self.__video_path_lst):
                basename = os.path.basename(self.__video_path_lst[index.row()])
                return f"{index.row()+1}. {basename}"

    def rowCount(self, parent=...) -> int:
        """
        :return: 파일 경로의 수를 int로 반환
        """
        return len(self.__video_path_lst)
