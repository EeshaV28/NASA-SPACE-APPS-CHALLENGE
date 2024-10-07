import requests
import streamlit as st
import pandas as pd
from openai import OpenAI

client = OpenAI(api_key="nd", base_url="https://api.zukijourney.com/v1") 

def fetch_osdr_image(osdr_number):
    url = f"https://osdr.nasa.gov/geode-py/ws/studies/OSD-{osdr_number}/image"
    response = requests.get(url)

    if response.status_code == 200:
        return response.url
    else:
        st.error("No image found for the given OSDR number.")
        return None

def fetch_nasa_images(query):
    url = f"https://images-api.nasa.gov/search?q={query}"
    response = requests.get(url)
    if response.status_code == 200:
        items = response.json().get('collection', {}).get('items', [])
        return items
    else:
        st.error("Failed to fetch images from NASA.")
        return []

def process_research_data_file(uploaded_file):
    try:
        content = uploaded_file.read().decode('utf-8')
        return content
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None

def generate_overview(metadata_text):
    prompt = (
        f"Summarize the following experiment information for easy understanding:\n\n"
        f"{metadata_text}\n\n"
        "List the number of subjects, treatments, events before and after launch, and similar experiments."
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content

def generate_image(overview):
    prompt = f"Create a visual representation of the following experiment overview: {overview}"

    try:
        img = client.images.generate(
            model="absolute-reality-v1.8.1",
            prompt=prompt,
            n=1,
            size="1024x1024"
        )

        st.write("Image generation response:", img)

        if 'data' in img and img['data']:
            return img['data'][0]['url']

        else:
            st.error("")
            return None
    except Exception as e:
        st.error(f": {e}")
        return None

def extract_factors(metadata_text):
    start = metadata_text.find("STUDY FACTORS")
    end = metadata_text.find("Study Factor Type Term Accession Number")

    if start != -1 and end != -1:
        factors_section = metadata_text[start:end].split('\n')

        st.write("Extracted Factors Section:", factors_section)

        factors = {
            "Study Factor Name": [],
            "Study Factor Type": []
        }

        header_names = factors_section[1].strip().split('\t')
        header_types = factors_section[2].strip().split('\t')

        if "Study Factor Name" in header_names and "Study Factor Type" in header_types:
            name_idx = header_names.index("Study Factor Name")
            type_idx = header_types.index("Study Factor Type")

            for line in factors_section[3:]:
                parts = line.split('\t')
                if len(parts) > max(name_idx, type_idx):
                    factors["Study Factor Name"].append(parts[name_idx].strip())
                    factors["Study Factor Type"].append(parts[type_idx].strip())

            return factors

    st.warning("STUDY FACTORS section not found or incomplete.")
    return {"Study Factor Name": [], "Study Factor Type": []}

st.title("OSDR Research Data Overview Tool")

st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Select a page:", ["Home", "Challenge Info", "Effects of Space", "General Space Info", "Analyze OSDR Data"])

if page == "Home":
    st.write("Welcome to the OSDR Research Data Overview Tool! Explore experiments and the wonders of space.")
    st.write("Use the navigation bar to analyze OSDR data or learn more about the challenges and effects of space. You can also upload data into the Analyze Section to see what the experiments can be summarized into and see visualizations!")

elif page == "Challenge Info":
    st.title("Space Apps Challenge 2024")
    st.write("The Space Apps Challenge is a global hackathon that brings together citizens to address challenges faced by NASA and other space agencies.")
    st.write("Learn more about the challenges here: [Space Apps Challenge](https://www.spaceappschallenge.org/nasa-space-apps-2024/challenges/visualize-space-science/)")
    images = fetch_nasa_images("space apps challenge")
    for item in images:
        if 'links' in item and len(item['links']) > 0:
            st.image(item['links'][0]['href'], caption=item['data'][0]['title'], use_column_width=True)

elif page == "Effects of Space":
    st.title("Effects of Space on the Human Body")
    st.write("Space can significantly affect the human body in various ways, including muscle atrophy, bone density loss, and fluid redistribution.")
    images = fetch_nasa_images("effects of space on the human body")
    for item in images:
        if 'links' in item and len(item['links']) > 0:
            st.image(item['links'][0]['href'], caption=item['data'][0]['title'], use_column_width=True)

elif page == "General Space Info":
    st.title("Explore Space")
    st.write("Information about the universe, solar system, and galaxies...")
    images = fetch_nasa_images("galaxy")
    for item in images:
        if 'links' in item and len(item['links']) > 0:
            st.image(item['links'][0]['href'], caption=item['data'][0]['title'], use_column_width=True)

elif page == "Analyze OSDR Data":
    st.title("Analyze OSDR Research Data")
    osdr_number = st.text_input("Enter OSDR Number (the digits at the end of OSD, e.g., OSD-678 = 678):", "", placeholder="Enter OSDR number")
    uploaded_file = st.file_uploader("Upload OSDR Research Data Text File:", type=["txt"])

    if st.button("Analyze Experiment"):
        if uploaded_file is not None and osdr_number:
            research_data_text = process_research_data_file(uploaded_file)

            if research_data_text:
                osdr_image_url = fetch_osdr_image(osdr_number)

                overview = generate_overview(research_data_text)
                st.subheader("Experiment Overview:")
                st.write(overview)

                image_data = generate_image(overview)
                if image_data:
                    st.subheader("Generated Visualization:")
                    st.image(image_data, caption="Visualization of the Experiment Overview", use_column_width=True)

                if osdr_image_url:
                    st.subheader(f"Related Image for OSD-{osdr_number}:")
                    st.image(osdr_image_url, caption="Related Image from OSDR Database", use_column_width=True)

                factors = extract_factors(research_data_text)
                if factors and factors["Study Factor Name"]:
                    st.subheader("Factors Table:")
                    df_factors = pd.DataFrame(factors)
                    st.table(df_factors)
                else:
                    st.warning("No factors found in the uploaded research data.")

                genelab_url = f"https://visualization.genelab.nasa.gov/data/OSD-{osdr_number}"
                st.markdown(f"[View GeneLab Visualization for OSD-{osdr_number}]({genelab_url})", unsafe_allow_html=True)

                chatgpt_url = f"https://chatgpt.com/"
                st.markdown(f"[Talk to the AI chatbot for help!]({chatgpt_url})", unsafe_allow_html=True)

        else:
            st.error("Please upload a valid OSDR research data text file and enter the OSDR number.")
