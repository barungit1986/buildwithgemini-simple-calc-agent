# My agent: Smart Pantry & Personal Chef Concierge
One-liner: A conversational agent that helps home cooks plan meals, manage pantry ingredients, and discover recipes with a catalog of recipes and pantry items.

Tool coverage:
- Memory: Remembers user dietary restrictions, allergies, favorite cuisines, and pantry history across sessions
- Tools: Recipe search, pantry ingredient lookup, shopping list generator
- Catalog/UI: Recipe cards (ingredients, instructions) and pantry inventory tables (rendered via A2UI)
- Image gen: Generates AI imagery of completed dishes
- Sandbox: Computes nutritional macros and scales recipe yields/measurements via Python code execution

Recommended for every project: memory, storage, tools, image generation, A2UI
Agent-specific / stretch (pick what fits): Code sandbox for macro/yield calculations, Firestore for pantry persistence
