from assets.config import B_search_queries_path, MAGPIE_dataset
from pipeline.MAGPIE_dataset_generation import MAGPIE_dataset_generation
from pipeline.utils.utils import get_json, dump_json


class B_search_queries:

    def __init__(self):
        self.MAGPIE_dataset_generation = MAGPIE_dataset_generation()
        figurative_phrases = []
        figurative_phrases.extend(self.get_IRLM_MAGPIE_idioms())
        dump_json(B_search_queries_path, figurative_phrases)
        print('[B_search_queries]: Initialized')

    def get_IRLM_MAGPIE_idioms(self):
        MAGPIE = get_json(MAGPIE_dataset)
        ids = list(MAGPIE)
        MAGPIE_idioms = []
        for id in ids[:50]:
            MAGPIE_idioms.append(self.MAGPIE_dataset_generation.get_IRLM_format(MAGPIE[id]))
        print('[B_search_queries]: MAGPIE Initialized')
        return MAGPIE_idioms


B_search_queries()
