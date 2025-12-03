import math

class CalculationService:
    
    @staticmethod
    def calculate_co2_generated(distance_km, grid_carbon_intensity, vehicle_efficiency):
        """Calculate CO2 generated for a trip"""
        energy_consumed = distance_km * vehicle_efficiency
        co2_grams = energy_consumed * grid_carbon_intensity
        return co2_grams
    
    @staticmethod
    def calculate_co2_saved(distance_km, petrol_emission_per_km=0.23):
        """Calculate CO2 saved vs petrol car"""
        petrol_co2 = distance_km * petrol_emission_per_km * 1000  # Convert to grams
        return petrol_co2
    
    @staticmethod
    def calculate_trees_needed(co2_grams, co2_per_tree_per_year=25000):
        """Calculate trees needed to offset CO2 (in grams)"""
        co2_kg = co2_grams / 1000
        trees = co2_kg / 25  # 25 kg CO2 per tree per year
        return trees
    
    @staticmethod
    def calculate_eco_score(trip):
        """Calculate eco-score for a trip"""
        score = 50  # Base score
        
        # Driving efficiency (max +20)
        if trip.duration_minutes and trip.distance_km:
            avg_speed = (trip.distance_km / trip.duration_minutes) * 60
            if 40 <= avg_speed <= 80:
                score += 20
            elif 30 <= avg_speed <= 100:
                score += 15
            else:
                score += 5
        
        # Battery efficiency (max +15)
        if trip.start_battery_percentage and trip.end_battery_percentage:
            battery_used = trip.start_battery_percentage - trip.end_battery_percentage
            if battery_used < 50:
                score += 15
            elif battery_used < 70:
                score += 10
            else:
                score += 5
        
        # Environmental factors (max +15)
        if trip.temperature_celsius:
            if 15 <= trip.temperature_celsius <= 30:
                score += 15  # Ideal conditions
            else:
                score += 5
        
        return min(100, score)
    
    @staticmethod
    def haversine(lat1, lon1, lat2, lon2):
        """Calculate distance between two coordinates"""
        R = 6371  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    
    @staticmethod
    def calculate_charging_score(station, grid_data, vehicle_efficiency):
        """Calculate score for charging station based on cost and carbon intensity"""
        eco_score = 100 - (grid_data.get('carbon_intensity', 700) - 300) / 5
        cost_score = 100 - station['cost_per_kwh'] * 5
        availability_score = (station['available_chargers'] / station['total_chargers']) * 100
        
        final_score = (eco_score * 0.4 + cost_score * 0.3 + availability_score * 0.3)
        
        return {
            'station_id': station['id'],
            'station_name': station['name'],
            'eco_score': int(final_score),
            'cost_per_kwh': station['cost_per_kwh'],
            'availability': station['available_chargers'],
            'cost_saving': (station['cost_per_kwh'] - 14) * 50  # Mock savings
        }
