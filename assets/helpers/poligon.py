from shapely.geometry import Point, Polygon


def point_in_zone(lat, lon, polygon_coords):
    if not polygon_coords:
        return False

    ring = polygon_coords[0]  
    polygon = Polygon(ring)
    point = Point(lon, lat)  

    return polygon.contains(point) or polygon.touches(point)