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


def parse_nmea_time(nmea_time):
    """Parse NMEA time format (hhmmss.ss) into timedelta."""
    try:
        hours = int(nmea_time[:2])
        minutes = int(nmea_time[2:4])
        seconds = float(nmea_time[4:])
        return timedelta(hours=hours, minutes=minutes, seconds=seconds)
    except (ValueError, IndexError):
        return None


def parse_nmea_date(nmea_date):
    """Parse NMEA date format (ddmmyy) into a datetime object."""
    try:
        day = int(nmea_date[:2])
        month = int(nmea_date[2:4])
        year = 2000 + int(nmea_date[4:])  # Assume 21st century
        return datetime(year, month, day)
    except (ValueError, IndexError):
        return None


def parse_nmea(nmea_file):
    """
    Parse NMEA log file for GPS data.
    Extracts latitude, longitude, and UTC timestamp from $GPRMC sentences.
    """
    locations = []
    try:
        with open(nmea_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line in lines:
            if line.startswith("$GPRMC") or line.startswith("$GNRMC"):
                parts = line.split(",")
                if len(parts) < 12 or parts[2] != "A":  # Ensure valid data
                    continue
                
                # Extract time (hhmmss.ss) and date (ddmmyy)
                nmea_time = parse_nmea_time(parts[1])
                nmea_date = parse_nmea_date(parts[9])
                if not nmea_time or not nmea_date:
                    continue
                timestamp = datetime.combine(nmea_date, datetime.min.time(), tzinfo=timezone.utc) + nmea_time

                # Extract latitude and longitude
                latitude = nmea_to_decimal(parts[3], parts[4])  # dddmm.mmmm, N/S
                longitude = nmea_to_decimal(parts[5], parts[6])  # dddmm.mmmm, E/W
                if latitude is None or longitude is None:
                    continue

                # Append to locations
                locations.append({
                    "latitude": latitude,
                    "longitude": longitude,
                    "timestamp": timestamp
                })

    except Exception as e:
        print(f"Error parsing NMEA file: {e}")
    return locations


def nmea_to_decimal(value, direction):
    """Convert NMEA latitude/longitude (dddmm.mmmm) to decimal degrees."""
    try:
        # Latitude is DDMM.MMMM, Longitude is DDDMM.MMMM
        if len(value.split(".")[0]) <= 4:  # Latitude (DDMM.MMMM)
            degrees = int(value[:2])
            minutes = float(value[2:])
        else:  # Longitude (DDDMM.MMMM)
            degrees = int(value[:3])
            minutes = float(value[3:])

        decimal = degrees + (minutes / 60)
        if direction in ("S", "W"):  # South or West means negative
            decimal *= -1
        return decimal
    except (ValueError, IndexError):
        return None


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


def find_photos_recursively(directory):
    """Recursively find all photo files in the directory."""
    photo_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg")):
                photo_files.append(os.path.join(root, file))
    return photo_files


def process_photos(photo_dir, location_file, file_type, progress_callback=None):
    """Process all photos to add GPS data, supporting multiple location data types."""
    if file_type == "json":
        locations = parse_segments(location_file)
    elif file_type == "nmea":
        locations = parse_nmea(location_file)
    else:
        raise ValueError("Unsupported file type")

    photo_files = find_photos_recursively(photo_dir)
    total = len(photo_files)

    added_count = 0
    skipped_count = 0
    error_log = []

    for i, photo_path in enumerate(photo_files, start=1):
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
            error_log.append(f"Error processing {photo_path}: {e}")

        if progress_callback:
            progress_callback(i, total)

    return added_count, skipped_count, error_log
