import sys
import math
from typing import Dict, Tuple, Optional, Union

from PyQt5.QtWidgets import QWidget, QDesktopWidget, QApplication, QVBoxLayout
from PyQt5.QtCore import (
    Qt,
    QPropertyAnimation,
    QSize,
    QEasingCurve,
    pyqtProperty,
    QEvent,
    QPoint,
    QPointF,
)
from PyQt5.QtGui import QCursor


class ToolBar(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ToolBar")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.scr_size = QDesktopWidget().screenGeometry()
        self.scr_width = self.scr_size.width()
        self.scr_height = self.scr_size.height()
        self.scr_diagonal = math.sqrt(self.scr_width**2 + self.scr_height**2)

        self.border_width = round(self.scr_diagonal / 1000)

        self.init_height = round(self.scr_height / 2.5)
        self.init_width = round(self.init_height / 8)

        self.mini_edge_para = self.init_width  # 平行边缘时的最小宽度
        self.mini_edge_perp = round(self.init_width / 2)  # 垂直边缘时的最小宽度

        self.init_size = QSize(self.init_width, self.init_height)  # 初始尺寸
        self.mini_size = QSize()  # 最小化尺寸
        self.current_size = QSize(self.init_width, self.init_height)  # 当前尺寸

        self.init_rad = self.init_width // 4  # 初始圆角半径
        self._TL_rad = self.init_rad  # 左上角半径
        self._TR_rad = self.init_rad  # 右上角半径
        self._BL_rad = self.init_rad  # 左下角半径
        self._BR_rad = self.init_rad  # 右下角半径

        self._mouse_drag_current_pos = QPointF()  # 鼠标当前位置
        self._pos_offsets = []  # 位置偏移量记录

        self._scale_focus_y_ratio = 0.5  # 缩放时Y轴方向的缩放倍率

        self.size_anim = QPropertyAnimation(self, b"win_size")  # 大小动画
        self.TL_rad_anim = QPropertyAnimation(self, b"TL_rad")  # 左上角圆角动画
        self.TR_rad_anim = QPropertyAnimation(self, b"TR_rad")  # 右上角圆角动画
        self.BL_rad_anim = QPropertyAnimation(self, b"BL_rad")  # 左下角圆角动画
        self.BR_rad_anim = QPropertyAnimation(self, b"BR_rad")  # 右下角圆角动画

        for anim in [
            self.size_anim,
            self.TL_rad_anim,
            self.TR_rad_anim,
            self.BL_rad_anim,
            self.BR_rad_anim,
        ]:
            anim.setDuration(320)  # 动画持续时间320ms
            anim.setEasingCurve(QEasingCurve.InOutCubic)  # 缓动曲线

        self.states = {
            "in_corner": self._is_win_in_corner(),  # 是否在屏幕角落
            "on_hovered": True,  # 是否鼠标悬停
        }

        self.central_layout = QVBoxLayout()  # 创建主布局
        self.setLayout(self.central_layout)
        self.central_layout.setContentsMargins(0, 0, 0, 0)  # 无外边距

        self.central_widget = QWidget()  # 中央控件
        self.central_widget.setObjectName("central_widget")
        self.central_layout.addWidget(self.central_widget)

        self._update_corner_rad()

        self.resize(self.init_size)
        self.installEventFilter(self)

    @pyqtProperty(QSize)  # 窗口大小属性(用于动画)
    def win_size(self):
        return self.current_size

    @win_size.setter
    def win_size(self, size):
        self._scale_compensation(size)

    @pyqtProperty(int)  # 圆角半径属性(用于动画)
    def TL_rad(self):
        return self._TL_rad

    @TL_rad.setter
    def TL_rad(self, value):
        self._TL_rad = value
        self._update_corner_rad()
        self.update()

    @pyqtProperty(int)  # 圆角半径属性(用于动画)
    def TR_rad(self):
        return self._TR_rad

    @TR_rad.setter
    def TR_rad(self, value):
        self._TR_rad = value
        self._update_corner_rad()
        self.update()

    @pyqtProperty(int)  # 圆角半径属性(用于动画)
    def BL_rad(self):
        return self._BL_rad

    @BL_rad.setter
    def BL_rad(self, value):
        self._BL_rad = value
        self._update_corner_rad()
        self.update()

    @pyqtProperty(int)  # 圆角半径属性(用于动画)
    def BR_rad(self):
        return self._BR_rad

    @BR_rad.setter
    def BR_rad(self, value):
        self._BR_rad = value
        self._update_corner_rad()
        self.update()

    def eventFilter(self, obj, event: QEvent) -> bool:
        event_handlers = {
            QEvent.MouseButtonPress: self._handle_mouse_press,  # 鼠标按下
            QEvent.MouseMove: self._handle_mouse_move,  # 鼠标移动
            QEvent.MouseButtonRelease: self._handle_mouse_release,  # 鼠标释放
            QEvent.Enter: self._handle_hover_enter,  # 鼠标进入
            QEvent.Leave: self._handle_hover_leave,  # 鼠标离开
        }

        handler = event_handlers.get(event.type())

        if handler and handler(obj, event):
            return True

        return super().eventFilter(obj, event)

    def _handle_mouse_press(self, obj, event) -> bool:
        if event.button() == Qt.LeftButton:
            self._mouse_drag_current_pos = event.globalPos()
            return True
        return False

    def _handle_mouse_move(self, obj, event) -> bool:
        self._auto_adjust_corner_rad()
        offset = event.globalPos() - self._mouse_drag_current_pos
        offset = QPointF(offset.x(), offset.y())
        self._pos_offsets.append(offset)
        self._mouse_drag_current_pos = event.globalPos()
        self._update_pos()
        return True

    def _handle_mouse_release(self, obj, event) -> bool:
        if event.button() == Qt.LeftButton:
            return True
        return False

    def _handle_hover_enter(self, obj, event) -> bool:
        if not self.states["on_hovered"]:
            self._update_size(on_hovered=True)
            self.states["on_hovered"] = True
        return True

    def _handle_hover_leave(self, obj, event) -> bool:
        self._update_scale_focus_y_ratio()
        if not self.rect().contains(self.mapFromGlobal(QCursor.pos())):
            self._update_size(on_hovered=False)
            self.states["on_hovered"] = False
        return True

    def _get_win_screen_margin(
        self,
        pos: Optional[QPoint] = None,
        size: Optional[QSize] = None,
        offset: int = 0,
    ) -> Tuple[int, int, int, int]:
        current_pos = pos if pos is not None else self.pos()
        current_size = size if size is not None else self.size()

        return (
            current_pos.x() - offset,  # 左距
            current_pos.y() - offset,  # 上距
            self.scr_width - current_pos.x() - current_size.width() - offset,  # 右距
            self.scr_height - current_pos.y() - current_size.height() - offset,  # 下距
        )

    def _is_win_in_corner(self) -> Dict[str, bool]:
        L_dist, T_dist, R_dist, B_dist = self._get_win_screen_margin()
        return {
            "TL": T_dist <= 1 or L_dist <= 1,  # 左上角
            "TR": T_dist <= 1 or R_dist <= 1,  # 右上角
            "BL": B_dist <= 1 or L_dist <= 1,  # 左下角
            "BR": B_dist <= 1 or R_dist <= 1,  # 右下角
        }

    def _auto_adjust_corner_rad(self) -> None:
        current_corner_states = self._is_win_in_corner()

        if (
            not any(current_corner_states.values())
            and current_corner_states == self.states["in_corner"]
        ):
            self.states["in_corner"] = current_corner_states
            return

        for corner in ["TL", "TR", "BL", "BR"]:
            anim = getattr(self, f"{corner}_rad_anim")  # 获取对应角落的动画
            rad = getattr(self, f"{corner}_rad")  # 获取当前圆角半径

            if current_corner_states[corner] != self.states["in_corner"][corner]:
                target = 0 if current_corner_states[corner] else self.init_rad
                self._perform_anim(anim, rad, target)

        self.states["in_corner"] = current_corner_states

    def _update_scale_focus_y_ratio(self) -> None:
        mouse_pos = self.mapFromGlobal(QCursor.pos())
        rect = self.rect()
        if rect.top() >= mouse_pos.y():
            self._scale_focus_y_ratio = 0
        elif rect.bottom() <= mouse_pos.y():
            self._scale_focus_y_ratio = 1
        else:
            self._scale_focus_y_ratio = mouse_pos.y() / self.height()

    def _update_corner_rad(self) -> None:
        self.setStyleSheet(f"""
            #central_widget {{
                background-color: {"#282626"};
                border: {self.border_width}px solid {"#877F7F"};
                border-top-left-radius: {self._TL_rad}px;
                border-top-right-radius: {self._TR_rad}px;
                border-bottom-left-radius: {self._BL_rad}px;
                border-bottom-right-radius: {self._BR_rad}px;
            }}
        """)

    def _update_pos(self) -> None:
        pos_offset = sum(self._pos_offsets, QPointF())
        x_offset = round(pos_offset.x() // 1)
        x_remain = pos_offset.x() % 1
        y_offset = round(pos_offset.y() // 1)
        y_remain = pos_offset.y() % 1
        self._pos_offsets = [QPointF(x_remain, y_remain)]
        pos = self.pos() + QPoint(x_offset, y_offset)

        new_x = max(0, min(pos.x(), self.scr_width - self.width()))
        new_y = max(0, min(pos.y(), self.scr_height - self.height()))

        self.move(new_x, new_y)

    def _perform_anim(
        self,
        anim: QPropertyAnimation,
        start_value: Union[int, QSize],
        end_value: Union[int, QSize],
    ) -> None:
        if anim.state() == QPropertyAnimation.Running:
            anim.stop()

        anim.setStartValue(start_value)
        anim.setEndValue(end_value)
        anim.start()

    def _scale_compensation(self, size: QSize) -> None:
        L_dist, T_dist, R_dist, B_dist = self._get_win_screen_margin()

        x_ratio = 0 if L_dist <= 1 else (1 if R_dist <= 1 else 0.5)

        if not (T_dist <= 1 or B_dist <= 1):  # 只在垂直方向中间区域生效
            y_ratio = self._scale_focus_y_ratio
        else:
            y_ratio = 0 if T_dist <= 1 else (1 if B_dist <= 1 else 0.5)

        self.resize(size)

        x_offset = (self.current_size.width() - size.width()) * x_ratio
        y_offset = (self.current_size.height() - size.height()) * y_ratio

        self.current_size = size
        self._pos_offsets.append(QPointF(x_offset, y_offset))
        self._update_pos()

    def _update_size(self, on_hovered: bool) -> None:
        L_dist, T_dist, R_dist, B_dist = self._get_win_screen_margin()

        mini_width = (
            self.mini_edge_perp if L_dist <= 1 or R_dist <= 1 else self.mini_edge_para
        )
        mini_height = (
            self.mini_edge_perp if T_dist <= 1 or B_dist <= 1 else self.mini_edge_para
        )
        self.mini_size = QSize(mini_width, mini_height)

        start_size = self.size()
        end_size = self.init_size if on_hovered else self.mini_size

        if end_size == self.current_size:
            return

        self._perform_anim(self.size_anim, start_size, end_size)


def main():
    app = QApplication(sys.argv)
    tool_bar = ToolBar()
    tool_bar.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
