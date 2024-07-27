from flask import Flask, request, jsonify
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import pandas as pd
from postalcodes_ca import postal_codes
from math import radians, sin, cos, sqrt, atan2

app = Flask(__name__)
geolocator = Nominatim(user_agent="daycare_locator")

# Load the daycare data
daycare_data = pd.read_csv('./daycare_location.csv')

def haversine_distance(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    # Radius of Earth in kilometers. Use 3956 for miles. Determines return value units.
    r = 6371.0
    
    # Calculate the result
    distance = r * c
    
    return distance


@app.route('/nearest_daycares', methods=['GET'])
def nearest_daycares():
    postal_code = request.args.get('postal_code')
    max_locations = int(request.args.get('max', 5))
    
    if not postal_code:
        return jsonify({"error": "Postal code is required"}), 400
    
    user_location = postal_codes[postal_code]

    if not user_location:
        return jsonify({"error": "Invalid postal code"}), 400
    
    # Calculate distances to all daycares
    daycare_data['distance'] = daycare_data.apply(
    lambda row: haversine_distance(user_location.latitude, user_location.longitude, row['daycare_latitude'], row['daycare_longitude']),
    axis=1
)
    
    # Sort by distance and select the nearest locations
    nearest_daycares = daycare_data.nsmallest(max_locations, 'distance')
    
    # Format the output
    result = ', '.join(f"{row['daycare_location']}({row['distance']:.1f}km)" 
                       for _, row in nearest_daycares.iterrows())
    
    return jsonify({"nearest_daycares": result})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000)

