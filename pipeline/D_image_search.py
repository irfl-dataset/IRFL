import sys

sys.path.append(r'C:\devel\IRLM-dataset')  # project path for parallel run

from pipeline.utils.image_search import ImageSearch

FILL_EMPTY_QUERIES_MODE = False
FILL_NEW_QUERIES_MODE = False  # When True, it will fill the new queries directly to aggregated file
######## Parallel running ##############

try:
    process_position = int(sys.argv[1])
    number_of_processes = int(sys.argv[2])

    if process_position not in range(1, 20) or number_of_processes not in range(1, 20):
        print('Process position or number of processes are not valid')
        raise Exception()
except:
    print('Failed to initialize parallel process, process will run all search queries')
    process_position = 1
    number_of_processes = 5


def get_process_piece(search_queries):
    search_queries = list(split(list(search_queries.items()), number_of_processes))
    return dict(search_queries[(process_position - 1)])


##########################################

from assets.config import D_search_result_folder_path, C_search_queries_path, C_search_queries_list_path, D_final_search_result_path, \
    D_aggregated_search_result_folder_path
from pipeline.utils.utils import get_json, dump_json, split


class D_Image_search:

    def search_images(self):
        image_search = ImageSearch()
        self.parallel = None not in [process_position, number_of_processes]
        if self.parallel:  # parallel
            print("Process number {} out of {}, started".format(process_position, number_of_processes))
            self.search_queries = get_process_piece(get_json(C_search_queries_list_path))
            self.output_file_path = D_search_result_folder_path.replace('.json', '-{}-{}.json'.format(process_position, number_of_processes))
        else:  # Not parallel
            self.output_file_path = D_search_result_folder_path
            self.search_queries = get_json(C_search_queries_list_path)

        if FILL_EMPTY_QUERIES_MODE:
            self.search_queries = get_json(self.output_file_path)

        if FILL_NEW_QUERIES_MODE:
            self.search_queries = get_json(D_aggregated_search_result_folder_path)
            new_search_queries = set(get_json(C_search_queries_list_path)) - set(get_json(D_aggregated_search_result_folder_path))
            self.output_file_path = D_aggregated_search_result_folder_path
            for new_query in new_search_queries:
                self.search_queries.update({new_query: []})

        for search_query in self.search_queries:
            if len(self.search_queries[search_query]) == 0 or len(self.search_queries[search_query][0]) == 0:
                try:
                    images_downloaded, image_metadata = image_search.google(search_query, 20)
                    self.search_queries[search_query].append(image_metadata)
                except Exception as exp:
                    print('Failed to to download images for', search_query)
                    print(exp)
                dump_json(self.output_file_path, self.search_queries)

    def aggregate_search_queries(self, number_of_processes):
        aggregated_search_queries = dict()
        for i in range(1, number_of_processes + 1):
            output_file_path = D_search_result_folder_path.replace('.json', '-{}-{}.json'.format(i, number_of_processes))
            search_queries = get_json(output_file_path)
            for search_query in search_queries:
                if len(search_queries[search_query]) == 0:
                    # print('One of the search query was not searched [{}] '.format(search_query))
                    continue
                aggregated_search_queries.update({search_query: list(map(lambda query: {'name': query}, search_queries[search_query][0]))})
        dump_json(D_search_result_folder_path.replace('.json', '-aggregated-{}.json'.format(number_of_processes)), aggregated_search_queries)

    # Add search queries to Pipeline C.json, phrases that were not searched will be removed here
    def generate_final_D_search_results(self, processes=number_of_processes):
        aggregated_search_queries = get_json(D_search_result_folder_path.replace('.json', '-aggregated-{}.json'.format(processes)))
        figurative_phrases = []
        search_queries = get_json(C_search_queries_path)
        for phrase in search_queries:
            if self.filter_idiom(phrase) is True:
                for search_query in phrase['search_query']:
                    search_query_results = aggregated_search_queries.get(search_query['query'].lower())
                    if search_query_results is not None:  # This can be non in case of filtering bad idioms (we do not search them)
                        search_query['search_results'] = search_query_results
                        search_query['num_search_results'] = len(search_query_results)
                figurative_phrases.append(phrase)
        dump_json(D_final_search_result_path, figurative_phrases)

    def filter_idiom(self, idiom):
        if idiom['figurative_type'] != 'idiom':
            return True  # This is not a idiom, its fine
        for query in idiom['search_query']:
            if query['source_context_score'] >= 1:
                return True  # Found idiomatic or figurative definition found
        return False  # No idiomatic or figurative definition found

# D_Image_search().search_images()
# D_Image_search().aggregate_search_queries(5)
# D_Image_search().generate_final_D_search_results(5)
