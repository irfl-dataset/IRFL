from assets.config import B_search_queries_path, C_search_queries_path, C_search_queries_list_path
from pipeline.utils.preplexity import get_perplexity
from pipeline.utils.utils import get_json, dump_json

class C_search_queries:

    def __init__(self):
        self.B_search_queries = get_json(B_search_queries_path)
        self.idiom_propmt_dict = dict()

        for phrase in self.B_search_queries:
            self.idiom_propmt_dict.update({phrase['prompt'].lower(): phrase})

        for phrase in self.B_search_queries:
            self.add_idiom_phrase_search_query(phrase)
            self.clean_idiom_definitions(phrase)
            self.get_IRLM_MAGPIE_idioms_score(phrase)

        dump_json(C_search_queries_list_path, self.get_queries_list(self.B_search_queries))
        dump_json(C_search_queries_path, self.B_search_queries)
        print('[C_search_queries]: Initialized')


    def get_IRLM_MAGPIE_idioms_score(self, idiom):
        new_search_queries = dict()
        search_queries = idiom['search_query']

        for query in search_queries:
            definition = query['definition']
            if len(search_queries) == 1:
                if definition.lower() == idiom['prompt'].lower():
                    print('Special case')
            elif self.idiom_propmt_dict.get(definition.lower()) is not None and not definition.lower() == idiom['prompt'].lower():
                print('nested idiom')
            new_search_queries.update({definition: {'query': definition, 'source_context_score': self.score_idiom_context(query['context']),
                                               'length_score': len(definition), 'perplexity_score': get_perplexity(definition)}})

        idiom['search_query'] = list(new_search_queries.values())
        return idiom

    def clean_idiom_definitions(self, idiom):
        search_queries = idiom['search_query']

        # extend nested idioms
        duplicate_search_queries = None
        for query in search_queries:
            definition = query['definition']
            identical_idiom = self.idiom_propmt_dict.get(definition.lower())
            if identical_idiom is not None:
                if duplicate_search_queries is None:
                    duplicate_search_queries = search_queries.copy()
                duplicate_search_queries.extend(identical_idiom['definition'])
                duplicate_search_queries.remove(query)

        if duplicate_search_queries is not None:
            idiom['search_query'] = duplicate_search_queries
            search_queries = idiom['search_query']

        # remove duplicate definitions
        cache = set()
        duplicate_search_queries_final = []
        for query in search_queries:
            if query['definition'].lower() not in cache:
                duplicate_search_queries_final.append(query)
                cache.add(query['definition'].lower())

        idiom['search_query'] = duplicate_search_queries_final
        idiom['definition'] = duplicate_search_queries_final  # In this part of the code search_query and definition are the same


    def add_idiom_phrase_search_query(self, idiom):
        idiom['search_query'].append({'context': '', 'definition': idiom['prompt']})
        idiom['definition'].append({'context': '', 'definition': idiom['prompt']})
        return idiom

    def score_idiom_context(self, context):
        if "sarcasm" in context or "slang" in context:
            return -2
        if context == "":
            return 0
        if 'figuratively' in context:
            return 1
        if 'idiomatic' in context:
            return 2

        return -1  # other

    def get_queries_list(self, B_search_queries):
        queries_list = []
        queries_set = set()
        for phrase in B_search_queries:
            if self.filter_idiom(phrase):
                for query in phrase.get('search_query'):
                    queries_list.append(query.get('query').lower())
                    queries_set.add(query.get('query').lower())
        print('{} search queries, {} unique search queries.'.format(len(queries_list), len(queries_set)))

        queries_dict = dict()
        for query in queries_set:
            queries_dict.update({query: []})
        return queries_dict

    def filter_idiom(self, idiom):
        for query in idiom['search_query']:
            if query['source_context_score'] >= 1:
                return True  # Found idiomatic or figurative definition
        return False  # No idiomatic or figurative definition found

C_search_queries()
