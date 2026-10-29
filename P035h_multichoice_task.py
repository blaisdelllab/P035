#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Experiment 2.5: Multichoice Paradigm
Kayley Ozimac / P035 project family

Task structure:
    Phase 1: Pair Training
        - Standard symbolic MTS with 8 trained sample-comparison pairs.
        - Two comparisons appear on each trial: correct paired comparison + one trained foil.
        - Correct choices are reinforced; incorrect choices go to ITI.
        - Per pair, per rep (10-trial placement template):
              * every arc anchor holds the correct comparison exactly twice
                and the foil exactly twice (no position predicts correctness);
              * the foil falls left of correct exactly as often as right (5 vs 5);
              * "pick the more central comparison" wins 4, loses 4, ties 2.
        - Every pair is shown once before any pair repeats (8-trial blocks),
          and the same pair never appears on two consecutive trials.
        - Foil identity per pair is drawn without replacement from that pair's
          7 possible foils (cycling), so foils are used as evenly as possible.

    Phase 2: Probe Testing
        - Novel sample-comparison probe pairs are tested.
        - Displays contain 2, 3, 4, or 5 comparison choices total
          (1-4 foils).
        - Probe foil composition:
              all_familiar = all foils are trained Phase-1 comparisons
              all_novel    = all foils are novel comparisons
              mixed        = mixture of familiar and novel foils
        - Probe trials are nonreinforced by default so choice is not shaped during the test.
        - Refresher training trials are interspersed (maintenance only).

Layout:
    - All comparisons ride an arc centered on the sample, so every comparison
      location is exactly equidistant from the sample (a shallow rainbow).
    - The sample sits low on the screen, beneath the arc.

Expected stimulus folders:
    In test mode:
        ./P035h_Stimuli/
    On boxes:
        /home/blaisdelllab/Desktop/Experiments/P035h/P035h_Stimuli/

Expected stimulus names:
    Trained samples:      S01.bmp ... S08.bmp
    Trained comparisons:  C01.bmp ... C08.bmp
    Novel probe samples:  NS01.bmp ... NS08.bmp
    Novel correct comps:  NC01.bmp ... NC08.bmp
    Novel foil comps:     NF01.bmp ... NF32.bmp  (or more)

Data notes:
    - One row per event. Multi-item fields (AllComparisons, FoilList,
      CompAnchorList, FoilKinds) are joined with ";" (not "|"), so they can be
      split in R with strsplit(x, ";") without regex escaping.
    - Empty / not-applicable fields are written as "NA".
    - TrialType: train / refresher_train / probe.
    - TrialResult: "NA" until a choice is made in that trial, then
      "correct" or "incorrect". For one row per trial, take the
      correct_choice / incorrect_choice Event row (or the last row of the trial).
"""

from csv import writer, QUOTE_MINIMAL
from datetime import datetime
from os import getcwd, listdir, mkdir, path as os_path, popen
from random import choice, shuffle, Random
from sys import path as sys_path, setrecursionlimit
from time import sleep, time
from tkinter import BOTH, Button, Canvas, IntVar, Label, OptionMenu, Radiobutton, StringVar, Tk, Toplevel
from math import cos, radians, sin
from collections import Counter
from PIL import Image, ImageTk

setrecursionlimit(5000)

# =============================================================================
# Hardware detection/setup
# =============================================================================
try:
    operant_box_version = os_path.expanduser("~").split("/")[2] == "blaisdelllab"
except IndexError:
    operant_box_version = False

if operant_box_version:
    print("*** Running operant box version ***\n")
else:
    print("*** Running test version (no hardware) ***\n")

try:
    if operant_box_version:
        import pigpio
        import csv

        sys_path.insert(0, str(os_path.expanduser("~") + "/Desktop/Experiments/P033/"))
        import graph       # noqa: F401
        import polygon_fill  # noqa: F401

        servo_GPIO_num = 2
        hopper_light_GPIO_num = 13
        house_light_GPIO_num = 21

        rpi_board = pigpio.pi()
        rpi_board.set_mode(servo_GPIO_num, pigpio.OUTPUT)
        rpi_board.set_mode(hopper_light_GPIO_num, pigpio.OUTPUT)
        rpi_board.set_mode(house_light_GPIO_num, pigpio.OUTPUT)
        rpi_board.set_PWM_frequency(servo_GPIO_num, 50)

        hopper_vals_csv_path = str(os_path.expanduser("~") + "/Desktop/Box_Info/Hopper_vals.csv")
        up_down_table = list(csv.reader(open(hopper_vals_csv_path)))
        # These are servo PULSE WIDTHS (microseconds), not 0-255 duty cycles,
        # so they must be sent with set_servo_pulsewidth (as in P035g).
        hopper_up_val = int(float(up_down_table[1][0]))
        hopper_down_val = int(float(up_down_table[1][1]))

        popen("sh /home/blaisdelllab/Desktop/Hardware_Code/map_touchscreen.sh")
except ModuleNotFoundError:
    input("ERROR: Cannot find hopper hardware! Check desktop.")


# =============================================================================
# Control panel
# =============================================================================
class ExperimenterControlPanel(object):
    def __init__(self):
        if operant_box_version:
            self.data_folder = "P035_data"
            self.data_folder_directory = str(os_path.expanduser("~")) + "/Desktop/Data/" + self.data_folder
        else:
            self.data_folder_directory = getcwd() + "/data"

        self.control_window = Tk()
        self.control_window.title("Exp. 2.5 Multichoice Control Panel")

        self.pigeon_name_list = ["Bowser", "Yoshi", "Shy Guy", "Athena", "Darwin", "Cousteau", "Bon Jovi"]
        self.pigeon_name_list.sort()
        self.pigeon_name_list.insert(0, "TEST")

        Label(self.control_window, text="Pigeon Name:").pack()
        self.subject_ID_variable = StringVar(self.control_window)
        self.subject_ID_variable.set("Subject")
        OptionMenu(self.control_window, self.subject_ID_variable, *self.pigeon_name_list,
                   command=self.set_pigeon_ID).pack()

        self.experimental_phase_titles = [
            "Phase 1 (Pair Training)",
            "Phase 2 (Multichoice Probe Testing)",
        ]

        Label(self.control_window, text="Experimental Phase:").pack()
        self.exp_phase_variable = StringVar(self.control_window)
        self.exp_phase_variable.set("Select")
        OptionMenu(self.control_window, self.exp_phase_variable, *self.experimental_phase_titles).pack()

        Label(self.control_window, text="Probe Session Number:").pack()
        self.session_num_variable = StringVar(self.control_window)
        # Defaults to "NA" (training). A number must be picked for Phase 2.
        self.session_num_variable.set("NA")
        OptionMenu(self.control_window, self.session_num_variable,
                   *(["NA"] + [str(i) for i in range(1, 15)])).pack()

        Label(self.control_window, text="Record data in separate data sheet?").pack()
        self.record_data_variable = IntVar()
        Radiobutton(self.control_window, variable=self.record_data_variable, text="Yes", value=True).pack()
        Radiobutton(self.control_window, variable=self.record_data_variable, text="No", value=False).pack()
        self.record_data_variable.set(True)

        Button(self.control_window, text="Start program", bg="green2", command=self.build_chamber_screen).pack()
        self.control_window.mainloop()

    def set_pigeon_ID(self, pigeon_name):
        if not os_path.isdir(self.data_folder_directory):
            mkdir(self.data_folder_directory)
        pigeon_path = os_path.join(self.data_folder_directory, pigeon_name)
        if not os_path.isdir(pigeon_path):
            mkdir(pigeon_path)
            print(f"\n ** NEW DATA FOLDER FOR {pigeon_name.upper()} CREATED **")
        else:
            print(f"DATA FOLDER FOR {pigeon_name.upper()} EXISTS")

    def build_chamber_screen(self):
        if self.subject_ID_variable.get() not in self.pigeon_name_list:
            print("\n ERROR: Input Correct Pigeon ID Before Starting Session")
            return
        if self.exp_phase_variable.get() == "Select":
            print("\n ERROR: Select Phase Before Starting Session")
            return

        phase_index = self.experimental_phase_titles.index(self.exp_phase_variable.get())
        session_choice = self.session_num_variable.get()
        if phase_index == 1 and session_choice == "NA":
            print("\n ERROR: Select Probe Session Number Before Starting Phase 2")
            return
        # Probe session number only applies to Phase 2; training is always NA.
        session_num = int(session_choice) if (phase_index == 1 and session_choice != "NA") else None

        MainScreen(
            subject_ID=str(self.subject_ID_variable.get()),
            record_data=self.record_data_variable.get(),
            data_folder_directory=self.data_folder_directory,
            exp_phase_name=self.exp_phase_variable.get(),
            exp_phase_num=phase_index,
            session_num=session_num,
        )


# =============================================================================
# Main task
# =============================================================================
class MainScreen(object):
    # -------------------------
    # Adjustable task constants
    # -------------------------
    trained_pair_count = 8
    probe_pair_count = 8
    phase1_template_reps = 1      # 8 pairs x 10 placements x 1 rep = 80 training trials/session
                                  # (set to 2 for 160)
    # Probe sessions: each session carries `probes_per_type_per_session` probe(s)
    # of every one of the 24 crossed types, plus maintenance (standard) trials,
    # for ~130 trials total. Run `probe_sessions_to_run` sessions to accumulate
    # the prospectus's 12 probes/type (24 types x 12 = 288 probes over the period).
    probes_per_type_per_session = 1   # 24 probes/session (one per crossed type)
    probe_session_standard_trials = 106  # maintenance trials -> 24 + 106 = 130
    probe_sessions_to_run = 12         # 12 sessions x 1/type = 12 probes/type
    sample_FR_min = 3
    sample_FR_max = 10
    comparison_FR = 1

    # Separator for multi-item data fields. ";" is not a regex metacharacter,
    # so strsplit(x, ";") works in R without fixed = TRUE.
    field_sep = ";"

    # Sample sits low on the screen; comparisons ride an arc centered ON the
    # sample, so every comparison location is exactly equidistant from it and
    # the display reads like a shallow rainbow. Anchor pixel positions are
    # computed from these three values in _compute_arc_anchors().
    sample_center = (512, 690)
    arc_radius = 370        # px from the sample center to each comparison
    arc_half_angle = 78     # deg; wide arc so comparisons spread toward the screen edges
    n_arc_positions = 5

    # Which arc anchors each display size uses (symmetric about center).
    # Anchor index 0 = far left ... 4 = far right.
    comparison_slots = {
        1: [2],
        2: [0, 4],
        3: [0, 2, 4],
        4: [0, 1, 3, 4],
        5: [0, 1, 2, 3, 4],
    }

    # Per-pair TRAINING placement template: (correct_anchor, foil_anchor).
    # Row 1: foil one step clockwise; row 2: foil one step counter-clockwise
    # (wrapping 4<->0). Per pass through the template:
    #   - each anchor is the CORRECT location exactly 2x and the FOIL location 2x
    #   - foil left of correct 5x, right 5x
    #   - "peck the more central comparison" wins 4, loses 4, ties 2
    # Because the unit of repetition is this balanced block, any integer number
    # of reps stays perfectly balanced.
    training_placement_template = [
        (0, 1), (1, 2), (2, 3), (3, 4), (4, 0),
        (0, 4), (1, 0), (2, 1), (3, 2), (4, 3),
    ]

    reinforce_probe_trials = False

    def __init__(self, subject_ID, record_data, data_folder_directory,
                 exp_phase_name, exp_phase_num, session_num=None):
        self.subject_ID = subject_ID
        self.record_data = record_data
        self.data_folder_directory = data_folder_directory
        self.exp_phase_name = exp_phase_name
        self.exp_phase_num = exp_phase_num  # 0 = Pair Training, 1 = Probe Testing
        self.session_num = session_num  # probe session number; None (logged "NA") in training
        self.exp_phase ="Phase 1" if self.exp_phase_num == 0 else "Phase 2"
        self.start_time = datetime.now()
        self.trial_start = None
        self.current_trial_counter = 0
        self.trial_stage = 0
        self.sample_key_presses = 0
        self.comparison_key_presses = 0
        self.chosen_comp_tag = None
        self.chosen_stimulus = "NA"
        self.trial_result = "NA"
        self.choice_latency = "NA"
        self.choice_duration = "NA"
        self.comparison_start_time = None
        self.choice_lock_time = None
        self.last_written_trial_num = None
        self.session_ended = False
        self.mainscreen_height = 768
        self.mainscreen_width = 1024
        self.ITI_duration = 1000 if (not operant_box_version or self.subject_ID == "TEST") else 15000
        self.hopper_duration = 1000 if (not operant_box_version or self.subject_ID == "TEST") else 4500

        # Equidistant arc anchor positions (computed from the constants above).
        self.comparison_anchors = self._compute_arc_anchors()

        self._setup_window()
        self._setup_stimuli()
        self._build_trial_list()
        self._setup_data_matrix()
        self._preview_trials()
        self.print_counterbalancing_report()
        # Match the original P035-style opening screen:
        # wait here until the bird is placed in the box and the experimenter presses space.
        self.place_birds_in_box()

    # -------------------------------------------------------------------------
    # Setup
    # -------------------------------------------------------------------------
    def _compute_arc_anchors(self):
        # Five points evenly spaced in angle from -arc_half_angle (left) to
        # +arc_half_angle (right), all at arc_radius from the sample center.
        # Straight up from the sample is angle 0; +angle sweeps rightward.
        cx, cy = self.sample_center
        anchors = []
        for i in range(self.n_arc_positions):
            frac = (2 * i / (self.n_arc_positions - 1)) - 1   # -1 .. +1
            ang = radians(self.arc_half_angle * frac)
            x = cx + self.arc_radius * sin(ang)
            y = cy - self.arc_radius * cos(ang)
            anchors.append((round(x), round(y)))
        return anchors

    def _setup_window(self):
        self.root = Toplevel()
        self.root.title(f"Exp. {self.exp_phase_name}: {self.subject_ID}")
        self.root.bind("<Escape>", self.exit_program)

        if operant_box_version:
            self.cursor_visible = True
            self.change_cursor_state()
            self.root.bind("<c>", lambda event: self.change_cursor_state())
            self.root.geometry(f"{self.mainscreen_width}x{self.mainscreen_height}+1920+0")
            self.root.attributes("-fullscreen", True)
            self.mastercanvas = Canvas(self.root, bg="black")
            self.mastercanvas.pack(fill=BOTH, expand=True)
            self.light_HL_on_bool = False
        else:
            self.mastercanvas = Canvas(self.root, bg="black", height=self.mainscreen_height,
                                       width=self.mainscreen_width)
            self.mastercanvas.pack()

    def _setup_stimuli(self):
        if operant_box_version:
            self.stimuli_path = "/home/blaisdelllab/Desktop/Experiments/P035/P035h_Stimuli"
        else:
            self.stimuli_path = "/Users/kayleyozimac/Desktop/P035h/P035h_stimuli"

        if not os_path.isdir(self.stimuli_path):
            raise FileNotFoundError(f"Stimulus folder not found: {self.stimuli_path}")

        all_files = sorted([f for f in listdir(self.stimuli_path) if f.lower().endswith((".bmp", ".png", ".jpg", ".jpeg"))])

        self.trained_samples = [f"S{i:02d}.bmp" for i in range(1, self.trained_pair_count + 1)]
        self.trained_comps = [f"C{i:02d}.bmp" for i in range(1, self.trained_pair_count + 1)]
        self.probe_samples = [f"NS{i:02d}.bmp" for i in range(1, self.probe_pair_count + 1)]
        self.probe_correct_comps = [f"NC{i:02d}.bmp" for i in range(1, self.probe_pair_count + 1)]

        missing = [f for f in self.trained_samples + self.trained_comps + self.probe_samples + self.probe_correct_comps
                   if f not in all_files]
        if missing:
            raise FileNotFoundError(f"Missing required stimulus files in {self.stimuli_path}: {missing}")

        self.novel_foil_comps = [f for f in all_files if f.upper().startswith("NF")]
        if len(self.novel_foil_comps) < 32:
            raise ValueError("Need 32 novel foil comparison files named NF01.bmp through NF32.bmp.")

        self.trained_pair_map = dict(zip(self.trained_samples, self.trained_comps))
        self.probe_pair_map = dict(zip(self.probe_samples, self.probe_correct_comps))

    def _setup_data_matrix(self):
        self.session_data_frame = [[
            "SessionTime", "ExpPhase", "TrialType", "Subject", "Event", "TrialSubStage",
            "SampleStimulus", "CompStimulus", "ChosenStimulus", "CorrectComparison",
            "ChoicePosition", "CorrectPosition", "FoilComposition", "FoilCount",
            "ChoiceCount", "AllComparisons", "FoilList", "TrialResult",
            "TrialTime", "TrialNum", "ReinTrialNum", "SampleFR",
            "ChoiceLatency", "ChoiceDuration", "Date", "ComparisonTrialTime",
            "CompAnchorList", "CorrectAnchor", "ChoiceAnchor",
            "ProbeType", "FoilKinds", "ProbeSessionNum"
        ]]

    # -------------------------------------------------------------------------
    # Trial construction
    # -------------------------------------------------------------------------
    def _draw_sample_FR(self):
        return choice(range(self.sample_FR_min, self.sample_FR_max + 1))

    def _rng(self, *parts):
        seed = "|".join(map(str, parts))
        return Random(seed)

    def _build_trial_list(self):
        if self.exp_phase_num == 0:
            trials = self._build_pair_training_trials(self.phase1_template_reps)
        else:
            probes = self._build_multichoice_probe_trials(self.probes_per_type_per_session)
            standard = self._build_refresher_trials(self.probe_session_standard_trials)
            trials = self._interleave_trials(standard, probes)

        self.stimuli_assignment_dict = {i + 1: tr for i, tr in enumerate(trials)}
        self.max_trials = len(self.stimuli_assignment_dict)

    def _build_pair_training_trials(self, reps, trial_type="train"):
        # Each pair receives the full balanced placement template once per rep
        # (each anchor 2x correct / 2x foil, 5 foil-left / 5 foil-right).
        # Trials are dealt in cycles so that every pair is shown exactly once
        # before any pair is repeated: one cycle = one presentation of each of
        # the 8 pairs, in a freshly shuffled order. Each pair walks its own
        # shuffled copy of the template across cycles, so its position condition
        # isn't tied to the cycle number.
        n_cycles = len(self.training_placement_template)

        # Per-pair foil bags: each pair draws its foil without replacement from
        # its 7 possible foils, refilling (reshuffled) when empty. Bags persist
        # across reps so foil use stays as even as possible over the session.
        foil_bags = {s: [] for s in self.trained_samples}

        trials = []
        last_sample = None
        for rep in range(1, reps + 1):
            pair_schedules = {}
            for sample in self.trained_samples:
                sched = self.training_placement_template.copy()
                shuffle(sched)
                pair_schedules[sample] = sched

            for cycle in range(n_cycles):
                pairs = self.trained_samples.copy()
                shuffle(pairs)
                # No back-to-back repeat across a cycle boundary.
                while len(pairs) > 1 and pairs[0] == last_sample:
                    shuffle(pairs)
                for sample in pairs:
                    correct = self.trained_pair_map[sample]
                    c_idx, f_idx = pair_schedules[sample][cycle]
                    if not foil_bags[sample]:
                        foil_bags[sample] = [c for c in self.trained_comps if c != correct]
                        shuffle(foil_bags[sample])
                    foil = foil_bags[sample].pop()
                    # Order comparisons left-to-right by anchor index so that the
                    # logged ChoicePosition/CorrectPosition read left-to-right.
                    placement = sorted([(correct, c_idx), (foil, f_idx)], key=lambda t: t[1])
                    trials.append({
                        "trial_type": trial_type,
                        "sample": sample,
                        "sample_FR": self._draw_sample_FR(),
                        "correct_comp": correct,
                        "foil_comp": foil,
                        "foil_list": [foil],
                        "comparison_list": [n for n, _ in placement],
                        "anchor_indices": [i for _, i in placement],
                        "foil_composition": "trained_binary",
                        "foil_count": 1,
                        "choice_count": 2,
                        "reinforced": True,
                        "rep_num": rep,
                    })
                    last_sample = sample
        return trials

    def _build_refresher_trials(self, n_trials, trial_type="refresher_train"):
        # Maintenance training trials for Phase 2. These are NOT L/R balanced or
        # position-counterbalanced; two comparisons land on two random anchors.
        trials = []
        pool = []
        for _ in range(n_trials):
            if not pool:
                pool = self.trained_samples.copy()
                shuffle(pool)
            sample = pool.pop()
            correct = self.trained_pair_map[sample]
            foil = choice([c for c in self.trained_comps if c != correct])

            idxs = list(range(self.n_arc_positions))
            shuffle(idxs)
            a, b = sorted(idxs[:2])
            if choice([True, False]):
                placement = [(correct, a), (foil, b)]
            else:
                placement = [(foil, a), (correct, b)]
            placement.sort(key=lambda t: t[1])

            trials.append({
                "trial_type": trial_type,
                "sample": sample,
                "sample_FR": self._draw_sample_FR(),
                "correct_comp": correct,
                "foil_comp": foil,
                "foil_list": [foil],
                "comparison_list": [n for n, _ in placement],
                "anchor_indices": [i for _, i in placement],
                "foil_composition": "trained_binary",
                "foil_count": 1,
                "choice_count": 2,
                "reinforced": True,
            })
        return trials

    def _build_multichoice_probe_trials(self, reps_per_type):
        # Build `reps_per_type` probe(s) for every cell of the fully crossed
        # 4 x 3 x 2 design (24 types). Across sessions, the correct comparison's
        # left-to-right position is counterbalanced by keying it to session_num
        # (and staggering by type), so pooling the 12 sessions gives an even
        # spread of correct positions per type.
        #   Number of foils : 1, 2, 3, 4        -> 2-, 3-, 4-, 5-choice displays
        #   Foil composition: all_familiar, all_novel, mixed
        #   Probe type      : critical (novel NS->NC) / control (trained S->C)
        foil_levels = [1, 2, 3, 4]
        compositions = ["all_familiar", "all_novel", "mixed"]
        probe_types = ["critical", "control"]

        trials = []
        type_idx = 0
        for probe_type in probe_types:
            if probe_type == "critical":
                sample_pool, pair_map = self.probe_samples, self.probe_pair_map
            else:
                sample_pool, pair_map = self.trained_samples, self.trained_pair_map

            for composition in compositions:
                for foil_count in foil_levels:
                    choice_count = foil_count + 1
                    anchor_indices = list(self.comparison_slots[choice_count])
                    type_samples = self._probe_sample_sequence(sample_pool, reps_per_type)
                    for i in range(reps_per_type):
                        sample = type_samples[i]
                        correct = pair_map[sample]
                        foils, foil_kinds = self._select_probe_foils(
                            correct, foil_count, composition, probe_type, i)

                        # Counterbalance the correct comparison's left-to-right
                        # position across sessions (staggered by type and rep).
                        correct_pos = (self.session_num - 1 + type_idx + i) % choice_count
                        order = list(zip(foils, foil_kinds))
                        shuffle(order)
                        comps = [None] * choice_count
                        kinds_by_pos = [None] * choice_count
                        comps[correct_pos] = correct
                        kinds_by_pos[correct_pos] = "correct"
                        open_slots = [p for p in range(choice_count) if p != correct_pos]
                        for slot, (fname, fkind) in zip(open_slots, order):
                            comps[slot] = fname
                            kinds_by_pos[slot] = fkind

                        trials.append({
                            "trial_type": "probe",
                            "probe_type": probe_type,
                            "sample": sample,
                            "sample_FR": self._draw_sample_FR(),
                            "correct_comp": correct,
                            "foil_comp": self.field_sep.join(foils),
                            "foil_list": foils,
                            # foil_kinds is aligned to comparison_list, so the
                            # familiarity of the *chosen* comparison is recoverable.
                            "foil_kinds": kinds_by_pos,
                            "comparison_list": comps,
                            "anchor_indices": anchor_indices,
                            "foil_composition": composition,
                            "foil_count": foil_count,
                            "choice_count": choice_count,
                            "reinforced": self.reinforce_probe_trials,
                        })
                    type_idx += 1

        shuffle(trials)
        return trials

    def _probe_sample_sequence(self, pool, n):
        # n samples drawn by cycling the pool without replacement (reshuffling
        # each full pass), so each sample is used as equally as possible.
        seq, bag = [], []
        for _ in range(n):
            if not bag:
                bag = pool.copy()
                shuffle(bag)
            seq.append(bag.pop())
        return seq

    def _select_probe_foils(self, correct, foil_count, composition, probe_type, idx):
        # Familiar foils are trained comparisons (associates of *other* samples);
        # excluding `correct` matters for control probes, whose correct comp is a
        # trained C. Novel foils come from the reserved never-seen pool.
        familiar_pool = [c for c in self.trained_comps if c != correct]
        novel_pool = self.novel_foil_comps.copy()
        shuffle(familiar_pool)
        shuffle(novel_pool)

        if composition == "all_familiar":
            chosen = familiar_pool[:foil_count]
            return chosen, ["familiar"] * len(chosen)

        if composition == "all_novel":
            chosen = novel_pool[:foil_count]
            return chosen, ["novel"] * len(chosen)

        # mixed: equal familiar/novel where possible. For odd foil counts (and
        # the 1-foil case) the extra foil alternates familiar/novel across
        # SESSIONS, so each mixed type comes out balanced over the 12 sessions.
        base = foil_count // 2
        if foil_count % 2 == 0:
            n_familiar, n_novel = base, base
        elif (self.session_num - 1 + idx) % 2 == 0:
            n_familiar, n_novel = base + 1, base
        else:
            n_familiar, n_novel = base, base + 1
        chosen = familiar_pool[:n_familiar] + novel_pool[:n_novel]
        kinds = ["familiar"] * n_familiar + ["novel"] * n_novel
        return chosen, kinds

    def _interleave_trials(self, standard_trials, probe_trials):
        # Spread probes as evenly as possible through the standard (maintenance)
        # trials: split the standard stream into (n_probes + 1) chunks and drop
        # one probe between chunks. With many more standard trials than probes,
        # this guarantees no two probes are adjacent and holds the embedding
        # ratio roughly constant across the session.
        standard = standard_trials.copy()
        probe = probe_trials.copy()
        shuffle(standard)
        shuffle(probe)

        n_p = len(probe)
        if n_p == 0:
            return standard

        n_s = len(standard)
        n_gaps = n_p + 1
        chunk_sizes = [n_s // n_gaps] * n_gaps
        for k in range(n_s - sum(chunk_sizes)):   # distribute the remainder
            chunk_sizes[k] += 1
        shuffle(chunk_sizes)                       # randomize which gaps are larger

        out = []
        si = 0
        for pi in range(n_p):
            out.extend(standard[si:si + chunk_sizes[pi]])
            si += chunk_sizes[pi]
            out.append(probe[pi])
        out.extend(standard[si:])                  # trailing chunk
        return out

    def _preview_trials(self):
        print("\n" + "=" * 80)
        print(f"TRIAL ORDER PREVIEW: {self.exp_phase_name}")
        print("=" * 80)
        for trial_num, tr in self.stimuli_assignment_dict.items():
            comps = ", ".join(tr["comparison_list"])
            anchors = tr.get("anchor_indices", [])
            print(
                f"Trial {trial_num:03d}: {tr['trial_type']:>15} | "
                f"S={tr['sample']} | correct={tr['correct_comp']} | comps=[{comps}] | "
                f"anchors={anchors} | foils={tr['foil_composition']} ({tr['foil_count']})"
            )

    def print_counterbalancing_report(self):
        # Aggregate summary of the built trial list, printed at session start so
        # counterbalancing can be checked in the terminal before a bird runs.
        # Read-only: reports what _build_trial_list() produced, changes nothing.
        trials = list(self.stimuli_assignment_dict.values())
        print("\n" + "=" * 60)
        print(f"COUNTERBALANCING | {self.exp_phase_name} | n={len(trials)}")
        print("Trial types:", dict(Counter(t["trial_type"] for t in trials)))

        if self.exp_phase_num == 0:  # Phase 1
            print("Per sample:", dict(Counter(t["sample"] for t in trials)))
            side = Counter()
            correct_anchor = Counter()
            foil_anchor = Counter()
            for t in trials:
                comps, anc = t["comparison_list"], t["anchor_indices"]
                ca = anc[comps.index(t["correct_comp"])]
                fa = anc[comps.index(t["foil_list"][0])]
                correct_anchor[ca] += 1
                foil_anchor[fa] += 1
                side["foil_L" if fa < ca else "foil_R"] += 1
            print("Foil side (want equal):", dict(side))
            print("Correct anchor 0-4 (want equal):",
                  [correct_anchor[a] for a in range(self.n_arc_positions)])
            print("Foil anchor 0-4    (want equal):",
                  [foil_anchor[a] for a in range(self.n_arc_positions)])

            # Foil identity spread per pair (want max - min <= 1).
            spreads = []
            for s in self.trained_samples:
                fc = Counter(t["foil_list"][0] for t in trials if t["sample"] == s)
                n_possible = self.trained_pair_count - 1
                counts = [fc.get(c, 0) for c in self.trained_comps
                          if c != self.trained_pair_map[s]][:n_possible]
                spreads.append(max(counts) - min(counts))
            print("Foil-identity spread per pair (want <=1):", spreads)

            # Block structure: every consecutive 8 trials contains all 8 pairs,
            # and no pair appears on two consecutive trials.
            k = self.trained_pair_count
            blocks_ok = all(
                len({t["sample"] for t in trials[i:i + k]}) == k
                for i in range(0, len(trials), k)
            )
            back_to_back = sum(
                trials[i]["sample"] == trials[i + 1]["sample"] for i in range(len(trials) - 1)
            )
            print(f"All pairs once per {k}-trial block: {blocks_ok}")
            print(f"Back-to-back repeats (want 0): {back_to_back}")
        else:  # Phase 2
            probes = [t for t in trials if t["trial_type"] == "probe"]
            cells = Counter((t["probe_type"], t["foil_composition"], t["foil_count"])
                            for t in probes)
            print(f"Probes: {len(probes)} across {len(cells)} cells "
                  f"(want 24, each ={self.probes_per_type_per_session})")
            for cell, n in sorted(cells.items()):
                flag = "" if n == self.probes_per_type_per_session else "  <-- off"
                print(f"   {cell}: {n}{flag}")
        print("=" * 60 + "\n")

    # -------------------------------------------------------------------------
    # Task flow
    # -------------------------------------------------------------------------
    def place_birds_in_box(self):
        # Default opening screen until bird is placed in the box and space bar is pressed.
        # After spacebar, the first ITI occurs prior to the first trial.
        self.clear_canvas()
        self.root.bind("<space>", self.first_ITI)
        self.mastercanvas.create_text(
            512, 384,
            fill="white",
            font="Times 26 italic bold",
            text=(f"P035h \n Place bird in box, then press space \n "
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

    def ITI(self):
        if self.session_ended:
            return
        self.clear_canvas()
        # Advance to the next trial. (1-based; the completion check below assumes
        # the counter has already been incremented for the trial about to run.)
        self.current_trial_counter += 1

        if self.current_trial_counter > self.max_trials:
            # exit_program writes the SessionEnds row and the final file (once).
            self.exit_program("Session complete")
            return

        self.sample_key_presses = 0
        self.comparison_key_presses = 0
        self.chosen_comp_tag = None
        self.chosen_stimulus = "NA"
        self.trial_result = "NA"
        self.choice_latency = "NA"
        self.choice_duration = "NA"
        self.choice_lock_time = None
        self.comparison_start_time = None
        self.trial_stage = 0
        self.trial_start = time()

        # ITI pecks (as in P035g). Logged under the upcoming trial's number,
        # with TrialSubStage = 0.
        self._draw_background("ITI_peck")
        if operant_box_version:
            rpi_board.write(house_light_GPIO_num, False)

        self.write_comp_data(False)
        self.root.after(self.ITI_duration, self.sample_phase)

        print(f"\n{'*' * 30} Trial {self.current_trial_counter} begins {'*' * 30}")

    def sample_phase(self):
        self.clear_canvas()
        self.trial_stage = 1
        # House light on during trial phases (as in P035g).
        if operant_box_version:
            rpi_board.write(house_light_GPIO_num, True)
        self._draw_background("background_peck")
        trial = self.stimuli_assignment_dict[self.current_trial_counter]
        stim_path = os_path.join(self.stimuli_path, trial["sample"])
        img = ImageTk.PhotoImage(Image.open(stim_path))
        self.active_sample_image = img

        sx, sy = self._sample_position()
        self.mastercanvas.create_image(sx, sy, image=self.active_sample_image, anchor="center", tag="sample")
        self.mastercanvas.tag_bind("sample", "<Button-1>", self.sample_key_press)

    def sample_key_press(self, event):
        self.sample_key_presses += 1
        self.write_data(event, "sample_key_press")
        trial = self.stimuli_assignment_dict[self.current_trial_counter]
        if self.sample_key_presses >= int(trial["sample_FR"]):
            self.comparison_phase()

    def comparison_phase(self):
        self.clear_canvas()
        self.trial_stage = 2
        self.comparison_start_time = datetime.now()
        trial = self.stimuli_assignment_dict[self.current_trial_counter]
        comps = trial["comparison_list"]
        # Each trial carries its own arc anchor indices (built above), so a given
        # location is identical regardless of the number of choices shown.
        positions = [self.comparison_anchors[i] for i in trial["anchor_indices"]]

        self._draw_background("background_peck")
        self._draw_inactive_sample(trial["sample"])

        self.comp_images = []
        for idx, (comp_name, (x, y)) in enumerate(zip(comps, positions), start=1):
            tag = f"comp_{idx}"
            img = ImageTk.PhotoImage(Image.open(os_path.join(self.stimuli_path, comp_name)))
            self.comp_images.append(img)
            self.mastercanvas.create_image(x, y, image=img, anchor="center", tag=tag)
            self.mastercanvas.tag_bind(tag, "<Button-1>", self.comp_key_press)

    def _draw_background(self, event_type):
        # Full-screen black rectangle, drawn FIRST so stimuli sit on top of it.
        # Pecks that land on a stimulus go to that stimulus's handler; pecks
        # anywhere else hit this rectangle and are logged as `event_type`.
        self.mastercanvas.create_rectangle(
            0, 0, self.mainscreen_width, self.mainscreen_height,
            fill="black", outline="black", tag="bkgrd"
        )
        self.mastercanvas.tag_bind(
            "bkgrd", "<Button-1>",
            lambda event, et=event_type: self.write_data(event, et)
        )

    def _draw_inactive_sample(self, sample_name):
        sx, sy = self._sample_position()
        img = ImageTk.PhotoImage(Image.open(os_path.join(self.stimuli_path, sample_name)))
        self.inactive_sample_image = img
        self.mastercanvas.create_image(sx, sy, image=self.inactive_sample_image, anchor="center", tag="inactive_sample")
        self.mastercanvas.tag_bind("inactive_sample", "<Button-1>",
                                   lambda event: self.write_data(event, "inactive_sample_key_press"))

    def comp_key_press(self, event):
        tags = self.mastercanvas.gettags("current")
        if not tags:
            return
        clicked_tag = tags[0]
        trial = self.stimuli_assignment_dict[self.current_trial_counter]
        comps = trial["comparison_list"]

        if not clicked_tag.startswith("comp_"):
            return

        clicked_index = int(clicked_tag.split("_")[1]) - 1
        clicked_stim = comps[clicked_index]

        self.write_data(event, f"{clicked_tag}_press")

        if self.chosen_comp_tag is None:
            self.chosen_comp_tag = clicked_tag
            self.chosen_stimulus = clicked_stim
            self.choice_lock_time = datetime.now()
            if self.comparison_start_time is not None:
                self.choice_latency = (self.choice_lock_time - self.comparison_start_time).total_seconds()

        # Choice lock: only pecks to the initially chosen comparison count toward FR
        if clicked_tag != self.chosen_comp_tag:
            return

        self.comparison_key_presses += 1
        if self.comparison_key_presses >= int(self.comparison_FR):
            complete_time = datetime.now()
            if self.choice_lock_time is not None:
                self.choice_duration = (complete_time - self.choice_lock_time).total_seconds()
            self._finish_choice()

    def _finish_choice(self):
        self.clear_canvas()
        # Keep logging stray pecks during the brief post-choice gap before ITI.
        self._draw_background("background_peck")
        trial = self.stimuli_assignment_dict[self.current_trial_counter]
        correct = trial["correct_comp"]
        is_correct = self.chosen_stimulus == correct
        self.trial_result = "correct" if is_correct else "incorrect"

        if is_correct:
            self.write_data(None, "correct_choice")
            if trial["reinforced"]:
                self.reinforcement_phase()
            else:
                self.root.after(250, self.ITI)
        else:
            self.write_data(None, "incorrect_choice")
            # Incorrect choices go to ITI (no reinforcement).
            self.root.after(250, self.ITI)

    def reinforcement_phase(self):
        self.trial_stage = 3   # as in P035g
        self.clear_canvas()
        self.write_data(None, "reinforcement_provided")
        if operant_box_version:
            rpi_board.write(house_light_GPIO_num, False)
            rpi_board.write(hopper_light_GPIO_num, True)
            rpi_board.set_servo_pulsewidth(servo_GPIO_num, hopper_up_val)
            self.root.after(self.hopper_duration, self._end_reinforcement)
        else:
            self.mastercanvas.create_text(512, 384, text="REINFORCEMENT", fill="white", font=("Arial", 32))
            self.root.after(self.hopper_duration, self._end_reinforcement)

    def _end_reinforcement(self):
        self._hopper_down()
        self.ITI()

    def _hopper_down(self):
        if operant_box_version:
            rpi_board.write(hopper_light_GPIO_num, False)
            rpi_board.set_servo_pulsewidth(servo_GPIO_num, hopper_down_val)

    # -------------------------------------------------------------------------
    # Data logging
    # -------------------------------------------------------------------------
    def _join(self, items):
        # Join multi-item fields with field_sep; empty -> "NA".
        items = [str(i) for i in items if i is not None]
        return self.field_sep.join(items) if items else "NA"

    def write_data(self, event, event_name):
        if self.current_trial_counter == 0:
            return
        trial = self.stimuli_assignment_dict.get(self.current_trial_counter, {})
        now = datetime.now()

        correct = trial.get("correct_comp", "NA")
        comps = trial.get("comparison_list", [])
        correct_position = "NA"
        choice_position = "NA"
        if correct in comps:
            correct_position = f"comp_{comps.index(correct) + 1}"
        if self.chosen_comp_tag is not None:
            choice_position = self.chosen_comp_tag

        # Arc anchor bookkeeping (lets you verify L/R balance and 5-position
        # coverage straight from the CSV). Anchor index 0 = far left ... 4 = far right.
        anchor_list = trial.get("anchor_indices", [])
        correct_anchor = "NA"
        choice_anchor = "NA"
        if len(anchor_list) == len(comps) and comps:
            if correct in comps:
                correct_anchor = anchor_list[comps.index(correct)]
            if self.chosen_stimulus not in (None, "NA") and self.chosen_stimulus in comps:
                choice_anchor = anchor_list[comps.index(self.chosen_stimulus)]

        trial_time = "NA" if self.trial_start is None else round(time() - self.trial_start, 4)
        comp_trial_time = "NA"
        if self.comparison_start_time is not None:
            comp_trial_time = round((now - self.comparison_start_time).total_seconds(), 4)
        row = [
            now.strftime("%H:%M:%S.%f")[:-3],
            self.exp_phase,
            trial.get("trial_type", "NA"),
            self.subject_ID,
            event_name,
            self.trial_stage,
            trial.get("sample", "NA"),
            self._current_comp_stimulus_from_event(event_name, trial),
            self.chosen_stimulus,
            correct,
            choice_position,
            correct_position,
            trial.get("foil_composition", "NA"),
            trial.get("foil_count", "NA"),
            trial.get("choice_count", "NA"),
            self._join(comps),
            self._join(trial.get("foil_list", [])),
            self.trial_result if trial else "NA",   # SessionEnds row has no trial
            trial_time,
            self.current_trial_counter,
            self.current_trial_counter,  # kept for compatibility with older analysis scripts
            trial.get("sample_FR", "NA"),
            self.choice_latency,
            self.choice_duration,
            now.strftime("%Y-%m-%d"),
            comp_trial_time,
            self._join(anchor_list),
            correct_anchor,
            choice_anchor,
            trial.get("probe_type", "NA"),
            self._join(trial.get("foil_kinds", [])),
            "NA" if self.session_num is None else self.session_num,
        ]
        self.session_data_frame.append(row)
        print(f"{event_name:>30} | Trial {self.current_trial_counter:03d} | {trial.get('trial_type', 'NA')}")

    def _current_comp_stimulus_from_event(self, event_name, trial):
        if event_name.startswith("comp_") and "_press" in event_name:
            try:
                idx = int(event_name.split("_")[1]) - 1
                return trial.get("comparison_list", [])[idx]
            except Exception:
                return "NA"
        return self.chosen_stimulus

    def write_comp_data(self, SessionEnded):
        if SessionEnded:
            self.write_data(None, "SessionEnds")
        if not self.record_data:
            return
        subject_folder = f"{self.data_folder_directory}/{self.subject_ID}"
        if not os_path.isdir(subject_folder):
            mkdir(subject_folder)
        file_loc = (
            f"{subject_folder}/{self.subject_ID}_"
            f"{self.start_time.strftime('%Y-%m-%d_%H.%M.%S')}_"
            f"Exp2.5_multichoice_Phase{self.exp_phase_num + 1}.csv"
        )
        with open(file_loc, "w", newline="") as myFile:
            w = writer(myFile, quoting=QUOTE_MINIMAL)
            w.writerows(self.session_data_frame)
        print(f"\n- Data file written to {file_loc}")

    # -------------------------------------------------------------------------
    # Utility
    # -------------------------------------------------------------------------
    def _sample_position(self):
        # Sample sits centered, low on the screen, below the comparison arc.
        # Same position for every bird, so the arc is equidistant for all subjects.
        return self.sample_center

    def clear_canvas(self):
        self.mastercanvas.delete("all")

    def change_cursor_state(self):
        if self.cursor_visible:
            self.root.config(cursor="none")
            self.cursor_visible = False
            print("### Cursor turned off ###")
        else:
            self.root.config(cursor="")
            self.cursor_visible = True
            print("### Cursor turned on ###")

    def exit_program(self, event):
        # Called by Escape or at normal session completion. Guarded so the
        # SessionEnds row and final file are written exactly once.
        if self.session_ended:
            return
        self.session_ended = True
        print("\nExiting program:", event)
        # Always lower the hopper and turn off its light: if Escape is pressed
        # during reinforcement, destroying the window cancels _end_reinforcement.
        try:
            self._hopper_down()
            if operant_box_version:
                # Same shutdown sequence as P035g: lights off, let the hopper
                # settle down, release the servo, and stop the board.
                rpi_board.write(house_light_GPIO_num, False)
                sleep(1)
                rpi_board.set_PWM_dutycycle(servo_GPIO_num, False)
                rpi_board.set_PWM_frequency(servo_GPIO_num, False)
                rpi_board.stop()
                if not self.cursor_visible:
                    self.change_cursor_state()
        except Exception as e:
            print("ERROR during hardware shutdown:", e)
        try:
            self.write_comp_data(True)
        except Exception as e:
            print("ERROR writing data on exit:", e)
        try:
            self.root.destroy()
        except Exception:
            pass


# =============================================================================
# Run
# =============================================================================
try:
    if __name__ == "__main__":
        cp = ExperimenterControlPanel()
except Exception as e:
    print("Unexpected error:", e)
    if operant_box_version:
        rpi_board.set_PWM_dutycycle(servo_GPIO_num, False)
        rpi_board.set_PWM_frequency(servo_GPIO_num, False)
        rpi_board.stop()
    raise
