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
        layout.addWidget(self.img_label)
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
        self.pix = QtGui.QPixmap.fromImage(qimg.copy())
        self.img_label.setPixmap(self.pix)
        self.clicks = []
        self.info.setText(f'{self.path.relative_to(SRC)}\nClick 4 corners in order: top-left, top-right, bottom-right, bottom-left')

    def add_click(self, x, y):
        if self.pix is None:
            return
        self.clicks.append((x, y))
        painter = QtGui.QPainter(self.pix)
        painter.setPen(QtGui.QPen(QtGui.QColor('red'), 8))
        painter.drawPoint(x, y)
        if len(self.clicks) > 1:
            painter.setPen(QtGui.QPen(QtGui.QColor('lime'), 3))
            p1 = QtCore.QPoint(*self.clicks[-2])
            p2 = QtCore.QPoint(*self.clicks[-1])
            painter.drawLine(p1, p2)
        painter.end()
        self.img_label.setPixmap(self.pix)

    def reset(self):
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

app = QtWidgets.QApplication(sys.argv)
win = Window()
win.resize(1500, 1000)
win.show()
sys.exit(app.exec_())
