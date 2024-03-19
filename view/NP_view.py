#!/usr/bin/env python
# encoding=utf-8

# author        : Juno Park
# created date  : 2024.03.04
# modified date : 2024.03.04
# description   :

from PySide2 import QtWidgets, QtGui, QtCore


class NP_ItemView(QtWidgets.QListView):
    # context_request = QtCore.Signal(QtCore.QPoint)

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
        # self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        self.setStyleSheet(
            "QListView::item:selected {"
            "background-color: rgba(30, 70, 255, 200);}"
            "QToolTip {font-family: Sans Serif; font-size: 10px;}"
        )


class NP_ListView(QtWidgets.QListView):
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
        # self.setSelectionMode(QtWidgets.QListView.NoSelection)
        self.setSelectionMode(QtWidgets.QListView.SingleSelection)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        # self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        self.setStyleSheet(
            "QListView::item:selected {" "background-color: rgba(30, 70, 255, 200);" "}"
        )
