path = "/home/rapa/.NP_temp/playlist.txt"


file_paths = []

with open(path, "r") as fp:
    for line in fp:
        file_paths.append(line.strip())


print(file_paths)
