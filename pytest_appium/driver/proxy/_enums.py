from enum import Enum


class Axis(Enum):
    X = 'x'
    Y = 'y'

    @property
    def inverse(self):
        return Axis.Y if self == Axis.X else Axis.X

    @property
    def size(self):
        return 'width' if self == Axis.X else 'height'


class Signum(Enum):
    POSITIVE = min
    NEGATIVE = max

    @property
    def inverse(self):
        return Signum.POSITIVE if self == Signum.NEGATIVE else Signum.NEGATIVE


class Direction(Enum):
    LEFT = (Axis.X, Signum.NEGATIVE)
    RIGHT = (Axis.X, Signum.POSITIVE)
    UP = (Axis.Y, Signum.NEGATIVE)
    DOWN = (Axis.Y, Signum.POSITIVE)

    def __init__(self, axis, direction):
        self.axis = axis
        self.signum = direction

    @property
    def inverse(self):
        return {
            self.LEFT: self.RIGHT,
            self.RIGHT: self.LEFT,
            self.UP: self.DOWN,
            self.DOWN: self.UP,
        }[self]