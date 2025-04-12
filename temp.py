from PyQt5.QtCore import QObject, QPoint, QPropertyAnimation, pyqtProperty, pyqtSignal, QEasingCurve


class PointAnimation(QObject):
    pointChanged = pyqtSignal(QPoint)

    def __init__(self, start_point, end_point, parent=None):
        super().__init__(parent)
        self._current_point = start_point
        self._start_point = start_point
        self._end_point = end_point
        self._deltas = []

        def s_curve_1(x):
            if x < 0.5:
                return 4 * x * x * x
            else:
                return 1 - pow(-2 * x + 2, 3) / 2

        curve = QEasingCurve()
        curve.setCustomType(s_curve_1)

        self.animation = QPropertyAnimation(self, b"point")
        self.animation.setStartValue(start_point)
        self.animation.setEndValue(end_point)
        self.animation.setDuration(500)  # 动画持续时间，单位为毫秒
        self.animation.setEasingCurve(curve)
        self.animation.valueChanged.connect(self.store_delta)

    def store_delta(self, new_point):
        delta_x = new_point.x() - self._current_point.x()
        delta_y = new_point.y() - self._current_point.y()
        self._deltas.append((delta_x, delta_y))
        self._current_point = new_point
        print(self._deltas)

    @pyqtProperty(QPoint, notify=pointChanged)
    def point(self):
        return self._current_point

    @point.setter
    def point(self, value):
        self.pointChanged.emit(value)

    def start(self):
        self.animation.start()

    def get_deltas(self):
        return self._deltas


# 使用示例
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    start_point = QPoint(0, 0)
    end_point = QPoint(200, 200)

    point_animation = PointAnimation(start_point, end_point)
    # point_animation.pointChanged.connect(lambda point: print(f"Current point: {point}"))
    point_animation.start()

    sys.exit(app.exec_())

    # 打印所有的增量
    # print("Deltas:", point_animation.get_deltas())

# from PyQt5.QtCore import QPoint

# print(QPoint(1, 2) + QPoint(3, 4))
