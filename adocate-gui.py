import customtkinter as ctk
from tkinter import filedialog, messagebox
from core import process_photos


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window setup
        self.title("Adocate - Add GPS Data to Photos")
        self.geometry("700x400")
        self.resizable(False, False)

        # Theme setup
        ctk.set_appearance_mode("System")  # System, Dark, or Light
        ctk.set_default_color_theme("blue")  # Themes: blue, dark-blue, green

        # Variables
        self.folder_path = ctk.StringVar()
        self.json_path = ctk.StringVar()

        # UI setup
        self.create_widgets()

    def create_widgets(self):
        """Set up the UI components."""
        # Frame for content
        frame = ctk.CTkFrame(self, corner_radius=15)
        frame.pack(pady=20, padx=20, fill="both", expand=True)

        # Title Label
        ctk.CTkLabel(frame, text="Adocate", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 5))
        ctk.CTkLabel(frame, text="Add GPS data to your photos using Google Maps location history.",
                     font=ctk.CTkFont(size=14)).pack(pady=(0, 20))

        # Photo Folder Input
        folder_frame = ctk.CTkFrame(frame, corner_radius=10)
        folder_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(folder_frame, text="Photo Folder:", font=ctk.CTkFont(size=14)).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ctk.CTkEntry(folder_frame, textvariable=self.folder_path, width=400).grid(row=0, column=1, padx=10, pady=10, sticky="w")
        ctk.CTkButton(folder_frame, text="Select", command=self.select_folder, width=100).grid(row=0, column=2, padx=10, pady=10)

        # JSON File Input
        json_frame = ctk.CTkFrame(frame, corner_radius=10)
        json_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(json_frame, text="JSON File:", font=ctk.CTkFont(size=14)).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ctk.CTkEntry(json_frame, textvariable=self.json_path, width=400).grid(row=0, column=1, padx=10, pady=10, sticky="w")
        ctk.CTkButton(json_frame, text="Select", command=self.select_json, width=100).grid(row=0, column=2, padx=10, pady=10)

        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(frame, orientation="horizontal", mode="determinate", width=500)
        self.progress_bar.pack(pady=20)
        self.progress_bar.set(0)

        # Run Button
        ctk.CTkButton(frame, text="Run", command=self.run_process, width=200, height=40,
                      font=ctk.CTkFont(size=16, weight="bold")).pack(pady=20)

    def select_folder(self):
        """Open a dialog to select the folder containing photos."""
        folder = filedialog.askdirectory(title="Select a Photo Folder")
        if folder:
            self.folder_path.set(folder)

    def select_json(self):
        """Open a dialog to select the Google Maps location history JSON file."""
        file = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")], title="Select a JSON File")
        if file:
            self.json_path.set(file)

    def update_progress(self, current, total):
        """Update the progress bar."""
        progress_value = current / total
        self.progress_bar.set(progress_value)
        self.update_idletasks()

    def run_process(self):
        """Run the photo processing logic."""
        folder = self.folder_path.get()
        json_file = self.json_path.get()

        if not folder or not json_file:
            messagebox.showerror("Error", "Please specify both a photo folder and a JSON file.")
            return

        try:
            self.progress_bar.set(0)  # Reset progress bar
            added_count, skipped_count, error_log = process_photos(
                folder, json_file, progress_callback=self.update_progress
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


# Run the app
if __name__ == "__main__":
    app = App()
    app.mainloop()
