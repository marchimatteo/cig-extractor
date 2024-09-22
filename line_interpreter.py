from datetime import datetime


class LineInterpreter:
    def __init__(self) -> None:
        True


    def is_date(self, value) -> bool:
        return isinstance(value, str) and \
            len(value) == 10 and \
            value[0:4].isnumeric() and \
            value[4:5] == '-' and \
            value[5:7].isnumeric() and \
            value[7:8] == '-' and \
            value[8:10].isnumeric()

    def get_date(self, value: str) -> datetime:
        return datetime.strptime(value, '%Y-%m-%d')
