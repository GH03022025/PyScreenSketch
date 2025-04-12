from PyQt5.QtCore import QEasingCurve


def s_curve_1(x):
    if x < 0.5:
        return 4 * x * x * x
    else:
        return 1 - pow(-2 * x + 2, 3) / 2

    curve = QEasingCurve()
    curve.setCustomType(s_curve_1)
    return curve
    