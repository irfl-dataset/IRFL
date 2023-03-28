import json

from assets.config import E_filter_results_path, F_filter_results_path
from assets.constants import images_blacklist, valid_idiom_definition_source_context_score_threshold, idioms_blacklist
from pipeline.utils.OCR_utils import is_image_text_not_similar
from pipeline.utils.filter_utils import get_top_images, get_idiom_literal_photos, filter_forbidden_websites_images
from pipeline.utils.utils import get_json, dump_json


class F_choose_best_images:

    def choose_best_images(self, figurative_phrases=None, output_path=F_filter_results_path):
        if figurative_phrases is None:
            figurative_phrases = get_json(E_filter_results_path)

        for figurative_phrase in figurative_phrases:
            prompt = figurative_phrase.get('prompt').lower()
            if prompt in idioms_blacklist:
                print('Skipping {} - blacklisted'.format(prompt))
                continue

            queries = self.filter_idioms_by_definition_context(figurative_phrase['search_query'],
                                                               figurative_phrase)  # filter-in only idiomatic, figurative, non-context and the idiom it self
            for query in queries:
                literal_query = query.get('literal')
                valid_images = list(filter(lambda image: self.is_image_valid(image, figurative_phrase), query['search_results']))
                if len(valid_images) == 0:
                    continue
                if literal_query:
                    self.rank_images(figurative_phrase, query, valid_images, True)
                else:
                    literal_images = get_idiom_literal_photos(valid_images)
                    self.rank_images(figurative_phrase, query, literal_images, True)

        if output_path is not None:
            dump_json(output_path, figurative_phrases)
        return figurative_phrases

    def filter_idioms_by_definition_context(self, queries, figurative_phrase):
        return filter(lambda query: query['source_context_score'] >= valid_idiom_definition_source_context_score_threshold or
                                    query['query'].lower() == figurative_phrase['prompt'], queries)

    def rank_images(self, phrase, query, images, literal=False):
        ranked_images = get_top_images(images, len(images), 'idiom_ViLT_score' if literal else 'query_ViLT_score')
        ranked_images = list(filter(lambda ranked_image: ranked_image.get('name') not in images_blacklist, ranked_images))
        highest_rank = 0
        for count, image in enumerate(ranked_images):
            image.update({'rank': count + 1})
            if literal is True:
                image.update({'literal': True})
            highest_rank = count + 1
        return highest_rank

    def is_image_valid(self, image, phrase):
        return image.get('filter_ocr') is True and not self.is_image_document(image) and filter_forbidden_websites_images(image) \
               and image.get('is_white') is False and self.is_image_metadata_filters_valid(image) and self.is_image_text_not_in_queries(phrase, image)

    def is_image_metadata_filters_valid(self, image):
        image_filters_metadata = json.loads(image.get('filters_metadata'))
        return image_filters_metadata.get('is_text_not_similar_to_phrase') is True and image_filters_metadata.get('is_text_not_similar_to_query') is True \
               and image_filters_metadata.get('is_corrected_text_not_similar_to_query') is True and image_filters_metadata.get('is_corrected_text_not_similar_to_phrase') is True

    def is_image_text_not_in_queries(self, phrase, image):
        image_text = image.get('OCR_metadata').get('text').lower()
        corrected_text = image.get('OCR_metadata').get('corrected_text').lower()
        queries_text = list(map(lambda query: query['query'].lower(), phrase['search_query']))
        for query_text in queries_text:
            if not is_image_text_not_similar(image_text, query_text)[0] or not is_image_text_not_similar(corrected_text, query_text)[0]:
                return False
        return True

    def is_image_document(self, image):
        return image.get('is_document')

F_choose_best_images().choose_best_images()
