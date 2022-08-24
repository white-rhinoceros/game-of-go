import enum
from collections import namedtuple


# Мы можем обращаться к классу например так:
# Player.black.name или Player.black.value.
class Player(enum.Enum):
    black = 1
    white = 2

    # Декоратор @property позволяет обращаться к методу, как к свойству.
    # Можно еще добавить декоратор @other.setter за этим объявлением так: def other.setter(self, player)
    # который позволит маскировать сеттер мод свойство.
    @property
    def other(self):
        return Player.black if self == Player.white else Player.white


class Point(namedtuple('Point', 'row col')):
    def neighbors(self):
        return [
            Point(self.row - 1, self.col),
            Point(self.row + 1, self.col),
            Point(self.row, self.col - 1),
            Point(self.row, self.col + 1),
        ]
