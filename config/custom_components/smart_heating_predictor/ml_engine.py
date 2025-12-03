import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import pickle
import logging
from datetime import datetime

_LOGGER = logging.getLogger(__name__)

class HeatingPredictor:
    def __init__(self, hass, data_dir):
        self.hass = hass
        self.data_dir = data_dir
        self.model = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42)
        self.scaler = StandardScaler()
        self.training_data = []
        self.is_trained = False
        self.learning_mode = True
        self.anomaly_threshold = 2.5

    def collect_features(self, thermostat_data, outdoor_temp, outdoor_humidity, target_temp, current_time):
        current_temp = thermostat_data.get('current_temp', 20)
        temp_delta = target_temp - current_temp
        features = [
            outdoor_temp if outdoor_temp is not None else 0,
            outdoor_humidity if outdoor_humidity is not None else 50,
            target_temp,
            current_temp,
            temp_delta,
            current_time.hour,
            current_time.weekday(),
            current_time.month,
            int(current_time.hour >= 6 and current_time.hour <= 22),
        ]
        return np.array(features).reshape(1, -1)

    def add_training_sample(self, features, heat_on_time, metadata=None):
        self.training_data.append({
            'features': features.flatten(),
            'label': heat_on_time,
            'timestamp': datetime.now(),
            'metadata': metadata or {}
        })
        # Rotation for memory management
        if len(self.training_data) > 10000:
            self.training_data = self.training_data[-10000:]

    def train_model(self):
        if len(self.training_data) < 100:
            _LOGGER.warning("Not enough data to train model!")
            return False
        
        X = np.vstack([d['features'] for d in self.training_data])
        y = np.array([d['label'] for d in self.training_data])
        
        # Filter outliers
        valid = ~np.isnan(y) & (y >= 0) & (y <= 180)
        X = X[valid]
        y = y[valid]
        
        if len(X) < 50:
            _LOGGER.warning("Too little valid samples after filtering.")
            return False
        
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_trained = True
        _LOGGER.info(f"Model trained on {len(y)} samples")
        return True

    def predict_preheat_time(self, features):
        if not self.is_trained:
            temp_delta = features[0, 4]
            return max(10, min(temp_delta * 15, 120))
        
        features_scaled = self.scaler.transform(features)
        prediction = self.model.predict(features_scaled)[0]
        return max(5, min(prediction, 120))

    def save_model(self, path):
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'training_data': self.training_data[-1000:],  # last 1000 samples
            'is_trained': self.is_trained
        }
        with open(path, 'wb') as f:
            pickle.dump(model_data, f)

    def load_model(self, path):
        try:
            with open(path, 'rb') as f:
                model_data = pickle.load(f)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.training_data = model_data.get('training_data', [])
            self.is_trained = model_data.get('is_trained', False)
            return True
        except Exception as e:
            _LOGGER.error(f"Failed to load model: {e}")
            return False
