#Bug Fixed, finally frame perfect.
#FunscriptCompilationGUI_v2.py

import json
import os
import subprocess
from subprocess import check_output
import tkinter as tk
import re
from tkinter import filedialog, messagebox
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.compositing.concatenate import concatenate_videoclips
from pathlib import Path
from pymkv import MKVFile
import ffmpeg
selected_index = None




def cut_video_mkvtoolnix(video_file_path, start_ms, end_ms):
    """
    Cuts a portion of the video based on start and end timestamps using mkvmerge.
    
    :param video_file_path: Path to the input video file.
    :param start_time: Start time in 'HH:MM:SS' format.
    :param end_time: End time in 'HH:MM:SS' format.
    """
    # Define output file name based on input file name
    #output_file = f"CLIPPED_{os.path.basename(video_file_path).replace('.mp4', '.mkv')}"

    print("made it into cut_video_mkvtoolnix")
    print("Values passed: ", video_file_path, start_ms, end_ms)
    
    start_time = convert_milliseconds_to_timestamp(start_ms)
    end_time = convert_milliseconds_to_timestamp(end_ms)


    # Get the directory of the original file
    directory = os.path.dirname(video_file_path)
    
    # Get the base name of the original file (file name + extension)
    base_name = os.path.basename(video_file_path)
    
    # Split the base name into name and extension
    name, ext = os.path.splitext(base_name)
    
    # Create the new filename
    new_filename = f"cut_{start_ms}_{name}{ext}"
    
    # Construct the full path for the new file
    output_file = os.path.join(directory, new_filename)

    print("filepath: ", video_file_path)
    print("output file: ", output_file)


    # Construct the mkvmerge command
    # mkvmerge_command = [
    #     'mkvmerge',
    #     '-o', f'"{output_file}"',
    #     '--forced-track', '0:no',
    #     '--forced-track', '1:no',
    #     '-a', '1',
    #     '-d', '0',
    #     '-S',
    #     '-T',
    #     '--no-global-tags',
    #     '--no-chapters',
    #     '(',
    #     f'"{video_file_path}"',
    #     ')',
    #     '--track-order', '0:0,0:1',
    #     '--split', f'parts:{start_time}-{end_time}'
    # ]
    mkvmerge_command = [
        'mkvmerge',
        '-o', f'"{output_file}"',
        '(',
        f'"{video_file_path}"',
        ')',
        '--track-order', '0:0,0:1',
        '--split', f'parts:{start_time}-{end_time}'
    ]

    # Join the command into a single string
    command_str = " ".join(mkvmerge_command)

    print("Running command:", command_str)  # Print the command for debugging

    try:
        # Run the mkvmerge command
        subprocess.run(command_str, check=True, shell=True)
        result = subprocess.run(command_str, check=True, shell=True, capture_output=True, text=True)
        # print(result.stdout)
        # print(result.stdout)
        # print(result.stdout)

        example_str = 'Timestamp used in split decision: 00:00:04.546000000'
        example_timestamp_lines = re.findall(r'Timestamp used in split decision: .*', example_str)
        example_timestamp_lines[0].split(': ')[1].split('.')[0]

        test_str = result.stdout
        #test_str = 'Timestamp used in split decision: 00:01:01.132000000\n\n\nTimestamp used in split decision: 00:02:02.232000000\n\n\n'
        timestamp_lines = re.findall(r'Timestamp used in split decision: .*', test_str)
        
        #if there is only 1 result in timestamp_lines
        #This happens if we supply 0 as the script time - mkvmerge doesn't have to calculate anything...
        
        # In this scenario, we are doing the full clip of the video, so no estimation is being done by 
        if len(timestamp_lines) == 0:
            print("timestamp_lines is empty")
            combined_ms1 = start_ms
            combined_ms2 = end_ms
        
        ## 00 scenario
        elif len(timestamp_lines) == 1 and start_ms == 0:
            combined_ms1 = 0
            print("think we found a 00:00:00.000 scenario")
            time_part2 = timestamp_lines[0].split(': ')[1].split('.')[0]
            milliseconds2 = timestamp_lines[0].split('.')[1][:3]
            combined_string2 = f"{time_part2}:{milliseconds2}"
            combined_ms2 = convert_to_milliseconds(combined_string2)
        elif len(timestamp_lines) == 1 and start_ms != 0:
            combined_ms2 = end_ms
            print("think we found a video segment through end scenario")
            time_part1 = timestamp_lines[0].split(': ')[1].split('.')[0]
            milliseconds1 = timestamp_lines[0].split('.')[1][:3]
            combined_string1 = f"{time_part1}:{milliseconds1}"
            combined_ms1 = convert_to_milliseconds(combined_string1)
        else:
            time_part1 = timestamp_lines[0].split(': ')[1].split('.')[0]
            milliseconds1 = timestamp_lines[0].split('.')[1][:3]
            combined_string1 = f"{time_part1}:{milliseconds1}"
            combined_ms1 = convert_to_milliseconds(combined_string1)
            time_part2 = timestamp_lines[1].split(': ')[1].split('.')[0]
            milliseconds2 = timestamp_lines[1].split('.')[1][:3]
            combined_string2 = f"{time_part2}:{milliseconds2}"
            combined_ms2 = convert_to_milliseconds(combined_string2)
        

        
        
        clip = VideoFileClip(output_file)
        duration_ms = clip.duration * 1000  # Convert seconds to milliseconds

        print(f"Video cut successfully: {output_file}")

        return VideoFileClip(output_file), duration_ms, output_file, combined_ms1, combined_ms2

        return output_file  # Return the output file name for later use
    except subprocess.CalledProcessError as e:
        print(f"Error cutting video {video_file_path}: {e}")
        return None



# # Example usage
# video_path = r'C:\Users\Derp\Downloads\slow blows 9 1080.SVP.mkv'  # Replace with your actual MKV file name
# start_timestamp = "00:00:00:000"  # Start at 0 seconds
# end_timestamp = "00:00:20:000"     # End at 20 seconds

# # Call the function to cut the video
# cut_video_mkvtoolnix(video_path, start_timestamp, end_timestamp)


def get_video_dimensions(video_file):
    cmd = [
        'ffprobe',
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_streams',
        video_file
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)
    video_stream = next(s for s in data['streams'] if s['codec_type'] == 'video')
    return int(video_stream['width']), int(video_stream['height'])

def find_max_dimensions(video_clips):
    max_width = max_height = 0
    for clip in video_clips:
        width, height = get_video_dimensions(clip)
        max_width = max(max_width, width)
        max_height = max(max_height, height)
    return max_width, max_height



def combine_videos_ffmpeg_diff_files(video_clips, output_file):
    max_width, max_height = find_max_dimensions(video_clips)
    
    filter_complex = []
    for i, clip in enumerate(video_clips):
        filter_complex.append(f"[{i}:v]scale={max_width}:{max_height}:force_original_aspect_ratio=decrease,pad={max_width}:{max_height}:(ow-iw)/2:(oh-ih)/2[v{i}];")
    
    filter_complex.append(f"{''.join([f'[v{i}][{i}:a]' for i in range(len(video_clips))])}concat=n={len(video_clips)}:v=1:a=1[outv][outa]")
    
    command = ['ffmpeg']
    for clip in video_clips:
        command.extend(['-i', clip])
    command.extend([
        '-filter_complex', ''.join(filter_complex),
        '-map', '[outv]',
        '-map', '[outa]',
        output_file
    ])
    
    subprocess.run(command, check=True)





# New Method hentaiprodigy69
def create_video_list_ffmpeg(video_clips, list_file):
    """
    Creates a text file listing all video clips for FFmpeg.
    """
    with open(list_file, 'w') as f:
        for clip in video_clips:
            f.write(f"file '{clip}'\n")

# New Method hentaiprodigy69
def combine_videos_ffmpeg(video_clips, output_file):
    """
    Combines multiple video files into one using FFmpeg.
    """
    list_file = 'video_list.txt'
    
    # Create the list of videos
    create_video_list_ffmpeg(video_clips, list_file)
 
    # Construct the FFmpeg command
    command = [
        'ffmpeg', 
        '-f', 'concat', 
        '-safe', '0', 
        '-i', list_file, 
        '-c', 'copy', 
        output_file
    ]
 
    # Execute the command
    subprocess.run(command)
    
    # Remove the list file after processing
    os.remove(list_file)
 
    print(f"Combined video saved to {output_file}")
 
 
# New Method hentai prodigy 69 
def all_filenames_are_same(filenames):
    """
    Check if all filenames in the list are the same.
    
    :param filenames: List of filename strings
    :return: True if all filenames are the same, False otherwise
    """
    if not filenames:
        return True  # Empty list case
 
    first_filename = filenames[0]
    
    for filename in filenames:
        if filename != first_filename:
            print("filename differences here: ", filename, first_filename)
            return False
            
    return True
 
 
 
def process_file(input_file_path, start_threshold, end_threshold):
    """
    Processes a .funscript file to retain 'actions' within a range and offset 'at' values.
    Returns the filtered and adjusted actions.
    """
    # Read the .funscript file (handling as JSON)

    print("start_threshold: ", start_threshold, "end_threshold: ", end_threshold)
    #print the types of start_threshold and end_threshold
    print(type(start_threshold), type(end_threshold))   

    start_threshold = int(start_threshold)
    end_threshold = int(end_threshold)

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
    global selected_index
    start_s = start_ms / 1000  # Convert milliseconds to seconds
    end_s = end_ms / 1000  # Convert milliseconds to seconds
    output_file = f"cut{start_ms}_{os.path.basename(video_file_path)}"
 
    # Construct the FFmpeg command
    ffmpeg_command = [
        'ffmpeg',
        '-i', video_file_path,          # Input file
        '-ss', str(start_s),            # Start time (seconds)
        '-to', str(end_s),              # End time (seconds)
        '-c:v', 'copy',                 # Copy video stream (no re-encoding)
        '-c:a', 'copy',                 # Copy audio stream (no re-encoding)
        '-pix_fmt', 'yuv420p',          # Convert to YUV 4:2:0 format as a possible bugfix...
        output_file                     # Output file name
    ]
    
    try:
        # Run the FFmpeg command
        subprocess.run(ffmpeg_command, check=True)
        print(f"Video cut successfully: {output_file}")
 
        
        clip = VideoFileClip(output_file)
        duration_ms = clip.duration * 1000  # Convert seconds to milliseconds
 
        return VideoFileClip(output_file), duration_ms, output_file
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
        file_thresholds[json_files_listbox.size() - 1] = {'start': 0, 'end': 0}  # Index-based tracking
        update_threshold_fields(json_files_listbox.size() - 1)
 
 
def update_threshold_fields(index):
    """
    Updates the start and end threshold fields when a .funscript file is selected.
    """
    start_entry.delete(0, tk.END)
    end_entry.delete(0, tk.END)
 
    # Get the current thresholds for the selected file
    if index in file_thresholds:
        start_entry.insert(0, milliseconds_to_time(file_thresholds[index]['start']))
        end_entry.insert(0, milliseconds_to_time(file_thresholds[index]['end']))
 
def on_select_file(event):
    """
    Handles .funscript file selection from the listbox, updates the threshold fields.
    """
    global selected_index
    selection = json_files_listbox.curselection()
    if selection:
        selected_index = selection[0]  # Get the first selected index
        update_threshold_fields(selected_index)
 
 
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
        offset_list = []
        video_filenames = []
        clip_filenames = []
        for i in range(json_files_listbox.size()):
            # Get the file path and thresholds for this instance
            funscript_file = json_files_listbox.get(i)
            start_threshold = file_thresholds[i]['start']
            end_threshold = file_thresholds[i]['end']
 
 
 
 
            # Handle corresponding video file
            video_file = funscript_file.replace('.funscript', '.mp4')
            if os.path.exists(video_file) and (combine_scripts_and_cut_videos_var.get() or combine_scripts_and_videos_var.get()):

                video_clip, vid_length, clip_filename, start_threshold_new, end_threshold_new = cut_video_mkvtoolnix(video_file, start_threshold, end_threshold)
                video_clips.append(video_clip)
                offset_list.append(vid_length)
                video_filenames.append(video_file)
                clip_filenames.append(clip_filename)

                
                # Process the .funscript file
                filtered_actions = process_file(funscript_file, start_threshold_new, end_threshold_new)
                all_actions.append(filtered_actions)
 
                #This part will save every clip's funscript file as well :)
                json_output_filename = clip_filename.replace('.mp4', '.funscript')
                with open(json_output_filename, 'w') as file:
                    json.dump({'actions': filtered_actions}, file, indent=4)
 
 
 
 
        ### SCRIPT GENERATION PART
 
        current_working_directory = os.getcwd()
 
 
        # Combine actions if "Combine Scripts Only" checkbox is selected
        if combine_scripts_and_cut_videos_var.get():
            combined_actions = combine_actions(all_actions, offset_list)
            combined_file_path = current_working_directory + "\Combined_Actions.funscript"
            with open(combined_file_path, 'w') as file:
                json.dump({'actions': combined_actions}, file, indent=4)
            print("Dumped combined actions to:", combined_file_path)
 
        # Combine Scripts and Cut Videos checkbox is eelcted
        if combine_scripts_var.get():
            combined_actions = combine_actions(all_actions, offset_list)
            combined_file_path = current_working_directory + "\Combined_Actions.funscript"
            with open(combined_file_path, 'w') as file:
                json.dump({'actions': combined_actions}, file, indent=4)
            print("Dumped combined actions to:", combined_file_path)
 
 
        # Combine actions and videos if needed
        if combine_scripts_and_videos_var.get():
            combined_actions = combine_actions(all_actions, offset_list)
            combined_file_path = current_working_directory + "\Combined_Actions.funscript"
            with open(combined_file_path, 'w') as file:
                json.dump({'actions': combined_actions}, file, indent=4)
            print("Dumped combined actions to:", combined_file_path)
 
 
 
            #hentaiprodigy69 method - this will only work if the videos are in the same format
 
            combined_video_path_hp69 = "Combined_Video_Lossless_Attempt.mkv"
            if video_clips:
                if(all_filenames_are_same(video_filenames)):
                    print("All video clips come from the same file, so we will append losslessly")
                    combine_videos_ffmpeg(clip_filenames, combined_video_path_hp69)
                    print("Combined video lossless saved to:", combined_video_path_hp69)
                else:
                    print("Not all video clips come from the same file, so we will combine with ffmpeg")

                    combined_video_path = "Combined_Video.mkv"
                    combine_videos_ffmpeg_diff_files(clip_filenames, combined_video_path)

                    #moviepy version:
                    # combine_videos(video_clips, combined_video_path)
                    print("Combined video saved to:", combined_video_path)
            
 
        messagebox.showinfo("Success", "Files processed and saved successfully!")
 
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")
 
 
def combine_actions(file_actions_list, offset_list):
    """
    Combines multiple 'actions' lists, offsetting the 'at' values for continuity.
    """
    combined_actions = []
    current_offset = 0
    file_num = 0
 
    for actions in file_actions_list:
        for action in actions:
            combined_actions.append({
                'at': action['at'] + current_offset,
                'pos': action['pos']
            })
        if actions:
            #current_offset += actions[-1]['at']  # Update offset to ensure continuity
            current_offset += offset_list[file_num]
            file_num += 1
 
 
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
    global selected_index
    if selected_index is not None:
        try:
            # start_threshold = start_entry.get()
            # end_threshold = end_entry.get()
            start_threshold = int(convert_to_milliseconds(start_entry.get()))
            end_threshold = int(convert_to_milliseconds(end_entry.get()))
            file_thresholds[selected_index] = {'start': start_threshold, 'end': end_threshold}
            print(f"Saved thresholds for file at index {selected_index}: Start - {start_threshold} ms, End - {end_threshold} ms")
        except ValueError:
            messagebox.showerror("Invalid Input", "Input must be in the format hh:mm:ss:milliseconds")
    else:
        messagebox.showerror("No Selection", "Please select a file from the listbox.")
 
 
def convert_milliseconds_to_timestamp(ms):
    """
    Converts milliseconds to a timestamp in the format HH:MM:SS:ms.
    
    :param ms: Duration in milliseconds.
    :return: A string representing the timestamp in HH:MM:SS:ms format.
    """
    # Calculate hours, minutes, seconds and remaining milliseconds
    hours = ms // 3600000
    ms %= 3600000
    minutes = ms // 60000
    ms %= 60000
    seconds = ms // 1000
    milliseconds = ms % 1000

    # Format the output string
    return f"{hours:02}:{minutes:02}:{seconds:02}:{milliseconds:03}"



def convert_to_milliseconds(time_str):
    # Split the input string into components
    parts = time_str.split(':')
    
    # Ensure there are exactly 4 parts (hh, mm, ss, milliseconds)
    if len(parts) != 4:
        raise ValueError("Input must be in the format hh:mm:ss:milliseconds")
    
    # Extract hours, minutes, seconds, and milliseconds
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = int(parts[2])
    milliseconds = int(parts[3])
    
    # Convert all parts to milliseconds
    total_milliseconds = (
        (hours * 3600 * 1000) +  # Convert hours to milliseconds
        (minutes * 60 * 1000) +  # Convert minutes to milliseconds
        (seconds * 1000) +       # Convert seconds to milliseconds
        milliseconds              # Already in milliseconds
    )
    
    return total_milliseconds
 
def milliseconds_to_time(ms):
    """
    Converts milliseconds to time in the format 'hh:mm:ss:milliseconds'.
    
    :param ms: Time in milliseconds
    :return: Formatted time as a string
    """
    hours = ms // (1000 * 60 * 60)
    minutes = (ms % (1000 * 60 * 60)) // (1000 * 60)
    seconds = (ms % (1000 * 60)) // 1000
    milliseconds = ms % 1000
    return f"{hours:02}:{minutes:02}:{seconds:02}:{milliseconds:03}"
 
 
 
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
tk.Label(thresholds_frame, text="Start Time:").grid(row=0, column=0, padx=5, pady=5)
start_entry = tk.Entry(thresholds_frame)
start_entry.grid(row=0, column=1, padx=5, pady=5)
 
tk.Label(thresholds_frame, text="End Time:").grid(row=1, column=0, padx=5, pady=5)
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
