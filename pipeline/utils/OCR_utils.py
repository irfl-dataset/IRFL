import json
import re

import cv2
import easyocr
import nltk
from matplotlib import pyplot as plt
from nltk.stem import WordNetLemmatizer
from textblob import TextBlob

from pipeline.utils.utils import get_image_size, open_image_by_url

wnl = WordNetLemmatizer()

reader = easyocr.Reader(["en"])

images_safe_text = ['vectorstock', 'stock', 'shutterstock', 'image id:', 'istock', 'alamy', 'dreamstimc',
                    'fotostock', 'dreamstime', '123rf', 'bigstock', 'dreamjtime', 'dreamrbime', 'dreamrbime', 'canstockphoto']
for safe_text in images_safe_text.copy():
    images_safe_text.append(safe_text + 'com')
    images_safe_text.append(safe_text + '.com')

def calculate_intersection(a, b):
    dx = min(a['xmax'], b['xmax']) - max(a['xmin'], b['xmin'])
    dy = min(a['ymax'], b['ymax']) - max(a['ymin'], b['ymin'])
    if (dx >= 0) and (dy >= 0):
        return dx * dy
    return 0


def plot_image_text_frames(IMAGE_PATH, image_details):
    font = cv2.FONT_HERSHEY_SIMPLEX
    img = cv2.imread(IMAGE_PATH)
    spacer = 100
    for detection in image_details:
        top_left = tuple(tuple(map(lambda x: int(x), detection[0][0])))
        bottom_right = tuple(tuple(map(lambda x: int(x), detection[0][2])))
        text = detection[1]
        img = cv2.rectangle(img, top_left, bottom_right, (0, 255, 0), 3)
        img = cv2.putText(img, text, (20, spacer), font, 0.5, (0, 255, 0), 2, cv2.LINE_AA)
        spacer += 15
    plt.figure(figsize=(10, 10))
    plt.imshow(img)
    plt.show()

# [x, y]
def get_OCR_frame_size(frame):
    top_left = tuple(frame[0])
    bottom_right = tuple(frame[2])
    width = bottom_right[0] - top_left[0]
    height = bottom_right[1] - top_left[1]
    size = height * width
    return size, {'xmin': top_left[0], 'xmax': bottom_right[0], 'ymin': top_left[1], 'ymax': bottom_right[1]}

def get_intersection_size(rectangles):  # array of [top_left, bottom_right]
    total_intersections = 0
    nested_rectangles = rectangles
    for first_rectangle in rectangles:
        nested_rectangles.remove(first_rectangle)
        for second_rectangle in rectangles:
            total_intersections += calculate_intersection(first_rectangle, second_rectangle)

    return total_intersections

def extract_text_size(image_details):
    total_frames_size = 0
    text_frames = list(map(lambda x: x[0], image_details))
    rectangles = []

    for frame in text_frames:
        frame_size, rectangle = get_OCR_frame_size(frame)
        rectangles.append(rectangle)
        total_frames_size += frame_size

    # TEST - rectangles = [{'xmin': 3, 'xmax': 5, 'ymin': 3, 'ymax': 5}, {'xmin': 1, 'xmax': 4, 'ymin': 1, 'ymax': 3.5}] will rsults 0.5
    intersection_size = get_intersection_size(rectangles)
    return total_frames_size - intersection_size

def extract_image_text(image_details):
    all_text = ' '.join(list(map(lambda x: x[1], image_details))).lower()
    return ' '.join(re.sub(' +', ' ', all_text).split(' '))

def get_text_words(text, min_length=3):
    tokenized = nltk.word_tokenize(text)
    return list(filter(lambda x: len(x) >= min_length, [word for (word, pos) in nltk.pos_tag(tokenized)]))

def correct_text_spelling_mistakes(text):
    try:
        textBlb = TextBlob(text)
        return textBlb.correct()
    except:
        return text

def read_image_details(img_path):
    try:
        img = open_image_by_url(img_path)
        return reader.readtext(img)
    except Exception as e:
        print('[Error easyOCR]: ' + str(e))
    return None

def filter_ocr(img_path, phrase, query, OCR_metadata=None):
    phrase = phrase.lower()
    query = query.lower()

    image_details = json.loads(OCR_metadata['image_details']) if OCR_metadata is not None else read_image_details(img_path)

    if image_details is None:
        return {'should_filter': False, 'text': '', 'corrected_text': '', 'text_size': -1, 'image_size': -1, 'text_percentage_of_image': -1, 'image_details': None, 'is_text_too_long': None,
                'is_safe_text': None, 'is_text_size_valid': None, 'is_text_not_similar_to_phrase': None, 'is_lemmatized_text_similar_to_phrase': None, 'is_text_not_similar_to_query': None, 'is_lemmatized_text_similar_to_query': None,
                'is_corrected_text_not_similar_to_phrase': None, 'is_corrected_lemmatized_text_similar_to_phrase': None, 'is_corrected_text_not_similar_to_query': None, 'is_corrected_lemmatized_text_similar_to_query': None
                }

    # plot_image_text_frames(img_path, image_details) # plots image
    text = OCR_metadata['text'] if OCR_metadata is not None else extract_image_text(image_details)
    text_size = OCR_metadata['text_size'] if OCR_metadata is not None else int(extract_text_size(image_details))
    image_size, text_percentage_of_image, is_text_size_valid = get_text_size_metadata(img_path, text_size, OCR_metadata['image_size'] if OCR_metadata is not None else None)
    is_text_too_long, is_safe_text = is_image_text_too_long(text)
    corrected_text = OCR_metadata['corrected_text'] if OCR_metadata is not None else correct_text_spelling_mistakes(text)
    is_text_not_similar_to_phrase, is_lemmatized_text_similar_to_phrase = is_image_text_not_similar(text, phrase)
    is_text_not_similar_to_query, is_lemmatized_text_similar_to_query = is_image_text_not_similar(text, query)
    is_corrected_text_not_similar_to_phrase, is_corrected_lemmatized_text_similar_to_phrase = is_image_text_not_similar(corrected_text, phrase)
    is_corrected_text_not_similar_to_query, is_corrected_lemmatized_text_similar_to_query = is_image_text_not_similar(corrected_text, query)
    should_filter = (is_text_too_long is False or is_safe_text) and is_corrected_text_not_similar_to_phrase and is_text_size_valid
    return {'should_filter': should_filter, 'text': text, 'corrected_text': corrected_text, 'text_size': text_size, 'image_size': image_size, 'text_percentage_of_image': text_percentage_of_image,
            'image_details': image_details, 'is_text_too_long': is_text_too_long, 'is_safe_text': is_safe_text, 'is_text_size_valid': is_text_size_valid,
            'is_text_not_similar_to_phrase': is_text_not_similar_to_phrase, 'is_lemmatized_text_similar_to_phrase': is_lemmatized_text_similar_to_phrase,
            'is_text_not_similar_to_query': is_text_not_similar_to_query, 'is_lemmatized_text_similar_to_query': is_lemmatized_text_similar_to_query,
            'is_corrected_text_not_similar_to_phrase': is_corrected_text_not_similar_to_phrase, 'is_corrected_lemmatized_text_similar_to_phrase': is_corrected_lemmatized_text_similar_to_phrase,
            'is_corrected_text_not_similar_to_query': is_corrected_text_not_similar_to_query, 'is_corrected_lemmatized_text_similar_to_query': is_corrected_lemmatized_text_similar_to_query
            }


def get_text_size_metadata(img_path, text_size, image_size=None):
    if image_size is None:
        image_size = get_image_size(img_path)
    return image_size, text_size / image_size, text_size / image_size < 0.3

def is_image_text_not_similar(text, phrase):
    try:
        words = get_text_words(str(phrase))
        lemmatized_text = ' '.join(list(map(lambda word: wnl.lemmatize(word), get_text_words(str(text), 1))))
        for word in words:
            if word in text:
                return False, wnl.lemmatize(word) in lemmatized_text
            if wnl.lemmatize(word) in lemmatized_text:
                return False, True
        return True, False
    except Exception as e:
        print('Error in is_image_text_not_similar')
        print(str(e))
        return False, False


def is_image_text_too_long(image_text):
    is_safe_text = False
    is_text_long = False
    for safe_text in images_safe_text:
        if safe_text in image_text:
            is_safe_text = True
    if len(set(image_text.split(' '))) >= 3:
        is_text_long = True
    return is_text_long, is_safe_text

