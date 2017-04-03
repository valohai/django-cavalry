import re

ELIDED_FILENAMES = [
    'socketserver.py',
    'threading.py',

    # Middleware-related stack frames
    'django/utils/deprecation.py',
    'django/core/handlers/exception.py',
]


class Stack(object):  # Wrapped as an object for easier serialization
    def __init__(self, frames):
        self.frames = frames

    def as_lines(self):
        stack_lines = []
        for filename, lineno, fn, text in self.frames:
            if any(filename.endswith(elided_end) for elided_end in ELIDED_FILENAMES):
                continue
            filename = re.sub('^.+site-packages/', '~/', filename)
            filename = re.sub('^.+lib/python\d\.\d/', '!/', filename)
            stack_lines.append('{filename}:{lineno} ({fn}) {text}'.format(
                filename=filename,
                lineno=lineno,
                fn=fn,
                text=text,
            ))
        return stack_lines
