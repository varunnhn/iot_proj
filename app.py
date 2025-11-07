import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import os

# --- 1. CONFIGURE YOUR API KEY ---
# Set up the API key using Streamlit's secrets management
# This line looks for a secret named "GOOGLE_API_KEY"
# You will set this in the Streamlit Community Cloud settings.
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except FileNotFoundError:
    # This is a fallback for local development
    # Create a file .streamlit/secrets.toml and add your key there
    st.error("API key not found. Please add it to your Streamlit secrets.")
    st.stop()
except Exception as e:
    st.error(f"Error configuring API key: {e}")
    st.stop()


# --- 2. DEFINE THE "EYES" FUNCTION (IMAGE-TO-TEXT) ---

def get_image_analysis(image_data):
    """
    This is the "Eyes". It takes an image and returns a text list of ingredients.
    """
    
    # 1. Load the multimodal model
    # We use a "pro" model because image analysis is a complex task
    model = genai.GenerativeModel('gemini-2.5-flash') 
    
    # 2. Create the specific prompt for this "Eye"
    prompt = """
    You are a pantry expert. Analyze this image of a fridge and list all 
    the edible food items and ingredients you can clearly identify. 
    Ignore non-food items, containers, or brands. 
    Output a simple, comma-separated list, along with the quantity available.
    
    Example: eggs, milk, broccoli, cheddar cheese, chicken thighs
    """
    
    # 3. Send both the prompt AND the image to the AI
    response = model.generate_content([prompt, image_data])
    
    # 4. Return just the text part of the response
    return response.text


# --- 3. DEFINE THE "BRAIN" FUNCTION (TEXT-TO-RECIPE) ---

def get_recipe_recommendations(ingredients_list):
    """
    This is the "Brain". It takes a text list of ingredients and returns recipes.
    """
    
    # 1. Load the text-only model
    # We use a "flash" model because it's fast and great for creative text
    model = genai.GenerativeModel('gemini-2.5-flash') 
    
    # 2. Create the prompt using an f-string to inject the ingredients
    prompt = f"""
    You are a creative and practical chef. Your goal is to suggest 3 
    delicious dishes based *only* on the ingredients provided. 
    You can assume common pantry staples like salt, pepper, and olive oil are available.

    Here are the ingredients I have: {ingredients_list}

    Please return your 3 recommendations. For each dish, provide:
    - **Dish Name:**
    - **Description:** A short, enticing description.
    - **Key Ingredients Used:** (from my list)
    
    If no ingredients were found, return "No ingredients found"
    Format each dish clearly using Markdown for headings and bold text.
    """
    
    # 3. Send ONLY the text prompt to the AI
    response = model.generate_content(prompt)
    
    # 4. Return the text response
    return response.text


# --- 4. BUILD THE STREAMLIT WEB APP INTERFACE ---

st.set_page_config(layout="wide", page_title="Fridge-to-Dish AI")
st.title("🧑‍🍳 Fridge-to-Dish AI")
st.write("Upload a picture of your fridge, and I'll tell you what you can make!")

# Create an upload button for the user
uploaded_file = st.file_uploader("Choose a photo of your fridge...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # --- This code runs *after* a user uploads a file ---
    
    # 1. Display the uploaded image
    image = Image.open(uploaded_file)
    
    # Create two columns for a cleaner layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.image(image, caption="Here's what you uploaded:", use_column_width=True)
    
    # 2. Start the AI process in the second column
    with col2:
        # Show a loading spinner while the AI works
        with st.spinner("Analyzing your fridge... (This is Step 1: The 'Eyes')"):
            # Convert the file to a format the API understands
            # We use a BytesIO buffer to hold the image data in memory
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format=image.format)
            image_data = Image.open(img_byte_arr)
            
            # Call the "Eyes" function
            try:
                ingredients_list = get_image_analysis(image_data)
                st.success("✅ I've identified your ingredients!")
                
                # Show the user what the AI found
                with st.expander("See identified ingredients list"):
                    st.write(ingredients_list)

                # 3. Call the "Brain" function to get recipes
                with st.spinner("Generating recipes... (This is Step 2: The 'Brain')"):
                    try:
                        recipe_recommendations = get_recipe_recommendations(ingredients_list)
                        st.success("✅ Recipes are ready!")
                        
                        # 4. Display the final recipes
                        st.subheader("Here are your dish recommendations:")
                        st.markdown(recipe_recommendations)
                        
                    except Exception as e:
                        st.error(f"Error generating recipes: {e}")
                        st.error("The AI might be busy or the ingredients list was unclear. Please try again.")

            except Exception as e:
                st.error(f"Error analyzing image: {e}")
                st.error("The AI couldn't understand the image. Try a clearer photo.")