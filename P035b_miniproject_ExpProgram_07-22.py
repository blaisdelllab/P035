#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun  3 09:58:27 2024

@author: kayleyozimac and Cyrus K.

Last updated on July 21, 2024.

This is the code for Kayley Ozimac's mini project (P035b) for her 'FOAM' project
    
    1) Phase 1 (familiarization): 10 (C1-10) comparison stimuli will be pre-
exposed to the subjects. TEach stimulus were presented individually in each session, 
an equal number of times on the left and right locations. Two pecks at the stimulus 
ended the trial, with the stimulus being removed from the screen while food was 
delivered from the hopper for 6 s. The completion of each trial is followed by a
 15-s intertrial interval (ITI), which remained in effect throughout the experiment. 
 The remaining 10 comparison stimuli were not shown during this phase. Each session 
 consisted of 60 trials, with each comparison stimulus presented 6 times (3 times 
 on the right and 3 times on the left) in a pseudorandomized order.
        
    2) Phase 2 (experimental trials): The next phase is a simple MTS task in which 
a sample stimulus is presented in the top-middle sample slot. After several pecks
(VR5 with bounds from 3 to 10, but this was built to be maniputable),two comparisons 
were presented at left and right of the sample (with the sample still visible). 
One of these comparisons was always linked with that specific sample (deemed 
the "correct comparison") and the other sample was non-linked with that sample, 
but instead was the linked pair of a seperate sample stimulus (deemed an "incorrect
choice" or foil). During this match to sample interval, a single peck to the 
correct comparison was reinforced with 6-s access to the food hopper, while a 
peck to the foil was punished with an absence of reinforcer and directly to the 
15s ITI. After the selection of a comparison key, the screen goes black until 
the reinforcement (if relevant) and/or ITI period completed and the next trial 
occured with a different sample. Each sample-comparison pair per trial type will 
be presented 6 times within a session, resulting in a total of 120 trials per 
session (20 combinations x 6 repetitions). 
"""
# Prior to running any code, its conventional to first import relevant 
# libraries for the entire script. These can range from python libraries (sys)
# or sublibraries (setrecursionlimit) that are downloaded to every computer
# along with python, or other files within this folder (like control_panel or 
# maestro).
# =============================================================================
from csv import writer, QUOTE_MINIMAL, DictReader
from datetime import datetime, timedelta, date
from sys import setrecursionlimit, path as sys_path
from tkinter import Toplevel, Canvas, BOTH, TclError, Tk, Label, Button, \
     StringVar, OptionMenu, IntVar, Radiobutton
from time import time, sleep
from os import getcwd, popen, mkdir, listdir, path as os_path
from random import choice, shuffle
from PIL import ImageTk, Image  

# The first variable declared is whether the program is the operant box version
# for pigeons, or the test version for humans to view. The variable below is 
# a T/F boolean that will be referenced many times throughout the program 
# when the two options differ (for example, when the Hopper is accessed or
# for onscreen text, etc.). It is changed automatically based on whether
# the program is running in operant boxes (True) or not (False). It is
# automatically set to True if the user is "blaisdelllab" (e.g., running
# on a rapberry pi) or False if not. The output of os_path.expanduser('~')
# should be "/home/blaisdelllab" on the RPis.

if os_path.expanduser('~').split("/")[2] =="blaisdelllab":
    operant_box_version = True
    print("*** Running operant box version *** \n")
else:
    operant_box_version = False
    print("*** Running test version (no hardware) *** \n")

# Import hopper/other specific libraries from files on operant box computers
try:
    if operant_box_version:
        # Import additional libraries...
        import pigpio # import pi, OUTPUT
        import csv
        #...including art scripts
        sys_path.insert(0, str(os_path.expanduser('~')+"/Desktop/Experiments/P033/"))
        import graph
        import polygon_fill
        
        # Setup GPIO numbers (NOT PINS; gpio only compatible with GPIO num)
        servo_GPIO_num = 2
        hopper_light_GPIO_num = 13
        house_light_GPIO_num = 21
        
        # Setup use of pi()
        rpi_board = pigpio.pi()
        
        # Then set each pin to output 
        rpi_board.set_mode(servo_GPIO_num,
                           pigpio.OUTPUT) # Servo motor...
        rpi_board.set_mode(hopper_light_GPIO_num,
                           pigpio.OUTPUT) # Hopper light LED...
        rpi_board.set_mode(house_light_GPIO_num,
                           pigpio.OUTPUT) # House light LED...
        
        # Setup the servo motor 
        rpi_board.set_PWM_frequency(servo_GPIO_num,
                                    50) # Default frequency is 50 MhZ
        
        # Next grab the up/down 
        hopper_vals_csv_path = str(os_path.expanduser('~')+"/Desktop/Box_Info/Hopper_vals.csv")
        
        # Store the proper UP/DOWN values for the hopper from csv file
        up_down_table = list(csv.reader(open(hopper_vals_csv_path)))
        hopper_up_val = up_down_table[1][0]
        hopper_down_val = up_down_table[1][1]
        
        # Lastly, run the shell script that maps the touchscreen to operant box monitor
        popen("sh /home/blaisdelllab/Desktop/Hardware_Code/map_touchscreen.sh")
                             
        
except ModuleNotFoundError:
    input("ERROR: Cannot find hopper hardware! Check desktop.")

# Below  is just a safety measure to prevent too many recursive loops). It
# doesn't need to be changed.
setrecursionlimit(5000) 

"""
The code below jumpstarts the loop by first building the hopper object and 
making sure everything is turned off, then passes that object to the
control_panel. The program is largely recursive and self-contained within each
object, and a macro-level overview is:
    
    ControlPanel -----------> MainScreen ------------> PaintProgram
         |                        |                         |
    Collects main           Runs the actual         Gets passed subject
    variables, passes      experiment, saves        name, but operates
    to Mainscreen          data when exited          independently
    

"""

# The first of two objects we declare is the ExperimentalControlPanel (CP). It
# exists "behind the scenes" throughout the entire session, and if it is exited,
# the session will terminate.
class ExperimenterControlPanel(object):
    # The init function declares the inherent variables within that object
    # (meaning that they don't require any input).
    def __init__(self):
        # First, setup the data directory in "Documents"
        self.doc_directory = str(os_path.expanduser('~'))+"/Documents/"
        # Next up, we need to do a couple things that will be different based
        # on whether the program is being run in the operant boxes or on a 
        # personal computer. These include setting up the hopper object so it 
        # can be referenced in the future, or the location where data files
        # should be stored.
        if operant_box_version:
            # Setup the data directory in "Documents"
            self.data_folder = "P035_data" # The folder within Documents where subject data is kept
            self.data_folder_directory = str(os_path.expanduser('~'))+"/Desktop/Data/" + self.data_folder
        else: # If not, just save in the current directory the program us being run in 
            self.data_folder_directory = getcwd() + "/data"
        
        # setup the root Tkinter window
        self.control_window = Tk()
        self.control_window.title("P035b Control Panel")
        ##  Next, setup variables within the control panel
        # Subject ID
        self.pigeon_name_list = ["Bowser", "Yoshi", "Shy Guy", "Athena",
                                 "Darwin","Cousteau",
                                 "Bon Jovi"]
        self.pigeon_name_list.sort() # This alphabetizes the list
        self.pigeon_name_list.insert(0, "TEST")
        
        Label(self.control_window, text="Pigeon Name:").pack()
        self.subject_ID_variable = StringVar(self.control_window)
        self.subject_ID_variable.set("Subject")
        self.subject_ID_menu = OptionMenu(self.control_window,
                                          self.subject_ID_variable,
                                          *self.pigeon_name_list,
                                          command=self.set_pigeon_ID).pack()

        
        # Exp phases
        self.experimental_phase_titles = ["Phase 1 (Familiarization)", 
                                          "Phase 2 (Experimental trials)"]
        
        Label(self.control_window, text="Experimental Phase:").pack()
        self.exp_phase_variable = StringVar(self.control_window)
        self.exp_phase_variable.set("Select")
        self.exp_phase_menu = OptionMenu(self.control_window,
                                          self.exp_phase_variable,
                                          *self.experimental_phase_titles
                                          ).pack()
        
        # Record data variable?
        Label(self.control_window,
              text = "Record data in seperate data sheet?").pack()
        self.record_data_variable = IntVar()
        self.record_data_rad_button1 =  Radiobutton(self.control_window,
                                   variable = self.record_data_variable, text = "Yes",
                                   value = True).pack()
        self.record_data_rad_button2 = Radiobutton(self.control_window,
                                  variable = self.record_data_variable, text = "No",
                                  value = False).pack()
        self.record_data_variable.set(True) # Default set to True
        
        
        # Start button
        self.start_button = Button(self.control_window,
                                   text = 'Start program',
                                   bg = "green2",
                                   command = self.build_chamber_screen).pack()
        
        # This makes sure that the control panel remains onscreen until exited
        self.control_window.mainloop() # This loops around the CP object
        
        
    def set_pigeon_ID(self, pigeon_name):
        # This function checks to see if a pigeon's data folder currently 
        # exists in the respective "data" folder within the Documents
        # folder and, if not, creates one.
        try:
            if not os_path.isdir(self.data_folder_directory + pigeon_name):
                mkdir(os_path.join(self.data_folder_directory, pigeon_name))
                print("\n ** NEW DATA FOLDER FOR %s CREATED **" % pigeon_name.upper())
        except FileExistsError:
            print(f"DATA FOLDER FOR {pigeon_name.upper()} EXISTS")
                
                
    def build_chamber_screen(self):
        # Once the green "start program" button is pressed, then the mainscreen
        # object is created and pops up in a new window. It gets passed the
        # important inputs from the control panel.
        if self.subject_ID_variable.get() in self.pigeon_name_list:
            if self.exp_phase_variable.get() != "Select":
                print("Operant Box Screen Built") 
                self.MS = MainScreen(
                    str(self.subject_ID_variable.get()), # subject_ID
                    self.record_data_variable.get(), # Boolean for recording data (or not)
                    self.data_folder_directory, # directory for data folder
                    self.exp_phase_variable.get(), # Exp phase name
                    self.experimental_phase_titles.index(self.exp_phase_variable.get()) # Exp Phase number (0-1)
                    )
            else:
                print("\n ERROR: Input Stimulus Set Before Starting Session")
        else:
            print("\n ERROR: Input Correct Pigeon ID Before Starting Session")
            

# Then, setup the MainScreen object
# This is where we set up our experiment, really 

#let's first set up the familiarization phase (Phase 1)

class MainScreen(object):
    # First, we need to declare several functions that are 
    # called within the initial __init__() function that is 
    # run when the object is first built:
    
    def __init__(self, subject_ID, record_data, data_folder_directory,
                 exp_phase_name, exp_phase_num):
        ## Firstly, we need to set up all the variables passed from within
        # the control panel object to this MainScreen object. We do this 
        # by setting each argument as "self." objects to make them global
        # within this object.
        
        # Setup experimental phase
        self.exp_phase_name = exp_phase_name # e.g., "Phase 1: Familiarization"
        self.exp_phase_num = exp_phase_num # e.g., 0   
        if self.exp_phase_num == 0:
            self.exp_phase = "Phase 1"
        if self.exp_phase_num == 1:
            self.exp_phase = "Phase 2"

        
        # Setup data directory
        self.data_folder_directory = data_folder_directory
        
        ## Set the other pertanent variables given in the command window
        self.subject_ID = subject_ID
        self.record_data = record_data
        
        ## Set up the visual Canvas
        self.root = Toplevel() 
        self.root.title(f"P035b {self.exp_phase_name}: ") # this is the title of the window
        self.mainscreen_height = 768 # height of the experimental canvas screen
        self.mainscreen_width = 1024 # width of the experimental canvas screen
        self.root.bind("<Escape>", self.exit_program) # bind exit program to the "esc" key
        
        # If the version is the one running in the boxes...
        if operant_box_version: 
            # Keybind relevant keys
            self.cursor_visible = True # Cursor starts on...
            self.change_cursor_state() # turn off cursor UNCOMMENT
            self.root.bind("<c>",
                           lambda event: self.change_cursor_state()) # bind cursor on/off state to "c" key
            # Then fullscreen (on a 1024x768p screen). Assumes that both screens
            # that are being used have identical dimensions
            self.root.geometry(f"{self.mainscreen_width}x{self.mainscreen_height}+{self.mainscreen_width}+0")
            self.root.attributes('-fullscreen',
                                 True)
            self.mastercanvas = Canvas(self.root,
                                   bg="black")
            self.mastercanvas.pack(fill = BOTH,
                                   expand = True)
        # If we want to run a "human-friendly" version
        else: 
            # No keybinds and  1024x768p fixed window
            self.mastercanvas = Canvas(self.root,
                                   bg="black",
                                   height=self.mainscreen_height,
                                   width = self.mainscreen_width)
            self.mastercanvas.pack()
        
        self.start_time = datetime.now()  # This will be reset once the session actually starts
        self.trial_start = None # Duration into each trial as a second count, resets each trial
        self.trial_timer_duration = 10000 # Duration of each trial (ms)
        if not operant_box_version or self.subject_ID == "TEST":
            self.ITI_duration = 1000
        else:
            self.ITI_duration = 15000 # duration of inter-trial interval (ms) 
        if not operant_box_version or  self.subject_ID == "TEST":
            self.hopper_duration = 1000 # Duration of food access (ms)
        else: 
            self.hopper_duration = 6000
        # Set up FR (2) 
        self.comparison_FR = 2 
        self.comparison_key_presses = 0 # counts number of key presses on comp for each trial
        self.correct_comparison_key_presses = 0 # counts number of key presses on comp for each trial
        self.incorrect_comparison_key_presses = 0 # counts number of key presses on comp for each trial
        self.sample_key_presses = 0 # counts number of key presses on sample for each trial
        self.reinforced_trial_counter = 0 
        self.last_written_trial_num = None  # Track the last written trial number
        # Max number of trials within a session differ by phase
        if self.exp_phase_num == 0: # 
            self.max_number_of_reinforced_trials = 60
        else: # All others are 80
            self.max_number_of_reinforced_trials = 80 # default
        # Here is stuff that is relevant to building trial stimuli
        
        if self.exp_phase_num == 0:
            self.sample_name = "NA"
            self.comparison_name = "NA"
            self.foil_name = "NA"
            self.comparison_location = "NA"
            self.group_name = "NA"
            self.sample_FR = "NA"
            self.comparison_group = "NA"
            self.foil_group = "NA"

        # These are additional "under the hood" variables that need to be declared
        # Do if else statement for max trial number
        if self.exp_phase_num == 0:
            self.max_trials = 60 # Max number of trials within a session = 60 (10 comparisons shown 6 times)
        elif self.exp_phase_num == 1:
            self.max_trials = 80 # 20 pairs shown 4 times each
        self.session_data_frame = [] #This where trial-by-trial data is stored
        self.trial_stage = 0 # This tracks the stage within the trial
        self.current_trial_counter = 0 # This counts the number of trials that have passed
        header_list = [
            "SessionTime", "ExpPhase", "Subject", "Xcord", "Ycord", "Event",
            "TrialSubStage", "SampleStimulus", "LComp", "RComp", "CorrectKey",
            "TrialTime", "TrialNum", "ReinTrialNum", "SampleFR", "SampleTrialType", 
            "CorrectComparisonGroup", "FoilGroup", "Date","ComparisonTrialTime"] # Column headers
        self.session_data_frame.append(header_list) # First row of matrix is the column headers
        self.date = date.today().strftime("%y-%m-%d")
        self.myFile_loc = 'FILL' # To be filled later on after Pig. ID is provided (in set vars func below)
        
        if operant_box_version:
            if self.exp_phase_num == 0:
                self.stimuli_folder_path = "/home/blaisdelllab/Desktop/Experiments/P035/P035b_Stimuli_familiarized_comparisons" #grabs the stimuli
                self.stimuli_files_list = listdir(self.stimuli_folder_path) #creates a dictionary of the stimuli
            elif self.exp_phase_num == 1:
                self.stimuli_folder_path = "/home/blaisdelllab/Desktop/Experiments/P035/P035b_Stimuli" #grabs the stimuli
                self.stimuli_files_list = listdir(self.stimuli_folder_path) #creates a dictionary of the stimuli
        else: 
            if self.exp_phase_num == 0:
                self.stimuli_folder_path = "/Users/kayleyozimac/Desktop/P035b/P035b (mini project)/P035b_Stimuli_familiarized_comparisons" #grabs the stimuli
                self.stimuli_files_list = listdir(self.stimuli_folder_path) #creates a dictionary of the stimuli
            elif self.exp_phase_num == 1:
                self.stimuli_folder_path = "/Users/kayleyozimac/Desktop/P035b/P035b (mini project)/P035b_Stimuli" #grabs the stimuli
                self.stimuli_files_list = listdir(self.stimuli_folder_path) #creates a dictionary of the stimuli
        
        ## SET UP STIMULI ORDER FOR TRIALS
        
        if self.exp_phase_num == 0: # For familiarization phase
            self.presentation_counts = {stimulus: {"left": 0, "right": 0} for stimulus in self.stimuli_files_list}
            self.max_presentations = 6  # Each image should be shown 6 times (3 times in each location)
            
            # Make a dictionary that is n = self.max_trials long (60). Each entry 
            # should start with the file name, then the location (left/right).
            comparison_list = [stimulus for stimulus in self.stimuli_files_list]
            num_comparisons = len(comparison_list)
            
            self.max_trials = num_comparisons * self.max_presentations  # Total trials needed
            
            # Initialize the stimuli assignment dictionary
            self.stimuli_assignment_dict = {}
            trial_counter = 1
            
            # Create a list of locations, ensuring each comparison is shown equally on the left and right within each block of 10 trials
            def generate_balanced_location_list(size):
                return ["left", "right"] * (size // 2)
            
            while trial_counter <= self.max_trials:
                location_list = generate_balanced_location_list(10)
                shuffle(location_list)
                shuffle(comparison_list)  # Reshuffle comparisons for each pass
            
                for i in range(num_comparisons):
                    if trial_counter > self.max_trials:
                        break
                    comparison = comparison_list[i]
                    location = location_list.pop()
            
                    # Ensure each stimulus is shown 3 times on each side
                    while self.presentation_counts[comparison][location] >= 3:
                        location_list.insert(0, location)
                        shuffle(location_list)
                        location = location_list.pop()
            
                    # Update the assignment dictionary
                    self.stimuli_assignment_dict[trial_counter] = {
                        "stimuli": comparison,
                        "location": location
                    }
                    self.presentation_counts[comparison][location] += 1
                    trial_counter += 1
            
            self.stimuli_assignment_dict = dict(sorted(self.stimuli_assignment_dict.items()))
            print(self.stimuli_assignment_dict)
            
            # Verify if each stimulus is shown exactly 3 times on the left and 3 times on the right
            for stimulus, counts in self.presentation_counts.items():
                print(f"{stimulus}: {counts}")
                    
        elif self.exp_phase_num == 1: # If P035b experimental trials
            # Make a dictionary that is n = self.max_trials long (60). Each entry 
            # should start with the sample file name, the the correct comparison,
            # then the foil, the comparison location, and finally the group 
            # name. There were four potential groups:
            #   1) FF: ....
            #   2) FN: ...
            
            # {
            #   1 : {"sample": "S08.bmp", 
            #        "comparison": "C08.bmp",
            #        "foil": "C11.bmp",
            #        "comparison_location": "right",
            #        "group" : "FN"},
            #   2 : {"sample": "S17.bmp", 
            #        "comparison": "C17.bmp",
            #        "foil": "C12.bmp",
            #        "comparison_location": "left",
            #        "group" : "NN"},
            # }
            
            self.stimuli_assignment_dict = {} # This dictionary will contain all stimulus assignments
            # Create a list of samples
            sample_list = [samp for samp in self.stimuli_files_list if samp[0] == "S"]
            num_samples = len(sample_list)

            # Ensure the max_trials is a multiple of the number of samples
            assert self.max_trials % num_samples == 0, "max_trials should be a multiple of the number of samples"

            # Shuffle the sample list once
            shuffle(sample_list)

            # Assign the shuffled trials to the stimuli_assignment_dict
            trial_num_list = list(range(1, self.max_trials + 1)) # Trial numbers

            for i in range(self.max_trials):
                # Get the sample for the current trial
                        if i % num_samples == 0:  # Reshuffle sample list after every complete round
                            shuffle(sample_list)
                            
                        sample = sample_list[i % num_samples]  # Round-robin assignment
            
                        comparison = "C" + sample[1:]
                        # Differentiate the group number
                        s_num = int(sample[1:3]) # Sample number 
                        if s_num in [1, 2, 3, 4, 5]:
                            group = "FF"
                            low, high = 1, 11
                        elif s_num in [6, 7, 8, 9, 10]:
                            group = "FN"
                            low, high = 11, 21
                        elif s_num in [11, 12, 13, 14, 15]:
                            group = "NF"
                            low, high = 1, 11
                        elif s_num in [16, 17, 18, 19, 20]:
                            group = "NN"
                            low, high = 11, 21
                        # Find foil
                        potential_foil_list = list(range(low, high)) # Possible numbers
                        if group in ["FF", "NN"]: # Removed the comp number if there's overlap of group number
                            potential_foil_list.remove(s_num) 
                        foil_num = choice(potential_foil_list) # Just choose a number from the remaining list
                        if len(str(foil_num)) == 1:
                            foil_num = "0" + str(foil_num)
                        # Else, do nothing
                        foil = "C" + str(foil_num) + ".bmp"
                        
                        # Pick comparison_location
                        comparison_location = choice(["left", "right"]) # Counterbalance?
                        
                        # Sample FR
                        
                        sample_FR = choice(list(range(3,9))) #VR5 
                        
                        # Familiarized/non for correct comparison
                        c_num = int(comparison[1:3]) # Extract the number from comparison
                        if c_num in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
                            self.comparison_group = "F"
                        else:
                            self.comparison_group = "N"
            
                        f_num = int(foil[1:3]) # Extract the number from foil
                        if f_num in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
                            self.foil_group = "F"
                        else:
                            self.foil_group = "N"
                        
                        # Add trial to our dictionary
                        trial_dict = {"sample": sample, 
                                      "comparison": comparison,
                                      "foil": foil,
                                      "comparison_location": comparison_location,
                                      "group" : group,
                                      "sample_FR": sample_FR,
                                      "comparison_group": self.comparison_group,
                                      "foil_group": self.foil_group}
                        self.stimuli_assignment_dict[trial_num_list[i]] = trial_dict    
            
            self.stimuli_assignment_dict = dict(sorted(self.stimuli_assignment_dict.items()))
            print(self.stimuli_assignment_dict)

        ## Finally, start the recursive loop that runs the program:
        self.place_birds_in_box()
                
    def place_birds_in_box(self):
        # This is the default screen run until the birds are placed into the
        # box and the space bar is pressed. It then proceedes to the ITI. It only
        # runs in the operant box version. After the space bar is pressed, the
        # "first_ITI" function is called for the only time prior to the first trial
        self.root.bind("<space>", self.first_ITI) # bind cursor state to "space" key
        #shows program text (i.e., what was chosen in the control panel)
        self.mastercanvas.create_text(512,384,
                                      fill="white",
                                      font="Times 26 italic bold",
                                      text=f"P035b \n Place bird in box, then press space \n Subject: {self.subject_ID} \n Training Phase: {self.exp_phase_name}")
    
    def first_ITI(self, event):
        print("Spacebar pressed -- SESSION STARTED") 
        self.root.unbind("<space>") # bind cursor state to "space" key
        self.clear_canvas()
        self.start_time = datetime.now()  # This is the ACTUAL time the session starts
        if not operant_box_version or self.subject_ID == "TEST": # If test, don't worry about first ITI delay
            self.ITI_duration = 1 * 1000
            self.root.after(1, lambda: self.ITI())
        else:
            self.root.after(30000, lambda: self.ITI())
            
    #create the first part of a trial (e.g., sample stimulus presented)
    def sample_phase(self):
        
        if self.exp_phase_num == 1:
            if operant_box_version and not self.light_HL_on_bool:
                rpi_board.write(house_light_GPIO_num,
                                True) # Turn on the houselight
            
        self.clear_canvas()
        self.trial_stage = 0
        #build background (i.e., "background pecks)
        self.mastercanvas.create_rectangle(0,0,
                                           self.mainscreen_width,
                                           self.mainscreen_height,
                                           fill = "black",
                                           outline = "black",
                                           tag = "bkgrd")
        self.mastercanvas.tag_bind("bkgrd",
                                   "<Button-1>",
                                   lambda event, 
                                   event_type = "background_peck": 
                                       self.write_data(event, event_type))

        trial_info_dict = self.stimuli_assignment_dict[self.current_trial_counter]
        sample_image_name = trial_info_dict["sample"]  

        # Load the selected image
        selected_image_path = os_path.join(self.stimuli_folder_path, sample_image_name)
        selected_image = Image.open(selected_image_path)
        self.image = ImageTk.PhotoImage(selected_image)
        
        x,y = 512, 384
        
        #Create black circle around stimuli
        oval_radius = 85  
        self.mastercanvas.create_oval(x - oval_radius, y - oval_radius,
                                      x + oval_radius, y + oval_radius,
                                      fill = "black",
            #                          outline = "red",
                                      tag = "button")
        
        # Finally, create/show the image on the canvas
        self.mastercanvas.create_image(x, y, 
                                       image=self.image, 
                                       anchor="center", 
                                       tag="button")

        # Bind the click event (i.e., peck to the stimulus results in moving onto reinforcement_phase)
        self.mastercanvas.tag_bind("button", 
                                   "<Button-1>", 
                                   self.sample_key_press)
        
        # Assign sample_FR from trial_info_dict
        self.sample_FR = trial_info_dict.get("sample_FR")
        
###### peck counter (sample)

    def sample_key_press(self, event):
        # This is one half of the RR loop. It can be thought of as the resting
        # "return state" that is dependent upon a key press (on the O key). 
        # Otherwise, it will stay in this state forever.
        self.write_data(event, "sample_key_press")
        self.sample_key_presses += 1 
        if self.sample_key_presses >= int(self.sample_FR):
            self.comparison_phase()
        else:
            self.sample_phase()
        

    #create the choice part of a trial (e.g., comparison stimulus presented)
    def comparison_phase(self):
        
        
        self.clear_canvas()
        
        if self.exp_phase_num == 0:
            if operant_box_version and not self.light_HL_on_bool:
                rpi_board.write(house_light_GPIO_num,
                                True) # Turn on the houselight
        
        self.trial_stage = 1
        
        # Check if the trial number has changed
        if self.current_trial_counter != self.last_written_trial_num:
            self.comparison_start_time = datetime.now()  # Start the timer if the trial number has changed
            self.last_written_trial_num = self.current_trial_counter
        
        self.mastercanvas.create_rectangle(0,0,
                                           self.mainscreen_width,
                                           self.mainscreen_height,
                                           fill = "black",
                                           outline = "black",
                                           tag = "bkgrd")
        #build background (i.e., "background pecks)
        self.mastercanvas.tag_bind("bkgrd",
                                   "<Button-1>",
                                   lambda event, 
                                   event_type = "background_peck": 
                                       self.write_data(event, event_type))
            
        #differentiate between phase 1 and phase 2 
        
        if self.exp_phase_num == 1: # For experimental trials
        

        #First we need to grab oue stimuli 
            trial_info_dict = self.stimuli_assignment_dict[self.current_trial_counter]
        
        #load comparisons and their respective locations from dictionary
        
            comparison_image_name = trial_info_dict["comparison"]  # This should work now
            foil_image_name = trial_info_dict["foil"]  # This should work now
            comparison_location = trial_info_dict["comparison_location"]  # This should work now
        
        # Load the comparison image
            comparison_image_path = os_path.join(self.stimuli_folder_path, comparison_image_name)
            comparison_image = Image.open(comparison_image_path)
            self.comparison_image = ImageTk.PhotoImage(comparison_image)
        
        # Load the foil image
            foil_image_path = os_path.join(self.stimuli_folder_path, foil_image_name)
            foil_image = Image.open(foil_image_path)
            self.foil_image = ImageTk.PhotoImage(foil_image)
        
        # Determine coordinates based on comparison_location
            if comparison_location == "left":
                comparison_x, comparison_y = 160, 550  # Left side
                foil_x, foil_y = 864, 550  # Right side
            else:
                    comparison_x, comparison_y = 864, 550  # Right side
                    foil_x, foil_y = 160, 550  # Left side
        
        # Create black circle around comparison image
            oval_radius = 85
            self.mastercanvas.create_oval(comparison_x - oval_radius, comparison_y - oval_radius,
                              comparison_x + oval_radius, comparison_y + oval_radius,
                              fill="black",
            #                  outline="red",
                              tag="comparison_button")

        # Create black circle around foil image
            self.mastercanvas.create_oval(foil_x - oval_radius, foil_y - oval_radius,
                              foil_x + oval_radius, foil_y + oval_radius,
                              fill="black",
             #                 outline="red",
                              tag="foil_button")
        
        # Finally, create/show the comparison image on the canvas
            self.mastercanvas.create_image(comparison_x, comparison_y,
                               image=self.comparison_image,
                               anchor="center",
                               tag="comparison_button")
            
            # Bind the comparison button to the correct choice handler
            self.mastercanvas.tag_bind("comparison_button",
                                       "<Button-1>",
                                       self.correct_choice)
                
                                                       
    
        # Finally, create/show the foil image on the canvas
            self.mastercanvas.create_image(foil_x, foil_y,
                               image=self.foil_image,
                               anchor="center",
                               tag="foil_button")
        
        # Bind the foil button to the incorrect choice handler
            self.mastercanvas.tag_bind("foil_button",
                           "<Button-1>",
                            self.incorrect_choice)
            
            #Keep the sample up
            
            sample_image_name = trial_info_dict["sample"]  # load sample

        # Load the selected image
            selected_image_path = os_path.join(self.stimuli_folder_path, sample_image_name)
            selected_image = Image.open(selected_image_path)
            self.image = ImageTk.PhotoImage(selected_image)
            
            x,y = 512, 384
            
            #Create black circle around stimuli
            oval_radius = 85  
            self.mastercanvas.create_oval(x - oval_radius, y - oval_radius,
                                          x + oval_radius, y + oval_radius,
                                          fill = "black",
                     #                     outline = "red",
                                          tag = "inactive_sample_key_press")
            
                        
            self.mastercanvas.tag_bind("inactive_sample_key_press",
                                       "<Button-1>",
                                       lambda event, 
                                       event_type = "inactive_sample_key_press": 
                                           self.write_data(event, event_type))
            
            self.mastercanvas.create_image(x,y,
                                image=self.image, 
                                anchor="center", 
                                tag="inactive_sample_key_press")
            
            self.mastercanvas.tag_bind("inactive_sample_key_press",
                                       "<Button-1>",
                                       lambda event, 
                                       event_type = "inactive_sample_key_press": 
                                           self.write_data(event, event_type))
            
            
        elif self.exp_phase_num == 0: # For familiarization phase

        #####TRACK AND RECORD LOCATION
        
        #if else (logic = if comparison, put in comparison location; if not, put in the other location)
        
        # First, we need to grab our stimuli. 
            trial_info_dict = self.stimuli_assignment_dict[self.current_trial_counter]
        
            stimulus_file = trial_info_dict['stimuli']
            location = trial_info_dict['location']
        
        # Load the selected image
            selected_image_path = os_path.join(self.stimuli_folder_path, stimulus_file)
            selected_image = Image.open(selected_image_path)
            self.image = ImageTk.PhotoImage(selected_image)

        # Determine coordinates based on the selected location above
            if location == "left":
                x, y = 160, 550
            else:  # If right...
                x, y = 864, 550
        #Create black circle around stimuli
            oval_radius = 85  
            self.mastercanvas.create_oval(x - oval_radius, y - oval_radius,
                                      x + oval_radius, y + oval_radius,
                                      fill = "black",
               #                       outline = "red",
                                      tag = "button")

        # Finally, create/show the image on the canvas
            self.mastercanvas.create_image(x,y, 
                                       image=self.image, 
                                       anchor="center", 
                                       tag="button")

        # Bind the click event (i.e., peck to the stimulus results in moving onto reinforcement_phase)
            self.mastercanvas.tag_bind("button", 
                                   "<Button-1>", 
                                   self.comp_key_press)
            
    #comparison phase timer
        
    def update_comparison_trial_time(self):
        if hasattr(self, 'comparison_start_time'):
            self.comparison_trial_time = (datetime.now() - self.comparison_start_time).total_seconds()
        else:
            self.comparison_trial_time = "NA"
        

###### peck counter (comparison)

    def comp_key_press(self, event):
        # This is one half of the RR loop. It can be thought of as the resting
        # "return state" that is dependent upon a key press (on the O key). 
        # Otherwise, it will stay in this state forever.
        self.update_comparison_trial_time()  # Update the timer
        self.write_data(event, "comparison_key_press")
        self.comparison_key_presses += 1 
        if self.comparison_key_presses >= self.comparison_FR:
             self.reinforcement_phase()
        else:
             self.comparison_phase()
            
            
    # correct choice
    
    def correct_choice(self, event):
        # This is one half of the RR loop. It can be thought of as the resting
        # "return state" that is dependent upon a key press (on the O key). 
        # Otherwise, it will stay in this state forever.
        self.update_comparison_trial_time()  # Update the timer
        self.write_data(event, "correct_choice"),
        self.correct_comparison_key_presses += 1 
        if self.correct_comparison_key_presses >= self.comparison_FR:
             self.reinforcement_phase()
        else:
             self.comparison_phase()
        
    #incorrect choice
    def incorrect_choice(self, event):
        # This is one half of the RR loop. It can be thought of as the resting
        # "return state" that is dependent upon a key press (on the O key). 
        # Otherwise, it will stay in this state forever.
        self.update_comparison_trial_time()  # Update the timer
        self.write_data(event, "incorrect_choice")
        self.incorrect_comparison_key_presses += 1 
        if self.incorrect_comparison_key_presses >= self.comparison_FR:
             self.ITI()
        else:
             self.comparison_phase()
            
#######
            
    #Reinforcement!
    def reinforcement_phase(self):
        self.trial_stage = 2
        # We first need to add one to the reinforcement counter
        self.reinforced_trial_counter += 1
        # In this part of a trial, reinforcement is provided
        self.clear_canvas()
        self.write_data(None, "reinforcement_provided")
    # Print text on screen if a test (should be black if an experimental trial)
        if not operant_box_version or self.subject_ID == "TEST":
            self.mastercanvas.create_text(512, 384,
                                      fill="white",
                                      font="Times 26 italic bold",
                                      text=f"Reinforcement TIME ({int(self.hopper_duration/1000)} s)")
        
        # Next send output to the box's hardware
        if operant_box_version:
            rpi_board.write(house_light_GPIO_num,
                            False) # Turn off the house light
            rpi_board.write(hopper_light_GPIO_num,
                            True) # Turn off the house light
            rpi_board.set_servo_pulsewidth(servo_GPIO_num,
                                           hopper_up_val) # Move hopper to up position
            # Check if this is the last trial
        if self.current_trial_counter == self.max_trials:
            self.root.after(self.hopper_duration, lambda: self.exit_program("event"))
        else:
            self.root.after(self.hopper_duration, lambda: self.ITI())
       # self.root.after(self.hopper_duration,
       #                 lambda: self.ITI())
    
        
    def ITI (self):
        # In this part of a trial, it is ITI
            
        self.clear_canvas()
        
        # Make sure pecks during ITI are saved
        self.mastercanvas.create_rectangle(0,0,
                                           self.mainscreen_width,
                                           self.mainscreen_height,
                                           fill = "black",
                                           outline = "black",
                                           tag = "bkgrd")
        self.mastercanvas.tag_bind("bkgrd",
                                   "<Button-1>",
                                   lambda event, 
                                   event_type = "ITI_peck": 
                                       self.write_data(event, event_type))
            
        # First, check to see if any session limits have been reached (e.g.,
        # if the max time or reinforcers earned limits are reached).
        
        # First, check to see if any session limits have been reached (e.g.,
        # if the max time or reinforcers earned limits are reached).
        if self.current_trial_counter  == self.max_number_of_reinforced_trials + 1:
            print("&&& Trial max reached &&&")
            self.exit_program("event")
            
      # Else, after a timer move on to the next trial. Note that,
      # although the after() function is given here, the rest of the code 
      # within this function is still executed before moving on.
   #     else: 
          # Print text on screen if a test (should be black if an experimental trial)
        if not operant_box_version or self.subject_ID == "TEST":
             self.mastercanvas.create_text(512,384,
                                            fill="white",
                                            font="Times 26 italic bold",
                                            text=f"ITI ({int(self.ITI_duration/1000)} sec.)")
              
          # This turns all the stimuli off from the previous trial (during the
          # ITI).
        if operant_box_version:
              rpi_board.write(hopper_light_GPIO_num,
                              False) # Turn off the hopper light
              rpi_board.set_servo_pulsewidth(servo_GPIO_num,
                                             hopper_down_val) # Hopper down
              rpi_board.write(house_light_GPIO_num, 
                              False) # Turn off house light
          
          # Tracks whether HL light is currently on
        self.light_HL_on_bool = False
              
        # Reset other variables for the following trial.
        # Update everything for the next trial
        # Increment trial counter for the next trial
        self.current_trial_counter += 1
        self.comparison_key_presses = 0 # counts number of key presses on comp for each trial
        self.correct_comparison_key_presses = 0 # counts number of key presses on comp for each trial
        self.incorrect_comparison_key_presses = 0 # counts number of key presses on comp for each trial
        self.sample_key_presses = 0
        self.trial_stage = 0 
        self.trial_start = time() # Set trial start time (note that it includes the ITI, which is subtracted later)
         # Update everything for the next trial
        self.last_written_trial_num = None  # Reset the last written trial number for the new trial
        self.comparison_start_time = None  # Reset the comparison start time for the new trial
        # If in phase 2, set all of our trial information for the coming trial
        print(type(self.stimuli_assignment_dict[self.current_trial_counter]))
        print(self.stimuli_assignment_dict[self.current_trial_counter])
        if self.exp_phase_num == 1:
            trial_info = self.stimuli_assignment_dict[self.current_trial_counter]
            self.sample_name = trial_info['sample']
            self.comparison_name = trial_info['comparison']
            self.foil_name = trial_info['foil']
            self.comparison_location = trial_info['comparison_location']
            self.group_name = trial_info['group']
        #build background (i.e., "background pecks)
        # Also write data
        self.write_comp_data(False) # update data .csv with trial data from the previous trial
        # Timer
        if self.exp_phase_num == 0:
            self.root.after(self.ITI_duration,
                            self.comparison_phase)
        elif self.exp_phase_num == 1:
            self.root.after(self.ITI_duration,
                            self.sample_phase)
        
        # Finally, print terminal feedback "headers" for each event within the next trial
        print(f"\n{'*'*30} Trial {self.current_trial_counter} begins {'*'*30}") # Terminal feedback...
        print(f"{'Event Type':>30} | Xcord. Ycord. | Stage | Session Time")
            
        
    def change_cursor_state(self):
        # This function toggles the cursor state on/off. 
        # May need to update accessibility settings on your machince.
        if self.cursor_visible: # If cursor currently on...
            self.root.config(cursor="none") # Turn off cursor
            print("### Cursor turned off ###")
            self.cursor_visible = False
        else: # If cursor currently off...
            self.root.config(cursor="") # Turn on cursor
            print("### Cursor turned on ###")
            self.cursor_visible = True
    
    def clear_canvas(self):
         # This is by far the most called function across the program. It
         # deletes all the objects currently on the Canvas. A finer point to 
         # note here is that objects still exist onscreen if they are covered
         # up (rendering them invisible and inaccessible); if too many objects
         # are stacked upon each other, it can may be too difficult to track/
         # project at once (especially if many of the objects have functions 
         # tied to them. Therefore, its important to frequently clean up the 
         # Canvas by literally deleting every element.
        try:
            self.mastercanvas.delete("all")
        except TclError:
            print("No screen to exit")
        
    def exit_program(self, event): 
        # This function can be called two different ways: automatically (when
        # time/reinforcer session constraints are reached) or manually (via the
        # "End Program" button in the control panel or bound "esc" key).
            
        # The program does a few different things:
        #   1) Return hopper to down state, in case session was manually ended
        #       during reinforcement (it shouldn't be)
        #   2) Turn cursor back on
        #   3) Writes compiled data matrix to a .csv file 
        #   4) Destroys the Canvas object 
        #   5) Calls the Paint object, which creates an onscreen Paint Canvas.
        #       In the future, if we aren't using the paint object, we'll need 
        #       to 
        def other_exit_funcs():
            if operant_box_version:
                rpi_board.write(hopper_light_GPIO_num,
                                False) # turn off hopper light
                rpi_board.write(house_light_GPIO_num,
                                False) # Turn off the house light
                rpi_board.set_servo_pulsewidth(servo_GPIO_num,
                                               hopper_down_val) # set hopper to down state
                sleep(1) # Sleep for 1 s
                rpi_board.set_PWM_dutycycle(servo_GPIO_num,
                                            False)
                rpi_board.set_PWM_frequency(servo_GPIO_num,
                                            False)
                rpi_board.stop() # Kill RPi board
                # root.after_cancel(AFTER)
                if not self.cursor_visible:
                	self.change_cursor_state() # turn cursor back on, if applicable
            self.write_comp_data(True) # write data for end of session
            if self.root.winfo_exists():  # Check if the window still exists
                self.root.destroy()  # destroy Canvas
            print("\n GUI window exited")
            
        self.clear_canvas()
        other_exit_funcs()
        print("\n You may now exit the terminal and operater windows now.")
        if operant_box_version:
            polygon_fill.main(self.subject_ID) # call paint object
            

    def write_data(self, event, outcome):
        # This function writes a new data line after EVERY peck. Data is
        # organized into a matrix (just a list/vector with two dimensions,
        # similar to a table). This matrix is appended to throughout the 
        # session, then written to a .csv at the end of each trial. This
        # ensures that, if the program crashes, all data up to the current
        # trial should be saved.
        if event != None: 
            x, y = event.x, event.y
        else: # There are certain data events that are not pecks.
            x, y = "NA", "NA"   
        print(f"{outcome:>30} | x: {x: ^3} y: {y:^3} | {self.trial_stage:^5} | {str(datetime.now() - self.start_time)}")
        
        # Initialize comparison_group and foil_group
        comparison_group = "NA"
        foil_group = "NA"
        
        # Retrieve trial information directly from the stimuli assignment dictionary
        trial_info_dict = self.stimuli_assignment_dict[self.current_trial_counter]
        
        if self.exp_phase_num == 1:
            comparison_group = trial_info_dict["comparison_group"]  
            foil_group = trial_info_dict["foil_group"]
        
        # Let's establish where our stimuli are (if the session has started)
        if self.exp_phase_num == 0 and self.current_trial_counter > 0:
            trial_info_dict = self.stimuli_assignment_dict[self.current_trial_counter]
            
            stimulus_file = trial_info_dict['stimuli'] # stimulus shown
            location = trial_info_dict['location'] # Left or right
            
            if location == "left":
                LComp = stimulus_file
                RComp = "NA"
            else:
                LComp = "NA"
                RComp = stimulus_file
        # Change for exp_phase_num == 1
        else:
            if self.comparison_location == "left":
                LComp = self.comparison_name
                RComp = self.foil_name
            else:
                LComp = self.foil_name
                RComp = self.comparison_name 
            # Calculate the comparison trial time consistently
        comparison_trial_time = (datetime.now() - self.comparison_start_time).total_seconds() if self.trial_stage == 1 else "NA"

        # Append peck data to data frame...
        self.session_data_frame.append([
            str(datetime.now() - self.start_time), # SessionTime as datetime object
            self.exp_phase,
            self.subject_ID,
            x,
            y, 
            outcome,
            self.trial_stage,
            self.sample_name, # SampleStimulus
            LComp, # LComp
            RComp, # RComp
            self.comparison_name, # "CorrectKey"
            round((time() - self.trial_start - (self.ITI_duration/1000)), 5), # Time into this trial minus ITI (if session ends during ITI, will be negative)
            self.current_trial_counter, 
            self.reinforced_trial_counter, # ReinTrialNum
            self.sample_FR, # SampleFR
            self.group_name, # SampleTrialType
            comparison_group, # ComparisonGroup
            foil_group, # FoilGroup
            date.today(), # Today's date as "MM-DD-YYYY"
            comparison_trial_time
        ])
        header_list = [
            "SessionTime", "ExpPhase", "Subject", "Xcord", "Ycord", "Event",
            "TrialSubStage", "SampleStimulus", "LComp", "RComp", "CorrectKey",
            "TrialTime", "TrialNum", "ReinTrialNum", "SampleFR", "SampleTrialType", 
            "CorrectComparisonGroup", "FoilGroup", "Date", "ComparisonTrialTime"] # Column headers
        
        
    def write_comp_data(self, SessionEnded):
        # The following function creates a .csv data document. It is either 
        # called after each trial during the ITI (SessionEnded ==False) or 
        # one the session finishes (SessionEnded). If the first time the 
        # function is called, it will produce a new .csv out of the
        # session_data_matrix variable, named after the subject, date, and
        # training phase. Consecutive iterations of the function will simply
        # write over the existing document.
        if SessionEnded:
            self.write_data(None, "SessionEnds") # Writes end of session to df
        if self.record_data : # If experimenter has choosen to automatically record data in seperate sheet:
            myFile_loc = f"{self.data_folder_directory}/{self.subject_ID}/{self.subject_ID}_{self.start_time.strftime('%Y-%m-%d_%H.%M.%S')}_P035b_data-Phase{self.exp_phase_num}.csv" # location of written .csv
            
            # This loop writes the data in the matrix to the .csv              
            edit_myFile = open(myFile_loc, 'w', newline='')
            with edit_myFile as myFile:
                w = writer(myFile, quoting=QUOTE_MINIMAL)
                w.writerows(self.session_data_frame) # Write all event/trial data 
                
            print(f"\n- Data file written to {myFile_loc}")

#%% Finally, this is the code that actually runs:
try:   
    if __name__ == '__main__':
        cp = ExperimenterControlPanel()
except:
    # If an unexpected error, make sure to clean up the GPIO board
    if operant_box_version:
        rpi_board.set_PWM_dutycycle(servo_GPIO_num,
                                    False)
        rpi_board.set_PWM_frequency(servo_GPIO_num,
                                    False)
        rpi_board.stop()
