"""Seed script for Firestore database.

HARDCODED PROJECT ID: "qwiklabs-gcp-02-c80c4225c4d5"
Do NOT use google.auth.default() or GOOGLE_CLOUD_PROJECT as those return the project number
on Agent Platform.
"""

import time
from google.cloud import firestore

# HARDCODED PROJECT ID STRING
PROJECT_ID = "qwiklabs-gcp-02-c80c4225c4d5"

def seed():
    db = firestore.Client(project=PROJECT_ID)

    print(f"Seeding Firestore in project: {PROJECT_ID}...")

    # Seed Pantry Items
    pantry_ref = db.collection("pantry_items")
    initial_pantry = [
        {"name": "Eggs", "category": "Dairy", "quantity": 12, "unit": "count", "expiration_date": "2026-10-05"},
        {"name": "Milk", "category": "Dairy", "quantity": 1.0, "unit": "gallon", "expiration_date": "2026-10-02"},
        {"name": "Garlic", "category": "Produce", "quantity": 5, "unit": "cloves", "expiration_date": "2026-10-15"},
        {"name": "Olive Oil", "category": "Pantry", "quantity": 500, "unit": "ml", "expiration_date": "2027-01-01"},
        {"name": "Spaghetti", "category": "Pantry", "quantity": 500, "unit": "grams", "expiration_date": "2027-06-01"},
        {"name": "Parmesan Cheese", "category": "Dairy", "quantity": 200, "unit": "grams", "expiration_date": "2026-10-20"},
        {"name": "Pancetta", "category": "Meat", "quantity": 150, "unit": "grams", "expiration_date": "2026-10-08"},
        {"name": "Tomatoes", "category": "Produce", "quantity": 4, "unit": "count", "expiration_date": "2026-10-04"},
        {"name": "Basil", "category": "Produce", "quantity": 1, "unit": "bunch", "expiration_date": "2026-10-01"},
    ]

    for item in initial_pantry:
        doc_id = item["name"].lower().replace(" ", "_")
        for attempt in range(3):
            try:
                pantry_ref.document(doc_id).set(item)
                print(f"  [+] Seeded pantry item: {item['name']}")
                break
            except Exception as e:
                if attempt == 2:
                    raise e
                time.sleep(1)

    # Seed Recipes
    recipes_ref = db.collection("recipes")
    initial_recipes = [
        {
            "name": "Spaghetti Carbonara",
            "cuisine": "Italian",
            "prep_time_mins": 20,
            "servings": 2,
            "ingredients": ["Spaghetti (200g)", "Pancetta (100g)", "Eggs (2)", "Parmesan Cheese (50g)", "Garlic (1 clove)", "Olive Oil"],
            "instructions": [
                "Boil pasta in salted water until al dente.",
                "Sauté pancetta with garlic in olive oil until crispy.",
                "Whisk eggs and parmesan together in a bowl.",
                "Toss drained pasta with pancetta, remove from heat, and quickly stir in egg mixture to create creamy sauce."
            ],
            "calories_per_serving": 620,
        },
        {
            "name": "Caprese Salad",
            "cuisine": "Italian",
            "prep_time_mins": 10,
            "servings": 2,
            "ingredients": ["Tomatoes (2)", "Mozzarella (150g)", "Basil (fresh leaves)", "Olive Oil (2 tbsp)", "Salt & Pepper"],
            "instructions": [
                "Slice tomatoes and mozzarella.",
                "Arrange alternating slices on a platter with basil leaves.",
                "Drizzle generously with olive oil and season with salt and fresh black pepper."
            ],
            "calories_per_serving": 280,
        },
        {
            "name": "Garlic Omelette",
            "cuisine": "American",
            "prep_time_mins": 10,
            "servings": 1,
            "ingredients": ["Eggs (3)", "Garlic (2 cloves minced)", "Butter (1 tbsp)", "Parmesan Cheese (20g)"],
            "instructions": [
                "Whisk eggs with salt and pepper.",
                "Melt butter over medium heat and lightly sauté garlic.",
                "Pour whisked eggs into pan, cook until set, sprinkle cheese, and fold."
            ],
            "calories_per_serving": 340,
        }
    ]

    for recipe in initial_recipes:
        doc_id = recipe["name"].lower().replace(" ", "_")
        for attempt in range(3):
            try:
                recipes_ref.document(doc_id).set(recipe)
                print(f"  [+] Seeded recipe: {recipe['name']}")
                break
            except Exception as e:
                if attempt == 2:
                    raise e
                time.sleep(1)

    print("Firestore seeding complete!")

if __name__ == "__main__":
    seed()
