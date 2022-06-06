class Deck:
    def __init__(self, name):
        """
        An Deck Object:
            name: is the deck name.
            main: is a list of tuple, card_name - amount of copies, of the main deck
            sideboard: is also a list of tuple, card_name - amount of copies
        :param name: name of the deck
        """
        self.name = name
        self.main = []
        self.sideboard = []

    def add_card(self, name, quantity, enable_sideboard):
        if enable_sideboard:
            self.sideboard.append((name, quantity))
        else:
            self.main.append((name, quantity))

    def __str__(self):
        res = f"{self.name}"
        res += f"\nMain:\n"
        for x in self.main:
            res += f"\t{x}\n"
        res += f"Side:\n"
        for x in self.sideboard:
            res += f"\t{x}\n"
        return res
