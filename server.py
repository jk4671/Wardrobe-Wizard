from flask import Flask, render_template, request, jsonify, redirect, url_for
import openai
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import vertexai
from vertexai.preview.generative_models import GenerativeModel, Image
import requests
import json
import re

load_dotenv()

# Initialize Google Cloud Vertex AI
PROJECT_ID = "gen-ai-441105"
LOCATION = "us-central1"
vertexai.init(project=PROJECT_ID, location=LOCATION)

# Initialize Flask app
app = Flask(__name__, static_folder='static')

UPLOAD_FOLDER = "static/uploads"
GENERATED_IMAGES_FOLDER = "static/generated_images"  # Now within 'static'

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_IMAGES_FOLDER, exist_ok=True)

openai.api_key = os.getenv("OPENAI_API_KEY")

# Safety and generation configurations for Vertex AI
generation_config = {
    "max_output_tokens": 300,
    "temperature": 0.7,
    "top_p": 0.95,
}

# Metadata structure
meta_data = {
    "gender": "",
    "age": 0,
    "outfit_type": "",
    "occasion": "",
    "core": "",
    "uploaded_image": None,
    "identified_clothing_item": "",
    "identified_clothing_item_description": "",
    "outfit_choices": {
        "top": [],
        "bottom": [],
        "accessory": [],
    },
    "outfit_selected": {
        "top": [],
        "bottom": [],
        "accessory": [],
    },
    "outfit_shopping_description": {
        "top": [],
        "bottom": [],
        "accessory": [],
    },
    "outfit_shopping_keyword": {
        "top": [],
        "bottom": [],
        "accessory": [],
    },
    "generation": None
}



fashion_cores = {
    "Cottagecore": {
        "Aesthetic": "Romanticizing rural life and simplicity.",
        "Elements": "Flowy dresses, floral prints, lace, straw hats, soft cardigans, and aprons.",
        "Colors": "Pastels, earthy tones, whites, and florals.",
        "Images": {
            "male": "/static/images/male/cottagecore_male.webp",
            "female": "/static/images/female/cottagecore_female.webp"
        }
    },
    "Dark Academia": {
        "Aesthetic": "Scholarly, mysterious, and vintage.",
        "Elements": "Tweed blazers, turtlenecks, plaid skirts, Oxford shoes, button-up shirts, and trench coats.",
        "Colors": "Browns, dark greens, blacks, and grays.",
        "Images": {
            "male": "/static/images/male/darkAcademia_male.webp",
            "female": "/static/images/female/darkAcademia_female.webp"
        }
    },
    
    "Light Academia": {
        "Aesthetic": "Softer, more optimistic counterpart of dark academia.",
        "Elements": "Lightweight fabrics, cozy knits, pleated skirts, cardigans, and loafers.",
        "Colors": "Creams, beiges, light browns, and soft pastels.",
        "Images": {
            "male": "/static/images/male/lightAcademia_male.webp",
            "female": "/static/images/female/lightAcademia_female.webp"
        }
    },
    "Y2K": {
        "Aesthetic": "Early 2000s nostalgia with a futuristic twist.",
        "Elements": "Low-rise jeans, baby tees, crop tops, metallics, chunky sneakers, and mini handbags.",
        "Colors": "Neon, metallics, pinks, and bright blues.",
        "Images": {
            "male": "/static/images/male/y2k_male.webp",
            "female": "/static/images/female/y2k_female.webp"
        }
    },
    "Goblincore": {
        "Aesthetic": "Embraces the chaotic, messy, and earthy elements of nature.",
        "Elements": "Overalls, utility vests, mushroom motifs, earthy textures, and unpolished jewelry.",
        "Colors": "Earthy greens, browns, and rusts.",
        "Images": {
            "male": "/static/images/male/goblincore_male.webp",
            "female": "/static/images/female/goblincore_female.webp"
        }
    },
    "Grungecore": {
        "Aesthetic": "Inspired by 90s grunge music and fashion.",
        "Elements": "Flannel shirts, ripped jeans, band tees, combat boots, and oversized sweaters.",
        "Colors": "Black, gray, red, and muted earth tones.",
        "Images": {
            "male": "/static/images/male/grungecore_male.webp",
            "female": "/static/images/female/grungecore_female.webp"
        }
    },
    "Normcore": {
        "Aesthetic": "Focuses on simple, functional, and minimalistic clothing.",
        "Elements": "Plain jeans, white tees, sneakers, neutral jackets, and minimal accessories.",
        "Colors": "Neutral shades like white, black, gray, and beige.",
        "Images": {
            "male": "/static/images/male/normcore_male.webp",
            "female": "/static/images/female/normcore_female.webp"
        }
    },
    "Kidcore": {
        "Aesthetic": "Nostalgic, playful, and childlike.",
        "Elements": "Bright colors, cartoon motifs, oversized tees, jelly shoes, and playful accessories.",
        "Colors": "Primary colors and bright, playful hues.",
        "Images": {
            "male": "/static/images/male/kidcore_male.webp",
            "female": "/static/images/female/kidcore_female.webp"
        }
    },
    "Angelcore": {
        "Aesthetic": "Soft, dreamy, and ethereal.",
        "Elements": "White dresses, lace, sheer fabrics, angel wings, and halos as accessories.",
        "Colors": "White, silver, pale blue, and pastels.",
        "Images": {
            "male": "/static/images/male/angelcore_male.webp",
            "female": "/static/images/female/angelcore_female.webp"
        }
    },
    "Cybercore": {
        "Aesthetic": "Futuristic, cyberpunk-inspired fashion.",
        "Elements": "Metallic fabrics, neon accents, futuristic sunglasses, cargo pants, and tech accessories.",
        "Colors": "Neon greens, blacks, silvers, and purples.",
        "Images": {
            "male": "/static/images/male/cybercore_male.webp",
            "female": "/static/images/female/cybercore_female.webp"
        }
    },
    "Royalcore": {
        "Aesthetic": "Regal, luxurious, and inspired by historical royalty.",
        "Elements": "Corsets, ball gowns, tiaras, lace gloves, and pearl jewelry.",
        "Colors": "Deep reds, golds, blues, and rich purples.",
        "Images": {
            "male": "/static/images/male/royalcore_male.webp",
            "female": "/static/images/female/royalcore_female.webp"
        }
    },
    "Egirl/Eboy Core": {
        "Aesthetic": "Edgy, internet-influenced, and youth-oriented.",
        "Elements": "Plaid skirts, oversized hoodies, striped long-sleeve shirts, chains, and chunky boots.",
        "Colors": "Black, neon green, red, and dark tones.",
        "Images": {
            "male": "/static/images/male/egirBoycore_male.webp",
            "female": "/static/images/female/egirBoycore_female.webp"
        }
    }
}


@app.route('/submit_occasion', methods=['POST'])
def submit_occasion():
    global meta_data
    data = request.get_json()

    occasion = data.get("occasion")
    if occasion:
        meta_data.update({"occasion": occasion})
        print(f"Occasion received: {occasion}")
        print(meta_data)

    return jsonify(meta_data)

@app.route('/submit_details', methods=['POST'])
def submit_details():
    global meta_data  # Declare global meta_data before using it
    data = request.get_json()

    gender = data.get("gender")
    age = data.get("age")
    outfit_type = data.get("outfit_type")

    if gender and age and outfit_type:
        meta_data.update({
            "gender": gender,
            "age": int(age),
            "outfit_type": outfit_type
        })
        print(f"Gender: {gender}, Age: {age}, Outfit Type: {outfit_type}")
        print(meta_data)
        
    return jsonify(meta_data)

def clear_upload_folder():
    """Deletes all files in the upload folder."""
    for filename in os.listdir(app.config["UPLOAD_FOLDER"]):
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Deleted old file: {file_path}")
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")


@app.route('/upload_image', methods=['POST'])
def upload_image():
    clear_upload_folder()

    if 'image' not in request.files:
        print("No image file uploaded")
        return jsonify({"error": "No image file uploaded"}), 400

    file = request.files['image']
    if file.filename == '':
        print("No selected file")
        return jsonify({"error": "No selected file"}), 400

    try:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        print(f"File saved at {file_path}")

        meta_data.update({
            "uploaded_image": url_for('static', filename=f'uploads/{filename}'),  # Web path for display
            "uploaded_image_path": file_path,  # Absolute path for processing
            "identified_clothing_item": identify_clothing_item(file_path)  # Pass the absolute path here
        })

        print(f"Meta data updated: {meta_data}")
        
        return jsonify({
            "message": "Image processed successfully",
            "clothing_item": meta_data["identified_clothing_item"]
        })
    
    except Exception as e:
        print(f"Error processing image: {e}")
        return jsonify({"error": "Error processing image"}), 500


    
@app.route('/')
def home():
    # Check if the route is accessed with 'clear' query parameter
    if request.args.get('clear') == 'true':
        reset_meta_data()
    return render_template('home.html', data=meta_data, fashion_cores=fashion_cores)

@app.route('/edit_details')
def edit_details():
    reset_meta_data()
    return render_template('home_chat.html', data=meta_data, fashion_cores=fashion_cores)


@app.route('/select_core', methods=['POST'])
def select_core():
    global meta_data
    data = request.get_json()

    selected_core = data.get("core")
    if selected_core and selected_core in fashion_cores:
        meta_data["core"] = selected_core
        gender = meta_data.get("gender", "male").lower()
        meta_data["core_image"] = fashion_cores[selected_core]["Images"].get(gender, "/static/images/placeholder.webp")
        print(f"Selected Fashion Core: {selected_core}, Image: {meta_data['core_image']}")

    return jsonify({"redirect": url_for('summary'), "meta_data": meta_data})

@app.route('/summary')
def summary():
    return render_template('summary.html', data=meta_data, fashion_cores=fashion_cores)

@app.route('/generate_outfits', methods=['POST'])
def generate_outfits():
    print("Request received at /generate_outfits")
    global meta_data

    # Generate description for identified clothing item
    file_path = meta_data.get("uploaded_image_path")
    identified_item = meta_data.get("identified_clothing_item")

    if file_path and identified_item:
        meta_data.update({
            "identified_clothing_item_description": generate_clothing_item_description(file_path, identified_item)
        })
    else:
        meta_data["identified_clothing_item_description"] = "Image or item information is missing."

    print(meta_data["identified_clothing_item_description"])

    # Generate keywords based on user data
    keywords = get_keywords_for_headline(
        meta_data["age"], 
        meta_data["gender"], 
        meta_data["outfit_type"], 
        meta_data["occasion"], 
        meta_data["core"],
        meta_data["identified_clothing_item"],
        meta_data["identified_clothing_item_description"],
    )

    # Validate and replace outfit choices
    validated_keywords = validate_and_replace_outfit_choices(
        keywords, 
        meta_data['age'], 
        meta_data['gender'], 
        meta_data['outfit_type'], 
        meta_data['occasion'], 
        meta_data['core'], 
        api_call_limit=3
    )

    # Update meta_data with validated outfit choices
    meta_data["outfit_choices"] = validated_keywords
    print(validated_keywords)

    validated_keywords["top"].insert(0, "Do Not Apply Top")
    validated_keywords["bottom"].insert(0, "Do Not Apply Bottom")
    validated_keywords["accessory"].insert(0, "Do Not Apply Accessories")

    # Return the validated outfit choices as a JSON response
    return jsonify({"validated_keywords": validated_keywords, "data": meta_data})

@app.route('/get_keywords_for_shopping', methods=['POST'])
def get_keywords_for_shopping():
    global meta_data

    # Use the local file path for image processing
    image_path = meta_data.get("generation_path")
    
    if not image_path:
        return jsonify({"error": "Image path not provided"}), 400
    
    # Define items to describe based on user selections
    items_to_describe = {
        "top": meta_data["outfit_selected"]["top"] if meta_data["outfit_selected"]["top"] != ["Do Not Apply Top"] else None,
        "bottom": meta_data["outfit_selected"]["bottom"] if meta_data["outfit_selected"]["bottom"] != ["Do Not Apply Bottom"] else None,
        "accessory": meta_data["outfit_selected"]["accessory"] if meta_data["outfit_selected"]["accessory"] != ["Do Not Apply Accessories"] else None
    }

    # Initialize metadata entries
    meta_data["outfit_shopping_description"] = {}
    meta_data["outfit_shopping_keyword"] = {"top": [], "bottom": [], "accessory": []}

    # Retrieve gender for appending to keywords
    gender = meta_data.get("gender", "").capitalize()  # Capitalize for consistent formatting
    print("Items to Describe:", items_to_describe)
    
    # Process each item category
    for item_category, items in items_to_describe.items():
        if items:
            print("items", items)
            # Generate description for the item using the local path
            description = generate_description_for_item(item_category, items)
            meta_data["outfit_shopping_description"][item_category] = description
            print(f"{item_category.capitalize()} Description: {description}")

            # Generate keywords from the description
            keywords_data = generate_keywords_from_description(description)
            
            # Validate the returned keywords
            if isinstance(keywords_data, dict) and "keywords" in keywords_data:
                keywords = [keywords_data["keywords"]]
                meta_data["outfit_shopping_keyword"][item_category] = [
                    f"{gender} {keyword}" for keyword in keywords
                ]
            else:
                meta_data["outfit_shopping_keyword"][item_category] = ["Invalid keyword generated."]
            
            print(f"{item_category.capitalize()} Keywords: {meta_data['outfit_shopping_keyword'][item_category]}")
        else:
            # Set default error message if items are not available
            meta_data["outfit_shopping_description"][item_category] = "No items selected."
            meta_data["outfit_shopping_keyword"][item_category] = ["No items available."]
    
    # Return the updated meta_data for client use
    return jsonify({
        "outfit_shopping_description": meta_data["outfit_shopping_description"],
        "outfit_shopping_keyword": meta_data["outfit_shopping_keyword"],
        "data": meta_data
    })


@app.route('/submit_outfit_selection', methods=['POST'])
def submit_outfit_selection():
    global meta_data
    data = request.get_json()

    # Extract the selected items from the request
    selected_top = data.get("top")
    selected_bottom = data.get("bottom")
    selected_accessory = data.get("accessory")

    # Update meta_data with the selected outfit components
    if selected_top and selected_bottom and selected_accessory:
        meta_data["outfit_selected"] = {
            "top": [selected_top],
            "bottom": [selected_bottom],
            "accessory": [selected_accessory],
        }
        print("Outfit selection updated:", meta_data["outfit_selected"])

        # Generate the prompt for the image
        prompt = create_image_prompt(
            meta_data["outfit_selected"],
            meta_data["gender"],
            meta_data["age"],
            meta_data["occasion"],
            meta_data["outfit_type"],
            meta_data["core"],
            meta_data["identified_clothing_item"],
            meta_data["identified_clothing_item_description"]
        )

        clear_generated_images_folder()

        # Call generate_images directly to get the image URL
        images = generate_images(prompt)
        
        # Check if an image was generated
        if images and "url" in images[0]:
            image_url = images[0]["url"]
            image_data = requests.get(image_url).content

            # Create a unique filename
            image_filename = f"generated_outfit_{len(os.listdir(GENERATED_IMAGES_FOLDER))}.jpg"
            image_path = os.path.join(app.root_path, GENERATED_IMAGES_FOLDER, image_filename)
            
            # Save the image locally
            with open(image_path, "wb") as img_file:
                img_file.write(image_data)

            # Generate the URL for the image
            image_url = url_for('static', filename=f'generated_images/{image_filename}', _external=True)

            # Update meta_data with both the URL and the local path
            meta_data.update({
                "generation": image_url,
                "generation_path": image_path  # Local path for internal file use
            })
            
            return jsonify({"image_url": url_for('static', filename=f'generated_images/{image_filename}'), "data": meta_data})
        else:
            return jsonify({"error": "Failed to generate an image."}), 500
    else:
        return jsonify({"error": "Incomplete selection"}), 400


@app.route('/regenerate_image', methods=['POST'])
def regenerate_image():
    global meta_data

    # Generate the prompt for the image using existing outfit selections
    prompt = create_image_prompt(
        meta_data["outfit_selected"],
        meta_data["gender"],
        meta_data["age"],
        meta_data["occasion"],
        meta_data["outfit_type"],
        meta_data["core"],
        meta_data["identified_clothing_item"],
        meta_data["identified_clothing_item_description"]
    )

    clear_generated_images_folder()  # Clear previous generated images

    # Generate a new image based on the existing prompt
    images = generate_images(prompt)
    
    # Check if an image was generated
    if images and "url" in images[0]:
        image_url = images[0]["url"]
        image_data = requests.get(image_url).content

        # Create a unique filename for the regenerated image
        image_filename = f"regenerated_outfit_{len(os.listdir(GENERATED_IMAGES_FOLDER))}.jpg"
        image_path = os.path.join(app.root_path, GENERATED_IMAGES_FOLDER, image_filename)
        
        # Save the regenerated image locally
        with open(image_path, "wb") as img_file:
            img_file.write(image_data)

        # Update meta_data with the new image URL and path
        meta_data.update({
            "generation": image_url,
            "generation_path": image_path  # Local path for internal file use
        })
        
        return jsonify({"image_url": url_for('static', filename=f'generated_images/{image_filename}'), "data": meta_data})
    else:
        return jsonify({"error": "Failed to regenerate image."}), 500


def clear_generated_images_folder():
    """Deletes all files in the generated_images folder."""
    for filename in os.listdir(GENERATED_IMAGES_FOLDER):
        file_path = os.path.join(GENERATED_IMAGES_FOLDER, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Deleted old generated image: {file_path}")
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")

def identify_clothing_item(image_path):
    try:
        # Load the image for the Vertex AI model
        image = Image.load_from_file(image_path)

        # Initialize the generative model
        generative_model = GenerativeModel("gemini-1.5-flash-002")
        
        # Generate content based on the image with the new prompt
        response = generative_model.generate_content([
            """Identify the main clothing item in this image. 
            Output only a JSON object with the key "item" and the value as the name of the item. 
            Example: 
            { 
              "item": "T-shirt" 
            }""", 
            image
        ])
        
        # Extract the response text from the structured output
        clothing_json = response.candidates[0].content.parts[0].text
        print("Raw clothing_json:", repr(clothing_json))  # Shows hidden characters


        try:
            # Remove Markdown-style JSON delimiters if present
            cleaned_json = re.sub(r"```json\n|\n```", "", clothing_json).strip()
            print("Cleaned clothing_json:", cleaned_json)

            # Parse the JSON
            clothing_data = json.loads(cleaned_json)  # Parse the cleaned JSON string
            item_name = clothing_data.get("item")      # Extract the value associated with the "item" key
            print("Parsed item_name:", item_name)      # Output: Dress
            return item_name.lower()

        except json.JSONDecodeError as e:
            print("Error parsing JSON:", e)
        except ValueError as ve:
            print("Error:", ve)
            
    except Exception as e:
        print(f"Error identifying clothing item: {e}")
        return "Error identifying clothing item."


def reset_meta_data():
    """Resets meta_data to its initial state."""
    global meta_data
    meta_data = {
        "gender": "",
        "age": 0,
        "outfit_type": "",
        "occasion": "",
        "core": "",
        "uploaded_image": None,
        "uploaded_image_path": "",
        "identified_clothing_item": "",
        "identified_clothing_item_description": "",
        "outfit_choices": {
            "top": [],
            "bottom": [],
            "accessory": [],
        },
        "outfit_selected": {
            "top": [],
            "bottom": [],
            "accessory": [],
        },
        "outfit_shopping_description": {
            "top": [],
            "bottom": [],
            "accessory": [],
        },
        "outfit_shopping_keyword": {
            "top": [],
            "bottom": [],
            "accessory": [],
        },
        "generation": None
    }

def to_title_case(parsed_keywords):
    return {
        key: [item.title() for item in values]
        for key, values in parsed_keywords.items()
    }

def get_keywords_for_headline(age, gender, outfit_type, occasion, core, identified_clothing_item, identified_clothing_item_description):
    prompt = f"""I am a {age}-year-old {gender} looking for {outfit_type} inspiration. I want to dress for {occasion}. My preferred fashion core is {core}. Here’s an item I already have in my closet: {identified_clothing_item} {identified_clothing_item_description}.
                
                What additional {outfit_type} pieces in the {core} style would complement this {identified_clothing_item} while creating a cohesive look for {occasion} for a {gender}?

                Please give me inspiration for various pieces categorized as "Top", "Bottom", and "Accessory". Ensure that:
                - Only include items typically worn on the upper body for "Top" (e.g., shirts, jackets).
                - Only include items typically worn on the lower body for "Bottom" (e.g., pants, skirts).
                - Accessories should include items like watches and scarves.
                - Exclude items that resembles {identified_clothing_item} with {identified_clothing_item_description}.

                Please provide the response in this JSON format:
                {{
                  "top": ["keyword1", "keyword2", "keyword3"],
                  "bottom": ["keyword4", "keyword5", "keyword6"],
                  "accessory": ["keyword7", "keyword8", "keyword9"]
                }}

                """

    response_raw = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100
    )

    raw_response = response_raw.choices[0].message.content.strip()
    print("Raw Response:", raw_response)

    try:
        # Remove unexpected delimiters (if any) and parse JSON
        cleaned_response = re.sub(r"```json\n|\n```", "", raw_response).strip()
        keywords_dict = json.loads(cleaned_response)
        keywords_dict = to_title_case(keywords_dict)

        print("Parsed Keywords:", keywords_dict)

        return keywords_dict
    
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        return {"top": [], "bottom": [], "accessory": []}
  

def validate_and_replace_outfit_choices(outfit_choices, age, gender, outfit_type, occasion, core, api_call_limit=4):
    api_call_count = 0

    def verify_item_category(item, category, core, occasion):
        nonlocal api_call_count
        if api_call_count >= api_call_limit:
            return False

        prompt = f"""The item "{item}" is categorized as "{core}" aesthetic fashion core suitable for the occasion "{occasion}".
        - "Top" items include shirts, jackets, hoodies.
        - "Bottom" items include pants, shorts, joggers.
        - "Accessory" items include scarves, gloves, watches.

        Respond in JSON format:
        {{
            "is_valid": true or false
        }}"""

        try:
            response_raw = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=20
            )
            api_call_count += 1
            raw_response = response_raw.choices[0].message.content.strip()

            # Clean and parse the response
            cleaned_response = re.sub(r"```json\n|\n```", "", raw_response).strip()
            validation_result = json.loads(cleaned_response)

            return validation_result.get("is_valid", False)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON in verify_item_category: {e}")
            return False
        except Exception as e:
            print(f"Error in verify_item_category: {e}")
            return False

    def generate_new_item(category, age, gender, outfit_type, occasion, core):
        nonlocal api_call_count
        if api_call_count >= api_call_limit:
            return None

        prompt = f"""I need a replacement item for the "{category}" category.
        I am a {age}-year-old {gender} looking for {outfit_type} outfits for {occasion}.
        My preferred fashion core is "{core}".

        Respond in JSON format:
        {{
            "new_item": "suggested_item_name"
        }}"""

        try:
            response_raw = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=30
            )
            api_call_count += 1
            raw_response = response_raw.choices[0].message.content.strip()

            # Clean and parse the response
            cleaned_response = re.sub(r"```json\n|\n```", "", raw_response).strip()
            item_result = json.loads(cleaned_response)

            return item_result.get("new_item").title()
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON in generate_new_item: {e}")
            return None
        except Exception as e:
            print(f"Error in generate_new_item: {e}")
            return None

    # Loop through categories and validate or replace items
    categories = ["top", "bottom", "accessory"]
    for category in categories:
        for i, item in enumerate(outfit_choices[category]):
            if api_call_count >= api_call_limit:
                return outfit_choices

            if not item or not verify_item_category(item, category, core, occasion):
                new_item = generate_new_item(category, age, gender, outfit_type, occasion, core)
                if new_item:
                    outfit_choices[category][i] = new_item

    return outfit_choices


def create_image_prompt(outfit_selected, gender, age, occasion, outfit_type, core, identified_clothing_item, identified_clothing_item_description):
    # Initialize keywords as empty strings
    top_keywords = ""
    bottom_keywords = ""
    accessory_keywords = ""

    # Only set keywords if they are not set to "No Top", "No Bottom", or "No Accessories" (case-insensitive)
    if outfit_selected["top"] and outfit_selected["top"][0].strip().lower() != "do not apply top":
        top_keywords = ", ".join(outfit_selected["top"])
    if outfit_selected["bottom"] and outfit_selected["bottom"][0].strip().lower() != "do not apply bottom":
        bottom_keywords = ", ".join(outfit_selected["bottom"])
    if outfit_selected["accessory"] and outfit_selected["accessory"][0].strip().lower() != "do not apply accessories":
        accessory_keywords = ", ".join(outfit_selected["accessory"])

    # Build the prompt with the provided information
    prompt = f"""Generate a high-quality, single, full-body fashion photo of a {age}-year-old {gender}, styled for {occasion} in {outfit_type} clothing with a {core} aesthetic.

            This image must include {identified_clothing_item} {identified_clothing_item_description}."""

    # Add specific items only if they are set
    if top_keywords:
        prompt += f"\n- Top: {top_keywords}"
    if bottom_keywords:
        prompt += f"\n- Bottom: {bottom_keywords}"
    if accessory_keywords:
        prompt += f"\n- Accessories: {accessory_keywords}"

    # Additional instructions to ensure clarity in the generated image
    prompt += f"""
            Ensure the following:
            - Only one person in the image. No additional people or models should be present.
            - Full-body, head-to-toe shot, including the feet clearly in the frame.
            - Model should be standing straight, centered in the frame, and fully visible.
            - Use a neutral background with no distractions.
            - No text or descriptions should appear in the image.
            - Include color in the image.

            Make the outfit and person stand out like a fashion catalog or Pinterest-style inspiration photo, with the full body, including the feet, visible.
            """

    return prompt


def generate_images(prompt):
    try:
        response_image = openai.Image.create(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )

        print(f"API response: {response_image}")
        if not response_image or not response_image.data:
            print("No data received from API.")
            return []

        url = response_image.data[0].url
        return [{"prompt": prompt, "url": url}]
    except Exception as e:
        print(f"Error in generate_images: {e}")
        return []

def generate_clothing_item_description(image_path, item_name):
    """
    Generates a description for the identified clothing item based on the provided image.
    
    Args:
        image_path (str): Path to the uploaded image.
        item_name (str): Name of the identified clothing item.

    Returns:
        str: Generated description of the clothing item.
    """
    print(image_path)
    prompt = f"""You are a fashion assistant. Look at the provided image {image_path} and describe the {item_name} in detail to help someone who wants to recreate it.

    Include the following in your description:
    1. Mention the colors, patterns, or prints for the {item_name}.
    2. Identify any visible fabrics or textures (e.g., denim, silk, wool) for the {item_name}.
    3. Describe the overall aesthetic or style conveyed by the {item_name}.
    """

    try:
        # Load the image for the Vertex AI model
        image = Image.load_from_file(image_path)

        # Initialize the generative model
        generative_model = GenerativeModel("gemini-1.5-flash-002")

        # Generate the content based on the prompt
        response = generative_model.generate_content([prompt, image])
        description = response.candidates[0].content.parts[0].text

        print(f"Generated description: {description}")
        return description
    except Exception as e:
        print(f"Error generating item description: {e}")
        return "Description generation failed."

def generate_description_for_item(item_category, items):
    """
    Generates a detailed description for a specific item category using the local file path.
    
    Args:
        item_category (str): The category of the item (e.g., "top", "bottom", "accessory").
        items (list): List of items selected for this category.
    
    Returns:
        str: Description of the item.
    """
    global meta_data

    # Use the local file path to load the image
    image_path = meta_data["generation_path"]
    item_name = ", ".join(items)  # Combine items for description

    prompt = f"""
    You are a fashion assistant. Look at the provided image and describe the {item_name} in detail.
    
    Include the following:
    - Colors, patterns, or prints (e.g., floral, plaid, solid color)
    - Visible fabrics or textures (e.g., cotton, wool, faux fur, knit)
    - Key features or styles that make the item unique (e.g., sweetheart neckline, faux fur lining, chunky knit)

    Format the response like this:
    Item Name
    a. Colors, patterns, or prints
    b. Fabrics or textures
    c. Key features or style details

    Make the description detailed enough for someone to use as a shopping guide for similar items.
    """
    
    try:
        # Load the image using the local path for Vertex AI
        image = Image.load_from_file(image_path)

        generative_model = GenerativeModel("gemini-1.5-flash-002")

        response = generative_model.generate_content([prompt, image])

        description = response.candidates[0].content.parts[0].text.strip()
        print(description)
        return description
    except Exception as e:
        print(f"Error generating description for {item_category}: {e}")
        return "Error generating description."

def generate_keywords_from_description(description):
    """
    Generates shopping keywords based on a given item description, with output as JSON.

    Args:
        description (str): Description of the item.

    Returns:
        str: A JSON string containing the generated keywords.
    """
    import openai
    import re
    import json

    prompt = """
    Generate a JSON object that represents a shopping keyword based on the given description. 
    The JSON should have the format:
    {
      "keywords": "[color] [texture] [1-3 word description of item]"
    }
    Example:
    Input: "A warm wool sweater in bright red."
    Output:
    {
      "keywords": "Red Wool Sweater"
    }
    Description: """ + description

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100
        )

        raw_json = response.choices[0].message.content.strip()
        print("Raw response:", repr(raw_json))  # For debugging

        # Clean up response in case of Markdown or unexpected formatting
        cleaned_json = re.sub(r"```json\n|\n```", "", raw_json).strip()
        print("Cleaned JSON:", cleaned_json)  # For debugging

        # Parse JSON to verify validity
        try:
            keywords_data = json.loads(cleaned_json)
            return keywords_data  # Return as a Python dictionary
        except json.JSONDecodeError as e:
            print("Error parsing JSON:", e)
            return {"error": "Invalid JSON format generated by AI"}

    except Exception as e:
        print(f"Error generating keywords: {e}")
        return {"error": "Failed to generate keywords"}



if __name__ == '__main__':
    app.run(debug=True)