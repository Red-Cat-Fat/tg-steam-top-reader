from dataclasses import dataclass, field

max_count_game = 1_000_000

# Приоритет 1 (новые игры) > 2 (поднявшиеся) > 3 (опустившиеся) > 4 (удалённые)
new_priority = 1
up_priority = 2
down_priority = 3
delete_priority = 3


@dataclass(order=True)  # Автоматически генерирует методы сравнения для сортировки
class ChangeGamePosition:
    sort_priority: int = field(init=False)  # Приоритет для сортировки
    game_name: str

    def __post_init__(self):
        self.sort_priority = self._define_sort_priority()

    def _define_sort_priority(self) -> int:
        """Определяет приоритет для сортировки (чем меньше число, тем выше в списке)."""
        raise NotImplementedError("Должен быть реализован в дочерних классах")

    def __str__(self) -> str:
        """Конвертирует объект в строку для вывода."""
        raise NotImplementedError("Должен быть реализован в дочерних классах")


@dataclass(order=True)
class UpPosition(ChangeGamePosition):
    prev_rank: int
    curr_rank: int

    def _define_sort_priority(self) -> int:
        # Чем больше рост в рейтинге (prev_rank - curr_rank), тем выше в списке
        return up_priority * max_count_game - (self.prev_rank - self.curr_rank)

    def __str__(self) -> str:
        return f"🔼 Игра поднялась: {self.game_name} (на {self.curr_rank} место с {self.prev_rank} - поднялась на {self.prev_rank - self.curr_rank} позиций)"


@dataclass(order=True)
class DownPosition(ChangeGamePosition):
    prev_rank: int
    curr_rank: int

    def _define_sort_priority(self) -> int:
        # Чем больше падение (curr_rank - prev_rank), тем выше в списке
        return down_priority * max_count_game - (self.curr_rank - self.prev_rank)

    def __str__(self) -> str:
        return f"🔽 Игра опустилась: {self.game_name} (с {self.prev_rank} места на {self.curr_rank} - опустилась на {self.curr_rank - self.prev_rank} позиций)"


@dataclass(order=True)
class DeleteGame(ChangeGamePosition):
    prev_rank: int

    def _define_sort_priority(self) -> int:
        # Чем выше была позиция (меньше prev_rank), тем выше в списке
        return delete_priority * max_count_game + self.prev_rank

    def __str__(self) -> str:
        return f"❌ Игра выбыла из топа: {self.game_name} (была на {self.prev_rank})"


@dataclass(order=True)
class NewGame(ChangeGamePosition):
    curr_rank: int

    def _define_sort_priority(self) -> int:
        # Чем выше текущая позиция (меньше curr_rank), тем выше в списке
        return new_priority * max_count_game + self.curr_rank

    def __str__(self) -> str:
        return f"🆕 Новая игра в топе: {self.game_name} (место {self.curr_rank})"
