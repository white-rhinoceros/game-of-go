import copy
from dlgo.gotypes import Player
from dlgo.gotypes import Point


class Move:
    """
    Класс Move - ход игрока реализуется 3 возможными действиями: размещение камня на доске (Play),
    пропуск хода (Pass), и выход из игры (Resign). Каждый реализован собственным методом класса.
    """

    def __init__(self, point: Point = None, is_pass: bool = False, is_resign: bool = False) -> None:
        # Тут '^' - побитовый XOR оператор, т.е. 0 ^ 1 = 1 или 1 ^ 0 = 1, в остальных случаях 0.
        assert (point is not None) ^ is_pass ^ is_resign, "Допускается только одно действие игрока"
        self.point: Point = point
        self.is_play: bool = self.point is not None
        self.is_pass: bool = is_pass
        self.is_resign: bool = is_resign

        # Размещение камня на доске
        @classmethod
        def play(cls, play_point: Point) -> Move:
            return Move(point=play_point)

        # Пропуск хода
        @classmethod
        def pass_turn(cls) -> Move:
            return Move(is_pass=True)

        # Выход из игры
        @classmethod
        def resign(cls) -> Move:
            return Move(is_resign=True)


class GoString:
    """Класс цепочки камней. Определяет связанную группу камней и ее степени свободы. liberties - свободы."""

    def __init__(self, color, stones, liberties) -> None:
        self.color = color
        self.stones = set(stones)
        self.liberties = set(liberties)

    def remove_liberty(self, point: Point) -> None:
        self.liberties.remove(point)

    def add_liberty(self, point) -> None:
        self.liberties.add(point)

    def merged_with(self, go_string):
        assert go_string.color == self.color, "Не допускается объединение цепочек камней разного цвета"
        combine_stones = self.stones | go_string.stones
        return GoString(
            self.color,
            combine_stones,
            (self.liberties | go_string.liberties) - combine_stones
        )

    @property
    def num_liberties(self) -> int:
        return int(len(self.liberties))

    def __eq__(self, other):
        return isinstance(other, GoString) \
               and self.color == other.color \
               and self.stones == other.stones \
               and self.liberties == other.liberties


class Board:
    """Класс доски"""

    def __init__(self, num_rows: int, num_cols: int) -> None:
        self.num_rows: int = num_rows
        self.num_cols: int = num_cols
        self._grid = {}  # Словарь, который хранит цепочки камней.

    def place_stone(self, player: Player, point: Point) -> None:
        """Размещение камня на доске и проверка количества степеней свободы соседних точек. """
        assert self.is_on_grid(point), "Точка размещения камня находится за границами сетки доски"
        assert self._grid.get(point) is None, "Точка размещения камня уже принадлежит цепочке камней (занята)"

        adjacent_same_color = []  # adjacent - примыкающий
        adjacent_opposite_color = []
        liberties = []

        # С начала исследуем непосредственные соседи точки.
        for neighbor in point.neighbors():
            if not self.is_on_grid(neighbor):
                continue

            neighbor_string = self._grid.get(neighbor)

            if neighbor_string is None:
                liberties.append(neighbor)
            elif neighbor_string.color == player:
                if neighbor_string not in adjacent_same_color:
                    adjacent_same_color.append(neighbor_string)
            else:
                if neighbor_string.color not in adjacent_opposite_color:
                    adjacent_opposite_color.append(neighbor_string)

            new_string = GoString(player, [point], liberties)

            # Объединение всех смежных цепочек камней одного вида.
            for same_color_string in adjacent_same_color:
                new_string = new_string.merged_with(same_color_string)
            for new_string_point in new_string.stones:
                self._grid[new_string_point] = new_string

            # Уменьшение количества степеней свободы соседних цепочек камней противоположного цвета.
            for other_color_string in adjacent_opposite_color:
                other_color_string.remove_liberty(point)

            # Удаление с доски цепочек камней противоположного цвета с нулевой степенью свободы.
            for other_color_string in adjacent_opposite_color:
                if other_color_string.num_liberties == 0:
                    self._remove_string(other_color_string)

    def is_on_grid(self, point: Point) -> bool:
        """Метод проверяет попадает ли переданная точка в границы сетки доски."""
        return 1 <= point.row <= self.num_rows and 1 <= point.col <= self.num_cols

    def get_go_string(self, point: Point) -> GoString | None:
        """Возвращает всю цепочку камней, если в этой точке находится камень, в противном случае - None."""
        string = self._grid.get(point)
        if string is None:
            return None
        return string

    def _remove_string(self, string: GoString) -> None:
        """
        Удаление цепочки камней с доски (учитываются также случаи, когда удаление цепочки может привести к
        увеличению степеней свободы других цепочек).
        :param string: GoString Цепочка камней
        """
        for point in string.stones:
            for neighbor in point.neighbors():
                neighbor_string = self._grid.get(neighbor)
                if neighbor_string is None:
                    continue
                if neighbor_string is not string:
                    neighbor_string.add_liberty(point)
            self._grid[point] = None


class GameState:
    """Класс игрового состояния доски"""

    def __init__(self, board: Board, next_player: Player, previous_state, last_move: Move | None) -> None:
        """
        :param board: Board Класс доски.
        :param next_player: Player Следующий игрок.
        :param previous_state: GameState Предыдущее состояние доски.
        :param last_move: Move Последний ход.
        """
        self.board: Board = board
        self.next_player: Player = next_player
        self.previous_state: GameState | None = previous_state
        self.last_move: Move | None = last_move

    def apply_move(self, move: Move):
        """
        Возвращает новое игровое состояние после совершения хода
        :param move: Экземпляр класса Move с текущем ходом игрока.
        """
        if move.is_play:
            next_board = copy.deepcopy(self.board)
            next_board.place_stone(self.next_player, move.point)
        else:
            next_board = self.board

        return GameState(next_board, self.next_player.other, self, move)

    @classmethod
    def new_game(cls, board_size: int):
        """Создание новой игры"""
        board = Board(*(board_size, board_size))
        return GameState(board, Player.black, None, None)  # Первым в игру вступает игрок черными камнями.

    def is_over(self):
        """Определение момента окончания игры"""
        if self.last_move is None:
            return False
        if self.last_move.is_resign:
            return True

        previous_last_move = self.previous_state.last_move
        if previous_last_move is None:
            return False

        return self.last_move.is_pass and previous_last_move.is_pass

