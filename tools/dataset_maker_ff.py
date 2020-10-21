# -*- coding: utf-8 -*-
import argparse
import fontforge as ff
import glob
import os.path
import pickle
import json
from fontTools.ttLib import TTFont

# Default data paths.
# 기본 파일 경로
DATASET_DIR = os.path.dirname(os.path.abspath("__file__"))
DEFAULT_FONTS_DIR = os.path.join(DATASET_DIR, "fonts")
DEFAULT_OUTPUT_DIR = os.path.join(DATASET_DIR, "output")
UNICODE_TABLE_PATH = os.path.join(DATASET_DIR, "UnicodeTable.json")

# 기본 언어 세팅
DEFAULT_LANGUAGE = "kr"
DEFAULT_LANGUAGE_REGION = "2350-Common-Hangul"


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


def make_sfd(font_dir, sfd_dir):
    """
    폰트 파일들을 fontforge를 이용하여 SFD(Spline Font Data) 형식으로
    바꿔주는 함수

    Args:
        font_dir(list): 폰트 파일들이 들어있는 디렉토리 경로
        sfd_dir(string): SFD 파일을 저장할 폴더(디렉토리) 이름

    Retruns:
        없음
    """

    if not os.path.exists(sfd_dir):
        os.makedirs(sfd_dir)

    font_file_list = glob.glob(os.path.join(font_dir, "*.ttf")) + glob.glob(
        os.path.join(font_dir, "*.TTF")
    )

    for font_file in font_file_list:
        font_name = make_font_name(font_file).decode("utf-8")
        print(font_name)
        if os.path.isfile(os.path.join(sfd_dir, font_name + ".sfd")):
            continue

        font = ff.open(font_file.decode("utf-8"))
        font.save(os.path.join(sfd_dir, font_name + ".sfd"))


def make_glyph_info(font_dir, pickle_dir, uni_list):
    """
    폰트 파일들을 fontforge를 이용하여 글자의 정보들을 
    pickle형식(파이썬 객체)로 저장하는 함수

    다른 정보는
    https://fontforge.org/docs/scripting/python/fontforge.html
    를 참고

    Args:
        font_dir(list): 폰트 파일들이 들어있는 디렉토리 경로
        pickle_dir(string): 글자 정보들을 저장할 디렉토리 경로
        uni_list(list): 유니코드 리스트

    Retruns:
        없음
    """

    # 폰트 파일이 들어있는 경로에서 폰트 파일들의 경로를 불러옴
    font_file_list = glob.glob(os.path.join(font_dir, "*.ttf")) + glob.glob(
        os.path.join(font_dir, "*.TTF")
    )
    data = {}

    for font_file in font_file_list:
        # font_name = make_font_name(font_file).decode("utf-8")
        # 폰트 이름 추출
        font_name = make_font_name(font_file).decode("utf-8")
        if os.path.isfile(os.path.join(pickle_dir, font_name + "_info.pkl")):
            continue

        # 폰트 파일을 fontforge로 불러옴
        font = ff.open(font_file.decode("utf-8"))
        # 폰트마다 유니코드 지원 여부가 다르므로 폰트 마다 검사
        check_unicode_list = check_unicode_in_font(uni_list, font_file)

        data["Unicode"] = []
        data["Width"] = []
        data["VWidth"] = []
        data["Glyph id"] = []
        data["Font name"] = []
        data["Bound"] = []
        data["Family Name"] = []
        data["Weight"] = []
        data["Version"] = []
        data["Copyright"] = []

        for uni in check_unicode_list:
            glyph = font[uni]
            data["Unicode"].append(glyph.unicode)
            data["Width"].append(glyph.width)
            data["VWidth"].append(glyph.vwidth)
            data["Glyph id"].append(str(glyph.originalgid))
            data["Font name"].append(font_name)
            data["Bound"].append(list(glyph.boundingBox()))
            data["Family Name"].append(font.familyname)
            data["Weight"].append(font.weight)
            data["Version"].append(font.version)
            data["Copyright"].append(font.copyright)

        # 글자가 몇개 생성되었는지 확인
        msg = u"{} glyph info len is :{}".format(font_name, len(data["Unicode"]))
        print(msg)
        # pickle 디렉터리가 없다면 생성
        if not os.path.exists(pickle_dir):
            os.makedirs(os.path.join(pickle_dir))
        # 글자 정보들 저장
        make_pickle(os.path.join(pickle_dir, font_name + "_info.pkl"), data)


def make_bfp(font_name):
    """
    폰트 파일 이름을 utf-8로 다시 인코딩하는 함수

    Args:
        font_name(string): 폰트 파일 이름

    Retruns:
        bfp(string): 인코딩된 폰트파일 이름
        
    """
    bfp = ""
    for c in font_name.decode("utf-8"):
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
        "--output", type=str, dest="output", default=DEFAULT_OUTPUT_DIR, help="",
    )

    args = parser.parse_args()
    uni_list = make_uni_list(args.language, args.lang_region)
    print("make sfd")
    make_sfd(args.input, os.path.join(args.output, "sfd"))
    print("make glyph info")
    make_glyph_info(args.input, os.path.join(args.output, "pickle"), uni_list)
