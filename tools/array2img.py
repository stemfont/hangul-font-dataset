import argparse
import pandas
import os
import glob
import numpy as np
from PIL import Image, ImageFont, ImageDraw

current_dir = os.path.dirname(os.path.abspath("__file__"))
DEFUALT_DATASET_DIR = os.path.join(current_dir, "./output/parquet")


def array2imag(dataset_path):
    file_list = glob.glob(os.path.join(dataset_path, "*.pq"))
    for file in file_list:
        font_name = os.path.basename(os.path.splitext(file)[0])
        out_dir = os.path.join(dataset_path, "../image")
        out_dir = os.path.join(out_dir, font_name + "-image")
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        # pq_data = pandas.read_feather(file)
        pq_data = pandas.read_parquet(file)
        image_list = pq_data["Image"]

        total_count = 0

        for i, image_data in enumerate(image_list):

            if total_count == 5000:
                print("{} images generated...".format(total_count))
                total_count = 0
            image_height, image_width = pq_data["Image size"][i].split(",")
            image = np.array(image_data)
            image = image.reshape(int(image_height), int(image_width))
            image = Image.fromarray(image.astype("uint8"), "L")
            file_path = "{}_{}.jpeg".format(font_name, pq_data["Unicode"][i])
            file_path = os.path.join(out_dir, file_path)
            image.save(file_path, "JPEG")

            total_count += 1

        msg = "{} is done. {} images made.".format(font_name, len(image_list))
        print(msg)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset_dir",
        type=str,
        dest="dataset_dir",
        default=DEFUALT_DATASET_DIR,
        help="Data format to train from font data",
    )

    args = parser.parse_args()
    print("image generating from font dataset")
    array2imag(args.dataset_dir)
