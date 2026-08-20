import os
import pickle
import json
import logging
import traceback
from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)

class CropRecommendationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crop_recommendation'

    # Singletons for prediction models
    crop_model = None
    label_encoder = None
    features = None
    soil_encoder = None
    season_encoder = None
    district_encoder = None
    irrigation_encoder = None

    def ready(self):
        # Model assets are now lazy-loaded on first use via load_models_if_needed()
        # instead of at server startup, to keep baseline memory usage low
        # (important on low-RAM hosts like Render's free tier).
        pass

    @classmethod
    def load_models_if_needed(cls):
        """Load ML model assets into memory on first use, then cache them
        as class attributes so later calls are instant. Safe to call many
        times; only loads once."""
        if cls.crop_model is not None:
            return

        model_dir = getattr(settings, 'CROP_MODEL_DIR', None)
        if not model_dir:
            model_dir = os.path.abspath(os.path.join(settings.BASE_DIR, '..', 'trained_models'))

        model_path = os.path.join(model_dir, 'crop_model.pkl')
        encoder_path = os.path.join(model_dir, 'label_encoder.pkl')
        features_path = os.path.join(model_dir, 'features.json')
        soil_encoder_path = os.path.join(model_dir, 'soil_encoder.pkl')
        season_encoder_path = os.path.join(model_dir, 'season_encoder.pkl')
        district_encoder_path = os.path.join(model_dir, 'district_encoder.pkl')
        irrigation_encoder_path = os.path.join(model_dir, 'irrigation_encoder.pkl')

        # Check if files exist before trying to load
        if not os.path.exists(model_path):
            logger.warning(f"Crop model file not found at: {model_path}")
            return
        if not os.path.exists(encoder_path):
            logger.warning(f"Label encoder file not found at: {encoder_path}")
            return
        if not os.path.exists(features_path):
            logger.warning(f"Features configuration file not found at: {features_path}")
            return
        if not os.path.exists(soil_encoder_path):
            logger.warning(f"Soil encoder file not found at: {soil_encoder_path}")
            return
        if not os.path.exists(season_encoder_path):
            logger.warning(f"Season encoder file not found at: {season_encoder_path}")
            return
        if not os.path.exists(district_encoder_path):
            logger.warning(f"District encoder file not found at: {district_encoder_path}")
            return
        if not os.path.exists(irrigation_encoder_path):
            logger.warning(f"Irrigation encoder file not found at: {irrigation_encoder_path}")
            return

        try:
            with open(model_path, 'rb') as f:
                cls.crop_model = pickle.load(f)
            with open(encoder_path, 'rb') as f:
                cls.label_encoder = pickle.load(f)
            with open(features_path, 'r') as f:
                cls.features = json.load(f)
            with open(soil_encoder_path, 'rb') as f:
                cls.soil_encoder = pickle.load(f)
            with open(season_encoder_path, 'rb') as f:
                cls.season_encoder = pickle.load(f)
            with open(district_encoder_path, 'rb') as f:
                cls.district_encoder = pickle.load(f)
            with open(irrigation_encoder_path, 'rb') as f:
                cls.irrigation_encoder = pickle.load(f)
            logger.info("✔ Crop Recommendation ML model assets loaded successfully.")
        except Exception as e:
            print("\n" + "="*80)
            print(f"❌ Failed to load Crop Recommendation ML model from {model_dir}: {str(e)}")
            print("Please confirm the python execution environment contains all ML packages (scikit-learn, pandas).")
            traceback.print_exc()
            print("="*80 + "\n")
            logger.exception("Failed to load Crop Recommendation ML model.")