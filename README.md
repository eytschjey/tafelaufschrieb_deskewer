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
pip install opencv-python-headless numpy PyQt5 'PyQt5-Qt5==5.15.18'
```

## Usage

1. Put your source images into the `input/` folder in this repo.
2. Start the tool:

```bash
./"Board Warp.command"
```

On macOS, you can double-click `Board Warp.command` in Finder. The launcher uses the repository's virtual environment, so the environment does not need to be activated manually.

For a one-click first-time setup that creates the virtual environment and installs or repairs dependencies, double-click `Install and Launch Board Warp.command` instead. It checks for Python 3, installs the dependencies if needed, and then starts the tool. The Qt version is pinned because newer builds currently fail to load the macOS `cocoa` platform plugin.

The image area is scrollable for large photos. After the fourth corner is selected, the chosen board area is highlighted with a translucent overlay.

You can also launch the script directly with:

```bash
.venv/bin/python board_warp.py
```

## Output

Warped images are written to the `output/` folder in this repo.
