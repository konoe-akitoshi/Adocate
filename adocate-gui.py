import customtkinter as ctk
from tkinter import filedialog, messagebox
from core import process_photos
import threading


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window setup
        self.title("Adocate - Add GPS Data to Photos")
        self.geometry("750x450")
        self.resizable(False, False)

        # Theme setup
        ctk.set_appearance_mode("System")  # System, Dark, or Light
        ctk.set_default_color_theme("blue")  # Themes: blue, dark-blue, green

        # Variables
        self.folder_path = ctk.StringVar()
        self.location_file_path = ctk.StringVar()
        self.file_type = None  # Automatically detected file type

        # UI setup
        self.create_widgets()

    def create_widgets(self):
        """Set up the UI components."""
        # Frame for content
        frame = ctk.CTkFrame(self, corner_radius=15)
        frame.pack(pady=20, padx=20, fill="both", expand=True)

        # Title Label
        ctk.CTkLabel(frame, text="Adocate", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 5))
        ctk.CTkLabel(frame, text="Add GPS data to your photos using Google Maps or NMEA log.",
                     font=ctk.CTkFont(size=14)).pack(pady=(0, 20))

        # Photo Folder Input
        folder_frame = ctk.CTkFrame(frame, corner_radius=10)
        folder_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(folder_frame, text="Photo Folder:", font=ctk.CTkFont(size=14)).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ctk.CTkEntry(folder_frame, textvariable=self.folder_path, width=400).grid(row=0, column=1, padx=10, pady=10, sticky="w")
        ctk.CTkButton(folder_frame, text="Select", command=self.select_folder, width=100).grid(row=0, column=2, padx=10, pady=10)

        # Location File Input
        file_frame = ctk.CTkFrame(frame, corner_radius=10)
        file_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(file_frame, text="Location File:", font=ctk.CTkFont(size=14)).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ctk.CTkEntry(file_frame, textvariable=self.location_file_path, width=400).grid(row=0, column=1, padx=10, pady=10, sticky="w")
        ctk.CTkButton(file_frame, text="Select", command=self.select_location_file, width=100).grid(row=0, column=2, padx=10, pady=10)

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

    def select_location_file(self):
        """Open a dialog to select the location data file."""
        file = filedialog.askopenfilename(filetypes=[("All Files", "*.*")], title="Select a Location File")
        if file:
            self.location_file_path.set(file)
            self.detect_file_type(file)

    def detect_file_type(self, file_path):
        """Detect the type of location file based on extension or content."""
        try:
            if file_path.endswith(".json"):
                self.file_type = "json"
            elif file_path.endswith(".log") or file_path.endswith(".txt"):
                with open(file_path, "r", encoding="utf-8") as f:
                    first_line = f.readline()
                    if first_line.startswith("$GPRMC") or first_line.startswith("$GPGGA"):
                        self.file_type = "nmea"
                    else:
                        raise ValueError("Unknown NMEA format.")
            else:
                raise ValueError("Unsupported file format.")
        except Exception as e:
            self.file_type = None
            messagebox.showerror("Error", f"Could not detect file type: {e}")

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
        location_file = self.location_file_path.get()

        if not folder or not location_file:
            messagebox.showerror("Error", "Please specify both a photo folder and a location file.")
            return

        if not self.file_type:
            messagebox.showerror("Error", "File type could not be detected. Please check the location file.")
            return

        try:
            self.run_button.configure(state="disabled")
            self.progress_bar.set(0)  # Reset progress bar

            added_count, skipped_count, error_log = process_photos(
                folder, location_file, self.file_type, progress_callback=self.update_progress
            )

            result_message = (
                f"GPS data added to {added_count} photos.\n"
                f"{skipped_count} photos already had GPS data.\n"
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
