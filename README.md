# DeckTutor
A command line script to scrap MTGGolfish.com for the Meta Decks of different formats of Magic: The Gathering. The deck data is put in a .cod file with the deck title as name, in a folder of the corresponding format.

You must set config.json in order to work. In case of doubt, set 'cant_process' = 2.

Warning the .cod files are deleted on every run, so check the 'path_to_save' variable.

Consider 'path_to_save' = /home/deck

Then every .cod file in /home/deck/standard will be deleted, and so with the formats specified in config.json.

