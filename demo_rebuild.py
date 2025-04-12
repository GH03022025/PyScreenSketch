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
    QPoint,
)
from PyQt5.QtGui import QColor, QPainter, QBrush, QPen, QPainterPath, QCursor

# from custom_curve import s_curve_1


class ToolBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)  # 保留透明背景属性

        self.scr_size = QDesktopWidget().screenGeometry()
        self.scr_width = self.scr_size.width()
        self.scr_height = self.scr_size.height()
        self.scr_diagonal = math.sqrt(self.scr_width**2 + self.scr_height**2)

        self.init_height = round(self.scr_height / 3)
        self.init_width = round(self.init_height / 1.5)  # x需要改为除8
        self.init_size = QSize(self.init_width, self.init_height)  # 记录原始大小
        self.mini_height = self.init_height // 4
        self.mini_width = self.init_width // 2
        self.mini_size = QSize(self.mini_width, self.mini_height)

        self.background_color = QColor("#FFA500")  # 背景色
        self.border_color = QColor("#C07600")  # 边框色

        self.border_width = round(self.scr_diagonal / 1000)

        self.init_rad = (self.init_width - self.border_width * 2) // 2
        self.mini_rad = (self.mini_width - self.border_width * 2) // 2
        self._TL_rad = self.init_rad
        self._TR_rad = self.init_rad
        self._BL_rad = self.init_rad
        self._BR_rad = self.init_rad

        def s_curve_1(x):
            if x < 0.5:
                return 4 * x * x * x
            else:
                return 1 - pow(-2 * x + 2, 3) / 2

        curve = QEasingCurve()
        curve.setCustomType(s_curve_1)

        self.size_anim = QPropertyAnimation(self, b"size")
        self.pos_anim = QPropertyAnimation(self, b"pos")
        self.TL_rad_anim = QPropertyAnimation(self, b"TL_rad")
        self.TR_rad_anim = QPropertyAnimation(self, b"TR_rad")
        self.BL_rad_anim = QPropertyAnimation(self, b"BL_rad")
        self.BR_rad_anim = QPropertyAnimation(self, b"BR_rad")

        for anim in [
            self.size_anim,
            self.pos_anim,
            self.TL_rad_anim,
            self.TR_rad_anim,
            self.BL_rad_anim,
            self.BR_rad_anim,
        ]:
            anim.setDuration(3200)
            anim.setEasingCurve(curve)

        self.installEventFilter(self)  # 事件过滤器

        self.states = {
            "in_corner": self.is_win_in_corner(),
            "on_hovered": True,
        }

        self.resize(self.init_size)  # 调整窗口大小

        self._current_anim_move_pos = self.pos()
        self.deltas_anim_move = []

    @pyqtProperty(QPoint)
    def anim_move_pos(self):
        return self._current_anim_move_pos

    @anim_move_pos.setter
    def anim_move_pos(self, pos):
        self.deltas_anim_move.append(pos - self._current_anim_move_pos)
        self._current_anim_move_pos = pos

    @pyqtProperty(int)
    def TL_rad(self):
        return self._TL_rad

    @TL_rad.setter
    def TL_rad(self, value):
        self._TL_rad = value
        self.update()

    @pyqtProperty(int)
    def TR_rad(self):
        return self._TR_rad

    @TR_rad.setter
    def TR_rad(self, value):
        self._TR_rad = value
        self.update()

    @pyqtProperty(int)
    def BL_rad(self):
        return self._BL_rad

    @BL_rad.setter
    def BL_rad(self, value):
        self._BL_rad = value
        self.update()

    @pyqtProperty(int)
    def BR_rad(self):
        return self._BR_rad

    @BR_rad.setter
    def BR_rad(self, value):
        self._BR_rad = value
        self.update()

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
        )  # 左、上、右、下 边缘缩进

        path = QPainterPath()

        if self._TL_rad > 0:  # 左上角
            path.moveTo(adjusted_rect.left(), adjusted_rect.top() + self._TL_rad)
            path.arcTo(
                adjusted_rect.left(),
                adjusted_rect.top(),
                self._TL_rad * 2,
                self._TL_rad * 2,
                180,
                -90,
            )
        else:
            path.moveTo(adjusted_rect.left(), adjusted_rect.top())

        if self._TR_rad > 0:  # 右上角
            path.lineTo(adjusted_rect.right() - self._TR_rad, adjusted_rect.top())
            path.arcTo(
                adjusted_rect.right() - self._TR_rad * 2,
                adjusted_rect.top(),
                self._TR_rad * 2,
                self._TR_rad * 2,
                90,
                -90,
            )
        else:
            path.lineTo(adjusted_rect.right(), adjusted_rect.top())

        if self._BR_rad > 0:  # 右下角
            path.lineTo(adjusted_rect.right(), adjusted_rect.bottom() - self._BR_rad)
            path.arcTo(
                adjusted_rect.right() - self._BR_rad * 2,
                adjusted_rect.bottom() - self._BR_rad * 2,
                self._BR_rad * 2,
                self._BR_rad * 2,
                0,
                -90,
            )
        else:
            path.lineTo(adjusted_rect.right(), adjusted_rect.bottom())

        if self._BL_rad > 0:  # 左下角
            path.lineTo(adjusted_rect.left() + self._BL_rad, adjusted_rect.bottom())
            path.arcTo(
                adjusted_rect.left(),
                adjusted_rect.bottom() - self._BL_rad * 2,
                self._BL_rad * 2,
                self._BL_rad * 2,
                270,
                -90,
            )
        else:
            path.lineTo(adjusted_rect.left(), adjusted_rect.bottom())

        path.closeSubpath()

        painter.setBrush(QBrush(self.background_color))  # 绘制
        painter.setPen(QPen(self.border_color, self.border_width))
        painter.drawPath(path)

    def move_with_mouse(self, event):
        if hasattr(self, "mouse_offset") and event.buttons() & Qt.LeftButton:
            new_pos = event.globalPos() - self.mouse_offset  # 计算新位置
            new_x = max(0, min(new_pos.x(), self.scr_width - self.width()))
            new_y = max(0, min(new_pos.y(), self.scr_height - self.height()))
            self.move(new_x, new_y)

    def get_win_screen_margin(self, offset=10):  # 检查窗口是否贴近近屏幕边缘
        pos = self.pos()
        L_dist = pos.x() - offset
        T_dist = pos.y() - offset
        R_dist = self.scr_width - pos.x() - self.width() - offset
        B_dist = self.scr_height - pos.y() - self.height() - offset

        return L_dist, T_dist, R_dist, B_dist

    def is_win_in_corner(self):
        L_dist, T_dist, R_dist, B_dist = self.get_win_screen_margin()
        return {
            "TL": T_dist < 1 or L_dist < 1,
            "TR": T_dist < 1 or R_dist < 1,
            "BL": B_dist < 1 or L_dist < 1,
            "BR": B_dist < 1 or R_dist < 1,
        }

    def get_scale_origin(self):
        L_dist, T_dist, R_dist, B_dist = self.get_win_screen_margin()
        in_corner = {
            "TL": T_dist < 1 and L_dist < 1,
            "TR": T_dist < 1 and R_dist < 1,
            "BL": B_dist < 1 and L_dist < 1,
            "BR": B_dist < 1 and R_dist < 1,
        }

        if in_corner["TL"]:
            return self.rect().topLeft()
        elif in_corner["TR"]:
            return self.rect().topRight()
        elif in_corner["BL"]:
            return self.rect().bottomLeft()
        elif in_corner["BR"]:
            return self.rect().bottomRight()

        if T_dist < 1:
            return QPoint(
                self.rect().left() + self.rect().right() // 2, self.rect().top()
            )
        elif B_dist < 1:
            return QPoint(
                self.rect().left() + self.rect().right() // 2, self.rect().bottom()
            )
        elif L_dist < 1:
            return QPoint(
                self.rect().left(), self.rect().top() + self.rect().bottom() // 2
            )
        elif R_dist < 1:
            return QPoint(
                self.rect().right(), self.rect().top() + self.rect().bottom() // 2
            )
        return self.rect().center()

    def get_move_endpoint(self, current_size, target_size, origin_point):
        width_ratio = target_size.width() / current_size.width()
        height_ratio = target_size.height() / current_size.height()

        current_pos = self.pos()

        origin_offset = origin_point - self.rect().topLeft()

        new_x = current_pos.x() + origin_offset.x() * (1 - width_ratio)
        new_y = current_pos.y() + origin_offset.y() * (1 - height_ratio)

        return QPoint(round(new_x), round(new_y))

    def perform_anim(self, anim, start_value, end_value):
        if not hasattr(self, "count"):
            self.count = 0
        self.count += 1
        if anim.state() == QPropertyAnimation.Running:
            print(f"{self.count}: stop")
            anim.stop()

        anim.setStartValue(start_value)
        anim.setEndValue(end_value)
        print(f"{self.count}: start")
        anim.start()

    def auto_adjust_corner_rad(self):
        current_corner_states = self.is_win_in_corner()

        for corner in ["TL", "TR", "BL", "BR"]:
            anim = getattr(self, f"{corner}_rad_anim")
            rad = getattr(self, f"{corner}_rad")
            if current_corner_states[corner] != self.states["in_corner"][corner]:
                target = 0 if current_corner_states[corner] else self.init_rad
                self.perform_anim(anim, rad, target)

        self.states["in_corner"] = current_corner_states

    def auto_adjust_size(self, on_hovered: bool):
        if self.states["on_hovered"] != on_hovered:
            scale_origin = self.get_scale_origin()
            endpoint = self.get_move_endpoint(
                self.size(),
                self.init_size if on_hovered else self.mini_size,
                scale_origin,
            )
            self.perform_anim(
                self.size_anim,
                self.size(),
                self.init_size if on_hovered else self.mini_size,
            )
            self.perform_anim(self.pos_anim, self.pos(), endpoint)

            self.states["on_hovered"] = on_hovered

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                self.mouse_offset = event.globalPos() - self.frameGeometry().topLeft()
                return True
        if event.type() == QEvent.MouseMove:
            self.move_with_mouse(event)
            self.auto_adjust_corner_rad()
            return True

        if event.type() == QEvent.MouseButtonRelease:
            if event.button() == Qt.LeftButton and hasattr(self, "mouse_offset"):
                del self.mouse_offset
                return True

        if event.type() == QEvent.Enter:
            self.auto_adjust_size(on_hovered=True)
            return True

        if event.type() == QEvent.Leave:
            self.auto_adjust_size(on_hovered=False)
            return True

        return super().eventFilter(obj, event)


def main():
    app = QApplication(sys.argv)
    tool_bar = ToolBar()
    tool_bar.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
