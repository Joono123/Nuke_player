import pathlib

import ffmpeg
import os


def add_watermark_run(self):
    video_files = [
        file
        for file in os.listdir(self.__mark_start)
        if file.endswith((".mp4", ".avi", ".mov"))
    ]

    for i, filename in enumerate(video_files, start=1):
        ratio = int((i / len(video_files)) * 100)
        dst_file = pathlib.Path(self.__mark_end) / pathlib.Path(filename).name
        msg_sig = MessageSig_M()

        print("filename", filename)
        print("dst_file", dst_file)

        video_path = os.path.join(self.__mark_start, filename)
        print(video_path)
