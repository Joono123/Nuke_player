#!/usr/bin/env python
# encoding=utf-8

# author        : Juno Park
# created date  : 2024.03.04
# modified date : 2024.03.04
# description   :

import os
from PySide2 import QtCore, QtWidgets, QtGui


class NP_ItemModel(QtCore.QAbstractListModel):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.__image_path = image_path

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DecorationRole:
            if 0 <= index.row() < len(self.__image_path):
                pixmap = QtGui.QPixmap(self.__image_path[index.row()])
                icon = QtGui.QIcon(pixmap)
                return icon
        elif role == QtCore.Qt.DisplayRole:
            if 0 <= index.row() < len(self.__image_path):
                file_name = os.path.splitext(
                    os.path.basename(self.__image_path[index.row()])
                )[0]
                return file_name
        return None

    def rowCount(self, parent=...):
        return len(self.__image_path)


class NP_ListModel(QtCore.QAbstractListModel):
    def __init__(self, playlist, parent=None):
        super().__init__(parent)
        self.__play_lst = playlist

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if 0 <= index.row() < len(self.__play_lst):
                basename = os.path.basename(self.__play_lst[index.row()])
                return f"{index.row()+1}. {basename}"

    def rowCount(self, parent=...):
        return len(self.__play_lst)
