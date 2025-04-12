import sys

# import cProfile
# import pstats
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QPushButton,
    QColorDialog,
)
from PyQt5.QtCore import Qt, QPoint, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QPainter, QPen, QColor, QPolygon, QPixmap
from pynput import mouse


class TransparentWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setGeometry(
            0, 0, QApplication.desktop().width(), QApplication.desktop().height()
        )

        # 初始化绘图缓冲和参数
        self.buffer_pixmap = QPixmap(self.size())
        self.buffer_pixmap.fill(Qt.transparent)
        self.points = []
        self.pen = QPen(QColor(255, 0, 0, 100), 4, Qt.SolidLine, Qt.RoundCap)
        self.last_point = None

    def paintEvent(self, event):
        """直接绘制缓冲画布"""
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.buffer_pixmap)

    def add_point(self, x, y):
        """增量绘制到缓冲画布"""
        current_point = QPoint(x, y)

        if self.last_point:
            # 在缓冲画布上绘制线段
            painter = QPainter(self.buffer_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(self.pen)
            painter.drawLine(self.last_point, current_point)
            painter.end()

        self.last_point = current_point
        self.points.append(current_point)
        self.update()

    def clear_points(self):
        """清除轨迹并重置缓冲"""
        self.points = []
        self.last_point = None
        self.buffer_pixmap.fill(Qt.transparent)
        self.update()

    def set_pen_color(self, color):
        """更新颜色并重绘缓冲"""
        self.pen.setColor(color)
        self.redraw_buffer()

    def set_pen_width(self, width):
        """更新粗细并重绘缓冲"""
        self.pen.setWidth(width)
        self.redraw_buffer()

    def redraw_buffer(self):
        """完全重绘缓冲画布"""
        self.buffer_pixmap.fill(Qt.transparent)
        if len(self.points) < 2:
            return

        painter = QPainter(self.buffer_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(self.pen)
        painter.drawPolyline(QPolygon(self.points))
        painter.end()
        self.update()

    def resizeEvent(self, event):
        """窗口大小变化时重置缓冲"""
        self.buffer_pixmap = QPixmap(self.size())
        self.redraw_buffer()


class MouseListener(QObject):
    move_signal = pyqtSignal(int, int)
    click_signal = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.is_pressing = False

    def on_click(self, x, y, button, pressed):
        self.is_pressing = pressed
        self.click_signal.emit(pressed)
        if pressed:
            self.move_signal.emit(x, y)

    def on_move(self, x, y):
        if self.is_pressing:
            self.move_signal.emit(x, y)

    def start_listening(self):
        with mouse.Listener(on_click=self.on_click, on_move=self.on_move) as listener:
            listener.join()


class ListenerThread(QThread):
    def __init__(self, listener):
        super().__init__()
        self.listener = listener

    def run(self):
        self.listener.start_listening()


class ControlWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("画笔设置")
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

        self.size_input = QSpinBox()
        self.size_input.setRange(1, 20)
        self.size_input.setValue(4)

        self.color_btn = QPushButton("选择颜色")
        self.color_btn.clicked.connect(self.choose_color)

        layout = QHBoxLayout()
        layout.addWidget(QLabel("画笔粗细:"))
        layout.addWidget(self.size_input)
        layout.addWidget(self.color_btn)
        self.setLayout(layout)

        self.size_input.valueChanged.connect(self.update_pen)

    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.main_window.set_pen_color(color)

    def update_pen(self):
        self.main_window.set_pen_width(self.size_input.value())


if __name__ == "__main__":
    # profiler = cProfile.Profile()
    # profiler.enable()

    app = QApplication(sys.argv)
    window = TransparentWindow()
    window.show()

    control = ControlWindow(window)
    control.show()

    listener = MouseListener()
    listener.move_signal.connect(window.add_point)
    listener.click_signal.connect(lambda p: window.clear_points() if not p else None)

    thread = ListenerThread(listener)
    thread.start()

    # profiler.disable()
    # profiler_stats = pstats.Stats(profiler)
    # profiler_stats.sort_stats("cumtime")
    # profiler_stats.dump_stats("results.prof")
    # profiler_stats.print_stats()

    sys.exit(app.exec_())
