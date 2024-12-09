import json
from datetime import datetime
from typing import List, Dict


class JSONLocationParser:
    """Parser for new JSON format with latitudeE7 and longitudeE7 fields."""

    @staticmethod
    def parse(file_path: str) -> List[Dict]:
        """Parse the JSON file and return unified location data."""
        locations = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for entry in data.get("locations", []):
                try:
                    timestamp = datetime.fromtimestamp(float(entry["timestampMs"]) / 1000)
                    longitude = float(entry["longitudeE7"]) / 1e7
                    latitude = float(entry["latitudeE7"]) / 1e7

                    locations.append({
                        "latitude": latitude,
                        "longitude": longitude,
                        "timestamp": timestamp,
                    })
                except KeyError as e:
                    print(f"Skipping entry due to missing key: {e}")

        except Exception as e:
            print(f"Error parsing file {file_path}: {e}")

        return locations


class OldJSONLocationParser:
    """Parser for old JSON format with semanticSegments."""

    @staticmethod
    def parse(file_path: str) -> List[Dict]:
        """Parse the old JSON format and return unified location data."""
        locations = []
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for segment in data.get("semanticSegments", []):
            if "timelinePath" in segment:
                for path in segment["timelinePath"]:
                    try:
                        # Remove ° symbol before converting to float
                        latitude, longitude = map(
                            lambda x: float(x.replace("°", "").strip()), 
                            path["point"].split(",")
                        )
                        timestamp = datetime.strptime(path["time"], "%Y-%m-%dT%H:%M:%S.%f%z")
                        locations.append({
                            "latitude": latitude,
                            "longitude": longitude,
                            "timestamp": timestamp,
                        })
                    except Exception as e:
                        print(f"Error parsing old JSON entry: {e}")

        return locations


class NMEALocationParser:
    """Parser for NMEA location format (e.g., GPS logs)."""

    @staticmethod
    def parse(file_path: str) -> List[Dict]:
        locations = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("$GPGGA"):
                    try:
                        parts = line.split(",")
                        latitude = NMEALocationParser.convert_to_decimal(parts[2], parts[3])
                        longitude = NMEALocationParser.convert_to_decimal(parts[4], parts[5])
                        timestamp = NMEALocationParser.parse_timestamp(parts[1])
                        locations.append({
                            "latitude": latitude,
                            "longitude": longitude,
                            "timestamp": timestamp,
                        })
                    except Exception as e:
                        print(f"Error parsing NMEA line: {line.strip()} - {e}")
        return locations

    @staticmethod
    def convert_to_decimal(coord, direction):
        """Convert NMEA coordinates to decimal degrees."""
        if not coord or not direction:
            raise ValueError("Invalid NMEA coordinate or direction.")
        degrees = int(float(coord) / 100)
        minutes = float(coord) - (degrees * 100)
        decimal = degrees + (minutes / 60)
        if direction in ["S", "W"]:
            decimal *= -1
        return decimal

    @staticmethod
    def parse_timestamp(time_str):
        """Parse NMEA UTC time to datetime."""
        if not time_str:
            raise ValueError("Invalid NMEA time string.")
        hour = int(time_str[:2])
        minute = int(time_str[2:4])
        second = int(float(time_str[4:]))
        return datetime.utcnow().replace(hour=hour, minute=minute, second=second, microsecond=0)


class GoogleTimelineParser:
    """Parser for Google Timeline JSON format."""

    @staticmethod
    def parse(file_path: str) -> List[Dict]:
        """Parse the Google Timeline JSON format and return unified location data."""
        locations = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for obj in data.get("timelineObjects", []):
                # Handle activitySegment
                if "activitySegment" in obj:
                    segment = obj["activitySegment"]
                    try:
                        # Check for required keys in activitySegment
                        if "startLocation" not in segment or "endLocation" not in segment:
                            print(f"Skipping activitySegment due to missing start or end location: {segment}")
                            continue

                        start_lat = segment["startLocation"]["latitudeE7"] / 1e7
                        start_lng = segment["startLocation"]["longitudeE7"] / 1e7
                        end_lat = segment["endLocation"]["latitudeE7"] / 1e7
                        end_lng = segment["endLocation"]["longitudeE7"] / 1e7
                        start_time = datetime.fromisoformat(segment["duration"]["startTimestamp"].replace("Z", "+00:00"))
                        end_time = datetime.fromisoformat(segment["duration"]["endTimestamp"].replace("Z", "+00:00"))

                        locations.append({
                            "latitude": start_lat,
                            "longitude": start_lng,
                            "timestamp": start_time,
                        })
                        locations.append({
                            "latitude": end_lat,
                            "longitude": end_lng,
                            "timestamp": end_time,
                        })
                    except KeyError as e:
                        print(f"Skipping activitySegment due to missing key: {e}")

                # Handle placeVisit
                if "placeVisit" in obj:
                    visit = obj["placeVisit"]
                    try:
                        # Check for required keys in placeVisit
                        if "location" not in visit or "latitudeE7" not in visit["location"] or "longitudeE7" not in visit["location"]:
                            print(f"Skipping placeVisit due to missing location data: {visit}")
                            continue

                        location = visit["location"]
                        latitude = location["latitudeE7"] / 1e7
                        longitude = location["longitudeE7"] / 1e7
                        start_time = datetime.fromisoformat(visit["duration"]["startTimestamp"].replace("Z", "+00:00"))
                        end_time = datetime.fromisoformat(visit["duration"]["endTimestamp"].replace("Z", "+00:00"))

                        locations.append({
                            "latitude": latitude,
                            "longitude": longitude,
                            "timestamp": start_time,
                        })
                        locations.append({
                            "latitude": latitude,
                            "longitude": longitude,
                            "timestamp": end_time,
                        })
                    except KeyError as e:
                        print(f"Skipping placeVisit due to missing key: {e}")

        except Exception as e:
            print(f"Error parsing Google Timeline JSON: {e}")

        return locations


class LocationParserFactory:
    """Factory to determine and return the appropriate parser."""

    @staticmethod
    def get_parser(file_path: str):
        """Determine the correct parser based on file structure."""
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if "timelineObjects" in data:
                    return GoogleTimelineParser
                if "locations" in data:
                    return JSONLocationParser
                if "semanticSegments" in data:
                    return OldJSONLocationParser
            except json.JSONDecodeError:
                with open(file_path, "r", encoding="utf-8") as file:
                    first_line = file.readline()
                    if first_line.startswith("$GPGGA"):
                        return NMEALocationParser

        raise ValueError("Unknown file format.")


def parse_location_files(file_paths: List[str]) -> List[Dict]:
    """Parse multiple location files and combine into a unified format."""
    all_locations = []

    for file_path in file_paths:
        try:
            parser_class = LocationParserFactory.get_parser(file_path)
            locations = parser_class.parse(file_path)
            all_locations.extend(locations)
        except Exception as e:
            print(f"Error parsing file {file_path}: {e}")

    return sorted(all_locations, key=lambda x: x["timestamp"])
