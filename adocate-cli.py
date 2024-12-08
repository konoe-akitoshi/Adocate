import argparse
from core import process_photos

def main():
    parser = argparse.ArgumentParser(description="Add GPS data to photos using Google Maps location history.")
    parser.add_argument("photo_dir", help="Path to the directory containing photos.")
    parser.add_argument("json_file", help="Path to the Google Maps location history JSON file.")
    args = parser.parse_args()

    print("Processing photos...")
    added_count, skipped_count, error_log = process_photos(args.photo_dir, args.json_file)

    print(f"GPS data added to {added_count} photos.")
    print(f"{skipped_count} photos already had GPS data.")
    if error_log:
        print(f"{len(error_log)} photos could not be processed:")
        for error in error_log:
            print(error)

if __name__ == "__main__":
    main()
