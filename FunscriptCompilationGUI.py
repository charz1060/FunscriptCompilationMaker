import json
import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.compositing.concatenate import concatenate_videoclips


def process_file(input_file_path, start_threshold, end_threshold):
    """
    Processes a .funscript file to retain 'actions' within a range and offset 'at' values.
    Returns the filtered and adjusted actions.
    """
    # Read the .funscript file (handling as JSON)
    with open(input_file_path, 'r') as file:
        data = json.load(file)

    # Filter and offset the "actions"
    filtered_actions = [
        {'at': action['at'] - start_threshold, 'pos': action['pos']}
        for action in data['actions']
        if start_threshold <= action['at'] <= end_threshold
    ]
    return filtered_actions


def cut_video(video_file_path, start_ms, end_ms):
    """
    Cuts a portion of the video based on start and end milliseconds using FFmpeg.
    """
    start_s = start_ms / 1000  # Convert milliseconds to seconds
    end_s = end_ms / 1000  # Convert milliseconds to seconds
    output_file = f"cut_{os.path.basename(video_file_path)}"

    # Construct the FFmpeg command
    ffmpeg_command = [
        'ffmpeg',
        '-i', video_file_path,          # Input file
        '-ss', str(start_s),            # Start time (seconds)
        '-to', str(end_s),              # End time (seconds)
        '-c:v', 'copy',                 # Copy video stream (no re-encoding)
        '-c:a', 'copy',                 # Copy audio stream (no re-encoding)
        output_file                     # Output file name
    ]
    
    try:
        # Run the FFmpeg command
        subprocess.run(ffmpeg_command, check=True)
        print(f"Video cut successfully: {output_file}")
        return VideoFileClip(output_file)
    except subprocess.CalledProcessError as e:
        print(f"Error cutting video {video_file_path}: {e}")
        return None


def combine_videos(video_clips, output_file):
    """
    Combines multiple VideoFileClip objects into one video.
    """
    final_clip = concatenate_videoclips(video_clips, method="compose")
    final_clip.write_videofile(output_file, codec="libx264")
    print(f"Combined video saved to {output_file}")


def browse_files():
    """
    Opens a file dialog to select a .funscript file and add it to the listbox.
    """
    funscript_file = filedialog.askopenfilename(filetypes=[("Funscript files", "*.funscript")])
    if funscript_file:
        # Add .funscript file to the listbox
        json_files_listbox.insert(tk.END, funscript_file)
        # Initialize thresholds as empty for new files
        file_thresholds[funscript_file] = {'start': 0, 'end': 0}
        update_threshold_fields(funscript_file)


def update_threshold_fields(file):
    """
    Updates the start and end threshold fields when a .funscript file is selected.
    """
    start_entry.delete(0, tk.END)
    end_entry.delete(0, tk.END)

    # Get the current thresholds for the selected file
    if file in file_thresholds:
        start_entry.insert(0, file_thresholds[file]['start'])
        end_entry.insert(0, file_thresholds[file]['end'])


def save_thresholds():
    """
    Save the updated thresholds for the selected .funscript file.
    """
    selected_file = json_files_listbox.get(json_files_listbox.curselection())
    try:
        start_threshold = int(start_entry.get())
        end_threshold = int(end_entry.get())
        file_thresholds[selected_file] = {'start': start_threshold, 'end': end_threshold}
        print(f"Saved thresholds for {selected_file}: Start - {start_threshold} ms, End - {end_threshold} ms")
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter valid numeric values for thresholds.")



def on_select_file(event):
    """
    Handles .funscript file selection from the listbox, updates the threshold fields.
    """
    selected_file = json_files_listbox.get(json_files_listbox.curselection())
    update_threshold_fields(selected_file)


def remove_selected():
    """
    Removes selected .funscript files from the listbox and corresponding threshold entries.
    """
    selected_indices = json_files_listbox.curselection()
    for index in reversed(selected_indices):
        selected_file = json_files_listbox.get(index)
        json_files_listbox.delete(index)
        del file_thresholds[selected_file]
    update_threshold_fields('')  # Reset fields


def process_all_files():
    """
    Processes all selected files and generates combined output based on the selected checkboxes.
    """
    try:
        all_actions = []
        video_clips = []
        for i, json_file in enumerate(json_files_listbox.get(0, tk.END)):
            # Get the thresholds for each file
            start_threshold = file_thresholds[json_file]['start']
            end_threshold = file_thresholds[json_file]['end']

            # Process the JSON file
            filtered_actions = process_file(json_file, start_threshold, end_threshold)
            all_actions.append(filtered_actions)

            video_file = json_file.replace('.funscript', '.mp4')  # Assuming video has the same name as JSON file
            if os.path.exists(video_file) and (combine_scripts_and_cut_videos_var.get() or combine_scripts_and_videos_var.get()):
                video_clip = cut_video(video_file, start_threshold, end_threshold)
                video_clips.append(video_clip)

        # Combine actions if "Combine Scripts Only" checkbox is selected
        if combine_scripts_var.get():
            combined_actions = combine_actions(all_actions)
            combined_file_path = "Combined_Actions.funscript"
            with open(combined_file_path, 'w') as file:
                json.dump({'actions': combined_actions}, file, indent=4)

        # Combine actions and cut videos if "Combine Scripts and Cut Videos" checkbox is selected
        if combine_scripts_and_cut_videos_var.get():
            combined_actions = combine_actions(all_actions)
            combined_file_path = "Combined_Actions.funscript"
            with open(combined_file_path, 'w') as file:
                json.dump({'actions': combined_actions}, file, indent=4)

        # Combine actions and videos if "Combine Scripts and Videos" checkbox is selected
        if combine_scripts_and_videos_var.get():
            combined_actions = combine_actions(all_actions)
            combined_file_path = "Combined_Actions.funscript"
            with open(combined_file_path, 'w') as file:
                json.dump({'actions': combined_actions}, file, indent=4)

            combined_video_path = "Combined_Video.mp4"
            if video_clips:
                combine_videos(video_clips, combined_video_path)

        messagebox.showinfo("Success", "Files processed and saved successfully!")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")


def combine_actions(file_actions_list):
    """
    Combines multiple 'actions' lists, offsetting the 'at' values for continuity.
    """
    combined_actions = []
    current_offset = 0

    for actions in file_actions_list:
        for action in actions:
            combined_actions.append({
                'at': action['at'] + current_offset,
                'pos': action['pos']
            })
        if actions:
            current_offset += actions[-1]['at']  # Update offset to ensure continuity

    return combined_actions

# Function to manage checkbox states
def manage_checkboxes(selected_var):
    """
    Disable other checkboxes when one checkbox is selected.
    Enable all checkboxes if none are selected.
    """
    if selected_var.get():
        # Disable other checkboxes
        if selected_var == combine_scripts_var:
            combine_scripts_and_cut_videos_checkbox.config(state="disabled")
            combine_scripts_and_videos_checkbox.config(state="disabled")
        elif selected_var == combine_scripts_and_cut_videos_var:
            combine_scripts_checkbox.config(state="disabled")
            combine_scripts_and_videos_checkbox.config(state="disabled")
        elif selected_var == combine_scripts_and_videos_var:
            combine_scripts_checkbox.config(state="disabled")
            combine_scripts_and_cut_videos_checkbox.config(state="disabled")
    else:
        # Enable all checkboxes if none are selected
        combine_scripts_checkbox.config(state="normal")
        combine_scripts_and_cut_videos_checkbox.config(state="normal")
        combine_scripts_and_videos_checkbox.config(state="normal")

# Save button to save the current thresholds
def save_thresholds():
    """
    Save the updated thresholds for the selected file.
    """
    selected_file = json_files_listbox.get(json_files_listbox.curselection())
    try:
        start_threshold = int(start_entry.get())
        end_threshold = int(end_entry.get())
        file_thresholds[selected_file] = {'start': start_threshold, 'end': end_threshold}
        print(f"Saved thresholds for {selected_file}: Start - {start_threshold} ms, End - {end_threshold} ms")
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter valid numeric values for thresholds.")


# Initialize the main window
window = tk.Tk()
window.title("Funscript Compilation Maker")
window.geometry("400x600")

# Create a frame to hold the content
frame = tk.Frame(window)

# JSON files listbox
json_files_listbox = tk.Listbox(frame, width=50, height=10)
json_files_listbox.pack(pady=20)

# Bind selection event for listbox
json_files_listbox.bind('<<ListboxSelect>>', on_select_file)

# Browse button
browse_button = tk.Button(frame, text="Browse Files", command=browse_files)
browse_button.pack(pady=5)

# Remove selected button
remove_button = tk.Button(frame, text="Remove Selected", command=remove_selected)
remove_button.pack(pady=5)

# Thresholds frame for start and end points
thresholds_frame = tk.Frame(frame)
thresholds_frame.pack(pady=10)

# Labels and entries for start and end threshold inputs
tk.Label(thresholds_frame, text="Start Time (ms):").grid(row=0, column=0, padx=5, pady=5)
start_entry = tk.Entry(thresholds_frame)
start_entry.grid(row=0, column=1, padx=5, pady=5)

tk.Label(thresholds_frame, text="End Time (ms):").grid(row=1, column=0, padx=5, pady=5)
end_entry = tk.Entry(thresholds_frame)
end_entry.grid(row=1, column=1, padx=5, pady=5)

# Initialize the dictionary for file thresholds
file_thresholds = {}

# Save button UI
save_button = tk.Button(frame, text="Save Time", command=save_thresholds)
save_button.pack(pady=10)

# Checkboxes for different functionalities with commands to manage state
combine_scripts_var = tk.BooleanVar()
combine_scripts_and_cut_videos_var = tk.BooleanVar()
combine_scripts_and_videos_var = tk.BooleanVar()

combine_scripts_checkbox = tk.Checkbutton(
    frame, text="Combine Scripts Only", variable=combine_scripts_var,
    command=lambda: manage_checkboxes(combine_scripts_var)
)
combine_scripts_checkbox.pack(pady=5)

combine_scripts_and_cut_videos_checkbox = tk.Checkbutton(
    frame, text="Combine Scripts and Cut Videos", variable=combine_scripts_and_cut_videos_var,
    command=lambda: manage_checkboxes(combine_scripts_and_cut_videos_var)
)
combine_scripts_and_cut_videos_checkbox.pack(pady=5)

combine_scripts_and_videos_checkbox = tk.Checkbutton(
    frame, text="Combine Scripts and Videos", variable=combine_scripts_and_videos_var,
    command=lambda: manage_checkboxes(combine_scripts_and_videos_var)
)
combine_scripts_and_videos_checkbox.pack(pady=5)

# Process button
process_button = tk.Button(frame, text="Create Funscript", command=process_all_files)
process_button.pack(pady=20)

# Add the frame to the window
frame.pack()

# Start the GUI loop
window.mainloop()