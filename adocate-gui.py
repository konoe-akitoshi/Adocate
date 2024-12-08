import customtkinter as ctk
from tkinter import filedialog, messagebox
from core import process_photos, parse_location_files, export_to_gpx
import threading


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window setup
        self.title("Adocate - Add GPS Data to Photos")
        self.geometry("750x600")
        self.resizable(False, False)

        # Theme setup
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Variables
        self.folder_path = ctk.StringVar()
        self.location_file_paths = []  # List to hold multiple location files
        self.unified_locations = []  # Holds unified location data
        self.overwrite_gps = ctk.BooleanVar(value=False)  # Overwrite GPS flag

        # UI setup
        self.create_widgets()

    def create_widgets(self):
        """Set up the UI components."""
        frame = ctk.CTkFrame(self, corner_radius=15)
        frame.pack(pady=20, padx=20, fill="both", expand=True)

        ctk.CTkLabel(frame, text="Adocate", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 5))
        ctk.CTkLabel(frame, text="Add GPS data to your photos using various location files.",
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

        self.file_list = ctk.CTkTextbox(file_frame, height=150, width=550, state="normal")
        self.file_list.grid(row=1, column=0, columnspan=3, padx=10, pady=10)

        # Overwrite Option
        ctk.CTkCheckBox(frame, text="Overwrite existing GPS data", variable=self.overwrite_gps).pack(pady=10)

        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(frame, orientation="horizontal", mode="determinate", width=500)
        self.progress_bar.pack(pady=20)
        self.progress_bar.set(0)

        # Run and Export Buttons
        button_frame = ctk.CTkFrame(frame, corner_radius=10)
        button_frame.pack(pady=20, fill="x")

        self.run_button = ctk.CTkButton(button_frame, text="Run", command=self.run_in_thread, width=150, height=40,
                                        font=ctk.CTkFont(size=16, weight="bold"))
        self.run_button.pack(side="left", padx=20)

        ctk.CTkButton(button_frame, text="Export GPX", command=self.export_gpx, width=150, height=40,
                      font=ctk.CTkFont(size=16, weight="bold")).pack(side="right", padx=20)

    def select_folder(self):
        folder = filedialog.askdirectory(title="Select a Photo Folder")
        if folder:
            self.folder_path.set(folder)

    def select_location_files(self):
        files = filedialog.askopenfilenames(filetypes=[("All Files", "*.*")], title="Select Location Files")
        if files:
            self.location_file_paths.extend(files)
            self.update_file_list()

    def update_file_list(self):
        self.file_list.configure(state="normal")
        self.file_list.delete("1.0", "end")
        for file_path in self.location_file_paths:
            self.file_list.insert("end", f"{file_path}\n")
        self.file_list.configure(state="disabled")

    def update_progress(self, current, total):
        progress_value = current / total
        self.progress_bar.set(progress_value)
        self.update_idletasks()

    def run_in_thread(self):
        thread = threading.Thread(target=self.run_process, daemon=True)
        thread.start()

    def run_process(self):
        folder = self.folder_path.get()
        if not folder or not self.location_file_paths:
            messagebox.showerror("Error", "Please specify both a photo folder and at least one location file.")
            return

        try:
            self.run_button.configure(state="disabled")
            self.progress_bar.set(0)

            self.unified_locations = parse_location_files(self.location_file_paths)
            added_count, skipped_count, error_log = process_photos(
                folder, self.location_file_paths, progress_callback=self.update_progress, overwrite=self.overwrite_gps.get()
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

    def export_gpx(self):
        if not self.location_file_paths:
            messagebox.showerror("Error", "Please specify at least one location file.")
            return

        try:
            self.unified_locations = parse_location_files(self.location_file_paths)
            output_file = filedialog.asksaveasfilename(
                defaultextension=".gpx", filetypes=[("GPX Files", "*.gpx")], title="Save GPX File"
            )
            if output_file:
                export_to_gpx(self.unified_locations, output_file)
                messagebox.showinfo("Success", f"GPX file saved to {output_file}.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export GPX: {e}")


if __name__ == "__main__":
    app = App()
    app.mainloop()
