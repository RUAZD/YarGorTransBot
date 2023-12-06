from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def InlineButton(text: str, data: str | CallbackData, *, is_url: bool = False) -> InlineKeyboardButton:
    """
    Создаёт InlineKeyboardButton кнопку
    :param text: текст на кнопке
    :param data: данные для callback запроса в виде строки или фабрики callbacks
    :param is_url: является ли data ссылкой и нужно ли создать кнопку с url
    :return: InlineKeyboardButton
    """
    if not is_url:
        if isinstance(data, CallbackData):
            data = data.pack()
        return InlineKeyboardButton(text=text, callback_data=data)
    else:
        assert isinstance(data, str), "url не может быть CallbackData"
        return InlineKeyboardButton(text=text, url=data)


class Markup:
    def __init__(self):
        self._temp_: list[InlineKeyboardButton] = list()
        self._buttons_: list[list[InlineKeyboardButton]] = list()

    def btn(self, text: str, data: str | CallbackData, *, is_url: bool = False) -> "Markup":
        """
        Создаёт кнопку и добавляет её во временный список с подготовленными кнопками
        :param text: текст на кнопке
        :param data: данные для callback запроса в виде строки или фабрики callbacks
        :param is_url: является ли data ссылкой и нужно ли создать кнопку с url
        :return:
        """
        self._temp_.append(InlineButton(text=text, data=data, is_url=is_url))
        return self

    def btr(self, text: str, data: str | CallbackData, *, is_url: bool = False) -> "Markup":
        """
        Создаёт кнопку и добавляет её в новый ряд InlineKeyboardMarkup
        :param text: текст на кнопке
        :param data: данные для callback запроса в виде строки или фабрики callbacks
        :param is_url: является ли data ссылкой и нужно ли создать кнопку с url
        :return:
        """
        self._buttons_.append([InlineButton(text=text, data=data, is_url=is_url)])
        return self

    def btp(self, text: str, data: str | CallbackData, *, is_url: bool = False) -> "Markup":
        """
        Добавляет ряд кнопок из временного списка и новой кнопки
        :param text: текст на кнопке
        :param data: данные для callback запроса в виде строки или фабрики callbacks
        :param is_url: является ли data ссылкой, а кнопка - url?
        :return:
        """
        return self.btn(text=text, data=data, is_url=is_url).pack()

    def add(self, button: InlineKeyboardButton) -> "Markup":
        """
        Добавляет кнопку во временный список
        :param button: Готовая InlineKeyboard кнопка
        """
        self._temp_.append(button)
        return self

    def row(self, button: InlineKeyboardButton) -> "Markup":
        """
        Добавляет кнопку в новый ряд
        :param button: Готовая InlineKeyboard кнопка
        """
        self._buttons_.append([button])
        return self

    def pack(self) -> "Markup":
        """
        Переносит временный список с подготовленными кнопками
        в новый ряд InlineKeyboardMarkup
        """
        if len(self._temp_) > 0:
            self._buttons_.append(list(self._temp_))
            self._temp_.clear()
        return self

    def packs(self, c: int = 2) -> "Markup":
        """
        Разбивает временный список с подготовленными кнопками
        на несколько новых рядов и добавляет их в InlineKeyboardMarkup
        :param c: Количество кнопок в ряде
        """
        if len(self._temp_) > 0:
            self._buttons_ += [self._temp_[i:i + c] for i in range(0, len(self._temp_), c)]
            self._temp_.clear()
        return self

    def as_markup(self) -> InlineKeyboardMarkup:
        """ Генерирует готовую InlineKeyboardMarkup для сообщений """
        if len(self._temp_) > 0:
            self.pack()
        return InlineKeyboardMarkup(inline_keyboard=self._buttons_)

    def as_reply_keyboard_markup(self, *, is_persistent: bool = False, is_resize: bool = False,
                                 is_one_time: bool = False, description: str = None) -> "Keyboard":
        """ Преобразует KeyboardMarkup конструктор из Inline в Reply """
        k = Keyboard(is_persistent=is_persistent, is_resize=is_resize, is_one_time=is_one_time, description=description)
        k._temp_ = self._temp_
        k._keyboard_ = [[KeyboardButton(text=button.text) for button in row] for row in self._buttons_]
        return k


class Keyboard:
    def __init__(self, *, is_persistent: bool = False, is_resize: bool = False, is_one_time: bool = False,
                 description: str = None):
        """
        :param is_persistent:
            Запрашивает у клиентов всегда показывать клавиатуру, когда обычная клавиатура скрыта.
            По умолчанию имеет значение false, и в этом случае пользовательскую клавиатуру
            можно скрыть и открыть с помощью значка клавиатуры.
        :param is_resize:
            Просит клиентов изменить размер клавиатуры по вертикали для оптимальной посадки
            (например, уменьшить размер клавиатуры, если кнопок всего два ряда).
            По умолчанию имеет значение false, и в этом случае пользовательская клавиатура
            всегда имеет ту же высоту, что и стандартная клавиатура приложения.
        :param is_one_time:
            Запрашивает у клиентов скрытие клавиатуры сразу после ее использования.
            Клавиатура по-прежнему будет доступна,
            но клиенты будут автоматически отображать в чате привычную букву-клавиатуру —
            пользователь может нажать специальную кнопку в поле ввода, чтобы снова увидеть кастомную клавиатуру.
            Значение по умолчанию — false.
        :param description:
            Заполнитель, который будет отображаться в поле ввода, когда клавиатура активна; 1-64 символа.
        """
        self._temp_: list[KeyboardButton] = list()
        self._keyboard_: list[list[KeyboardButton]] = list()
        self.is_persistent = is_persistent
        self.is_resize = is_resize
        self.is_one_time = is_one_time
        self.description = description

    def add(self, *text: str) -> "Keyboard":
        """
        Добавляет кнопки во временный список
        :param text: Текст на кнопках
        """
        self._temp_ += [KeyboardButton(text=txt) for txt in text]
        return self

    def line(self, *text: str) -> "Keyboard":
        """
        Добавляет в новый ряд кнопки из временного списка и новых кнопок
        :param text: Текст на кнопках
        """
        return self.add(*text).pack()

    def row(self, *text: str) -> "Keyboard":
        """
        Добавляет кнопки в новый ряд
        :param text: Текст на кнопках
        """
        self._keyboard_.append([KeyboardButton(text=txt) for txt in text])
        return self

    def pack(self) -> "Keyboard":
        """ Добавляет в новый ряд кнопки из временного списка """
        if len(self._temp_) > 0:
            self._keyboard_.append(self._temp_)
            self._temp_.clear()
        return self

    def packs(self, c: int = 2) -> "Keyboard":
        """
        Переносит кнопки из временного списка в новые ряды с определённым количеством кнопок
        :param c: Максимальное количество кнопок в каждом ряду
        """
        if len(self._temp_) > 0:
            self._keyboard_ += [self._temp_[i:i + c] for i in range(0, len(self._temp_), c)]
            self._temp_.clear()
        return self

    def as_markup(self) -> ReplyKeyboardMarkup:
        """ Генерирует готовую ReplyKeyboard разметку для сообщений """
        keyboard = ReplyKeyboardMarkup(
            keyboard=self.pack()._keyboard_,
            is_persistent=self.is_persistent,
            resize_keyboard=self.is_resize,
            one_time_keyboard=self.is_one_time,
            input_field_placeholder=self.description
        )
        return keyboard
