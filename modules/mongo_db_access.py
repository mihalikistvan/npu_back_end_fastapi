import certifi
import os
from pymongo.mongo_client import MongoClient
from bson.json_util import dumps
from bson.json_util import loads


class mongoDB():
    def __init__(self):
        client = MongoClient(os.getenv("mongo_db_url"),
                             tlsCAFile=certifi.where())
        db = client["npu_dev_1"]
        self.col_user = db["users"]
        self.col_creations = db["creations"]
        self.col_ratings = db["creation_ratings"]
        self.col_bricks = db["bricks"]

    def query_user(self):
        user_list = [i['user_name']
                     for i in self.col_user.find({'user_type': 'uploader'})]
        return user_list

    def query_bricks(self):
        bricks = list(self.col_bricks.find(
            {"brick_dict": {"$exists": True}}, {'_id': 0}))
        return loads(dumps(bricks))

    def query_creations(self):
        creations = list(self.col_creations.find(
            {"creation_name": {"$exists": True}}, {'_id': 0}))
        return loads(dumps(creations))

    def query_one_creations(self, creation_id):
        creations = self.col_creations.find_one(
            {"creation_id": creation_id}, {'_id': 0})
        return creations

    def query_creation_ratings(self, creation_id):
        ratings = list(self.col_ratings.find(
            {"creation_id": creation_id}, {'_id': 0}))
        return loads(dumps(ratings))

    def upload_creation_rating(self, creation_id, uniqueness, creativity, rated_by):

        if self.col_ratings.find_one({"$and": [{"creation_id": creation_id}, {"rated_by": rated_by}]}) is None:
            new_rating = {
                'creation_id': creation_id,
                'uniqueness': uniqueness,
                'creativity': creativity,
                'rated_by': rated_by,
            }
            self.col_ratings.insert_one(new_rating)
            return 'Successful rating.'
        return 'User allready rated this creation.'

    def upload_file_metadata(self, creation_name, creation_id, user_email, bricks, generated_file_name):
        metadata = {
            'creation_name': creation_name,
            'creation_id': creation_id,
            'user_email': user_email,
            'bricks': bricks,
            'file_url': f"{os.getenv('s3_url')}{generated_file_name}"
        }
        self.col_creations.insert_one(metadata)
        return 'Successful upload'

    def delete_creation(self, creation_id):
        self.col_creations.delete_one({"creation_id": creation_id})
        self.col_ratings.delete_manye({"creation_id": creation_id})
