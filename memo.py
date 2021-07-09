class Memo():
    def __init__(self, index, value=None):
        self.index = index
        self.value = value


class MemoManager:
    def __init__(self):
        self.name_to_memo = {}
        self.current_index = 0

    def contains(self, name) -> bool:
        return name in self.name_to_memo

    def get_memo(self, name) -> Memo:
        if name in self.name_to_memo:
            return self.name_to_memo[name]

        self.current_index += 1
        self.name_to_memo[name] = Memo(self.current_index)
        return self.name_to_memo[name]

    def set_memo(self, name, value):
        memo = get_memo(name)
        memo.value = value