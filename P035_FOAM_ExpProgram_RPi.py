#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Tue Jan 17 13:35:04 2023

@author: cyruskirkman

Last updated: 2024-01-09 CK


This is the main code for Kayley Ozimac's first-year 'FOAM' project
    
    1) Mixed instrumental/autoshaping: one of the three stimuli were filled in
        at the beginning of each trial. After a peck on the filled stimulus (FR1),
        a reinforcer was immediately provided. If no response was made within 
        10 s, a reinforcer was immediately provided. Fill colors were either blue
        or yellow, save for six trials for the first two sessions that were grey.
        
    2) Match to sample: The next phase was a simple MTS task in which a sample
        stimulus was presented in the top-middle sample slot. After several pecks
        (RR8 with bounds from 6 to 10, but this was built to be maniputable),
        two comparisons were presented at left and right of the sample (with
        the sample still visible). One of these comparisons was always linked
        with that specific sample (deemed the "correct comparison") and the 
        other sample was non-linked with that sample, but instead was the 
        linked pair of a seperate sample stimulus (deemed an "incorrect
        choice" or foil). During this match to sample interval, a single s
        peck to the correct comparison was reinforced with 3-s access to the
        food hopper, while a peck to the foil was punished with an absence of
        reinforcer and directly to the ITI. After the selection of a comparison
        key, the screen went black until the reinforcement (if relevant) and/or
        ITI period completed and the next trial occured with a different sample.
        
Updated to run 1024 x 768p on 2023-09-09 with RPi system. Note the difference
in spatial data (e.g., x & y coordinates) after this time.

"""
# Prior to running any code, its conventional to first import relevant 
# libraries for the entire script. These can range from python libraries (sys)
# or sublibraries (setrecursionlimit) that are downloaded to every computer
# along with python, or other files within this folder (like control_panel or 
# maestro).
from tkinter import Toplevel, Canvas, BOTH, TclError, Tk, Label, Button, \
    StringVar, OptionMenu, IntVar, Radiobutton, Entry, Checkbutton, Variable
from datetime import datetime, timedelta, date
from time import time, sleep
from csv import writer, DictReader, DictWriter, QUOTE_MINIMAL
from os import getcwd, popen, mkdir, listdir, path as os_path
from random import choice, randint, shuffle
from PIL import ImageTk, Image  
from sys import setrecursionlimit, path as sys_path

# The first variable declared is whether the program is the operant box version
# for pigeons, or the test version for humans to view. The variable below is 
# a T/F boolean that will be referenced many times throughout the program 
# when the two options differ (for example, when the Hopper is accessed or
# for onscreen text, etc.). It is changed automatically based on whether
# the program is running in operant boxes (True) or not (False). It is
# automatically set to True if the user is "blaisdelllab" (e.g., running
# on a rapberry pi) or False if not. The output of os_path.expanduser('~')
# should be "/home/blaisdelllab" on the RPis

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
# the session will terminate. The purpose of the control panel is to input 
# relevant information (like pigeon name) and select any variations to occur 
# within the upcoming session (sub/phase, FR, etc.)
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
        self.control_window.title("P035 Control Panel")
        ##  Next, setup variables within the control panel:
        # Subject ID list (need to build/alphabetize)
        self.pigeon_name_list = ["Bowser", "Yoshi", "Shy Guy", "Athena",
                                 "Darwin","Cousteau", "Bon Jovi"]
        self.pigeon_name_list.sort() # This alphabetizes the list
        self.pigeon_name_list.insert(0, "TEST")
        # Subject ID menu and label
        Label(self.control_window, text="Pigeon Name:").pack()
        self.subject_ID_variable = StringVar(self.control_window)
        self.subject_ID_variable.set("Select")
        self.subject_ID_menu = OptionMenu(self.control_window,
                                          self.subject_ID_variable,
                                          *self.pigeon_name_list,
                                          command=self.set_pigeon_ID).pack()
        
        # Training phases
        Label(self.control_window, text = "Select experimental phase:").pack()
        self.training_phase_variable = StringVar() # This is the literal text of the phase, e.g., "0: Autoshaping"
        self.training_phase_variable.set("Select") # Default
        self.training_phase_name_list = ["0: Autoshaping",
                                    "1: Three Pairs",
                                    "2: Six Pairs",
                                    "3: Twelve Pairs",
                                    "4: Twenty-four Pairs",
                                    "5: Forty-Eight Pairs",
                                    "6: Ninety-Six Pairs",
                                    "7: 192 Pairs"
                                    ]
        self.training_phase_menu = OptionMenu(self.control_window,
                                          self.training_phase_variable,
                                          *self.training_phase_name_list)
        self.training_phase_menu.pack()
        self.training_phase_menu.config(width = 20)
        # If we want, we can set it to a specific training phase
        self.training_phase_variable.set("1: Three Pairs") # Default set to first training phase
        
        # Training subphases (nearly identical to phases above)
        Label(self.control_window, text = "Select subphase:").pack()
        self.training_subphase_variable = StringVar()
        self.training_subphase_variable.set("Select")
        self.training_subphase_name_list = ["i: Training",
                                         "ii: CBE.1",
                                         "iii: FM.1",
                                         "iv: CBE.2",
                                         "v: FM.2",
                                         "vi: CBE.3",
                                         "vii: FM.3"
                                    ]
        self.training_subphase_menu = OptionMenu(self.control_window,
                                          self.training_subphase_variable,
                                          *self.training_subphase_name_list)
        self.training_subphase_menu.pack()
        self.training_subphase_menu.config(width = 20)
        self.training_subphase_variable.set("i: Training") # Default set to first training phase
        
        # Sample key FR selection. This is default "NA" (resulting in the normal
        # RR8), but can be varied to a static FR if needed for training purposes.
        # If it is a non-numerical value, it will not he ahle to run.
        Label(self.control_window,
              text = "Manual Sample FR:").pack()
        self.manual_FR_stringvar = StringVar()
        self.manual_FR_variable = Entry(self.control_window, 
                                     textvariable = self.manual_FR_stringvar).pack()
        self.manual_FR_stringvar.set("NA")
        
        # Forced choice option-- checkbutton
        self.forced_choice_variable = IntVar()
        self.forced_choice_check_button = Checkbutton(self.control_window,
                                                      variable = self.forced_choice_variable,
                                                      text = "Forced Choice Session",
                                                      onvalue = True, 
                                                      offvalue = False).pack()
        self.forced_choice_variable.set(False) # Default set to False
        
        # New stimuli only-- checkbutton
        self.new_stimuli_only_variable = IntVar()
        self.new_stimuli_only_button = Checkbutton(self.control_window,
                                                      variable = self.new_stimuli_only_variable,
                                                      text = "New Stimuli Only",
                                                      onvalue = True, 
                                                      offvalue = False).pack()
        self.new_stimuli_only_variable.set(False) # Default set to False
        
        # New/old procedure? Y/N binary radio button
        Label(self.control_window,
              text = "New/Old Procedure?").pack()
        self.new_old_variable = StringVar()
        self.new_old_button1 =  Radiobutton(self.control_window,
                                    variable = self.new_old_variable,
                                    text = "NA",
                                    value = "NA").pack()
        self.new_old_button2 = Radiobutton(self.control_window,
                                  variable = self.new_old_variable,
                                  text = "New",
                                  value = "New").pack()
        self.new_old_button3 = Radiobutton(self.control_window,
                                  variable = self.new_old_variable,
                                  text = "Old",
                                  value = "Old").pack()
        self.new_old_variable.set("NA") # Default set to NA
        
        # Record data variable? Y/N binary radio button
        Label(self.control_window,
              text = "Record data in seperate data sheet?").pack()
        self.record_data_variable = IntVar()
        self.record_data_rad_button1 =  Radiobutton(self.control_window,
                                   variable = self.record_data_variable,
                                   text = "Yes",
                                   value = True).pack()
        self.record_data_rad_button2 = Radiobutton(self.control_window,
                                  variable = self.record_data_variable,
                                  text = "No",
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
        # important inputs from the control panel. Importantly, it won't
        # run unless all the informative fields are filled in.
        if not sum([self.new_old_variable.get() != "NA", self.forced_choice_variable.get() == 1, self.new_stimuli_only_variable.get()]) > 1:
            if not (self.new_old_variable.get() != "NA" and int(self.training_phase_variable.get()[0]) in [0,1]):
                if not (self.forced_choice_variable.get() and self.new_stimuli_only_variable.get()):
                    if self.subject_ID_variable.get() in self.pigeon_name_list:
                        if self.training_phase_variable.get() in self.training_phase_name_list and self.training_subphase_variable.get() in  self.training_subphase_name_list:
                            # If a forced choice session, it must be for training subphases 
                            # only (and not autoshaping)
                            if (self.forced_choice_variable.get() == 0) or (self.training_subphase_variable.get() == "i: Training" and self.training_phase_variable.get() != "0: Autoshaping") and not (self.new_stimuli_only_variable.get() and self.training_subphase_variable.get() > 0):
                                list_of_variables_to_pass = [self.subject_ID_variable.get(),
                                                             self.record_data_variable.get(), # Boolean for recording data (or not)
                                                             self.data_folder_directory, # directory for data folder
                                                             self.training_phase_variable.get(), # Which training phase
                                                             self.training_phase_name_list, # list of training phases
                                                             self.training_subphase_variable.get(), # Training subphase variable
                                                             self.training_subphase_name_list,
                                                             self.manual_FR_stringvar.get(), # Manual FR
                                                             self.forced_choice_variable.get(), # Forced choice Boolean,
                                                             self.new_stimuli_only_variable.get(), # New stimuli only Boolean
                                                             self.new_old_variable.get() # Designate new/old contingency
                                                             ]
                                # If not forced choice (default)...
                                if not self.forced_choice_variable.get():
                                    print("Operant Box Screen Built") 
                                    list_of_variables_to_pass.append([]) # Add an empty list at the end for forced choice trials
                                    self.MS = MainScreen(*list_of_variables_to_pass)
                                # ...if forced choice
                                else:
                                    self.FPO = ForcedChoiceOptionWindow(self.training_phase_name_list.index(self.training_phase_variable.get()),
                                                                        list_of_variables_to_pass)
                            else:
                                print("\nERROR: Cannot Run Forced Choice/Only New for Non-Training or Autoshaping Sessions")
                        else:
                            print("\nERROR: Input Experimental Phase Before Starting Session")
                    else:
                        print("\nERROR: Input Correct Pigeon ID Before Starting Session")
                else:
                    print("\nERROR: Cannot run 'forced choice' and 'all new' at once")
            else:
                print("\nERROR: Cannot run 'new/old' procedure on training phase 1; there's no old!")
        else:
            print("\nERROR: Cannot run new/old procedure, forced choice session, or new stimuli only procedures together!")
            
    
# This window is generated for forced choice sessions and will 
class ForcedChoiceOptionWindow (object):
    # The init function declares the inherent variables within that object
    # (meaning that they don't require any input).
    def __init__(self, training_phase, list_of_info_to_be_passsed):
        # Make the passed variables global within the class:
        self.list_of_info_to_be_passsed = list_of_info_to_be_passsed
        stimuli_folder_path = "stimuli/"
        
        # This is a list of each picture file's directory
        stimuli_files_list = listdir(stimuli_folder_path)
        list_of_stimuli = []
            
        for i in stimuli_files_list:
            # Make sure all files are .bmp images...
            if i.split(".")[1] == "bmp":
                # Next, add the file to the list if it is within the
                # following phase (may be removed later)
                # Then, check if we need it for this specific training phase.
                img_phase_integer = int(i.split(".")[0][-1])
                if (img_phase_integer <= training_phase):
                    # Check if a sample... S10_Phase3.bmp
                    if i[0] == "S":
                        list_of_stimuli.append(i)
                    
        # Then sort our compiled list by pair number
        list_of_stimuli = (sorted(list_of_stimuli,
                                  key = lambda x: int(x.split("_")[0][1:])))
        
        # Then create a dictionary of values for the on/off checkboxes. Default
        # set to zero
        self.dict_of_stimuli_vals = {}
        for i in list_of_stimuli:
            self.dict_of_stimuli_vals[i] = 0

        # setup the root Tkinter window
        self.FC_window = Toplevel()
        self.FC_window.title("P035 Forced Choice Stimuli Checklist")
        
        r = 1 # Row counter
        c = 0 # Column counter
        for x in self.dict_of_stimuli_vals:
            # The window would be too tall if we only append using the .pack()
            # funciton, so instead we need to split up the entries into various
            # columns of height 12
            if r > 12:
                c += 1
                r = 1
            # Set each dictionary entry to be equal to a variable (TBD)
            self.dict_of_stimuli_vals[x] = Variable()
            # Then create the checkbutton
            l = Checkbutton(self.FC_window,
                        text = x,
                        variable = self.dict_of_stimuli_vals[x])
            # Set the value of that box to zero (not 'null')
            l.deselect()
            # Place the checkbox into the wondow
            l.grid(row = r,
                   column = c)
            # Lastly, increase row num for next stimulus
            r += 1 
        
        # Write label, once we have the number of columns...
        Label(self.FC_window,
              text = "Select forced choice stimulus (or stimuli):").grid(row = 0,
                                                                         column = c // 2)
            
        # Start button
        Button(self.FC_window,
               text = 'Start program',
               bg = "green2",
               command = self.build_chamber_screen).grid(row = 13 if (c > 0) else r + 1,
                                                         column = c // 2)
        
        # Loop to make sure things are looping...
        self.FC_window.mainloop()
        
    def build_chamber_screen(self):
        # Once the stimuli are selected and the start button is pressed, the 
        # selected checkbuttons will be appended to a list that is then
        # sent to the mainscreen level
        selected_FC_stimuli = []
        for i in self.dict_of_stimuli_vals:
            # If selected...
            if int(self.dict_of_stimuli_vals[i].get()) == 1:
                selected_FC_stimuli.append(i)
        self.list_of_info_to_be_passsed.append(selected_FC_stimuli)
        # Then we can start the session and create the main screen
        self.MS = MainScreen(*self.list_of_info_to_be_passsed)
        # Finally we can quit the current window
        self.FC_window.destroy()
        


# Next, setup the MainScreen object
class MainScreen(object):
    # We need to declare several functions that are 
    # called within the initial __init__() function that is 
    # run when the object is first built:
    
    def __init__(self, subject_ID, record_data, data_folder_directory,
                 training_phase, training_phase_name_list, training_subphase,
                 training_subphase_name_list, manual_FR, forced_choice_session,
                 all_new_simuli_var, new_old_var, forced_choice_stim_list):
        ## Firstly, we need to set up all the variables passed from within
        # the control panel object to this MainScreen object. We do this 
        # by setting each argument as "self." objects to make them global
        # within this object.
        
        # Setup training phase and subphase
        self.training_phase = training_phase_name_list.index(training_phase) # Starts at 0 **
        self.training_phase_name_list = training_phase_name_list
        
        self.training_subphase = training_subphase_name_list.index(training_subphase) # Also starts at 0 **
        self.training_subphase_name_list = training_subphase_name_list
        
        # Setup data directory
        self.data_folder_directory = data_folder_directory
        
        ## Set the other pertanent variables given in the command window
        self.subject_ID = subject_ID
        self.record_data = record_data
        if manual_FR != "NA":
            try:
                self.manual_FR = int(manual_FR) # Number of times the oberving key should be pressed for the target to appear 
            except ValueError:
                print("\nERROR: Incorrect Manual FR Input")
        else:
            self.manual_FR = manual_FR
        # Including forced choice variables
        self.forced_choice_session = forced_choice_session
        self.forced_choice_stim_list = forced_choice_stim_list
        self.all_new_simuli_var = all_new_simuli_var
        self.new_old_var = new_old_var
        
        ## Set up the visual Canvas
        self.root = Toplevel()
        self.root.title("P035: FOAM - " + self.training_phase_name_list[self.training_phase][3:]) # this is the title of the windows
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
            # Then fullscreen (on a 768x1024p screen). Note that this assumes 
            # both monitors have identical sizes & the operant box is to the
            # "left" of the control panel.
            self.root.geometry(f"{self.mainscreen_width}x{self.mainscreen_height}+1920+0")
            self.root.attributes('-fullscreen',
                                 True)
            self.mastercanvas = Canvas(self.root,
                                   bg="black")
            self.mastercanvas.pack(fill = BOTH,
                                   expand = True)
        # If we want to run a "human-friendly" version
        else: 
            # No keybinds and  800x600p fixed window
            self.mastercanvas = Canvas(self.root,
                                   bg="black",
                                   height=self.mainscreen_height,
                                   width = self.mainscreen_width)
            self.mastercanvas.pack()
        
        # Timing variables
        self.auto_reinforcer_timer = 10 * 1000 # Time (ms) before reinforcement for AS
        self.start_time = None # This will be reset once the session actually starts
        self.trial_start = None # Duration into each trial as a second count, resets each trial
        self.trial_FR = None # FR of a trial
        self.session_duration = datetime.now() + timedelta(minutes = 90) # Max session time is 90 min
        self.ITI_duration = 15 * 1000 # duration of inter-trial interval (ms)
        if self.subject_ID in ["Shy Guy", "Athena", "Bon Jovi", "Darwin"]:
            self.hopper_duration = 3500 # duration of accessible hopper(ms)
        elif self.subject_ID == "TEST":
            self.hopper_duration = 2000 # duration of accessible hopper(ms)
        elif self.subject_ID in ["Cousteau", "Yoshi"]:
            self.hopper_duration = 3500 # duration of accessible hopper(ms)
        else:
            self.hopper_duration = 6 * 1000 # duration of accessible hopper(ms)
        self.FI_duration = 1 # 1ms FI timer
        self.FI_complete = True
        self.current_trial_counter = 0 # counter for current trial in session
        self.trial_stage = "NA"
        self.reinforced_trial_counter = 0 # number of trials where a reinforcer was provided
        # Max number of trials within a session differ by phase
        if self.training_phase == 0: # Autoshaping only has 90
            self.max_number_of_reinforced_trials = 90
        else: # All others are 96 (divisible by 16)
            self.max_number_of_reinforced_trials = 96 # default
        # Number of probe trials during CBE or FM subphases should be a variable
        self.probe_trials_per_session = 4
        
        # Here are variables for data structuring 
        self.session_data_frame = [] #This where trial-by-trial data is stored
        header_list = ["SessionTime", "Xcord","Ycord", "Event",
                       "SampleStimulus", "LComp", "RComp", "CorrectKey", "PairNum",
                       "TrialSubStage", "TrialTime", "TrialNum", "ReinTrialNum",
                       "SampleFR", "FI", "TrialType", "Subject", "TrainingPhase",
                       "TrainingSubPhase", "ForcedChoiceSession", "AllNewStimuli",
                       "NewOldStimuliSession", "Date"] # Column headers
        self.session_data_frame.append(header_list) # First row of matrix is the column headers
        self.date = date.today().strftime("%y-%m-%d") # Today's date

        ## Finally, start the recursive loop that runs the program:
        self.place_birds_in_box()

    def place_birds_in_box(self):
        # This is the default screen run until the birds are placed into the
        # box and the space bar is pressed. It then proceedes to the ITI. It only
        # runs in the operant box version. After the space bar is pressed, the
        # "first_ITI" function is called for the only time prior to the first trial
        
        def first_ITI(event):
            # Is initial delay before first trial starts. It first deletes all the
            # objects off the mnainscreen (making it blank), unbinds the spacebar to 
            # the first_ITI link, followed by a 30s pause before the first trial to 
            # let birds settle in and acclimate.
            print("Spacebar pressed -- SESSION STARTED") 
            self.mastercanvas.delete("all")
            self.root.unbind("<space>")
            self.start_time = datetime.now() # Set start time
            self.current_key_stimulus_dict = {"left_comparison_key": "black",
                                           "right_comparison_key": "black",
                                           "sample_key": "black"}
            
            # Set up the stimulus dictionary first and foremost. This will
            # be a long process, starting by setting the directory to the 
            # folder with all the stimuli
            stimuli_folder_path = "stimuli/"
            
            # This is a list of each picture file's directory
            stimuli_files_list = listdir(stimuli_folder_path)

            # Next, let's set up a list of any probe trial stimuli that will be needed!
            probe_stim_list = []
            
            # Our first for list will pick out all the probe trial stimuli for
            # any training subphases (e.g., CBE and FM)
            if self.training_subphase > 0:
                for i in stimuli_files_list:
                    # First, make sure file is an image (.bmp file)
                    if i.split(".")[1] == "bmp":
                        # Next, add the file to the list if it is within the
                        # following phase (may be removed later)
                         img_phase_integer = int(i.split(".")[0][-1])
                         if (self.training_phase + 1 == img_phase_integer):
                             probe_stim_list.append(i)
                        
            # Once we have all the potential stimuli for probe trials picked out,
            # we need to only pick either the first set of three pairs (S1, C1, 
            # S2, C2, S3, C3) for CBE.1 and FM.1 OR the fourth through sixth pairs 
            # S4, C4, S5, C5, S6, C6) for CBE.2
            # by sorting the list by the stimulus number.
            # Ex. From 'S10_Phase3.bmp' we extract '10'
            probe_stim_list = (sorted(probe_stim_list,
                                      key = lambda x: int(x.split("_")[0][1:])))
            if self.training_subphase in [1,2]:
                probe_stim_list = probe_stim_list[:2]
            elif self.training_subphase in [3,4]:
                probe_stim_list = probe_stim_list[2:4]
            elif self.training_subphase in [5,6]:
                probe_stim_list = probe_stim_list[4:6]
                
            # After we select the correct probe pair for test subphases, we 
            # need to select the fast-mapping FOIL stimulus for the FM phases 
            # 2, 4, and 6. These stimuli will be unique to each FM session and
            # never reused across FM phases. Therefore, we need a .csv doc to 
            # track which stimuli have been used before.
            FM_probe_FOIL_stimulus = "NA"
            if self.training_subphase in [2,4,6]:
                # Set up the directory for the csv.
                FM_stimuli_log_directory = "FM_stimuli_logs/"
                # Finalize the directory:
                FM_stimuli_log_directory += f"{self.subject_ID}_P035_Used_FM_Stimuli_Log.csv"
                
                # Next, check if the csv file already exists (e.g., the subject
                # has been run under a FM test before). We do this by setting 
                # up a list of previous entries and then seeing if the file 
                # exists. If it does, we add entries to it (e.g., rows of the
                # .csv file). If it doesn't exist, it remains empty.
                FM_log_list = []
                if os_path.isfile(FM_stimuli_log_directory):
                    # Read the content of the csv as a dictionary
                    with open(FM_stimuli_log_directory, 'r', encoding='utf-8-sig') as data:
                        for line in DictReader(data):
                            FM_log_list.append(line)
                # If the log doesn't exist, we can assume the subject has never 
                # run a FM session before this point (so we'll need to write
                # a new .csv file later)
                    
                # Once we find this info, we can choose our FOIL for our FM
                # probe trials via a few "if" statements.
                while FM_probe_FOIL_stimulus == "NA":
                    possible_FM_probe_FOIL_stimulus = choice(stimuli_files_list)
                    # First, make sure file is an image (.bmp file)
                    if possible_FM_probe_FOIL_stimulus.split(".")[1] == "bmp":
                        # Next, make sure the possible choice has not been
                        # used before:
                        stimulus_used = False
                        # If we have run FM tests before, we have to check our
                        # list of dictionaries that was generated...
                        if len(FM_log_list) != 0:
                            for FM_dict in FM_log_list:
                                if FM_dict["Used_FM"] == possible_FM_probe_FOIL_stimulus:
                                    stimulus_used = True
                                    break
                        if not stimulus_used:
                            # Lastly, determine the phase the possible FOIL stimulus
                            # to make sure it has never been seen in prior training
                            # (or in test subphases). NOTE THIS ASSUMES THAT WE 
                            # HAVE NOT YET REACHED PHASE 8)
                            img_phase_integer = int(possible_FM_probe_FOIL_stimulus.split(".")[0][-1])
                            if (img_phase_integer > self.training_phase + 1):
                                # If all of the requests are met, we have
                                # found our FM probe FOIL!
                                FM_probe_FOIL_stimulus = possible_FM_probe_FOIL_stimulus
                                break
                
                # Finally, we should update our csv document with this new probe
                # if we're going to use it for this session (so its not used
                # again). First up, we need to append this entry to the dictionary
                FM_log_list.append({
                    "Subject" : self.subject_ID,
                    "Used_FM" : FM_probe_FOIL_stimulus,
                    "Date_Used" : self.date,
                    "FM_phase" : f"{self.training_phase_name_list[self.training_phase].split(':')[0]}.{self.training_subphase_name_list[self.training_subphase].split(':')[0]}"
                    })
                
                # Then write the updated list to a csv file
                with open(FM_stimuli_log_directory, 'w') as csvfile:
                    writer = DictWriter(csvfile,
                                        fieldnames = ['Subject', 'Used_FM',
                                                      'Date_Used', 'FM_phase'])
                    writer.writeheader()
                    writer.writerows(FM_log_list)

                
            
            # Next, we can build the primary dictionary that will hold all the
            # photo file information, their connections to  other stimuli, and
            # the actual loaded image itself,
            self.stimuli_dict = {} 
            
            for i in stimuli_files_list:
                # Image should be "NA" until categorized (if applicable)
                pair_type = "NA"
                # First, make sure file is an image (.bmp file)
                if i.split(".")[1] == "bmp":
                    # First we can determine whether its a sample or comparison
                    # stimulus for future reference 
                    if i[0] == "C":
                        pair = "S"
                    elif i[0] == "S":
                        pair = "C"
                    
                    # Then, check if we need it for this specific training phase.
                    # Autoshaping (or training phase 0)  is special in that it
                    # copies the stimuli used in the first phase. If we are
                    # running the new/old program, then we only select 
                    img_phase_integer = int(i.split(".")[0][-1])
                    if self.all_new_simuli_var:
                        # In "all new stimuli sessions," the image's phase
                        # number must be EQUAL the current phase if it is a 
                        # comparison stimulus OR if the FOIL sample is less
                        # than or equal to the phase num.
                        if (img_phase_integer == self.training_phase) or (img_phase_integer < self.training_phase and i[0] == "C"):
                            # If so, categorize it as a training type stimulus (for
                            # appending ot the dictionary later)
                            pair_type = "training"
                    
                    # For the "new/old" sessions, we take all the comparisons
                    # like normal, but will only select specific samples. If 
                    # new, we only grab the samples from the current phase (e.g.,
                    # img_phase_integer == self.training_phase). If old, we only
                    # grab samples that are from previous phases.
                    elif self.new_old_var in ["New", "Old"]:
                        # If a comparison and from this phase or a previous
                        # one, then buisness as usual
                        if pair == "S" and (img_phase_integer <= self.training_phase): 
                            pair_type = "training"
                        # If a sample, there's more nuance to accept it...
                        else:
                            if self.new_old_var == "New" and img_phase_integer == self.training_phase:
                                pair_type = "training"
                            elif self.new_old_var == "Old" and img_phase_integer < self.training_phase:
                                pair_type = "training"
                        
                    elif (img_phase_integer <= self.training_phase) or (self.training_phase == 0 and img_phase_integer == 1):
                        # If so, categorize it as a training type stimulus (for
                        # appending ot the dictionary later)
                        pair_type = "training"
                        
                    # For non-training probe trials...
                    elif i in probe_stim_list:
                        pair_type = self.training_subphase_name_list[self.training_subphase].split(" ")[1]
                    
                    elif i == FM_probe_FOIL_stimulus:
                        pair_type = "FM_foil"
                        
                    # Finally, generate the actual image and append it's
                    # information to the dictionary before moving on to
                    # the next image.
                    if pair_type != "NA":
                        # If we want to use this stimulus for the
                        # current session, we can process/load the image into 
                        # the existing program.
                        img_file = Image.open(f"{stimuli_folder_path}{i}")
                        # resized_img = img_file.resize(self.choice_key_dims, Image.ANTIALIAS)
                        new_img = ImageTk.PhotoImage(img_file)
                        
                        # Then append everything to the dictionary...
                        self.stimuli_dict[i] = {"type": i[0],
                                                "pair_num": int(i.split("_")[0][1:]),
                                                "phase": int(i.split(".")[0][-1]),
                                                "pair":f"{pair}{i[1:]}",
                                                "trial_type": pair_type,
                                                "image_file": new_img
                                                }

            # Now that we have a dictionary with all this session's stimuli, 
            # we should next determine the order of stimulus presentation for
            # each trial. We can do this by first picking a random sample
            # without replacement in ONLY THE training stimuli (different 
            # process for probe trials), then picking a "foil" or incorrect
            # comparison, and finally  assigning the foil and comparison to
            # either left or right, randomly.
            
            
            # This function just sorts through the created dictionary
            # of stimuli for samples (or "S" type), adds them to a list,
            # and returns it. It's used both for probe trials and for normal
            # stimuli trials.
            def build_stimuli_list(s_dict, stim_type):
                l = []
                for j in s_dict:
                    if s_dict[j]["type"] == "S" and s_dict[j]["trial_type"] == stim_type:
                        l.append(j)
                return l
                
            # First, we need to set up the order of any forced choice trials 
            # if the correction procedure is in place. Note that these forced
            # force trials only occur in training phases (e.g., subphase == 0)
            fc_trial_index = []
            if len(self.forced_choice_stim_list) > 0:
                # The first half of sessions should be forced choice. The second
                # half should be regular training trials with two comparison choices:
                # the correct comparison and a foil.
                fc_trial_index = list(range(1, self.max_number_of_reinforced_trials//2))
                

            # Next, we should assign the twelve probe trials if a CBE or FM
            # subphase type. We do this by gathering the three novel samples, 
            # inputting them into a list, and then multiplying this by four.
            # Note that this only needs to be done once at the beginning of 
            # each session.
            probe_trial_index = []
            if self.training_subphase != 0: # If not training,
                # Then build the semi-randomized INDEX of these twelve stimuli. 
                # This index will be a list of twelve numbers, each one greater
                # than the last and each step being equal to the total number 
                # of trials divided by 12 plus a random value "step" per probe
                # trial. For example, in a CBE session with 96 trials, the probe
                # trial index might look someting like:
                # [5, (3 + 8*1), (4 + 8*2),(8 + 8*3),(2 + 8*4),(1 + 8*5)...(5 + 8*11)]
                # OR
                # [5, 11, 20, 32, 34, 41...93] 
                # where the last value in the list will never be greater than 
                # the total number of reinforced trials (or 96)
                for i in list(range(0, self.probe_trials_per_session)):
                    step = randint(1, self.max_number_of_reinforced_trials//self.probe_trials_per_session)
                    probe_trial_index.append((i * self.max_number_of_reinforced_trials//self.probe_trials_per_session) + step)
                
                # After determing the index at which each probe trial will occur
                # within a session, we need to also assign the relevant FOIL
                # stimuli for each probe trial
                probe_foil_stimulus_list = []
                # For the choice by exclusion test...
                if self.training_subphase in [1,3,5]: # CBE.1, CBE.2, CBE.3
                    # We only need 4 foils for our 4 probe trials. So we can 
                    # just cycle through the available FOIL stimuli (e.g., 
                    # comparisons that have been featured in previous training),
                    # which will differ in number each phase (3,6,12, etc.). As
                    # such, we can just create add to a list of comparisons
                    # names until it reaches 4 items. This will result in 
                    # repeated FOILs if the number of prior stimuli is less 
                    # than 4. 
                    while len(probe_foil_stimulus_list) < self.probe_trials_per_session:
                        # First we can just choose a random training comparison
                        # from the previous training set:
                        pf = choice(list(self.stimuli_dict.keys()))
                        # This should be a comparison and from training
                        if self.stimuli_dict[pf]["type"] == "C" and self.stimuli_dict[pf]["trial_type"] == "training":
                            # Next make sure if it's either not in the list
                            # OR if the number of available comparisons is less
                            # than the number of probe trials, we can have 
                            # repeats after all available training comparisons
                            # are used
                            if pf not in probe_foil_stimulus_list or (self.training_phase == 1 and len(probe_foil_stimulus_list) >= 3):
                                probe_foil_stimulus_list.append(pf)
                
                # There's a different process for the fast mapping test types,
                # which have the same foil for every single trial within a session
                elif self.training_subphase in [2,4,6]: # FM.1, FM.2, FM.3
                    probe_foil_stimulus_list = [FM_probe_FOIL_stimulus] * self.probe_trials_per_session
                
                # Lastly, let's shuffle the probe foil list to make sure its 
                # quasi random. 
                shuffle(probe_foil_stimulus_list)

            # Now that we have the organization of probe trials (both the index
            # and any assigned FOILs), we can finally get around to building 
            # the identity of each trial within our session. First, a couple 
            # variables, lists, and dictionaries that will be manipulated 
            # within our "for" loop:
            self.stimulus_order_dict = {} # This will be the order of each trial's stimuli
            c = 1 # Counter (for each trial)
            list_of_samples = [] # For training trials
            probe_trials_sample_list = [] # For probe trials
            
            # Then set up the left/right counterbalancing
            def refill_left_right_list ():
                lr_list = ["left", "right"] * (self.max_number_of_reinforced_trials // 12)
                shuffle(lr_list)
                return(lr_list)
            
            left_right_list = refill_left_right_list()
            
            # Build the training trials...
            while c <= self.max_number_of_reinforced_trials:
                # If a CBE or FM non-training probe trial, we do something special
                if c in probe_trial_index:
                    if len(probe_trials_sample_list) == 0:
                        probe_trials_sample_list = build_stimuli_list(self.stimuli_dict,
                                                                      self.training_subphase_name_list[self.training_subphase].split(" ")[1])
                    # Choose a sample from that list...
                    sample_choice = choice(probe_trials_sample_list) # this is our sample!!
                    # ...without replacement (remove it)
                    probe_trials_sample_list.remove(sample_choice)
                    
                    # Next, choose a left and right sample. One should be the
                    # correct comparison, one should be the foil. We can start 
                    # with the foil. This process differs for CBE and FM sub-phase
                    # types. Importantly for each, the foil shouldn't be 
                    # repeated across trials (as much as possible), and is
                    # pre-determined before this loop begins in the 4-item
                    # probe_foil_stimulus_list.
                    foil = probe_foil_stimulus_list[0]
                    probe_foil_stimulus_list.remove(foil)

                    # Next we grab the correct image:
                    correct_comp = self.stimuli_dict[sample_choice]["pair"]
                 
                else:
                    # If a trial in a forced choice session...
                    if self.forced_choice_session:
                        # For forced choice trials in training, we don't need to 
                        # balance out the sample assignments or need anything 
                        # fancy (its training). We can just rely on random choice.
                        sample_choice = choice(self.forced_choice_stim_list)
                        # Next we grab the correct image:
                        correct_comp = self.stimuli_dict[sample_choice]["pair"]
                    
                    # If a training trial (non-probe), we do the default
                    else:
                        # (Re)fill our list of samples population (e.g., bag of marbles)
                        #if it is empty
                        if len(list_of_samples) == 0:
                            list_of_samples = build_stimuli_list(self.stimuli_dict,
                                                                 "training")
                        # Choose a sample from that list...
                        sample_choice = choice(list_of_samples) # this is our sample!!
                        # ...without replacement (remove it)
                        list_of_samples.remove(sample_choice)
                        # Next we grab the correct image:
                        correct_comp = self.stimuli_dict[sample_choice]["pair"]
                        
                    # Next, choose the foil stimulus (the incorrect comparison)
                    foil = "NA"
                    while foil == "NA":
                        possible_foil = choice(list(self.stimuli_dict.keys())) # Choose some random stimulus
                        # First, it MUST be a comparison (not sample)
                        if self.stimuli_dict[possible_foil]["type"] == "C":
                            # ...and must be one of the training comparions...
                            if self.stimuli_dict[possible_foil]["trial_type"] == "training":
                                # ...and it MUST NOT be the sample for the chosen sample (e.g., different pair numbers)
                                if self.stimuli_dict[possible_foil]["pair_num"] != self.stimuli_dict[sample_choice]["pair_num"]:
                                    # If both are yes, we've found a foil!
                                    foil = possible_foil
                    # If the chosen foil does not match any of these boolean
                    # statements, we try again w/ another random choice...
                
                
                # After we determine the correct comparison and the the foil,
                # we assign to left or right key locations randomly by adding
                # to a list and randomly selecting one for the leftside  and 
                # one for the right.
                if len(left_right_list) == 0:
                    left_right_list = refill_left_right_list()
                
                if left_right_list[0] == "left":
                    left = correct_comp
                    right = foil
                else:
                    left = foil
                    right = correct_comp
                
                # Remove that choice
                left_right_list.remove(left_right_list[0])
                
                # Finally, we can add this trial to our dictionary before moving
                # on to the next trial.
                self.stimulus_order_dict[c] = {
                    # These are the literal image files
                    "sample_key": self.stimuli_dict[sample_choice]["image_file"],
                    "left_comparison_key": self.stimuli_dict[left]["image_file"],
                    "right_comparison_key": self.stimuli_dict[right]["image_file"],
                    "correct_comparison_key": self.stimuli_dict[correct_comp]["image_file"],
                    # This is for writing data
                    "sample_stimulus_name": sample_choice.split(".")[0],
                    "left_stimulus_name": left.split(".")[0],
                    "right_stimulus_name": right.split(".")[0],
                    "correct_stimulus_name": correct_comp.split(".")[0],
                    "pair_num": self.stimuli_dict[sample_choice]["pair"],
                    "trial_type": self.stimuli_dict[sample_choice]["trial_type"]
                    }
                
                # Importantly, we need to change the trial type if its a forced
                # choice trial (easier to do this after the fact):
                if c in fc_trial_index:
                    self.stimulus_order_dict[c]["trial_type"] = "FC_trial"

                # Lastly, increment the counter by 1 for the next trial!
                c += 1
            
            # After we ~finally~ set up the stimulus order, we need to set up 
            # a timer and move on to the ITI
            
            if self.subject_ID == "TEST": # If test, don't worry about first ITI delay
                self.ITI_duration = 1 * 1000
                self.root.after(1, lambda: self.ITI())
            else:
                self.root.after(30000, lambda: self.ITI())

        self.root.bind("<space>", first_ITI) # bind cursor state to "space" key
        self.mastercanvas.create_text(448,384,
                                      fill="white",
                                      font="Times 26 italic bold",
                                      text=f"P035 \n Place bird in box, then press space \n Subject: {self.subject_ID} \n Training Phase {self.training_phase_name_list[self.training_phase]} \n Subphase {self.training_subphase_name_list[self.training_subphase]}")
        
                
## %% ITI

    # Every trial (including the first) "starts" with an ITI. The ITI function
    # does several different things:
    #   1) Checks to see if any session constraints have been reached
    #   2) Resets the hopper and any trial-by-trial variables
    #   3) Increases the trial counter by one
    #   4) Moves on to the next trial after a delay
    # 
    def ITI (self):
        # This function just clear the screen. It will be used a lot in the future, too.
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
        if self.current_trial_counter  == self.max_number_of_reinforced_trials:
            print("&&& Trial max reached &&&")
            self.exit_program("event")
        # elif datetime.now() >= (self.session_duration):
        #    print("Time max reached")
        #    self.exit_program("event")
        
        # Else, after a timer move on to the next trial. Note that,
        # although the after() function is given here, the rest of the code 
        # within this function is still executed before moving on.
        else: 
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
            self.trial_start = time() # Set trial start time (note that it includes the ITI, which is subtracted later)
            self.write_comp_data(False) # update data .csv with trial data from the previous trial
            
            # Next up, set the sample key FR for this upcoming
            if self.training_phase == 0:
                self.sample_key_FR = 1
            elif self.manual_FR != "NA":
                self.sample_key_FR = self.manual_FR
            else:
                self.sample_key_FR = choice(list(range(3,9)))

            # Increase trial counter by one
            self.current_trial_counter += 1
            
            # Next, set a delay timer to proceed to the next trial
            self.root.after(self.ITI_duration,
                            lambda: self.sample_key_loop(self.sample_key_FR))
            
            # If autoshaping, pick the key that will be illuminated 
            if self.training_phase == 0:
                as_options = ["left_comparison_key",
                              "right_comparison_key",
                              "sample_key"]
                self.illuminated_key = choice(as_options)
                
            # Finally, print terminal feedback "headers" for each event within the next trial
            print(f"\n{'*'*35} Trial {self.current_trial_counter} begins {'*'*35}") # Terminal feedback...
            print(f"{'Event Type':>30} | Xcord. Ycord. | Stage | Session Time | Trial Type")
        
#    #%%  Pre-choice loop 
    """
    Each DMTS trial is built of four seperate stages (following the ITI). The
    AS and MTS phases each use a subset of these stages. The numeric "code" of
    each stage is given below, and are used in the "build_keys()" function 
    below to determine what keys should be colored and activated.
        
        0) Sample key loop - the sample is pecked a certain number of times. 
            This differs within the MTS phase and is fixed in the DMTS. The
            AS phase only takes place within this stage.
            
        1) Delay stage - following the completion of the sample key loop, a 
            brief delay occurs in the DMTS phase. In MTS, there is no delay
            and the sample remains onscreen. 
            
        2) Choice stage - in this stage, the color of each of the parallel 
            choice keys is filled in and are activated. A single peck of either
            leads to reinforcement or 
        
        3) Feedback stage - for DMTS trials, a post-choice period featured 
            information dependent upon a subject's experimental group. For 
            experimental subjects, the sample key was illuminated with the 
            correct sample stimulus (regardless of choice). For control
            subjects, the sample key was illuminated with a grey key (e.g.,
            non-informative cue).
    """
    

    def sample_key_loop(self, passed_FR):
        # This is one half of the RR loop. It can be thought of as the resting
        # "return state" that is dependent upon a key press (on the O key). 
        # Otherwise, it will stay in this state forever.
        if operant_box_version and not self.light_HL_on_bool:
            rpi_board.write(house_light_GPIO_num,
                            True) # Turn on the houselight
        self.trial_FR = passed_FR
        self.clear_canvas()
        self.trial_stage = 0
        self.build_keys()
    
    def sample_key_press(self, event):
        # This is the other half of the RR loop. When the key is pressed in the 
        # resting state above, the function below is triggered via the
        # "build_keys()" function. If the RR is completed, then it moves
        # on to the choice phase (via the present_target() function). If not,
        # the RR is decreased by one and it returns to the resting state.
        if self.trial_stage == 0: # If sample stage
            self.write_data(event, "sample_key_press")
            if self.trial_FR <= 1:
                self.clear_canvas()
                # Once FR is completed, then move on to matching stage
                self.matching_stage()
                    
            else:
                self.trial_FR -= 1
                self.sample_key_loop(self.trial_FR)
        else:
            self.write_data(event, "nonactive_sample_key_press")
    
    def matching_stage(self):
        self.clear_canvas()
        self.trial_stage = 1
        self.build_keys()
        self.FI_complete = not self.FI_complete # Flip boolean to false (or back to true)
        if not self.FI_complete:
            self.FI_timer = self.root.after(self.FI_duration,
                                            self.matching_stage)
    
        
    def build_keys(self):
        # This is a function that builds the all the buttons on the Tkinter
        # Canvas. The Tkinter code (and geometry) may appear a little dense
        # here, but it follows many of the same rules. Al keys will be built
        # during non-ITI intervals, but they will only be filled in and active
        # during specific times. However, pecks to keys will be differentiated
        # regardless of activity.
        
        # First, build the background. This basically builds a button the size of 
        # screen to track any pecks; buttons built on top of this button will
        # NOT count as background pecks but as key pecks, because the object is
        # covering that part of the background. Once a peck is made, an event line
        # is appended to the data matrix.
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
        
        # Nest, we update all the colors needed for this stage of the trial
        self.calculate_trial_key_stimuli() # updates color list
        
        # Coordinate dictionary for the shapes around a key
        key_coord_dict = {"sample_key": [416, 352, 608, 544], # [325, 275, 475, 425], # ~192 p diameter
                          "left_comparison_key": [128, 448, 320, 640], #[100, 350, 250, 500], # ~192 diameter
                          "right_comparison_key": [704, 448, 896, 640] #[550, 350, 700, 500] # ~192 diameter
                          }
        
        # Now that we have all the coordinates linked to each specific key,
        # we can use a for loop to build each one.
        for key_string in key_coord_dict:
            # First up, build the actual circle that is the key and will
            # contain the stimulus. Order is important here, as shapes built
            # on top of each other will overlap/cover each other.
            
            # Next up, build the in the stimuli (if they should be built)
            if self.current_key_stimulus_dict[key_string] != "black": # Only strue if its an image
                self.mastercanvas.create_image((key_coord_dict[key_string][0] + key_coord_dict[key_string][2])//2,
                                               (key_coord_dict[key_string][1] + key_coord_dict[key_string][3])//2,
                                               anchor='center',
                                               image= self.current_key_stimulus_dict[key_string],
                                               tag = key_string)
                
            self.mastercanvas.create_oval(key_coord_dict[key_string],
# =============================================================================
#                 [key_coord_dict[key_string][0],
#                                           key_coord_dict[key_string][1],
#                                           key_coord_dict[key_string][2],
#                                           key_coord_dict[key_string][3]],
# =============================================================================
                                                         fill = "",
                                                         outline = "",
                                                         tag = key_string)
                
            self.mastercanvas.tag_bind(key_string,
                                       "<Button-1>",
                                       lambda event,
                                       key_string = key_string: self.key_press(event,
                                                                    key_string))
            
        # If we're in a forced choice trial, we need to cover up the incorrect 
        # foil such that only the sample and correct comparison are visible 
        # (and active) on the screen.
        if self.stimulus_order_dict[self.current_trial_counter]["trial_type"] == "FC_trial":
            # To do this, we need to first figure out if the foil is on the 
            # left or the right side. If the correct comparison is on the left,
            # foil should be on the right:
            if self.stimulus_order_dict[self.current_trial_counter]["correct_comparison_key"] == self.stimulus_order_dict[self.current_trial_counter]["left_comparison_key"]:
                cover_cords = key_coord_dict["right_comparison_key"]
                # foil should be on the right:
            elif self.stimulus_order_dict[self.current_trial_counter]["correct_comparison_key"] == self.stimulus_order_dict[self.current_trial_counter]["right_comparison_key"]:
                cover_cords = key_coord_dict["left_comparison_key"]
            # Then we can build the cover on top of the foil:
            self.mastercanvas.create_rectangle(cover_cords,
                                               fill = "black",
                                               outline = "black",
                                               tag = "bkgrd")
            # This cover should be just like the background and write data
            # events accordingly...
            self.mastercanvas.tag_bind("bkgrd",
                                       "<Button-1>",
                                       lambda event, 
                                       event_type = "background_peck": 
                                           self.write_data(event, event_type))
            
        # Lastly, start an auto timer if it's autoshaping
        if self.training_phase == 0:
            self.auto_timer = self.root.after(self.auto_reinforcer_timer,
                                               lambda: self.provide_food(False)) # False b/c non autoreinforced


    def calculate_trial_key_stimuli(self):
        # This function calculates the colors for each key at a particular 
        # experimental phase and/or trial_stage. It is referenced multiple
        # times throughout each stage of a trial. It always starts by resetting
        # the color list to default
        self.current_key_stimulus_dict = {
            "left_comparison_key": "black",
            "right_comparison_key": "black",
            "sample_key": "black"
            }
        
        if self.training_phase == 0: # If autoshaping...
            self.current_key_stimulus_dict[self.illuminated_key] = self.stimulus_order_dict[self.current_trial_counter][self.illuminated_key]
                            
        else:
            if self.trial_stage == 0: # sample key alone
                self.current_key_stimulus_dict["sample_key"] = self.stimulus_order_dict[self.current_trial_counter]["sample_key"]
            
            elif self.trial_stage == 1: # shows all stimuli
                for stim in self.current_key_stimulus_dict:
                    self.current_key_stimulus_dict[stim] = self.stimulus_order_dict[self.current_trial_counter][stim]


    
    """ 
    The three functions below represent the outcomes of choices made under the 
    two different cotnigencies (simple or choice). In the simple task (with
    only one "choice" key and target color), any response on the green "choice" 
    key within time contraints is correct and will be reinforced and logged as
    such. In the true choice task, only a choice of the "correct" target-color
    matching key will be reinforced; the opposite key leads to a TO.
    
    Note that, in this setup, the left and right choice keys are fixed to a 
    specific color (left is always blue). We'll need to counterbalance color
    across subjects later on.
    """
    
    def key_press(self, event, keytag):
        # For sample key, always pass off to different function
        if keytag == "sample_key": 
            self.sample_key_press(event)
        # First, make sure the keys are actually active
        elif self.current_key_stimulus_dict[keytag] == "black":
            self.write_data(event, (f"non_active_{keytag}_peck"))
        else:
            # If active, always write the type of key press
            self.write_data(event, f"{keytag}_press")
            # If autoshaping, its automatically correct (if active)
            if self.training_phase == 0:
                self.write_data(event, "correct_choice")
                # Next, cancel the timer
                try:
                    self.root.after_cancel(self.auto_timer)
                except AttributeError:
                    pass
                # Next, provide food!
                self.provide_food(True)
            # Lastly, if active but not autoshaping...
            else:
                # If key key is active, the below should always be true
                if self.trial_stage == 1: 
                    if self.FI_complete: # If FI is complete...
                        # If correct choice
                        if self.stimulus_order_dict[self.current_trial_counter]["correct_comparison_key"] == self.current_key_stimulus_dict[keytag]:
                            self.write_data(event, "correct_choice")
                            # Only training trials are reinforced (including FC training)
                            if self.stimulus_order_dict[self.current_trial_counter]["trial_type"] in ["training", "FC_trial"]:
                                self.provide_food(True) 
                            # ... correct probe trials go straight to the ITI
                            else:
                                self.ITI()
                         # If incorrect choice...
                        else:
                            self.write_data(event, "incorrect_choice")
                            self.ITI()
                    else: # FI is not complete
                        self.write_data(event, "pre_FI_choice")
                else:
                    print("ERROR: something is fucked up")
            
    
    # %% Post-choice contingencies: always either reinforcement (provide_food)
    # or time-out (time_out_func). Both lead back to the next trial's ITI,
    # thereby completing the loop.
    
    def provide_food(self, key_pecked):
        # This function is contingent upon correct and timely choice key
        # response. It opens the hopper and then leads to ITI after a preset
        # reinforcement interval (i.e., hopper down duration)
        self.clear_canvas()
        self.write_data(None, "reinforcer_provided")
        
        # We first need to add one to the reinforcement counter
        self.reinforced_trial_counter += 1
        
        # If key is operantly reinforced
        if key_pecked:
            if not operant_box_version or self.subject_ID == "TEST":
                self.mastercanvas.create_text(512, 384,
                                              fill="white",
                                              font="Times 26 italic bold", 
                                              text=f"Correct Key Pecked \nFood accessible ({int(self.hopper_duration/1000)} s)") # just onscreen feedback
        else: # If auto-reinforced
            if not operant_box_version or self.subject_ID == "TEST":
                    self.mastercanvas.create_text(512, 384,
                                  fill="White",
                                  font="Times 26 italic bold", 
                                  text=f"Auto-timer complete \nFood accessible ({int(self.hopper_duration/1000)} s)") # just onscreen feedback
            self.write_data(None, "auto_reinforcer_provided")
        # Next send output to the box's hardware
        if operant_box_version:
            rpi_board.write(house_light_GPIO_num,
                            False) # Turn off the house light
            rpi_board.write(hopper_light_GPIO_num,
                            True) # Turn off the house light
            rpi_board.set_servo_pulsewidth(servo_GPIO_num,
                                           hopper_up_val) # Move hopper to up position
        self.root.after(self.hopper_duration,
                        lambda: self.ITI())
        

    # %% Outside of the main loop functions, there are several additional
    # repeated functions that are called either outside of the loop or 
    # multiple times across phases.
    
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
# =============================================================================
#                                                          
#     def manual_reinforcer(self):
#         # This function provides a manual reinforcer to the bird but keeps
#         # everything the same. The trial doesn't end, there's just a 3s 
#         # food access.
#         def delete_text(m, t):
#             self.mastercanvas.destroy(t)
#         
#         self.write_data(None, "manual_reinforcer_provided")
#         if operant_box_version:
#             self.Hopper.change_hopper_state("On") # turn on hopper
#             self.root.after(self.hopper_duration,
#                             lambda: self.Hopper.change_hopper_state("Off"))
#         else:
#             text = self.mastercanvas.create_text(400,100,
#                                             fill="white",
#                                             font="Times 20 italic bold", 
#                                             text=f"Manual reinforcer provided \nFood accessible ({int(self.hopper_duration/1000)} s)")
#             self.root.after(self.hopper_duration,
#                             delete_text(text)) # then remove the text after a delay
#         
# =============================================================================
    
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
            self.root.destroy() # destroy Canvas
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
        # session, then written to a .csv once at the end of the session.
        if event != None: 
            x, y = event.x, event.y
        else: # There are certain data events that are not pecks.
            x, y = "NA", "NA"
            
        print(f"{outcome:>25} | x: {x: ^3} y: {y:^3} | {self.trial_stage:^5} | {str(datetime.now() - self.start_time)} | {self.stimulus_order_dict[self.current_trial_counter]['trial_type']}")
        # print(f"{outcome:>30} | x: {x: ^3} y: {y:^3} | Target: {self.current_target_location: ^2} | {str(datetime.now() - self.start_time)}")
        self.session_data_frame.append([
            str(datetime.now() - self.start_time), # SessionTime as datetime object
            x, # X coordinate of a peck
            y, # Y coordinate of a peck
            outcome, # Type of event (e.g., background peck, target presentation, session end, etc.)
            # For the three stimuli shown, we need to split the filename from the directory
            self.stimulus_order_dict[self.current_trial_counter]["sample_stimulus_name"], # Sample stimulus
            self.stimulus_order_dict[self.current_trial_counter]["left_stimulus_name"], # Left comparison
            self.stimulus_order_dict[self.current_trial_counter]["right_stimulus_name"], # Right comparison 
            self.stimulus_order_dict[self.current_trial_counter]["correct_stimulus_name"], # Correct stimulus
            self.stimulus_order_dict[self.current_trial_counter]["pair_num"], # Number of the pair
            self.trial_stage, # Substage within each trial (1 or 2)
            round((time() - self.trial_start - (self.ITI_duration/1000)), 5), # Time into this trial minus ITI (if session ends during ITI, will be negative)
            self.current_trial_counter, # Trial count within session (1 - max # trials)
            self.reinforced_trial_counter, # Reinforced trial counter
            self.trial_FR, # FR of a specific trial
            self.FI_duration, # FI Timer
            self.stimulus_order_dict[self.current_trial_counter]["trial_type"], # Trial type (e.g., "training", "CBE.1", etc.)
            self.subject_ID, # Name of subject (same across datasheet)
            self.training_phase, # Phase of training as a number (0 - 7)
            self.training_subphase,  # Phase of training subphase as a numer (0 - 4)
            self.forced_choice_session, # Forced choice session
            self.all_new_simuli_var, # All new stimuli session
            self.new_old_var, # New/old session 
            date.today() # Today's date as "MM-DD-YYYY"
            ])
        
        
        header_list = ["SessionTime", "Xcord","Ycord", "Event",
                       "SampleStimulus", "LComp", "RComp", "CorrectKey", "PairNum",
                       "TrialSubStage", "TrialTime", "TrialNum", "ReinTrialNum",
                       "SampleFR", "FI", "TrialType", "Subject", "TrainingPhase",
                       "TrainingSubPhase", "ForcedChoiceSession", "AllNewStimuli",
                       "NewOldStimuliSession", "Date"] # Column headers
        
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
            myFile_loc = f"{self.data_folder_directory}/{self.subject_ID}/{self.subject_ID}_{self.start_time.strftime('%Y-%m-%d_%H.%M.%S')}_P035_data-Phase{self.training_phase}.csv" # location of written .csv
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


    
