import nuke
import nukescripts
from PySide2 import QtWidgets


class Test_UI(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        w = QtWidgets.QWidget()
        self.setFixedSize(300, 150)
        vlay = QtWidgets.QVBoxLayout()
        btn = QtWidgets.QPushButton("Test")
        btn.clicked.connect(self.slot_btn)
        vlay.addWidget(btn)
        w.setLayout(vlay)
        self.setCentralWidget(w)

    def slot_btn(self):
        print("test")
        read_node = nuke.createNode("Read")
        read_node["file"].setValue("")


def add_custom_panel():
    panel = nuke.Panel("Custom Panel")
    panel.addSingleLineInput("Test Input:", "")
    result = panel.show()
    if result:
        print("User input:", panel.value("Test Input:"))


def add_custom_menu():
    menubar = nuke.menu("Nuke")
    custom_menu = menubar.addMenu("Custom Menu")
    custom_menu.addCommand("Test Command", lambda: print("Test command executed"))


def create_custom_panel_and_menu():
    add_custom_panel()
    add_custom_menu()


if __name__ == "__main__":
    # Register custom panel
    nukescripts.registerPanel("Test_UI", Test_UI)

    # Add custom menu
    add_custom_menu()

    # Add toolbar button
    toolbar = nuke.toolbar("Nodes")
    toolbar.addCommand(
        "Custom/Test UI",
        "nuke.createNode('Test_UI')",
        icon="/home/rapa/workspace/python/Nuke_player/resource/png/video-player.ico",
    )

    # Execute function to create custom panel and menu
    create_custom_panel_and_menu()
