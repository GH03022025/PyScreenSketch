from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.QtGui import QPainter, QPixmap, QPen, QColor
from PyQt5.QtCore import Qt, QPoint


class DrawingWidget(QWidget):
    def __init__(self):
        super().__init__()

        # 初始化透明背景画布
        self.canvas = QPixmap(self.size())
        self.canvas.fill(Qt.transparent)  # 透明背景

        # 默认是绘制模式
        self.drawing = False
        self.last_point = QPoint()

        # 默认画笔（黑色）
        self.pen = QPen(Qt.black, 5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)

        # 是否处于擦除模式
        self.eraser_mode = False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.last_point = event.pos()

    def mouseMoveEvent(self, event):
        if self.drawing and event.buttons() & Qt.LeftButton:
            painter = QPainter(self.canvas)

            if self.eraser_mode:
                # 真正的擦除模式
                painter.setCompositionMode(QPainter.CompositionMode_Clear)
                painter.setPen(
                    QPen(Qt.transparent, 10, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                )
                print("Eraser mode active")  # 调试输出
            else:
                # 绘制模式
                painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                painter.setPen(self.pen)

            # 绘制线条（从上一个点到当前点）
            painter.drawLine(self.last_point, event.pos())
            painter.end()

            self.last_point = event.pos()
            self.update()  # 触发 paintEvent 更新显示

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False

    def paintEvent(self, event):
        # 动态调整画布大小
        if self.canvas.size() != self.size():
            new_canvas = QPixmap(self.size())
            new_canvas.fill(Qt.transparent)
            painter = QPainter(new_canvas)
            painter.drawPixmap(0, 0, self.canvas)
            painter.end()
            self.canvas = new_canvas

        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.canvas)

    def clear_canvas(self):
        self.canvas.fill(Qt.white)
        self.update()

    def toggle_eraser(self, enabled):
        self.eraser_mode = enabled


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt 绘图与擦除")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.drawing_widget = DrawingWidget()
        self.setCentralWidget(self.drawing_widget)

        from PyQt5.QtWidgets import QPushButton, QVBoxLayout, QHBoxLayout

        toolbar = QWidget()
        toolbar.setStyleSheet("background-color: rgba(200, 200, 200, 150);")
        layout = QHBoxLayout()

        clear_btn = QPushButton("清空画布")
        clear_btn.clicked.connect(self.drawing_widget.clear_canvas)

        eraser_btn = QPushButton("橡皮擦")
        eraser_btn.setCheckable(True)
        eraser_btn.toggled.connect(self.drawing_widget.toggle_eraser)

        layout.addWidget(clear_btn)
        layout.addWidget(eraser_btn)
        toolbar.setLayout(layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(toolbar)
        main_layout.addWidget(self.drawing_widget)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.showFullScreen()
    app.exec_()

print("Done")