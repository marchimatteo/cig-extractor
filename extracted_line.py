# Basically a dict, but if it finds a key is already present it adds a '_n' at the end of it
class ExtractedLine:
    def __init__(self, given_id: str) -> None:
        self._internal_dict = {}
        # Used to identify this specific line in all jsons
        self.id = given_id

    def add(self, key, value) -> None:
        counter = 1
        internal_key = key
        while True:
            if counter > 1:
                internal_key = internal_key + '_' + str(counter)
            if internal_key not in self._internal_dict:
                self._internal_dict[key] = value
                break
            counter += 1

    def get(self) -> dict:
        return self._internal_dict

    def has(self, key, value: list[str]) -> bool:
        return key in self._internal_dict and self._internal_dict[key] in value
    