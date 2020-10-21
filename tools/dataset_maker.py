# -*- coding: utf-8 -*-
import argparse
import json
import glob
import os.path
import pickle
import random
import pandas as pd
import numpy as np
import os
from PIL import Image, ImageFont, ImageDraw
from fontTools.ttLib import TTFont

# Default data paths.
# 기본 파일 경로
DATASET_DIR = os.path.dirname(os.path.abspath("__file__"))
DEFAULT_FONTS_DIR = os.path.join(DATASET_DIR, "fonts")
DEFAULT_OUTPUT_DIR = os.path.join(DATASET_DIR, "output")
UNICODE_TABLE_PATH = os.path.join(DATASET_DIR, "UnicodeTable.json")

# Default language settings.
# 기본 파일 경로
DEFAULT_LANGUAGE = "kr"
DEFAULT_LANGUAGE_REGION = "2350-Common-Hangul"
DEFAULT_DATA_FORMAT = "parquet"
IMAGE_SIZE = (64, 64)


def make_font_name(font_file):
    """
    폰트 파일 경로에서 폰트 파일의 이름을 반환 해주는 함수

    Args:
        font_file(string): 폰트 파일의 경로
    
    Retruns:
        string: 폰트 파일의 이름
    """
    return os.path.basename(os.path.splitext(font_file)[0])


def make_uni_list(language, lang_region):
    """
    사용자로부터 입력 받은 국가 코드와 유니코드 블록이름으로 UnicodeTable.json에
    선언되어 있는 유니코드 리스트를 받아와서 반환 해주는 함수

    Args:
        language(string ex) kr, en): 국가 코드
        lang_region(string): 유니코드 블록 이름 참고: https://en.wikipedia.org/wiki/Unicode_block

    Retruns:
        list : 유니코드 리스트
    """
    unicode_table = json.load(open(UNICODE_TABLE_PATH))
    lang_unicode = unicode_table[language][lang_region]
    lang_unicode = [int(i, 16) for i in lang_unicode]
    return lang_unicode


def check_unicode_in_font(uni_list, font_path):
    """
    폰트에서 존재하는 유니코드(글자)만 모아서 리스트를 만들어
    반환 해주는 함수

    Args:
        uni_list(list): 유니코드 리스트
        font_path(string): 폰트 파일 경로

    Retruns:
        list : 유니코드 리스트
    """

    check_uni_list = []
    font = TTFont(font_path)

    for uni in uni_list:
        for cmap in font["cmap"].tables:
            if cmap.isUnicode() and uni in cmap.cmap and uni not in check_uni_list:
                check_uni_list.append(uni)

    return check_uni_list


def make_image(font_dir, pickle_dir, uni_list, image_size):
    """
    폰트에 있는 글자들을 이미지로 만들어주는 함수
    최종 생성되는 것은 이미지의 픽셀 정보가 들어 있는 피클 형식의 파일 이다.

    Args:
        font_dir(list): 폰트 파일들이 있는 폴더(디렉토리) 경로
        pickle_dir(string): 피클 형식(파이썬 객체)를 저장할 경로
        uni_list(list): 유니코드가 저장되어 있는 리스트
        image_size(tuple): 이미지 사이즈(width, height)

    Retruns:
        none
    """
    font_file_list = glob.glob(os.path.join(font_dir, "*.ttf")) + glob.glob(
        os.path.join(font_dir, "*.TTF")
    )
    image_size_string = "{},{}".format(image_size[0], image_size[1])
    data = {}

    for font_file in font_file_list:
        check_uni_list = check_unicode_in_font(uni_list, font_file)
        font_name = make_font_name(font_file)

        if os.path.isfile(os.path.join(pickle_dir, font_name + "_image.pkl")):
            continue

        data["Image"] = []
        data["Image size"] = []

        for uni in check_uni_list:
            character = chr(uni)
            image = Image.new("L", image_size, color=0)
            font = ImageFont.truetype(font_file, 48)
            drawing = ImageDraw.Draw(image)
            w, h = drawing.textsize(character, font=font)
            drawing.text(
                ((image_size[0] - w) / 2, (image_size[1] - h) / 2),
                character,
                fill=(255),
                font=font,
            )

            data["Image"].append(np.asarray(image).flatten())
            data["Image size"].append(image_size_string)

        print(font_name, len(data["Image"]))
        make_pickle(os.path.join(pickle_dir, font_name + "_image.pkl"), data)


def make_spline_dict(sfd_file, uni_list):
    """
    SFD파일을 유니코드 글자 마다 잘라서 딕셔너리 형식으로 저장하는 함수

    Args:
        sfd_file(string): SFD 파일 경로
        uni_list(list): 유니코드가 저장되어 있는 리스트

    Retruns:
        dictionary: sfd를 딕셔너리 형식으로 바꾼 것
    """

    # sfd 파일 읽기
    with open(sfd_file, "r") as f:
        sfd = f.read()

    spline_dict = {}
    gid_dict = {}
    # SFD 파일에 정의 된 첫 글자 찾기
    bi = sfd.find("BeginChars")
    # SFD 파일에 정의 된 마지막 글자 찾기
    ei = sfd.find("EndChars")
    # SFD 글자 정보만 가져오기
    sfd = sfd[sfd.find("\n", bi, ei) + 1 : ei]
    # 글자씩 자르기
    sfd_list = sfd.split("EndChar")

    # 글자 하나씩 읽기
    for part in sfd_list:
        part = part.strip()

        if "Fore" in part:
            part = part.split("Fore")
        else:
            continue

        if "StartChar" in part[0]:
            enc = part[0].split("\n", 2)[1]
            enc = enc.split(": ")[1]
            enc = enc.strip().split(" ")
            _, uni, gid = enc
        else:
            continue

        if "SplineSet" in part[1]:
            ssi = part[1].find("SplineSet") + len("SplineSet")
            esi = part[1].find("EndSplineSet")
            splineset = part[1][ssi:esi].strip()
            gid_dict[gid] = splineset
        else:
            continue

    for part in sfd_list:
        part = part.strip()

        if "Fore" in part:
            part = part.split("Fore")
        else:
            continue

        if "StartChar" in part[0]:
            enc = part[0].split("\n", 2)[1]
            enc = enc.split(": ")[1]
            enc = enc.strip().split(" ")
            _, uni, gid = enc

            if int(uni) in uni_list:
                pass
            else:
                continue
        else:
            continue

        splinesets = ""
        if "Refer" in part[1]:
            for line in part[1].split("\n"):
                if "Refer" in line:
                    line = line.split(" ")
                    splinesets += gid_dict.get(line[1]) + "\n"
        else:
            splinesets = gid_dict.get(gid)

        if splinesets == "":
            continue

        spline_dict[int(uni)] = "SplineSet\n" + splinesets + "EndSplineSet"

    return spline_dict


def make_TTFWeight(sfd_file):
    """
    폰트의 TTFWeight를 만들어주는 함수

    Args:
        sfd_file(string): SFD 파일 경로

    Retruns:
        int: TTFWeight (ex: 400, 500)
    """

    # SFD 파일 열기
    with open(sfd_file, "r") as f:
        sfd = f.read()

    # SFD 파일에서 TTFWeight 키워드를 찾아서 TTFWeight 키워드는 자르고 수치만 가져옴
    TTFWeight = (
        sfd[sfd.find("TTFWeight") : sfd.find("TTFWeight") + 14].split(":")[1].strip()
    )

    return TTFWeight


def count_contour(splineset):
    """
    글자(glyph)의 외곽선 개수를 반환 하는 함수


    Args:
        splineset(list): sfd에서 가져온 글자(glyph) 정보

    Retruns:
        number: 글자의 외각선 개수
    """

    c = 0

    for line in splineset.split("\n"):
        line = line.strip().split(" ")
        try:
            if line[-2] == "m":
                c += 1
        except IndexError as e:
            pass

    return c


def make_spline(sfd_dir, pickle_dir, uni_list):
    """
    fontforge를 이용하여 생성한 SFD파일에서
    글자(glyph) 정보, 외곽선 개수, 폰트의 굵기(Weight)를 가져와
    이를 파이썬 객체 피클로 저장하는 함수

    Args:
        sfd_dir(list): SFD 파일들이 있는 폴더(디렉터리) 경로
        uni_list(list): 유니코드 리스트

    Retruns:
        none
    """

    # SFD가 있는 폴더에서 파일들의 경로를 리스트 형식으로 불러옴
    sfd_file_list = glob.glob(os.path.join(sfd_dir, "*.sfd"))
    data = {}

    for sfd_file in sfd_file_list:
        # 폰트 파일 이름을 가져옴
        font_name = make_font_name(sfd_file)

        if os.path.isfile(os.path.join(pickle_dir, font_name + "_sfd.pkl")):
            continue
        # SFD, Contour num(외각선 개수), TTFWeight(굵기) key 선언
        # key에 해당되는 value는 리스트 형식이다
        data["SFD"] = []
        data["Contour num"] = []
        data["TTFWeight"] = []

        # 글자 정보들만 가져오기
        spline_dict = make_spline_dict(sfd_file, uni_list)
        # 폰트에 선언된 TTFWeight 가져오기
        ttf_weight = make_TTFWeight(sfd_file)

        for uni in uni_list:
            # SFD에 정의된 글자라면
            if spline_dict.get(uni) != None:
                # SFD , 외각선 개수, TTFWeight 저장
                data["SFD"].append(spline_dict[uni])
                data["Contour num"].append(count_contour(spline_dict[uni]))
                data["TTFWeight"].append(ttf_weight)

        # 피클 디렉터리가 존재하지 않는다면
        if not os.path.exists(pickle_dir):
            # 피클 디렉터리 생성
            os.makedirs(os.path.join(pickle_dir))
        # 생성한 글자 정보들 저장
        make_pickle(os.path.join(pickle_dir, font_name + "_sfd.pkl"), data)


def make_bfp(font_name):
    """
    폰트 파일 이름을 utf-8로 다시 인코딩하는 함수

    Args:
        font_name(string): 폰트 파일 이름

    Retruns:
        bfp(string): 인코딩된 폰트파일 이름
        
    """
    bfp = ""
    for c in font_name.encode():
        bfp += str(c)
    return bfp


def make_pickle(pickle_dir, data_dict):
    """
    폰트 파일 정보를 피클 형식(파이썬 객체)으로 저장해주는 함수

    Args:
        pickle_dir(string): pickle 객체를 저장할 경로
        data_dict(dictionary): 폰트 파일 정보
    Retruns:
        none
        
    """
    # print(pickle_dir)
    with open(pickle_dir, "wb") as f:
        pickle.dump(data_dict, f)


def make_dataset(data_format, font_dir, pickle_dir, output_dir):
    """
    피클 형식으로 저장되어 있는 폰트 정보들을 사용자가 지정한 파일 형식으로 
    저장하는 함수. 최종 font-dataset을 생성한다.

    Args:
        font_dir(string): 폰트들이 저장되어 있는 폴더(디렉터리) 경로
        pickle_dir(string): pickle 객체를 저장할 경로
        output_dir(string): font-dataset을 저장할 경로
    Retruns:
        count(int): 만들어진 폰트 데이터셋 개수

     """
    count = 0
    font_file_list = glob.glob(os.path.join(font_dir, "*.ttf")) + glob.glob(
        os.path.join(font_dir, "*.TTF")
    )

    for font_file in font_file_list:
        font_name = make_font_name(font_file)
        if data_format == "parquet" and os.path.isfile(
            os.path.join(output_dir, font_name + ".pq")
        ):
            continue

        elif data_format == "hd5" and os.path.isfile(
            os.path.join(output_dir, font_name + ".h5")
        ):
            continue

        elif data_format == "feather" and os.path.isfile(
            os.path.join(output_dir, font_name + ".ftr")
        ):
            continue

        pickle_list = glob.glob(os.path.join(pickle_dir, font_name + "_*.pkl"))
        df = {}

        for pickle_file in pickle_list:
            with open(pickle_file, "rb") as f:
                data = pickle.load(f)
            df.update(data)

        df = pd.DataFrame(df)
        # print(font_name)
        # print(df.shape)

        if not os.path.exists(output_dir):
            os.makedirs(os.path.join(output_dir))

        if data_format == "parquet":
            df.to_parquet(os.path.join(output_dir, font_name + ".pq"), "pyarrow")

        elif data_format == "hd5":
            df.to_hdf(os.path.join(output_dir, font_name + ".h5"), key="df", mode="w")

        elif data_format == "feather":
            df.to_feather(os.path.join(output_dir, font_name + ".ftr"))
        count += 1

    return count


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--lang",
        type=str,
        dest="language",
        default=DEFAULT_LANGUAGE,
        help="Language to create font character images",
    )

    parser.add_argument(
        "--lang_region",
        type=str,
        dest="lang_region",
        default=DEFAULT_LANGUAGE_REGION,
        help="Language region to create font character images",
    )

    parser.add_argument(
        "--input",
        type=str,
        dest="input",
        default=DEFAULT_FONTS_DIR,
        help="Directory of ttf fonts to use.",
    )

    parser.add_argument(
        "--data_format",
        type=str,
        dest="data_format",
        default=DEFAULT_DATA_FORMAT,
        help="Data format to train from font data",
    )

    parser.add_argument(
        "--output", type=str, dest="output", default=DEFAULT_OUTPUT_DIR, help="",
    )

    args = parser.parse_args()
    pickle_dir = os.path.join(args.output, "pickle")
    sfd_dir = os.path.join(args.output, "sfd")
    uni_list = make_uni_list(args.language, args.lang_region)
    print("make font image...")
    make_image(args.input, pickle_dir, uni_list, IMAGE_SIZE)
    print("make spline format database...")
    make_spline(sfd_dir, pickle_dir, uni_list)
    print("make font dataset")
    font_num = make_dataset(args.data_format, args.input, pickle_dir, args.output)
    print(f"total {font_num} font data is made")

    print("earse all sfd, pickle file...")
    pickle_file_list = os.listdir(pickle_dir)
    for file in pickle_file_list:
        if os.path.isfile(os.path.join(pickle_dir, file)):
            os.remove(os.path.join(pickle_dir, file))

    os.rmdir(pickle_dir)

    sfd_file_list = os.listdir(sfd_dir)
    for file in sfd_file_list:
        if os.path.isfile(os.path.join(sfd_dir, file)):
            os.remove(os.path.join(sfd_dir, file))

    os.rmdir(sfd_dir)
