from bs4 import BeautifulSoup, SoupStrainer
from Deck import Deck
import json
import requests
import concurrent.futures
import time
import os
import zipfile


with open('config.json', 'r') as config_file:
    CONFIG_DATA = json.load(config_file)


def get_deck(deck_data: dict, req: requests) -> Deck:
    """
    It get the cards and amount of copies for a given deck link.
    :param deck_data: a dict that has the deck name and deck link
    :param req: a request session, to prevent the time consumption of creating new ones everytime.
    :return: a Deck Object with the scrap data ready to use.
    """
    deck = Deck(deck_data['deck_name'])
    enable_sideboard = False
    with req.get(CONFIG_DATA['mtggolfish_url'] + deck_data['link']) as url:
        constrain = SoupStrainer('div', {'class': 'deck-table-container'})
        try:
            if not url.ok:
                url.raise_for_status()
            soup = BeautifulSoup(url.text, features='lxml', parse_only=constrain).find('table').findAll('tr')
            for elem in soup:
                if elem.has_attr('class'):
                    if 'sideboard' in elem.th.getText().lower():
                        enable_sideboard = True
                else:
                    elem_cant = int(elem.find(class_='text-right').getText())
                    elem_name = elem.find('a').getText()
                    deck.add_card(elem_name, elem_cant, enable_sideboard)
        except (AttributeError, requests.exceptions.HTTPError):
            deck = Deck('Error')
    return deck


def get_decks_url(format_name: str, req: requests.Session) -> list:
    """
    It gets the links for the meta decks of a given format.
    :param format_name: an string with the name of format to scrap
    :param req: a request session, to prevent the time consumption of creating new ones everytime.
    :return: a list of dicts with the deck_name and the link as keys
    """
    decks_url = []
    url = f'{CONFIG_DATA["mtggolfish_url"]}/metagame/{format_name}/#paper'
    try:
        with req.get(url) as page:
            if not page.ok:
                page.raise_for_status()
            constrain = SoupStrainer('div', {'class': 'archetype-tile-container', 'id': 'metagame-decks-container'})
            soup = BeautifulSoup(page.text, features='lxml', parse_only=constrain)\
                .findAll('div', class_='archetype-tile')
        for elem in soup:
            partial_res = elem.find('span', class_='deck-price-paper').a
            decks_url.append({'deck_name': partial_res.getText(), 'link': partial_res.get('href')})
    except requests.exceptions.HTTPError:
        decks_url = []
    return decks_url


def tutor(working_format: tuple) -> None:
    """
    Each process has a request session, speeding up the scrap process for a given format.
    First it get the decks url and name, then for each one gets the cards and amount of copies.
    The deck list, has an Object call Deck to organize the data.
    :param working_format: its a tuple in the form of (format_name: str, decks: lst)
    :return: None, the tuple is a reference so its use as a param and a way to return the values.
    """
    with requests.session() as req:
        decks_url = get_decks_url(working_format[0], req)
        for deck in decks_url:
            working_format[1].append(get_deck(deck, req))
            time.sleep(0.3)


def create_deck_file(working_format: tuple) -> None:
    """
    It will check if the path to save the decks exists, if it does it will remove all file ended in .cod.
    If the path does not exist, its created.
    Then each deck is writen to a file
    :param working_format: its a tuple in the form of (format_name: str, decks: lst)
    :return:None, the dir and files are created as output
    """
    complete_path = os.path.join(CONFIG_DATA['path_to_use'], working_format[0])
    if not os.path.exists(complete_path):
        os.makedirs(complete_path)
    else:
        for file in os.scandir(complete_path):
            if file.is_file() and file.name.endswith(".cod"):
                os.remove(file.path)
    check_duplicate = {}
    for deck in working_format[1]:
        if deck.name in check_duplicate:
            check_duplicate[deck.name] += 1
            deck_path = os.path.join(complete_path, f'{deck.name}-{check_duplicate[deck.name]}.cod')
        else:
            check_duplicate[deck.name] = 0
            deck_path = os.path.join(complete_path, f'{deck.name}.cod')
        with open(deck_path, 'w') as writer:
            writer.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            writer.write('<cockatrice_deck version="1">\n')
            writer.write(f'\t<deckname>{deck.name}</deckname>\n')
            writer.write('\t<comments></comments>\n')
            writer.write('\t<zone name=\"main\">\n')
            for card in deck.main:
                writer.write(f'\t\t<card number="{card[1]}" name="{card[0]}"/>\n')
            writer.write('\t</zone>\n')
            writer.write('\t<zone name="side">\n')
            for card in deck.sideboard:
                writer.write(f'\t\t<card number="{card[1]}" name="{card[0]}"/>\n')
            writer.write('\t</zone>\n')
            writer.write('</cockatrice_deck>\n')


def create_zip_file() -> None:
    """
    It create a zip file with the scrap data, copying the dir structure
    :return: None, a zip file is created as result
    """
    selected_formats = [k for k, v in CONFIG_DATA['formats'].items() if v]
    with zipfile.ZipFile(os.path.join(CONFIG_DATA['path_to_use'], "Decks.zip"), mode="w") as archive:
        for file in os.scandir(CONFIG_DATA['path_to_use']):
            if file.is_dir() and file.name in selected_formats:
                for sub_file in os.scandir(file.path):
                    temp_path = sub_file.path.replace(os.path.join(CONFIG_DATA['path_to_use'], ''), '')
                    archive.write(sub_file.path, arcname=temp_path)


def app():
    """
    Each format is scrap in parallel, set "cant_process" to match your cpu.
    res is a list of tuples (format_name: str, list of Decks: lst[Decks]), in this way each process has one tuple
    to work with.
    """
    global CONFIG_DATA
    if CONFIG_DATA['path_to_save']:
        CONFIG_DATA['path_to_use'] = CONFIG_DATA['path_to_save']
    else:
        CONFIG_DATA['path_to_use'] = os.path.join(os.path.expanduser('~'), 'Decks')
    res = []
    for fname in (k for k, v in CONFIG_DATA['formats'].items() if v):
        res.append((f'{fname}', []))
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONFIG_DATA['cant_process']) as executor:
        executor.map(tutor, res)
    for mtg_format in res:
        create_deck_file(mtg_format)
    if CONFIG_DATA['create_zip']:
        create_zip_file()


if __name__ == '__main__':
    app()
