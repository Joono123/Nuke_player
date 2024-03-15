from PySide2.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QSlider, QLabel
from PySide2.QtCore import Qt, QUrl
from PySide2.QtMultimedia import QMediaPlayer, QMediaContent

class VideoPlayer(QWidget):
    def __init__(self):
        super().__init__()

        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self)

        self.play_button = QPushButton('Play')
        self.slider = QSlider(Qt.Horizontal)
        self.label = QLabel()

        layout = QVBoxLayout()
        layout.addWidget(self.play_button)
        layout.addWidget(self.slider)
        layout.addWidget(self.label)

        self.setLayout(layout)

        self.play_button.clicked.connect(self.play_clicked)
        self.media_player.durationChanged.connect(self.set_duration)
        self.slider.sliderPressed.connect(self.slider_pressed)

    def play_clicked(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.play_button.setText('Play')
        else:
            self.media_player.play()
            self.play_button.setText('Pause')

    def set_duration(self, duration):
        self.slider.setRange(0, duration)

    def slider_pressed(self):
        position = self.slider.value()
        self.media_player.setPosition(position)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)  # 부모 클래스의 mousePressEvent 호출
        # 슬라이더 위젯의 절대 좌표를 가져옴
        slider_pos = self.slider.mapFromGlobal(event.globalPos())
        # 슬라이더 위젯의 바깥 영역을 클릭한 경우 무시
        if not self.slider.rect().contains(slider_pos):
            return
        # 클릭한 지점의 값을 계산하여 setPosition()으로 영상 위치 설정
        value = self.slider.minimum() + (slider_pos.x() / self.slider.width()) * (self.slider.maximum() - self.slider.minimum())
        self.media_player.setPosition(int(value))

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)  # 부모 클래스의 mouseMoveEvent 호출
        # 마우스 버튼이 눌린 상태에서 슬라이더를 움직이는 경우 setPosition()으로 영상 위치 설정
        if event.buttons() == Qt.LeftButton:
            self.slider_pressed()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)  # 부모 클래스의 mouseReleaseEvent 호출
        # 마우스 버튼이 떼어진 상태에서 슬라이더를 놓은 경우 setPosition()으로 영상 위치 설정
        self.slider_pressed()

if __name__ == "__main__":
    app = QApplication([])
    player = VideoPlayer()
    player.setWindowTitle('Video Player')
    player.setGeometry(100, 100, 400, 200)
    player.media_player.setMedia(QMediaContent(QUrl.fromLocalFile('/home/rapa/Downloads/test1.MOV')))
    player.show()
    app.exec_()
