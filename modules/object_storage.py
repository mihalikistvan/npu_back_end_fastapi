import boto3
import os

class s3_service():

    def __init__(self):
        self.session = boto3.Session(
            aws_access_key_id=os.getenv("aws_access_key_id"),
            aws_secret_access_key=os.getenv("aws_secret_access_key"),
        )
    def upload_file(self, generated_filename):
        s3 = self.session.resource('s3')
        try:
            s3.meta.client.upload_file(Filename='./static/'+generated_filename, 
                                   Bucket='npudev1', 
                                   Key=generated_filename,
                                   ExtraArgs={'ACL':'public-read'})
        except Exception as e:
            print (e)