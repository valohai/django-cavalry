import re
from traceback import FrameSummary
from typing import List

ELIDED_FILENAMES = [
    'socketserver.py',
    'threading.py',
    # Middleware-related stack frames
    'django/utils/deprecation.py',
    'django/core/handlers/exception.py',
]


class Stack:  # Wrapped as an object for easier serialization
    def __init__(self, frames: List[FrameSummary]) -> None:
        self.frames = frames

    def as_lines(self) -> List[str]:
        stack_lines = []
        for filename, lineno, fn, text in self.frames:
            if any(filename.endswith(elided_end) for elided_end in ELIDED_FILENAMES):
                continue
            filename = re.sub(r'^.+site-packages/', '~/', filename)
            filename = re.sub(r'^.+lib/python\d\.\d/', '!/', filename)
            stack_lines.append(f'{filename}:{lineno} ({fn}) {text}')
        return stack_lines
