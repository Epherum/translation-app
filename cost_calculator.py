import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- Page Configuration ---
st.set_page_config(
    page_title="Cloud API Cost Calculator",
    page_icon="💰",
    layout="wide"
)

# --- App Header ---
st.title("💰 Interactive Cloud API Cost Calculator")
st.markdown("Use the sliders and inputs in the sidebar to adjust the assumptions and see the projected monthly costs for your app.")

# --- Sidebar for User Inputs ---
st.sidebar.header("Core Assumptions")
st.sidebar.markdown("Adjust these values to model different scenarios.")

# User Base Input
mau = st.sidebar.slider(
    "Number of Monthly Active Users (MAUs)",
    min_value=100,
    max_value=25000,
    value=1000,
    step=100,
    help="An active user is someone who opens the app at least once a month."
)

# User Engagement Inputs
actions_per_day = st.sidebar.slider(
    "Actions per Active Day",
    min_value=1,
    max_value=20,
    value=4,
    help="An 'action' is a translation, a voice recording, or a camera scan."
)

days_per_month = st.sidebar.slider(
    "Active Days per Month (per user)",
    min_value=1,
    max_value=30,
    value=5
)

st.sidebar.subheader("Feature Usage Mix (%)")
# Feature Mix Inputs (ensure they sum to 100)
text_ratio = st.sidebar.slider("Text Translation %", 0, 100, 70)
speech_ratio = st.sidebar.slider("Speech-to-Text %", 0, 100, 20)
camera_ratio = st.sidebar.slider("Camera (OCR) %", 0, 100, 10)

if text_ratio + speech_ratio + camera_ratio != 100:
    st.sidebar.error("The percentages must add up to 100%.")

st.sidebar.subheader("Average Action Size")
# Action Size Inputs
chars_per_action = st.sidebar.number_input(
    "Characters per Text Translation",
    value=250,
    help="Average length of text a user translates at one time."
)
seconds_per_action = st.sidebar.number_input(
    "Seconds per Speech Recording",
    value=5,
    help="Average duration of a voice input."
)

# --- Pricing and Free Tier Constants ---
st.sidebar.subheader("Google Cloud Pricing (USD)")
price_per_mil_chars = st.sidebar.number_input("Price per 1M Chars", value=20.00)
price_per_1k_images = st.sidebar.number_input("Price per 1k Images", value=1.50)
price_per_min_audio = st.sidebar.number_input("Price per Minute of Audio", value=0.024)

free_chars = 500000
free_images = 1000
free_minutes = 60

# --- Core Calculation Logic ---
total_actions_per_month = mau * days_per_month * actions_per_day

# Calculate usage for each service
total_text_actions = total_actions_per_month * (text_ratio / 100)
total_speech_actions = total_actions_per_month * (speech_ratio / 100)
total_camera_actions = total_actions_per_month * (camera_ratio / 100)

total_chars = total_text_actions * chars_per_action
total_images = total_camera_actions # 1 image per action
total_minutes = (total_speech_actions * seconds_per_action) / 60

# Calculate cost after applying free tier
cost_translate = max(0, total_chars - free_chars) / 1000000 * price_per_mil_chars
cost_vision = max(0, total_images - free_images) / 1000 * price_per_1k_images
cost_speech = max(0, total_minutes - free_minutes) * price_per_min_audio

total_cost = cost_translate + cost_vision + cost_speech

# --- Displaying the Results ---
st.header("📈 Estimated Monthly Costs")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Estimated Cost", f"${total_cost:,.2f}", delta_color="inverse")
col2.metric("Translation Cost", f"${cost_translate:,.2f}")
col3.metric("Vision (OCR) Cost", f"${cost_vision:,.2f}")
col4.metric("Speech-to-Text Cost", f"${cost_speech:,.2f}")

st.markdown("---")

st.subheader("📊 Detailed Usage Breakdown")
usage_data = {
    'Service': ['Translation', 'Vision (OCR)', 'Speech-to-Text'],
    'Monthly Usage': [f"{total_chars:,.0f} characters", f"{total_images:,.0f} images", f"{total_minutes:,.2f} minutes"],
    'Free Tier': [f"{free_chars:,.0f} chars", f"{free_images:,.0f} images", f"{free_minutes:,.0f} min"],
    'Billable Usage': [f"{max(0, total_chars - free_chars):,.0f}", f"{max(0, total_images - free_images):,.0f}", f"{max(0, total_minutes - free_minutes):,.2f}"],
    'Estimated Cost (USD)': [f"${cost_translate:,.2f}", f"${cost_vision:,.2f}", f"${cost_speech:,.2f}"]
}
usage_df = pd.DataFrame(usage_data)
st.table(usage_df)


# --- Cost Projection Graph ---
st.subheader("Cost Projection vs. User Growth")
user_range = np.linspace(100, mau * 2, 10, dtype=int)
cost_range = []

for u in user_range:
    # Simplified calculation for the graph
    monthly_actions = u * days_per_month * actions_per_day
    chars = (monthly_actions * (text_ratio / 100)) * chars_per_action
    images = (monthly_actions * (camera_ratio / 100))
    minutes = ((monthly_actions * (speech_ratio / 100)) * seconds_per_action) / 60

    c_trans = max(0, chars - free_chars) / 1000000 * price_per_mil_chars
    c_vis = max(0, images - free_images) / 1000 * price_per_1k_images
    c_speech = max(0, minutes - free_minutes) * price_per_min_audio
    cost_range.append(c_trans + c_vis + c_speech)

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(user_range, cost_range, marker='o', linestyle='-', color='b')
ax.set_title('Cost Growth as User Base Increases')
ax.set_xlabel('Number of Monthly Active Users (MAUs)')
ax.set_ylabel('Estimated Monthly Cost (USD)')
ax.grid(True)
ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
ax.get_xaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))

st.pyplot(fig)