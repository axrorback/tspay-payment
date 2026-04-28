class Money:
    @staticmethod
    def to_tiyin(som):
        return int(som * 100)

    @staticmethod
    def to_som(tiyin):
        return int(tiyin / 100)