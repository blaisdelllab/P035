#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 15 11:57:17 2026

@author: kayleyozimac
""

#This is the code for Kayley Ozimac's mini project (P035g) for her 'FOAM' project.
It is a replication of Castro et al. (2013)
    
     1) Phase 1 (Acclimation): During this phase, subjects were acclimated to the 
experimental contingencies and stimuli. Each trial began with the presentation of a 
centrally located orienting stimulus (a white square). A single peck to this orienting 
stimulus resulted in its disappearance and the immediate presentation of a stimulus 
(either a sample or comparison) in the center of the screen. Two pecks to this stimulus 
resulted in reinforcement (6-s access to the food hopper), followed by a 15-s intertrial 
interval (ITI).

    2) Phase 2 (Unsupervised sample–comparison association training): During this phase,
subjects were exposed to consistent pairings between sample stimuli and comparison stimuli.
Each trial began with presentation of the orienting stimulus in the center of the screen.
A single peck resulted in the presentation of a sample stimulus in the center of the screen.
Subjects were required to complete an observing response requirement to the sample stimulus,
which ranged from 3 to 10 pecks (adjusted across sessions). Upon completion of this requirement,
a single comparison stimulus was presented in either the left or right comparison location.
Subjects were required to peck the comparison stimulus on an FR1 schedule. Completion of this
requirement resulted in reinforcement followed by the 15-s ITI.


    3) Phase 3 (Association test trials): During this phase, probe trials were interspersed 
among regular training trials to assess whether subjects had acquired sample-comparison associations. 
Each session began with 16 standard training trials identical to those in Phase 2. The remaining 
trials consisted of 112 training trials and 32 probe trials presented in pseudorandom order.


    4) Phase 4 (Supervised sample-comparison association training): In this phase, subjects were 
trained with differential reinforcement to explicitly learn sample-comparison mappings. Each trial
 began with presentation of the orienting stimulus, followed by the sample stimulus and completion 
 of the observing response requirement. Upon completion, two comparison stimuli (1 paired; 1 of the other 7)
 were presented simultaneously: the correct comparison associated with the object stimulus and 
 an incorrect comparison (foil) associated with a different object.
 
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
        self.control_window.title("P035g Control Panel")
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
            "Phase 1.i (Acclimation: S01–S08 / C01–C08)",
            "Phase 1.ii (Acclimation: S09–S16 / C09–C16)",
            "Phase 2 (Unsupervised Training)",
            "Phase 3 (Testing Session)",
            "Phase 4 (Supervised Training)"
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
                    str(self.subject_ID_variable.get()),
                    self.record_data_variable.get(),
                    self.data_folder_directory,
                    self.exp_phase_variable.get(),
                    self.experimental_phase_titles.index(self.exp_phase_variable.get())
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
        # Choice requirement for test/supervised NDE-style)
        # i.e., require the same number of pecks on the chosen comparison as the sample observing req
        # Comparison requirement: DE-style FR1 on comparisons
        self.comparison_FR = 1
        # Correction + choice-lock variables
        self.in_correction = False
        self.chosen_comp_tag = None
        
        # Setup experimental phase
        self.exp_phase_name = exp_phase_name # e.g., "Phase 1: Familiarization"
        self.exp_phase_num = exp_phase_num # e.g., 0   
        if self.exp_phase_num in [0, 1]: self.exp_phase = "Phase 1"
        if self.exp_phase_num == 2:      self.exp_phase = "Phase 2"
        if self.exp_phase_num == 3:      self.exp_phase = "Phase 3"
        if self.exp_phase_num == 4:      self.exp_phase = "Phase 4"
        
        # Setup data directory
        self.data_folder_directory = data_folder_directory
        
        ## Set the other pertanent variables given in the command window
        self.subject_ID = subject_ID
        self.record_data = record_data
        
        ## Set up the visual Canvas
        self.root = Toplevel() 
        self.root.title(f"P035g {self.exp_phase_name}: ") # this is the title of the window
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
            # House light state tracking (prevents AttributeError)
            self.light_HL_on_bool = False

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
        # Set up FR 
        self.comparison_FR = 1
        self.comparison_key_presses = 0 # counts number of key presses on comp for each trial
        self.correct_comparison_key_presses = 0 # counts number of key presses on comp for each trial
        self.incorrect_comparison_key_presses = 0 # counts number of key presses on comp for each trial
        self.sample_key_presses = 0 # counts number of key presses on sample for each trial
        self.reinforced_trial_counter = 0 
        self.last_written_trial_num = None  # Track the last written trial number
        if self.exp_phase_num in [0, 1]:
            self.max_trials = 160
        elif self.exp_phase_num == 2:
            self.max_trials = 128
        elif self.exp_phase_num == 3:
            self.max_trials = 160
        elif self.exp_phase_num == 4:
            self.max_trials = 112
        else:
            self.max_trials = 100
        
        # Here is stuff that is relevant to building trial stimuli
        if self.exp_phase_num in [0, 1]:
            self.sample_name = "NA"
            self.comparison_name = "NA"
            self.foil_name = "NA"
            self.comparison_location = "NA"

        # These are additional "under the hood" variables that need to be declared
        self.session_data_frame = [] #This where trial-by-trial data is stored
        self.trial_stage = 0 # This tracks the stage within the trial
        self.current_trial_counter = 0 # This counts the number of trials that have passed
      
        header_list = [
                "SessionTime", "ExpPhase", "Subject", "Xcord", "Ycord", "Event",
                "TrialSubStage",
                "TrialType",
                "TrialNum", "ReinTrialNum",
                "SampleFR", "ComparisonFR",
                "SampleFile",
                "PairedCompFile",
                "FoilCompFile",
                "LeftCompFile",
                "RightCompFile",
                "SingleCompFile",
                "SingleSide",
                "ChosenCompFile",
                "ChosenSide",
                "IsPairedChoice",
                "Correctness",
                "TrialTime",
                "ChoiceLatency", "ChoiceDuration",
                "InCorrection",
                "Date"
        ]
    
        self.session_data_frame.append(header_list) # First row of matrix is the column headers
        self.date = date.today().strftime("%y-%m-%d")
        self.myFile_loc = 'FILL' # To be filled later on after Pig. ID is provided (in set vars func below)
        
        # Determine base path depending on environment
        if operant_box_version:
            base_path = "/home/blaisdelllab/Desktop/Experiments/P035"
        else:
            base_path = "/Users/kayleyozimac/Desktop/P035g"
        
        # Assign paths and load files based on phase

        # ----------------------------
        # Stimulus paths (single folder)
        # ----------------------------
        if operant_box_version:
            base_path = "/home/blaisdelllab/Desktop/Experiments/P035g"
        else:
            base_path = "/Users/kayleyozimac/Desktop/P035g"
        
        self.stimuli_path = os_path.join(base_path, "P035g_stimuli")
        
        # Load stimuli from one folder
        all_files = sorted([f for f in listdir(self.stimuli_path) if f.lower().endswith(".bmp")])
        
        # Split into samples vs comparisons by filename prefix
        self.sample_files = sorted([f for f in all_files if f.upper().startswith("S")])
        self.comparison_files = sorted([f for f in all_files if f.upper().startswith("C")])
        
        assert len(self.sample_files) == 16, f"Need 16 sample stimuli (S##.bmp), found {len(self.sample_files)}: {self.sample_files}"
        assert len(self.comparison_files) == 16, f"Need 16 comparison stimuli (C##.bmp), found {len(self.comparison_files)}: {self.comparison_files}"
               
         # Pair map: S01->C01, S02->C02, etc.
        def stim_num(fname):
            # "S01.bmp" -> 1
            return int(fname[1:3])
        
        self.pair_map = {}
        for s in self.sample_files:
            n = stim_num(s)
            c_match = f"C{str(n).zfill(2)}.bmp"
            if c_match not in self.comparison_files:
                raise ValueError(f"Missing comparison for {s}: expected {c_match}")
            self.pair_map[s] = c_match
        
        print("Loaded samples:", self.sample_files)
        print("Loaded comparisons:", self.comparison_files)
        print("Pair map:", self.pair_map)
        
        # ---------------------------------------------------------
        # DE-group split (Phase 2–3 uses only 8 pairs; Phase 4 returns the other 8)
        # ---------------------------------------------------------
        # Option 1 (simple & stable): first 8 pairs are trained early, last 8 withheld
        phase23_samples = self.sample_files[:8]     # S01–S08
        withheld_samples = self.sample_files[8:]    # S09–S16
        
        # If you want it randomized but consistent per bird, use this instead:
        # rng_list = self.sample_files.copy()
        # shuffle(rng_list)
        # phase23_samples = rng_list[:8]
        # withheld_samples = rng_list[8:]
        
        self.phase23_samples = phase23_samples
        self.withheld_samples = withheld_samples
        
        self.phase23_comps = [self.pair_map[s] for s in self.phase23_samples]
        self.withheld_comps = [self.pair_map[s] for s in self.withheld_samples]
        
        print("\nDE split:")
        print(" Phase2–3 samples:", self.phase23_samples)
        print(" Withheld samples:", self.withheld_samples)
        
        # Always initialize, so later code never crashes
        self.stimuli_assignment_dict = {}
        
        def draw_vr5_bounded_3_10():
            """
            VR5-ish with bounds 3–10 implemented as a per-trial draw from [3..10].
            (Mean = 6.5, not 5, but this matches the style of your example code.)
            """
            return choice(range(3, 11))  # 3..10 inclusive
        
        self.draw_vr5_bounded_3_10 = draw_vr5_bounded_3_10
        
        def interleave_with_spacing(train_trials, probe_trials, min_train_between_probes=1):
            train = train_trials.copy()
            probe = probe_trials.copy()
            shuffle(train)
            shuffle(probe)
        
            out = []
            train_since_probe = min_train_between_probes
        
            while train or probe:
                can_take_probe = bool(probe) and train_since_probe >= min_train_between_probes
                can_take_train = bool(train)
        
                if can_take_probe and (not can_take_train or choice([True, False])):
                    out.append(probe.pop())
                    train_since_probe = 0
                elif can_take_train:
                    out.append(train.pop())
                    train_since_probe += 1
                else:
                    # fallback only if probes remain
                    out.append(probe.pop())
                    train_since_probe = 0
        
            return out
        
        def build_counterbalanced_train_trials(samples, n_blocks, pair_map):
            """
            Build n_blocks of training trials where each block contains each sample once.
            Counterbalance sides across pairs of blocks so each sample appears once on left
            and once on right within each 2-block pair.
            """
            assert n_blocks % 2 == 0, "Use an even number of blocks for perfect counterbalancing."
        
            trials = []
            for _ in range(n_blocks // 2):
                # block A
                blockA = samples.copy()
                shuffle(blockA)
        
                # assign exactly 4 left + 4 right (for 8 samples)
                sidesA = (["left"] * (len(samples)//2)) + (["right"] * (len(samples)//2))
                shuffle(sidesA)
        
                # block B: same samples, but opposite side for each sample
                # We keep mapping sample->side from blockA so we can invert it
                side_map_A = {s: side for s, side in zip(blockA, sidesA)}
        
                # Shuffle order independently for block B
                blockB = samples.copy()
                shuffle(blockB)
        
                for s in blockA:
                    trials.append({
                        "trial_type": "train",
                        "sample": s,
                        "sample_FR": self.draw_vr5_bounded_3_10(),  # NEW
                        "single_comp": pair_map[s],
                        "single_side": side_map_A[s]
                    })
        
                for s in blockB:
                    trials.append({
                        "trial_type": "train",
                        "sample": s,
                        "sample_FR": self.draw_vr5_bounded_3_10(),  # NEW
                        "single_comp": pair_map[s],
                        "single_side": ("right" if side_map_A[s] == "left" else "left")
                    })
        
            return trials
        
        def cycle_shuffle(items, n_needed):
            """
            Returns a list of length n_needed built from repeated shuffled cycles of items,
            so every item appears once before any repeats.
            """
            items = list(items)
            out = []
            while len(out) < n_needed:
                block = items.copy()
                shuffle(block)
                out.extend(block)
            return out[:n_needed]
        
        self.cycle_shuffle = cycle_shuffle

        ## SET UP STIMULI ORDER FOR TRIALS
        
        def _is_sample(fname):
            return isinstance(fname, str) and fname.upper().startswith("S")
        
        def _is_comp(fname):
            return isinstance(fname, str) and fname.upper().startswith("C")
        
        def pretty_print_trial_order(phase_num, trials_dict):
            if not trials_dict:
                print("NOTE: stimuli_assignment_dict not built for this phase yet.")
                return
        
            print("\n" + "="*72)
            # nicer label (so 0/1 show as Phase 1.i / 1.ii, etc.)
            phase_labels = {
                0: "Phase 1.i (Acclimation: S01–S08 / C01–C08)",
                1: "Phase 1.ii (Acclimation: S09–S16 / C09–C16)",
                2: "Phase 2 (Unsupervised Training)",
                3: "Phase 3 (Testing Session)",
                4: "Phase 4 (Supervised Training)"
            }
            print(f"TRIAL ORDER PREVIEW ({phase_labels.get(phase_num, f'Phase {phase_num}')})")
            
            if phase_num == 3:
                print("NOTE: In Phase 3 (Testing Session), '*' indicates a TEST/PROBE trial.")
            print("="*72)
        
            for tn in sorted(trials_dict.keys()):
                tr = trials_dict[tn]
                ttype = tr.get("trial_type", "NA")
        
                # Mark test/probe trials in Phase 3 
                star = ""
                if phase_num == 3 and ttype == "test":
                    star = "*"
        
                # -------------------------
                # Phase 1 (Acclimation): single stimulus per trial (either S or C)
                # (both 1.i and 1.ii)
                if phase_num in [0, 1]:
                    stim = tr.get("stimulus", "NA")
                    side = tr.get("side", "NA")
        
                    # classify by filename prefix only
                    if _is_sample(stim):
                        line = f"Trial {tn:>3}{star}: SAMPLE  {stim}  (side={side})"
                    elif _is_comp(stim):
                        line = f"Trial {tn:>3}{star}: COMP    {stim}  (side={side})"
                    else:
                        line = f"Trial {tn:>3}{star}: UNKNOWN {stim}  (side={side})"
        
                    print(line)
                    
                    continue
        
                # -------------------------
                # Phase 2 (Unsupervised training): sample + single paired comp
                # -------------------------
                if phase_num == 2:
                    s = tr.get("sample", "NA")
                    c = tr.get("single_comp", "NA")
                    side = tr.get("single_side", "NA")
        
                    print(f"Trial {tn:>3}{star}: TRAIN  S={s}  ->  C={c}  (side={side})")
                    continue
        
                # -------------------------
                # Phase 3 (Testing session): TRAIN (single comp) vs TEST (two comps)
                # -------------------------
                if phase_num == 3:
                    s = tr.get("sample", "NA")
        
                    if ttype == "train":
                        c = tr.get("single_comp", "NA")
                        side = tr.get("single_side", "NA")
                        print(f"Trial {tn:>3}{star}: TRAIN  S={s}  ->  C={c}  (side={side})")
        
                    elif ttype == "test":
                        L = tr.get("left_comp", "NA")
                        R = tr.get("right_comp", "NA")
                        correct = tr.get("correct_comp", "NA")
                        foil = tr.get("foil_comp", "NA")
        
                        # sanity check: label them as comps if they start with C
                        print(
                            f"Trial {tn:>3}{star}: TEST   S={s}  |  L={L}  R={R}  "
                            f"|  correct={correct}  foil={foil}"
                        )
                    else:
                        print(f"Trial {tn:>3}{star}: UNKNOWN_TTYPE={ttype}  raw={tr}")
                    continue
        
                # -------------------------
                # Phase 4 (Supervised training): always two comps, one correct
                # -------------------------
                if phase_num == 4:
                    s = tr.get("sample", "NA")
                    L = tr.get("left_comp", "NA")
                    R = tr.get("right_comp", "NA")
                    correct = tr.get("correct_comp", "NA")
                    # derive foil as the other one (if possible)
                    foil = "NA"
                    if correct != "NA" and L != "NA" and R != "NA":
                        foil = R if L == correct else L
        
                    print(
                        f"Trial {tn:>3}{star}: SUP    S={s}  |  L={L}  R={R}  "
                        f"|  correct={correct}  foil={foil}"
                    )
                    continue
        
                # Fallback for unexpected phases
                print(f"Trial {tn:>3}{star}: {ttype}  raw={tr}")
            
        if self.exp_phase_num in [0, 1]:
            self.max_trials = 160
        
            # Choose which half-set to use
            if self.exp_phase_num == 0:
                acclim_samples = self.sample_files[:8]      # S01–S08
                acclim_comps   = self.comparison_files[:8]  # C01–C08
            else:
                acclim_samples = self.sample_files[8:]      # S09–S16
                acclim_comps   = self.comparison_files[8:]  # C09–C16
        
            all_stims = acclim_samples + acclim_comps
            stim_seq  = cycle_shuffle(all_stims, self.max_trials)
        
            # Comparison side counterbalance: alternate L/R for every comparison trial
            next_comp_side = "left"
        
            self.stimuli_assignment_dict = {}
            for t, stim in enumerate(stim_seq, start=1):
                is_sample = stim.upper().startswith("S")
                if is_sample:
                    self.stimuli_assignment_dict[t] = {
                        "trial_type": "acclimation",
                        "stimulus": stim,
                        "stim_class": "sample",
                        "side": "center"
                    }
                else:
                    self.stimuli_assignment_dict[t] = {
                        "trial_type": "acclimation",
                        "stimulus": stim,
                        "stim_class": "comparison",
                        "side": next_comp_side
                    }
                    next_comp_side = "right" if next_comp_side == "left" else "left"
        
            pretty_print_trial_order(self.exp_phase_num, self.stimuli_assignment_dict)
                    
        if self.exp_phase_num == 2:
            self.max_trials = 128
        
            # 128 trials = 16 blocks of 8 samples
            # build_counterbalanced_train_trials uses pairs of blocks,
            # so 16 is perfect: each sample appears equally often left/right
            trials = build_counterbalanced_train_trials(
                self.phase23_samples,
                n_blocks=16,
                pair_map=self.pair_map
            )
        
            self.stimuli_assignment_dict = {i+1: tr for i, tr in enumerate(trials)}
            pretty_print_trial_order(self.exp_phase_num, self.stimuli_assignment_dict)
            
        if self.exp_phase_num == 3:
            # 16 initial training trials + 112 training + 28 probe = 156 total
            self.max_trials = 160
        
            # first 16 training trials = 2 blocks (counterbalanced)
            first16 = build_counterbalanced_train_trials(self.phase23_samples, n_blocks=2, pair_map=self.pair_map)
            
            # remaining 112 training trials = 14 blocks (counterbalanced across 2-block pairs)
            train112 = build_counterbalanced_train_trials(self.phase23_samples, n_blocks=14, pair_map=self.pair_map)
        
            # --- 3) build 32 probe trials
            
            probe32 = []
            
            probe_sample_seq = cycle_shuffle(self.phase23_samples, 32)  # 8-sample cycles
            
            # Optional: make foil selection cycle-y too (per sample), so foils aren’t overly repetitive
            foil_pools = {s: [] for s in self.phase23_samples}
            
            for s in probe_sample_seq:
                correct = self.pair_map[s]
            
                # Build/refill that sample's foil pool as a shuffled cycle of the 7 allowed foils
                if len(foil_pools[s]) == 0:
                    foil_pools[s] = [c for c in self.phase23_comps if c != correct]
                    shuffle(foil_pools[s])
            
                foil = foil_pools[s].pop()  # no-repeat foils (within that sample) until exhausted
            
                # randomize left/right positions
                if choice([True, False]):
                    left_comp, right_comp = correct, foil
                else:
                    left_comp, right_comp = foil, correct
            
                probe32.append({
                    "trial_type": "test",
                    "sample": s,
                    "sample_FR": self.draw_vr5_bounded_3_10(),  # NEW
                    "left_comp": left_comp,
                    "right_comp": right_comp,
                    "correct_comp": correct,
                    "foil_comp": foil
                })
            # --- 4) pseudorandomize remaining (112 train + 28 probe) ---
            remaining = interleave_with_spacing(train112, probe32, min_train_between_probes=1)
            trials = first16 + remaining
            
            self.stimuli_assignment_dict = {i+1: tr for i, tr in enumerate(trials)}
            
            pretty_print_trial_order(self.exp_phase_num, self.stimuli_assignment_dict)
            
        if self.exp_phase_num == 4:
            self.max_trials = 112
        
            all_samples = self.sample_files[:]  # S01–S16
        
            # Define the two “families”
            comps_A = self.comparison_files[:8]   # C01–C08
            comps_B = self.comparison_files[8:]   # C09–C16
        
            # Separate foil pools so you never cross families
            foil_pools = {"A": [], "B": []}
        
            def comp_family(correct_comp):
                # correct_comp like "C03.bmp" or "C12.bmp"
                n = int(correct_comp[1:3])
                return "A" if n <= 8 else "B"
        
            def get_next_foil(correct):
                fam = comp_family(correct)
        
                # refill that family pool as a full shuffled cycle
                if len(foil_pools[fam]) == 0:
                    foil_pools[fam] = (comps_A.copy() if fam == "A" else comps_B.copy())
                    shuffle(foil_pools[fam])
        
                # pull until not the correct comp
                for _ in range(len(foil_pools[fam])):
                    f = foil_pools[fam].pop()
                    if f != correct:
                        return f
        
                # fallback (shouldn't happen)
                return choice([c for c in (comps_A if fam == "A" else comps_B) if c != correct])
        
            trials = []
            for _ in range(7):  # 7 blocks × 16 = 112
                block = all_samples.copy()
                shuffle(block)
            
                # exactly 8 correct-left and 8 correct-right per block
                correct_sides = ["left"] * 8 + ["right"] * 8
                shuffle(correct_sides)
                side_map = {s: side for s, side in zip(block, correct_sides)}
            
                for s in block:
                    correct = self.pair_map[s]
                    foil = get_next_foil(correct)
            
                    if side_map[s] == "left":
                        left_comp, right_comp = correct, foil
                    else:
                        left_comp, right_comp = foil, correct
            
                    trials.append({
                        "trial_type": "supervised",
                        "sample": s,
                        "sample_FR": self.draw_vr5_bounded_3_10(),
                        "left_comp": left_comp,
                        "right_comp": right_comp,
                        "correct_comp": correct
                    })
        
            self.stimuli_assignment_dict = {i+1: tr for i, tr in enumerate(trials)}
            pretty_print_trial_order(self.exp_phase_num, self.stimuli_assignment_dict)


        ## Finally, start the recursive loop that runs the program:
        self.place_birds_in_box()
    
    def place_birds_in_box(self):
        # Default screen until birds are placed into the box and space bar is pressed.
        # After spacebar, the first ITI occurs prior to the first trial.
        self.root.bind("<space>", self.first_ITI)
        self.mastercanvas.create_text(
            512, 384,
            fill="white",
            font="Times 26 italic bold",
            text=(f"P035g \n Place bird in box, then press space \n "
                  f"Subject: {self.subject_ID} \n Phase: {self.exp_phase_name}")
        )
    
    def first_ITI(self, event):
        print("Spacebar pressed -- SESSION STARTED")
        self.root.unbind("<space>")
        self.clear_canvas()
        self.trial_stage = 0
        self.start_time = datetime.now()  # actual session start
    
        if not operant_box_version or self.subject_ID == "TEST":
            self.ITI_duration = 1 * 1000
            self.root.after(1, lambda: self.ITI())
        else:
            self.root.after(30000, lambda: self.ITI())
    
    # Orienting stimulus phase
    
    def orienting_phase(self):
        
        self.clear_canvas()
        self.trial_stage = 0
    
        # House light on during trial phases
        if operant_box_version and not self.light_HL_on_bool:
            rpi_board.write(house_light_GPIO_num, True)
            self.light_HL_on_bool = True
    
        # Background pecks
        self.mastercanvas.create_rectangle(
            0, 0, self.mainscreen_width, self.mainscreen_height,
            fill="black", outline="black", tag="bkgrd"
        )
        self.mastercanvas.tag_bind(
            "bkgrd", "<Button-1>",
            lambda event, event_type="background_peck": self.write_data(event, event_type)
        )
    
        # Center white square orienting stimulus
        x, y = 512, 384
        size = 60 
        self.mastercanvas.create_rectangle(
            x - size, y - size, x + size, y + size,
            fill="white", outline="white", tag="orient"
        )
        self.mastercanvas.tag_bind("orient", "<Button-1>", self.orient_peck)
    
    def orient_peck(self, event):
        self.write_data(event, "orient_peck")
        # Reset per-trial counters at trial start (safest place for it)
        self.sample_key_presses = 0
        self.comparison_key_presses = 0
        self.correct_comparison_key_presses = 0
        self.incorrect_comparison_key_presses = 0
        self.sample_phase()

    
    def sample_phase(self):
        self.clear_canvas()
        self.trial_stage = 1
    
        # House light on during trial phases
        if operant_box_version and not self.light_HL_on_bool:
            rpi_board.write(house_light_GPIO_num, True)
            self.light_HL_on_bool = True
    
        # Background pecks
        self.mastercanvas.create_rectangle(
            0, 0, self.mainscreen_width, self.mainscreen_height,
            fill="black", outline="black", tag="bkgrd"
        )
        self.mastercanvas.tag_bind(
            "bkgrd", "<Button-1>",
            lambda event, event_type="background_peck": self.write_data(event, event_type)
        )
    
        trial_info = self.stimuli_assignment_dict.get(self.current_trial_counter, None)
        if trial_info is None:
            print(f"ERROR: No trial info for trial {self.current_trial_counter}. Ending session.")
            self.exit_program("event")
            return

        # Phase 1 (Acclimation): show S stimuli in center; C stimuli left/right; require 2 pecks
        if self.exp_phase_num in [0, 1]:
            stim_name  = trial_info["stimulus"]
            stim_class = trial_info.get("stim_class", "NA")  # "sample" or "comparison"
            side       = trial_info.get("side", "center")    # "center" / "left" / "right"
        
            stim_path = os_path.join(self.stimuli_path, stim_name)
            self.sample_FR = 2  # acclimation requirement
        
            # For logging consistency (not required, but fine)
            self.sample_name = stim_name
        
            # Choose coordinates by class/side
            if stim_class == "sample" or side == "center":
                x, y = 512, 405
                if self.subject_ID == "Darwin":
                    y = 460
            else:
                # comparison position
                if side == "left":
                    x, y = 160, 550
                else:
                    x, y = 864, 550
    
        # Phase 2–4: show sample centrally; observing_req pecks
        else:
            stim_name = trial_info["sample"]
            stim_path = os_path.join(self.stimuli_path, stim_name)
            # Phase 2–4: sample centrally; pull per-trial sample_FR from dict
            self.sample_FR = int(trial_info.get("sample_FR", 5))  # NEW (fallback 5 if missing)
            self.sample_name = stim_name
    
            # For logging consistency
            self.sample_name = stim_name

        # Load and display sample image
        selected_image = Image.open(stim_path)
        self.image = ImageTk.PhotoImage(selected_image)
        
        # -------------------------------------------------
        # Coordinates:
        # - Phase 1 uses whatever x,y computed above
        # - Phases 2–4 always center sample
        if self.exp_phase_num not in [0, 1]:
            x, y = 512, 405
            if self.subject_ID == "Darwin":
                y = 460
        # else: keep x,y already computed in Phase 1 logic
        
        oval_radius = 85
        self.mastercanvas.create_oval(
            x - oval_radius, y - oval_radius,
            x + oval_radius, y + oval_radius,
            fill="black", tag="sample_button"
        )
        self.mastercanvas.create_image(
            x, y, image=self.image, anchor="center", tag="sample_button"
        )
        self.mastercanvas.tag_bind("sample_button", "<Button-1>", self.sample_key_press)

    
    def sample_key_press(self, event):
        self.write_data(event, "sample_key_press")
        self.trial_stage = 1
        self.sample_key_presses += 1
    
        # Phase 1 acclimation: FR2 then reinforce immediately (no comparison stage)
        if self.exp_phase_num in [0, 1]:
            if self.sample_key_presses >= 2:
                self.reinforcement_phase()
            else:
                self.sample_phase()
            return
    
        # Phases 2–4: after sample requirement, go to comparisons
        if self.sample_key_presses >= int(self.sample_FR):
            self.comparison_FR = 1  # comparisons are always FR1 (DE-style)
            self.comparison_phase()
        else:
            self.sample_phase()

    # Comparison phase (Unsupervised / Test / Supervised)
        
    def comparison_phase(self):
        self.clear_canvas()
        self.trial_stage = 2
    
        # Track trial start for this stage
        if self.current_trial_counter != self.last_written_trial_num:
            self.comparison_start_time = datetime.now()
            self.last_written_trial_num = self.current_trial_counter
    
        # Background pecks
        self.mastercanvas.create_rectangle(
            0, 0, self.mainscreen_width, self.mainscreen_height,
            fill="black", outline="black", tag="bkgrd"
        )
        self.mastercanvas.tag_bind(
            "bkgrd", "<Button-1>",
            lambda event, event_type="background_peck": self.write_data(event, event_type)
        )
    
        trial = self.stimuli_assignment_dict.get(self.current_trial_counter, None)
        if trial is None:
            print(f"ERROR: No trial dict for trial {self.current_trial_counter}")
            self.exit_program("event")
            return
    
        ttype = trial.get("trial_type", "train")

        # -------------------------s
        # Coordinates
        # -------------------------
        left_x, left_y = 160, 550
        right_x, right_y = 864, 550
        oval_radius = 85
    
        # Helper to draw a comp key
        def draw_comp(tag, stim_name, x, y):
            img = ImageTk.PhotoImage(Image.open(os_path.join(self.stimuli_path, stim_name)))
            setattr(self, f"{tag}_image", img)  # keep reference
            self.mastercanvas.create_oval(
                x - oval_radius, y - oval_radius,
                x + oval_radius, y + oval_radius,
                fill="black", tag=tag
            )
            self.mastercanvas.create_image(x, y, image=img, anchor="center", tag=tag)
            self.mastercanvas.tag_bind(tag, "<Button-1>", self.comp_key_press)
    
        # -------------------------
        # PHASE 2: Unsupervised training (single comparison)
        # -------------------------
        if self.exp_phase_num == 2:
            comp_name = trial["single_comp"]
            side = trial["single_side"]
            x, y = (left_x, left_y) if side == "left" else (right_x, right_y)
    
            draw_comp("single_comp", comp_name, x, y)
            self._draw_inactive_sample(trial["sample"])
            return
    
        # -------------------------
        # PHASE 3: Testing session
        #   - train: single comp
        #   - test: two comps
        # -------------------------
        
        if self.exp_phase_num == 3:
            if ttype == "train":
                comp_name = trial["single_comp"]
                side = trial["single_side"]
                x, y = (left_x, left_y) if side == "left" else (right_x, right_y)
    
                draw_comp("single_comp", comp_name, x, y)
                self._draw_inactive_sample(trial["sample"])
                return
    
            elif ttype == "test":
                # two-choice
                L = trial["left_comp"]
                R = trial["right_comp"]
    
                draw_comp("left_comp", L, left_x, left_y)
                draw_comp("right_comp", R, right_x, right_y)
                self._draw_inactive_sample(trial["sample"])
                return
    
            else:
                print(f"ERROR: Unknown trial_type in Phase 3: {ttype}")
                self.exit_program("event")
                return
    
        # -------------------------
        # PHASE 4: Supervised training (two comparisons)
        # -------------------------
        if self.exp_phase_num == 4:
            L = trial["left_comp"]
            R = trial["right_comp"]
    
            draw_comp("left_comp", L, left_x, left_y)
            draw_comp("right_comp", R, right_x, right_y)
            self._draw_inactive_sample(trial["sample"])
            return
    
    # Keep sample visible but inactive during comparisons

    def _draw_inactive_sample(self, sample_name):
        stim_path = os_path.join(self.stimuli_path, sample_name)
        img = ImageTk.PhotoImage(Image.open(stim_path))
        self.inactive_sample_image = img  # keep reference
    
        sx, sy = 512, 405
        if self.subject_ID == "Darwin":
            sy = 460
    
        oval_radius = 85
        self.mastercanvas.create_oval(
            sx - oval_radius, sy - oval_radius,
            sx + oval_radius, sy + oval_radius,
            fill="black", tag="inactive_sample"
        )
        self.mastercanvas.create_image(sx, sy, image=self.inactive_sample_image, anchor="center", tag="inactive_sample")
        self.mastercanvas.tag_bind(
            "inactive_sample", "<Button-1>",
            lambda event, event_type="inactive_sample_key_press": self.write_data(event, event_type)
        )

 ###### peck counter (comparison)
    
    def comp_key_press(self, event):
        """
        Handles pecks to comparison stimuli across:
          - Phase 2 unsupervised (single comparison)
          - Phase 3 testing (single training OR 2-choice test)
          - Phase 4 supervised (2-choice)
        Rule: comparison peck requirement == sample peck requirement (self.comparison_FR)
        """
        tags = self.mastercanvas.gettags("current")
        if not tags:
                return
        clicked_tag = tags[0]
    
        # Log which stimulus was pecked
        if clicked_tag == "single_comp":
            self.write_data(event, "comparison_key_press")
            chosen_side = "single"
        elif clicked_tag == "left_comp":
            self.write_data(event, "left_comp_press")
            chosen_side = "left"
        elif clicked_tag == "right_comp":
            self.write_data(event, "right_comp_press")
            chosen_side = "right"
        else:
            self.write_data(event, "comparison_key_press")
            chosen_side = "unknown"
    
        self.trial_stage = 2
    
        # If we're in a 2-choice phase (Phase 3 test trials or Phase 4 supervised),
        # we must "lock in" the chosen side and only count pecks on that chosen key.
        trial = self.stimuli_assignment_dict[self.current_trial_counter]
        ttype = trial.get("trial_type", "train")
    
        two_choice_now = (
            (self.exp_phase_num == 3 and ttype == "test") or  # Phase 3 test trial
            (self.exp_phase_num == 4)                         # Phase 4 supervised (always 2-choice)
        )
    
        if two_choice_now:
            # On the first peck of the comparison stage, lock in the chosen key
            if getattr(self, "chosen_comp_tag", None) is None:
                if chosen_side in ("left", "right"):
                    self.chosen_comp_tag = chosen_side  # "left" or "right"
                    self.choice_lock_time = datetime.now()
                    if getattr(self, "comparison_start_time", None) is not None:
                        self.choice_latency = (self.choice_lock_time - self.comparison_start_time).total_seconds()
                    self.write_data(None, f"choice_locked_{self.chosen_comp_tag}")
                else:
                    # If somehow we didn't click left/right in a 2-choice trial, ignore
                    return
    
            # Only count pecks if they are on the chosen key
            if chosen_side != self.chosen_comp_tag:
                # Still log it (above), but do not advance the FR
                return
    
        # Count pecks toward the requirement
        self.comparison_key_presses += 1
    
        if self.comparison_key_presses >= int(self.comparison_FR):
            self.choice_complete_time = datetime.now()
            if getattr(self, "choice_lock_time", None) is not None:
                self.choice_duration = (self.choice_complete_time - self.choice_lock_time).total_seconds()
            self.clear_canvas()
    
            # Decide what happens after meeting the comparison requirement
            # Phase 2: single comp -> reinforce
            if self.exp_phase_num == 2:
                self.root.after(250, self.reinforcement_phase)
    
            # Phase 3:
            #   - training trials (single comp) -> reinforce
            #   - test trials (2-choice) -> both choices reinforced
            elif self.exp_phase_num == 3:
                self.root.after(250, self.reinforcement_phase)
    
            # Phase 4 supervised: after FR on chosen key, check correct vs foil
            elif self.exp_phase_num == 4:
                self.root.after(250, self._finish_supervised_choice)
    
            else:
                # Fallback
                self.root.after(250, self.reinforcement_phase)
    
        else:
            self.comparison_phase()


    def _finish_supervised_choice(self):
        """
        After the bird completes the FR on the chosen comparison in Phase 4,
        determine correctness and route to reinforcement or correction.
        """
        trial = self.stimuli_assignment_dict[self.current_trial_counter]
    
        # Which stimulus did the bird "choose"?
        chosen_tag = getattr(self, "chosen_comp_tag", None)  # "left" or "right"
        if chosen_tag == "left":
            chosen_stim = trial["left_comp"]
        elif chosen_tag == "right":
            chosen_stim = trial["right_comp"]
        else:
            self.write_data(None, "choice_error_no_locked_tag")
            self.in_correction = True
            self.ITI()
            return
    
        # Correctness check
        correct_stim = trial["correct_comp"]  # must exist in Phase 4 trial dict
    
        if chosen_stim == correct_stim:
            self.in_correction = False
            self.write_data(None, "correct_choice")
            self.reinforcement_phase()
        else:
            # Correction trials ONLY in Phase 4
            if self.exp_phase_num == 4:
                self.in_correction = True
                self.write_data(None, "incorrect_choice")
                self.start_correction_trial()
            else:
                self.in_correction = False
                self.write_data(None, "incorrect_choice")
                self.ITI()
    
    def start_correction_trial(self):
        """
        Repeat the SAME trial after an incorrect response in Phase 4.
        This does not advance the trial counter; it just restarts the ITI -> orient -> sample.
        """
        # Mark that we're in correction mode (useful for logging later if you want)
        self.in_correction = True
    
        # Reset within-trial counters
        self.sample_key_presses = 0
        self.comparison_key_presses = 0
        self.chosen_comp_tag = None
    
        # Go to ITI (same ITI duration), but do NOT increment trial counter in ITI when in correction
        self.ITI()
        
    
    # Reinforcement 

    def reinforcement_phase(self):
        self.trial_stage = 3
        self.reinforced_trial_counter += 1
        self.clear_canvas()
        self.write_data(None, "reinforcement_provided")
    
        if not operant_box_version or self.subject_ID == "TEST":
            self.mastercanvas.create_text(
                512, 384,
                fill="white",
                font="Times 26 italic bold",
                text=f"Reinforcement TIME ({int(self.hopper_duration/1000)} s)"
            )
    
        if operant_box_version:
            rpi_board.write(house_light_GPIO_num, False)
            rpi_board.write(hopper_light_GPIO_num, True)
            rpi_board.set_servo_pulsewidth(servo_GPIO_num, hopper_up_val)
    
        # End check
        if self.current_trial_counter == self.max_trials:
            self.root.after(self.hopper_duration, lambda: self.exit_program("event"))
        else:
            self.root.after(self.hopper_duration, lambda: self.ITI())

    def ITI(self):
    # In this part of a trial, it is ITI
    
        self.clear_canvas()
        self.trial_stage = 0
        self.choice_lock_time = None      # when first comparison peck locks choice (2-choice trials)
        self.choice_complete_time = None  # when comparison FR requirement is completed
        self.choice_latency = "NA"
        self.choice_duration = "NA"
    
        # Make sure pecks during ITI are saved
        self.mastercanvas.create_rectangle(
            0, 0,
            self.mainscreen_width,
            self.mainscreen_height,
            fill="black",
            outline="black",
            tag="bkgrd"
        )
        self.mastercanvas.tag_bind(
            "bkgrd",
            "<Button-1>",
            lambda event, event_type="ITI_peck": self.write_data(event, event_type)
        )
    
        # --- Session end checks ---
        if self.current_trial_counter != 0 and self.current_trial_counter not in self.stimuli_assignment_dict:
            self.exit_program("event")
            return
    
        if self.current_trial_counter == self.max_trials + 1:
            print("&&& Trial max reached &&&")
            self.exit_program("event")
            return
    
        # Print text on screen if a test
        if not operant_box_version or self.subject_ID == "TEST":
            self.mastercanvas.create_text(
                512, 384,
                fill="white",
                font="Times 26 italic bold",
                text=f"ITI ({int(self.ITI_duration/1000)} sec.)"
            )
    
        # Hardware off during ITI
        if operant_box_version:
            rpi_board.write(hopper_light_GPIO_num, False)
            rpi_board.set_servo_pulsewidth(servo_GPIO_num, hopper_down_val)
            rpi_board.write(house_light_GPIO_num, False)
    
        self.light_HL_on_bool = False
    
        # If we are correcting (Phase 4), do NOT advance trial number
        
        in_correction = getattr(self, "in_correction", False) and self.exp_phase_num == 4
    
        if not in_correction:
            self.current_trial_counter += 1
        else:
            # stay on the same trial number; do NOT change current_trial_counter during correction
            pass
    
        # If we're not correcting, validate we haven't run past the dict
        if not in_correction:
            if self.current_trial_counter != 0 and self.current_trial_counter not in self.stimuli_assignment_dict:
                self.exit_program("event")
                return
    
        # Reset trial counters/state
        self.comparison_key_presses = 0
        self.correct_comparison_key_presses = 0
        self.incorrect_comparison_key_presses = 0
        self.sample_key_presses = 0
        self.trial_stage = 0
        self.trial_start = time()
        self.last_written_trial_num = None
        self.comparison_start_time = None
    
        # Reset choice lock for 2-choice trials
        self.chosen_comp_tag = None
    
        # ---------------------------------------------------------
        # NEW: set per-trial "what stimuli are we on" for logging
        # (update these blocks to match your new trial dict keys)
        # ---------------------------------------------------------
        if self.current_trial_counter == 0:
            trial_info = {}
        else:
            trial_info = self.stimuli_assignment_dict.get(self.current_trial_counter, {})
    
        # Default values
        self.sample_name = trial_info.get("sample", trial_info.get("stimulus", "NA"))
    
        # For Phase 2/3 training (single comparison)
        if self.exp_phase_num in [2, 3] and trial_info.get("trial_type", "train") == "train":
            self.comparison_name = trial_info.get("single_comp", "NA")
            self.foil_name = "NA"
            self.comparison_location = trial_info.get("single_side", "NA")
    
        # For Phase 3 test and Phase 4 supervised (two comparisons)
        elif self.exp_phase_num in [3, 4]:
            self.comparison_name = trial_info.get("left_comp", "NA")   # for your old logger fields
            self.foil_name = trial_info.get("right_comp", "NA")
            self.comparison_location = "NA"
    
        else:
            self.comparison_name = "NA"
            self.foil_name = "NA"
            self.comparison_location = "NA"
    
        # Also write data (writes previous-trial data + any end flags)
        self.write_comp_data(False)
    
        # ---------------------------------------------------------
        # IMPORTANT: next stage should be orienting_phase, not sample_phase
        # ---------------------------------------------------------
        self.root.after(self.ITI_duration, self.orienting_phase)
    
        print(f"\n{'*'*30} Trial {self.current_trial_counter} begins {'*'*30}")
        print(f"{'Event Type':>30} | Xcord. Ycord. | Stage | Session Time")
    
        # If we were in correction, keep flag True until the bird gets it correct.
        # We DO NOT clear it here.
        # It should be cleared only when a correct choice occurs in Phase 4:
        #   in _finish_supervised_choice(): if correct -> self.in_correction = False

        
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
        """
        Event-level logger.
    
        Goal: every row carries the exact stimulus filenames relevant to the CURRENT trial,
        rather than writing separate "*_presented" events.
    
        Columns written (must match your header_list order if you updated it):
          SessionTime, ExpPhase, Subject, Xcord, Ycord, Event,
          TrialSubStage, TrialType, TrialNum, ReinTrialNum, SampleFR, ComparisonFR,
          SampleFile, PairedCompFile, FoilCompFile, LeftCompFile, RightCompFile,
          SingleCompFile, SingleSide, ChosenCompFile, ChosenSide,
          IsPairedChoice, Correctness,
          TrialTime, ChoiceLatency, ChoiceDuration, InCorrection, Date
        """
        # Skip writing data if current_trial_counter is 0 (dictionary access invalid)
        if self.current_trial_counter == 0:
            return
    
        # Event coordinates
        if event is not None:
            x, y = event.x, event.y
        else:
            x, y = "NA", "NA"
    
        print(f"{outcome:>30} | x: {x: ^3} y: {y:^3} | {self.trial_stage:^5} | {str(datetime.now() - self.start_time)}")
    
        # Grab current trial info safely
        trial_info = self.stimuli_assignment_dict.get(self.current_trial_counter, {})
        trial_type = trial_info.get("trial_type", "NA")
    
        # ---- Core trial identity ----
        SampleFile = trial_info.get("sample", trial_info.get("stimulus", "NA"))
    
        # Comparison requirements (comparison_FR is set to sample_FR when sample requirement is met)
        SampleFR = getattr(self, "sample_FR", "NA")
        ComparisonFR = getattr(self, "comparison_FR", "NA")
    
        # ---- Initialize all stimulus fields to NA ----
        PairedCompFile = "NA"
        FoilCompFile   = "NA"
        LeftCompFile   = "NA"
        RightCompFile  = "NA"
        SingleCompFile = "NA"
        SingleSide     = "NA"
    
        # ---- Choice fields ----
        ChosenSide     = getattr(self, "chosen_comp_tag", None) or "NA"
        ChosenCompFile = "NA"
        IsPairedChoice = "NA"
        Correctness    = "NA"
    
        # Correction flag
        InCorrection = bool(getattr(self, "in_correction", False))
    
        # Choice timing fields (populated elsewhere when you lock choice / finish FR)
        ChoiceLatency  = getattr(self, "choice_latency", "NA")
        ChoiceDuration = getattr(self, "choice_duration", "NA")
    
        # ---- Phase-specific stimulus mapping ----
        # Phase 1 (Acclimation): only a single center stimulus; treat it as "SampleFile"
        if self.exp_phase_num in [0, 1]:
            trial_type = "acclimation"
        
            stim_name  = trial_info.get("stimulus", "NA")
            stim_class = trial_info.get("stim_class", "NA")
            side       = trial_info.get("side", "NA")
        
            if stim_class == "sample" or stim_name.upper().startswith("S"):
                # Sample in center
                SampleFile = stim_name
            else:
                # Comparison on left/right
                SampleFile = "NA"
                SingleCompFile = stim_name
                SingleSide = side
        
                # Optional: also populate Left/Right columns
                if side == "left":
                    LeftCompFile = stim_name
                elif side == "right":
                    RightCompFile = stim_name
    
        # Phase 2 (Unsupervised training): sample + SINGLE paired comparison (left or right)
        elif self.exp_phase_num == 2:
            trial_type = "train"
            SingleCompFile = trial_info.get("single_comp", "NA")
            SingleSide     = trial_info.get("single_side", "NA")
    
            PairedCompFile = SingleCompFile
            # no foil in unsupervised training
            if SingleSide == "left":
                LeftCompFile = SingleCompFile
            elif SingleSide == "right":
                RightCompFile = SingleCompFile
    
            # If you ever want to count "choice" on single-comp trials:
            if ChosenSide == "single":
                ChosenCompFile = SingleCompFile
    
        # Phase 3 (Testing session): mixture of training (single comp) and test (two comps)
        elif self.exp_phase_num == 3:
            trial_type = trial_info.get("trial_type", "train")
    
            if trial_type == "train":
                SingleCompFile = trial_info.get("single_comp", "NA")
                SingleSide     = trial_info.get("single_side", "NA")
                PairedCompFile = SingleCompFile
    
                if SingleSide == "left":
                    LeftCompFile = SingleCompFile
                elif SingleSide == "right":
                    RightCompFile = SingleCompFile
    
                if ChosenSide == "single":
                    ChosenCompFile = SingleCompFile
    
            elif trial_type == "test":
                LeftCompFile  = trial_info.get("left_comp", "NA")
                RightCompFile = trial_info.get("right_comp", "NA")
    
                PairedCompFile = trial_info.get("correct_comp", "NA")
                FoilCompFile   = trial_info.get("foil_comp", "NA")
    
                # Determine chosen comp (only meaningful if you locked choice on left/right)
                if ChosenSide == "left":
                    ChosenCompFile = LeftCompFile
                elif ChosenSide == "right":
                    ChosenCompFile = RightCompFile
    
                # Paired vs unpaired choice
                if ChosenCompFile != "NA" and PairedCompFile != "NA":
                    IsPairedChoice = (ChosenCompFile == PairedCompFile)
    
            else:
                # unexpected label
                pass
    
        # Phase 4 (Supervised training): always two comps (paired vs foil), differential reinforcement
        elif self.exp_phase_num == 4:
            trial_type = "supervised"
    
            LeftCompFile  = trial_info.get("left_comp", "NA")
            RightCompFile = trial_info.get("right_comp", "NA")
            PairedCompFile = trial_info.get("correct_comp", "NA")
    
            # Derive foil as "the other one"
            if LeftCompFile != "NA" and RightCompFile != "NA" and PairedCompFile != "NA":
                FoilCompFile = RightCompFile if LeftCompFile == PairedCompFile else LeftCompFile
    
            # Determine chosen comp
            if ChosenSide == "left":
                ChosenCompFile = LeftCompFile
            elif ChosenSide == "right":
                ChosenCompFile = RightCompFile
    
            # Correctness
            if ChosenCompFile != "NA" and PairedCompFile != "NA":
                Correctness = "correct" if (ChosenCompFile == PairedCompFile) else "incorrect"
    
        # ---- Trial time (relative to trial_start, keeping your existing logic) ----
        trial_time = "NA"
        if self.trial_start is not None:
            trial_time = round((time() - self.trial_start - (self.ITI_duration / 1000)), 5)
    
        # ---- Append row ----
        self.session_data_frame.append([
            str(datetime.now() - self.start_time),  # SessionTime
            self.exp_phase,                         # ExpPhase
            self.subject_ID,                        # Subject
            x,                                      # Xcord
            y,                                      # Ycord
            outcome,                                # Event
            self.trial_stage,                       # TrialSubStage
            trial_type,                             # TrialType
            self.current_trial_counter,             # TrialNum
            self.reinforced_trial_counter,          # ReinTrialNum
            SampleFR,                               # SampleFR
            ComparisonFR,                           # ComparisonFR
    
            SampleFile,                             # SampleFile
            PairedCompFile,                         # PairedCompFile
            FoilCompFile,                           # FoilCompFile
            LeftCompFile,                           # LeftCompFile
            RightCompFile,                          # RightCompFile
            SingleCompFile,                         # SingleCompFile
            SingleSide,                             # SingleSide
    
            ChosenCompFile,                         # ChosenCompFile
            ChosenSide,                             # ChosenSide
            IsPairedChoice,                         # IsPairedChoice
            Correctness,                            # Correctness
    
            trial_time,                             # TrialTime
            ChoiceLatency,                          # ChoiceLatency
            ChoiceDuration,                         # ChoiceDuration
            InCorrection,                           # InCorrection
            date.today()                            # Date
        ])

        
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
            subject_folder = f"{self.data_folder_directory}/{self.subject_ID}"
            if not os_path.isdir(subject_folder):
                mkdir(subject_folder)
            myFile_loc = f"{self.data_folder_directory}/{self.subject_ID}/{self.subject_ID}_{self.start_time.strftime('%Y-%m-%d_%H.%M.%S')}_P035g_data-Phase{self.exp_phase_num}.csv" # location of written .csv
            
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