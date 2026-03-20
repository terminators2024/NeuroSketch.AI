from tensorflow.keras.models import load_model

def load_models():
    spiral_wave_classifier = load_model("models/spiral_wave_classifier.keras")
    wave_model = load_model("models/vgg19_inception_model_Wave1.keras")
    spiral_model = load_model("models/vgg19_inception_model_Spiral.keras")
    return spiral_wave_classifier, wave_model, spiral_model
