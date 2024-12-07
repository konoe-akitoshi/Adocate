import os
import piexif
from datetime import datetime, timezone, timedelta
import json
import re
from tkinter import Tk, StringVar, messagebox, filedialog
from tkinter.ttk import Label, Button, Entry, Frame, Progressbar, Style
from PIL import Image
from PIL.ExifTags import TAGS


# --- Utility Functions ---
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
    except Exception as e:
        print(f"Error checking GPS data for {photo_path}: {e}")
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
    except Exception as e:
        print(f"Error reading timestamp for {photo_path}: {e}")
    return None


def process_photos(photo_dir, json_file, progress):
    """Process all photos in the directory to add GPS data."""
    locations = parse_segments(json_file)
    photos = [f for f in os.listdir(photo_dir) if f.lower().endswith((".jpg", ".jpeg"))]
    total = len(photos)

    added_count = 0
    skipped_count = 0

    for i, photo_file in enumerate(photos):
        photo_path = os.path.join(photo_dir, photo_file)

        if has_gps_data(photo_path):
            skipped_count += 1
            print(f"Skipping photo (already has GPS): {photo_path}")
            continue

        photo_time = get_photo_timestamp(photo_path)
        if photo_time:
            closest = find_closest_location(photo_time, locations)
            if closest:
                add_gps_to_photo(photo_path, closest["latitude"], closest["longitude"])
                added_count += 1
                print(f"Added GPS data to: {photo_path}")
        else:
            print(f"No timestamp found for: {photo_path}")

        progress["value"] = (i + 1) / total * 100
        root.update_idletasks()

    return added_count, skipped_count


# --- GUI Functions ---
def select_folder():
    folder = filedialog.askdirectory(title="Select a Photo Folder")
    if folder:
        folder_path.set(folder)


def select_json():
    file = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")], title="Select a JSON File")
    if file:
        json_path.set(file)


def run_process():
    folder = folder_path.get()
    json_file = json_path.get()
    if not folder or not json_file:
        messagebox.showerror("Error", "Please specify both a photo folder and a JSON file.")
        return

    try:
        progress_bar["value"] = 0
        added_count, skipped_count = process_photos(folder, json_file, progress_bar)
        messagebox.showinfo(
            "Complete",
            f"GPS data has been added to {added_count} photos.\n"
            f"{skipped_count} photos were skipped (already had GPS)."
        )
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")


# --- GUI Setup ---
root = Tk()
root.title("GPS Adder Tool")
root.geometry("500x250")
root.resizable(False, False)

style = Style()
style.configure("TLabel", font=("Segoe UI", 11))
style.configure("TButton", font=("Segoe UI", 10))

frame = Frame(root, padding=10)
frame.grid(row=0, column=0, sticky="nsew")

folder_path = StringVar()
json_path = StringVar()

Label(frame, text="Photo Folder:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
Entry(frame, textvariable=folder_path, width=40).grid(row=0, column=1, padx=10, pady=10, sticky="w")
Button(frame, text="Select Folder", command=select_folder).grid(row=0, column=2, padx=10, pady=10)

Label(frame, text="JSON File:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
Entry(frame, textvariable=json_path, width=40).grid(row=1, column=1, padx=10, pady=10, sticky="w")
Button(frame, text="Select JSON", command=select_json).grid(row=1, column=2, padx=10, pady=10)

progress_bar = Progressbar(frame, orient="horizontal", mode="determinate", length=400)
progress_bar.grid(row=2, column=0, columnspan=3, padx=10, pady=20)

Button(frame, text="Run", command=run_process).grid(row=3, column=0, columnspan=3, pady=20)

root.mainloop()
