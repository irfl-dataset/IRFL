import json

import cv2
import nltk
import torch
from nltk.stem import WordNetLemmatizer
from transformers import ViltProcessor, ViltForImageAndTextRetrieval

from pipeline.assets.constants import forbidden_website
from pipeline.utils.OCR_utils import filter_ocr
from pipeline.utils.image_details_db import ImageDetailsDB
from pipeline.utils.utils import convert, open_image_by_url, get_cv2_image_by_url

wnl = WordNetLemmatizer()

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

image_details_db = ImageDetailsDB()

device = 'cuda'

# ViLT
processor = ViltProcessor.from_pretrained("dandelin/vilt-b32-finetuned-coco")
vilt_model = ViltForImageAndTextRetrieval.from_pretrained("dandelin/vilt-b32-finetuned-coco")
vilt_model.to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))

counter = 1
def enchant_idiom_ViLT_features(idiom, prompt, query, OVERRIDE_MODE=False):
    global counter
    for img_metadata in idiom['search_results']:
        image_path = image_details_db.get_image_url_and_source(img_metadata['name']).get('img')
        if img_metadata.get('filter_ocr') is not None and OVERRIDE_MODE is False:
            filter_ocr_details = filter_ocr(image_path, prompt, query, img_metadata.get('OCR_metadata'))
            set_image_OCR(img_metadata, filter_ocr_details)
            continue

        if img_metadata.get('idiom_ViLT_score') is None:
            img_metadata['idiom_ViLT_score'] = 0
            img_metadata['query_ViLT_score'] = 0

        img_metadata['is_white'] = is_white(image_path)

        img_metadata['filter_ocr'] = False

        filter_ocr_details = filter_ocr(image_path, prompt, query, img_metadata.get('OCR_metadata'))
        set_image_OCR(img_metadata, filter_ocr_details)

        if img_metadata['filter_ocr']:
            img_metadata['filter_ocr'] = True
            with torch.no_grad():
                try:
                    ViLT_logits_per_image = calculate_ViLT([prompt, query, 'document', 'a page of a book', 'a contract'], image_path)

                    # Phrase/Query related
                    img_metadata['idiom_ViLT_score'] = float(ViLT_logits_per_image[0])
                    img_metadata['query_ViLT_score'] = float(ViLT_logits_per_image[1])

                    # Image related
                    img_metadata['is_document'] = sum([float(ViLT_logits_per_image[2]), float(ViLT_logits_per_image[3]), float(ViLT_logits_per_image[4])]) >= 18.77992821
                    img_metadata['is_document_metadata'] = {'document_ViLT_score': float(ViLT_logits_per_image[2]),
                                                            'a_page_of_a_book_ViLT_score': float(ViLT_logits_per_image[3]),
                                                            'a_contract': float(ViLT_logits_per_image[4])}
                except Exception as e:
                    print('[filter_utils.enchant_idiom_ViLT_features]: ' + str(e))


def calculate_ViLT(texts, image_path):
    scores = []
    image = open_image_by_url(image_path, 'PIL')
    for text in texts:
        encoding = processor(image, text, return_tensors="pt")
        # Transforms all tensors to device
        encoding.data['input_ids'] = encoding.data['input_ids'].to(device)
        encoding.data['token_type_ids'] = encoding.data['token_type_ids'].to(device)
        encoding.data['attention_mask'] = encoding.data['attention_mask'].to(device)
        encoding.data['pixel_values'] = encoding.data['pixel_values'].to(device)
        encoding.data['pixel_mask'] = encoding.data['pixel_mask'].to(device)

        output = vilt_model(**encoding)
        score = output.logits[:, 0].item()
        scores.append(score)

    return scores

def set_image_OCR(img_metadata, filter_ocr_details):
    img_metadata['OCR_metadata'] = {'text': filter_ocr_details['text'], 'text_size': filter_ocr_details['text_size'], 'image_size': filter_ocr_details['image_size'],
                                    'text_percentage_of_image': filter_ocr_details['text_percentage_of_image'], 'corrected_text': filter_ocr_details['corrected_text'],
                                    'image_details': json.dumps(filter_ocr_details['image_details'], default=convert)}

    img_metadata['filter_ocr'] = filter_ocr_details['should_filter']

    filters_metadata = dict()
    filters_metadata['is_text_too_long'] = filter_ocr_details['is_text_too_long']
    filters_metadata['is_safe_text'] = filter_ocr_details['is_safe_text']
    filters_metadata['is_text_size_valid'] = filter_ocr_details['is_text_size_valid']
    filters_metadata['is_text_not_similar_to_phrase'] = filter_ocr_details['is_text_not_similar_to_phrase']
    filters_metadata['is_text_not_similar_to_query'] = filter_ocr_details['is_text_not_similar_to_query']
    filters_metadata['is_lemmatized_text_similar_to_phrase'] = filter_ocr_details['is_lemmatized_text_similar_to_phrase']
    filters_metadata['is_lemmatized_text_similar_to_query'] = filter_ocr_details['is_lemmatized_text_similar_to_query']
    filters_metadata['is_corrected_text_not_similar_to_phrase'] = filter_ocr_details['is_corrected_text_not_similar_to_phrase']
    filters_metadata['is_corrected_text_not_similar_to_query'] = filter_ocr_details['is_corrected_text_not_similar_to_query']
    filters_metadata['is_corrected_lemmatized_text_similar_to_phrase'] = filter_ocr_details['is_corrected_lemmatized_text_similar_to_phrase']
    filters_metadata['is_corrected_lemmatized_text_similar_to_query'] = filter_ocr_details['is_corrected_lemmatized_text_similar_to_query']

    img_metadata['filters_metadata'] = json.dumps(filters_metadata, default=convert)
    return img_metadata

def filter_forbidden_websites_images(image):
    try:
        result = image_details_db.get_item_by_uuid(image.get('name'))
        return forbidden_website not in result.get('Item').get('websiteURL').get('S')
    except Exception as exception:
        print(exception)
        return True

def get_idiom_literal_photos(images):
    return list(filter(lambda image: round(image['idiom_ViLT_score'], 2) >= round(image['query_ViLT_score'], 2) and image['idiom_ViLT_score'] > 1.150353, images))

def get_top_images(images, k, property):
    sorted_images = sorted(images, key=lambda x: x[property], reverse=True)
    return sorted_images[:k]

def is_white(image_path):
    try:
        '''Returns True if all white pixels or False if not all white'''
        image = get_cv2_image_by_url(image_path)
        H, W = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

        pixels = cv2.countNonZero(thresh)
        return True if pixels == (H * W) else False
    except Exception as e:
        print(e)
        return False
