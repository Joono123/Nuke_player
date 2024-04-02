import nuke
from PySide2 import QtWidgets


def getNukeMainWindow():
    for obj in QtWidgets.QApplication.topLevelWidgets():
        if obj.metaObject().className() == "Foundry::UI::DockMainWindow":
            return obj
    return None


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


# Main 클래스 인스턴스를 반환하는 팩토리 함수
def createMainPanel():
    # Nuke의 메인 윈도우를 부모로 사용하여 Main 인스턴스 생성
    widget = Test_UI(parent=getNukeMainWindow())
    widget.setObjectName("MyCustomPanel")  # 옵션: 패널의 고유 이름 설정
    return widget


# Nuke 패널로 등록
panelId = "uk.co.thefoundry.Main"
nukescripts.panels.registerWidgetAsPanel(
    "createMainPanel", "My Custom Panel", panelId  # 팩토리 함수 이름  # 패널의 표시 이름
)

# Nuke 메뉴에 패널 추가
nuke.menu("Nuke").addCommand(
    "Custom Tools/Nuke Player",
    lambda: nukescripts.panels.restorePanel(panelId),
)
