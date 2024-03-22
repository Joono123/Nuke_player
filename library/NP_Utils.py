#!/usr/bin/env python
# encoding=utf-8
# author        : Juno Park
# created date  : 2024.02.26
# modified date : 2024.02.26
# description   : subprocess 및 ffmpeg을 활용한 썸네일 제작 VLC로 영상 재생

# ffmpeg 모듈 설치: https://computingforgeeks.com/how-to-install-ffmpeg-on-centos-rhel-8/#google_vignette
# ffmpeg-python : pip install ffmpeg-python

import sys
import os.path
import subprocess

sys.path.append("/home/rapa/libs_nuke")
import ffmpeg
from PySide2 import QtWidgets, QtGui

sys.path.append("/home/rapa/workspace/python/Nuke_player")


class NP_Utils:
    def __init__(self):
        pass

    @staticmethod
    def extract_thumbnail(video_path: str, output_path: str, size: str):
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"File {video_path} not found.")
        (
            ffmpeg.input(video_path, ss="00:00:01")
            .filter("scale", size)
            .output(output_path, vframes=1)
            .run(capture_stdout=True, capture_stderr=True)
        )

    @staticmethod
    def change_video_bitrate(video_path: str, output_path: str, bitrate: int):
        (ffmpeg.input(video_path).output(output_path, b=str(bitrate) + "k").run())

    @staticmethod
    def extract_thumbnail_subprocess(video_path: str, output_path: str, size: str):
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"File {video_path} not found.")

        cmd = [
            "ffmpeg",
            "-ss",
            "00:00:01",
            "-i",
            video_path,
            "-vf",
            f"scale={size}",
            "-vframes",
            "1",
            output_path,
        ]

        # ffmpeg 실행
        try:
            subprocess.run(cmd, capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")

    @staticmethod
    def make_dir(dir_path: str):
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"\033[32m" f"임시 디렉토리 '{dir_path}'가 생성되었습니다" f"\033[0m")
        else:
            pass

    @staticmethod
    def open_with_vlc(video_path: str, vlc_path: str = "/usr/bin/vlc") -> None:
        """
        :param video_path: 재생할 영상의 경로
        :param vlc_path: vlc가 설치된 경로 (기본값: "/usr/bin/vlc")
        """
        if not os.path.exists(vlc_path):
            raise FileNotFoundError(f"VLC doesn't exist current path.")
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"File {video_path} not found")
        subprocess.Popen([vlc_path, video_path], shell=True)

    @staticmethod
    def get_video_fps(file_path: str) -> int:
        """
        :param file_path: fps를 추출할 파일의 경로
        :return: numerator와 denominator를 추출하여 fps값을 반환
        """
        probe = ffmpeg.probe(file_path)
        video_info = next(
            stream for stream in probe["streams"] if stream["codec_type"] == "video"
        )
        fps_str = video_info["avg_frame_rate"]
        numerator, denominator = map(int, fps_str.split("/"))
        return numerator / denominator

    @staticmethod
    def get_video_resolution(file_path: str) -> tuple:
        """
        :param file_path: 해상도를 추출할 파일의 경로
        :return: 해상도를 width와 heiget 형태로 추출하여 pixel, width, height값을 튜플로 반환
        """
        probe = ffmpeg.probe(file_path)
        video_stream = next(
            (stream for stream in probe["streams"] if stream["codec_type"] == "video"),
            None,
        )
        width = int(video_stream["width"])
        height = int(video_stream["height"])
        pixel = width * height
        result = (pixel, width, height)
        return result


###########################################################################################


class CustomMessageBox(QtWidgets.QMessageBox):
    def __init__(self, icon_path: str, parent=None):
        super(CustomMessageBox, self).__init__(parent)
        if icon_path == "":
            pass
        else:
            self.setIconPixmap(QtGui.QPixmap.fromImage(QtGui.QImage(icon_path)))
        self.setFont(QtGui.QFont("Sans Serif", 9))
        self.setStyleSheet(
            "color: rgb(255, 255, 255);" "background-color: rgb(70, 70, 70);"
        )
        self.setStandardButtons(QtWidgets.QMessageBox.Close)


class QuestionMessageBox(QtWidgets.QMessageBox):
    def __init__(self, icon_path: str, parent=None):
        super(QuestionMessageBox, self).__init__(parent)
        if icon_path == "":
            pass
        else:
            self.setIconPixmap(QtGui.QPixmap.fromImage(QtGui.QImage(icon_path)))
        self.setFont(QtGui.QFont("Sans Serif", 9))
        self.setStyleSheet(
            "color: rgb(255, 255, 255);" "background-color: rgb(70, 70, 70);"
        )

        self.addButton(QtWidgets.QMessageBox.No)
        self.addButton(QtWidgets.QMessageBox.Ignore)
        self.setDefaultButton(QtWidgets.QMessageBox.No)

    def exec_(self):
        res = super().exec_()
        return res == QtWidgets.QMessageBox.Ignore
