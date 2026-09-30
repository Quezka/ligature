"""Русский перевод интерфейса Ligature."""

NAMES: dict[str, list[str]] = {}

# English singular -> (1, 2-4, 5+) forms.
PLURALS = {
    "entity": ("сущность", "сущности", "сущностей"),
    "relationship": ("связь", "связи", "связей"),
    "class": ("класс", "класса", "классов"),
    "link": ("связь", "связи", "связей"),
}

MESSAGES = {
    # ---- window and pages
    "Ligature": "Ligature",
    "Home": "Главная",
    "Diagram": "Диаграмма",
    "SQL": "SQL",
    "More": "Ещё",
    "Start": "Начать",
    "Recent": "Недавние",
    "ER and UML class diagrams for school, with the SQL they make.":
        "ER-диаграммы и диаграммы классов UML для школы — и SQL по ним.",
    "New ER diagram": "Новая ER-диаграмма",
    "New UML class diagram": "Новая диаграмма классов UML",
    "Entities, relationships, keys → SQL": "Сущности, связи, ключи → SQL",
    "Classes, inheritance, associations": "Классы, наследование, ассоциации",
    "Open…": "Открыть…",
    "A .ligature file, or a picture Ligature made": "Файл .ligature или картинка из Ligature",
    "Or look around a sample first:": "Или сначала посмотрите пример:",
    "School register (ER)": "Школьный журнал (ER)",
    "Geometric shapes (UML)": "Геометрические фигуры (UML)",
    "Diagrams you open or save show up here.":
        "Здесь появятся диаграммы, которые вы открываете или сохраняете.",
    "ER diagram": "ER-диаграмма",
    "UML class diagram": "Диаграмма классов UML",
    "Not saved yet": "Ещё не сохранена",
    "Untitled diagram": "Диаграмма без названия",
    "saved": "сохранено",
    "unsaved changes": "есть несохранённые изменения",
    "Unsaved changes": "Несохранённые изменения",
    "Save the changes to this diagram first?": "Сохранить изменения в этой диаграмме?",

    # ---- files
    "Save": "Сохранить",
    "Save (Ctrl+S)": "Сохранить (Ctrl+S)",
    "Save as…": "Сохранить как…",
    "Save the diagram": "Сохранить диаграмму",
    "Open a diagram": "Открыть диаграмму",
    "Open a picture from the clipboard": "Открыть картинку из буфера обмена",
    "Copy a Ligature picture first (e.g. from a note), then try again.":
        "Сначала скопируйте картинку из Ligature (например, из заметки), затем попробуйте снова.",
    "Diagrams": "Диаграммы",
    "All files": "Все файлы",
    "Ligature diagram": "Диаграмма Ligature",
    "Editable PNG picture": "Редактируемая картинка PNG",
    "Editable SVG picture": "Редактируемая картинка SVG",
    "Export": "Экспорт",
    "PNG picture (editable)…": "Картинка PNG (редактируемая)…",
    "SVG picture (editable)…": "Картинка SVG (редактируемая)…",
    "PDF…": "PDF…",
    "PNG picture": "Картинка PNG",
    "SVG picture": "Картинка SVG",
    "PDF document": "Документ PDF",
    "Export as PNG…": "Экспорт в PNG…",
    "Export as SVG…": "Экспорт в SVG…",
    "Export as PDF…": "Экспорт в PDF…",
    "Copy as picture": "Копировать как картинку",
    "Copy as picture (paste it into notes)": "Копировать как картинку (вставьте её в заметки)",
    "Exported pictures are always drawn on white.":
        "Экспортированные картинки всегда рисуются на белом фоне.",

    # ---- tools
    "Select and move": "Выбрать и двигать",
    "Entity": "Сущность",
    "Relationship": "Связь",
    "Class": "Класс",
    "Link": "Связь",
    "Click where the entity goes.": "Щёлкните там, где будет сущность.",
    "Click where the class goes.": "Щёлкните там, где будет класс.",
    "Click the first entity.": "Щёлкните первую сущность.",
    "Click the first class.": "Щёлкните первый класс.",
    "Now click the second entity (the same one again for a recursive relationship). Esc cancels.":
        "Теперь щёлкните вторую сущность (ту же ещё раз для рекурсивной связи). Esc — отмена.",
    "Now click the parent class or interface. Esc cancels.":
        "Теперь щёлкните родительский класс или интерфейс. Esc — отмена.",
    "Now click the second class. Esc cancels.": "Теперь щёлкните второй класс. Esc — отмена.",
    "Undo (Ctrl+Z)": "Отменить (Ctrl+Z)",
    "Redo (Ctrl+Shift+Z)": "Повторить (Ctrl+Shift+Z)",
    "Zoom out (Ctrl+-)": "Уменьшить (Ctrl+-)",
    "Zoom in (Ctrl+=, or Ctrl+scroll)": "Увеличить (Ctrl+= или Ctrl+колесо)",
    "Fit the diagram (Ctrl+0)": "Вписать диаграмму (Ctrl+0)",
    "Fit the diagram": "Вписать диаграмму",
    "Add an entity here": "Добавить сущность здесь",
    "Add a class here": "Добавить класс здесь",
    "Duplicate": "Дублировать",
    "Delete": "Удалить",
    "{count} selected": "Выбрано: {count}",

    # ---- the panel
    "Title": "Название",
    "Notation": "Нотация",
    "Chen": "Чен",
    "Crow's foot": "«Воронья лапка»",
    "Double-click empty space to add an entity. To join entities, pick Relationship in the toolbar and click one entity, then the other (the same one twice for a recursive relationship). Drag to move; Delete removes.":
        "Дважды щёлкните по пустому месту, чтобы добавить сущность. Чтобы связать сущности, "
        "выберите «Связь» на панели и щёлкните одну сущность, затем другую (ту же дважды — для "
        "рекурсивной связи). Перетаскивайте, чтобы двигать; Delete удаляет.",
    "Double-click empty space to add a class. To link classes, pick a link type in the toolbar and click one class, then the other: for inheritance, click the child first, then the parent.":
        "Дважды щёлкните по пустому месту, чтобы добавить класс. Чтобы связать классы, выберите "
        "тип связи на панели и щёлкните один класс, затем другой: для наследования — сначала "
        "потомка, затем родителя.",
    "Entity name": "Имя сущности",
    "Weak entity (identified through a relationship)":
        "Слабая сущность (определяется через связь)",
    "Attributes": "Атрибуты",
    "No attributes yet.": "Атрибутов пока нет.",
    "Add attribute": "Добавить атрибут",
    "name": "имя",
    "Column type in SQL": "Тип столбца в SQL",
    "Part of the key (identifier)": "Часть ключа (идентификатора)",
    "Optional: may be left empty": "Необязательный: может быть пустым",
    "Remove attribute": "Удалить атрибут",
    "The key icon marks the identifier (the primary key). “0,1” marks an optional attribute.":
        "Значок ключа отмечает идентификатор (первичный ключ). «0,1» — необязательный атрибут.",
    "Relationship name": "Имя связи",
    "Entities": "Сущности",
    "Add an entity": "Добавить сущность",
    "For relationships between three or more entities": "Для связей трёх и более сущностей",
    "How many times this entity takes part: (min,max)":
        "Сколько раз сущность участвует в связи: (min,max)",
    "role": "роль",
    "Remove this entity from the relationship": "Убрать эту сущность из связи",
    "(min,max) is how many times each entity takes part: (1,1) exactly once, (0,N) any number of times. A role tells the two sides of a recursive relationship apart.":
        "(min,max) — сколько раз каждая сущность участвует в связи: (1,1) ровно один раз, "
        "(0,N) — сколько угодно. Роль различает две стороны рекурсивной связи.",
    "Class name": "Имя класса",
    "Abstract class": "Абстрактный класс",
    "Interface": "Интерфейс",
    "Enumeration": "Перечисление",
    "Operations": "Операции",
    "- nome: String\n- eta: int": "- имя: String\n- возраст: int",
    "+ getNome(): String": "+ getИмя(): String",
    "One per line. Start with + public, - private, # protected or ~ package; write “static” or “abstract” before the name to underline it or put it in italics.":
        "По одному в строке. Начните с + public, - private, # protected или ~ package; "
        "напишите «static» или «abstract» перед именем, чтобы подчеркнуть его или выделить "
        "курсивом.",
    "Type": "Тип",
    "Association": "Ассоциация",
    "Directed association": "Направленная ассоциация",
    "Aggregation": "Агрегация",
    "Composition": "Композиция",
    "Inheritance (generalisation)": "Наследование (обобщение)",
    "Realisation (implements)": "Реализация (implements)",
    "Dependency": "Зависимость",
    "Multiplicity at the start": "Кратность в начале",
    "Multiplicity at the end": "Кратность в конце",
    "Label": "Подпись",
    "e.g. contiene": "напр. содержит",
    "Reverse direction": "Развернуть",

    # ---- SQL
    "The tables your ER diagram becomes, ready to paste into a database.":
        "Таблицы, в которые превращается ваша ER-диаграмма, — готово для базы данных.",
    "Standard": "Стандартный",
    "Copy": "Копировать",
    "Save as .sql…": "Сохранить как .sql…",
    "Save the SQL": "Сохранить SQL",
    "SQL script": "Скрипт SQL",
    "Logical schema": "Логическая схема",
    "CREATE TABLE statements": "Команды CREATE TABLE",
    "Underlined: primary key. Italics with *: foreign key. ? may be empty.":
        "Подчёркнуто — первичный ключ. Курсив со * — внешний ключ. ? — может быть пустым.",
    "SQL comes from ER diagrams. Open or start an ER diagram to see its tables here.":
        "SQL строится по ER-диаграммам. Откройте или создайте ER-диаграмму, чтобы увидеть "
        "её таблицы.",
    "No entities yet.": "Сущностей пока нет.",
    "“{subject}” has no key, so an “id” column was added. Mark its identifier with the key icon.":
        "У «{subject}» нет ключа, поэтому добавлен столбец «id». Отметьте идентификатор "
        "значком ключа.",
    "“{subject}” is weak but no relationship identifies it: give it a (1,1) relationship to its owner.":
        "«{subject}» — слабая сущность, но её не определяет ни одна связь: добавьте связь (1,1) "
        "с владельцем.",
    "“{subject}” is identified through a circle of weak entities.":
        "«{subject}» определяется через замкнутый круг слабых сущностей.",
    "“{subject}” joins fewer than two entities, so it was left out.":
        "«{subject}» связывает меньше двух сущностей, поэтому пропущена.",
    "Two tables are called “{subject}”; one was renamed.":
        "Две таблицы называются «{subject}»; одна переименована.",
    "“{subject}” appears twice; the second was left out.":
        "«{subject}» встречается дважды; второй пропущен.",

    # ---- settings, help, about
    "Settings": "Настройки",
    "Settings…": "Настройки…",
    "Appearance": "Оформление",
    "System": "Как в системе",
    "Light": "Светлое",
    "Dark": "Тёмное",
    "Language": "Язык",
    "Interface language": "Язык интерфейса",
    "Restart Ligature now": "Перезапустить Ligature",
    "Close": "Закрыть",
    "Keyboard shortcuts": "Сочетания клавиш",
    "New ER / UML diagram": "Новая диаграмма ER / UML",
    "Open, save, save as": "Открыть, сохранить, сохранить как",
    "Tools: select, entity, relationship, generalisation, class, link":
        "Инструменты: выбор, сущность, связь, обобщение, класс, связь UML",
    "Copy, cut, paste (also into another diagram)": "Копировать, вырезать, вставить (и в другую диаграмму)",
    "Arrow keys": "Стрелки",
    "Move the selection (with Shift, further)": "Сдвинуть выбранное (с Shift — дальше)",
    "Tools: select, entity, relationship, class, link":
        "Инструменты: выбор, сущность, связь, класс, связь UML",
    "Double-click": "Двойной щелчок",
    "Add an entity or class, or edit the one clicked":
        "Добавить сущность или класс либо изменить тот, по которому щёлкнули",
    "Delete the selection": "Удалить выбранное",
    "Undo / redo": "Отменить / повторить",
    "Cancel the tool": "Отменить инструмент",
    "Space + drag, middle button": "Пробел + перетаскивание, средняя кнопка",
    "Move around": "Перемещаться",
    "Zoom": "Масштаб",
    "Export as PNG, PDF": "Экспорт в PNG, PDF",
    "About Ligature": "О Ligature",
    "Quit Ligature": "Выйти из Ligature",
    "Free software under the GNU General Public License, version 3 or later.":
        "Свободная программа под лицензией GNU GPL версии 3 или новее.",

    # ---- errors
    "Choose where to save the diagram.": "Выберите, куда сохранить диаграмму.",
    "That entity no longer exists.": "Этой сущности больше нет.",
    "That item is no longer in the diagram.": "Этого элемента больше нет в диаграмме.",
    "That file doesn't exist any more.": "Этого файла больше нет.",
    "Couldn't read the file.": "Не удалось прочитать файл.",
    "Couldn't save the file there.": "Не удалось сохранить файл туда.",
    "This picture has no Ligature diagram inside it.": "В этой картинке нет диаграммы Ligature.",
    "This isn't a Ligature diagram, or it's damaged.":
        "Это не диаграмма Ligature, или файл повреждён.",
    "This diagram was made with a newer Ligature. Update Ligature to open it.":
        "Эта диаграмма создана в более новой Ligature. Обновите Ligature, чтобы открыть её.",
    "not a Ligature file": "это не файл Ligature",
    "not a PNG": "это не PNG",
    "not an SVG": "это не SVG",
    "a picture is needed to save as PNG or SVG": "для PNG или SVG нужна картинка",

    # ---- generalisations, clipboard, warnings
    "Generalisation": "Обобщение",
    "Specialisations": "Специализации",
    "Specialisations of {parent}": "Специализации сущности {parent}",
    "No longer a specialisation": "Больше не специализация",
    "Total": "Полное",
    "Partial": "Частичное",
    "Exclusive": "Исключающее",
    "Overlapping": "Перекрывающееся",
    "As tables": "В таблицах",
    "A table for each (children use the parent's key)":
        "Таблица для каждой (потомки берут ключ родителя)",
    "One table: children merged into the parent": "Одна таблица: потомки слиты в родителя",
    "A table per child: parent merged into them": "Таблица на потомка: родитель слит в них",
    "Total (t): every parent is also one of the children; partial (p): not necessarily. Exclusive (e): at most one child; overlapping (s): maybe several. To add a child, pick Generalisation in the toolbar and click the child, then the parent.":
        "Полное (t): каждый родитель — также один из потомков; частичное (p): не обязательно. "
        "Исключающее (e): не больше одного потомка; перекрывающееся (s): возможно несколько. "
        "Чтобы добавить потомка, выберите «Обобщение» на панели и щёлкните потомка, затем "
        "родителя.",
    "Merging into the children needs a total generalisation whose parent takes part in no relationship.":
        "Слияние в потомков требует полного обобщения, родитель которого не участвует ни в одной "
        "связи.",
    "Click the specialised entity (the child).": "Щёлкните специализированную сущность (потомка).",
    "Now click the parent entity. Esc cancels.": "Теперь щёлкните родительскую сущность. Esc — отмена.",
    "No key: mark its identifier with the key icon.":
        "Нет ключа: отметьте идентификатор значком ключа.",
    "University, with a generalisation (ER)": "Университет, с обобщением (ER)",
    "Cut": "Вырезать",
    "Paste": "Вставить",
    "An entity can't be a specialisation of itself.":
        "Сущность не может быть специализацией самой себя.",
    "That would make a circle of specialisations.": "Получился бы круг специализаций.",
    "Those items belong in a different kind of diagram.":
        "Эти элементы относятся к диаграмме другого вида.",
    "“{subject}”'s generalisation is partial, so it can't be merged into its children: it keeps separate tables.":
        "Обобщение «{subject}» частичное, поэтому его нельзя слить в потомков: таблицы остаются "
        "отдельными.",
    "“{subject}” takes part in relationships, so its generalisation can't be merged into its children: it keeps separate tables.":
        "«{subject}» участвует в связях, поэтому его обобщение нельзя слить в потомков: таблицы "
        "остаются отдельными.",

    # ---- updates
    "Can't reach GitHub to check for updates. Check your internet connection.": 'GitHub недоступен для проверки обновлений. Проверьте подключение к интернету.',
    'Check for updates…': 'Проверить обновления…',
    'Check now': 'Проверить сейчас',
    "Couldn't check for updates": 'Не удалось проверить обновления',
    "Couldn't start the installer.": 'Не удалось запустить установщик.',
    'Downloading…': 'Загрузка…',
    'Downloading… {done} of {total} MB': 'Загрузка… {done} из {total} МБ',
    'GitHub is limiting update checks right now: try again in an hour.': 'GitHub сейчас ограничивает проверки обновлений: попробуйте через час.',
    "GitHub sent an answer Ligature doesn't understand.": 'GitHub прислал ответ, который Ligature не понимает.',
    'Installing was cancelled.': 'Установка отменена.',
    'Installing… your system may ask for your password.': 'Установка… система может спросить пароль.',
    'Later': 'Позже',
    'Ligature {version} is available': 'Доступна версия Ligature {version}',
    'No release notes.': 'Описания выпуска нет.',
    'No updates': 'Обновлений нет',
    'Open download page': 'Открыть страницу загрузки',
    'Skip this version': 'Пропустить эту версию',
    'Something went wrong: {error}': 'Что-то пошло не так: {error}',
    "The download didn't finish. Check your internet connection and try again.": 'Загрузка не завершилась. Проверьте подключение к интернету и попробуйте снова.',
    "The download was damaged (its checksum doesn't match), so it wasn't installed. Try again.": 'Загруженный файл повреждён (контрольная сумма не совпадает), поэтому он не установлен. Попробуйте снова.',
    "There's no download for this computer in that release.": 'В этом выпуске нет файла для этого компьютера.',
    "This copy of Ligature can't update itself (for example when it runs from source). Download the new version from GitHub.": 'Эта копия Ligature не может обновиться сама (например, при запуске из исходников). Скачайте новую версию с GitHub.',
    "This copy of Ligature can't update itself.": 'Эта копия Ligature не может обновиться сама.',
    'Update available': 'Доступно обновление',
    'Update now': 'Обновить сейчас',
    'Updates': 'Обновления',
    'You have the latest version of Ligature ({version}).': 'У вас последняя версия Ligature ({version}).',
    "You have {version}. Here's what's new:": 'У вас версия {version}. Что нового:',
    'Check for new versions once a day': 'Проверять новые версии раз в день',
    'You have version {version}.': 'У вас версия {version}.',
}
