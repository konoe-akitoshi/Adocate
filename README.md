# Adocate
Adocate is a tool that leverages your Google Maps location history to add GPS location data (latitude and longitude) to your photos. Perfect for photographers or anyone who wants to enrich their images with geotagging information based on historical data.

# Features
Add GPS Data: Automatically adds latitude and longitude to your photos' EXIF metadata.
Leverages Google Maps Location History: Uses your Google location data (.json file) to geotag photos.
Timestamp Matching: Matches photo timestamps with location data for precise geotagging.
Smart Skipping: Skips photos that already contain GPS information.
User-Friendly Interface: Simple and clean GUI for easy operation.

# Requirements
Python 3.8 or higher
Required Python packages:
piexif
Pillow
tkinter
Install the dependencies using:

```bash
pip install piexif Pillow
```

# How to Use
Download Google Maps Location History:

Go to Google Takeout.
Select Location History, export it as a .json file, and download it.
Prepare Your Photos:

Place your photos in a directory. Supported formats: .jpg, .jpeg.
Run Adocate:

Clone this repository:

```bash
git clone https://github.com/your-username/adocate.git
cd adocate
```

Launch the tool:

```bash
python adocate.py
```

Use the GUI:

Select the folder containing your photos.
Select the exported Google Maps location history JSON file.
Click Run to add GPS data to your photos.
Check Your Photos:

The tool will update your photos with GPS data directly in the EXIF metadata.

# Screenshots
