# Adocate
Adocate is a tool that leverages your Google Maps location history to add GPS location data (latitude and longitude) to your photos. Perfect for photographers or anyone who wants to enrich their images with geotagging information based on historical data.

Adocate（アドケイト） は、Googleマップのロケーション履歴を活用して、写真にGPS位置情報（緯度・経度）を追加するツールです。撮影地を記録したい写真愛好家や、位置情報の管理を効率化したい方に最適です。

# Features / 特徴
- **Add GPS Data / GPSデータの追加:**  
Automatically adds latitude and longitude to your photos' EXIF metadata.  
写真のEXIFメタデータに緯度・経度を自動で追加します。

- **Leverages Google Maps Location History / Googleマップ履歴を利用:**  
Uses your Google location data (.json file) to geotag photos.  
Googleマップのロケーション履歴（JSONファイル）を使用して位置情報を付加します。

- **Timestamp Matching / タイムスタンプの一致:**  
Matches photo timestamps with location data for precise geotagging.  
写真のタイムスタンプとロケーションデータを照合して正確なタグ付けを行います。

- **Smart Skipping / スキップ機能:**  
Skips photos that already contain GPS information.  
既にGPSデータを含む写真はスキップされます。

- **User-Friendly Interface / ユーザーフレンドリーなインターフェース:**  
Simple and clean GUI for easy operation.  
シンプルで使いやすいGUIを提供します。

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

## Step 1: Download Google Maps Location History
1. Go to [Google Takeout](https://takeout.google.com/).
2. Select **Location History**, export it as a `.json` file, and download it.

---

## Step 2: Prepare Your Photos
1. Place the photos you want to process in a directory.
2. Supported formats: `.jpg`, `.jpeg`.

---

## Step 3: Run Adocate

### Option 1: Using the EXE File (Windows)

If you are on **Windows** and have the pre-built `adocate.exe` file:

1. Download the `adocate.exe` file from the [Releases](https://github.com/your-username/adocate/releases) page.
2. Double-click on the `adocate.exe` file to launch the graphical interface.
3. In the GUI:
   - Select the folder containing your photos.
   - Select the exported Google Maps location history JSON file.
   - Click the **Run** button to process the photos.
4. The tool will add GPS data to your photos and notify you upon completion.

### Option 2: Using the Binary File (Linux)

Clone this repository:

```bash
git clone https://github.com/your-username/adocate.git
cd adocate
```
#### GUI Version
Launch the tool:
```bash
python adocate-gui.py
```

#### CLI Version
```bash
python adocate-cli.py /path/to/photo/folder /path/to/location_history.json
```

Use the GUI:

Select the folder containing your photos.
Select the exported Google Maps location history JSON file.
Click Run to add GPS data to your photos.
Check Your Photos:

The tool will update your photos with GPS data directly in the EXIF metadata.

# Screenshots
![image](https://github.com/user-attachments/assets/df6bcbbf-3a96-4e92-a837-5c2553775da7)
