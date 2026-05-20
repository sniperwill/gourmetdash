from flask import Flask, request, jsonify, render_template
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from bson import ObjectId
from datetime import datetime, timedelta
import jwt, functools

from db import (users_col, restaurants_col,
                menu_items_col, orders_col, delivery_agents_col)
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
bcrypt = Bcrypt(app)
CORS(app, supports_credentials=True)


# ════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════

def _serialize(doc):
    """Recursively convert ObjectId / datetime → str for JSON."""
    if doc is None:
        return None
    for k, v in list(doc.items()):
        if isinstance(v, ObjectId):
            doc[k] = str(v)
        elif isinstance(v, datetime):
            doc[k] = v.isoformat()
    doc["_id"] = str(doc["_id"])
    return doc

def _create_token(user_id, role):
    payload = {
        "user_id": str(user_id),
        "role":    role,
        "exp":     datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")

def token_required(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        raw = request.headers.get("Authorization", "")
        token = raw.replace("Bearer ", "").strip()
        if not token:
            return jsonify({"error": "Token missing"}), 401
        try:
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            request.user_id   = data["user_id"]
            request.user_role = data["role"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return wrapper

def role_required(*roles):
    def decorator(f):
        @functools.wraps(f)
        @token_required
        def wrapper(*args, **kwargs):
            if request.user_role not in roles:
                return jsonify({"error": "Insufficient permissions"}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator


# ════════════════════════════════════════════════════════════════
# FRONTEND ENTRY
# ════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index.html")


# ════════════════════════════════════════════════════════════════
# AUTH  /api/auth/*
# ════════════════════════════════════════════════════════════════

@app.route("/api/auth/signup", methods=["POST"])
def signup():
    data = request.get_json()
    for field in ("name", "email", "phone", "password", "role"):
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    role = data["role"]
    if role not in ("customer", "restaurant", "delivery"):
        return jsonify({"error": "Invalid role"}), 400

    if users_col.find_one({"email": data["email"]}):
        return jsonify({"error": "Email already registered"}), 409

    hashed_pw = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
    user_doc  = {
        "name":       data["name"],
        "email":      data["email"],
        "phone":      data["phone"],
        "password":   hashed_pw,
        "role":       role,
        "created_at": datetime.utcnow()
    }
    user_id = users_col.insert_one(user_doc).inserted_id

    extra = {}

    if role == "restaurant":
        if not data.get("restaurant_name"):
            return jsonify({"error": "restaurant_name is required"}), 400
        rest_doc = {
            "name":              data["restaurant_name"],
            "owner_id":          user_id,
            "cuisine":           data.get("cuisine", "Multi-cuisine"),
            "cuisine_tag":       data.get("cuisine_tag", "all"),
            "emoji":             data.get("emoji", "🍽️"),
            "address":           data.get("address", ""),
            "phone":             data["phone"],
            "email":             data["email"],
            "rating":            0.0,
            "review_count":      0,
            "is_open":           True,
            "open_time":         "09:00",
            "close_time":        "23:00",
            "min_order":         149,
            "delivery_time":     "30–40 min",
            "min_delivery_mins": 30,
            "tags":              [],
            "created_at":        datetime.utcnow()
        }
        rest_id = restaurants_col.insert_one(rest_doc).inserted_id
        extra["restaurant_id"]   = str(rest_id)
        extra["restaurant_name"] = data["restaurant_name"]

    elif role == "delivery":
        agent_doc = {
            "user_id":          user_id,
            "name":             data["name"],
            "phone":            data["phone"],
            "location":         data.get("location", ""),
            "vehicle_number":   data.get("vehicle_number", ""),
            "license_id":       data.get("license_id", ""),
            "is_available":     True,
            "rating":           5.0,
            "total_deliveries": 0,
            "created_at":       datetime.utcnow()
        }
        agent_id = delivery_agents_col.insert_one(agent_doc).inserted_id
        extra["agent_id"] = str(agent_id)

    token = _create_token(user_id, role)
    return jsonify({
        "message": "Account created successfully",
        "token":   token,
        "user": {"id": str(user_id), "name": data["name"],
                 "email": data["email"], "role": role, **extra}
    }), 201


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email and password required"}), 400

    user = users_col.find_one({"email": data["email"]})
    if not user or not bcrypt.check_password_hash(user["password"], data["password"]):
        return jsonify({"error": "Invalid credentials"}), 401

    if data.get("role") and data["role"] != user["role"]:
        return jsonify({"error": "Role mismatch — check the 'I am a' dropdown"}), 401

    extra = {}
    if user["role"] == "restaurant":
        rest = restaurants_col.find_one({"owner_id": user["_id"]})
        if rest:
            extra["restaurant_id"]   = str(rest["_id"])
            extra["restaurant_name"] = rest["name"]
    elif user["role"] == "delivery":
        agent = delivery_agents_col.find_one({"user_id": user["_id"]})
        if agent:
            extra["agent_id"] = str(agent["_id"])

    token = _create_token(user["_id"], user["role"])
    return jsonify({
        "message": "Login successful",
        "token":   token,
        "user": {"id": str(user["_id"]), "name": user["name"],
                 "email": user["email"], "role": user["role"], **extra}
    })


# ════════════════════════════════════════════════════════════════
# RESTAURANTS  /api/restaurants/*
# ════════════════════════════════════════════════════════════════

@app.route("/api/restaurants", methods=["GET"])
def get_restaurants():
    cuisine  = request.args.get("cuisine", "all")
    sort_by  = request.args.get("sort", "relevance")
    query    = {} if cuisine == "all" else {"cuisine_tag": cuisine}
    results  = list(restaurants_col.find(query))

    sort_map = {
        "rating":        lambda x: -x.get("rating", 0),
        "delivery_time": lambda x:  x.get("min_delivery_mins", 30),
        "cost":          lambda x:  x.get("min_order", 0),
    }
    if sort_by in sort_map:
        results.sort(key=sort_map[sort_by])

    return jsonify([_serialize(r) for r in results])


@app.route("/api/restaurants/<rid>", methods=["GET"])
def get_restaurant(rid):
    try:
        rest = restaurants_col.find_one({"_id": ObjectId(rid)})
    except Exception:
        return jsonify({"error": "Invalid ID"}), 400
    if not rest:
        return jsonify({"error": "Not found"}), 404
    return jsonify(_serialize(rest))


@app.route("/api/restaurants/<rid>", methods=["PUT"])
@token_required
def update_restaurant(rid):
    try:
        rest = restaurants_col.find_one({"_id": ObjectId(rid)})
    except Exception:
        return jsonify({"error": "Invalid ID"}), 400
    if not rest:
        return jsonify({"error": "Not found"}), 404
    if str(rest["owner_id"]) != request.user_id:
        return jsonify({"error": "Unauthorized"}), 403

    data    = request.get_json()
    allowed = ["name", "cuisine", "address", "open_time", "close_time",
               "is_open", "min_order", "emoji", "phone", "email"]
    update  = {k: data[k] for k in allowed if k in data}
    restaurants_col.update_one({"_id": ObjectId(rid)}, {"$set": update})
    return jsonify({"message": "Restaurant updated"})


@app.route("/api/restaurants/<rid>/analytics", methods=["GET"])
@token_required
def get_analytics(rid):
    if request.user_role != "restaurant":
        return jsonify({"error": "Unauthorized"}), 403
    try:
        rest = restaurants_col.find_one({"_id": ObjectId(rid)})
    except Exception:
        return jsonify({"error": "Invalid ID"}), 400
    if not rest or str(rest["owner_id"]) != request.user_id:
        return jsonify({"error": "Unauthorized"}), 403

    today        = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_orders = list(orders_col.find({"restaurant_id": ObjectId(rid),
                                         "placed_at": {"$gte": today}}))
    return jsonify({
        "today_orders":   len(today_orders),
        "today_revenue":  round(sum(o["total"] for o in today_orders), 2),
        "pending_orders": sum(1 for o in today_orders if o["status"] == "pending"),
        "avg_rating":     rest.get("rating", 0),
        "review_count":   rest.get("review_count", 0)
    })


# ════════════════════════════════════════════════════════════════
# MENU  /api/restaurants/<rid>/menu  &  /api/menu/<id>
# ════════════════════════════════════════════════════════════════

@app.route("/api/restaurants/<rid>/menu", methods=["GET"])
def get_menu(rid):
    try:
        items = list(menu_items_col.find({"restaurant_id": ObjectId(rid),
                                          "is_available": True}))
    except Exception:
        return jsonify({"error": "Invalid ID"}), 400

    categories = {}
    for item in items:
        cat = item.get("category", "Other")
        categories.setdefault(cat, []).append(_serialize(dict(item)))

    return jsonify({"categories": categories,
                    "items": [_serialize(i) for i in items]})


@app.route("/api/menu", methods=["POST"])
@token_required
def add_menu_item():
    if request.user_role != "restaurant":
        return jsonify({"error": "Only restaurants can add items"}), 403

    data = request.get_json()
    for field in ("name", "price", "category", "restaurant_id"):
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    try:
        rest = restaurants_col.find_one({"_id": ObjectId(data["restaurant_id"])})
    except Exception:
        return jsonify({"error": "Invalid restaurant_id"}), 400
    if not rest or str(rest["owner_id"]) != request.user_id:
        return jsonify({"error": "Unauthorized"}), 403

    doc = {
        "name":          data["name"],
        "price":         float(data["price"]),
        "category":      data["category"],
        "type":          data.get("type", "veg"),
        "description":   data.get("description", ""),
        "emoji":         data.get("emoji", "🍽️"),
        "restaurant_id": ObjectId(data["restaurant_id"]),
        "is_available":  True,
        "created_at":    datetime.utcnow()
    }
    inserted_id = menu_items_col.insert_one(doc).inserted_id
    doc["_id"] = str(inserted_id)
    doc["restaurant_id"] = data["restaurant_id"]
    return jsonify({"message": "Item added", "item": doc}), 201


@app.route("/api/menu/<item_id>", methods=["PUT"])
@token_required
def update_menu_item(item_id):
    if request.user_role != "restaurant":
        return jsonify({"error": "Unauthorized"}), 403
    try:
        item = menu_items_col.find_one({"_id": ObjectId(item_id)})
    except Exception:
        return jsonify({"error": "Invalid ID"}), 400
    if not item:
        return jsonify({"error": "Item not found"}), 404

    rest = restaurants_col.find_one({"_id": item["restaurant_id"]})
    if not rest or str(rest["owner_id"]) != request.user_id:
        return jsonify({"error": "Unauthorized"}), 403

    data    = request.get_json()
    allowed = ["name", "price", "category", "type", "description", "emoji", "is_available"]
    update  = {k: data[k] for k in allowed if k in data}
    if "price" in update:
        update["price"] = float(update["price"])

    menu_items_col.update_one({"_id": ObjectId(item_id)}, {"$set": update})
    return jsonify({"message": "Item updated"})


@app.route("/api/menu/<item_id>", methods=["DELETE"])
@token_required
def delete_menu_item(item_id):
    if request.user_role != "restaurant":
        return jsonify({"error": "Unauthorized"}), 403
    try:
        item = menu_items_col.find_one({"_id": ObjectId(item_id)})
    except Exception:
        return jsonify({"error": "Invalid ID"}), 400
    if not item:
        return jsonify({"error": "Item not found"}), 404

    rest = restaurants_col.find_one({"_id": item["restaurant_id"]})
    if not rest or str(rest["owner_id"]) != request.user_id:
        return jsonify({"error": "Unauthorized"}), 403

    menu_items_col.delete_one({"_id": ObjectId(item_id)})
    return jsonify({"message": "Item deleted"})


# ════════════════════════════════════════════════════════════════
# ORDERS  /api/orders/*
# ════════════════════════════════════════════════════════════════

@app.route("/api/orders", methods=["POST"])
@token_required
def place_order():
    if request.user_role != "customer":
        return jsonify({"error": "Only customers can place orders"}), 403

    data = request.get_json() or {}
    for field in ("restaurant_id", "items", "delivery_address"):
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    items = data["items"]   # [{name, price, qty}, ...]
    if not isinstance(items, list) or len(items) == 0:
        return jsonify({"error": "items must be a non-empty list"}), 400

    try:
        sanitized_items = []
        subtotal = 0.0
        for item in items:
            name = str(item.get("name", "")).strip()
            price = float(item.get("price", 0))
            qty = int(item.get("qty", 0))
            if not name or price <= 0 or qty <= 0:
                return jsonify({"error": "Each item must include valid name, price, and qty"}), 400
            sanitized_items.append({"name": name, "price": price, "qty": qty})
            subtotal += price * qty
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid item values supplied"}), 400

    fee      = 30.0
    tax      = round(subtotal * 0.05, 2)
    total    = subtotal + fee + tax

    try:
        rest_oid = ObjectId(data["restaurant_id"])
    except Exception:
        return jsonify({"error": "Invalid restaurant_id"}), 400

    if not restaurants_col.find_one({"_id": rest_oid}):
        return jsonify({"error": "Restaurant not found"}), 404

    doc = {
        "order_number":       f"ORD{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "customer_id":        ObjectId(request.user_id),
        "restaurant_id":      rest_oid,
        "items":              sanitized_items,
        "subtotal":           subtotal,
        "delivery_fee":       fee,
        "tax":                tax,
        "total":              total,
        "delivery_address":   data["delivery_address"],
        "payment_method":     data.get("payment_method", "cash"),
        "status":             "pending",
        "delivery_agent_id":  None,
        "special_instructions": data.get("special_instructions", ""),
        "placed_at":          datetime.utcnow(),
        "updated_at":         datetime.utcnow()
    }
    oid = orders_col.insert_one(doc).inserted_id
    return jsonify({
        "message":          "Order placed successfully",
        "order_id":         str(oid),
        "order_number":     doc["order_number"],
        "total":            total,
        "estimated_delivery": "25–35 minutes"
    }), 201


@app.route("/api/orders", methods=["GET"])
@token_required
def get_orders():
    role = request.user_role

    if role == "customer":
        cursor = orders_col.find({"customer_id": ObjectId(request.user_id)}) \
                           .sort("placed_at", -1).limit(20)

    elif role == "restaurant":
        rest = restaurants_col.find_one({"owner_id": ObjectId(request.user_id)})
        if not rest:
            return jsonify([])
        query = {"restaurant_id": rest["_id"]}
        if request.args.get("status"):
            query["status"] = request.args.get("status")
        cursor = orders_col.find(query).sort("placed_at", -1).limit(50)

    elif role == "delivery":
        agent = delivery_agents_col.find_one({"user_id": ObjectId(request.user_id)})
        if not agent:
            return jsonify([])
        cursor = orders_col.find({"delivery_agent_id": agent["_id"]}) \
                           .sort("placed_at", -1).limit(20)
    else:
        return jsonify({"error": "Unauthorized"}), 403

    result = []
    for order in cursor:
        order = _serialize(order)
        cust  = users_col.find_one({"_id": ObjectId(order["customer_id"])})
        rest  = restaurants_col.find_one({"_id": ObjectId(order["restaurant_id"])})
        if cust:  order["customer_name"]   = cust["name"]
        if rest:  order["restaurant_name"] = rest["name"]
        result.append(order)
    return jsonify(result)


@app.route("/api/orders/<order_id>/status", methods=["PUT"])
@token_required
def update_order_status(order_id):
    data       = request.get_json()
    new_status = data.get("status")
    VALID      = ["pending", "accepted", "preparing", "ready",
                  "out_for_delivery", "delivered", "cancelled"]
    if new_status not in VALID:
        return jsonify({"error": "Invalid status"}), 400

    try:
        order = orders_col.find_one({"_id": ObjectId(order_id)})
    except Exception:
        return jsonify({"error": "Invalid ID"}), 400
    if not order:
        return jsonify({"error": "Order not found"}), 404

    if request.user_role == "restaurant":
        rest = restaurants_col.find_one({"owner_id": ObjectId(request.user_id)})
        if not rest or str(rest["_id"]) != str(order["restaurant_id"]):
            return jsonify({"error": "Unauthorized"}), 403
        if new_status not in ("accepted", "preparing", "ready", "cancelled"):
            return jsonify({"error": "Restaurants can only set: accepted / preparing / ready / cancelled"}), 400

    elif request.user_role == "delivery":
        agent = delivery_agents_col.find_one({"user_id": ObjectId(request.user_id)})
        if not agent:
            return jsonify({"error": "Agent not found"}), 404
        if new_status not in ("out_for_delivery", "delivered"):
            return jsonify({"error": "Delivery agents can only set: out_for_delivery / delivered"}), 400
        if new_status == "out_for_delivery":
            orders_col.update_one({"_id": ObjectId(order_id)},
                                  {"$set": {"delivery_agent_id": agent["_id"]}})
        elif new_status == "delivered":
            delivery_agents_col.update_one({"_id": agent["_id"]},
                                           {"$inc": {"total_deliveries": 1}})

    elif request.user_role == "customer":
        if new_status != "cancelled" or order["status"] != "pending":
            return jsonify({"error": "Customers can only cancel pending orders"}), 400

    orders_col.update_one({"_id": ObjectId(order_id)},
                          {"$set": {"status": new_status, "updated_at": datetime.utcnow()}})
    return jsonify({"message": f"Status updated to '{new_status}'"})


# ════════════════════════════════════════════════════════════════
# DELIVERY AGENT  /api/delivery/*
# ════════════════════════════════════════════════════════════════

@app.route("/api/delivery/available-orders", methods=["GET"])
@token_required
def available_orders():
    if request.user_role != "delivery":
        return jsonify({"error": "Unauthorized"}), 403
    orders = list(orders_col.find({"status": "ready", "delivery_agent_id": None})
                             .sort("placed_at", 1))
    result = []
    for o in orders:
        o = _serialize(o)
        rest = restaurants_col.find_one({"_id": ObjectId(o["restaurant_id"])})
        if rest:
            o["restaurant_name"]    = rest["name"]
            o["restaurant_address"] = rest.get("address", "")
        result.append(o)
    return jsonify(result)


@app.route("/api/delivery/earnings", methods=["GET"])
@token_required
def delivery_earnings():
    if request.user_role != "delivery":
        return jsonify({"error": "Unauthorized"}), 403

    agent = delivery_agents_col.find_one({"user_id": ObjectId(request.user_id)})
    if not agent:
        return jsonify({"error": "Agent not found"}), 404

    today      = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_done = orders_col.count_documents({"delivery_agent_id": agent["_id"],
                                             "status": "delivered",
                                             "updated_at": {"$gte": today}})
    total_done = agent.get("total_deliveries", 0)
    return jsonify({
        "today_deliveries": today_done,
        "today_earnings":   today_done * 40,
        "total_deliveries": total_done,
        "total_earnings":   total_done * 40,
        "rating":           agent.get("rating", 5.0)
    })


@app.route("/api/delivery/profile", methods=["PUT"])
@token_required
def update_agent_profile():
    if request.user_role != "delivery":
        return jsonify({"error": "Unauthorized"}), 403

    data  = request.get_json()
    agent = delivery_agents_col.find_one({"user_id": ObjectId(request.user_id)})
    if not agent:
        return jsonify({"error": "Agent not found"}), 404

    allowed = ["name", "phone", "location", "vehicle_number", "license_id", "is_available"]
    update  = {k: data[k] for k in allowed if k in data}
    delivery_agents_col.update_one({"user_id": ObjectId(request.user_id)}, {"$set": update})

    user_update = {k: update[k] for k in ("name", "phone") if k in update}
    if user_update:
        users_col.update_one({"_id": ObjectId(request.user_id)}, {"$set": user_update})

    return jsonify({"message": "Profile updated"})


# ════════════════════════════════════════════════════════════════
# SEARCH  /api/search
# ════════════════════════════════════════════════════════════════

@app.route("/api/search", methods=["GET"])
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"restaurants": [], "items": []})
    pattern    = {"$regex": q, "$options": "i"}
    restaurants = list(restaurants_col.find(
        {"$or": [{"name": pattern}, {"cuisine": pattern}]}).limit(5))
    items       = list(menu_items_col.find(
        {"name": pattern, "is_available": True}).limit(10))
    return jsonify({
        "restaurants": [_serialize(r) for r in restaurants],
        "items":       [_serialize(i) for i in items]
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)