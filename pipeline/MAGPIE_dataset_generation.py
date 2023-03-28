import json

from assets.config import MAGPIE_dataset, original_MAGPIE_dataset
from pipeline.utils.dictionary_utils import get_wiktionary_definition
from pipeline.utils.utils import dump_json


class MAGPIE_dataset_generation:

    def __init__(self):
        self.counter = 0

    def generate_MAGPIE_dataset(self):
        self.MAGPIE_idioms = self.read_MAGPIE_idioms()
        dump_json(MAGPIE_dataset, self.MAGPIE_idioms, None, False)
        print('[MAGPIE_dataset_generation]: generated ')
        return self.MAGPIE_idioms

    def read_MAGPIE_idioms(self):
        MAGPIE_idioms = dict()
        with open(original_MAGPIE_dataset, "r", encoding="utf-8") as f:
            for line in f:
                MAGPIE_idiom = self.remove_features(json.loads(line))
                idiomatic_sentences = MAGPIE_idioms.get(MAGPIE_idiom['idiom'])
                if idiomatic_sentences is None:
                    MAGPIE_idioms.update({MAGPIE_idiom['idiom']: [MAGPIE_idiom]})
                else:
                    idiomatic_sentences.append(MAGPIE_idiom)
        f.close()
        return MAGPIE_idioms

    def remove_features(self, idiom_sentence):
        idiom_sentence.pop('document_id', None)
        idiom_sentence.pop('offsets', None)
        idiom_sentence.pop('split', None)
        idiom_sentence.pop('sentence_no', None)
        idiom_sentence.pop('id', None)
        return idiom_sentence


    def get_IRLM_format(self, MAGPIE_idiom):
        self.counter += 1
        if self.counter % 50 == 0:
            print(self.counter)
        IRFL_IDIOM = dict()
        IRFL_IDIOM.update({'prompt': MAGPIE_idiom[0]['idiom'] })
        definitions = get_wiktionary_definition(MAGPIE_idiom[0]['idiom'])
        IRFL_IDIOM.update({'search_query': definitions})
        IRFL_IDIOM.update({'definition': definitions})
        IRFL_IDIOM.update({'definition_source': 'MAGPIE'})
        IRFL_IDIOM.update({'figurative_type': 'idiom'})
        return IRFL_IDIOM


    def get_C_search_query_format(self, MAGPIE_idiom):
        return MAGPIE_idiom
