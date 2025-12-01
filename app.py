import re
import textwrap
from flask import Flask, request, jsonify, render_template

# -------------------------
# 1. Flask app setup
# -------------------------
app = Flask(__name__, template_folder="templates", static_folder="static")

# -------------------------
# 2. Simple food database
# -------------------------
# Har food ke approx nutrition values (per 1 unit)
FOOD_DATA = {
    "apple": {
        "calories": 95,
        "protein": 0.5,
        "carbs": 25,
        "fat": 0.3,
        "fiber": 4.4,
        "notes": "Apples provide fiber and vitamin C. Good for digestion."
    },
    "banana": {
        "calories": 105,
        "protein": 1.3,
        "carbs": 27,
        "fat": 0.3,
        "fiber": 3.1,
        "notes": "Bananas give quick energy and potassium. Good before exercise."
    },
    "orange": {
        "calories": 62,
        "protein": 1.2,
        "carbs": 15,
        "fat": 0.2,
        "fiber": 3.1,
        "notes": "Oranges are rich in vitamin C and support immunity."
    },
    "rice": {
        "calories": 200,
        "protein": 4.3,
        "carbs": 45,
        "fat": 0.4,
        "fiber": 0.6,
        "notes": "Rice gives carbohydrates for energy. Best with vegetables and protein."
    },
    "chapati": {
        "calories": 120,
        "protein": 3.5,
        "carbs": 18,
        "fat": 3.7,
        "fiber": 2.0,
        "notes": "Chapati (roti) from wheat gives carbs and some fiber."
    },
    "dal": {
        "calories": 180,
        "protein": 9,
        "carbs": 26,
        "fat": 3,
        "fiber": 7,
        "notes": "Dal provides plant-based protein and good fiber."
    },
    "paneer": {
        "calories": 265,
        "protein": 18,
        "carbs": 6,
        "fat": 20,
        "fiber": 0,
        "notes": "Paneer is high in protein and fat. Good in moderation."
    },
    "milk": {
        "calories": 103,
        "protein": 8,
        "carbs": 12,
        "fat": 2.4,
        "fiber": 0,
        "notes": "Milk provides protein and calcium. Good for bones."
    },
    "egg": {
        "calories": 78,
        "protein": 6.3,
        "carbs": 0.6,
        "fat": 5.3,
        "fiber": 0,
        "notes": "Eggs are rich in protein and healthy fats."
    },
    "almond": {
        "calories": 7,
        "protein": 0.3,
        "carbs": 0.2,
        "fat": 0.6,
        "fiber": 0.3,
        "notes": "Almonds provide healthy fats and vitamin E."
    },
    "salad": {
        "calories": 50,
        "protein": 2,
        "carbs": 10,
        "fat": 0.5,
        "fiber": 3,
        "notes": "Vegetable salad is low in calories and high in fiber."
    },
    "pizza": {
        "calories": 285,
        "protein": 12,
        "carbs": 36,
        "fat": 10,
        "fiber": 2,
        "notes": "Pizza is usually high in calories, refined flour and fats."
    },
    "burger": {
        "calories": 300,
        "protein": 13,
        "carbs": 30,
        "fat": 14,
        "fiber": 1.5,
        "notes": "Burgers can have a lot of fats and refined carbs."
    },
    "fries": {
        "calories": 180,
        "protein": 2,
        "carbs": 22,
        "fat": 9,
        "fiber": 2,
        "notes": "Fries are deep fried and high in unhealthy fats."
    },
    "soda": {
        "calories": 140,
        "protein": 0,
        "carbs": 39,
        "fat": 0,
        "fiber": 0,
        "notes": "Soda has a lot of sugar and almost no nutrients."
    },
}

# -------------------------
# 3. Helper: parse food text
# -------------------------
def analyze_food_text(text: str):
    """
    Detect known foods and quantities from the user's text.
    Example:
      "I ate 2 chapatis and 1 dal"
      -> list of {name, quantity, data}
    """
    lower = text.lower()
    items = []

    for food_name, data in FOOD_DATA.items():
        pattern = rf"(\d+)\s*{food_name}s?"
        match = re.search(pattern, lower)

        if food_name in lower:
            quantity = 1
            if match:
                quantity = int(match.group(1))

            items.append({
                "name": food_name,
                "quantity": quantity,
                "data": data,
            })

    return items

# -------------------------
# 4. Helper: nutrition summary
# -------------------------
def build_nutrition_summary(food_items):
    if not food_items:
        return {
            "totals": {
                "calories": 0.0,
                "protein": 0.0,
                "carbs": 0.0,
                "fat": 0.0,
                "fiber": 0.0,
            },
            "summary_text": "I could not detect any known foods from the text."
        }

    totals = {
        "calories": 0.0,
        "protein": 0.0,
        "carbs": 0.0,
        "fat": 0.0,
        "fiber": 0.0,
    }

    lines = []
    for item in food_items:
        q = item["quantity"]
        d = item["data"]

        cals = d["calories"] * q
        protein = d["protein"] * q
        carbs = d["carbs"] * q
        fat = d["fat"] * q
        fiber = d["fiber"] * q

        totals["calories"] += cals
        totals["protein"] += protein
        totals["carbs"] += carbs
        totals["fat"] += fat
        totals["fiber"] += fiber

        lines.append(
            f"{q} x {item['name']}: ~{round(cals)} kcal "
            f"(protein: {protein:.1f} g, carbs: {carbs:.1f} g, "
            f"fat: {fat:.1f} g, fiber: {fiber:.1f} g)"
        )

    summary = textwrap.dedent(f"""
    Total approximate values:
    - Calories: {round(totals['calories'])} kcal
    - Protein: {totals['protein']:.1f} g
    - Carbohydrates: {totals['carbs']:.1f} g
    - Fat: {totals['fat']:.1f} g
    - Fiber: {totals['fiber']:.1f} g
    """)

    summary_text = "Nutrition breakdown:\n" + "\n".join(lines) + "\n\n" + summary
    return {"totals": totals, "summary_text": summary_text}

# -------------------------
# 5. Offline AI reply (no API)
# -------------------------
def offline_ai_reply(user_message: str, totals, summary_text: str) -> str:
    calories = totals["calories"]

    # Meal size guess
    if calories == 0:
        meal_size = "unknown (I could not find known foods)"
    elif calories < 200:
        meal_size = "very light"
    elif calories < 500:
        meal_size = "light to medium"
    elif calories < 800:
        meal_size = "medium to heavy"
    else:
        meal_size = "quite heavy"

    # Junk food check
    lower = user_message.lower()
    junk_words = ["pizza", "burger", "fries", "soda"]
    has_junk = any(w in lower for w in junk_words)

    lines = []
    lines.append("Hi! I am your Nutrition Buddy 🤖🥗")
    lines.append("")
    lines.append(f"From your message, your meal looks **{meal_size}** in size.")
    lines.append("")
    lines.append("Here is a simple nutrition summary:")
    lines.append("")
    lines.append(summary_text.strip())
    lines.append("")
    lines.append("What this means in easy English:")

    if calories == 0:
        lines.append("- I could not understand the foods. Please try again with simple names like '2 chapati and 1 dal'.")
    elif calories < 200:
        lines.append("- This meal is very small. It may not keep you full for long.")
    elif calories < 500:
        lines.append("- This is a light to medium meal. Good as a snack or small meal.")
    elif calories < 800:
        lines.append("- This is a medium to heavy meal. It should keep you full for some time.")
    else:
        lines.append("- This is a heavy meal. You may feel very full or sleepy after this.")

    if totals["protein"] < 10:
        lines.append("- Protein is low. You can add dal, paneer, milk, curd, or eggs to improve it.")
    else:
        lines.append("- Protein looks okay for this meal 👍.")

    if totals["fiber"] < 5:
        lines.append("- Fiber is low. Adding salad, fruits, or vegetables would make it healthier.")
    else:
        lines.append("- There is a decent amount of fiber, which is good for digestion.")

    if has_junk:
        lines.append("")
        lines.append("I see some junk food like pizza, burger, fries, or soda.")
        lines.append("It is okay sometimes, but try not to eat them every day.")
        lines.append("You can balance them with more fruits, salad, and home-cooked food. 🙂")

    lines.append("")
    lines.append("Remember: I am an AI helper, not a doctor or professional nutritionist.")
    lines.append("For medical or diet advice, please talk to a real health professional. 💛")

    return "\n".join(lines)

# -------------------------
# 6. Routes
# -------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"reply": "Please tell me what you ate so I can help."}), 200

    food_items = analyze_food_text(user_message)
    result = build_nutrition_summary(food_items)
    totals = result["totals"]
    summary_text = result["summary_text"]

    reply = offline_ai_reply(user_message, totals, summary_text)

    return jsonify({"reply": reply}), 200

# -------------------------
# 7. Run app
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
