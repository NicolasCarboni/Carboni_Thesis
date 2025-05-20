import csv
import random
from datetime import datetime, timedelta
import os

def generate_CSV_2(num_rows, seed, output_file="GHGe2.csv"):
    # Ensure the output directory exists
    output_dir = os.path.join("data", "uploaded")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, output_file)

    start_date = datetime(2020, 1, 1)
    random. seed(seed)

    cities = [
        ("Milan", "Italy"), ("Rome", "Italy"), ("Naples", "Italy"), ("Florence", "Italy"), ("Venice", "Italy"),
        ("Paris", "France"), ("Lyon", "France"), ("Marseille", "France"), ("Bordeaux", "France"), ("Nice", "France"),
        ("Berlin", "Germany"), ("Munich", "Germany"), ("Hamburg", "Germany"), ("Cologne", "Germany"), ("Frankfurt", "Germany"),
        ("Tokyo", "Japan"), ("Osaka", "Japan"), ("Kyoto", "Japan"), ("Nagoya", "Japan"), ("Fukuoka", "Japan")
    ]

    products = [
        ("Basic T-shirt", "T-shirt"), ("Graphic T-shirt", "T-shirt"), ("Slim Fit Jeans", "Jeans"), ("Relaxed Fit Jeans", "Jeans"),
        ("Bomber Jacket", "Jacket"), ("Light Jacket", "Jacket"), ("Running Shoes", "Shoes"), ("Leather Boots", "Shoes"),
        ("Wool Scarf", "Accessories"), ("Baseball Cap", "Accessories"), ("Denim Jacket", "Jacket"), ("Oversized Hoodie", "T-shirt"),
        ("Cargo Pants", "Jeans"), ("Canvas Sneakers", "Shoes"), ("Raincoat", "Jacket"), ("Beanie", "Accessories"),
        ("Polo Shirt", "T-shirt"), ("Chino Pants", "Jeans"), ("Ankle Boots", "Shoes"), ("Leather Belt", "Accessories")
    ]

    # Product base info
    data = []
    for _ in range(num_rows):
        random_date = start_date + timedelta(days=random.randint(0, 1825))  # Random date within 5 years
        city, state = random.choice(cities)
        product, category = random.choice(products)
        quantity = random.randint(1, 50)

        row ={
            "Date": random_date.strftime("%Y-%m-%d"),
            "Product Name": product,
            "Category": category,
            "City": city,
            "State": state,
            "Quantity": quantity
        }
        data.append(row)

    # Write CSV
    filename = "GHGe2.csv"
    with open(output_file, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "Date",
            "Product Name",
            "Category",
            "City",
            "Country",
            "Emissions Raw Materials per unit (kgCO₂e)",
            "Emissions Manufacturing per unit (kgCO₂e)",
            "Emissions Transport per unit (kgCO₂e)",
            "Total Emissions per unit (kgCO₂e)",
            "Quantity",
            "Total Emissions (kgCO₂e)",
        ])

        for row in data:
            e_rawm = round(random.uniform(1.0, 5.0), 2)  # Emissions from raw materials
            e_man = round(random.uniform(2.0, 7.0), 2)  # Emissions from manufacturing
            e_transp = round(random.uniform(0.5, 4.0), 2)  # Emissions from transport
            e_tot_unit = round(e_rawm + e_man + e_transp, 2)  # Total emissions per unit
            e_tot = round(e_tot_unit * row["Quantity"], 2)  # Total emissions for the quantity sold

            writer.writerow([
                row["Date"],
                row["Product Name"],
                row["Category"],
                row["City"],
                row["State"],
                e_rawm,
                e_man,
                e_transp,
                e_tot_unit,
                row["Quantity"],
                e_tot,
            ])

    print(f"CSV generated: {filename}")
