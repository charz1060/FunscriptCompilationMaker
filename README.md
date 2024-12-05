# FunscriptCompilationMaker

This is an application to make a new script using sections from existing scripts, basically a script compilation maker tool. You can combine any number of scripts by defining the start and end time of the segments you want, the result is a new script that combines the segments into one file. There is also an option to create the combined video that will be in sync with the generated script.

## Installation
To install the required libraries, run the following command: `pip install -r requirements.txt`

## Launching the UI
Running the Python script will open the User Interface.

<p align="center">
  <img src="https://github.com/user-attachments/assets/f6e3e12f-e3c9-4c5d-a237-105b11795f05" />
</p>

## Using the Application

1. Using the 'Browse Files' button select the scripts you want to pull from. The order in the list box is the order the final combined script and video will be in.

   * If you want to include several sections from the same script you will have to browse for the file as many times as you want to use it. For example, if you want 3 sections from the same script, the script needs to be in the box 3 times.

2. Set the start time and end time of the section of each script you want to use.

   * To do this you select the script in the box, set the start and end time values and click 'Save Time.'

   * Time must be in milliseconds, make sure you convert the time properly.

   * Note: The UI for this is a little janky, do not use tab to change fields and do not double click anywhere as that will deselect whatever script you have selected in the box.

3. Select the method of script generation you want.

   * Combine Funscripts Only: No video processing, will just generate combined_actions.funscript.

   * Combine Funscripts and Cut Videos: Will generate the combined_actions.funscript and the cut videos, which are just the segments of the videos defined by the start and end times entered.

   * Combine Funscripts and Videos: Will generate the combine_actions.funscript, the cut videos, and a combined_video.mp4, which is the full video in sync with the combined script.

4. Select 'Generate Funscript'.

   * The time it takes will depend heavily on the script generation method. Just generating the script is near instant, but the video processing will take longer. Video processing can take very long and depends on several factors such as encoding, length, quality and your computers capabilities.
