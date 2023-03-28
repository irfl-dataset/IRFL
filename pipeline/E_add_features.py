import sys
from datetime import datetime

from assets.config import D_final_search_result_path, E_filter_results_folder_path, E_filter_results_path
from assets.constants import image_formats
from pipeline.utils.filter_utils import enchant_idiom_ViLT_features
from pipeline.utils.utils import get_json, dump_json

sys.path.append(r'C:\devel\IRLM')  # project path for parallel run

##########################################
FILL_EMPTY_QUERIES_MODE = False
OVERRIDE_MODE = False  # When False it will not add features to image with existing features

class E_add_features:

    def add_features(self):
        self.output_path = E_filter_results_folder_path
        # If FILL_EMPTY_QUERIES_MODE it will start where it stopped
        if FILL_EMPTY_QUERIES_MODE:
            print('FILL_AGGREGATED_QUERIES_MODE')
            self.output_path = E_filter_results_path
            self.figurative_phrases = get_json(self.output_path)
        else:
            self.figurative_phrases = get_json(D_final_search_result_path)
        self.image_formats = image_formats
        self.iterate_over_figurative_phrases()

    def iterate_over_figurative_phrases(self):
        counter = 0
        for figurative_phrase in self.figurative_phrases:
            print('[E_add_ViLT_OCR_features:{}]: Start feature enchantment on idiom: {}'.format(datetime.now(), figurative_phrase['prompt']))
            for query in figurative_phrase['search_query']:
                enchant_idiom_ViLT_features(query, figurative_phrase['prompt'], query['query'], OVERRIDE_MODE)
                self.enchant_is_query_literal(query, figurative_phrase)
            print('[E_add_ViLT_OCR_features:{}]: Finished feature enchantment on idiom: {}'.format(datetime.now(), figurative_phrase['prompt']))
            counter += 1
            if counter % 5 == 0:  # print every 5 items (it takes time...)
                print(counter)
            if counter % 10 == 0:  # save every 5 items (it takes time...)
                print(counter)
                dump_json(self.output_path, self.figurative_phrases)
        dump_json(self.output_path, self.figurative_phrases)

    def enchant_is_query_literal(self, query, figurative_phrase):
        literal_query = False
        if query.get('literal') is True:
            return True

        query_definition = next(filter(lambda definition: definition.get('definition').lower() == query['query'].lower(), figurative_phrase.get('definition')))
        if query.get('query') == figurative_phrase['prompt'] or 'literally' in query_definition['context'].lower():
            query.update({'literal': True})
            literal_query = True

        return literal_query

E_add_features().add_features()

