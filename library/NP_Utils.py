#!/usr/bin/env python
# encoding=utf-8

# author        :   Juno Park
# created date  :   2024.03.03
# modified date :   2024.03.23
# description   :   Nuke_player에 필요한 기능을 모아둔 유틸리티 클래스

# ffmpeg 모듈 설치:   https://computingforgeeks.com/how-to-install-ffmpeg-on-centos-rhel-8/#google_vignette
# ffmpeg-python :   pip install ffmpeg-python

import sys
import os.path
import subprocess
import shutil
import mimetypes

sys.path.append("/home/rapa/libs_nuke")  # ffmpeg path
import ffmpeg
from PySide2 import QtWidgets, QtGui

sys.path.append("/home/rapa/workspace/python/Nuke_player")


class NP_Utils:
    def __init__(self):
        pass

    @staticmethod
    def extract_thumbnail(video_path: str, output_path: str, size: str):
        """
        :param video_path: 썸네일을 추출하고자 하는 영상 경로
        :param output_path: 썸네일을 저장할 경로
        :param size: 썸네일의 해상도
        :return: 썸네일이 정상적으로 추출되면 True, 그렇지 않으면 False
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"File {video_path} not found.")

        try:
            (
                ffmpeg.input(video_path, ss="00:00:01")
                .filter("scale", size)
                .output(output_path, vframes=1)
                .run(capture_stdout=True, capture_stderr=True)
            )
            return True
        except ffmpeg.Error as err:
            print("FFMPEG error:", err.stderr.decode("utf8"))
            return False
        except Exception as err:
            print(f"\033[31m\nERROR: 썸네일을 추출하는 동안 오류가 발생했습니다:\033[0m", err)
            return False

    @staticmethod
    def extract_thumbnail_subprocess(
        video_path: str, output_path: str, size: str
    ) -> bool:
        """
        :param video_path: 썸네일을 추출하고자 하는 영상 경로
        :param output_path: 썸네일을 저장할 경로
        :param size: 썸네일의 해상도
        :return: 썸네일이 정상적으로 추출되면 True, 그렇지 않으면 False
        """
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
            return True
        except subprocess.CalledProcessError as err:
            print(f"\033[31m\nERROR: 썸네일을 추출하는 동안 오류가 발생했습니다:\033[0m", err)
            return False

    @staticmethod
    def make_dirs(dir_path: str) -> bool:
        """
        :param dir_path: 생성하고자 하는 디렉토리 경로
        :return: 해당 경로의 디렉토리가 모두 생성되거나 이미 존재하면 True, 그렇지 않으면 False
        """
        try:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                print(f"\033[32m" f"디렉토리 '{dir_path}'가 생성되었습니다" f"\033[0m")
            else:
                pass
            return True
        except Exception as err:
            print(
                f"\033[31m\nERROR: 디렉토리 '{dir_path}'를 생성하는 동안 오류가 발생했습니다:\033[0m", err
            )
            return False

    @staticmethod
    def remove_dirs(dir_path: str) -> bool:
        """
        :param dir_path: 지우고자 하는 디렉토리 경로
        :return: 해당 경로의 디렉토리 모두 삭제되면 True, 그렇지 않으면 False
        """
        try:
            shutil.rmtree(dir_path)
            print(f"\033[32m\n디렉토리 '{dir_path}'가 성공적으로 삭제되었습니다.\033[0m")
            return True
        except Exception as err:
            print(
                f"\033[31m\nERROR: 디렉토리 '{dir_path}'를 삭제하는 동안 오류가 발생했습니다:\033[0m", err
            )
            return False

    @staticmethod
    def is_file_video(file_path: str) -> bool:
        """
        :param file_path: 파일 경로
        :return: 해당 파일이 비디오 형식이면 True, 그렇지 않으면 False를 반환
        """
        mime_type, _ = mimetypes.guess_type(file_path)
        # 해당 파일의 mime_type이 영상인지 검증
        if mime_type is not None and mime_type.startswith("video"):
            return True
        else:
            return False

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

    @staticmethod
    def change_video_bitrate(video_path: str, output_path: str, bitrate: int) -> bool:
        """
        :param video_path: 변환할 영상 파일의 경로
        :param output_path: 저장할 경로
        :param bitrate: 비트레이트
        :return: 영상의 비트레이트가 정상적으로 변환되면 True, 그렇지 않으면 False
        """
        if os.path.exists(output_path):
            print(f"\033[31m파일이 이미 존재합니다: {output_path}\033[0m")
            return False
        if os.path.exists(video_path):
            (ffmpeg.input(video_path).output(output_path, b=str(bitrate) + "k").run())
            return True
        else:
            print(f"\033[31m파일이 존재하지 않습니다: {video_path}\033[0m")
            return False

    @staticmethod
    def delete_key_from_value(dictionary: dict, value) -> dict:
        """
        :param dictionary: 데이터를 삭제할 딕셔너리
        :param value: 찾고자 하는 value
        :return: 찾은 value가 존재하는 key값을 삭제한 후 index를 재부여한 딕셔너리
        ex) {0: 123, 1: 456, 2: 789} >>> value = 456 >>> {0: 123, 1: 789}
        """
        keys_to_del = []
        new_dict = dict()
        for key, val in dictionary.items():
            if val == value:
                keys_to_del.append(key)
        for key in keys_to_del:
            del dictionary[key]
        for idx, val in enumerate(list(dictionary.values())):
            new_dict[idx] = val
        return new_dict


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
