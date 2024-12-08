# core.py
import os
import piexif
from datetime import datetime, timezone, timedelta
import json
import re
from PIL import Image
from PIL.ExifTags import TAGS


def parse_timestamp(timestamp):
    """Convert ISO 8601 timestamp to datetime object."""
    return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f%z")


def parse_segments(json_file):
    """Extract location data (latitude, longitude, timestamp) from JSON file."""
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    locations = []
    for segment in data.get("semanticSegments", []):
        for path in segment.get("timelinePath", []):
            try:
                point = re.sub(r"[^\d.,-]", "", path["point"])
                lat, lng = map(float, point.split(","))
                timestamp = parse_timestamp(path["time"])
                locations.append({"latitude": lat, "longitude": lng, "timestamp": timestamp})
            except (ValueError, AttributeError):
                continue
    return locations


def find_closest_location(photo_time, locations):
    """Find the location with the timestamp closest to the given photo timestamp."""
    return min(locations, key=lambda loc: abs(photo_time - loc["timestamp"]), default=None)


def convert_to_dms(degree):
    """Convert decimal degrees to degrees, minutes, and seconds."""
    degrees = int(degree)
    minutes = int((degree - degrees) * 60)
    seconds = round((degree - degrees - minutes / 60) * 3600, 5)
    return degrees, minutes, seconds


def create_gps_ifd(lat, lng):
    """Create GPS data structure for EXIF."""
    lat_dms = convert_to_dms(abs(lat))
    lng_dms = convert_to_dms(abs(lng))
    return {
        piexif.GPSIFD.GPSLatitudeRef: b'N' if lat >= 0 else b'S',
        piexif.GPSIFD.GPSLatitude: [(lat_dms[0], 1), (lat_dms[1], 1), (int(lat_dms[2] * 10000), 10000)],
        piexif.GPSIFD.GPSLongitudeRef: b'E' if lng >= 0 else b'W',
        piexif.GPSIFD.GPSLongitude: [(lng_dms[0], 1), (lng_dms[1], 1), (int(lng_dms[2] * 10000), 10000)],
    }


def has_gps_data(photo_path):
    """Check if the photo already contains valid GPS data."""
    try:
        exif_dict = piexif.load(photo_path)
        gps_data = exif_dict.get("GPS", {})
        return piexif.GPSIFD.GPSLatitude in gps_data and piexif.GPSIFD.GPSLongitude in gps_data
    except Exception:
        return False


def add_gps_to_photo(photo_path, lat, lng):
    """Add GPS data to the specified photo."""
    gps_ifd = create_gps_ifd(lat, lng)
    exif_dict = piexif.load(photo_path)
    exif_dict["GPS"] = gps_ifd
    piexif.insert(piexif.dump(exif_dict), photo_path)


def get_photo_timestamp(photo_path):
    """Retrieve the timestamp from the photo's EXIF data."""
    try:
        img = Image.open(photo_path)
        exif_data = img._getexif()
        if exif_data:
            for tag, value in exif_data.items():
                if TAGS.get(tag) == "DateTimeOriginal":
                    return datetime.strptime(value, "%Y:%m:%d %H:%M:%S").replace(tzinfo=timezone(timedelta(hours=9)))
    except Exception:
        pass
    return None


def process_photos(photo_dir, json_file):
    """Process all photos in the directory to add GPS data."""
    locations = parse_segments(json_file)
    photos = [f for f in os.listdir(photo_dir) if f.lower().endswith((".jpg", ".jpeg"))]
    total = len(photos)

    added_count = 0
    skipped_count = 0
    error_log = []

    for photo_file in photos:
        photo_path = os.path.join(photo_dir, photo_file)

        try:
            if has_gps_data(photo_path):
                skipped_count += 1
                continue

            photo_time = get_photo_timestamp(photo_path)
            if not photo_time:
                error_log.append(f"No timestamp found for: {photo_path}")
                continue

            closest = find_closest_location(photo_time, locations)
            if closest:
                add_gps_to_photo(photo_path, closest["latitude"], closest["longitude"])
                added_count += 1
            else:
                error_log.append(f"No location data found for: {photo_path}")
        except Exception as e:
            # キャッチされなかったエラーをログに追加
            error_log.append(f"Error processing {photo_path}: {e}")

    return added_count, skipped_count, error_log
