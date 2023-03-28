import json
import os

import boto3

from pipeline.utils.utils import get_str_hash


# The datasets saves the images details using the image UUID as primary key

class ImageDetailsDB:

    def __init__(self, use_local_cache=True):
        self.client = boto3.client('dynamodb', aws_access_key_id=os.environ['AWS_ID'], aws_secret_access_key=os.environ['AWS_SECRET'], region_name='us-east-1')
        self.dynamodb = boto3.resource('dynamodb', aws_access_key_id=os.environ['AWS_ID'], aws_secret_access_key=os.environ['AWS_SECRET'], region_name='us-east-1')
        self.dynamoDB_Cache = dict()
        if use_local_cache:
            self.init_dynamoDB_cache()

    def init_dynamoDB_cache(self):
        try:
            with open(r'CACHE_PATH') as f:
                for line in f:
                    item = json.loads(line)
                    self.dynamoDB_Cache.update({item.get('Item').get('imageUUID').get('S'): item})
        except Exception as e:
            print(e)

    def put_item(self, image_data):
        try:
            self.client.put_item(TableName='image-details',
                                 Item={
                                     'imageUUID': {'S': image_data['id']},
                                     'imageURL': {'S': image_data['url']},
                                     'imageType': {'S': image_data['type']},
                                     'label': {'S': image_data['label']},
                                     'websiteURL': {'S': image_data['websiteURL']}},
                                 ConditionExpression='attribute_not_exists(imageURL)')
            return True
        except Exception as error:
            print(error)
            return False

    def get_item_by_url(self, url):
        imageUUID = get_str_hash(url)
        res = self.dynamoDB_Cache.get(imageUUID)
        if res is None:
            res = self.client.get_item(TableName='image-details', Key={'imageUUID': {'S': imageUUID}})
        print(res)

    def get_item_by_uuid(self, uuid):
        res = self.dynamoDB_Cache.get(uuid)
        if res is None:
            res = self.client.get_item(TableName='image-details', Key={'imageUUID': {'S': uuid}})
        return res

    def has_item(self, imageUUID):
        res = self.dynamoDB_Cache.get(imageUUID)
        if res is None:
            res = self.client.get_item(TableName='image-details', Key={'imageUUID': {'S': imageUUID}})
        return res.get('Item') is not None

    def get_image_url_and_source(self, uuid):
        uuid = uuid.replace('.jpeg', '')
        try:
            return {'img': self.get_item_by_uuid(uuid).get('Item').get('imageURL').get('S'), 'source': self.get_item_by_uuid(uuid).get('Item').get('websiteURL').get('S'), 'uuid': uuid}
        except:
            print(f'Could not found {uuid}')
            return {}
