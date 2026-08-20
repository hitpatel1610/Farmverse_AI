import datetime
import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .serializers import CropRecommendationRequestSerializer
from .apps import CropRecommendationConfig
from .city_mapping import map_city_to_district_and_soil

class PingCropRecommendationView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {"status": "online", "message": "Welcome to FarmVerse AI - CropRecommendation module API placeholder"}, 
            status=status.HTTP_200_OK
        )

class CropRecommendationPredictView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CropRecommendationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "error": "Invalid values",
                    "details": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        validated_data = serializer.validated_data

        # Load ML model assets now (first call loads + caches; later calls are instant)
        CropRecommendationConfig.load_models_if_needed()

        # 10. Handle Model and encoder loading failure (safe singleton check)
        if (CropRecommendationConfig.crop_model is None or 
            CropRecommendationConfig.label_encoder is None or 
            CropRecommendationConfig.features is None or
            CropRecommendationConfig.soil_encoder is None or
            CropRecommendationConfig.season_encoder is None or
            CropRecommendationConfig.district_encoder is None or
            CropRecommendationConfig.irrigation_encoder is None):
            return Response(
                {
                    "success": False,
                    "error": "Model loading failure"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            # Resolve district and soil type automatically from city (backward compatible with district input)
            city_val = request.data.get('city') or validated_data.get('city') or request.data.get('district') or validated_data.get('district') or 'Rajkot'
            final_district, final_soil = map_city_to_district_and_soil(city_val)
            
            # Calculate season automatically (Kharif: June-Oct, Rabi: Nov-May)
            current_month = datetime.datetime.now().month
            final_season = 'Kharif' if 6 <= current_month <= 10 else 'Rabi'
            
            # Determine irrigation automatically based on rainfall
            rainfall_val = validated_data.get('rainfall', 0.0)
            final_irrigation = 'High' if rainfall_val >= 600.0 else ('Medium' if rainfall_val >= 300.0 else 'Low')

            # Transform categorical values using saved LabelEncoders
            data_dict = dict(validated_data)
            
            try:
                data_dict['soil_type'] = CropRecommendationConfig.soil_encoder.transform([final_soil])[0]
                data_dict['season'] = CropRecommendationConfig.season_encoder.transform([final_season])[0]
                data_dict['district'] = CropRecommendationConfig.district_encoder.transform([final_district])[0]
                data_dict['irrigation'] = CropRecommendationConfig.irrigation_encoder.transform([final_irrigation])[0]
            except ValueError as ve:
                return Response(
                    {
                        "success": False,
                        "error": "Encoding failure",
                        "details": f"Invalid categorical value supplied: {str(ve)}"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Reconstruct feature DataFrame with column order matching train dataset (features.json)
            input_dict = {feat: [data_dict[feat]] for feat in CropRecommendationConfig.features}
            input_df = pd.DataFrame(input_dict)

            # Predict encoded target class
            pred_encoded = CropRecommendationConfig.crop_model.predict(input_df)[0]
            recommended_crop = CropRecommendationConfig.label_encoder.inverse_transform([pred_encoded])[0]

            # Calculate prediction confidence probability
            if hasattr(CropRecommendationConfig.crop_model, 'predict_proba'):
                proba = CropRecommendationConfig.crop_model.predict_proba(input_df)
                confidence = proba[0][pred_encoded] * 100
                confidence = round(float(confidence), 2)
            else:
                confidence = 100.0

            # Save telemetry log record
            try:
                from .models import CropRecommendationLog
                user_val = request.user if request.user and request.user.is_authenticated else None
                CropRecommendationLog.objects.create(
                    user=user_val,
                    city=city_val,
                    district=final_district,
                    soil_type=final_soil,
                    season=final_season,
                    rainfall=float(validated_data.get('rainfall', 0.0)),
                    recommended_crop=recommended_crop,
                    confidence=float(confidence)
                )
            except Exception as log_err:
                pass

            return Response(
                {
                    "success": True,
                    "recommended_crop": recommended_crop,
                    "confidence": confidence
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "error": "Prediction failure",
                    "details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )