class ParamCache(dict):
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def get(self, k):
        return self.__getitem__(k)

    def set(self, n, v):
        return self.__setitem__(n, v)
