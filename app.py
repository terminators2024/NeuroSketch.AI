import streamlit as st
from PIL import Image
import numpy as np
import os
import base64
import matplotlib.pyplot as plt
from skimage.segmentation import mark_boundaries

from model_loader import load_models
from processing import preprocess_image, classify_spiral_or_wave, explain_with_lime, generate_pdf

# Load models
spiral_wave_classifier, wave_model, spiral_model = load_models()

# Class names
class_names = ['Healthy', 'Parkinson']

# Streamlit setup
st.set_page_config(page_title="Parkinson Prediction", page_icon="🧠", layout="wide")

# Sidebar
sidebar = st.sidebar
sidebar.title("🧠 Welcome")

# Custom CSS for button color
st.markdown("""
    <style>
    div.stButton > button {
        color: white;
        background-color: #007BFF;
        border-radius: 10px;
        width: 100%;
        font-size: 18px;
    }
    div.stButton > button:hover {
        background-color: #0056b3;
    }
    </style>
""", unsafe_allow_html=True)

if "page" not in st.session_state:
    st.session_state.page = "Home"

if sidebar.button("🏠 Home"):
    st.session_state.page = "Home"

if sidebar.button("🧪 Use Interpretable AI"):
    st.session_state.page = "Use Interpretable AI"

# Home Page
if st.session_state.page == "Home":
    st.title("🧠 Parkinson’s Disease Prediction Using Deep Learning and EXAI")
    st.image("assets/PD1.jpg", use_container_width=True)
    st.write("""
    **Parkinson's Disease (PD)** is a neurodegenerative disorder that affects movement control.
    This tool uses **Deep Learning** models and **LIME Explainability** to help predict and interpret the severity of Parkinson’s Disease.
    """)

# AI Page
elif st.session_state.page == "Use Interpretable AI":
    st.title("🧪 Interpretable AI for Parkinson’s Disease Prediction")

    uploaded_file = st.file_uploader("📤 Upload a Spiral/Wave Image...", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        img_path = "temp_input.jpg"
        image.save(img_path)

        st.write("### Uploaded Image and Detected Type")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.image(image, caption="Uploaded Image", width=350)

        with col2:
            with st.spinner("Classifying image..."):
                image_type = classify_spiral_or_wave(image, spiral_wave_classifier)
                if image_type is None:
                    st.error("❌ Uploaded image is not recognized as Spiral or Wave.")
                else:
                    st.success(f"✅ Detected as: {image_type}")


            model = spiral_model if "Spiral" in image_type else wave_model
            img_array = preprocess_image(image)

        if st.button("🔮 Predict", type="primary"):
            with st.spinner("Predicting..."):
                prediction = model.predict(img_array)
                predicted_label = int(prediction[0] > 0.5)
                confidence = np.max(prediction)
                
                severity = "Normal" if confidence < 0.4 else \
                           "Initial Stage" if confidence < 0.95 else \
                           "Moderate Stage" if confidence < 0.97 else "Severe Stage"

                severity_color = "green" if severity == "Normal" else \
                                 "yellow" if severity == "Initial Stage" else \
                                 "orange" if severity == "Moderate Stage" else "red"

                st.session_state.prediction_done = True
                st.session_state.predicted_label = predicted_label
                st.session_state.confidence = confidence
                st.session_state.severity = severity
                st.session_state.severity_color = severity_color

            if st.session_state.get("prediction_done"):
                st.success(f"🔵 Predicted: {class_names[st.session_state.predicted_label]}")
                st.markdown(f"<span style='color:{st.session_state.severity_color}; font-size:20px;'>🩺 Severity: {st.session_state.severity}</span>", unsafe_allow_html=True)

        if st.button("🧠 Explain with LIME", type="primary"):
            with st.spinner("Generating Explanation..."):
                temp, mask = explain_with_lime(image, model)
                fig, ax = plt.subplots(1, 2, figsize=(12, 6))
                ax[0].imshow(image)
                ax[0].set_title("Original Image")
                ax[0].axis("off")
                ax[1].imshow(mark_boundaries(temp, mask))
                ax[1].set_title("LIME Explanation")
                ax[1].axis("off")
                st.pyplot(fig)

                lime_path = "temp_lime.jpg"
                fig.savefig(lime_path)
                plt.close(fig)

                st.session_state.lime_done = True
                st.session_state.lime_path = lime_path

        if st.session_state.get("prediction_done") and st.session_state.get("lime_done"):
            if st.button("📄 Generate PDF Report", type="primary"):
                output_pdf = "Parkinson_Report.pdf"
                generate_pdf(input_image_path=img_path,
                        predicted_label=class_names[st.session_state.predicted_label],
                        confidence=st.session_state.confidence,
                        severity=st.session_state.severity,
                        output_path=output_pdf,
                        explanation_path=st.session_state.lime_path
                    )

                    # Preview PDF
                with open(output_pdf, "rb") as f:
                    base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)

                    # Download Button
                with open(output_pdf, "rb") as file:
                    st.download_button(
                            label="📥 Download PDF",
                            data=file,
                            file_name="Parkinson_Report.pdf",
                            mime="application/pdf"
                    )
