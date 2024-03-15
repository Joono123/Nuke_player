import sys
from PySide2.QtCore import Qt, QPropertyAnimation
from PySide2.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

class DissolveLabel(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Dissolving Label")
        self.setGeometry(100, 100, 300, 200)

        layout = QVBoxLayout()

        self.label = QLabel("Hello, World!")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self.setLayout(layout)

    def dissolve_label(self):
        # 레이아웃 애니메이션 생성
        animation = QPropertyAnimation(self.layout(), b"opacity")
        animation.setDuration(3000)  # 디졸브에 걸리는 시간 (밀리초)
        animation.setStartValue(1.0)  # 완전히 불투명한 상태
        animation.setEndValue(0.0)    # 완전히 투명한 상태
        animation.start(QPropertyAnimation.DeleteWhenStopped)

        # 애니메이션 종료 후 텍스트 변경
        animation.finished.connect(self.change_text)

    def change_text(self):
        self.label.setText("Animation Finished!")

        # 다시 레이아웃 애니메이션 적용
        animation = QPropertyAnimation(self.layout(), b"opacity")
        animation.setDuration(3000)
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.start(QPropertyAnimation.DeleteWhenStopped)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DissolveLabel()
    window.show()
    window.dissolve_label()  # 디졸브 애니메이션 시작
    sys.exit(app.exec_())