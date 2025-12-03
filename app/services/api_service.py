import requests
import os

class APIService:
    
    def __init__(self):
        self.maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY', '')
        self.weather_api_key = os.getenv('OPENWEATHER_API_KEY', '')
        self.electricity_maps_key = os.getenv('ELECTRICITY_MAPS_API_KEY', '')
    
    def get_weather(self, latitude, longitude):
        """Get weather data from OpenWeatherMap"""
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={self.weather_api_key}&units=metric"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'temperature': data['main']['temp'],
                    'humidity': data['main']['humidity'],
                    'wind_speed': data['wind']['speed'],
                    'weather_condition': data['weather']['main'],
                    'temperature_impact': self._calculate_temp_impact(data['main']['temp'])
                }
        except Exception as e:
            print(f"Weather API Error: {e}")
        
        # Return mock data if API fails
        return {'temperature': 25, 'humidity': 50, 'weather_condition': 'Clear', 'temperature_impact': 0}
    
    def get_grid_carbon_intensity(self, latitude, longitude):
        """Get grid carbon intensity from Electricity Maps"""
        try:
            url = f"https://api.electricitymap.org/v3/carbon-intensity/latest?lat={latitude}&lon={longitude}"
            headers = {'auth-token': self.electricity_maps_key}
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'carbon_intensity': data['carbonIntensity'],
                    'peak_renewable_time': '2-4 PM',
                    'coal_percentage': 55,
                    'renewable_percentage': 30
                }
        except Exception as e:
            print(f"Grid Carbon API Error: {e}")
        
        # Return mock data for India
        return {'carbon_intensity': 700, 'peak_renewable_time': '2-4 PM', 'coal_percentage': 55, 'renewable_percentage': 30}
    
    def get_nearby_charging_stations(self, latitude, longitude, radius_km=10):
        """Get nearby charging stations - Mock data"""
        # In production, integrate with OpenChargeMap API
        return [
            {
                'id': 1,
                'name': 'Premium EV Hub - Andheri',
                'distance_km': 2.5,
                'power_kw': 150,
                'available_chargers': 3,
                'total_chargers': 5,
                'cost_per_kwh': 15
            },
            {
                'id': 2,
                'name': 'Fast Charging - Bandra',
                'distance_km': 5.2,
                'power_kw': 50,
                'available_chargers': 1,
                'total_chargers': 3,
                'cost_per_kwh': 12
            }
        ]
    
    def get_air_quality_on_route(self, start_lat, start_lon, end_lat, end_lon):
        """Get air quality data for a route"""
        # Mock data - in production integrate with Google Air Quality API
        return {'aqi': 65, 'pm25': 42.5, 'pm10': 78.3}
    
    @staticmethod
    def _calculate_temp_impact(temperature):
        """Calculate temperature impact on range"""
        if temperature < 0:
            return -25
        elif temperature < 10:
            return -15
        elif temperature > 40:
            return -10
        return 0
