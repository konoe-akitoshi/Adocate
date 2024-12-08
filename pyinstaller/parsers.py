from abc import ABC, abstractmethod
from datetime import datetime, timezone, time
import json  # 修正: json モジュールをインポート


class LocationParser(ABC):
    """Abstract base class for location parsers."""
    @abstractmethod
    def parse(self, file_path):
        """Parse the file and return a list of unified location data."""
        pass


class JSONLocationParser(LocationParser):
    """Parser for Google Takeout JSON files."""
    def parse(self, file_path):
        locations = []
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for segment in data.get("semanticSegments", []):
            if "timelinePath" in segment:
                for path in segment["timelinePath"]:
                    try:
                        lat, lng = float(path["point"].split(",")[0]), float(path["point"].split(",")[1])
                        timestamp = datetime.strptime(path["time"], "%Y-%m-%dT%H:%M:%S.%f%z").astimezone(timezone.utc)
                        locations.append({"latitude": lat, "longitude": lng, "timestamp": timestamp})
                    except (ValueError, KeyError):
                        continue
        return locations


class NMEALocationParser(LocationParser):
    """Parser for NMEA log files."""
    def parse(self, file_path):
        locations = []
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line in lines:
            if line.startswith("$GPRMC") or line.startswith("$GNRMC"):
                parts = line.split(",")
                if len(parts) < 12 or parts[2] != "A":  # Ensure valid data
                    continue

                try:
                    lat = self.nmea_to_decimal(parts[3], parts[4])
                    lng = self.nmea_to_decimal(parts[5], parts[6])
                    utc_time = self.parse_nmea_time(parts[1])
                    date = self.parse_nmea_date(parts[9])
                    timestamp = datetime.combine(date, utc_time).replace(tzinfo=timezone.utc)

                    locations.append({"latitude": lat, "longitude": lng, "timestamp": timestamp})
                except (ValueError, IndexError):
                    continue
        return locations

    def nmea_to_decimal(self, value, direction):
        if len(value.split(".")[0]) <= 4:  # Latitude (DDMM.MMMM)
            degrees = int(value[:2])
            minutes = float(value[2:])
        else:  # Longitude (DDDMM.MMMM)
            degrees = int(value[:3])
            minutes = float(value[3:])

        decimal = degrees + (minutes / 60)
        return -decimal if direction in ("S", "W") else decimal

    def parse_nmea_time(self, nmea_time):
        """Parse NMEA time format (hhmmss.ss) into time object."""
        hours = int(nmea_time[:2])
        minutes = int(nmea_time[2:4])
        seconds = int(float(nmea_time[4:]))
        return time(hour=hours, minute=minutes, second=seconds)

    def parse_nmea_date(self, nmea_date):
        """Parse NMEA date format (ddmmyy) into date object."""
        day = int(nmea_date[:2])
        month = int(nmea_date[2:4])
        year = 2000 + int(nmea_date[4:])  # Assume 21st century
        return datetime(year, month, day).date()


class LocationParserFactory:
    """Factory for creating location parsers based on file type."""
    @staticmethod
    def get_parser(file_path):
        if file_path.endswith(".json"):
            return JSONLocationParser()
        elif file_path.endswith(".log") or file_path.endswith(".txt"):
            return NMEALocationParser()
        else:
            raise ValueError(f"Unsupported file format: {file_path}")
