from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["gourmetdash"]

users = db["users"]

print("\n===== USERS =====\n")

for user in users.find():
    print(f"Email    : {user.get('email', 'N/A')}")
    print(f"Password : {user.get('password', 'N/A')}")
    print(f"Role     : {user.get('role', 'N/A')}")
    print("-----------------------------")