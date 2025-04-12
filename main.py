import sys
import math
from PyQt5.QtWidgets import (
    QWidget,
    QDesktopWidget,
    QApplication,
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QSize, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QColor, QPainter, QBrush, QPen, QFont


class ToolBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)  # 保留透明背景属性

        self.screen_size = QDesktopWidget().screenGeometry()
        self.screen_width = self.screen_size.width()
        self.screen_height = self.screen_size.height()
        self.screen_diagonal = math.sqrt(self.screen_width**2 + self.screen_height**2)

        self.default_height = round(self.screen_height / 3)
        self.default_width = round(self.default_height / 10)

        self.border_radius = self.default_width // 2
        self.top_left_border_radius = self.border_radius
        self.top_right_border_radius = self.border_radius
        self.bottom_left_border_radius = self.border_radius
        self.bottom_right_border_radius = self.border_radius
        self.border_width = round(self.screen_diagonal / 1000)

        self.original_size = QSize(
            self.default_width, self.default_height
        )  # 记录原始大小
        self.is_minimized = False

        self.background_color = QColor("#FFA500")  # 背景色
        self.border_color = QColor("#C07600")  # 边框色

        # 添加鼠标拖动相关变量
        self.mouse_press_pos = None
        self.window_pos = None
        self.drag_start_pos = None

        # 初始化大小动画
        self.size_animation = QPropertyAnimation(self, b"size")
        self.size_animation.setDuration(240)  # 1秒动画
        
        # 初始化圆角动画
        self.radius_animation = QPropertyAnimation(self, b"border_radius")
        self.radius_animation.setDuration(200)

        self.trigger = False
        self.press = False

        self.resize(self.default_width, self.default_height)  # 调整窗口大小

        def custom_easing(x):  # 自定义缓入缓出曲线
            # 使用三次方曲线，使缓入缓出效果更明显
            if x < 0.5:
                return 4 * x * x * x
            else:
                return 1 - pow(-2 * x + 2, 3) / 2

        curve = QEasingCurve()  # QEasingCurve(QEasingCurve.Custom)
        curve.setCustomType(custom_easing)
        self.size_animation.setEasingCurve(curve)
        self.radius_animation.setEasingCurve(curve)

    def get_border_radius(self):
        return self.border_radius

    def set_border_radius(self, radius):
        self.border_radius = radius
        self.update()

    border_radius = pyqtProperty(int, get_border_radius, set_border_radius)

    def toggle_size(self):
        if self.size_animation.state() == QPropertyAnimation.Running:
            self.size_animation.stop()
        if self.is_minimized:
            # 恢复到原始大小
            self.size_animation.setStartValue(self.size())
            self.size_animation.setEndValue(self.original_size)
        else:
            # 缩小到一半
            half_size = QSize(
                self.original_size.width() // 8, self.original_size.height()
            )
            self.size_animation.setStartValue(self.size())
            self.size_animation.setEndValue(half_size)

        self.size_animation.start()
        self.is_minimized = not self.is_minimized

    def check_edge_proximity(self):
        # 检测窗口是否靠近屏幕边缘
        pos = self.pos()
        width = self.width()
        height = self.height()
        
        # 定义贴边的阈值距离
        threshold = 5
        
        # 检查各边是否贴边
        left_edge = pos.x() <= threshold
        right_edge = (pos.x() + width) >= (self.screen_width - threshold)
        top_edge = pos.y() <= threshold
        bottom_edge = (pos.y() + height) >= (self.screen_height - threshold)
        
        # 设置圆角半径动画
        if self.radius_animation.state() == QPropertyAnimation.Running:
            self.radius_animation.stop()
            
        self.radius_animation.setStartValue(self.border_radius)
        
        # 根据贴边情况设置目标圆角半径
        target_radius = self.border_radius
        if left_edge and top_edge:
            target_radius = 0
        elif left_edge and bottom_edge:
            target_radius = 0
        elif right_edge and top_edge:
            target_radius = 0
        elif right_edge and bottom_edge:
            target_radius = 0
        else:
            target_radius = self.default_width // 2
            
        self.radius_animation.setEndValue(target_radius)
        self.radius_animation.start()

    # 添加鼠标事件处理
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self.press:
                self.trigger = True
            self.press = True
            self.drag_start_pos = event.pos()  # 记录点击位置用于判断是否拖动
            self.mouse_press_pos = event.globalPos()  # 获取鼠标全局位置
            self.window_pos = self.pos()  # 获取窗口位置
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.mouse_press_pos:
            self.trigger = False

            if (event.pos() - self.drag_start_pos).manhattanLength() > 4:  # 防止抖动
                delta = event.globalPos() - self.mouse_press_pos  # 计算移动距离
                new_pos = self.window_pos + delta  # 计算新位置
                new_x = max(0, min(new_pos.x(), self.screen_width - self.width()))
                new_y = max(0, min(new_pos.y(), self.screen_height - self.height()))
                self.move(new_x, new_y)  # 移动窗口
                self.check_edge_proximity()  # 检查是否贴边

            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.press = False
            # 如果没有明显移动，则视为点击事件
            if (event.pos() - self.drag_start_pos).manhattanLength() <= 5:
                if self.trigger:
                    self.toggle_size()
                    self.trigger = False
            self.mouse_press_pos = None
            self.drag_start_pos = None
            self.check_edge_proximity()  # 检查是否贴边
            event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制圆角矩形
        rect = self.rect()
        painter.setBrush(QBrush(self.background_color))
        painter.setPen(QPen(self.border_color, self.border_width))
        adjusted_rect = rect.adjusted(
            round(self.border_width / 2),
            round(self.border_width / 2),
            -round(self.border_width / 2),
            -round(self.border_width / 2),
        )
        painter.drawRoundedRect(adjusted_rect, self.border_radius, self.border_radius)


app = QApplication(sys.argv)
tool_bar = ToolBar()
tool_bar.show()
sys.exit(app.exec_())
