class Memo():
    def __init__(self, index, is_module=False):
        self.index = index
        # self.is_module = is_module


class MemoManager:
    def __init__(self):
        self.name_to_memo = {}
        self.current_index = 0

    def contains(self, name) -> bool:
        return name in self.name_to_memo

    def get_memo(self, name, is_module=False) -> Memo:
        if name in self.name_to_memo:
            return self.name_to_memo[name]

        self.name_to_memo[name] = Memo(self.current_index, is_module)
        # if not is_module:
        self.current_index += 1
        return self.name_to_memo[name]

