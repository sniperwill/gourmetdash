from db import (users_col, restaurants_col,
                menu_items_col, orders_col, delivery_agents_col)
from flask_bcrypt import generate_password_hash
from datetime import datetime, timedelta
from bson import ObjectId
import random

def seed():
    print("Clearing collections...")
    for col in (users_col, restaurants_col, menu_items_col,
                orders_col, delivery_agents_col):
        col.delete_many({})

    pw = generate_password_hash("password123").decode("utf-8")

    # ── Customers ────────────────────────────────────────────────
    customers_raw = [
        {"name": "Ravi Kumar",    "email": "ravi@example.com",   "phone": "+91 9000000001"},
        {"name": "Priya Nair",    "email": "priya@example.com",  "phone": "+91 9000000002"},
        {"name": "Amit Shah",     "email": "amit@example.com",   "phone": "+91 9000000003"},
        {"name": "Sunita Verma",  "email": "sunita@example.com", "phone": "+91 9000000004"},
    ]
    cust_ids = []
    for c in customers_raw:
        cust_ids.append(users_col.insert_one(
            {**c, "password": pw, "role": "customer", "created_at": datetime.utcnow()}
        ).inserted_id)

    # ── Restaurant owners ─────────────────────────────────────────
    owners_raw = [
        {"name": "Rajesh Sharma",  "email": "rajesh@tajmahal.com",  "phone": "+91 9000000010"},
        {"name": "Lakshmi Devi",   "email": "lakshmi@southern.com", "phone": "+91 9000000011"},
        {"name": "Joseph Pereira", "email": "joseph@coastal.com",   "phone": "+91 9000000012"},
        {"name": "Mohammed Khan",  "email": "khan@biryani.com",     "phone": "+91 9000000013"},
        {"name": "Marco Ferrari",  "email": "marco@pizzahub.com",   "phone": "+91 9000000014"},
        {"name": "Chen Wei",       "email": "chen@wokstory.com",    "phone": "+91 9000000015"},
    ]
    owner_ids = []
    for o in owners_raw:
        owner_ids.append(users_col.insert_one(
            {**o, "password": pw, "role": "restaurant", "created_at": datetime.utcnow()}
        ).inserted_id)

    # ── Delivery agents ───────────────────────────────────────────
    agents_raw = [
        {"name": "Rahul Kumar",  "email": "rahul@delivery.com",  "phone": "+91 9000000020"},
        {"name": "Suresh Yadav", "email": "suresh@delivery.com", "phone": "+91 9000000021"},
    ]
    agent_user_ids = []
    for a in agents_raw:
        agent_user_ids.append(users_col.insert_one(
            {**a, "password": pw, "role": "delivery", "created_at": datetime.utcnow()}
        ).inserted_id)

    agent_ids = []
    for i, uid in enumerate(agent_user_ids):
        agent_ids.append(delivery_agents_col.insert_one({
            "user_id":          uid,
            "name":             agents_raw[i]["name"],
            "phone":            agents_raw[i]["phone"],
            "location":         "Bangalore, Karnataka",
            "vehicle_number":   f"KA01AB{1000 + i}",
            "license_id":       f"DL 1234{i}",
            "is_available":     True,
            "rating":           round(4.7 + random.random() * 0.3, 1),
            "total_deliveries": random.randint(50, 200),
            "created_at":       datetime.utcnow()
        }).inserted_id)

    # ── Restaurants ───────────────────────────────────────────────
    restaurants_data = [
        dict(name="Taj Mahal Restaurant", owner_id=owner_ids[0],  cuisine="North Indian", cuisine_tag="north",   emoji="🍖", address="Building 10, MG Road, Bangalore – 560025",       rating=4.7, review_count=891,  is_open=True,  open_time="09:00", close_time="23:00", min_order=199, delivery_time="30–35 min", min_delivery_mins=30, tags=["Bestseller"]),
        dict(name="Southern Spice",       owner_id=owner_ids[1],  cuisine="South Indian", cuisine_tag="south",   emoji="🥘", address="12 Anna Salai, Chennai – 600002",               rating=4.5, review_count=342,  is_open=True,  open_time="07:00", close_time="22:00", min_order=149, delivery_time="20–25 min", min_delivery_mins=20, tags=["Pure Veg"]),
        dict(name="Coastal Catch",        owner_id=owner_ids[2],  cuisine="Seafood",      cuisine_tag="coastal", emoji="🐟", address="8 Marine Drive, Mumbai – 400020",               rating=4.3, review_count=213,  is_open=True,  open_time="11:00", close_time="23:00", min_order=299, delivery_time="35–40 min", min_delivery_mins=35, tags=["New"]),
        dict(name="Biryani Palace",       owner_id=owner_ids[3],  cuisine="Mughlai",      cuisine_tag="mughlai", emoji="🍛", address="45 Park Street, Kolkata – 700016",              rating=4.6, review_count=1200, is_open=True,  open_time="10:00", close_time="23:30", min_order=149, delivery_time="20–25 min", min_delivery_mins=20, tags=["Most Ordered"]),
        dict(name="Pizza Hub",            owner_id=owner_ids[4],  cuisine="Italian",      cuisine_tag="italian", emoji="🍕", address="7 FC Road, Pune – 411004",                     rating=4.2, review_count=567,  is_open=True,  open_time="11:00", close_time="23:00", min_order=249, delivery_time="40–50 min", min_delivery_mins=40, tags=["30% Off"]),
        dict(name="The Wok Story",        owner_id=owner_ids[5],  cuisine="Chinese",      cuisine_tag="chinese", emoji="🍜", address="22 Linking Road, Bandra, Mumbai – 400050",     rating=4.4, review_count=432,  is_open=True,  open_time="12:00", close_time="23:00", min_order=199, delivery_time="25–30 min", min_delivery_mins=25, tags=["Trending"]),
    ]
    rest_ids = []
    for r in restaurants_data:
        rest_ids.append(restaurants_col.insert_one(
            {**r, "created_at": datetime.utcnow()}
        ).inserted_id)

    # ── Menu items ────────────────────────────────────────────────
    taj_id   = rest_ids[0]
    south_id = rest_ids[1]

    items = [
        # Taj Mahal
        dict(name="Masala Dosa",          price=120, category="Bestsellers",  type="veg",     emoji="🍳", description="Crispy rice crepe filled with spiced potato masala",                       restaurant_id=taj_id),
        dict(name="Veg Biryani",          price=220, category="Bestsellers",  type="veg",     emoji="🍚", description="Fragrant basmati rice with seasonal vegetables and whole spices",          restaurant_id=taj_id),
        dict(name="Chicken Tikka",        price=320, category="Bestsellers",  type="non-veg", emoji="🍗", description="Tender marinated chicken grilled in tandoor, with mint chutney",           restaurant_id=taj_id),
        dict(name="Onion Bhaji",          price=90,  category="Starters",     type="veg",     emoji="🧅", description="Crispy golden onion fritters with green coriander dip",                    restaurant_id=taj_id),
        dict(name="Seekh Kebab",          price=280, category="Starters",     type="non-veg", emoji="🍢", description="Minced lamb kebabs on skewers, flame-grilled with spices",                 restaurant_id=taj_id),
        dict(name="Filter Coffee",        price=60,  category="Drinks",       type="veg",     emoji="☕", description="Traditional South Indian filter coffee, strong and aromatic",              restaurant_id=taj_id),
        dict(name="Mango Lassi",          price=80,  category="Drinks",       type="veg",     emoji="🥛", description="Chilled yogurt drink with fresh Alphonso mango pulp",                     restaurant_id=taj_id),
        dict(name="Butter Chicken",       price=380, category="Main Course",  type="non-veg", emoji="🍛", description="Rich tomato-based curry with tender chicken pieces",                       restaurant_id=taj_id),
        dict(name="Paneer Butter Masala", price=280, category="Main Course",  type="veg",     emoji="🧀", description="Soft paneer cubes in creamy tomato-cashew gravy",                         restaurant_id=taj_id),
        dict(name="Garlic Naan",          price=45,  category="Breads",       type="veg",     emoji="🫓", description="Leavened flatbread baked in tandoor with garlic and butter",              restaurant_id=taj_id),
        # Southern Spice
        dict(name="Idli Sambar",          price=80,  category="Breakfast",    type="veg",     emoji="🍱", description="Steamed rice cakes with lentil soup and chutneys",                        restaurant_id=south_id),
        dict(name="Rava Dosa",            price=100, category="Bestsellers",  type="veg",     emoji="🥞", description="Crispy semolina crepe with coconut chutney",                              restaurant_id=south_id),
        dict(name="Chettinad Chicken",    price=340, category="Main Course",  type="non-veg", emoji="🍗", description="Spicy authentic Chettinad style chicken curry",                           restaurant_id=south_id),
        dict(name="Pongal",               price=90,  category="Breakfast",    type="veg",     emoji="🍲", description="Slow-cooked rice and lentil porridge with ghee and pepper",               restaurant_id=south_id),
    ]
    # Generic items for remaining restaurants
    for i, rid in enumerate(rest_ids[2:], 2):
        items += [
            dict(name="House Special",    price=250 + i*20, category="Bestsellers", type="non-veg", emoji="⭐", description="Chef's special dish",              restaurant_id=rid),
            dict(name="Veg Combo",        price=180 + i*10, category="Combos",      type="veg",     emoji="🥗", description="Wholesome vegetarian combo meal",   restaurant_id=rid),
            dict(name="Signature Drink",  price=80,         category="Drinks",      type="veg",     emoji="🥤", description="Our signature refreshing drink",    restaurant_id=rid),
        ]

    for item in items:
        menu_items_col.insert_one({**item, "is_available": True, "created_at": datetime.utcnow()})

    # ── Sample orders (matching HTML table) ───────────────────────
    now = datetime.utcnow()
    sample_orders = [
        dict(order_number="ORD001", customer_id=cust_ids[0], restaurant_id=taj_id,
             items=[{"name": "Masala Dosa", "price": 120, "qty": 1}, {"name": "Filter Coffee", "price": 60, "qty": 1}],
             subtotal=180, delivery_fee=30, tax=9, total=219,
             delivery_address="Sector 7, Whitefield, Bangalore – 560066",
             payment_method="cash", status="pending", delivery_agent_id=None,
             placed_at=now - timedelta(minutes=26), updated_at=now - timedelta(minutes=26)),

        dict(order_number="ORD002", customer_id=cust_ids[1], restaurant_id=taj_id,
             items=[{"name": "Chicken Tikka", "price": 320, "qty": 1},
                    {"name": "Veg Biryani",   "price": 220, "qty": 1},
                    {"name": "Mango Lassi",   "price":  80, "qty": 1}],
             subtotal=620, delivery_fee=30, tax=31, total=681,
             delivery_address="Building 2, Park Road, Kolkata – 700031",
             payment_method="upi", status="preparing", delivery_agent_id=agent_ids[0],
             placed_at=now - timedelta(minutes=41), updated_at=now - timedelta(minutes=10)),

        dict(order_number="ORD003", customer_id=cust_ids[2], restaurant_id=taj_id,
             items=[{"name": "Seekh Kebab", "price": 280, "qty": 1},
                    {"name": "Onion Bhaji", "price":  90, "qty": 1}],
             subtotal=370, delivery_fee=30, tax=18, total=418,
             delivery_address="HSR Layout, Bangalore – 560102",
             payment_method="card", status="out_for_delivery", delivery_agent_id=agent_ids[0],
             placed_at=now - timedelta(minutes=58), updated_at=now - timedelta(minutes=5)),

        dict(order_number="ORD004", customer_id=cust_ids[3], restaurant_id=taj_id,
             items=[{"name": "Veg Biryani", "price": 220, "qty": 2}],
             subtotal=440, delivery_fee=30, tax=22, total=492,
             delivery_address="Jayanagar, Bangalore – 560041",
             payment_method="upi", status="delivered", delivery_agent_id=agent_ids[1],
             placed_at=now - timedelta(hours=1, minutes=15), updated_at=now - timedelta(minutes=30)),
    ]
    for o in sample_orders:
        orders_col.insert_one({**o, "special_instructions": ""})

    print("\n✅  Database seeded!")
    print("=" * 42)
    print("  Customer:   ravi@example.com")
    print("  Restaurant: rajesh@tajmahal.com")
    print("  Delivery:   rahul@delivery.com")
    print("  Password:   password123 (all accounts)")
    print("=" * 42)

if __name__ == "__main__":
    seed()