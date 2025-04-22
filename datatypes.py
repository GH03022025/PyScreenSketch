class PointF:
    def __init__(self, x=0, y=0):
        self.__x = round(x, 2)
        self.__y = round(y, 2)

    def __add__(self, other):
        return PointF(self.__x + other.__x, self.__y + other.__y)

    def __repr__(self):
        return f"PointF({self.__x}, {self.__y})"

    def x(self):
        return self.__x

    def y(self):
        return self.__y
