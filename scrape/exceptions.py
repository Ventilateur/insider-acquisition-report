class MissingDataException(Exception):
    def __init__(self, field_name):
        self.field_name = field_name


class UnneededDataException(Exception):
    def __init__(self, msg):
        self.msg = msg


class CannotFetchDataException(Exception):
    def __init__(self, url):
        self.url = url
