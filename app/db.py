import os
import yaml
import gridfs

from bson import ObjectId
from bson.errors import InvalidId
from typing import List, TypeVar, Optional
from logzero import logger
from pymongo import MongoClient
from pymongo.database import Database, Collection
from pymongo.results import UpdateResult, DeleteResult


host = os.getenv("MONGODB_HOST", "localhost")
port = os.getenv("MONGODB_PORT", 27017)
auth = {}

DATABASE_NAME = "recipebook"
db: Database = MongoClient(host=host, port=port, **auth)[DATABASE_NAME]
fs = gridfs.GridFS(db)

TBase = TypeVar("TBase", bound="Base")


class Base(dict):
    __collection__: Collection = None

    __getattr__ = dict.get
    __delattr__ = dict.__delitem__
    __setattr__ = dict.__setitem__

    @classmethod
    def get_doc(cls, object_id) -> TBase:
        try:
            doc = cls.__collection__.find_one({"_id": ObjectId(object_id)})
            if doc:
                return cls(doc)

        except InvalidId:
            return None

    @classmethod
    def find(cls, *args, **kwargs) -> List[TBase]:
        docs = cls.__collection__.find(*args, **kwargs)
        if docs:
            return [cls(doc) for doc in docs]

    @classmethod
    def find_one(cls, *args, **kwargs) -> TBase:
        doc = cls.__collection__.find_one(*args, **kwargs)
        if doc:
            return cls(doc)

    @classmethod
    def update_one(cls, *args, **kwargs) -> UpdateResult:
        return cls.__collection__.update_one(*args, **kwargs)

    def save(self):
        """
        Persist object into database collection
        """
        if not self._id:
            res = self.__collection__.insert_one(self)
            self["_id"] = res.inserted_id
        else:
            update_fields = dict(**self)
            update_fields.pop("_id")
            self.__collection__.update_one(
                {"_id": ObjectId(self._id)}, {"$set": update_fields}
            )

    def reload(self):
        """
        Reload object's attributes from database
        """
        if self._id:
            self.update(self.__collection__.find_one({"_id": ObjectId(self._id)}))

    def remove(self) -> Optional[DeleteResult]:
        """
        Remove object from database
        """
        if self._id:
            result = self.__collection__.delete_one({"_id": ObjectId(self._id)})
            self.clear()
            return result
        else:
            return None


class Recipe(Base):
    """
    A Python object to represent the Recipes collection in MongoDB
    """

    __collection__ = db["recipe"]


class FileStorage:
    """
    A Python object to interact with MongoDB file storage
    """

    __fs__ = fs
    __default_recipe_img__ = "app/static/images/default_recipe_img.png"

    @classmethod
    def read_image(cls, filename):
        file = cls.__fs__.find_one({"filename": filename})
        if file:
            return file.read()

        with open(cls.__default_recipe_img__, "rb") as f:
            contents = f.read()
        return contents

    @classmethod
    def store_image(cls, filename, contents):
        cls.remove_images(filename)
        logger.info(f"Storing image with filename [{filename}]")
        cls.__fs__.put(contents, filename=filename)

    @classmethod
    def remove_images(cls, filename):
        logger.info(f"Removing existing images with filename [{filename}]")
        for existing in cls.__fs__.find({"filename": filename}):
            cls.__fs__.delete(existing._id)


def initialize():
    logger.info("Initializing DB collections")

    RECIPE_IDX_NAME = "recipe_search_index"
    indexes = Recipe.__collection__.list_indexes()
    matches = [idx for idx in indexes if idx["name"] == RECIPE_IDX_NAME]

    if len(matches) == 0:
        logger.info("Creating search index for recipes")
        Recipe.__collection__.create_index(
            [
                ("name", "text"),
            ],
            name=RECIPE_IDX_NAME,
        )


def import_sample_data():
    ROOT_DIR = "samples"
    IMG_DIR = "samples/img/"

    for root, dirs, files in os.walk(ROOT_DIR):
        dirs[:] = [d for d in dirs if d != "img"]
        for file in [f for f in files if f.endswith(".yaml")]:
            with open(os.path.join(root, file), "r") as recipe_file:
                doc = yaml.safe_load(recipe_file)

            logger.info(f"Creating recipe [{doc['name']}]")
            recipe = Recipe(**doc)
            recipe.save()

            src_img = IMG_DIR + file.split(".")[0] + ".jpg"
            with open(src_img, "rb") as f:
                contents = f.read()
            FileStorage.store_image(filename=str(recipe._id), contents=contents)


initialize()
