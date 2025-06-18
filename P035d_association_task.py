#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 16 11:33:35 2025

@author: kayleyozimac


#This is the code for Kayley Ozimac's mini project (P035d) for her 'FOAM' project
    
    1) Phase 1 (familiarization via association): 10 (C1-10) comparison stimuli will be pre-
exposed to the subjects. This phase will consist of 3 different subphases:
    
        Subphase 1 (distractor sample). A training sample began the trial. Pecks (VR 5)
resulted in the beginning of Subphase 2.
    
        Subphase 2 (comparison). A paired comparison to the distractor sample is
presented below the sample. Two (?) pecks at the stimulus resulted in 1 seconda delay before
the presentation of:
    
        Subphase 3 (choice task). As the comparison stimulus acted as a start key to 
the trial. That is, two circles, each different sizes, were positioned in both 
of the comparison locations. During this task, birds must choose the smaller of 
the 2 stimuli in order to recieve reinforcement (6s access to the food hopper). 

The completion of each trial is followed by a 15-s intertrial interval (ITI), 
which remained in effect throughout the experiment. The remaining 10 comparison 
stimuli were not shown during this phase. 

Each session consisted of x amount of trials, with each comparison stimulus 
presented 6 times (3 times on the right and 3 times on the left) in a 
pseudorandomized order (*or positioned int he sample location).

    2) Phase 3 (distractor sample association test): 40 probe trials interspersed
between 60 regaular training trials. During probe trials, there is a choice between
the familiarized comparison linked with the distractor sample (e.g., DS01-C01) and
a familiarized comparison linked to another distractor sample (e.g., CO1). Choice of
either comparison results in a 1 second delay before being presented with the choice 
task from Phase 1. 
        
    3) Phase 2 (experimental trials): The next phase is a simple MTS task in which 
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
        self.control_window.title("P035d Control Panel")
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
        self.experimental_phase_titles = [
            "Phase 1 (Familiarization via association)",
            "Phase 2 (Intermediate test trials)",
            "Phase 3 (MTS trials)"
        ]

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
        # First, ensure the main data directory exists
        if not os_path.isdir(self.data_folder_directory):
            mkdir(self.data_folder_directory)
    
        # Then check and create the subfolder for the specific pigeon
        pigeon_path = os_path.join(self.data_folder_directory, pigeon_name)
        if not os_path.isdir(pigeon_path):
            mkdir(pigeon_path)
            print(f"\n ** NEW DATA FOLDER FOR {pigeon_name.upper()} CREATED **")
        else:
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
        
        self.comparison_location = None  # Initialize this to None or an appropriate default value
        self.sample_name = "NA"  # Initialize sample_name with a default value
        self.comparison_name = "NA"
        
        # Setup experimental phase
        self.exp_phase_name = exp_phase_name # e.g., "Phase 1: Familiarization"
        self.exp_phase_num = exp_phase_num # e.g., 0   
        if self.exp_phase_num == 0:
            self.exp_phase = "Phase 1"
        if self.exp_phase_num == 1:
            self.exp_phase = "Phase 2"
        if self.exp_phase_num == 2:
            self.exp_phase = "Phase 3"

        
        # Setup data directory
        self.data_folder_directory = data_folder_directory
        
        ## Set the other pertanent variables given in the command window
        self.subject_ID = subject_ID
        self.record_data = record_data
        
        ## Set up the visual Canvas
        self.root = Toplevel() 
        self.root.title(f"P035d {self.exp_phase_name}: ") # this is the title of the window
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
            # Set geometry before showing window
            self.root.geometry(f"{self.mainscreen_width}x{self.mainscreen_height}+1920+0")
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
            self.hopper_duration = 4500
        # Set up FR (2) 
        self.comparison_FR = 2 
        self.comparison_key_presses = 0 # counts number of key presses on comp for each trial
        self.correct_comparison_key_presses = 0 # counts number of key presses on comp for each trial
        self.incorrect_comparison_key_presses = 0 # counts number of key presses on comp for each trial
        self.sample_key_presses = 0 # counts number of key presses on sample for each trial
        self.reinforced_trial_counter = 0 
        self.last_written_trial_num = None  # Track the last written trial number
        self.max_trials = 100
        # Max number of trials within a session differ by phase
        if self.exp_phase_num == 0: # 
            self.max_number_of_reinforced_trials = 100
        else: # All others are 80
            self.max_number_of_reinforced_trials = 100 # default
        
        # Here is stuff that is relevant to building trial stimuli
        if self.exp_phase_num == 0:
            self.sample_name = "NA"
            self.comparison_name = "NA"
            self.foil_name = "NA"
            self.comparison_location = "NA"
            self.group_name = "NA"

        # These are additional "under the hood" variables that need to be declared
        self.session_data_frame = [] #This where trial-by-trial data is stored
        self.trial_stage = 0 # This tracks the stage within the trial
        self.current_trial_counter = 0 # This counts the number of trials that have passed
      
        header_list = [
            "SessionTime", "ExpPhase", "Subject", "Xcord", "Ycord", "Event",
            "TrialSubStage", "SampleStimulus", "CompStimulus", "LComp", "RComp", 
            "CorrectKey", "TrialType", "SmallCircleLoc", "LargeCircleLoc", 
            "TrialTime", "TrialNum", "ReinTrialNum", "SampleFR", 
            "ComparisonFamiliarity", "FoilFamiliarity", "Date"]
    
        self.session_data_frame.append(header_list) # First row of matrix is the column headers
        self.date = date.today().strftime("%y-%m-%d")
        self.myFile_loc = 'FILL' # To be filled later on after Pig. ID is provided (in set vars func below)
        
        # Determine base path depending on environment
        if operant_box_version:
            base_path = "/home/blaisdelllab/Desktop/Experiments/P035"
        else:
            base_path = "/Users/kayleyozimac/Desktop/P035d"
        
        # Assign paths and load files based on phase
        if self.exp_phase_num in [0, 1]:  # Phase 0 and Phase 1 use the same stimuli
            self.stimuli_folder_path = os_path.join(base_path, "P035d_familiarized_comparisons")
            self.stimuli_files_list = listdir(self.stimuli_folder_path)
            self.comparison_files_list = self.stimuli_files_list
        
            # Distractor samples path
            if operant_box_version:
                self.distractor_stimuli_path = os_path.join(base_path, "/home/blaisdelllab/Desktop/Experiments/P035/P035d_distractor_samples")
            else:
                self.distractor_stimuli_path = os_path.join(base_path, "P035d_distractor_samples")
        
            self.sample_files_list = listdir(self.distractor_stimuli_path)
            self.distractor_files_list = self.sample_files_list
        
        elif self.exp_phase_num == 2:  # Experimental MTS trials
            self.stimuli_folder_path = os_path.join(base_path, "P035d_Stimuli")
            self.stimuli_files_list = listdir(self.stimuli_folder_path)
        

        
        ## SET UP STIMULI ORDER FOR TRIALS
                
        if self.exp_phase_num == 0:  # For familiarization phase
            comparison_list = sorted(self.comparison_files_list)
            distractor_list = sorted(self.distractor_files_list)
            
            print("Comparison files:", self.comparison_files_list)
            print("Distractor files:", self.distractor_files_list)

        
            assert len(comparison_list) == len(distractor_list), \
                "Number of comparisons and distractors must match (10 each)."
        
            self.max_presentations = 10  # Each stimulus shown 10 times
            self.max_trials = len(comparison_list) * self.max_presentations  # 10 × 10 = 100 trials
            self.stimuli_assignment_dict = {}
        
            trial_counter = 1
        
            # Build 6 blocks, each showing all comparisons once
            for rep in range(self.max_presentations):
                # Shuffle trial order within block
                block = list(zip(comparison_list, distractor_list))
                shuffle(block)
        
                # Alternate left/right placement per comparison
                location_balance = ["left", "right"] * (len(block) // 2)
                shuffle(location_balance)
        
                for i, (comparison, distractor) in enumerate(block):
                    location = location_balance[i]
                    sample_FR = choice(range(3, 9))  # FR between 3–8
                    self.stimuli_assignment_dict[trial_counter] = {
                        "paired_comparison": comparison,
                        "distractor_sample": distractor,
                        "comparison_location": location,
                        "sample_FR": sample_FR
                    }
                    trial_counter += 1
        
            print("\nTrial assignments (Phase 1):")
            for t, v in self.stimuli_assignment_dict.items():
                print(f"Trial {t}: Distractor = {v['distractor_sample']}, Comp = {v['paired_comparison']}, Side = {v['comparison_location']}")

            
            if self.choice_task:
                
                # Number of trials should match the comparison phase trials
                self.max_trials = 100  # Assuming max_trials is 100
                
                # Define the two stimuli
                smaller_square = "correct_choice"
                larger_square = "incorrect_choice"
                
                # Initialize the stimuli assignment dictionary
                self.choice_stimuli_assignment_dict = {}
                
                # Create a list of trial numbers
                choice_trial_num_list = list(range(1, self.max_trials + 1))
                
                # Initialize lists to track last positions
                last_position = None
                consecutive_count = 0
                
                for i in range(self.max_trials):
                    # Randomly assign initial position
                    smaller_square_position = choice(["left", "right"])
                    
                    # Ensure no more than three consecutive placements in the same position
                    if smaller_square_position == last_position:
                        consecutive_count += 1
                        if consecutive_count > 3:
                            # Flip position if it would result in a fourth consecutive repeat
                            smaller_square_position = "right" if last_position == "left" else "left"
                            consecutive_count = 1  # Reset consecutive count
                    else:
                        consecutive_count = 1  # Reset if position changes
                    
                    # Update last position for tracking
                    last_position = smaller_square_position
                    larger_square_position = "right" if smaller_square_position == "left" else "left"
                    
                    # Assign the trial with the counterbalanced stimuli
                    choice_trial_dict = {
                        "smaller_square": smaller_square,
                        "larger_square": larger_square,
                        "left_stimulus": smaller_square if smaller_square_position == "left" else larger_square,
                        "right_stimulus": larger_square if smaller_square_position == "left" else smaller_square,
                    }
                    
                    # Add trial to the stimuli assignment dictionary
                    self.choice_stimuli_assignment_dict[choice_trial_num_list[i]] = choice_trial_dict
                
                # Sort the dictionary by trial number for consistency
  #              self.choice_stimuli_assignment_dict = dict(sorted(self.choice_stimuli_assignment_dict.items()))
  #              print(self.choice_stimuli_assignment_dict)
       
        elif self.exp_phase_num == 1:  # NEW Phase 2 (Mixed familiarization + test trials)
            comparison_list = sorted([stim for stim in self.comparison_files_list])
            distractor_list = sorted([stim for stim in self.distractor_files_list])
            assert len(comparison_list) == 10 and len(distractor_list) == 10, "Phase 2 must have 10 comparisons + 10 distractors"

            # Helper: build shuffled blocks of (comp, distractor) pairs
            def make_blocks(comp_list, dist_list, num_blocks):
                blocks = []
                for _ in range(num_blocks):
                    block = list(zip(comp_list, dist_list))
                    shuffle(block)
                    blocks.append(block)
                return blocks
            
            # --- Generate 6 training blocks of 10 trials (each comp once per block) ---
            training_blocks = make_blocks(comparison_list, distractor_list, 6)
            training_trials = []
            for block in training_blocks:
                for stim, distractor in block:
                    training_trials.append({
                        "trial_type": "training",
                        "paired_comparison": stim,
                        "distractor_sample": distractor,
                        "sample_FR": choice(range(3, 9)),
                        "comparison_location": choice(["left", "right"])
                    })
            
            # --- Generate 4 test blocks of 10 trials with unique foils ---
            comparison_to_foils = {}
            for i, stim in enumerate(comparison_list):
                foil_pool = comparison_list[:i] + comparison_list[i+1:]
                shuffle(foil_pool)
                comparison_to_foils[stim] = foil_pool[:4]
            
            test_blocks = []
            for i in range(4):
                block = []
                for stim, distractor in zip(comparison_list, distractor_list):
                    foil = comparison_to_foils[stim][i]
                    block.append({
                        "trial_type": "test",
                        "paired_comparison": stim,
                        "familiar_distractor": foil,
                        "distractor_sample": distractor,
                        "sample_FR": choice(range(3, 9)),
                        "comparison_location": choice(["left", "right"])
                    })
                shuffle(block)
                test_blocks.append(block)
            
            # --- Interleave test trials and training trials in blocks ---
            interleaved = []
            train_block_idx = 0
            test_block_idx = 0
            
            train_pointer = 0
            train_block_size = 10
            
            while test_block_idx < len(test_blocks):
                # Insert 1–3 training trials
                n_train = choice([1, 2])
                for _ in range(n_train):
                    if train_pointer < len(training_trials):
                        interleaved.append(training_trials[train_pointer])
                        train_pointer += 1
            
                # Add one full test trial
                test_trial = test_blocks[test_block_idx].pop(0)
                interleaved.append(test_trial)
            
                # If test block is exhausted, move to next
                if not test_blocks[test_block_idx]:
                    test_block_idx += 1
            
            # Add remaining training trials
            interleaved.extend(training_trials[train_pointer:])
            
            self.stimuli_assignment_dict = {i+1: trial for i, trial in enumerate(interleaved)}
            self.max_trials = len(self.stimuli_assignment_dict)
        
            # Print all trials
            for t, v in self.stimuli_assignment_dict.items():
                if v["trial_type"] == "training":
                    print(f"Trial {t} [TRAINING]: Distractor = {v['distractor_sample']}, Comp = {v['paired_comparison']}, Side = {v['comparison_location']}")
                elif v["trial_type"] == "test":
                    print(f"Trial {t} [TEST]: Distractor = {v['distractor_sample']}, Comp = {v['paired_comparison']}, Foil = {v['familiar_distractor']}, Side = {v['comparison_location']}")
                else:
                    print(f"Trial {t} [UNKNOWN]: {v}")
        
            # Build choice task mapping
            self.choice_stimuli_assignment_dict = {}
            for i in range(1, self.max_trials + 1):
                side = choice(["left", "right"])
                smaller_square = "correct_choice"
                larger_square = "incorrect_choice"
                left_stim = smaller_square if side == "left" else larger_square
                right_stim = larger_square if side == "left" else smaller_square
        
                self.choice_stimuli_assignment_dict[i] = {
                    "smaller_square": smaller_square,
                    "larger_square": larger_square,
                    "left_stimulus": left_stim,
                    "right_stimulus": right_stim,
                }

        elif self.exp_phase_num == 2:
            self.stimuli_assignment_dict = {}
            sample_list = sorted([s for s in self.stimuli_files_list if s.startswith("S")])
            num_repeats = int(self.max_trials / len(sample_list))  # should be 4 if 80 trials
        
            assert self.max_trials % len(sample_list) == 0, "max_trials must be divisible by number of sample stimuli"
        
            trial_num = 1
            for repeat in range(num_repeats):
                shuffled_samples = sample_list.copy()
                shuffle(shuffled_samples)  # reshuffle each round
                for sample in shuffled_samples:
                    comparison = "C" + sample[1:]
                    comparison_num = int(comparison[1:3])
                    comparison_group = "F" if comparison_num <= 10 else "N"
        
                    foil_candidates = [f"C{str(n).zfill(2)}.bmp" for n in range(1, 21) if n != comparison_num]
                    foil = choice(foil_candidates)
                    comparison_location = choice(["left", "right"])
                    sample_FR = choice(range(3, 9))
        
                    self.stimuli_assignment_dict[trial_num] = {
                        "sample": sample,
                        "comparison": comparison,
                        "foil": foil,
                        "comparison_location": comparison_location,
                        "sample_FR": sample_FR,
                        "comparison_group": comparison_group
                    }
                    trial_num += 1
            
            sample_FR = choice(range(3, 9))
               
            for trial_num, trial in self.stimuli_assignment_dict.items():
                print(f"Trial {trial_num}: Sample = {trial['sample']}, Comp = {trial['comparison']} ({trial['comparison_group']}), Foil = {trial['foil']}, Side = {trial['comparison_location']}, FR = {trial['sample_FR']}")

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
                                      text=f"P035d \n Place bird in box, then press space \n Subject: {self.subject_ID} \n Training Phase: {self.exp_phase_name}")
    
    def first_ITI(self, event):
        print("Spacebar pressed -- SESSION STARTED") 
        self.root.unbind("<space>") # bind cursor state to "space" key
        self.clear_canvas()
        self.trial_stage = 0
        self.start_time = datetime.now()  # This is the ACTUAL time the session starts
        if not operant_box_version or self.subject_ID == "TEST": # If test, don't worry about first ITI delay
            self.ITI_duration = 1 * 1000
            self.root.after(1, lambda: self.ITI())
        else:
            self.root.after(30000, lambda: self.ITI())
            
            
        #create the first part of a trial (e.g., sample stimulus presented)
    def sample_phase(self):
        self.clear_canvas()
        self.trial_stage = 1
    
        if operant_box_version and not self.light_HL_on_bool:
            rpi_board.write(house_light_GPIO_num,
                            True) # Turn on the houselight
                
        # Build background (i.e., "background pecks")
        self.mastercanvas.create_rectangle(0, 0,
                                           self.mainscreen_width,
                                           self.mainscreen_height,
                                           fill="black",
                                           outline="black",
                                           tag="bkgrd")
        self.mastercanvas.tag_bind("bkgrd", "<Button-1>",
                                   lambda event, event_type="background_peck": 
                                       self.write_data(event, event_type))
    
        trial_info = self.stimuli_assignment_dict[self.current_trial_counter]
    
        if self.exp_phase_num == 0:
            sample_image_name = trial_info["distractor_sample"]
            stim_path = os_path.join(self.distractor_stimuli_path, sample_image_name)
            self.sample_FR = trial_info.get("sample_FR")
        
        elif self.exp_phase_num == 1:
            # Phase 1 includes training and test trials
            if trial_info["trial_type"] == "training":
                sample_image_name = trial_info["distractor_sample"]
                stim_path = os_path.join(self.distractor_stimuli_path, sample_image_name)
            else:  # test trial
                sample_image_name = trial_info["distractor_sample"]
                stim_path = os_path.join(self.distractor_stimuli_path, sample_image_name)
            self.sample_FR = trial_info.get("sample_FR")
        
        elif self.exp_phase_num == 2:
            sample_image_name = trial_info["sample"]
            stim_path = os_path.join(self.stimuli_folder_path, sample_image_name)
            self.sample_FR = trial_info.get("sample_FR")

    
        # Load and display sample image
        selected_image = Image.open(stim_path)
        self.image = ImageTk.PhotoImage(selected_image)
    
        x, y = 512, 405
        oval_radius = 85
        self.mastercanvas.create_oval(x - oval_radius, y - oval_radius,
                                      x + oval_radius, y + oval_radius,
                                      fill="black", tag="button")
        self.mastercanvas.create_image(x, y, image=self.image, anchor="center", tag="button")
        self.mastercanvas.tag_bind("button", "<Button-1>", self.sample_key_press)

        
###### peck counter (sample)

    def sample_key_press(self, event):
        # This is one half of the RR loop. It can be thought of as the resting
        # "return state" that is dependent upon a key press (on the O key). 
        # Otherwise, it will stay in this state forever.
        self.write_data(event, "sample_key_press")
        self.trial_stage = 1
        self.sample_key_presses += 1 
        if self.sample_key_presses >= int(self.sample_FR):
            self.comparison_phase()
        else:
            self.sample_phase()
        
    #create the choice part of a trial (e.g., comparison stimulus presented)
    def comparison_phase(self):

        self.clear_canvas()
        
        self.trial_stage = 2
        
        # Check if the trial number has changed
        if self.current_trial_counter != self.last_written_trial_num:
            self.comparison_start_time = datetime.now()
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
            
                
        if self.exp_phase_num == 1:
            trial_info_dict = self.stimuli_assignment_dict[self.current_trial_counter]
            trial_type = trial_info_dict.get("trial_type", "train")
            comparison_location = trial_info_dict["comparison_location"]
        
            # Determine correct key based on trial type
            if trial_type == "test":
                comparison_image_name = trial_info_dict["paired_comparison"]
                foil_image_name = trial_info_dict["familiar_distractor"]
            else:  # training trial
                comparison_image_name = trial_info_dict["paired_comparison"]
        
            comparison_image_path = os_path.join(self.stimuli_folder_path, comparison_image_name)
            comparison_image = Image.open(comparison_image_path)
            self.comparison_image = ImageTk.PhotoImage(comparison_image)
            
            if trial_type == "test":
                # Load foil comparison image
                foil_image_name = trial_info_dict["familiar_distractor"]
                foil_image_path = os_path.join(self.stimuli_folder_path, foil_image_name)
                foil_image = Image.open(foil_image_path)
                self.foil_image = ImageTk.PhotoImage(foil_image)
            
                if comparison_location == "left":
                    comparison_x, foil_x = 160, 864
                else:
                    comparison_x, foil_x = 864, 160
                y = 550
            
                self.mastercanvas.create_oval(comparison_x - 85, y - 85, comparison_x + 85, y + 85, fill="black", tag="comparison_button")
                self.mastercanvas.create_image(comparison_x, y, image=self.comparison_image, anchor="center", tag="comparison_button")
                self.mastercanvas.tag_bind("comparison_button", "<Button-1>", self.comp_key_press)

            
                self.mastercanvas.create_oval(foil_x - 85, y - 85, foil_x + 85, y + 85, fill="black", tag="foil_button")
                self.mastercanvas.create_image(foil_x, y, image=self.foil_image, anchor="center", tag="foil_button")
                self.mastercanvas.tag_bind("foil_button", "<Button-1>", self.comp_key_press)
            else:
                # Training trials — only one comparison shown
                if comparison_location == "left":
                    x, y = 160, 550
                else:
                    x, y = 864, 550
            
                self.mastercanvas.create_oval(x - 85, y - 85, x + 85, y + 85, fill="black", tag="button")
                self.mastercanvas.create_image(x, y, image=self.comparison_image, anchor="center", tag="button")
                self.mastercanvas.tag_bind("button", "<Button-1>", self.comp_key_press)
            
            # Keep sample visible during comparison
            sample_image_name = trial_info_dict["distractor_sample"]
            selected_image_path = os_path.join(self.distractor_stimuli_path, sample_image_name)
            selected_image = Image.open(selected_image_path)
            self.image = ImageTk.PhotoImage(selected_image)
            self.mastercanvas.create_oval(512 - 85, 405 - 85, 512 + 85, 405 + 85, fill="black", tag="inactive_sample_key_press")
            self.mastercanvas.create_image(512, 405, image=self.image, anchor="center", tag="inactive_sample_key_press")
            self.mastercanvas.tag_bind("inactive_sample_key_press", "<Button-1>", lambda event, event_type="inactive_sample_key_press": self.write_data(event, event_type))
        
        if self.exp_phase_num == 2: # For experimental trials
        

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
            
            x,y = 512, 405
            
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
            
            
        elif self.exp_phase_num == 0:
            
            self.comparison_start_time = datetime.now()
            
            self.trial_stage = 1
        
            trial_info = self.stimuli_assignment_dict[self.current_trial_counter]
            sample_image_name = trial_info["distractor_sample"]
            comparison_image_name = trial_info["paired_comparison"]
            comparison_location = trial_info["comparison_location"]  # NEW: get side assignment
            
            # Load sample (top-center)
            sample_path = os_path.join(self.distractor_stimuli_path, sample_image_name)
            sample_image = Image.open(sample_path)
            self.sample_image = ImageTk.PhotoImage(sample_image)
            self.mastercanvas.create_oval(512 - 85, 405 - 85, 512 + 85, 405 + 85, fill="black", tag="sample")
            self.mastercanvas.create_image(512, 405, image=self.sample_image, anchor="center", tag="sample")
            
            # Determine coordinates based on comparison_location
            if comparison_location == "left":
                comp_x, comp_y = 160, 550
            else:
                comp_x, comp_y = 864, 550
            
            # Load and display comparison stimulus on assigned side
            comparison_path = os_path.join(self.stimuli_folder_path, comparison_image_name)
            comparison_image = Image.open(comparison_path)
            self.image = ImageTk.PhotoImage(comparison_image)
            self.mastercanvas.create_oval(comp_x - 85, comp_y - 85, comp_x + 85, comp_y + 85, fill="black", tag="button")
            self.mastercanvas.create_image(comp_x, comp_y, image=self.image, anchor="center", tag="button")
            self.mastercanvas.tag_bind("button", "<Button-1>", self.comp_key_press)
    
    #create the choice task 
    
    def choice_task(self):
    
            self.clear_canvas()
            self.trial_stage = 3
    
            # Build background (i.e., "background pecks")
            self.mastercanvas.create_rectangle(0, 0, self.mainscreen_width, 
                                               self.mainscreen_height,
                                               fill="black", 
                                               outline="black", 
                                               tag="bkgrd")
            self.mastercanvas.tag_bind("bkgrd", "<Button-1>",
                                       lambda event, 
                                       event_type="background_peck": 
                                           self.write_data(event, event_type))
    
            # Retrieve the stimuli for the current trial from the choice_stimuli_dict
            choice_trial_info_dict = self.choice_stimuli_assignment_dict.get(self.current_trial_counter)
            
            # Extract the stimuli and their positions
            smaller_square = choice_trial_info_dict.get("smaller_square")
            larger_square = choice_trial_info_dict.get("larger_square")
            left_stimulus = choice_trial_info_dict.get("left_stimulus")
            right_stimulus = choice_trial_info_dict.get("right_stimulus")
    
            # Check if all necessary stimuli are present
            if not all([smaller_square, larger_square, left_stimulus, right_stimulus]):
                print("ERROR: Missing stimuli information in the dictionary entry.")
                self.exit_program(None)
                return
    
            # Define coordinates for left and right positions
            left_x, left_y = 160, 550
            right_x, right_y = 864, 550
            
            # Define the size of the circles based on their labels
            # Define size of the squares
            small_size = 100  # white square
            large_size = 170  # black background
            
            if left_stimulus == smaller_square:
                # Left: smaller white square on black background
                self.mastercanvas.create_rectangle(left_x - large_size//2, left_y - large_size//2,
                                                   left_x + large_size//2, left_y + large_size//2,
                                                   fill="black", tag="left_button_bg")
                self.mastercanvas.create_rectangle(left_x - small_size//2, left_y - small_size//2,
                                                   left_x + small_size//2, left_y + small_size//2,
                                                   fill="white", tag="left_button")
            
                # Right: larger white square only
                self.mastercanvas.create_rectangle(right_x - large_size//2, right_y - large_size//2,
                                                   right_x + large_size//2, right_y + large_size//2,
                                                   fill="white", tag="right_button")
            else:
                # Left: larger white square only
                self.mastercanvas.create_rectangle(left_x - large_size//2, left_y - large_size//2,
                                                   left_x + large_size//2, left_y + large_size//2,
                                                   fill="white", tag="left_button")
            
                # Right: smaller white square on black background
                self.mastercanvas.create_rectangle(right_x - large_size//2, right_y - large_size//2,
                                                   right_x + large_size//2, right_y + large_size//2,
                                                   fill="black", tag="right_button_bg")
                self.mastercanvas.create_rectangle(right_x - small_size//2, right_y - small_size//2,
                                                   right_x + small_size//2, right_y + small_size//2,
                                                   fill="white", tag="right_button")
            

  # Bind the black background circle and the white circle to the correct/incorrect choice
            if left_stimulus == smaller_square:
                self.mastercanvas.tag_bind("left_button_bg", "<Button-1>", 
                                           self.correct_choice)
                self.mastercanvas.tag_bind("left_button", "<Button-1>", 
                                           self.correct_choice)
                self.mastercanvas.tag_bind("right_button", "<Button-1>", 
                                           self.incorrect_choice)
            else:
              self.mastercanvas.tag_bind("left_button", "<Button-1>", 
                                         self.incorrect_choice)
              self.mastercanvas.tag_bind("right_button_bg", 
                                         "<Button-1>", self.correct_choice)
              self.mastercanvas.tag_bind("right_button", 
                                         "<Button-1>", self.correct_choice)

###### peck counter (comparison)

    def comp_key_press(self, event):
        clicked_widget = self.mastercanvas.gettags("current")[0]  # "comparison_button" or "foil_button"     
        if clicked_widget == "comparison_button":
            self.write_data(event, "comparison_key_press")
        elif clicked_widget == "foil_button":
            self.write_data(event, "foil_key_press")
        else:
            self.write_data(event, "comparison_key_press")
        
        self.trial_stage = 2
        self.comparison_key_presses += 1 
        
        if self.comparison_key_presses >= self.comparison_FR:
            self.clear_canvas()
            self.root.after(1000, self.choice_task)
        else:
            self.comparison_phase()



    # correct choice
    
    def correct_choice(self, event):
        # This is one half of the RR loop. It can be thought of as the resting
        # "return state" that is dependent upon a key press (on the O key). 
        # Otherwise, it will stay in this state forever.
        self.trial_stage = 3
        self.write_data(event, "correct_choice"),
        self.correct_comparison_key_presses += 1 
        if self.exp_phase_num in [0, 1]:
            self.reinforcement_phase()
        else:
            if self.correct_comparison_key_presses >= self.comparison_FR:
                self.reinforcement_phase()
            else:
                self.comparison_phase()
                
             
       
    #incorrect choice
    def incorrect_choice(self, event):
        # This is one half of the RR loop. It can be thought of as the resting
        # "return state" that is dependent upon a key press (on the O key). 
        # Otherwise, it will stay in this state forever.
        self.trial_stage = 3
        self.write_data(event, "incorrect_choice")
        self.incorrect_comparison_key_presses += 1 
        if self.exp_phase_num in [0, 1]:
            self.ITI()
        else:
            if self.incorrect_comparison_key_presses >= self.comparison_FR:
                self.ITI()
            else:
                self.comparison_phase()
            
#######
            
    #Reinforcement!
    def reinforcement_phase(self):
        self.trial_stage = 3
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
        self.trial_stage = 0
        
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
        
        # Check if current trial counter exists in stimuli_assignment_dict
        if self.current_trial_counter != 0 and self.current_trial_counter not in self.stimuli_assignment_dict:
            self.exit_program("event")
            return
        
        # First, check to see if any session limits have been reached (e.g.,
        # if the max time or reinforcers earned limits are reached).
        if self.current_trial_counter  == self.max_trials + 1:
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
        if self.current_trial_counter != 0 and self.current_trial_counter not in self.stimuli_assignment_dict:
            self.exit_program("event")
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
       #print(type(self.stimuli_assignment_dict[self.current_trial_counter]))
       #print(self.stimuli_assignment_dict[self.current_trial_counter])
        if self.exp_phase_num == 2:
            if self.current_trial_counter not in self.stimuli_assignment_dict:
                trial_info = self.stimuli_assignment_dict[self.current_trial_counter - 1]
            else:
                trial_info = self.stimuli_assignment_dict[self.current_trial_counter]
            self.sample_name = trial_info['sample']
            self.comparison_name = trial_info['comparison']
            self.foil_name = trial_info['foil']
            self.comparison_location = trial_info['comparison_location']
            self.group_name = trial_info.get('comparison_group', 'NA')
        #build background (i.e., "background pecks)
        # Also write data
        self.write_comp_data(False) # update data .csv with trial data from the previous trial
        # Timer
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
        # Skip writing data if current_trial_counter is 0 (which would make the dictionary access invalid)
        if self.current_trial_counter == 0:
            return
    
        # Event coordinates
        if event is not None: 
            x, y = event.x, event.y
        else:  # There are certain data events that are not pecks.
            x, y = "NA", "NA"
    
        print(f"{outcome:>30} | x: {x: ^3} y: {y:^3} | {self.trial_stage:^5} | {str(datetime.now() - self.start_time)}")
    
        # Initialize comparison_group and foil_group
        comparison_group = "NA"
        foil_group = "NA"
        LComp = "NA"
        RComp = "NA"
        CompStimulus = "NA"
        stimulus_file = "NA"
        foil_group = "NA"
        trial_info_dict = self.stimuli_assignment_dict.get(self.current_trial_counter, {})
        trial_type = trial_info_dict.get("trial_type", "NA")

    # Phase 0 (familiarization and choice task)
        if self.exp_phase_num == 0:
            trial_info_dict = self.stimuli_assignment_dict.get(self.current_trial_counter, {})
            stimulus_file = trial_info_dict.get("paired_comparison", "NA")
            CompStimulus = stimulus_file
            LComp = "NA"
            RComp = "NA"
            self.sample_name = trial_info_dict.get("distractor_sample", "NA")  # update here
            comparison_group = "F"  # All comparisons in Phase 0 are familiarized

            choice_trial_info = self.choice_stimuli_assignment_dict.get(self.current_trial_counter, {})
            left_stimulus = choice_trial_info.get("left_stimulus", "NA")
            right_stimulus = choice_trial_info.get("right_stimulus", "NA")
    
            # Assign LComp and RComp based on which stimulus is presented on each side
            # Assign LComp and RComp directly as "smaller_circle" or "larger_circle"
            LComp = "smaller_square" if left_stimulus == "correct_choice" else "larger_square"
            RComp = "smaller_square" if right_stimulus == "correct_choice" else "larger_square"
            
            choice_trial_info = self.choice_stimuli_assignment_dict.get(self.current_trial_counter, {})
            left_stimulus = choice_trial_info.get("left_stimulus", "NA")
            right_stimulus = choice_trial_info.get("right_stimulus", "NA")
            
            LComp = "smaller_square" if left_stimulus == "correct_choice" else "larger_square"
            RComp = "smaller_square" if right_stimulus == "correct_choice" else "larger_square"
            
            small_loc = "left" if left_stimulus == "correct_choice" else "right"
            large_loc = "right" if small_loc == "left" else "left"

            
        # Phase 1 (association test)
        if self.exp_phase_num == 1:
            stimulus_file = trial_info_dict.get("paired_comparison", "NA")
            CompStimulus = stimulus_file
            self.sample_name = trial_info_dict.get("distractor_sample", "NA")
            self.sample_FR = trial_info_dict.get("sample_FR", "NA")
            trial_type = trial_info_dict.get("trial_type", "training")  # "test" or "training"
            comparison_location = trial_info_dict.get("comparison_location", "NA")
        
            if trial_type == "test":
                foil_file = trial_info_dict.get("familiar_distractor", "NA")
            else:
                foil_file = "NA"
        
            if comparison_location == "left":
                LComp = CompStimulus
                RComp = foil_file
            elif comparison_location == "right":
                RComp = CompStimulus
                LComp = foil_file
            else:
                LComp, RComp = "NA", "NA"
        
            try:
                comp_num = int(stimulus_file[1:3])
                comparison_group = "F" if comp_num <= 10 else "N"
            except:
                comparison_group = "NA"
                
            # Rename outcome for cleaner data labels
            if outcome == "comparison_key_press":
                outcome = "comparison_choice"
            elif outcome == "foil_key_press":
                outcome = "foil_choice"

            choice_trial_info = self.choice_stimuli_assignment_dict.get(self.current_trial_counter, {})
            left_stimulus = choice_trial_info.get("left_stimulus", "NA")
            right_stimulus = choice_trial_info.get("right_stimulus", "NA")
            
            small_loc = "left" if left_stimulus == "correct_choice" else "right"
            large_loc = "right" if small_loc == "left" else "left"
            
            # Determine foil familiarity
            try:
                foil_num = int(foil_file[1:3])
                foil_group = "F" if foil_num <= 10 else "N"
            except:
                foil_group = "NA"

        # Phase 2 logic (sample, comparison, and foil)
        if self.exp_phase_num == 2:
            trial_info_dict = self.stimuli_assignment_dict.get(self.current_trial_counter, {})
            
            stimulus_file = trial_info_dict.get("comparison", "NA")
            CompStimulus = stimulus_file
        
            # Determine side assignments
            if trial_info_dict.get("comparison_location") == "left":
                LComp = CompStimulus
                RComp = trial_info_dict.get("foil", "NA")
            else:
                LComp = trial_info_dict.get("foil", "NA")
                RComp = CompStimulus
        
            # Determine comparison familiarity
            try:
                comp_num = int(stimulus_file[1:3])
                comparison_group = "F" if comp_num <= 10 else "N"
            except:
                comparison_group = "NA"
                
            foil_file = trial_info_dict.get("foil", "NA")

            # Determine foil familiarity
            try:
                foil_num = int(foil_file[1:3])
                foil_group = "F" if foil_num <= 10 else "N"
            except:
                foil_group = "NA"

            
            small_loc = "NA"
            large_loc = "NA"
            
            trial_type = "Training"
    
        # Safely calculate trial time
        trial_time = "NA"
        if self.trial_start is not None:
            trial_time = round((time() - self.trial_start - (self.ITI_duration / 1000)), 5)
    
        # Append peck data to data frame...
        self.session_data_frame.append([
            str(datetime.now() - self.start_time),
            self.exp_phase,
            self.subject_ID,
            x,
            y, 
            outcome,
            self.trial_stage,
            self.sample_name,
            stimulus_file,
            LComp,
            RComp,
            CompStimulus,
            trial_type,
            small_loc,
            large_loc,
            trial_time,
            self.current_trial_counter, 
            self.reinforced_trial_counter,
            self.sample_FR,
            comparison_group,
            foil_group,
            date.today()
        ])

    header_list = [
        "SessionTime", "ExpPhase", "Subject", "Xcord", "Ycord", "Event",
        "TrialSubStage", "SampleStimulus", "CompStimulus", "LComp", "RComp", 
        "CorrectKey", "TrialType", "SmallCircleLoc", "LargeCircleLoc", 
        "TrialTime", "TrialNum", "ReinTrialNum", "SampleFR", 
        "ComparisonFamiliarity", "FoilFamiliarity", "Date"]

        
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
            myFile_loc = f"{self.data_folder_directory}/{self.subject_ID}/{self.subject_ID}_{self.start_time.strftime('%Y-%m-%d_%H.%M.%S')}_P035d_data-Phase{self.exp_phase_num}.csv" # location of written .csv
            
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
