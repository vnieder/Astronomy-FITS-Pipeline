import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading
import os
import ast

# Import pipeline functions from existing modules
from calibration import create_master_frames, calibrate_light_frames
from photometry import perform_photometry, plot

def read_config_file(config_file_path: str) -> dict:
    """
    Reads the configuration file and returns a dictionary of parameters.
    """
    config = {}
    with open(config_file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            if "," in line and ": " in line and "RA/DEC" not in line:
                key, value = line.split(": ", 1)
                value = ast.literal_eval(value)
                config[key] = value
            elif ": " in line:
                key, value = line.split(": ", 1)
                config[key] = value
    return config

def run_pipeline(config_path, log_callback):
    """
    Reads the configuration, then runs calibration, photometry, and plotting.
    Logs status messages via the provided callback.
    """
    try:
        log_callback("Reading config file...")
        config_dict = read_config_file(config_path)
        # Extract parameters from the config dictionary
        dir_path = config_dict["Main Directory (ex. /Users/spencermfreeman/Desktop/pipeline_test)"]
        transit_name = config_dict["Target Name"]
        wcs = config_dict["RA/DEC (ex. 00:28:12.944,+42:03:40.95)"]
        target_radius = int(config_dict["Target Radius"])
        x_targ, y_targ = tuple(config_dict["Target Coordinates (pix)"])
        x_comp, y_comp = tuple(config_dict["Comparison Coordinates (pix)"])
        x_vali, y_vali = tuple(config_dict["Validation Coordinates (pix)"])
        threshold_multiplier = int(config_dict["Source Detection Threshold"])
        catalogue_indicator = config_dict["Catalogue Indicator"]
        light_frame_indicator = config_dict["Light Frame Indicator"]
        output_dir = config_dict["Output Directory"]
        main_title = config_dict["Main Plot Title (transit name)"]
        date = config_dict["Observation Date (MM/DD/YYYY)"]
        observer_name = config_dict["Observer Name"]

        log_callback("Starting calibration...")
        master_flat, master_bias = create_master_frames(dir_path, flip=True)
        log_callback("Master frames created.")

        lights_calibrated = calibrate_light_frames(dir_path, transit_name, master_flat, master_bias, wcs, flip=True)
        log_callback("Light frames calibrated.")

        log_callback("Performing photometry...")
        target_lc, comparison_lc, validation_lc = perform_photometry(
            light_frame_indicator, catalogue_indicator, output_dir, threshold_multiplier, target_radius,
            target_location=(x_targ, y_targ),
            comparison_location=(x_comp, y_comp),
            validation_location=(x_vali, y_vali)
        )
        log_callback("Photometry completed.")

        log_callback("Generating plots and CSV outputs...")
        plot(target_lc, comparison_lc, validation_lc, target_radius, output_dir, main_title, date, observer_name)
        log_callback("Pipeline completed successfully!")
    except Exception as e:
        log_callback(f"Error: {str(e)}")

class AstroPipelineGUI:
    def __init__(self, master):
        self.master = master
        master.title("Astro Fits Pipeline GUI")
        master.geometry("800x600")

        self.config_path = None

        # Top frame for file selection
        self.top_frame = tk.Frame(master)
        self.top_frame.pack(pady=10)

        self.select_button = tk.Button(self.top_frame, text="Select Config File", command=self.select_config)
        self.select_button.pack(side=tk.LEFT, padx=5)

        self.config_label = tk.Label(self.top_frame, text="No config file selected")
        self.config_label.pack(side=tk.LEFT, padx=5)

        self.run_button = tk.Button(master, text="Run Pipeline", command=self.start_pipeline)
        self.run_button.pack(pady=10)

        self.log_text = scrolledtext.ScrolledText(master, width=90, height=30)
        self.log_text.pack(pady=10)

    def select_config(self):
        """
        Opens a file dialog for the user to select a configuration file.
        """
        self.config_path = filedialog.askopenfilename(
            title="Select Config File", 
            filetypes=(("Text Files", "*.txt"), ("All Files", "*.*"))
        )
        if self.config_path:
            self.config_label.config(text=os.path.basename(self.config_path))
            self.log(f"Config file selected: {self.config_path}")
        else:
            self.log("No config file selected.")

    def log(self, message):
        """
        Logs a message to the text area.
        """
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def start_pipeline(self):
        """
        Checks that a config file is selected and starts the pipeline in a new thread.
        """
        if not self.config_path:
            messagebox.showerror("Error", "Please select a config file first.")
            return
        self.log("Starting pipeline process...")
        thread = threading.Thread(target=run_pipeline, args=(self.config_path, self.log))
        thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    gui = AstroPipelineGUI(root)
    root.mainloop()
