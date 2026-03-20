import numpy as np
from tensorflow.keras.preprocessing.image import img_to_array
from PIL import Image
import lime.lime_image
from skimage.segmentation import mark_boundaries
import matplotlib.pyplot as plt
from fpdf import FPDF
import os

# Preprocessing function
def preprocess_image(image):
    image = image.convert("RGB")
    image = image.resize((224, 224))
    img_array = img_to_array(image) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

# Classify spiral or wave
def classify_spiral_or_wave(image, classifier):
    img_array = preprocess_image(image)
    prediction = classifier.predict(img_array)[0][0]
    if 0.4 < prediction < 0.6:
        return None
    return "Wave 🌀" if prediction > 0.5 else "Spiral 🔄"

# Get LIME explanation
def explain_with_lime(image, model):
    explainer = lime.lime_image.LimeImageExplainer()
    img_array = preprocess_image(image)

    def classifier_fn(images):
        return model.predict(np.array(images) / 255.0)

    explanation = explainer.explain_instance(
        img_array[0], classifier_fn, top_labels=2, num_samples=100
    )
    temp, mask = explanation.get_image_and_mask(
        explanation.top_labels[0], positive_only=False, num_features=50, hide_rest=False
    )
    return temp, mask

# Generate PDF
def generate_pdf(input_image_path, predicted_label, confidence, severity, output_path, explanation_path):
    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(30, 30, 150)
    pdf.cell(0, 15, "Parkinson's Disease Prediction Report", ln=True, align="C")
    pdf.ln(10)

    # Prediction Details
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "Prediction Summary:", ln=True)

    pdf.set_font("Arial", '', 12)
    pdf.multi_cell(0, 8, f"The uploaded image is predicted as '{predicted_label}' with a confidence of {confidence*100:.2f}%.")

    # Color according to severity

    if severity == "Normal":
        pdf.set_text_color(0, 150, 0)
    elif severity == "Initial Stage":
        pdf.set_text_color(255, 165, 0)
    elif severity == "Moderate Stage":
        pdf.set_text_color(255, 140, 0)
    else:
        pdf.set_text_color(255, 0, 0)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"Based on models confidence severity of disease is {severity}.", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)

    # Input Image
    

    # LIME Image
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "LIME Explanation:", ln=False)
    pdf.image(explanation_path, x=10, y=76, w=170)
    pdf.ln(85)

    # LIME Explanation
    pdf.set_font("Arial", '', 12)
    pdf.multi_cell(0, 8,
               f"LIME highlights the important regions of the image.\n"
               f"Green area strongly support for prediction of '{predicted_label}'.\n"
               f"Red area support for prediction of not {predicted_label}.\n"
               "\nBy interpreting these highlighted regions, doctors and researchers can better understand why the model made a particular decision.")


    pdf.output(output_path)

