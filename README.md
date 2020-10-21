hangul-font-dataset: 딥러닝 기반의 폰트 연구를 위한 폰트 데이터셋
=============

## Introduction


딥러닝 기반의 폰트 연구를 위한 한글 폰트 데이터셋 입니다.


## Structure

### Hangul-font-dataset 구조

|KEY|TYPE|VALUE|
|:---|:---|:---|
|Image|Array|글자 이미지의 정보를 배열로 저장|
|Image size|tuple(width, height)|글자 이미지의 사이즈, 가로와 세로 값이 저장된 튜플이다.|
|Font name|String|폰트 이름|
|Family name|String|폰트 글꼴 이름|
|Glyph id|Number|폰트 프로그램에서 정의 해놓은 글자의 id|
|Unicode|Number|글자의 유니코드 값|
|Width|Number|글자의 너비|
|VWidth|Number|글자의 높이|
|Bound|tuple(xmin, ymin, xmax, ymax)|글자를 감싸는 정사각형의 정보|
|Contour number|Number|글자 외곽선 개수|
|Weight|String|글자의 굵기를 글 로 나타낸 것|
|TTFWeight|Number|글자의 굵기를 수치로 나타낸 것|
|SFD|Spline Font Database|폰트 스플라인 데이터베이스 형식의 데이터|
|Version|String|폰트 프로그램의 버전|
|Copyright|String|폰트 프로그램의 copyright|

## Repository structure

* gothic: 총 31개의 고딕(돋움) 폰트 데이터셋: https://github.com/stemfont/hangul-font-dataset/tree/main/gothic
* myeongjo: 총 30개의 명조(바탕) 폰트 데이터셋: https://github.com/stemfont/hangul-font-dataset/tree/main/myeongjo

## How to get data?

글자 이미지 데이터를 얻고 싶다면,

```
python ./tools/array2img.py 
```
option:
- --input: hangul-font-dataset이 들어있는 경로
- --output: 데이터가 생성되는 경로 

## How to make data?

### Requirement

fontforge를 제외하고 pip 로 받아주시면 됩니다.

```
pip install 라이브러리 이름
```

- python
- pandas (0.23.2)
- numpy
- Pillow
- pyarrow (0.13)
- fonttools

fontforge는 리눅스의 경우

```
sudo apt-get install fontforge
```

로 설치하시면 됩니다.

### Make hangul font-dataset

1. 먼저 fontforge를 이용하여 폰트 정보를 생성합니다.(폰트 파일은 다 넣어 놨습니다.)

```
fontforge -script ./tools/dataset_maker_ff.py

```
옵션:

- --lang: 폰트에서 만들고자 하는 국가코드(기본: kr)
- --lang_region: 해당 언어의 유니코드 블록(기본: 2350-Common-Hangul)
- --fonts_dir: 폰트 데이터셋 생성 폴더 경로(기본: ./fonts)


2. 그 다음 폰트 데이터셋을 만듭니다.

```
python ./tools/dataset_maker.py

```
옵션:

- --lang: 폰트에서 만들고자 하는 국가코드(기본: kr)
- --lang_region: 해당 언어의 유니코드 블록(기본: 2350-Common-Hangul)
- --fonts_dir: 폰트 데이터셋 생성 폴더 경로(기본: ./fonts)
- --data_format: 폰트 데이터셋 형식(기본: parquet)

3. 그러면 fonts/parquet 디렉터리 안에 폰트 데이터셋이 생성됩니다

```
fonts/
└── parquet
	├── 폰트이름1.pq
	├── 폰트이름2.pq
			.
			.
			.
```