from pipeline.MAGPIE_dataset_generation import MAGPIE_dataset_generation

GENERATE_MAGPIE = True


class A_generate_figurative_dataset:

    def __init__(self):
        if GENERATE_MAGPIE:
            MAGPIE_dataset_generation().generate_MAGPIE_dataset()
        print('[A_generate_figurative_dataset]: Initialized')


A_generate_figurative_dataset()
