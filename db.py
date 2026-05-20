from copy import deepcopy

from pymongo import ASCENDING, DESCENDING, MongoClient
from bson import ObjectId

from config import Config


class _InsertResult:
	def __init__(self, inserted_id):
		self.inserted_id = inserted_id


class _UpdateResult:
	def __init__(self, modified_count=0):
		self.modified_count = modified_count


class _DeleteResult:
	def __init__(self, deleted_count=0):
		self.deleted_count = deleted_count


class _Cursor:
	def __init__(self, documents):
		self._documents = documents

	def sort(self, key_or_list, direction=ASCENDING):
		if isinstance(key_or_list, list):
			sort_fields = list(reversed(key_or_list))
		else:
			sort_fields = [(key_or_list, direction)]

		for field, sort_direction in sort_fields:
			reverse = sort_direction == DESCENDING
			self._documents.sort(key=lambda doc, field=field: doc.get(field), reverse=reverse)
		return self

	def limit(self, amount):
		self._documents = self._documents[:amount]
		return self

	def __iter__(self):
		return iter(self._documents)


def _normalize(value):
	if isinstance(value, ObjectId):
		return str(value)
	return value


def _matches(document, query):
	for key, expected in query.items():
		if key == "$or":
			if not any(_matches(document, clause) for clause in expected):
				return False
			continue

		actual = document.get(key)

		if isinstance(expected, dict):
			if "$gte" in expected and actual < expected["$gte"]:
				return False
			if "$regex" in expected:
				import re

				pattern = expected["$regex"]
				flags = re.IGNORECASE if expected.get("$options") == "i" else 0
				if actual is None or re.search(pattern, str(actual), flags) is None:
					return False
			continue

		if _normalize(actual) != _normalize(expected):
			return False

	return True


class _Collection:
	def __init__(self, name):
		self._name = name
		self._documents = []

	def create_index(self, *args, **kwargs):
		return None

	def insert_one(self, document):
		doc = deepcopy(document)
		doc.setdefault("_id", ObjectId())
		self._documents.append(doc)
		return _InsertResult(doc["_id"])

	def find_one(self, query):
		for document in self._documents:
			if _matches(document, query):
				return deepcopy(document)
		return None

	def find(self, query):
		return _Cursor([deepcopy(document) for document in self._documents if _matches(document, query)])

	def update_one(self, query, update):
		for document in self._documents:
			if _matches(document, query):
				changed = False
				if "$set" in update:
					document.update(deepcopy(update["$set"]))
					changed = True
				if "$inc" in update:
					for key, amount in update["$inc"].items():
						document[key] = document.get(key, 0) + amount
					changed = True
				return _UpdateResult(1 if changed else 0)
		return _UpdateResult(0)

	def delete_many(self, query):
		before = len(self._documents)
		self._documents = [document for document in self._documents if not _matches(document, query)]
		return _DeleteResult(before - len(self._documents))

	def delete_one(self, query):
		for index, document in enumerate(self._documents):
			if _matches(document, query):
				del self._documents[index]
				return _DeleteResult(1)
		return _DeleteResult(0)

	def count_documents(self, query):
		return sum(1 for document in self._documents if _matches(document, query))


class _Database:
	def __init__(self):
		self._collections = {}

	def __getitem__(self, name):
		if name not in self._collections:
			self._collections[name] = _Collection(name)
		return self._collections[name]


def _connect():
	client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=1000)
	client.admin.command("ping")
	return client.get_default_database()


try:
	db = _connect()
except Exception:
	db = _Database()

# ── Collections ───────────────────────────────────────────────
users_col = db["users"]
restaurants_col = db["restaurants"]
menu_items_col = db["menu_items"]
orders_col = db["orders"]
delivery_agents_col = db["delivery_agents"]

# ── Indexes ───────────────────────────────────────────────────
users_col.create_index("email", unique=True)
restaurants_col.create_index("owner_id")
restaurants_col.create_index("cuisine_tag")
menu_items_col.create_index("restaurant_id")
orders_col.create_index([("restaurant_id", ASCENDING), ("placed_at", DESCENDING)])
orders_col.create_index([("customer_id", ASCENDING), ("placed_at", DESCENDING)])
orders_col.create_index("status")
delivery_agents_col.create_index("user_id")