from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Security, status, Depends
from fastapi.security import APIKeyHeader
from dotenv import find_dotenv, load_dotenv
import shutil
import random
import string
from typing_extensions import Annotated
from modules.mongo_db_access import mongoDB
from modules.object_storage import s3_service
import os

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = FastAPI()
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

mongoDB_instance = mongoDB()
s3 = s3_service()


def api_key_auth(api_key_header: str = Security(api_key_header),) -> str:
    if api_key_header != os.getenv('api_key'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Forbidden"
        )


@app.get("/")
def read_root():
    return {"msg": "npu dev api v1"}


@app.get("/bricks")
def get_dict_of_bricks():
    return mongoDB_instance.query_bricks()


@app.get("/creations")
def get_creations():
    return mongoDB_instance.query_creations()


@app.get("/creations/{creation_id}")
def get_creation_by_id(creation_id: str):
    return mongoDB_instance.query_one_creations(creation_id)


@app.get("/creation_by_bricks/{brick_name}")
def get_creations_by_brick_id(brick_name: str):
    return mongoDB_instance.query_creations_by_brick_name(brick_name)


@app.get("/ratings/{creation_id}")
def get_ratings_of_a_creation(creation_id: str):
    return mongoDB_instance.query_creation_ratings(creation_id)


@app.post("/ratings/{creation_id}", dependencies=[Depends(api_key_auth)])
async def add_rating_for_a_creation(creation_id:str,
                                    uniqueness: Annotated[int, Form()],
                                    creativity: Annotated[int, Form()],
                                    rated_by: Annotated[str, Form()]):
    return mongoDB_instance.upload_creation_rating(creation_id, uniqueness, creativity, rated_by)


@app.post("/upload", dependencies=[Depends(api_key_auth)])
async def upload_new_creation(creation_name: Annotated[str, Form()],
                              user_email: Annotated[str, Form()],
                              bricks: Annotated[list, Form()],
                              description: Annotated[str, Form()],
                              file: UploadFile = File(...)):

    try:
        generated_filename = ''.join(random.choice(
            string.ascii_letters) for _ in range(32))+'.'+file.filename.split('.')[-1]
        generated_id = user_email + \
            ''.join(random.choice(string.ascii_letters) for _ in range(12))
        with open('static/'+generated_filename, 'wb') as f:

            mongoDB_instance.upload_file_metadata(creation_name=creation_name,
                                                  creation_id=generated_id,
                                                  user_email=user_email,
                                                  description=description,
                                                  bricks=bricks,
                                                  generated_file_name=generated_filename)

            shutil.copyfileobj(file.file, f)
            s3.upload_file(generated_filename=generated_filename)
            file.file.close()
    except Exception as e:
        print(e)
        return {"message": "There was an error uploading the file"}

    return {"message": f"Successfully uploaded"}


@app.delete("/creations/{creation_id}", dependencies=[Depends(api_key_auth)])
async def delete_creation(creation_id: str):
    mongoDB_instance.remove_creation(creation_id=creation_id)
    return {"message": "Successfully removed creation"}
