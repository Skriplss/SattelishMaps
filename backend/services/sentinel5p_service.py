"""
Service for Sentinel-5P atmospheric data processing
"""
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class Sentinel5PService:
    """Service for processing Sentinel-5P atmospheric data"""
    
    # Thresholds for air quality assessment (example values, adjust based on standards)
    THRESHOLDS = {
        'NO2': {
            'good': 40,
            'moderate': 90,
            'unhealthy': 120,
            'very_unhealthy': 230
        },
        'O3': {
            'good': 60,
            'moderate': 100,
            'unhealthy': 140,
            'very_unhealthy': 180
        },
        'SO2': {
            'good': 20,
            'moderate': 80,
            'unhealthy': 250,
            'very_unhealthy': 350
        },
        'CO': {
            'good': 4.4,
            'moderate': 9.4,
            'unhealthy': 12.4,
            'very_unhealthy': 15.4
        },
        'PM2.5': {  # Derived from AER_AI
            'good': 12,
            'moderate': 35.4,
            'unhealthy': 55.4,
            'very_unhealthy': 150.4
        }
    }
    
    def calculate_aqi(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Air Quality Index from Sentinel-5P data
        
        Args:
            data: Dictionary with atmospheric measurements
        
        Returns:
            AQI information with category and health implications
        """
        try:
            # Extract measurements
            no2 = data.get('no2')
            o3 = data.get('o3')
            so2 = data.get('so2')
            co = data.get('co')
            aer_ai = data.get('aer_ai')
            
            # Calculate individual AQIs
            aqis = {}
            if no2 is not None:
                aqis['NO2'] = self._calculate_parameter_aqi('NO2', no2)
            if o3 is not None:
                aqis['O3'] = self._calculate_parameter_aqi('O3', o3)
            if so2 is not None:
                aqis['SO2'] = self._calculate_parameter_aqi('SO2', so2)
            if co is not None:
                aqis['CO'] = self._calculate_parameter_aqi('CO', co)
            if aer_ai is not None:
                # Convert aerosol index to PM2.5 proxy
                aqis['PM2.5'] = self._calculate_parameter_aqi('PM2.5', aer_ai * 10)
            
            if not aqis:
                return self._default_aqi()
            
            # Get dominant pollutant (highest AQI)
            dominant = max(aqis.items(), key=lambda x: x[1])
            overall_aqi = dominant[1]
            
            # Determine category
            category, color, health = self._get_aqi_category(overall_aqi)
            
            return {
                'overall_aqi': overall_aqi,
                'category': category,
                'dominant_pollutant': dominant[0],
                'health_implications': health,
                'color': color,
                'individual_aqis': aqis
            }
            
        except Exception as e:
            logger.error(f"Error calculating AQI: {str(e)}")
            return self._default_aqi()
    
    def _calculate_parameter_aqi(self, parameter: str, value: float) -> int:
        """Calculate AQI for a specific parameter"""
        thresholds = self.THRESHOLDS.get(parameter, {})
        
        if value <= thresholds.get('good', 0):
            return int((value / thresholds['good']) * 50)
        elif value <= thresholds.get('moderate', 0):
            return int(50 + ((value - thresholds['good']) / (thresholds['moderate'] - thresholds['good'])) * 50)
        elif value <= thresholds.get('unhealthy', 0):
            return int(100 + ((value - thresholds['moderate']) / (thresholds['unhealthy'] - thresholds['moderate'])) * 100)
        else:
            return min(500, int(200 + ((value - thresholds['unhealthy']) / (thresholds.get('very_unhealthy', thresholds['unhealthy']) - thresholds['unhealthy'])) * 200))
    
    def _get_aqi_category(self, aqi: int) -> tuple:
        """Get category, color, and health implications for AQI value"""
        if aqi <= 50:
            return ('Good', '#00E400', 'Air quality is satisfactory')
        elif aqi <= 100:
            return ('Moderate', '#FFFF00', 'Acceptable for most people')
        elif aqi <= 150:
            return ('Unhealthy for Sensitive Groups', '#FF7E00', 'Sensitive groups may experience health effects')
        elif aqi <= 200:
            return ('Unhealthy', '#FF0000', 'Everyone may begin to experience health effects')
        elif aqi <= 300:
            return ('Very Unhealthy', '#8F3F97', 'Health alert: everyone may experience serious effects')
        else:
            return ('Hazardous', '#7E0023', 'Health warnings of emergency conditions')
    
    def _default_aqi(self) -> Dict[str, Any]:
        """Return default AQI when calculation fails"""
        return {
            'overall_aqi': 0,
            'category': 'Unknown',
            'dominant_pollutant': 'N/A',
            'health_implications': 'Insufficient data',
            'color': '#CCCCCC',
            'individual_aqis': {}
        }
    
    def analyze_pollution_trend(
        self,
        current: Dict[str, Any],
        previous: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze pollution trends"""
        trends = {}
        
        parameters = ['no2', 'o3', 'so2', 'co', 'aer_ai']
        
        for param in parameters:
            current_val = current.get(param)
            if current_val is None:
                continue
            
            trend_data = {
                'parameter': param.upper(),
                'current_value': current_val,
                'severity': self._get_severity(param, current_val)
            }
            
            if previous and previous.get(param) is not None:
                prev_val = previous[param]
                change = ((current_val - prev_val) / prev_val) * 100 if prev_val != 0 else 0
                
                trend_data['previous_value'] = prev_val
                trend_data['change_percentage'] = round(change, 2)
                
                if abs(change) < 5:
                    trend_data['trend'] = 'stable'
                elif change > 0:
                    trend_data['trend'] = 'increasing'
                else:
                    trend_data['trend'] = 'decreasing'
            else:
                trend_data['trend'] = 'unknown'
            
            trends[param] = trend_data
        
        return trends
    
    def _get_severity(self, parameter: str, value: float) -> str:
        """Determine severity level for a parameter"""
        param_upper = parameter.upper().replace('_', '')
        thresholds = self.THRESHOLDS.get(param_upper, self.THRESHOLDS.get('NO2'))
        
        if value <= thresholds.get('good', 0):
            return 'low'
        elif value <= thresholds.get('moderate', 0):
            return 'moderate'
        elif value <= thresholds.get('unhealthy', 0):
            return 'high'
        else:
            return 'very_high'


# Singleton instance
sentinel5p_service = Sentinel5PService()
