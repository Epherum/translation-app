import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Translation App Cost Calculator",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    .accuracy-high { color: #28a745; font-weight: bold; }
    .accuracy-medium { color: #ffc107; font-weight: bold; }
    .accuracy-low { color: #dc3545; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">🌐 Translation App Cost & Performance Calculator</h1>', unsafe_allow_html=True)

# Provider data
PROVIDERS = {
    "Google Cloud Translation": {
        "text_free_tier": 500000,
        "text_cost_per_million": 20,
        "stt_free_tier": 60,  # minutes
        "stt_cost_per_minute": 0.016,
        "ocr_free_tier": 1000,
        "ocr_cost_per_1000": 1.50,
        "languages": 189,
        "accuracy_text": 92,
        "accuracy_stt": 95,
        "accuracy_ocr": 96,
        "strengths": "Broadest language support, strong API ecosystem"
    },
    "Microsoft Azure Translator": {
        "text_free_tier": 2000000,
        "text_cost_per_million": 10,
        "stt_free_tier": 300,  # minutes (5 hours)
        "stt_cost_per_minute": 1.0,
        "ocr_free_tier": 5000,
        "ocr_cost_per_1000": 1.50,
        "languages": 100,
        "accuracy_text": 90,
        "accuracy_stt": 94,
        "accuracy_ocr": 95,
        "strengths": "Most generous free tier, excellent for business content"
    },
    "Amazon Translate/Transcribe": {
        "text_free_tier": 2000000,
        "text_cost_per_million": 15,
        "stt_free_tier": 60,
        "stt_cost_per_minute": 0.024,
        "ocr_free_tier": 1000,
        "ocr_cost_per_1000": 1.50,
        "languages": 75,
        "accuracy_text": 89,
        "accuracy_stt": 93,
        "accuracy_ocr": 93,
        "strengths": "AWS ecosystem integration, competitive pricing"
    },
    "DeepL API": {
        "text_free_tier": 500000,
        "text_cost_per_million": 25,
        "stt_free_tier": 0,  # No STT service
        "stt_cost_per_minute": 0,
        "ocr_free_tier": 0,  # No OCR service
        "ocr_cost_per_1000": 0,
        "languages": 33,
        "accuracy_text": 96,
        "accuracy_stt": 0,
        "accuracy_ocr": 0,
        "strengths": "Highest translation accuracy, best for European languages"
    }
}

OFFLINE_SPECS = {
    "accuracy_text": 78,
    "accuracy_stt": 88,
    "accuracy_ocr": 87,
    "languages": 52,
    "app_size_mb": 150,
    "processing_time_ms": 200,
    "cpu_usage_percent": 25,
    "battery_impact": "10-20% additional drain",
    "one_time_cost": True
}

# Sidebar configuration
st.sidebar.header("📊 Configuration Panel")

# Usage parameters
st.sidebar.subheader("📈 Usage Patterns")
monthly_users = st.sidebar.number_input("Monthly Active Users", min_value=100, max_value=1000000, value=5000, step=100)
active_days = st.sidebar.slider("Active Days per Month", min_value=1, max_value=30, value=20)
sessions_per_day = st.sidebar.slider("Average Sessions per User per Day", min_value=1, max_value=20, value=3)

# Feature usage distribution
st.sidebar.subheader("🎯 Feature Usage Distribution")
text_percent = st.sidebar.slider("Text Translation (%)", min_value=0, max_value=100, value=70)
photo_percent = st.sidebar.slider("Photo Translation (OCR) (%)", min_value=0, max_value=100-text_percent, value=20)
voice_percent = 100 - text_percent - photo_percent
st.sidebar.write(f"Voice Translation: {voice_percent}%")

# Actions per session
st.sidebar.subheader("🎬 Actions per Session")
text_actions = st.sidebar.number_input("Text translations per session", min_value=1, max_value=50, value=5)
photo_actions = st.sidebar.number_input("Photo translations per session", min_value=1, max_value=20, value=2)
voice_actions = st.sidebar.number_input("Voice translations per session", min_value=1, max_value=10, value=3)

# Character estimates
st.sidebar.subheader("📝 Content Size Estimates")
avg_text_chars = st.sidebar.slider("Average characters per text translation", min_value=10, max_value=2000, value=150)
avg_voice_chars = st.sidebar.slider("Average characters per voice translation", min_value=10, max_value=1000, value=100)

# Provider selection
st.sidebar.subheader("🏢 Provider Selection")
selected_provider = st.sidebar.selectbox("Choose Cloud Provider", list(PROVIDERS.keys()))

# Offline toggle
st.sidebar.subheader("📱 Offline Consideration")
include_offline = st.sidebar.checkbox("Compare with Offline Solution", value=False)

# Calculate usage volumes
total_sessions = monthly_users * active_days * sessions_per_day

# Text usage
text_sessions = total_sessions * (text_percent / 100)
total_text_chars = text_sessions * text_actions * avg_text_chars

# Voice usage (STT + Translation)
voice_sessions = total_sessions * (voice_percent / 100)
total_voice_minutes = voice_sessions * voice_actions * 0.5  # Assume 30 seconds average
total_voice_chars = voice_sessions * voice_actions * avg_voice_chars

# Photo usage (OCR + Translation)
photo_sessions = total_sessions * (photo_percent / 100)
total_photo_images = photo_sessions * photo_actions
total_photo_chars = photo_sessions * photo_actions * 200  # Assume 200 chars per photo

# Total volumes
total_chars_for_translation = total_text_chars + total_voice_chars + total_photo_chars
total_stt_minutes = total_voice_minutes
total_ocr_images = total_photo_images

# Cost calculation function
def calculate_costs(provider_data, chars, stt_mins, ocr_imgs):
    # Text translation costs
    chars_after_free = max(0, chars - provider_data["text_free_tier"])
    text_cost = (chars_after_free / 1000000) * provider_data["text_cost_per_million"]
    
    # STT costs
    stt_after_free = max(0, stt_mins - provider_data["stt_free_tier"])
    stt_cost = stt_after_free * provider_data["stt_cost_per_minute"]
    
    # OCR costs
    ocr_after_free = max(0, ocr_imgs - provider_data["ocr_free_tier"])
    ocr_cost = (ocr_after_free / 1000) * provider_data["ocr_cost_per_1000"]
    
    return text_cost, stt_cost, ocr_cost

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📊 Cost Analysis")
    
    # Calculate costs for selected provider
    provider_data = PROVIDERS[selected_provider]
    text_cost, stt_cost, ocr_cost = calculate_costs(
        provider_data, total_chars_for_translation, total_stt_minutes, total_ocr_images
    )
    total_monthly_cost = text_cost + stt_cost + ocr_cost
    annual_cost = total_monthly_cost * 12
    
    # Display key metrics
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    
    with metric_col1:
        st.metric("Monthly Cost", f"${total_monthly_cost:.2f}")
    with metric_col2:
        st.metric("Annual Cost", f"${annual_cost:.2f}")
    with metric_col3:
        st.metric("Cost per User/Month", f"${total_monthly_cost/monthly_users:.3f}")
    with metric_col4:
        st.metric("Total Sessions", f"{total_sessions:,}")
    
    # Cost breakdown chart
    if total_monthly_cost > 0:
        cost_breakdown = pd.DataFrame({
            'Service': ['Text Translation', 'Speech-to-Text', 'OCR'],
            'Cost': [text_cost, stt_cost, ocr_cost],
            'Percentage': [
                (text_cost/total_monthly_cost)*100 if total_monthly_cost > 0 else 0,
                (stt_cost/total_monthly_cost)*100 if total_monthly_cost > 0 else 0,
                (ocr_cost/total_monthly_cost)*100 if total_monthly_cost > 0 else 0
            ]
        })
        
        fig_pie = px.pie(cost_breakdown, values='Cost', names='Service', 
                        title=f"Monthly Cost Breakdown - {selected_provider}")
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Usage volume breakdown
    st.subheader("📈 Usage Volume Breakdown")
    
    volume_data = pd.DataFrame({
        'Metric': ['Characters for Translation', 'STT Minutes', 'OCR Images'],
        'Volume': [
            f"{total_chars_for_translation:,.0f}",
            f"{total_stt_minutes:,.1f}",
            f"{total_ocr_images:,.0f}"
        ],
        'Free Tier': [
            f"{provider_data['text_free_tier']:,}",
            f"{provider_data['stt_free_tier']:,}",
            f"{provider_data['ocr_free_tier']:,}"
        ],
        'Billable': [
            f"{max(0, total_chars_for_translation - provider_data['text_free_tier']):,.0f}",
            f"{max(0, total_stt_minutes - provider_data['stt_free_tier']):,.1f}",
            f"{max(0, total_ocr_images - provider_data['ocr_free_tier']):,.0f}"
        ]
    })
    
    st.dataframe(volume_data, use_container_width=True)

with col2:
    st.header("🎯 Provider Specs")
    
    # Provider accuracy display
    def get_accuracy_class(accuracy):
        if accuracy >= 95:
            return "accuracy-high"
        elif accuracy >= 90:
            return "accuracy-medium"
        else:
            return "accuracy-low"
    
    st.markdown(f"### {selected_provider}")
    st.markdown(f"**Languages Supported:** {provider_data['languages']}")
    st.markdown(f"**Strengths:** {provider_data['strengths']}")
    
    st.markdown("**Accuracy Ratings:**")
    st.markdown(f'<span class="{get_accuracy_class(provider_data["accuracy_text"])}">Text Translation: {provider_data["accuracy_text"]}%</span>', unsafe_allow_html=True)
    st.markdown(f'<span class="{get_accuracy_class(provider_data["accuracy_stt"])}">Speech-to-Text: {provider_data["accuracy_stt"]}%</span>', unsafe_allow_html=True)
    st.markdown(f'<span class="{get_accuracy_class(provider_data["accuracy_ocr"])}">OCR: {provider_data["accuracy_ocr"]}%</span>', unsafe_allow_html=True)
    
    # Free tier status
    st.markdown("**Free Tier Usage:**")
    text_free_usage = (total_chars_for_translation / provider_data['text_free_tier']) * 100 if provider_data['text_free_tier'] > 0 else 100
    stt_free_usage = (total_stt_minutes / provider_data['stt_free_tier']) * 100 if provider_data['stt_free_tier'] > 0 else 100
    ocr_free_usage = (total_ocr_images / provider_data['ocr_free_tier']) * 100 if provider_data['ocr_free_tier'] > 0 else 100
    
    st.progress(min(text_free_usage/100, 1.0))
    st.caption(f"Text: {text_free_usage:.1f}% of free tier used")
    
    if provider_data['stt_free_tier'] > 0:
        st.progress(min(stt_free_usage/100, 1.0))
        st.caption(f"STT: {stt_free_usage:.1f}% of free tier used")
    else:
        st.warning("⚠️ No STT service available")
    
    if provider_data['ocr_free_tier'] > 0:
        st.progress(min(ocr_free_usage/100, 1.0))
        st.caption(f"OCR: {ocr_free_usage:.1f}% of free tier used")
    else:
        st.warning("⚠️ No OCR service available")

# Offline comparison section
if include_offline:
    st.header("📱 Offline vs Cloud Comparison")
    
    # Create comparison dataframe
    comparison_data = {
        'Metric': ['Text Accuracy', 'STT Accuracy', 'OCR Accuracy', 'Languages', 'Monthly Cost', 'Response Time'],
        'Cloud (Selected Provider)': [
            f"{provider_data['accuracy_text']}%",
            f"{provider_data['accuracy_stt']}%" if provider_data['accuracy_stt'] > 0 else "N/A",
            f"{provider_data['accuracy_ocr']}%" if provider_data['accuracy_ocr'] > 0 else "N/A",
            str(provider_data['languages']),
            f"${total_monthly_cost:.2f}",
            "200-1000ms + network"
        ],
        'Offline Solution': [
            f"{OFFLINE_SPECS['accuracy_text']}%",
            f"{OFFLINE_SPECS['accuracy_stt']}%",
            f"{OFFLINE_SPECS['accuracy_ocr']}%",
            str(OFFLINE_SPECS['languages']),
            "$0 (one-time dev cost)",
            f"{OFFLINE_SPECS['processing_time_ms']}ms"
        ]
    }
    
    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(comparison_df, use_container_width=True)
    
    # Offline considerations
    col1_offline, col2_offline = st.columns(2)
    
    with col1_offline:
        st.subheader("✅ Offline Advantages")
        st.write("• No ongoing API costs")
        st.write("• Works without internet")
        st.write("• Faster response times")
        st.write("• Complete data privacy")
        st.write("• Predictable performance")
    
    with col2_offline:
        st.subheader("⚠️ Offline Considerations")
        st.write(f"• App size increase: ~{OFFLINE_SPECS['app_size_mb']}MB")
        st.write(f"• CPU usage: ~{OFFLINE_SPECS['cpu_usage_percent']}% during processing")
        st.write(f"• Battery impact: {OFFLINE_SPECS['battery_impact']}")
        st.write("• Limited language support")
        st.write("• Lower accuracy for complex content")
        st.write("• No real-time model improvements")
    
    # ROI calculation
    st.subheader("💰 Return on Investment Analysis")
    development_cost = st.slider("Estimated offline development cost ($)", min_value=5000, max_value=50000, value=15000)
    
    if total_monthly_cost > 0:
        payback_months = development_cost / total_monthly_cost
        st.metric("Payback Period", f"{payback_months:.1f} months")
        
        if payback_months <= 12:
            st.success(f"✅ Offline solution pays for itself in {payback_months:.1f} months")
        elif payback_months <= 24:
            st.warning(f"⚠️ Offline solution pays for itself in {payback_months:.1f} months")
        else:
            st.error(f"❌ Long payback period: {payback_months:.1f} months")

# Provider comparison section
st.header("🏢 All Providers Comparison")

# Calculate costs for all providers
all_provider_costs = []
for provider_name, provider_info in PROVIDERS.items():
    text_c, stt_c, ocr_c = calculate_costs(provider_info, total_chars_for_translation, total_stt_minutes, total_ocr_images)
    total_c = text_c + stt_c + ocr_c
    
    all_provider_costs.append({
        'Provider': provider_name,
        'Monthly Cost': total_c,
        'Annual Cost': total_c * 12,
        'Text Accuracy': provider_info['accuracy_text'],
        'Languages': provider_info['languages'],
        'Free Tier (chars)': f"{provider_info['text_free_tier']:,}"
    })

comparison_df = pd.DataFrame(all_provider_costs)

# Sort by cost
comparison_df = comparison_df.sort_values('Monthly Cost')

# Display comparison table
st.dataframe(comparison_df.style.format({
    'Monthly Cost': '${:.2f}',
    'Annual Cost': '${:.2f}',
    'Text Accuracy': '{:.0f}%'
}), use_container_width=True)

# Cost vs Accuracy scatter plot
fig_scatter = px.scatter(comparison_df, x='Text Accuracy', y='Monthly Cost', 
                        size='Languages', hover_name='Provider',
                        title='Cost vs Accuracy Analysis',
                        labels={'Text Accuracy': 'Text Translation Accuracy (%)', 
                               'Monthly Cost': 'Monthly Cost ($)'})

fig_scatter.update_traces(marker=dict(sizemode='diameter', sizeref=max(comparison_df['Languages'])/100))
st.plotly_chart(fig_scatter, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
### 📋 Methodology Notes:
- **Cost calculations** include only usage above free tier limits
- **Accuracy percentages** based on industry benchmarks and provider documentation
- **Offline specifications** represent typical ML Kit/on-device performance
- **Character estimates** use industry-standard assumptions for voice and image content
- **Free tier limits** reset monthly for all providers
""")
