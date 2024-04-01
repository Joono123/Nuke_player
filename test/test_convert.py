import os
import re

# fps = 24
# seq_path = "/home/rapa/Downloads/test/comp_gun.%d.jpg"
# output = "/home/rapa/Downloads/Output/test_convert.mp4"
#
# os.system(f"ffmpeg -f image2 -r {fps} -i {seq_path} -vcodec mpeg4 -y {output}")
# os.system(
#     f"ffmpeg -framerate {fps} -pattern_type glob -i '/home/rapa/Downloads/test/*.jpg' -c:v libx264 -r {fps} -pix_fmt yuv420p {output}"
# )
import ffmpeg

input_pattern = "/home/rapa/Downloads/test/\%04d.jpg"
output = "/home/rapa/Downloads/Output/output.mp4"
fps = 30

ffmpeg.input(input_pattern, framerate=fps, pattern_type="glob").output(
    output, codec="libx264", pix_fmt="yuv420p", r=fps
).run()


def check_missing_numbers(directory_path, extension):
    existing_numbers = set()

    # 파일명에서 숫자를 추출하는 정규표현식 패턴
    pattern = re.compile(r"\d+")

    # 디렉토리 내에 있는 파일들을 순회하며 이미지 파일의 번호를 추출
    for filename in os.listdir(directory_path):
        if filename.endswith(extension):
            match = pattern.search(filename)
            if match:
                file_number = int(match.group())
                existing_numbers.add(file_number)

    # 추출한 번호 중에서 가장 작은 번호와 가장 큰 번호를 찾음
    if existing_numbers:
        min_number = min(existing_numbers)
        max_number = max(existing_numbers)
    else:
        min_number = None
        max_number = None

    # 최소 번호부터 최대 번호까지 모든 번호를 확인하며 빠진 번호를 찾습니다.
    missing_numbers = [
        num for num in range(min_number, max_number + 1) if num not in existing_numbers
    ]
    if missing_numbers:
        print("Missing Numbers:", missing_numbers)
        return
    else:
        print("No Missing Numbers")


# 디렉토리 경로와 확장자를 설정합니다.
directory_path = "/home/rapa/Downloads/test"
extension = ".jpg"

# 빠진 번호를 확인합니다.
# missing_numbers = check_missing_numbers(directory_path, extension)

# test = os.path.isdir(directory_path)
# print(test)
