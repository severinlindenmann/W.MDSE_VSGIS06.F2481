import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import json
import os
import math

# def is_inside_boundary(df, boundary='city'):
#   path = '../data/opendata/'

#   if boundary == 'district':
#     gdf_boundary = gpd.read_file(f'{path}quartiere_luzern.json')
#     gdf_boundary.to_crs(epsg=4326)
#   elif boundary == 'city':
#     gdf_boundary = gpd.read_file(f'{path}stadt_luzern_grenzen.json')
#     gdf_boundary.to_crs(epsg=4326)
#   elif boundary == 'canton':
#     gdf_boundary = gpd.read_file(f'{path}kanton_luzern_grenzen.json')
#     gdf_boundary.to_crs(epsg=4326)
#   else:
#     print('Boundary not found')


#   # Create a list of Point objects from lat and lon columns in your Pandas DataFrame
#   points = [Point(lon, lat) for lat, lon in zip(df['lat'], df['lon'])]

#   # Create a GeoSeries of points
#   point_series = gpd.GeoSeries(points)

#   if boundary == 'city' or boundary == 'canton':   
#     df[f'inside_{boundary}'] = point_series.within(gdf_boundary.geometry.iloc[0])
#     return df
  
#   elif boundary == 'district':
#     df['inside_district'] = None

#     # Iterate through the districts and check if each point is within a district
#     for district_name, district_geometry in zip(gdf_boundary['NAME'], gdf_boundary['geometry']):
#         for index, point in enumerate(point_series):
#             if point.within(district_geometry):
#                 df.at[index, 'inside_district'] = district_name

#     return df

# File path for storing cached altitude data
cache_file = "data/geodata/altitude.json"

# Load cached altitude data from file, if available
if os.path.exists(cache_file):
    with open(cache_file, "r") as f:
        try:
            altitude_cache = json.load(f)
        except json.JSONDecodeError:
            print("Error loading altitude file")
else:
    print("Error loading altitude file")

def altitude(lat, lon):
    """
    Load altitude data for the region of Luzern.

    Args:
    lat (float): Latitude
    lon (float): Longitude

    Returns:
    float: Altitude in meters
    """

    def get_cache_key(lat, lon):
        return f"{lat},{lon}"

    cache_key = get_cache_key(lat, lon)

    if cache_key in altitude_cache:
        return altitude_cache[cache_key]
    else:
        print("No altitude data found for", lat, lon)
        return 0

def distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two points on the Earth's surface.

    Args:
    lat1 (float): Latitude of the first point
    lon1 (float): Longitude of the first point
    lat2 (float): Latitude of the second point
    lon2 (float): Longitude of the second point

    Returns:
    float: The distance between the two points in kilometers
    """
    # Radius of the Earth in kilometers
    R = 6371.0

    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Calculate the differences in latitude and longitude
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Calculate the distance using the Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    distance = distance * 1000

    return distance