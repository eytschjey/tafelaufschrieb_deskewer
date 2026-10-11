# Board Warp

A small PyQt tool for manually perspective-warping classroom board photos into scanner-style images.

## What it does

- Opens each image in a folder
- Lets you click 4 corners of the board in order:
  1. top-left
  2. top-right
  3. bottom-right
  4. bottom-left
- Warps the image into a rectangle and saves it to a sibling output folder

## Requirements

- Python 3
- `opencv-python-headless`
- `numpy`
- `PyQt5`

Install in a virtualenv:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install opencv-python-headless numpy PyQt5
```

## Usage

1. Put your source images into the `input/` folder in this repo.
2. Run:

```bash
python board_warp.py
```

## Output

Warped images are written to the `output/` folder in this repo.
