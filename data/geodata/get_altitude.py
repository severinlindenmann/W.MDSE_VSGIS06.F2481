# import requests
# import json
# import os
# import pandas as pd
# import time

# API_KEY = "AIzaSyA1FMSyBmd8kHJG1qclw53MKWTfFbuXl-E"

# # Global variable for caching altitude data
# altitude_cache = {}

# # File path for storing cached altitude data
# cache_file = "altitude_cache.json"

# # Load cached altitude data from file, if available
# if os.path.exists(cache_file):
#     with open(cache_file, "r") as f:
#         try:
#             altitude_cache = json.load(f)
#             print(len(altitude_cache), "cached altitude data entries loaded.")
#         except json.JSONDecodeError:
#             altitude_cache = {}

# def get_cache_key(lat, lon):
#     return f"{lat},{lon}"


# def get_altitude(lat, lon):
#     # Generate cache key
#     cache_key = get_cache_key(lat, lon)

#     # Check if altitude data is already cached for the given coordinates
#     if cache_key in altitude_cache:
#         # print("Altitude data found in cache.")
#         return altitude_cache[cache_key]

#     url = f"https://maps.googleapis.com/maps/api/elevation/json?locations={lat},{lon}&key={API_KEY}"
#     response = requests.get(url)
#     data = response.json()
#     # time.sleep(0.5)
#     # print("Altitude data retrieved from API.")

#     try:
#         # Extract elevation from response
#         elevation = data["results"][0]["elevation"]
#         # Cache altitude data for future use
#         altitude_cache[cache_key] = elevation
#     except (KeyError, IndexError):
#         print("Error: Could not retrieve altitude data.")
#         print(lat, lon)
#         print(data)
        
#     # Write cached data to file
#     with open(cache_file, "w") as f:
#         json.dump(altitude_cache, f)

#     return elevation

# # Function to calculate altitude for each row and add to DataFrame
# def calculate_altitude(row):
#     start_altitude = get_altitude(row['start_lat'], row['start_lng'])
#     end_altitude = get_altitude(row['end_lat'], row['end_lng'])
#     altitude_difference = end_altitude - start_altitude
#     return pd.Series([start_altitude, end_altitude, altitude_difference],
#                      index=['altitude_start', 'altitude_end', 'altitude_difference'])

# # Apply the function to each row
# altitude_data = df.apply(calculate_altitude, axis=1)

# # Add the new columns to the DataFrame
# df[['altitude_start', 'altitude_end', 'altitude_difference']] = altitude_data