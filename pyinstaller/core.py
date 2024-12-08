import os
import piexif
from datetime import datetime, timezone, timedelta
from parsers import LocationParserFactory

def find_photos_recursively(directory):
    """Recursively find all photo files in a directory."""
    photo_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg')):
                full_path = os.path.join(root, file)
                if os.access(full_path, os.R_OK):
                    photo_files.append(full_path)
                else:
                    print(f"Cannot access file: {full_path}")
    return photo_files

def get_photo_timestamp(photo_path):
    """Get timestamp from photo's EXIF data."""
    from PIL import Image, ExifTags

    try:
        img = Image.open(photo_path)
        exif_data = img._getexif()
        if exif_data:
            for tag, value in exif_data.items():
                if ExifTags.TAGS.get(tag) == "DateTimeOriginal":
                    return datetime.strptime(value, "%Y:%m:%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except Exception as e:
        print(f"Error reading timestamp from {photo_path}: {e}")
    return None

def has_gps_data(photo_path):
    """Check if the photo already contains valid GPS data."""
    try:
        exif_dict = piexif.load(photo_path)
        gps_data = exif_dict.get("GPS", {})
        if gps_data and piexif.GPSIFD.GPSLatitude in gps_data and piexif.GPSIFD.GPSLongitude in gps_data:
            return True
    except Exception as e:
        print(f"Error checking GPS data for {photo_path}: {e}")
    return False

def create_gps_ifd(lat, lng):
    """Create GPS IFD (Image File Directory)."""
    def convert_to_dms(degree):
        degrees = int(degree)
        minutes = int((degree - degrees) * 60)
        seconds = round((degree - degrees - minutes / 60) * 3600, 5)
        return degrees, minutes, seconds

    lat_dms = convert_to_dms(abs(lat))
    lng_dms = convert_to_dms(abs(lng))

    gps_ifd = {
        piexif.GPSIFD.GPSLatitudeRef: b'N' if lat >= 0 else b'S',
        piexif.GPSIFD.GPSLatitude: [(lat_dms[0], 1), (lat_dms[1], 1), (int(lat_dms[2] * 10000), 10000)],
        piexif.GPSIFD.GPSLongitudeRef: b'E' if lng >= 0 else b'W',
        piexif.GPSIFD.GPSLongitude: [(lng_dms[0], 1), (lng_dms[1], 1), (int(lng_dms[2] * 10000), 10000)],
    }
    return gps_ifd

def add_gps_to_photo(photo_path, lat, lng):
    """Add GPS information to a photo."""
    try:
        gps_ifd = create_gps_ifd(lat, lng)
        exif_dict = piexif.load(photo_path)
        exif_dict["GPS"] = gps_ifd
        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, photo_path)
    except Exception as e:
        print(f"Failed to add GPS data to {photo_path}: {e}")

def parse_location_files(location_files):
    """Parse multiple location files and return a unified list of GPX-style data."""
    all_locations = []
    for file_path in location_files:
        try:
            parser = LocationParserFactory.get_parser(file_path)
            all_locations.extend(parser.parse(file_path))
        except Exception as e:
            print(f"Error parsing file {file_path}: {e}")
    # Sort locations by timestamp
    all_locations.sort(key=lambda loc: loc["timestamp"])
    return all_locations

def find_closest_location(photo_time, locations):
    """Find the closest location by timestamp."""
    closest_location = None
    min_diff = timedelta.max
    for loc in locations:
        time_diff = abs(photo_time - loc["timestamp"])
        if time_diff < min_diff:
            min_diff = time_diff
            closest_location = loc
    return closest_location

def process_photos(photo_dir, location_files, progress_callback=None, overwrite=False):
    """Process photos and add GPS data using unified GPX-style location data."""
    photo_files = find_photos_recursively(photo_dir)
    print(f"Found {len(photo_files)} photos.")

    all_locations = parse_location_files(location_files)
    print(f"Loaded {len(all_locations)} location points.")

    total = len(photo_files)
    added_count, skipped_count, error_log = 0, 0, []

    for i, photo_path in enumerate(photo_files, start=1):
        try:
            # Skip if GPS data exists and overwrite is not enabled
            if not overwrite and has_gps_data(photo_path):
                skipped_count += 1
                continue

            # Get photo timestamp
            photo_time = get_photo_timestamp(photo_path)
            if not photo_time:
                error_log.append(f"No timestamp found for: {photo_path}")
                continue

            # Find the closest location data
            closest = find_closest_location(photo_time, all_locations)
            if closest:
                add_gps_to_photo(photo_path, closest["latitude"], closest["longitude"])
                added_count += 1
            else:
                error_log.append(f"No location data found for: {photo_path}")
        except Exception as e:
            error_log.append(f"Error processing {photo_path}: {e}")

        # Update progress
        if progress_callback:
            progress_callback(i, total)

    return added_count, skipped_count, error_log

def export_to_gpx(locations, output_file):
    """Export unified location data to a GPX file."""
    import xml.etree.ElementTree as ET

    gpx = ET.Element("gpx", attrib={
        "version": "1.1",
        "creator": "Adocate",
        "xmlns": "http://www.topografix.com/GPX/1/1",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:schemaLocation": (
            "http://www.topografix.com/GPX/1/1 "
            "http://www.topografix.com/GPX/1/1/gpx.xsd"
        ),
    })

    trk = ET.SubElement(gpx, "trk")
    ET.SubElement(trk, "name").text = "Combined Location Data"

    trkseg = ET.SubElement(trk, "trkseg")
    for loc in locations:
        trkpt = ET.SubElement(trkseg, "trkpt", attrib={
            "lat": f"{loc['latitude']}",
            "lon": f"{loc['longitude']}"
        })
        ET.SubElement(trkpt, "time").text = loc["timestamp"].isoformat()

    tree = ET.ElementTree(gpx)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)
