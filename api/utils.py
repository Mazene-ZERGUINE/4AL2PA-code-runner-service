from enum import Enum


class ProgramingLanguagesEnum(Enum):
    JAVASCRIPT = 'javascript'
    PYTHON = 'python'
    PHP = 'php'
    CPP = 'c++'


class ProgramResultDto:
    def __init__(self, stdout, stderr, returncode):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode

    def to_dict(self):
        return {
            'stdout': self.stdout,
            'stderr': self.stderr,
            'returncode': self.returncode
        }