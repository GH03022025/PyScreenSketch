"""
此模块实现了一个自定义的工具栏窗口，具有以下特性：
- 无边框设计
- 窗口置顶显示
- 透明背景
- 圆角边框
- 鼠标拖拽移动
- 自动调整窗口圆角
- 平滑的窗口大小动画效果
"""

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
    """自定义工具栏窗口类

    特性：
    - 支持鼠标拖拽移动
    - 自动调整窗口圆角
    - 窗口大小动画效果
    - 屏幕边缘检测
    """

    def __init__(self) -> None:
        """初始化工具栏窗口"""
        super().__init__()
        # 窗口基本设置
        self.setWindowTitle("ToolBar")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 获取屏幕尺寸信息
        self.scr_size = QDesktopWidget().screenGeometry()
        self.scr_width = self.scr_size.width()
        self.scr_height = self.scr_size.height()
        self.scr_diagonal = math.sqrt(self.scr_width**2 + self.scr_height**2)

        # 边框宽度计算(基于屏幕对角线)
        self.border_width = round(self.scr_diagonal / 1000)

        # 初始窗口尺寸计算
        self.init_height = round(self.scr_height / 2.5)
        self.init_width = round(self.init_height / 8)

        # 最小化时的尺寸
        self.mini_edge_para = self.init_width  # 平行边缘时的最小宽度
        self.mini_edge_perp = round(self.init_width / 2)  # 垂直边缘时的最小宽度

        # 尺寸对象
        self.init_size = QSize(self.init_width, self.init_height)  # 初始尺寸
        self.mini_size = QSize()  # 最小化尺寸
        self.current_size = QSize(self.init_width, self.init_height)  # 当前尺寸

        # 圆角半径设置
        self.init_rad = self.init_width // 4  # 初始圆角半径
        self._TL_rad = self.init_rad  # 左上角半径
        self._TR_rad = self.init_rad  # 右上角半径
        self._BL_rad = self.init_rad  # 左下角半径
        self._BR_rad = self.init_rad  # 右下角半径

        # 鼠标拖拽相关
        self._mouse_drag_current_pos = QPointF()  # 鼠标当前位置
        self._pos_offsets = []  # 位置偏移量记录

        # 初始化动画效果
        self.size_anim = QPropertyAnimation(self, b"win_size")  # 大小动画
        self.TL_rad_anim = QPropertyAnimation(self, b"TL_rad")  # 左上角圆角动画
        self.TR_rad_anim = QPropertyAnimation(self, b"TR_rad")  # 右上角圆角动画
        self.BL_rad_anim = QPropertyAnimation(self, b"BL_rad")  # 左下角圆角动画
        self.BR_rad_anim = QPropertyAnimation(self, b"BR_rad")  # 右下角圆角动画

        # 设置动画参数
        for anim in [
            self.size_anim,
            self.TL_rad_anim,
            self.TR_rad_anim,
            self.BL_rad_anim,
            self.BR_rad_anim,
        ]:
            anim.setDuration(320)  # 动画持续时间320ms
            anim.setEasingCurve(QEasingCurve.InOutCubic)  # 缓动曲线

        # 窗口状态记录
        self.states = {
            "in_corner": self._is_win_in_corner(),  # 是否在屏幕角落
            "on_hovered": True,  # 是否鼠标悬停
        }

        # 创建主布局
        self.central_layout = QVBoxLayout()
        self.setLayout(self.central_layout)
        self.central_layout.setContentsMargins(0, 0, 0, 0)  # 无外边距

        # 中央控件
        self.central_widget = QWidget()
        self.central_widget.setObjectName("central_widget")
        self.central_layout.addWidget(self.central_widget)

        # 初始化圆角
        self._update_corner_rad()

        # 设置初始大小并安装事件过滤器
        self.resize(self.init_size)
        self.installEventFilter(self)

    # 窗口大小属性(用于动画)
    @pyqtProperty(QSize)
    def win_size(self):
        """获取当前窗口大小"""
        return self.current_size

    @win_size.setter
    def win_size(self, size):
        """设置窗口大小(带缩放补偿)"""
        self._scale_compensation(size)

    # 圆角半径属性(用于动画)
    @pyqtProperty(int)
    def TL_rad(self):
        """获取左上角圆角半径"""
        return self._TL_rad

    @TL_rad.setter
    def TL_rad(self, value):
        """设置左上角圆角半径"""
        self._TL_rad = value
        self._update_corner_rad()
        self.update()

    @pyqtProperty(int)
    def TR_rad(self):
        """获取右上角圆角半径"""
        return self._TR_rad

    @TR_rad.setter
    def TR_rad(self, value):
        """设置右上角圆角半径"""
        self._TR_rad = value
        self._update_corner_rad()
        self.update()

    @pyqtProperty(int)
    def BL_rad(self):
        """获取左下角圆角半径"""
        return self._BL_rad

    @BL_rad.setter
    def BL_rad(self, value):
        """设置左下角圆角半径"""
        self._BL_rad = value
        self._update_corner_rad()
        self.update()

    @pyqtProperty(int)
    def BR_rad(self):
        """获取右下角圆角半径"""
        return self._BR_rad

    @BR_rad.setter
    def BR_rad(self, value):
        """设置右下角圆角半径"""
        self._BR_rad = value
        self._update_corner_rad()
        self.update()

    def eventFilter(self, obj, event: QEvent) -> bool:
        """事件过滤器处理各种鼠标事件"""
        event_handlers = {
            QEvent.MouseButtonPress: self._handle_mouse_press,  # 鼠标按下
            QEvent.MouseMove: self._handle_mouse_move,  # 鼠标移动
            QEvent.MouseButtonRelease: self._handle_mouse_release,  # 鼠标释放
            QEvent.Enter: self._handle_hover_enter,  # 鼠标进入
            QEvent.Leave: self._handle_hover_leave,  # 鼠标离开
        }

        handler = event_handlers.get(event.type())

        if handler and handler(event):
            return True

        return super().eventFilter(obj, event)

    def _handle_mouse_press(self, event) -> bool:
        """处理鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self._mouse_drag_current_pos = event.globalPos()
            return True
        return False

    def _handle_mouse_move(self, event) -> bool:
        """处理鼠标移动事件"""
        self._auto_adjust_corner_rad()
        offset = event.globalPos() - self._mouse_drag_current_pos
        offset = QPointF(offset.x(), offset.y())
        self._pos_offsets.append(offset)
        self._mouse_drag_current_pos = event.globalPos()
        self._update_pos()
        return True

    def _handle_mouse_release(self, event) -> bool:
        """处理鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            return True
        return False

    def _handle_hover_enter(self, event) -> bool:
        """处理鼠标进入事件"""
        if not self.states["on_hovered"]:
            self._update_size(on_hovered=True)
            self.states["on_hovered"] = True
        return True

    def _handle_hover_leave(self, event) -> bool:
        """处理鼠标离开事件"""
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
        """计算窗口到屏幕四边的距离

        参数:
            pos: 窗口位置(QPoint), 默认为当前窗口位置
            size: 窗口大小(QSize), 默认为当前窗口大小
            offset: 偏移量, 默认为0

        返回:
            元组: (左距, 上距, 右距, 下距)
        """
        current_pos = pos if pos is not None else self.pos()
        current_size = size if size is not None else self.size()

        return (
            current_pos.x() - offset,  # 左距
            current_pos.y() - offset,  # 上距
            self.scr_width - current_pos.x() - current_size.width() - offset,  # 右距
            self.scr_height - current_pos.y() - current_size.height() - offset,  # 下距
        )

    def _is_win_in_corner(self) -> Dict[str, bool]:
        """检测窗口是否在屏幕角落

        返回:
            字典: 包含四个角落的状态(TL, TR, BL, BR)
        """
        L_dist, T_dist, R_dist, B_dist = self._get_win_screen_margin()
        return {
            "TL": T_dist <= 1 or L_dist <= 1,  # 左上角
            "TR": T_dist <= 1 or R_dist <= 1,  # 右上角
            "BL": B_dist <= 1 or L_dist <= 1,  # 左下角
            "BR": B_dist <= 1 or R_dist <= 1,  # 右下角
        }

    def _auto_adjust_corner_rad(self) -> None:
        """自动调整窗口圆角半径"""
        current_corner_states = self._is_win_in_corner()

        # 如果窗口不在角落且状态未改变，则直接返回
        if (
            not any(current_corner_states.values())
            and current_corner_states == self.states["in_corner"]
        ):
            self.states["in_corner"] = current_corner_states
            return

        # 遍历四个角落，根据需要调整圆角
        for corner in ["TL", "TR", "BL", "BR"]:
            anim = getattr(self, f"{corner}_rad_anim")  # 获取对应角落的动画
            rad = getattr(self, f"{corner}_rad")  # 获取当前圆角半径

            # 如果角落状态发生变化，则执行动画
            if current_corner_states[corner] != self.states["in_corner"][corner]:
                target = 0 if current_corner_states[corner] else self.init_rad
                self._perform_anim(anim, rad, target)

        self.states["in_corner"] = current_corner_states

    def _update_corner_rad(self) -> None:
        """更新窗口圆角样式"""
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
        """更新窗口位置"""
        pos_offset = sum(self._pos_offsets, QPointF())
        x_offset = round(pos_offset.x() // 1)
        x_remain = pos_offset.x() % 1
        y_offset = round(pos_offset.y() // 1)
        y_remain = pos_offset.y() % 1
        self._pos_offsets = [QPointF(x_remain, y_remain)]
        pos = self.pos() + QPoint(x_offset, y_offset)

        # 确保窗口不会移出屏幕
        new_x = max(0, min(pos.x(), self.scr_width - self.width()))
        new_y = max(0, min(pos.y(), self.scr_height - self.height()))

        self.move(new_x, new_y)

    def _perform_anim(
        self,
        anim: QPropertyAnimation,
        start_value: Union[int, QSize],
        end_value: Union[int, QSize],
    ) -> None:
        """执行动画效果

        参数:
            anim: 动画对象
            start_value: 起始值
            end_value: 结束值
        """
        if anim.state() == QPropertyAnimation.Running:
            anim.stop()

        anim.setStartValue(start_value)
        anim.setEndValue(end_value)
        anim.start()

    def _scale_compensation(self, size: QSize) -> None:
        """窗口大小变化的补偿处理

        当窗口大小变化时，确保窗口不会移出屏幕
        """
        L_dist, T_dist, R_dist, B_dist = self._get_win_screen_margin()

        # 计算缩放比例
        x_ratio = 0 if L_dist <= 1 else (1 if R_dist <= 1 else 0.5)
        y_ratio = 0 if T_dist <= 1 else (1 if B_dist <= 1 else 0.5)

        self.resize(size)

        # 计算位置偏移
        x_offset = (self.current_size.width() - size.width()) * x_ratio
        y_offset = (self.current_size.height() - size.height()) * y_ratio

        self.current_size = size

        # 更新位置
        self._pos_offsets.append(QPointF(x_offset, y_offset))
        self._update_pos()

    def _update_size(self, on_hovered: bool) -> None:
        """更新窗口大小

        参数:
            on_hovered: 是否鼠标悬停
        """
        L_dist, T_dist, R_dist, B_dist = self._get_win_screen_margin()

        # 计算最小化尺寸
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

        # 执行大小变化动画
        self._perform_anim(self.size_anim, start_size, end_size)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    tool_bar = ToolBar()
    tool_bar.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
