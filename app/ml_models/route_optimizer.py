import numpy as np
from typing import Dict, List

class RouteOptimizer:
    """Route optimization using multi-objective criteria"""
    
    def __init__(self):
        """Initialize optimizer"""
        self.weights = {
            'time': 0.25,
            'cost': 0.25,
            'carbon': 0.25,
            'air_quality': 0.25
        }
    
    def set_weights(self, weights: Dict[str, float]):
        """
        Set optimization weights
        
        Args:
            weights: {'time': 0.25, 'cost': 0.25, 'carbon': 0.25, 'air_quality': 0.25}
        """
        total = sum(weights.values())
        self.weights = {k: v/total for k, v in weights.items()}
    
    def optimize_route(self, routes: List[Dict]) -> int:
        """
        Optimize among multiple routes
        
        Args:
            routes: [
                {
                    'id': 0,
                    'time_minutes': 30,
                    'cost_rupees': 50,
                    'co2_grams': 2000,
                    'avg_aqi': 78
                },
                ...
            ]
        
        Returns:
            best_route_id
        """
        
        if not routes:
            return 0
        
        # Normalize each metric (0-1 scale)
        times = np.array([r['time_minutes'] for r in routes])
        costs = np.array([r['cost_rupees'] for r in routes])
        carbons = np.array([r['co2_grams'] for r in routes])
        aqis = np.array([r['avg_aqi'] for r in routes])
        
        time_norm = (times - times.min()) / (times.max() - times.min() + 1)
        cost_norm = (costs - costs.min()) / (costs.max() - costs.min() + 1)
        carbon_norm = (carbons - carbons.min()) / (carbons.max() - carbons.min() + 1)
        aqi_norm = (aqis - aqis.min()) / (aqis.max() - aqis.min() + 1)
        
        # Calculate scores
        scores = (
            self.weights['time'] * time_norm +
            self.weights['cost'] * cost_norm +
            self.weights['carbon'] * carbon_norm +
            self.weights['air_quality'] * aqi_norm
        )
        
        best_idx = np.argmin(scores)
        return routes[best_idx]['id']
    
    def get_multi_stop_route(self, 
                            start: Dict,
                            destination: Dict,
                            available_stations: List[Dict]) -> List[Dict]:
        """
        Find multi-stop charging route
        
        Args:
            start: {'lat': float, 'lon': float, 'battery': float}
            destination: {'lat': float, 'lon': float}
            available_stations: List of charging stations with lat/lon/cost
        
        Returns:
            route: [start, station1, station2, ..., destination]
        """
        
        # Simplified greedy approach
        route = [start]
        current_pos = start
        current_battery = start['battery']
        
        while not self._near_destination(current_pos, destination):
            # Find nearest station on the way
            best_station = self._find_best_station(
                current_pos,
                destination,
                available_stations,
                current_battery
            )
            
            if best_station:
                route.append(best_station)
                current_pos = best_station
                current_battery = 100  # Full charge after stop
            else:
                break
        
        route.append(destination)
        return route
    
    def _near_destination(self, current: Dict, dest: Dict, threshold=5) -> bool:
        """Check if close to destination"""
        dist = np.sqrt(
            (current['lat'] - dest['lat'])**2 + 
            (current['lon'] - dest['lon'])**2
        )
        return dist < threshold
    
    def _find_best_station(self, current, dest, stations, battery):
        """Find best charging station on the route"""
        if not stations:
            return None
        
        # Sort by proximity to destination
        stations_sorted = sorted(
            stations,
            key=lambda s: np.sqrt(
                (s['lat'] - dest['lat'])**2 + 
                (s['lon'] - dest['lon'])**2
            )
        )
        
        return stations_sorted if stations_sorted else None
