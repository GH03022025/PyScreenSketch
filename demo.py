import sys
import math
from PyQt5.QtWidgets import (
    QWidget,
    QDesktopWidget,
    QApplication,
)
from PyQt5.QtCore import (
    Qt,
    QPropertyAnimation,
    QSize,
    QEasingCurve,
    pyqtProperty,
    QEvent,
)
from PyQt5.QtGui import QColor, QPainter, QBrush, QPen, QPainterPath


class ToolBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)  # 保留透明背景属性

        self.screen_size = QDesktopWidget().screenGeometry()
        self.screen_width = self.screen_size.width()
        self.screen_height = self.screen_size.height()
        self.screen_diagonal = math.sqrt(self.screen_width**2 + self.screen_height**2)

        self.init_height = round(self.screen_height / 2)
        self.init_width = round(self.init_height / 1.5)
        self.init_size = QSize(self.init_width, self.init_height)  # 记录原始大小
        self.resize(self.init_size)  # 调整窗口大小

        self.border_width = round(self.screen_diagonal / 1000)
        self.init_radius = (self.init_width - self.border_width * 2) // 2
        self.border_radius = {
            "TL": self.init_radius,
            "TR": self.init_radius,
            "BL": self.init_radius,
            "BR": self.init_radius,
        }  # 圆角设置

        self.track_border_proximity = {
            "left": False,
            "top": False,
            "right": False,
            "bottom": False,
        }

        self.background_color = QColor("#FFA500")  # 背景色
        self.border_color = QColor("#C07600")  # 边框色

        def custom_easing(x):  # 定义缓入缓出曲线
            if x < 0.5:
                return 4 * x * x * x
            else:
                return 1 - pow(-2 * x + 2, 3) / 2

        curve = QEasingCurve()  # QEasingCurve(QEasingCurve.Custom)
        curve.setCustomType(custom_easing)

        self.size_anime = QPropertyAnimation(self, b"size")  # 尺寸变化动画
        self.size_anime.setDuration(1000)  # 时长 240 毫秒
        self.size_anime.setEasingCurve(curve)  # 应用曲线curve

        self.TL_radius_anime = QPropertyAnimation(self, b"TL_radius")
        self.TL_radius_anime.setDuration(1000)  # 时长 120 毫秒
        self.TL_radius_anime.setEasingCurve(curve)  # 应用曲线curve

        self.TR_radius_anime = QPropertyAnimation(self, b"TR_radius")
        self.TR_radius_anime.setDuration(1000)  # 时长 120 毫秒
        self.TR_radius_anime.setEasingCurve(curve)  # 应用曲线curve

        self.BL_radius_anime = QPropertyAnimation(self, b"BL_radius")
        self.BL_radius_anime.setDuration(1000)  # 时长 120 毫秒
        self.BL_radius_anime.setEasingCurve(curve)  # 应用曲线curve

        self.BR_radius_anime = QPropertyAnimation(self, b"BR_radius")
        self.BR_radius_anime.setDuration(1000)  # 时长 120 毫秒
        self.BR_radius_anime.setEasingCurve(curve)  # 应用曲线curve

        # 添加鼠标拖动相关变量
        self.mouse_press_pos = None
        self.window_pos = None
        self.drag_start_pos = None

        self.installEventFilter(self)  # 事件过滤器

        # self.hovered = False  # 鼠标是否悬停

    @pyqtProperty(int)
    def TL_radius(self):
        return self.border_radius["TL"]

    @TL_radius.setter
    def TL_radius(self, value):
        self.border_radius["TL"] = value
        self.update()

    @pyqtProperty(int)
    def TR_radius(self):
        return self.border_radius["TR"]

    @TR_radius.setter
    def TR_radius(self, value):
        self.border_radius["TR"] = value
        self.update()

    @pyqtProperty(int)
    def BL_radius(self):
        return self.border_radius["BL"]

    @BL_radius.setter
    def BL_radius(self, value):
        self.border_radius["BL"] = value
        self.update()

    @pyqtProperty(int)
    def BR_radius(self):
        return self.border_radius["BR"]

    @BR_radius.setter
    def BR_radius(self, value):
        self.border_radius["BR"] = value
        self.update()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Enter:
            if not hasattr(self, "hovered"):
                self.hovered = False

            if not self.hovered:
                minimized_size = QSize(
                    self.init_size.width() // 2, self.init_size.height() // 4
                )
                self.toggle_size(
                    minimized_size, self.init_size
                )  # 鼠标离开窗口后触发放大

            self.hovered = True

        elif event.type() == QEvent.Leave:
            if not hasattr(self, "hovered"):
                self.hovered = True

            if self.hovered:
                minimized_size = QSize(
                    self.init_size.width() // 2, self.init_size.height() // 4
                )
                self.toggle_size(self.size(), minimized_size)  # 鼠标进入窗口后触发缩小

            self.hovered = False

        return super(QWidget, self).eventFilter(obj, event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()  # 记录点击位置用于判断是否拖动
            self.mouse_press_pos = event.globalPos()  # 获取鼠标全局位置
            self.window_pos = self.pos()  # 获取窗口位置
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.mouse_press_pos:
            if (event.pos() - self.drag_start_pos).manhattanLength() > 4:  # 防止抖动
                delta = event.globalPos() - self.mouse_press_pos  # 计算移动距离
                new_pos = self.window_pos + delta  # 计算新位置
                new_x = max(0, min(new_pos.x(), self.screen_width - self.width()))
                new_y = max(0, min(new_pos.y(), self.screen_height - self.height()))
                self.move(new_x, new_y)  # 移动窗口

                self.handle_corner_radius()

            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mouse_press_pos = None
            self.drag_start_pos = None
            event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制圆角矩形
        rect = self.rect()
        painter.setBrush(QBrush(self.background_color))
        painter.setPen(QPen(self.border_color, self.border_width))
        rect = rect.adjusted(
            round(self.border_width / 2),
            round(self.border_width / 2),
            -round(self.border_width / 2),
            -round(self.border_width / 2),
        )  # 左、上、右、下 边缘缩进

        path = QPainterPath()

        if self.border_radius["TL"] > 0:  # 左上角
            path.moveTo(rect.left(), rect.top() + self.border_radius["TL"])
            path.arcTo(
                rect.left(),
                rect.top(),
                self.border_radius["TL"] * 2,
                self.border_radius["TL"] * 2,
                180,
                -90,
            )
        else:
            path.moveTo(rect.left(), rect.top())

        if self.border_radius["TR"] > 0:  # 右上角
            path.lineTo(rect.right() - self.border_radius["TR"], rect.top())
            path.arcTo(
                rect.right() - self.border_radius["TR"] * 2,
                rect.top(),
                self.border_radius["TR"] * 2,
                self.border_radius["TR"] * 2,
                90,
                -90,
            )
        else:
            path.lineTo(rect.right(), rect.top())

        if self.border_radius["BR"] > 0:  # 右下角
            path.lineTo(rect.right(), rect.bottom() - self.border_radius["BR"])
            path.arcTo(
                rect.right() - self.border_radius["BR"] * 2,
                rect.bottom() - self.border_radius["BR"] * 2,
                self.border_radius["BR"] * 2,
                self.border_radius["BR"] * 2,
                0,
                -90,
            )
        else:
            path.lineTo(rect.right(), rect.bottom())

        if self.border_radius["BL"] > 0:  # 左下角
            path.lineTo(rect.left() + self.border_radius["BL"], rect.bottom())
            path.arcTo(
                rect.left(),
                rect.bottom() - self.border_radius["BL"] * 2,
                self.border_radius["BL"] * 2,
                self.border_radius["BL"] * 2,
                270,
                -90,
            )
        else:
            path.lineTo(rect.left(), rect.bottom())

        path.closeSubpath()

        painter.setBrush(QBrush(self.background_color))  # 绘制
        painter.setPen(QPen(self.border_color, self.border_width))
        painter.drawPath(path)

    def toggle_size(self, start_value, end_value):
        if self.size_anime.state() == QPropertyAnimation.Running:
            self.size_anime.stop()

        self.size_anime.setStartValue(start_value)
        self.size_anime.setEndValue(end_value)
        self.size_anime.start()

    def handle_corner_radius(self):
        L, T, R, B = self.check_win_edge_distance()  # 获取当前窗口边缘距离

        new_states = {
            "TL_near": L < 1 or T < 1,
            "TR_near": R < 1 or T < 1,
            "BL_near": L < 1 or B < 1,
            "BR_near": R < 1 or B < 1,
        }  # 四个角的贴近状态

        if not hasattr(self, "_prev_states"):  # 检查状态是否发生变化
            self._prev_states = new_states.copy()

        for corner in ["TL", "TR", "BL", "BR"]:  # 处理每个角的半径变化
            anime = getattr(self, f"{corner}_radius_anime")
            radius = getattr(self, f"{corner}_radius")
            state_key = f"{corner}_near"

            if new_states[state_key] != self._prev_states[state_key]:
                if anime.state() == QPropertyAnimation.Running:
                    anime.stop()

                target = 0 if new_states[state_key] else self.init_radius
                self.change_radius(anime, radius, target)  # 执行新变化

        self._prev_states = new_states  # 更新状态记录

    def check_win_edge_distance(self):  # 检查窗口是否贴近近屏幕边缘
        pos = self.pos()
        width = self.width()
        height = self.height()
        threshold = self.border_width // 2

        L_edge_distance = pos.x() - threshold
        T_edge_distance = pos.y() - threshold
        R_edge_distance = self.screen_width - threshold - pos.x() - width
        B_edge_distance = self.screen_height - threshold - pos.y() - height

        return (
            L_edge_distance,
            T_edge_distance,
            R_edge_distance,
            B_edge_distance,
        )

    def change_radius(self, anime_instance, start_value, end_value):
        anime_instance.setStartValue(start_value)
        anime_instance.setEndValue(end_value)
        anime_instance.start()


app = QApplication(sys.argv)
tool_bar = ToolBar()
tool_bar.show()
sys.exit(app.exec_())
