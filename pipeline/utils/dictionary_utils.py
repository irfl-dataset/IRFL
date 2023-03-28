import requests
import spacy  # run python -m spacy download en_core_web_lg
from bs4 import BeautifulSoup

nlp = spacy.load("en_core_web_lg")

query_url = 'https://en.wiktionary.org/w/index.php?title=$idiom&printable=yes'
oxford_spellcheck_query = 'https://www.oxfordlearnersdictionaries.com/spellcheck/english/?q=$idiom'
oxford_search_query = 'https://www.oxfordlearnersdictionaries.com/search/english/?q=$idiom'

def get_wiktionary_definition(idiom, alternative_chain=[]):  # alternative_chain is to prevent infinite loop of Alternative form of * scenario
    idiom = idiom.lower()

    response = requests.get(query_url.replace('$idiom', idiom))
    if response.status_code != 200:
        print(idiom)
        return get_oxford_definition(idiom)

    if 'Wiktionary does not yet have an entry for ' + idiom in response.text:
        print('Idiom: ' + idiom + ' was not found')
        return get_oxford_definition(idiom)

    bs = BeautifulSoup(response.text, 'html.parser')

    if len(bs.findAll('ol')) != 1:
        print('More than one ol idiom: ' + idiom)

    definitions = []
    definitions_list = bs.findAll('ol')
    for definitions_element in definitions_list:

        ol_classes = definitions_element.attrs.get('class')
        if ol_classes is not None and 'references' in ol_classes:
            continue

        definitions_element = list(definitions_element.children)
        for definition_element in definitions_element:
            if 'Alternative form of' in definition_element.text or 'Alternative spelling of' in definition_element.text:
                alternative_idiom = definition_element.find('span', class_='form-of-definition').find('a').text
                if alternative_idiom not in alternative_chain:
                    alternative_chain.append(alternative_idiom)
                    definitions.extend(get_wiktionary_definition(definition_element.find('span', class_='form-of-definition').find('a').text, alternative_chain))
                    print('Check alternative of ' + idiom)
                continue

            definition_text = definition_element.text.split('\n')[0].split('.')[0]
            split = definition_text.split(')')
            context = ''

            if len(split) > 1:
                definition_text = definition_text[definition_text.index(')') + 2:]
                context = split[0][split[0].index('(') + 1:]

            filtered_definitions = filter(lambda x: x is not None and len(x) > 0, definition_text.split(';'))
            definitions.extend(map(lambda text: {'definition': ' '.join(text.split()), 'context': context}, filtered_definitions))

    if len(definitions) == 0:
        print(idiom)
        return get_oxford_definition(idiom)
    definitions = list(filter(lambda definition: not definition['definition'].lower().startswith('used other than figuratively'), definitions))
    return definitions


def get_oxford_definition(idiom):
    try:
        direct_result = get_oxford_idiom_definition_by_search_url(oxford_search_query.replace('$idiom', idiom), [idiom], idiom)
        if direct_result[0].get('definition') != idiom:
            return direct_result

        response = requests.get(oxford_spellcheck_query.replace('$idiom', idiom), headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code != 200:
            return [{'definition': idiom, 'context': ''}]

        bs = BeautifulSoup(response.text, 'html.parser')
        did_you_mean_options = bs.find('div', id='results-container-all').find('ul').findAll('li')
        for option in did_you_mean_options:

            option_text = option.text.replace('\n', '')
            definitions = split_by_slash(option_text)
            if idiom in definitions or if_array_contains_similar_sentence(idiom, definitions):
                return get_oxford_idiom_definition_by_search_url(option.find('a').attrs['href'], definitions, idiom)

        print('Oxford failed on idiom: ' + idiom)
        return [{'definition': idiom, 'context': ''}]
    except Exception as error:
        print('Oxford failed on idiom: ' + idiom)
        print(error)
        return [{'definition': idiom, 'context': ''}]


def split_by_slash(definition):
    split_text = remove_empty_space(definition).split('/')
    if len(split_text) > 1:
        first = remove_empty_space(split_text[0])
        second = remove_empty_space(split_text[1])

        first_definition = ' '.join(first.split(' ')[:-1]) + ' ' + second
        second_definition = first + ' ' + ' '.join(second.split(' ')[1:])
        return [first_definition, second_definition]
    return [split_text[0]]


def remove_empty_space(text):
    return ' '.join(filter(lambda word: len(word) > 0, text.split(' ')))


def get_oxford_idiom_definition_by_search_url(idiom_url, idiom_phrases, idiom):
    response = requests.get(idiom_url, headers={'User-Agent': 'Mozilla/5.0'})
    if response.status_code != 200:
        print('Oxford request error idiom: ' + idiom)
        return [{'definition': idiom, 'context': ''}]
    bs = BeautifulSoup(response.text, 'html.parser')
    idioms_container = bs.find('div', class_='idioms')

    if idioms_container is None:
        try:
            definitions = bs.find('span', class_='sensetop').find('span', class_='def').text.split(';')
            print('Oxford found definition for ' + idiom, 'definition: ' + str(definitions))
            return list(map(lambda definition: {'definition': definition, 'context': ''}, definitions))
        except:
            return [{'definition': idiom, 'context': ''}]

    definitions_element = idioms_container.findAll('span', class_='idm-g')
    for definition_element in definitions_element:
        for phrase in idiom_phrases:
            if phrase.lower() in definition_element.text.lower():
                definitions = idioms_container.find('span', class_='def').text.split(';')

                print('Oxford found definition for ' + idiom, 'definition: ' + str(definitions))
                return list(map(lambda definition: {'definition': definition, 'context': ''}, definitions))

    print('Oxford definition was not found: ' + idiom)
    return [{'definition': idiom, 'context': ''}]


def if_array_contains_similar_sentence(sentence, array):
    spicy_object = nlp(sentence)
    return True in map(lambda definition: spicy_object.similarity(nlp(definition)) > 0.98, array)
