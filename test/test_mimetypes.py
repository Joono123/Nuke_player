from NP_libs import NP_Utils

dir = "/home/rapa/Downloads/test"
res = NP_Utils.NP_Utils.is_file_image(dir)

print(res)

print(NP_Utils.NP_Utils.is_image_sequence(dir))
