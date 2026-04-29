import psycopg2
import os
import random
import uuid
from datetime import datetime, timedelta, date
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user":     os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

conn = psycopg2.connect(**DB_CONFIG)
cur  = conn.cursor()
random.seed(42)
today = date(2026, 4, 21)

print("Connected to PostgreSQL...")
# ── Section 1: Seed Zones ────────────────────────────────────
def seed_zones():
    zones = [
    ('A', 'Los Angeles Hub',  'Los Angeles', 'West Coast',
     'Commerce Industrial District, Los Angeles CA',
     33.9902, -118.1553, 250000, 'James Mitchell'),
    ('B', 'Chicago Hub',      'Chicago',     'Midwest',
     'Elk Grove Village Industrial Park, Chicago IL',
     41.9742, -87.9073, 180000, 'Sarah Johnson'),
    ('C', 'Dallas Hub',       'Dallas',      'South Central',
     'DFW Trade Center, Irving TX',
     32.8141, -96.9489, 220000, 'Michael Rodriguez'),
    ('D', 'New York Hub',     'New York',    'East Coast',
     'Meadowlands Distribution Center, NJ',
     40.8140, -74.0776, 300000, 'Emily Chen'),
    ('E', 'Atlanta Hub',      'Atlanta',     'Southeast',
     'Fulton Industrial Boulevard, Atlanta GA',
     33.7490, -84.5466, 200000, 'David Williams'),
    ]

    cur.execute("DELETE FROM zones")
    cur.executemany("""
        INSERT INTO zones VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, zones)
    print(f"✅ Zones seeded — {len(zones)} zones")

seed_zones()

# ── Section 2: Seed Inventory ────────────────────────────────
def seed_inventory():
    categories = {
    "Beverages":     ["Coca-Cola 500ml","Pepsi 500ml","Sprite 500ml",
                      "Gatorade 32oz","Red Bull 8.4oz","Tropicana OJ 52oz",
                      "Mountain Dew 500ml","Dr Pepper 500ml",
                      "Lipton Iced Tea 64oz","Monster Energy 16oz",
                      "Snapple Tea 16oz","Arizona Green Tea 23oz",
                      "Powerade 32oz","Vitamin Water 20oz",
                      "Sparkling Ice 17oz","LaCroix Sparkling 12pk",
                      "Honest Tea 16oz","Starbucks Frappuccino 13.7oz"],
    "Snacks":        ["Lays Classic 8oz","Doritos Nacho 9.25oz",
                      "Pringles Original 5.57oz","Cheetos Crunchy 8oz",
                      "Oreo Cookies 14.3oz","Ritz Crackers 13.7oz",
                      "Goldfish Crackers 6.6oz","Cheez-It 12.4oz",
                      "Pop-Tarts 8ct","Nature Valley Bars 6ct",
                      "Clif Bar 6ct","Kind Bar 12ct",
                      "Skinny Pop Popcorn 4.4oz","SunChips 7oz",
                      "Triscuit Crackers 8.5oz","Wheat Thins 9.1oz",
                      "Pretzel Crisps 7.2oz","Rice Krispies Treats 8ct"],
    "Personal Care": ["Head & Shoulders 13.5oz","Dove Body Wash 22oz",
                      "Colgate Toothpaste 6oz","Pantene Shampoo 12oz",
                      "Nivea Body Lotion 16.9oz","Dove Soap Bar 4pk",
                      "Degree Deodorant 2.6oz","Neutrogena Face Wash 6oz",
                      "Gillette Fusion 4ct","Vaseline Lotion 20.3oz",
                      "Olay Moisturizer 4oz","TRESemme Conditioner 28oz",
                      "Crest Whitening Strips 14ct","Listerine 1L",
                      "Axe Body Spray 4oz","Old Spice Deodorant 3oz",
                      "Aveeno Lotion 18oz","Cetaphil Cleanser 16oz"],
    "Household":     ["Tide Pods 42ct","Dawn Dish Soap 19.4oz",
                      "Lysol Spray 19oz","Bounty Paper Towels 8pk",
                      "Charmin TP 12pk","Febreze Air 8.8oz",
                      "Windex Glass Cleaner 26oz","Glad Trash Bags 40ct",
                      "Swiffer Sweeper Refills 16ct","Clorox Wipes 75ct",
                      "Ziploc Bags Gallon 30ct","Reynolds Wrap 75sqft",
                      "Mr Clean Magic Eraser 4ct","Pine-Sol 48oz",
                      "Cascade Dishwasher Pods 30ct","Arm & Hammer Detergent 4.75lb",
                      "Scotch-Brite Sponges 6ct","Hefty Trash Bags 38ct"],
    "Dairy":         ["Horizon Whole Milk 1gal","Land O Lakes Butter 1lb",
                      "Chobani Greek Yogurt 32oz","Kraft Singles 24ct",
                      "Philadelphia Cream Cheese 8oz",
                      "Daisy Sour Cream 16oz","Breakstone Cottage Cheese 16oz",
                      "Tillamook Cheddar 16oz","Laughing Cow Cheese 6oz",
                      "Silk Almond Milk 64oz","Oatly Oat Milk 64oz",
                      "Yoplait Yogurt 6oz","Babybel Cheese 6ct",
                      "International Delight Creamer 32oz",
                      "Cool Whip 8oz","Reddi Whip 6.5oz",
                      "Blue Diamond Almond Milk 96oz","Fairlife Milk 52oz"],
    "Staples":       ["King Arthur Flour 5lb","Crisco Vegetable Oil 48oz",
                      "Morton Salt 26oz","Uncle Ben's Rice 5lb",
                      "McCormick Black Pepper 3oz","Heinz Ketchup 32oz",
                      "Hellmann's Mayo 30oz","Campbell's Soup 10.75oz",
                      "Quaker Oats 42oz","Skippy Peanut Butter 40oz",
                      "Jif Peanut Butter 40oz","Smucker's Strawberry Jam 18oz",
                      "Hunt's Tomato Sauce 29oz","Kraft Mac & Cheese 7.25oz",
                      "Barilla Pasta 16oz","Bertolli Olive Oil 16.9oz",
                      "Domino Sugar 4lb","Arm & Hammer Baking Soda 4lb"],
}
    zone_demand_multiplier = {
    'A': {'Beverages':1.4,'Snacks':1.1,'Personal Care':1.3,
          'Household':1.0,'Dairy':0.8,'Staples':0.9},  # LA — hot, high beverage/personal care
    'B': {'Beverages':0.9,'Snacks':1.1,'Personal Care':1.0,
          'Household':1.2,'Dairy':1.3,'Staples':1.1},  # Chicago — cold, high dairy/household
    'C': {'Beverages':1.2,'Snacks':1.3,'Personal Care':1.0,
          'Household':1.0,'Dairy':0.9,'Staples':1.1},  # Dallas — high snacks/beverages
    'D': {'Beverages':1.0,'Snacks':1.0,'Personal Care':1.2,
          'Household':1.1,'Dairy':1.0,'Staples':1.3},  # New York — high staples/personal care
    'E': {'Beverages':1.1,'Snacks':1.0,'Personal Care':1.1,
          'Household':1.2,'Dairy':1.1,'Staples':1.0},  # Atlanta — balanced, high household
}

    suppliers = {
        "Beverages":     ["PepsiCo North America","Coca-Cola Distributors",
                        "Red Bull Distribution"],
        "Snacks":        ["Frito-Lay Inc","Mondelez International",
                        "Kellogg's Distribution"],
        "Personal Care": ["Procter & Gamble","Unilever US",
                        "Colgate-Palmolive"],
        "Household":     ["Procter & Gamble","SC Johnson",
                        "Reckitt Benckiser US"],
        "Dairy":         ["Dean Foods","Land O Lakes Co-op",
                        "Chobani LLC"],
        "Staples":       ["ConAgra Foods","B&G Foods",
                        "Campbell Soup Co"],
                    }

    rows = []
    sku_counter = 1001

    for cat, products in categories.items():
        for product in products:
            sku_id = f"SK-{sku_counter}"
            for zone_id in ['A','B','C','D','E']:
                # Zone specific demand
                multiplier = zone_demand_multiplier[zone_id][cat]
                base_demand = random.randint(8, 50)
                demand = max(1, int(base_demand * multiplier))
                lead   = random.randint(2, 10)
                rop    = demand * lead

                # Mix of stock levels — critical, warning, healthy
                roll = random.random()
                if roll < 0.15:
                    stock = random.randint(0, int(rop * 0.4))
                elif roll < 0.35:
                    stock = random.randint(int(rop*0.4), rop)
                else:
                    stock = random.randint(rop, int(rop * 2.5))

                days_of_stock  = round(stock / demand, 1)
                reorder_qty    = max(0, int(rop * 1.5) - stock)
                unit_cost      = round(random.uniform(15, 450), 2)

                # Urgency classification — Python decides
                if stock < rop * 0.5:
                    status = "CRITICAL"
                    action = f"ORDER NOW — {max(0, round(lead - days_of_stock, 1))} days overdue"
                elif stock < rop:
                    status = "WARNING"
                    action = "Reorder soon"
                else:
                    status = "HEALTHY"
                    action = "OK"

                rows.append((
                    sku_id, zone_id, product, cat,
                    stock, rop, demand, lead,
                    random.choice(suppliers[cat]),
                    unit_cost, days_of_stock, reorder_qty,
                    status, action,
                    datetime.now()
                ))
            sku_counter += 1

    cur.execute("DELETE FROM inventory")
    cur.executemany("""
        INSERT INTO inventory VALUES
        (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, rows)
    print(f"✅ Inventory seeded — {len(rows)} records across 5 zones")

seed_inventory()

# ── Section 3: Seed Transport ────────────────────────────────
def seed_transport():

    # Each zone has specific nearby customer hubs it serves
    zone_routes = {
        'A': [('Los Angeles WH','San Diego Hub',120),
              ('Los Angeles WH','Phoenix Hub',370),
              ('Los Angeles WH','Las Vegas Hub',270),
              ('Los Angeles WH','Fresno Hub',220),
              ('Los Angeles WH','San Jose Hub',340),
              ('Los Angeles WH','Sacramento Hub',380),
              ('Los Angeles WH','Bakersfield Hub',170),
              ('Los Angeles WH','Riverside Hub',80)],
        'B': [('Chicago WH','Milwaukee Hub',90),
              ('Chicago WH','Indianapolis Hub',180),
              ('Chicago WH','Detroit Hub',280),
              ('Chicago WH','St Louis Hub',300),
              ('Chicago WH','Minneapolis Hub',410),
              ('Chicago WH','Columbus Hub',350),
              ('Chicago WH','Cincinnati Hub',300),
              ('Chicago WH','Kansas City Hub',510)],
        'C': [('Dallas WH','Houston Hub',240),
              ('Dallas WH','San Antonio Hub',280),
              ('Dallas WH','Austin Hub',195),
              ('Dallas WH','Oklahoma City Hub',200),
              ('Dallas WH','Memphis Hub',470),
              ('Dallas WH','New Orleans Hub',510),
              ('Dallas WH','Little Rock Hub',320),
              ('Dallas WH','Shreveport Hub',190)],
        'D': [('New York WH','Boston Hub',215),
              ('New York WH','Philadelphia Hub',95),
              ('New York WH','Baltimore Hub',185),
              ('New York WH','Washington DC Hub',225),
              ('New York WH','Hartford Hub',115),
              ('New York WH','Providence Hub',180),
              ('New York WH','Albany Hub',145),
              ('New York WH','Pittsburgh Hub',370)],
        'E': [('Atlanta WH','Charlotte Hub',245),
              ('Atlanta WH','Nashville Hub',250),
              ('Atlanta WH','Birmingham Hub',145),
              ('Atlanta WH','Jacksonville Hub',340),
              ('Atlanta WH','Memphis Hub',395),
              ('Atlanta WH','Chattanooga Hub',115),
              ('Atlanta WH','Savannah Hub',250),
              ('Atlanta WH','Greenville Hub',145)],
    }

    carriers = ["FedEx Freight","UPS Supply Chain",
                "XPO Logistics","J.B. Hunt Transport",
                "Werner Enterprises","Old Dominion Freight",
                "Schneider National","Swift Transportation"]
    modes    = ["Road FTL","Road LTL","Rail","Air Express"]

    rows = []
    lane_counter = 3001

    for zone_id, routes in zone_routes.items():
        for origin, destination, distance in routes:
            carrier      = random.choice(carriers)
            mode         = random.choice(modes)
            planned_tt   = max(1, round(distance / 400))
            actual_tt    = planned_tt + random.choice([-1,0,0,0,1,1,2,3])
            actual_tt    = max(1, actual_tt)
            on_time      = actual_tt <= planned_tt
            delay_days   = max(0, actual_tt - planned_tt)
            cost_per_kg  = round(random.uniform(0.5, 8.5), 2)
            damage_rate  = round(random.uniform(0, 4.5), 2)
            perf_score   = round(
                (0.4 * (1 if on_time else 0) * 100) +
                (0.3 * max(0, 100 - damage_rate * 20)) +
                (0.3 * max(0, 100 - delay_days * 15)), 1
            )

            rows.append((
                f"LN-{lane_counter}", zone_id,
                origin, destination, carrier, mode, distance,
                planned_tt, actual_tt, on_time, delay_days,
                cost_per_kg, damage_rate, perf_score,
                datetime.now()
            ))
            lane_counter += 1

    cur.execute("DELETE FROM transport")
    cur.executemany("""
        INSERT INTO transport VALUES
        (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, rows)
    print(f"✅ Transport seeded — {len(rows)} lanes across 5 zones")

seed_transport()

# ── Section 4: Seed Shipments ────────────────────────────────
def seed_shipments():

    # Each zone ships to its nearby customer hubs
    zone_customers = {
        'A': ["Walmart San Diego","Target Phoenix","Costco Las Vegas",
              "Kroger Fresno","Safeway San Jose","Albertsons Sacramento"],
        'B': ["Walmart Milwaukee","Target Indianapolis","Costco Detroit",
              "Kroger St Louis","Meijer Minneapolis","Giant Eagle Columbus"],
        'C': ["Walmart Houston","Target San Antonio","Costco Austin",
              "Kroger Oklahoma City","HEB Memphis","Winn-Dixie New Orleans"],
        'D': ["Walmart Boston","Target Philadelphia","Costco Baltimore",
              "Kroger Washington DC","Stop & Shop Hartford","Shaw's Providence"],
        'E': ["Walmart Charlotte","Target Nashville","Costco Birmingham",
              "Kroger Jacksonville","Publix Memphis","Winn-Dixie Savannah"],
    }

    carriers = ["FedEx Freight","UPS Supply Chain","XPO Logistics",
                "J.B. Hunt Transport","Old Dominion Freight",
                "Schneider National"]

    statuses = ["In Transit","In Transit","In Transit","Delivered",
                "Delivered","Delayed","Delayed","Out for Delivery",
                "Held at Hub","Lost in Transit"]

    categories = ["Beverages","Snacks","Personal Care",
                  "Household","Dairy","Staples"]

    rows = []
    shipment_counter = 5001

    for zone_id, customers in zone_customers.items():
        # 24 shipments per zone = 120 total
        for i in range(24):
            status       = random.choice(statuses)
            dispatch     = date(2026, 4, 21) - timedelta(days=random.randint(1,14))
            planned_del  = dispatch + timedelta(days=random.randint(2,8))

            if status == "Delivered":
                actual_del = planned_del + timedelta(days=random.randint(-1,2))
                delay_days = max(0,(actual_del - planned_del).days)
            else:
                actual_del = None
                delay_days = max(0,(date(2026,4,21) - planned_del).days)

            # Pick a lane from transport table for this zone
            lane_id = f"LN-{3001 + list(zone_customers.keys()).index(zone_id) * 8 + (i % 8)}"

            rows.append((
                f"SHP-{shipment_counter}",
                f"ORD-{8001 + shipment_counter}",
                zone_id,
                lane_id,
                f"{['Los Angeles','Chicago','Dallas','New York','Atlanta'][list(zone_customers.keys()).index(zone_id)]} WH",
                random.choice(customers),
                random.choice(categories),
                random.choice(carriers),
                status,
                dispatch,
                planned_del,
                actual_del,
                delay_days,
                round(random.uniform(50, 800), 1),
                round(random.uniform(2000, 150000), 2),
                status == "Delivered" and random.random() > 0.1,
                datetime.now()
            ))
            shipment_counter += 1

    cur.execute("DELETE FROM shipments")
    cur.executemany("""
        INSERT INTO shipments VALUES
        (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, rows)
    print(f"✅ Shipments seeded — {len(rows)} shipments across 5 zones")

seed_shipments()

# ── Section 5: Seed Sales History (90 days) ─────────────────
def seed_sales():

    channels = ["In-Store","Online","Wholesale","B2B"]

    rows = []
    sale_counter = 1

    # Get all SKUs from inventory
    cur.execute("""
        SELECT DISTINCT sku_id, product_name, category, 
               zone_id, avg_daily_demand, unit_cost_usd
        FROM inventory
    """)
    skus = cur.fetchall()


    for sku_id, product, category, zone_id, avg_demand, unit_cost in skus:
        for day in range(90):
            sale_date = date(2026, 4, 21) - timedelta(days=day)

            # Weekend spike — 30% more sales on weekends
            is_weekend = sale_date.weekday() >= 5
            weekend_mult = 1.3 if is_weekend else 1.0

            # Promotion flag — random 10% of days
            promotion = random.random() < 0.1
            promo_mult = 1.5 if promotion else 1.0

            # Daily quantity sold
            qty = max(1, int(
                avg_demand * weekend_mult * promo_mult *
                random.uniform(0.7, 1.3)
            ))

            price = round(unit_cost * random.uniform(1.2, 1.8), 2)

            rows.append((
                f"SL-{sale_counter:07d}",
                zone_id,
                sku_id,
                product,
                category,
                qty,
                sale_date,
                random.choice(["Walmart","Target","Costco",
                               "Kroger","Safeway","Publix"]),
                random.choice(channels),
                price,
                promotion,
                datetime.now()
            ))
            sale_counter += 1

    cur.execute("DELETE FROM sales")
    cur.executemany("""
        INSERT INTO sales VALUES
        (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, rows)
    print(f"✅ Sales seeded — {len(rows):,} records (90 days × all SKUs)")

seed_sales()

# ── Section 6: Seed Forecasts (30-day rolling average) ───────
def seed_forecasts():

    rows = []
    forecast_counter = 1

    # Get sales history per SKU per zone
    cur.execute("""
        SELECT 
            zone_id,
            sku_id,
            AVG(quantity_sold) as avg_30d,
            STDDEV(quantity_sold) as std_30d
        FROM sales
        WHERE sale_date >= DATE '2026-03-22'  -- last 30 days
        GROUP BY zone_id, sku_id
    """)
    sales_data = cur.fetchall()

    forecast_date = date(2026, 4, 21)

    for zone_id, sku_id, avg_30d, std_30d in sales_data:
        std_30d = std_30d or 0

        # Rolling average forecast
        forecasted = round(avg_30d, 1)

        # Upper and lower bounds — 1 standard deviation
        upper = round(avg_30d + std_30d, 1)
        lower = round(max(0, avg_30d - std_30d), 1)

        rows.append((
            f"FC-{forecast_counter:06d}",
            zone_id,
            sku_id,
            forecast_date,
            forecasted,
            round(avg_30d, 1),
            upper,
            lower,
            datetime.now()
        ))
        forecast_counter += 1

    cur.execute("DELETE FROM forecasts")
    cur.executemany("""
        INSERT INTO forecasts VALUES
        (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, rows)
    print(f"✅ Forecasts seeded — {len(rows):,} records")

seed_forecasts()

conn.commit()
cur.close()
conn.close()
print("All data committed and connection closed")