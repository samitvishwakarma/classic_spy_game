# Spy game made using python and tkinter standard module.

import tkinter as tk
from tkinter import messagebox
import random
import json, os
import time


# --- Files ---
cache_file = "player_cache.json"
locations_file = "custom_locations.json"

# --- Default hardcoded locations ---
default_locations = [
    "Airport", "Beach", "Casino", "Concert Hall", "Police Station",
    "Restaurant", "School", "Theater", "Hospital", "Library"
]

# --- JSON handling ---
def load_json(filename, default):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default


def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# --- App / Screen Management ---
class SpyGameApp:

    def __init__(self, root):
        self.root = root
        root.title("Spy Game")

        try:
            root.state('zoomed')
        except Exception:
            root.attributes('-fullscreen', True)

        # Game states

        self.players = 0
        self.spies = 0
        self.roles = []
        self.player_names = {}
        self.name_entries = []
        self.current_reveal_index = 0
        self.location = None
        self.timer = None  # seconds

        # Load custom locations (or empty list if none)
        self.custom_locations = load_json(locations_file, [])

        self.show_start_screen()

    def clear_window(self):
        for w in self.root.winfo_children():
            w.destroy()

    # --- Game starting screen, asking playing whether to use cache settings or not. ---
    def show_start_screen(self):
        self.clear_window()
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(expand=True)

        tk.Label(frame, text="Welcome to Spy Game", font=("Helvetica", 28)).pack(pady=(0, 20))

        if os.path.exists(cache_file):
            tk.Button(frame, text="Use last settings", font=("Helvetica", 16),
                      command=self.load_cache_and_start).pack(pady=10)

        tk.Button(frame, text="Start fresh", font=("Helvetica", 16),
                  command=self.show_main_menu).pack(pady=10)

        tk.Button(frame, text="Manage Locations", font=("Helvetica", 14),
                  command=self.manage_locations).pack(pady=(40, 10))

        tk.Button(frame, text="Quit", font=("Helvetica", 12), command=self.root.quit).pack(pady=10)

    # --- Main menu screen ---
    def show_main_menu(self):
        self.clear_window()
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(expand=True)

        tk.Label(frame, text="Setup New Game", font=("Helvetica", 28)).pack(pady=(0, 10))
        tk.Label(frame, text="Enter number of players (Minimum 2):", font=("Helvetica", 16)).pack(pady=(0, 6))

        self.entry = tk.Entry(frame, font=("Helvetica", 16), width=6, justify='center')
        self.entry.pack(pady=(0, 12))
        self.entry.focus_set()

        tk.Label(frame, text="Enter number of spies:", font=("Helvetica", 16)).pack(pady=(0, 6))
        self.entry_2 = tk.Entry(frame, font=("Helvetica", 16), width=6, justify='center')
        self.entry_2.pack(pady=(0, 12))

        tk.Label(frame, text="Enter the round discussion time (minutes):", font=("Helvetica", 16)).pack(pady=(0, 6))
        self.entry_3 = tk.Entry(frame, font=("Helvetica", 16), width=6, justify='center')
        self.entry_3.pack(pady=(0, 12))

        submit_btn = tk.Button(frame, text="Continue", font=("Helvetica", 14), width=12, command=self.submit_players)
        submit_btn.pack(pady=(5, 8))

        tk.Button(frame, text="Back", font=("Helvetica", 12), command=self.show_start_screen).pack(pady=10)

    def submit_players(self):
        try:
            n = int(self.entry.get().strip())
            spies = int(self.entry_2.get().strip())
            minutes = int(self.entry_3.get().strip())
            self.timer = minutes * 60
        except ValueError:
            messagebox.showerror("Invalid input", "Please enter integer values.")
            return

        if n <= 1:
            messagebox.showerror("Invalid number", "At least 2 players.")
            return
        elif spies <= 0 or spies >= n:
            messagebox.showerror(title="Invalid number", message= "There must be at least 1 spy. Please enter a number between 1 and " + str(n) + ".")
            return
        elif self.timer <= 0:
            messagebox.showerror(title="Invalid number.", message="Please enter a valid time in minutes.")
            return

        self.players = n
        self.spies = spies
        self.player_customizations()

    # --- Player name customization ---
    def player_customizations(self):
        self.clear_window()
        self.player_names = {}
        self.name_entries = []

        tk.Label(self.root, text="Enter player names:", font=("Helvetica", 20)).pack(pady=10)

        form_frame = tk.Frame(self.root)
        form_frame.pack(pady=10)

        for i in range(self.players):
            tk.Label(form_frame, text=f"Player {i+1}:", font=("Helvetica", 14)).grid(row=i, column=0, padx=5, pady=5, sticky="e")
            entry = tk.Entry(form_frame, font=("Helvetica", 14))
            entry.grid(row=i, column=1, padx=5, pady=5)
            self.name_entries.append(entry)

        tk.Button(self.root, text="Continue", font=("Helvetica", 16),
                  command=self.save_player_names).pack(pady=15)

    def save_player_names(self):
        for i, entry in enumerate(self.name_entries):
            name = entry.get().strip()
            if not name:
                name = f"Player {i+1}"
            self.player_names[f"Player {i+1}"] = name

        # Save cache
        cache_data = {
            "players": self.players,
            "spies": self.spies,
            "names": self.player_names,
            "timer": self.timer
        }
        save_json(cache_file, cache_data)

        self.setup_game()

    def load_cache_and_start(self):
        cache_data = load_json(cache_file, None)
        if not cache_data:
            messagebox.showerror("Error", "No valid cache found.")
            return

        self.players = cache_data.get("players", 0)
        self.spies = cache_data.get("spies", 0)
        self.player_names = cache_data.get("names", {})
        self.timer = cache_data.get("timer", None)

        if not self.players or not self.spies:
            messagebox.showerror("Error", "Cache data incomplete.")
            return

        self.setup_game()

    # --- Game setup and role assignment ---
    def setup_game(self):
        all_locations = default_locations + self.custom_locations
        self.location = random.choice(all_locations)

        roles = ["Spy"] * self.spies + [self.location] * (self.players - self.spies)
        random.shuffle(roles)

        self.roles = roles
        self.current_reveal_index = 0

        self.reveal_screen()

    # --- Sequential reveal screen ---
    def reveal_screen(self):
        self.clear_window()
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(expand=True)

        tk.Label(frame, text="Role Reveal", font=("Helvetica", 24)).pack(pady=(0, 12))
        tk.Label(frame, text="Pass the device. Each player presses 'Reveal my role', and pass to the next player after finishing.",
                 font=("Helvetica", 12), wraplength=700).pack(pady=(0, 18))

        self.reveal_label = tk.Label(frame, text=f"Player {self.current_reveal_index + 1} of {self.players}", font=("Helvetica", 16))
        self.reveal_label.pack(pady=(0, 12))
        self.reveal_label_named = tk.Label(frame, text=self.player_names[f"Player {self.current_reveal_index + 1}"], justify='center', font=("Cursive", 20))
        self.reveal_label_named.pack(pady=(0, 12))

        reveal_btn = tk.Button(frame, text="Reveal my role", font=("Helvetica", 14), width=16,
                               command=self.show_role_popup)
        reveal_btn.pack(pady=(4, 8))

        tk.Button(frame, text="Restart", font=("Helvetica", 12), command=self.show_start_screen).pack(side="left", padx=10, pady=20)
        tk.Button(frame, text="Finish setup (start discussion)", font=("Helvetica", 12),
                  command=self.show_summary_if_all_revealed).pack(side="right", padx=10, pady=20)

    def show_role_popup(self):
        idx = self.current_reveal_index
        role = self.roles[idx]

        popup = tk.Toplevel(self.root)
        popup.transient(self.root)
        popup.grab_set()
        popup.title(f"Player {idx + 1} role")
        popup.geometry("400x220")
        popup.resizable(False, False)

        tk.Label(popup, text=f"Player {idx + 1}", font=("Helvetica", 18)).pack(pady=(12, 6))
        role_text = ("SPY" if role == "Spy" else f"Location:\n{role}")
        lbl = tk.Label(popup, text=role_text, font=("Helvetica", 16), wraplength=350)
        lbl.pack(pady=(6, 12))

        def close_and_next():
            popup.destroy()
            self.current_reveal_index += 1
            if self.current_reveal_index >= self.players:
                self.show_all_revealed()
            else:
                self.reveal_label.config(text=f"Player {self.current_reveal_index + 1} of {self.players}")
                self.reveal_label_named.config(text=self.player_names[f"Player {self.current_reveal_index + 1}"])


        tk.Button(popup, text="Done (pass to next player)", font=("Helvetica", 12), command=close_and_next).pack(pady=(6, 10))

    def show_all_revealed(self):
        self.clear_window()
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(expand=True)

        tk.Label(frame, text="All roles revealed", font=("Helvetica", 22)).pack(pady=(0, 12))
        tk.Label(frame, text="Now start the discussion and try to find the spy!", font=("Helvetica", 14)).pack(pady=(0, 10))

        self.timer_label = tk.Label(frame, text="", font=("Helvetica", 14))
        self.timer_label.pack(pady=(0, 10))

        # ---------- only start countdown if a valid timer exists ----------
        if isinstance(self.timer, int) and self.timer > 0:
            self.countdown()
        else:
            # if no timer set
            self.timer_label.config(text="No timer set. Set time during Setup.")

        tk.Button(frame, text="Back to main menu", font=("Helvetica", 12), command=self.show_start_screen).pack(pady=(6, 8))

    def show_summary_if_all_revealed(self):
        if self.current_reveal_index >= self.players:
            self.show_all_revealed()
        else:
            messagebox.showinfo("Not finished", "Not all players have revealed their roles yet. Continue revealing for each player.")

    # --- Managing custom locations ---
    def manage_locations(self):
        self.clear_window()
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(expand=True)

        tk.Label(frame, text="Custom Locations", font=("Helvetica", 22)).pack(pady=(0, 12))

        list_frame = tk.Frame(frame)
        list_frame.pack(pady=10)

        for i, loc in enumerate(self.custom_locations):
            tk.Label(list_frame, text=loc, font=("Helvetica", 14)).grid(row=i, column=0, sticky="w", padx=5, pady=3)
            tk.Button(list_frame, text="Remove", font=("Helvetica", 10),
                      command=lambda l=loc: self.remove_location(l)).grid(row=i, column=1, padx=5)

        self.new_loc_entry = tk.Entry(frame, font=("Helvetica", 14))
        self.new_loc_entry.pack(pady=(10, 5))
        tk.Button(frame, text="Add Location", font=("Helvetica", 12), command=self.add_location).pack()

        tk.Label(frame, text="Default locations are always included and cannot be edited.",
                 font=("Helvetica", 10), fg="gray").pack(pady=(10, 0))

        tk.Button(frame, text="Back", font=("Helvetica", 12), command=self.show_start_screen).pack(pady=(20, 0))

    def add_location(self):
        loc = self.new_loc_entry.get().strip()
        if loc and loc not in self.custom_locations and loc not in default_locations:
            self.custom_locations.append(loc)
            save_json(locations_file, self.custom_locations)
            self.manage_locations()
        else:
            messagebox.showerror("Invalid", "Location empty or already exists.")

    def remove_location(self, loc):
        self.custom_locations.remove(loc)
        save_json(locations_file, self.custom_locations)
        self.manage_locations()


    # --- Countdown timer ---
    def countdown(self):
        if isinstance(self.timer, int) and self.timer > 0:
            mins, secs = divmod(self.timer, 60)
            self.counter = '{:02d}:{:02d}'.format(mins, secs)
            self.timer_label.config(text=self.counter)
            self.timer -= 1
            self.root.after(1000, self.countdown)  # Schedule next tick without blocking UI
        else:
            # final state
            self.timer_label.config(text="Time’s up!")
            try:
                messagebox.showinfo("Time's up!", "The round is over! Time to vote.")
            except Exception:
                pass  # in case called during teardown

if __name__ == "__main__":
    root = tk.Tk()
    app = SpyGameApp(root)
    root.mainloop()
