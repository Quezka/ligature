import itertools

import pytest

from ligature.application.editor import Editor
from ligature.infrastructure.files import JsonDiagramFiles


@pytest.fixture
def editor():
    counter = itertools.count(1)
    return Editor(JsonDiagramFiles(), new_id=lambda: f"id{next(counter)}")
