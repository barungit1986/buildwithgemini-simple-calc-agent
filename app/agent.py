# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import base64
import math
import ast
import operator as op
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

# Supported math operators for safe calculation
_ALLOWED_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.Mod: op.mod,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}

_ALLOWED_FUNCTIONS = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "ceil": math.ceil,
    "floor": math.floor,
    "abs": abs,
    "pi": math.pi,
    "e": math.e,
}

def _eval_expr(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value)}")
    elif isinstance(node, ast.BinOp):
        left = _eval_expr(node.left)
        right = _eval_expr(node.right)
        op_type = type(node.op)
        if op_type in _ALLOWED_OPERATORS:
            return _ALLOWED_OPERATORS[op_type](left, right)
        raise ValueError(f"Unsupported binary operator: {op_type}")
    elif isinstance(node, ast.UnaryOp):
        operand = _eval_expr(node.operand)
        op_type = type(node.op)
        if op_type in _ALLOWED_OPERATORS:
            return _ALLOWED_OPERATORS[op_type](operand)
        raise ValueError(f"Unsupported unary operator: {op_type}")
    elif isinstance(node, ast.Call):
        func_name = node.func.id if isinstance(node.func, ast.Name) else None
        if func_name in _ALLOWED_FUNCTIONS:
            args = [_eval_expr(arg) for arg in node.args]
            return _ALLOWED_FUNCTIONS[func_name](*args)
        raise ValueError(f"Function '{func_name}' is not supported")
    elif isinstance(node, ast.Name):
        if node.id in _ALLOWED_FUNCTIONS:
            val = _ALLOWED_FUNCTIONS[node.id]
            if isinstance(val, (int, float)):
                return val
        raise ValueError(f"Identifier '{node.id}' is not supported")
    else:
        raise ValueError(f"Unsupported expression element: {type(node)}")

def calculate(expression: str) -> str:
    """Evaluates a mathematical expression safely.

    Args:
        expression: A string containing a math expression (e.g., '2 + 3 * 4', 'sqrt(144)', '2^10', '15 / 100 * 80').

    Returns:
        The numerical result as a string or an error message.
    """
    clean_expr = expression.replace("^", "**")
    try:
        parsed = ast.parse(clean_expr, mode="eval")
        result = _eval_expr(parsed.body)
        return f"Result: {result}"
    except Exception as e:
        return f"Error evaluating expression '{expression}': {str(e)}"

def unit_converter(value: float, from_unit: str, to_unit: str) -> str:
    """Converts a value between standard units (celsius/fahrenheit, km/miles, kg/lbs).

    Args:
        value: The numerical value to convert.
        from_unit: The unit converting from (e.g. 'celsius', 'fahrenheit', 'km', 'miles', 'kg', 'lbs').
        to_unit: The target unit.

    Returns:
        A string with the conversion result.
    """
    f_u = from_unit.lower().strip()
    t_u = to_unit.lower().strip()

    # Temperature
    if f_u in ["celsius", "c"] and t_u in ["fahrenheit", "f"]:
        res = (value * 9/5) + 32
        return f"{value}°C = {res:.2f}°F"
    elif f_u in ["fahrenheit", "f"] and t_u in ["celsius", "c"]:
        res = (value - 32) * 5/9
        return f"{value}°F = {res:.2f}°C"

    # Distance
    if f_u in ["km", "kilometer", "kilometers"] and t_u in ["miles", "mile"]:
        res = value * 0.621371
        return f"{value} km = {res:.2f} miles"
    elif f_u in ["miles", "mile"] and t_u in ["km", "kilometer", "kilometers"]:
        res = value / 0.621371
        return f"{value} miles = {res:.2f} km"

    # Weight
    if f_u in ["kg", "kilogram", "kilograms"] and t_u in ["lbs", "pound", "pounds"]:
        res = value * 2.20462
        return f"{value} kg = {res:.2f} lbs"
    elif f_u in ["lbs", "pound", "pounds"] and t_u in ["kg", "kilogram", "kilograms"]:
        res = value / 2.20462
        return f"{value} lbs = {res:.2f} kg"

    return f"Unsupported unit conversion from '{from_unit}' to '{to_unit}'."

def get_weather(query: str) -> str:
    """Simulates a web search for weather information.

    Args:
        query: A location string.

    Returns:
        Weather report.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60°F and foggy in San Francisco."
    elif "nyc" in query.lower() or "new york" in query.lower():
        return "It's 72°F and sunny in New York City."
    return f"It's 75°F with clear skies in {query}."

def get_current_time(query: str) -> str:
    """Gets current time for a city.

    Args:
        query: City name.

    Returns:
        Current time string.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    elif "nyc" in query.lower() or "new york" in query.lower():
        tz_identifier = "America/New_York"
    else:
        tz_identifier = "UTC"

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"Current time in {query} ({tz_identifier}): {now.strftime('%Y-%m-%d %H:%M:%S %Z')}"

from google.cloud import firestore

# HARDCODED PROJECT ID STRING - DO NOT READ FROM GOOGLE_CLOUD_PROJECT or google.auth.default()
PROJECT_ID = "qwiklabs-gcp-02-c80c4225c4d5"

def get_firestore_client():
    return firestore.Client(project=PROJECT_ID)

def get_pantry_items(category: str = "") -> str:
    """Reads pantry inventory items from Firestore.

    Args:
        category: Optional category filter (e.g. 'Dairy', 'Produce', 'Pantry', 'Meat'). Leave empty for all.

    Returns:
        A list of available pantry ingredients with quantities and expiration dates.
    """
    try:
        db = get_firestore_client()
        docs = db.collection("pantry_items").stream()
        items = []
        for doc in docs:
            data = doc.to_dict()
            if category and data.get("category", "").lower() != category.lower():
                continue
            items.append(f"- {data.get('name')}: {data.get('quantity')} {data.get('unit')} (Category: {data.get('category', 'N/A')}, Expires: {data.get('expiration_date', 'N/A')})")

        if not items:
            return "No pantry items found matching criteria."
        return "Pantry Items:\n" + "\n".join(items)
    except Exception as e:
        return f"Error reading pantry items: {str(e)}"

def add_pantry_item(name: str, quantity: float, unit: str, category: str = "Pantry", expiration_date: str = "") -> str:
    """Adds or updates a pantry ingredient in Firestore.

    Args:
        name: Name of the ingredient (e.g., 'Butter', 'Eggs').
        quantity: Amount of the item.
        unit: Unit of measurement (e.g., 'grams', 'count', 'gallon').
        category: Category ('Dairy', 'Produce', 'Pantry', 'Meat').
        expiration_date: YYYY-MM-DD expiration date string if known.

    Returns:
        Status message of the operation.
    """
    try:
        db = get_firestore_client()
        doc_id = name.lower().replace(" ", "_")
        doc_data = {
            "name": name,
            "quantity": quantity,
            "unit": unit,
            "category": category,
            "expiration_date": expiration_date
        }
        db.collection("pantry_items").document(doc_id).set(doc_data)
        return f"Successfully saved pantry item '{name}' ({quantity} {unit}) to Firestore!"
    except Exception as e:
        return f"Error adding pantry item: {str(e)}"

def search_recipes(cuisine: str = "", max_prep_time: int = 0) -> str:
    """Searches recipe collection stored in Firestore.

    Args:
        cuisine: Optional cuisine filter (e.g., 'Italian', 'American'). Leave empty for all.
        max_prep_time: Optional maximum prep time in minutes filter.

    Returns:
        Formatted recipe details including ingredients and instructions.
    """
    try:
        db = get_firestore_client()
        docs = db.collection("recipes").stream()
        recipes = []
        for doc in docs:
            data = doc.to_dict()
            if cuisine and data.get("cuisine", "").lower() != cuisine.lower():
                continue
            if max_prep_time > 0 and data.get("prep_time_mins", 0) > max_prep_time:
                continue

            ing_list = ", ".join(data.get("ingredients", []))
            recipes.append(
                f"🍳 {data.get('name')} ({data.get('cuisine')} cuisine)\n"
                f"  Prep Time: {data.get('prep_time_mins')} mins | Servings: {data.get('servings')} | Calories: {data.get('calories_per_serving')} kcal/serving\n"
                f"  Ingredients: {ing_list}\n"
                f"  Instructions:\n    " + "\n    ".join(data.get("instructions", []))
            )

        if not recipes:
            return "No recipes found matching criteria."
        return "\n\n".join(recipes)
    except Exception as e:
        return f"Error searching recipes: {str(e)}"

def add_recipe(name: str, cuisine: str, prep_time_mins: int, servings: int, ingredients: list[str], instructions: list[str], calories_per_serving: int = 0) -> str:
    """Adds a new recipe document to Firestore.

    Args:
        name: Recipe title (e.g. 'Pesto Pasta').
        cuisine: Cuisine style (e.g. 'Italian').
        prep_time_mins: Preparation time in minutes.
        servings: Number of servings.
        ingredients: List of ingredient strings with amounts.
        instructions: Step-by-step instruction list.
        calories_per_serving: Caloric count per serving.

    Returns:
        Status string.
    """
    try:
        db = get_firestore_client()
        doc_id = name.lower().replace(" ", "_")
        doc_data = {
            "name": name,
            "cuisine": cuisine,
            "prep_time_mins": prep_time_mins,
            "servings": servings,
            "ingredients": ingredients,
            "instructions": instructions,
            "calories_per_serving": calories_per_serving
        }
        db.collection("recipes").document(doc_id).set(doc_data)
        return f"Successfully created recipe '{name}' in Firestore!"
    except Exception as e:
        return f"Error adding recipe: {str(e)}"

def generate_shopping_list(recipe_name: str) -> str:
    """Generates a missing ingredients shopping list for a recipe by comparing with Firestore pantry inventory.

    Args:
        recipe_name: Name of the recipe (e.g., 'Spaghetti Carbonara', 'Caprese Salad').

    Returns:
        Formatted shopping list of missing ingredients or confirmation that all items are in stock.
    """
    try:
        db = get_firestore_client()

        # Find recipe in Firestore
        doc_id = recipe_name.lower().replace(" ", "_")
        rec_doc = db.collection("recipes").document(doc_id).get()
        if not rec_doc.exists:
            # Search by name match
            docs = db.collection("recipes").stream()
            found = None
            for d in docs:
                if recipe_name.lower() in d.to_dict().get("name", "").lower():
                    found = d.to_dict()
                    break
            if not found:
                return f"Recipe '{recipe_name}' not found in database."
            rec_data = found
        else:
            rec_data = rec_doc.to_dict()

        # Fetch current pantry items
        pantry_docs = db.collection("pantry_items").stream()
        pantry_names = {d.to_dict().get("name", "").lower() for d in pantry_docs}

        recipe_ingredients = rec_data.get("ingredients", [])
        missing = []

        for ing in recipe_ingredients:
            in_stock = any(p_item in ing.lower() for p_item in pantry_names if p_item)
            if not in_stock:
                missing.append(ing)

        if not missing:
            return f"Great news! You already have all ingredients in stock to make {rec_data.get('name')}."

        return f"Shopping List for {rec_data.get('name')}:\n" + "\n".join([f"- [ ] {item}" for item in missing])
    except Exception as e:
        return f"Error generating shopping list: {str(e)}"

import os
import urllib.request
import urllib.parse
import json

def fetch_online_recipe(dish_name: str) -> str:
    """Fetches real recipe data from TheMealDB public web API.

    Args:
        dish_name: The name or keyword of the dish to search online (e.g., 'pasta', 'arrabiata', 'curry', 'pie').

    Returns:
        Recipe details retrieved from the web API including ingredients, instructions, and image URL.
    """
    api_key = os.environ.get("THEMEALDB_API_KEY", "1")
    encoded_query = urllib.parse.quote(dish_name.strip())
    url = f"https://www.themealdb.com/api/json/v1/{api_key}/search.php?s={encoded_query}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        meals = data.get("meals")
        if not meals:
            return f"No online recipes found for '{dish_name}' via TheMealDB API."

        meal = meals[0]
        name = meal.get("strMeal")
        category = meal.get("strCategory")
        area = meal.get("strArea")
        instructions = meal.get("strInstructions")
        thumb = meal.get("strMealThumb")

        ingredients = []
        for i in range(1, 21):
            ing = meal.get(f"strIngredient{i}")
            measure = meal.get(f"strMeasure{i}")
            if ing and ing.strip():
                ingredients.append(f"{ing.strip()} ({measure.strip() if measure else ''})")

        return (
            f"🌐 Online Recipe Found: {name}\n"
            f"Cuisine: {area} | Category: {category}\n"
            f"Image: {thumb}\n\n"
            f"Ingredients:\n" + "\n".join([f"- {i}" for i in ingredients]) + "\n\n"
            f"Instructions:\n{instructions}"
        )
    except Exception as e:
        return f"Error fetching online recipe for '{dish_name}': {str(e)}"

def geocode_address(address: str) -> str:
    """Converts a street address or location name into geographic coordinates (latitude, longitude) using Google Geocoding API.

    Args:
        address: The address or place name to geocode (e.g., '1600 Amphitheatre Parkway, Mountain View, CA').

    Returns:
        Key fields including formatted address, latitude, and longitude.
    """
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return "Error: GOOGLE_MAPS_API_KEY environment variable is not set."

    encoded_address = urllib.parse.quote(address.strip())
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        if data.get("status") != "OK" or not data.get("results"):
            return f"Geocoding failed for address '{address}': {data.get('status')}"

        result = data["results"][0]
        fmt_address = result.get("formatted_address")
        loc = result.get("geometry", {}).get("location", {})
        lat, lng = loc.get("lat"), loc.get("lng")

        return f"Address: {fmt_address}\nLocation: Latitude {lat}, Longitude {lng}"
    except Exception as e:
        return f"Error geocoding address: {str(e)}"

def find_nearby_places(place_type: str, latitude: float, longitude: float, radius_meters: float = 5000.0) -> str:
    """Finds nearby places of a given type around coordinates using Google Places API (New).

    Args:
        place_type: Type of place to search (e.g., 'supermarket', 'grocery_store', 'bakery', 'restaurant').
        latitude: Center latitude coordinate.
        longitude: Center longitude coordinate.
        radius_meters: Search radius in meters (default 5000.0).

    Returns:
        List of nearby places with name, formatted address, and location.
    """
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return "Error: GOOGLE_MAPS_API_KEY environment variable is not set."

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.primaryType"
    }

    body = {
        "includedTypes": [place_type.lower().strip()],
        "maxResultCount": 5,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "radius": radius_meters
            }
        }
    }

    try:
        req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        places = data.get("places", [])
        if not places:
            return f"No nearby '{place_type}' places found within {radius_meters}m."

        results = []
        for p in places:
            name = p.get("displayName", {}).get("text", "N/A")
            addr = p.get("formattedAddress", "N/A")
            loc = p.get("location", {})
            results.append(f"📍 {name}\n   Address: {addr}\n   Location: Lat {loc.get('latitude')}, Lng {loc.get('longitude')}")

        return f"Nearby '{place_type}' Places:\n\n" + "\n\n".join(results)
    except Exception as e:
        return f"Error searching nearby places: {str(e)}"

from google.adk.tools import ToolContext
from google.cloud import storage
import google.genai as genai

# HARDCODED BUCKET NAME STRING
BUCKET_NAME = "smart-pantry-chef-qwiklabs-gcp-02-c80c4225c4d5"

def generate_dish_image(dish_name: str, tool_context: ToolContext) -> str:
    """Generates an image for a culinary dish using gemini-3.1-flash-lite-image model in the global region.

    Saves the image with tool_context.save_artifact for the Playground's Artifacts panel and uploads it to the public GCS bucket.

    Args:
        dish_name: Name of the dish or recipe (e.g., 'Spaghetti Carbonara', 'Caprese Salad', 'Garlic Omelette').
        tool_context: ToolContext instance injected by ADK.

    Returns:
        Public HTTPS URL of the uploaded image in Cloud Storage.
    """
    try:
        genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
        prompt = f"Professional food photography of {dish_name}, delicious presentation, studio lighting"

        resp = genai_client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
            config=types.GenerateContentConfig(response_modalities=["IMAGE"])
        )

        image_bytes = None
        mime_type = "image/jpeg"
        if resp.candidates and resp.candidates[0].content.parts:
            for part in resp.candidates[0].content.parts:
                if part.inline_data:
                    image_bytes = part.inline_data.data
                    if part.inline_data.mime_type:
                        mime_type = part.inline_data.mime_type
                    break

        if not image_bytes:
            return f"Failed to generate image bytes for '{dish_name}'."

        clean_name = dish_name.lower().replace(" ", "_")
        ext = "png" if "png" in mime_type else "jpg"
        filename = f"{clean_name}.{ext}"

        # 1. Save artifact for Playground Artifacts panel
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 2. Upload same image bytes to public Cloud Storage bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        return f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
    except Exception as e:
        return f"Error generating dish image: {str(e)}"

def generate_dish_video(dish_name: str, tool_context: ToolContext) -> str:
    """Generates a short video for a culinary dish or item using Google's Omni model (gemini-omni-flash-preview) in the global region.

    Saves the video with tool_context.save_artifact for the Playground's Artifacts panel and uploads it to the public GCS bucket.

    Args:
        dish_name: Name of the dish, recipe, or culinary item (e.g., 'Spaghetti Carbonara', 'Sizzling Steak', 'Tossed Salad').
        tool_context: ToolContext instance injected by ADK.

    Returns:
        Public HTTPS URL of the uploaded video in Cloud Storage.
    """
    try:
        genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
        prompt = f"Generate a short video showing how to prepare or serve {dish_name}, delicious presentation"

        interaction = genai_client.interactions.create(
            model="gemini-omni-flash-preview",
            input=prompt
        )

        video_bytes = None
        mime_type = "video/mp4"

        if hasattr(interaction, "output_video") and interaction.output_video:
            items = interaction.output_video if isinstance(interaction.output_video, (list, tuple)) else [interaction.output_video]
            for v in items:
                data = getattr(v, "data", None)
                if data:
                    if isinstance(data, bytes):
                        video_bytes = data
                    elif isinstance(data, str):
                        try:
                            video_bytes = base64.b64decode(data)
                        except Exception:
                            pass

                if not video_bytes:
                    uri = getattr(v, "uri", None)
                    if uri and isinstance(uri, str) and uri.startswith("data:"):
                        try:
                            header, b64_str = uri.split(",", 1)
                            if "video/" in header:
                                mime_type = header.split(";")[0].replace("data:", "")
                            video_bytes = base64.b64decode(b64_str)
                        except Exception:
                            pass

                if getattr(v, "mime_type", None):
                    mime_type = v.mime_type

                if video_bytes:
                    break

        if not video_bytes:
            return f"Failed to generate video bytes for '{dish_name}'."

        clean_name = dish_name.lower().replace(" ", "_")
        filename = f"{clean_name}_video.mp4"

        # 1. Save artifact for Playground Artifacts panel
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
        tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 2. Upload same video bytes to public Cloud Storage bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        return f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
    except Exception as e:
        return f"Error generating dish video: {str(e)}"

from google.adk.code_executors.agent_engine_sandbox_code_executor import AgentEngineSandboxCodeExecutor

# Load Agent Engine resource name from deployment_metadata.json
DEPLOYMENT_META_PATH = os.path.join(os.path.dirname(__file__), "..", "deployment_metadata.json")
agent_engine_resource = None

if os.path.exists(DEPLOYMENT_META_PATH):
    try:
        with open(DEPLOYMENT_META_PATH) as f:
            meta = json.load(f)
            agent_engine_resource = meta.get("remote_agent_runtime_id")
    except Exception:
        pass

if not agent_engine_resource:
    agent_engine_resource = "projects/860421281343/locations/us-east1/reasoningEngines/6810135328909688832"

sandbox_code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=agent_engine_resource
)

from google.adk.tools import load_memory, preload_memory
from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from app.a2ui_utils import a2ui_callback

# Agent Engine Memory Bank URI for redeployment
MEMORY_SERVICE_URI = "agentengine://6810135328909688832"

a2ui_schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

a2ui_instruction = a2ui_schema_manager.generate_system_prompt(
    role_description=(
        "You are the Smart Pantry & Personal Chef Concierge! You help users manage "
        "their food allergies, dietary restrictions, pantry ingredients, recipe searches, shopping lists, and meal plans."
    ),
    workflow_description=(
        "Analyze the request and return structured UI when appropriate.\n"
        "1. Always check memory using `load_memory` or `preload_memory` to retrieve the user's stored allergies (e.g. peanuts, dairy, shellfish, gluten, tree nuts) and dietary preferences.\n"
        "2. When a user states an allergy, dietary restriction, or food preference, acknowledge it clearly and ensure it is stored in memory for future sessions.\n"
        "3. NEVER recommend, search, or include recipes or ingredients that contain any of the user's remembered allergies."
    ),
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=a2ui_instruction,
    code_executor=sandbox_code_executor,
    after_model_callback=a2ui_callback,
    tools=[
        calculate,
        unit_converter,
        get_weather,
        get_current_time,
        get_pantry_items,
        add_pantry_item,
        search_recipes,
        add_recipe,
        generate_shopping_list,
        fetch_online_recipe,
        geocode_address,
        find_nearby_places,
        generate_dish_image,
        generate_dish_video,
        load_memory,
        preload_memory
    ],
)


app = App(
    root_agent=root_agent,
    name="app",
)









