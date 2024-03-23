#!/usr/bin/env python
# encoding=utf-8

# author        :   Juno Park
# created date  :   2024.03.03
# modified date :   2024.03.23
# description   :   mvc 패턴으로 구성된 Nuke_player의 View 역할을 하는 클래스
#                   Item을 관리하는 ListView와 Text를 관리하는 ListView로 구성됨


from PySide2 import QtWidgets, QtGui, QtCore


class NP_ItemView(QtWidgets.QListView):  # -> 아이템을 등록하고 관리하는 ListView
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(QtGui.QFont("Sans Serif", 9))
        self.setFrameShape(QtWidgets.QFrame.Panel)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.setViewMode(QtWidgets.QListView.IconMode)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QtWidgets.QListView.InternalMove)
        self.setDropIndicatorShown(True)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setAlternatingRowColors(False)

        self.setSelectionMode(QtWidgets.QListView.ExtendedSelection)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        self.setStyleSheet(
            "QListView::item:selected {"
            "background-color: rgba(30, 70, 255, 200);}"
            "QToolTip {font-family: Sans Serif; font-size: 12px;}"
        )


class NP_ListView(QtWidgets.QListView):  # -> 선택된 아이템(플레이리스트)을 관리하는 ListView
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(QtGui.QFont("Sans Serif", 9))
        self.setFrameShape(QtWidgets.QFrame.Panel)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.setViewMode(QtWidgets.QListView.ListMode)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QtWidgets.QListView.InternalMove)
        self.setDropIndicatorShown(True)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setAlternatingRowColors(False)
        self.setFixedWidth(200)
        self.setContentsMargins(5, 5, 5, 30)
        self.setSelectionMode(QtWidgets.QListView.SingleSelection)
        self.setFocusPolicy(QtCore.Qt.NoFocus)

        self.setStyleSheet(
            "QListView::item:selected {" "background-color: rgba(30, 70, 255, 200);" "}"
        )
