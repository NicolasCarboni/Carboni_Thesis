import csv
import random
from datetime import datetime, timedelta
import os

def generate_clothing_emissions_data_1(num_rows, seed, output_file="GHGe1.csv"):
    # Ensure the output directory exists
    output_dir = os.path.join("data", "uploaded")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, output_file)

    start_date = datetime(2020, 1, 1)
    random.seed(seed)

    # Sample product data
    products = [
        {"name": "Basic T-shirt", "category": "T-shirt", "material": "Cotton", "unit_emission": 2.1},
        {"name": "Slim Fit Jeans", "category": "Jeans", "material": "Denim", "unit_emission": 6.5},
        {"name": "Oversized Hoodie", "category": "Sweatshirt", "material": "Cotton", "unit_emission": 4.2},
        {"name": "Light Jacket", "category": "Jacket", "material": "Polyester", "unit_emission": 8.9},
        {"name": "Cargo Pants", "category": "Pants", "material": "Cotton", "unit_emission": 5.1},
        {"name": "Denim Jacket", "category": "Jacket", "material": "Denim", "unit_emission": 7.8},
        {"name": "Printed T-shirt", "category": "T-shirt", "material": "Organic Cotton", "unit_emission": 1.9},
        {"name": "Chino Pants", "category": "Pants", "material": "Cotton", "unit_emission": 4.7},
        {"name": "Running Shoes", "category": "Shoes", "material": "Synthetic", "unit_emission": 9.5},
        {"name": "Leather Boots", "category": "Shoes", "material": "Leather", "unit_emission": 11.0},
        {"name": "Summer Dress", "category": "Dress", "material": "Linen", "unit_emission": 3.3},
        {"name": "Winter Coat", "category": "Jacket", "material": "Wool", "unit_emission": 10.2},
        {"name": "Knitted Sweater", "category": "Sweater", "material": "Wool", "unit_emission": 6.0},
        {"name": "Raincoat", "category": "Jacket", "material": "Polyester", "unit_emission": 7.4},
        {"name": "Tank Top", "category": "T-shirt", "material": "Cotton", "unit_emission": 1.8},
        {"name": "Formal Shirt", "category": "Shirt", "material": "Cotton", "unit_emission": 3.9},
        {"name": "Tracksuit Pants", "category": "Pants", "material": "Polyester", "unit_emission": 6.3},
        {"name": "Zip Hoodie", "category": "Sweatshirt", "material": "Cotton", "unit_emission": 4.5},
        {"name": "Slip-On Sneakers", "category": "Shoes", "material": "Canvas", "unit_emission": 5.7},
        {"name": "Shorts", "category": "Shorts", "material": "Denim", "unit_emission": 3.5}
    ]

    # Generate the data
    data = []
    for _ in range(num_rows):
        random_date = start_date + timedelta(days=random.randint(0, 1825))  # Random date within 5 years
        product = random.choice(products)
        quantity = random.randint(1, 100)
        unit_emission = product["unit_emission"]
        total_emission = round(unit_emission * quantity, 2)

        row = {
            "Date": random_date.strftime("%Y-%m-%d"),
            "Product Name": product["name"],
            "Category": product["category"],
            "Material": product["material"],
            "Quantity": quantity,
            "GHG per Unit (kgCO₂e)": unit_emission,
            "Total Emissions (kgCO₂e)": total_emission
        }
        data.append(row)

    with open(output_file, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "Date",
            "Product Name",
            "Category",
            "Material",
            "Quantity",
            "GHG per Unit (kgCO₂e)",
            "Total Emissions (kgCO₂e)"
        ])
        for row in data:
            writer.writerow([
                row["Date"],
                row["Product Name"],
                row["Category"],
                row["Material"],
                row["Quantity"],
                row["GHG per Unit (kgCO₂e)"],
                row["Total Emissions (kgCO₂e)"]
            ])
    
    print(f"CSV generated: {output_file}")
