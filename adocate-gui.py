import customtkinter as ctk
from tkinter import filedialog, messagebox
from core import process_photos, parse_nmea, parse_segments
import threading


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window setup
        self.title("Adocate - Add GPS Data to Photos")
        self.geometry("750x550")
        self.resizable(False, False)

        # Theme setup
        ctk.set_appearance_mode("System")  # System, Dark, or Light
        ctk.set_default_color_theme("blue")  # Themes: blue, dark-blue, green

        # Variables
        self.folder_path = ctk.StringVar()
        self.location_file_paths = []  # List to hold multiple location files
        self.file_types = []  # List of file types corresponding to each location file
        self.overwrite_gps = ctk.BooleanVar(value=False)  # Overwrite GPS flag

        # UI setup
        self.create_widgets()

    def create_widgets(self):
        """Set up the UI components."""
        # Frame for content
        frame = ctk.CTkFrame(self, corner_radius=15)
        frame.pack(pady=20, padx=20, fill="both", expand=True)

        # Title Label
        ctk.CTkLabel(frame, text="Adocate", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 5))
        ctk.CTkLabel(frame, text="Add GPS data to your photos using Google Maps or NMEA logs.",
                     font=ctk.CTkFont(size=14)).pack(pady=(0, 20))

        # Photo Folder Input
        folder_frame = ctk.CTkFrame(frame, corner_radius=10)
        folder_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(folder_frame, text="Photo Folder:", font=ctk.CTkFont(size=14)).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ctk.CTkEntry(folder_frame, textvariable=self.folder_path, width=400).grid(row=0, column=1, padx=10, pady=10, sticky="w")
        ctk.CTkButton(folder_frame, text="Select", command=self.select_folder, width=100).grid(row=0, column=2, padx=10, pady=10)

        # Location Files Input
        file_frame = ctk.CTkFrame(frame, corner_radius=10)
        file_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(file_frame, text="Location Files:", font=ctk.CTkFont(size=14)).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ctk.CTkButton(file_frame, text="Select", command=self.select_location_files, width=100).grid(row=0, column=2, padx=10, pady=10)

        self.file_list = ctk.CTkTextbox(file_frame, height=100, width=550, state="normal")
        self.file_list.grid(row=1, column=0, columnspan=3, padx=10, pady=10)

        # Overwrite Option
        ctk.CTkCheckBox(frame, text="Overwrite existing GPS data", variable=self.overwrite_gps).pack(pady=10)

        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(frame, orientation="horizontal", mode="determinate", width=500)
        self.progress_bar.pack(pady=20)
        self.progress_bar.set(0)

        # Run Button
        self.run_button = ctk.CTkButton(frame, text="Run", command=self.run_in_thread, width=200, height=40,
                                        font=ctk.CTkFont(size=16, weight="bold"))
        self.run_button.pack(pady=20)

    def select_folder(self):
        """Open a dialog to select the folder containing photos."""
        folder = filedialog.askdirectory(title="Select a Photo Folder")
        if folder:
            self.folder_path.set(folder)

    def select_location_files(self):
        """Open a dialog to select multiple location files."""
        files = filedialog.askopenfilenames(filetypes=[("All Files", "*.*")], title="Select Location Files")
        if files:
            self.location_file_paths.extend(files)
            self.detect_file_types(files)
            self.update_file_list()

    def detect_file_types(self, files):
        """Detect file types for the selected location files."""
        for file_path in files:
            try:
                if file_path.endswith(".json"):
                    self.file_types.append("json")
                elif file_path.endswith(".log") or file_path.endswith(".txt"):
                    with open(file_path, "r", encoding="utf-8") as f:
                        first_line = f.readline()
                        if first_line.startswith("$GPRMC") or first_line.startswith("$GPGGA"):
                            self.file_types.append("nmea")
                        else:
                            raise ValueError("Unknown NMEA format.")
                else:
                    raise ValueError("Unsupported file format.")
            except Exception as e:
                messagebox.showerror("Error", f"Could not detect file type for {file_path}: {e}")

    def update_file_list(self):
        """Update the displayed list of selected location files."""
        self.file_list.configure(state="normal")
        self.file_list.delete("1.0", "end")
        for file_path in self.location_file_paths:
            self.file_list.insert("end", f"{file_path}\n")
        self.file_list.configure(state="disabled")

    def update_progress(self, current, total):
        """Update the progress bar."""
        progress_value = current / total
        self.progress_bar.set(progress_value)
        self.update_idletasks()

    def run_in_thread(self):
        """Run the photo processing logic in a separate thread."""
        thread = threading.Thread(target=self.run_process, daemon=True)
        thread.start()

    def run_process(self):
        """Run the photo processing logic."""
        folder = self.folder_path.get()

        if not folder or not self.location_file_paths:
            messagebox.showerror("Error", "Please specify both a photo folder and at least one location file.")
            return

        try:
            self.run_button.configure(state="disabled")
            self.progress_bar.set(0)  # Reset progress bar

            # Combine all location data from the selected files
            all_locations = []
            for file_path, file_type in zip(self.location_file_paths, self.file_types):
                if file_type == "json":
                    all_locations.extend(parse_segments(file_path))
                elif file_type == "nmea":
                    all_locations.extend(parse_nmea(file_path))

            # Ensure all locations have a unified structure and sort by timestamp
            all_locations = [loc for loc in all_locations if loc.get("latitude") and loc.get("longitude") and loc.get("timestamp")]
            all_locations.sort(key=lambda loc: loc["timestamp"])

            # Process photos with overwrite option
            added_count, skipped_count, error_log = process_photos(
                folder, all_locations, progress_callback=self.update_progress, overwrite=self.overwrite_gps.get()
            )

            result_message = (
                f"GPS data added to {added_count} photos.\n"
                f"{skipped_count} photos were skipped.\n"
            )
            if error_log:
                result_message += f"{len(error_log)} photos could not be processed. Check the console for details."

            messagebox.showinfo("Complete", result_message)

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

        finally:
            self.run_button.configure(state="normal")


# Run the app
if __name__ == "__main__":
    app = App()
    app.mainloop()
