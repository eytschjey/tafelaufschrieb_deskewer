#!/usr/bin/env python3

from pathlib import Path
import sys
import cv2
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets

ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'input'
OUT = ROOT / 'output'
OUT.mkdir(exist_ok=True)
SRC.mkdir(exist_ok=True)
FILES = sorted([p for p in SRC.rglob('*') if p.is_file() and p.suffix.lower() in {'.jpg','.jpeg','.png','.heic','.tif','.tiff'}])


def order_points(pts):
    rect = np.zeros((4, 2), dtype='float32')
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def detect_corners(image):
    """Return a likely board quadrilateral, or None when detection is uncertain."""
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 40, 140)
    edges = cv2.dilate(edges, np.ones((3, 3), dtype=np.uint8), iterations=1)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    height, width = gray.shape
    image_area = float(width * height)
    candidates = []

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < image_area * 0.08 or area > image_area * 0.95:
            continue
        perimeter = cv2.arcLength(contour, True)
        polygon = cv2.approxPolyDP(contour, perimeter * 0.03, True)
        if len(polygon) != 4 or not cv2.isContourConvex(polygon):
            continue
        points = polygon.reshape(4, 2).astype('float32')
        rect = cv2.minAreaRect(points)
        rect_area = cv2.contourArea(cv2.boxPoints(rect).astype('float32'))
        if rect_area <= 0:
            continue
        rectangularity = area / rect_area
        if rectangularity < 0.55:
            continue
        touches_edge = np.any(
            (points[:, 0] <= 5) | (points[:, 0] >= width - 6) |
            (points[:, 1] <= 5) | (points[:, 1] >= height - 6)
        )
        score = area * rectangularity * (0.25 if touches_edge else 1.0)
        candidates.append((score, points))

    if not candidates:
        return None
    _, points = max(candidates, key=lambda candidate: candidate[0])
    return order_points(points)


class Label(QtWidgets.QLabel):
    clicked = QtCore.pyqtSignal(int, int)
    def mousePressEvent(self, ev):
        self.clicked.emit(ev.pos().x(), ev.pos().y())

class Window(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Board warp')
        self.img_label = Label()
        self.img_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.image_scroll = QtWidgets.QScrollArea()
        self.image_scroll.setWidget(self.img_label)
        self.image_scroll.setWidgetResizable(False)
        self.info = QtWidgets.QLabel()
        self.info.setWordWrap(True)
        self.reset_btn = QtWidgets.QPushButton('Reset')
        self.save_btn = QtWidgets.QPushButton('Save / Next')
        self.quit_btn = QtWidgets.QPushButton('Quit')
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.reset_btn)
        row.addWidget(self.save_btn)
        row.addWidget(self.quit_btn)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.info)
        layout.addWidget(self.image_scroll, 1)
        layout.addLayout(row)
        self.reset_btn.clicked.connect(self.reset)
        self.save_btn.clicked.connect(self.save_next)
        self.quit_btn.clicked.connect(self.close)
        self.img_label.clicked.connect(self.add_click)
        self.idx = 0
        self.clicks = []
        self.scale = 1.0
        self.orig = None
        self.pix = None
        self.base_pix = None
        self.auto_detected = False
        self.load_current()

    def load_current(self):
        if self.idx >= len(FILES):
            self.info.setText(f'Done -> {OUT}')
            self.img_label.clear()
            return
        self.path = FILES[self.idx]
        img = cv2.imread(str(self.path))
        if img is None:
            self.idx += 1
            self.load_current()
            return
        self.orig = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w = self.orig.shape[:2]
        self.scale = 1400 / max(h, w) if max(h, w) > 1400 else 1.0
        disp = cv2.resize(self.orig, (int(w*self.scale), int(h*self.scale))) if self.scale != 1.0 else self.orig.copy()
        qimg = QtGui.QImage(disp.data, disp.shape[1], disp.shape[0], disp.strides[0], QtGui.QImage.Format_RGB888)
        self.base_pix = QtGui.QPixmap.fromImage(qimg.copy())
        self.pix = self.base_pix.copy()
        self.img_label.setPixmap(self.pix)
        self.img_label.resize(self.pix.size())
        detected = detect_corners(self.orig)
        self.clicks = []
        self.auto_detected = detected is not None
        if detected is not None:
            self.clicks = [tuple((point * self.scale).astype(int)) for point in detected]
            self.info.setText(
                f'{self.path.relative_to(SRC)}\n'
                'Corners detected automatically. Click near a point to adjust it, or click Reset for manual selection.'
            )
            self.redraw_selection()
        else:
            self.info.setText(
                f'{self.path.relative_to(SRC)}\n'
                'Corners not detected. Click 4 corners in order: top-left, top-right, bottom-right, bottom-left'
            )

    def add_click(self, x, y):
        if self.pix is None:
            return
        if self.auto_detected:
            distances = [np.hypot(x - point[0], y - point[1]) for point in self.clicks]
            nearest = int(np.argmin(distances))
            if distances[nearest] <= 35:
                self.clicks[nearest] = (x, y)
                self.redraw_selection()
            return
        if len(self.clicks) == 4:
            return
        self.clicks.append((x, y))
        self.redraw_selection()

    def redraw_selection(self):
        self.pix = self.base_pix.copy()
        painter = QtGui.QPainter(self.pix)
        painter.setPen(QtGui.QPen(QtGui.QColor('red'), 8))
        for point in self.clicks:
            painter.drawPoint(*point)
        if len(self.clicks) > 1:
            painter.setPen(QtGui.QPen(QtGui.QColor('lime'), 3))
            for first, second in zip(self.clicks, self.clicks[1:]):
                painter.drawLine(QtCore.QPoint(*first), QtCore.QPoint(*second))
        if len(self.clicks) == 4:
            polygon = QtGui.QPolygon([QtCore.QPoint(*point) for point in self.clicks])
            painter.setBrush(QtGui.QBrush(QtGui.QColor(0, 255, 0, 70)))
            painter.setPen(QtGui.QPen(QtGui.QColor('lime'), 4))
            painter.drawPolygon(polygon)
        painter.end()
        self.img_label.setPixmap(self.pix)
        self.img_label.resize(self.pix.size())

    def reset(self):
        if self.auto_detected:
            self.clicks = []
            self.auto_detected = False
            self.redraw_selection()
            self.info.setText(
                f'{self.path.relative_to(SRC)}\n'
                'Manual mode. Click 4 corners in order: top-left, top-right, bottom-right, bottom-left'
            )
        else:
            self.load_current()

    def save_next(self):
        if len(self.clicks) != 4:
            self.info.setText('Need exactly 4 clicks (TL, TR, BR, BL).')
            return
        pts = np.array(self.clicks, dtype='float32')
        if self.scale != 1.0:
            pts /= self.scale
        rect = order_points(pts)
        (tl, tr, br, bl) = rect
        widthA = np.linalg.norm(br - bl)
        widthB = np.linalg.norm(tr - tl)
        heightA = np.linalg.norm(tr - br)
        heightB = np.linalg.norm(tl - bl)
        maxW = int(max(widthA, widthB))
        maxH = int(max(heightA, heightB))
        dst = np.array([[0,0],[maxW-1,0],[maxW-1,maxH-1],[0,maxH-1]], dtype='float32')
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(cv2.cvtColor(self.orig, cv2.COLOR_RGB2BGR), M, (maxW, maxH))
        dest = OUT / self.path.relative_to(SRC)
        dest.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(dest), warped, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        self.idx += 1
        self.load_current()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = Window()
    screen = app.primaryScreen().availableGeometry()
    win.resize(min(1500, screen.width() - 80), min(1000, screen.height() - 120))
    win.show()
    sys.exit(app.exec_())
