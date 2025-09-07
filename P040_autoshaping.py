#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Autoshaping procedure for P040

Trials begin with a circle stimulus. 
Pecks to the circle stimulus on a VR5 schedule result in reinforcement (4s food). 
Instrumental pecks advance the trial. 
60 trials per session.
"""

from csv import writer, QUOTE_MINIMAL
from datetime import datetime, date
from sys import setrecursionlimit, path as sys_path
from tkinter import Toplevel, Canvas, Tk, Label, Button, StringVar, OptionMenu, IntVar, Radiobutton
from time import sleep
from os import path as os_path
import os, random

# --- Box or test version ---
if os_path.expanduser('~').split("/")[2] == "blaisdelllab":
    operant_box_version = True
    print("*** Running operant box version ***\n")
else:
    operant_box_version = False
    print("*** Running test version (no hardware) ***\n")

# --- Hardware setup (only if on Pi) ---
try:
    if operant_box_version:
        import pigpio, csv
        servo_GPIO_num = 2
        hopper_light_GPIO_num = 13
        rpi_board = pigpio.pi()
        rpi_board.set_mode(servo_GPIO_num, pigpio.OUTPUT)
        rpi_board.set_mode(hopper_light_GPIO_num, pigpio.OUTPUT)
        rpi_board.set_PWM_frequency(servo_GPIO_num, 50)
        hopper_vals_csv_path = str(os_path.expanduser('~') + "/Desktop/Box_Info/Hopper_vals.csv")
        up_down_table = list(csv.reader(open(hopper_vals_csv_path)))
        hopper_up_val = int(up_down_table[1][0])
        hopper_down_val = int(up_down_table[1][1])
except ModuleNotFoundError:
    input("ERROR: Cannot find hopper hardware! Check desktop.")

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

# --- Control panel ---
class ExperimenterControlPanel(object):
    def __init__(self):
        self.doc_directory = str(os_path.expanduser('~')) + "/Documents/"
        if operant_box_version:
            self.data_folder_directory = "/home/blaisdelllab/Desktop/Data/P040/"
        else:
            self.data_folder_directory = os_path.expanduser('~/Desktop/Experiments/P040/data')

        self.control_window = Tk()
        self.control_window.title("P040 Autoshaping Control Panel")

        # Subject ID
        self.pigeon_name_list = ["Thoth","Jagger","Durrell","Vonnegut"]
        self.pigeon_name_list.sort()
        self.pigeon_name_list.insert(0, "TEST")
        Label(self.control_window, text="Pigeon Name:").pack()
        self.subject_ID_variable = StringVar(self.control_window)
        self.subject_ID_variable.set("Subject")
        OptionMenu(self.control_window,
                   self.subject_ID_variable,
                   *self.pigeon_name_list,
                   command=self.set_pigeon_ID).pack()

        # Record data?
        Label(self.control_window, text="Record data?").pack()
        self.record_data_variable = IntVar()
        Radiobutton(self.control_window, variable=self.record_data_variable,
                    text="Yes", value=True).pack()
        Radiobutton(self.control_window, variable=self.record_data_variable,
                    text="No", value=False).pack()
        self.record_data_variable.set(True)

        # Start button
        Button(self.control_window, text='Start program', bg="green2",
               command=self.build_chamber_screen).pack()

        self.control_window.mainloop()

    def set_pigeon_ID(self, pigeon_name):
        if not os_path.isdir(self.data_folder_directory + pigeon_name):
            os.makedirs(os.path.join(self.data_folder_directory, pigeon_name), exist_ok=True)
            print(f"\n ** NEW DATA FOLDER FOR {pigeon_name.upper()} CREATED **")

    def build_chamber_screen(self):
        if self.subject_ID_variable.get() in self.pigeon_name_list:
            print("Operant Box Screen Built")
            self.MS = MainScreen(
                str(self.subject_ID_variable.get()),
                self.record_data_variable.get(),
                self.data_folder_directory
            )
        else:
            print("\n ERROR: Input Correct Pigeon ID Before Starting Session")


# --- MainScreen ---
class MainScreen(object):
    def __init__(self, subject_ID, record_data, data_folder_directory):
        self.subject_ID = subject_ID
        self.record_data = record_data
        self.data_folder_directory = data_folder_directory

        # Tkinter setup
        self.root = Toplevel()
        self.root.title("Autoshaping Task")
        self.mainscreen_height, self.mainscreen_width = 768, 1024
        self.root.bind("<Escape>", self.exit_program)

        if operant_box_version: 
            self.cursor_visible = True 
            self.change_cursor_state() 
            self.root.bind("<c>", lambda event: self.change_cursor_state()) 
            self.root.geometry(f"{self.mainscreen_width}x{self.mainscreen_height}+1920+0")
            self.root.attributes('-fullscreen', True)
            self.mastercanvas = Canvas(self.root, bg="grey",
                                       height=self.mainscreen_height,
                                       width=self.mainscreen_width)
            self.mastercanvas.pack()   # <-- you were missing this
        else: 
            self.mastercanvas = Canvas(self.root,
                                       bg="grey",
                                       height=self.mainscreen_height,
                                       width=self.mainscreen_width)
            self.mastercanvas.pack()

        # Session vars
        self.trial_counter = 0
        self.max_trials = 60
        self.peck_counter = 0
        self.requirement = self.VR_schedule(5)
        self.hopper_duration = 5000
        self.ITI_duration = 15000
        self.start_time = datetime.now()
        self.date = date.today().strftime("%y-%m-%d")
        self.session_data_frame = [["SessionTime", "Subject", "Trial_Num", "Event",
                            "Xcord", "Ycord", "TrialSubStage",
                            "PeckCount", "VR_Requirement", "Date"]]
        self.place_birds_in_box()

    def VR_schedule(self, mean=5):
        return random.randint(3, 8)  # bounded VR schedule


    def place_birds_in_box(self):
        self.mastercanvas.create_text(512, 384, fill="white",
                                      font="Times 26 italic bold",
                                      text="Autoshaping \n Place bird in box, then press space")
        self.root.bind("<space>", self.first_ITI)

    def first_ITI(self, event):
        print("Session started")
        self.write_data(None, "SessionStarts")   
        self.root.after(1000, self.ITI)

    def ITI(self):
        self.mastercanvas.delete("all")
        if self.trial_counter >= self.max_trials:
            self.exit_program()
            return

        self.trial_counter += 1
        self.peck_counter = 0
        self.requirement = self.VR_schedule()

        print(f"\n{'*' * 30} Trial {self.trial_counter} begins {'*' * 30}")
        print(f"{'Event Type':>30} | Xcord. Ycord. | Stage | Session Time")

        # ITI screen clickable for logging ITI pecks
        self.mastercanvas.create_rectangle(0, 0, self.mainscreen_width, self.mainscreen_height,
                                           fill="grey", outline="grey", tag="bkgrd")
        self.mastercanvas.tag_bind("bkgrd", "<Button-1>",
                                   lambda event: self.write_data(event, "ITI_peck"))

        if self.subject_ID == "TEST":
            self.ITI_duration = 1000
            self.mastercanvas.create_text(512, 384,
                                          text=f"ITI ({int(self.ITI_duration/1000)} sec.)",
                                          fill="white",
                                          font="Times 26 italic bold")
        else:
            self.ITI_duration = 15000

        self.root.after(self.ITI_duration, self.start_trial)

    def start_trial(self):
        self.mastercanvas.delete("all")

        # Foreground (white) circle coordinates
        key_coord_list = [400, 300, 600, 500]

        # Background clickable area for background pecks
        self.mastercanvas.create_rectangle(0, 0, self.mainscreen_width, self.mainscreen_height,
                                           fill="grey", outline="grey", tag="bkgrd")
        self.mastercanvas.tag_bind("bkgrd", "<Button-1>",
                                   lambda event: self.write_data(event, "background_peck"))

        # Background "outline" circle (25px larger)
        outline_size = 25
        outline_coords_list = [
            key_coord_list[0] - outline_size,
            key_coord_list[1] - outline_size,
            key_coord_list[2] + outline_size,
            key_coord_list[3] + outline_size
        ]
        self.mastercanvas.create_oval(*outline_coords_list,
                                      fill="grey", outline="grey", tag="bg_circle")
        self.mastercanvas.tag_bind("bg_circle", "<Button-1>", self.register_peck)

        # Foreground circle
        self.mastercanvas.create_oval(*key_coord_list,
                                      fill="white", outline="white", tag="circle")
        self.mastercanvas.tag_bind("circle", "<Button-1>", self.register_peck)

        print(f"Trial {self.trial_counter} started, VR req = {self.requirement}")

    def register_peck(self, event):
        self.peck_counter += 1
        self.write_data(event, "circle_peck")
        if self.peck_counter >= self.requirement:
            self.mastercanvas.tag_unbind("circle", "<Button-1>")
            self.mastercanvas.tag_unbind("bg_circle", "<Button-1>")
            self.reinforcement_phase()

    def reinforcement_phase(self):
        self.write_data(None, "reinforcement_provided")
        self.mastercanvas.delete("all")
        if self.subject_ID == "TEST":
            self.mastercanvas.create_text(512, 384,
                                          text=f"Reinforcement ({self.hopper_duration/1000}s)",
                                          fill="white", font="Times 26 italic bold")
        
        # --- Real hardware actions if running in operant box version ---
        if operant_box_version:
            rpi_board.write(hopper_light_GPIO_num, True)       # Turn on hopper light
            rpi_board.set_servo_pulsewidth(servo_GPIO_num,
                                           hopper_up_val)      # Raise hopper to UP position
    
        # Schedule hopper return down after duration
        def end_reinforcement():
            if operant_box_version:
                rpi_board.write(hopper_light_GPIO_num, False)  # Turn off hopper light
                rpi_board.set_servo_pulsewidth(servo_GPIO_num,
                                               hopper_down_val) # Lower hopper to DOWN position
            self.ITI()
    
        self.root.after(self.hopper_duration, end_reinforcement)

        # %% Outside of the main loop functions, there are several additional
    # repeated functions that are called either outside of the loop or 
    # multiple times across phases.
    
    def clear_canvas(self):

        self.mastercanvas.delete("all")  # This removes all elements from the canvas
                    

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

                rpi_board.write(hopper_light_GPIO_num, False)  # Turn off hopper light

                rpi_board.set_servo_pulsewidth(servo_GPIO_num, hopper_down_val)  # Set hopper to down state

                rpi_board.stop()  # Stop the Raspberry Pi GPIO board

                # root.after_cancel(AFTER)

                if not self.cursor_visible:

                    self.change_cursor_state()  # Turn cursor back on, if applicable

            self.write_comp_data(True)  # Write data for the end of session

            if self.root.winfo_exists():  # Check if the window still exists

                self.root.destroy()  # Destroy Canvas

            print("\n GUI window exited")

            

        self.clear_canvas()

        other_exit_funcs()

        print("\n You may now exit the terminal and operator windows now.")
    
    def write_data(self, event, outcome):
        # Get event coordinates if from GUI, else NA
        x, y = (event.x, event.y) if event is not None else ("NA", "NA")

        # Stage codes
        if outcome == "ITI_peck":
            stage = 0
        elif outcome in ["circle_peck", "background_peck"]:
            stage = 1
        elif outcome == "reinforcement_provided":
            stage = 2
        elif outcome in ["SessionStarts", "SessionEnds"]:
            stage = "-"
        else:
            stage = "NA"

        # --- Terminal printout ---
        print(f"{outcome:>30} | x: {x:^3} y: {y:^3} | {stage:^5} | {str(datetime.now() - self.start_time)}")

        # --- Save to CSV ---
        self.session_data_frame.append([
            str(datetime.now() - self.start_time),  # SessionTime
            self.subject_ID,                        # Subject
            self.trial_counter,                     # Trial_Num
            outcome,                                # Event
            x,                                      # Xcord
            y,                                      # Ycord
            stage,                                  # TrialSubStage
            self.peck_counter,                      # PeckCount
            self.requirement,                       # VR_Requirement
            self.date                               # Date
        ])

        # Save continuously
        self.write_comp_data(False)
    
    def write_comp_data(self, SessionEnded):
        if SessionEnded:
            self.write_data(None, "SessionEnds")

        if self.record_data:
            myFile_loc = f"{self.data_folder_directory}/{self.subject_ID}/{self.subject_ID}_{self.start_time.strftime('%Y-%m-%d_%H.%M.%S')}_autoshaping.csv"
            with open(myFile_loc, 'w', newline='') as myFile:
                w = writer(myFile, quoting=QUOTE_MINIMAL)
                w.writerows(self.session_data_frame)
            if SessionEnded:
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
