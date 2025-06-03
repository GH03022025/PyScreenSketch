import sys
import math
from typing import Dict, List, Tuple, Optional, Union
import time

from PyQt5.QtWidgets import (
    QWidget,
    QDesktopWidget,
    QApplication,
    QVBoxLayout,
    QGraphicsDropShadowEffect,
    QSizePolicy,
)
from PyQt5.QtCore import (
    Qt,
    QPropertyAnimation,
    QSize,
    QEasingCurve,
    pyqtProperty,
    QEvent,
    QPoint,
    QPointF,
    QRectF,
    QSizeF,
    pyqtSignal,
)
from PyQt5.QtGui import QCursor, QPainter, QColor


class ToolBar(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PyScreenSketch")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)  # 背景透明
        self.setAttribute(Qt.WA_NoSystemBackground, True)  # 优化性能

        self.scr_size = QDesktopWidget().screenGeometry()
        self.scr_w = self.scr_size.width()  # 屏幕宽度
        self.scr_h = self.scr_size.height()  # 屏幕高度
        self.scr_center_x = self.scr_w * 0.5  # 屏幕中心X坐标
        self.scr_center_y = self.scr_h * 0.5  # 屏幕中心Y坐标

        self.unit_len = self.scr_h * 0.4

        self.cnt_h = round(self.unit_len)  # 实际绘制区域高度
        self.cnt_w = round(self.unit_len * 0.125)  # 实际绘制区域宽度
        self.cur_cnt_h = self.cnt_h  # 当前绘制区域高度
        self.cur_cnt_w = self.cnt_w  # 当前绘制区域宽度

        self.cnt_frame_mg = self.cnt_w

        self.h = self.cur_cnt_h + self.cnt_frame_mg * 2  # 画布高度
        self.w = self.cur_cnt_w + self.cnt_frame_mg * 2  # 画布宽度

        self.cur_pos_x = round(self.scr_center_x - self.w * 0.5)
        self.cur_pos_y = round(self.scr_center_y - self.h * 0.5)

        self.cnt_frame = QVBoxLayout(self)  # 布局器边框
        self.cnt_frame.setContentsMargins(*[self.cnt_frame_mg] * 4)
        self.setLayout(self.cnt_frame)

        self.cnt = QWidget(self)  # 绘制区域
        self.cnt.setObjectName("cnt")
        self.cnt.setCursor(Qt.OpenHandCursor)
        self.cnt_frame.addWidget(self.cnt)  # 添加绘制区域到布局器

        self.cnt_shadow = QGraphicsDropShadowEffect()
        self.cnt.setGraphicsEffect(self.cnt_shadow)
        self.cnt_shadow_color = QColor(0, 0, 0, 255)  # 阴影颜色
        self.cnt_shadow_blur_radius = round(self.cnt_frame_mg * 0.3)  # 阴影模糊半径

        self.bg_color = "#282626"
        self.bd_width = round(self.unit_len * 0.003)
        self.bd_color = "#877F7F"
        self.bd_radius = round(self.unit_len * 0.02)

        self.cur_bg_color = self.bg_color
        self.cur_bd_color = self.bd_color
        self.cur_bd_width = self.bd_width
        self.cur_bd_radius = self.bd_radius

        self.cached_style = None

        self.dragging_offsets: List[QPoint] = []  # 拖动偏移量列表
        self.scale_offsets: List[QPoint] = []  # 缩放偏移量列表

        self.cnt.installEventFilter(self)  # 安装事件过滤器

        self._set_shadow_style()  # 设置阴影样式
        self._set_win_style()  # 设置窗口样式
        self._set_geometry()

    def eventFilter(self, obj, event: QEvent) -> bool:
        event_handlers = {
            QEvent.MouseButtonPress: self._handle_mouse_btn_press,
            QEvent.MouseButtonRelease: self._handle_mouse_btn_release,
            QEvent.MouseMove: self._handle_mouse_move,
            QEvent.Enter: self._handle_enter,
            QEvent.Leave: self._handle_leave,
        }

        handler = event_handlers.get(event.type())

        if handler and handler(obj, event):
            return True

        return super().eventFilter(obj, event)

    def _handle_mouse_btn_press(self, obj, event: QEvent) -> bool:
        if event.button() == Qt.LeftButton:
            self.cur_drag_pos = event.globalPos()
            self._scale(1.1, event.pos())
            # self.cnt_shadow_color = QColor(0,0,0,200)
            self.cnt_shadow_blur_radius = self.cnt_frame_mg
            self._set_shadow_style()
            self.cnt.setCursor(Qt.ClosedHandCursor)
        return True

    def _handle_mouse_btn_release(self, obj, event: QEvent) -> bool:
        if event.button() == Qt.LeftButton:
            self._scale(1.0, event.pos())
            # self.cnt_shadow_color = QColor(0,0,0,255)
            self.cnt_shadow_blur_radius = round(self.cnt_frame_mg * 0.3)
            self._set_shadow_style()
            self.cnt.setCursor(Qt.OpenHandCursor)
        return True

    def _handle_mouse_move(self, obj, event: QEvent) -> bool:
        self._calculate_dagging_offset(event)
        # self._set_shadow_style()
        return True

    def _handle_enter(self, obj, event: QEvent) -> bool:
        self.cur_bd_color = "#FFFFFF"
        self._set_win_style()
        # return True
        return True

    def _handle_leave(self, obj, event: QEvent) -> bool:
        self.cur_bd_color = "#877F7F"
        self._set_win_style()
        # return True
        return True

    def _set_win_style(self) -> None:
        new_style = f"""
            #cnt {{
                background-color: {self.cur_bg_color};
                border: {self.cur_bd_width}px solid {self.cur_bd_color};
                border-top-left-radius: {self.cur_bd_radius}px;
                border-top-right-radius: {self.cur_bd_radius}px;
                border-bottom-left-radius: {self.cur_bd_radius}px;
                border-bottom-right-radius: {self.cur_bd_radius}px;
            }}
        """
        if new_style != self.cached_style:
            self.cnt.setStyleSheet(new_style)
            self.cached_style = new_style

    def _calculate_dagging_offset(self, event: QEvent) -> None:
        dragging_offset = event.globalPos() - self.cur_drag_pos
        self.dragging_offsets.append(dragging_offset)
        self.cur_drag_pos = event.globalPos()
        self._set_geometry()

    def _set_geometry(self) -> None:
        pos = self.pos()
        if self.dragging_offsets:
            offsets = sum(self.dragging_offsets, QPoint())
            self.dragging_offsets.clear()
            pos = pos + offsets
        if self.scale_offsets:
            offsets = sum(self.scale_offsets, QPoint())
            self.scale_offsets.clear()
            pos = pos + offsets

        pos.setX(max(pos.x(), -self.cnt_frame_mg))
        pos.setY(max(pos.y(), -self.cnt_frame_mg))
        pos.setX(min(pos.x(), self.scr_w - self.w + self.cnt_frame_mg))
        pos.setY(min(pos.y(), self.scr_h - self.h + self.cnt_frame_mg))

        self.setGeometry(pos.x(), pos.y(), self.w, self.h)

    def _set_shadow_style(self) -> None:
        # cur_center = self.pos() + QPoint(round(self.w / 2), round(self.h / 2))
        # cur_center_x = cur_center.x()
        # cur_center_y = cur_center.y()
        # offset_x = round((cur_center_x - self.scr_center_x) * 0.01)
        # offset_y = round((cur_center_y - self.scr_center_y) * 0.01)
        # offset_diag = math.sqrt(offset_x**2 + offset_y**2)
        # blur_radius = round(offset_diag * 2)
        # self.cnt_shadow.setXOffset(offset_x)
        # self.cnt_shadow.setYOffset(offset_y)
        # self.cnt_shadow.setBlurRadius(blur_radius)
        self.cnt_shadow.setColor(self.cnt_shadow_color)
        self.cnt_shadow.setBlurRadius(self.cnt_shadow_blur_radius)
        self.cnt_shadow.setXOffset(0)
        self.cnt_shadow.setYOffset(0)

    def _set_pressed_style(self) -> None:
        pass

    def _scale(self, *args) -> None:
        if len(args) == 2:
            if isinstance(args[0], float) and isinstance(args[1], QPoint):
                ratio_x = args[0]
                ratio_y = args[0]
                center = args[1]
            else:
                return
        elif len(args) == 3:
            if (
                isinstance(args[0], float)
                and isinstance(args[1], float)
                and isinstance(args[2], QPoint)
            ):
                ratio_x = args[0]
                ratio_y = args[1]
                center = args[2]
            else:
                return
        else:
            return

        self._compensate_scale_pos(ratio_x, ratio_y, center)

        self.cur_cnt_w = round(self.cnt_w * ratio_x)
        self.cur_cnt_h = round(self.cnt_h * ratio_y)

        self.w = self.cur_cnt_w + self.cnt_frame_mg * 2
        self.h = self.cur_cnt_h + self.cnt_frame_mg * 2

        self.cur_bd_width = round(self.bd_width * ratio_x)
        self.cur_bd_radius = round(self.bd_radius * ratio_x)

        self._set_win_style()
        self._set_geometry()

    def _compensate_scale_pos(
        self, ratio_x: float, ratio_y: float, center: QPoint
    ) -> None:
        offset_x = round(center.x() * (self.cur_cnt_w / self.cnt_w - ratio_x))
        offset_y = round(center.y() * (self.cur_cnt_h / self.cnt_h - ratio_y))

        self.scale_offsets.append(QPoint(offset_x, offset_y))

    def _play_animation(self) -> None:
        pass


def main():
    print(QRectF(QPointF(0, 0), QSizeF(100, 100)))
    app = QApplication(sys.argv)
    tool_bar = ToolBar()
    tool_bar.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
