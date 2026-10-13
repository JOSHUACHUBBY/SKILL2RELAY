
import json
import os
import tempfile
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

APP_NAME = "Skill2Relay"
DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "users.json",
)

# colour palette
CREAM = "#F7F6F0"
WHITE = "#FFFFFF"
SAGE = "#527D68"
SAGE_DARK = "#3D6653"
SAGE_LIGHT = "#E6EFE8"
BLUE_LIGHT = "#E8F0F8"
BLUE = "#527DA8"
TEXT = "#26352D"
MUTED = "#78847C"
BORDER = "#E5E9E3"
RED = "#B94D4D"
RED_LIGHT = "#F9E9E7"

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")


# --------------------------------------------------
# DATA STORAGE
# --------------------------------------------------

def load_users():
    """Load profiles without overwriting an unreadable data file."""
    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError("The JSON file must contain a list of profiles.")

        # Convert the original field names to the names used by the GUI
        for user in data:
            if not isinstance(user, dict):
                raise ValueError("A profile in users.json is not valid.")

            if "teach" not in user and "teach_skill" in user:
                user["teach"] = user["teach_skill"]

            if "learn" not in user and "learn_skill" in user:
                user["learn"] = user["learn_skill"]

        # Validate each profile
        for user in data:
            if not all(
                key in user
                and isinstance(user[key], str)
                and user[key].strip()
                for key in ("name", "teach", "learn")
            ):
                raise ValueError(
                    "A profile must have a non-empty name, teach, and learn field."
                )

        return data

    except (json.JSONDecodeError, OSError, ValueError) as error:
        messagebox.showerror(
            "Could not load profiles",
            f"Skill2Relay could not read users.json.\n\n{error}\n\n"
            "Your original file has not been overwritten.",
        )
        return []


def save_users(profiles):
    """Save profiles atomically to reduce the risk of a damaged JSON file."""
    folder = os.path.dirname(DATA_FILE)

    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=folder,
            delete=False,
            suffix=".tmp",
        ) as temporary_file:
            json.dump(profiles, temporary_file, indent=4, ensure_ascii=False)
            temporary_file.write("\n")
            temporary_path = temporary_file.name

        os.replace(temporary_path, DATA_FILE)
        return True

    except OSError as error:
        if temporary_path and os.path.exists(temporary_path):
            try:
                os.remove(temporary_path)
            except OSError:
                pass

        messagebox.showerror(
            "Could not save profiles",
            f"Your changes could not be saved.\n\n{error}",
        )
        return False


# --------------------------------------------------
# PROFILE FORM
# --------------------------------------------------

class ProfileDialog(ctk.CTkToplevel):
    def __init__(self, app, profile=None):
        super().__init__(app)

        self.app = app
        self.profile = profile
        self.result = None
        self.is_editing = profile is not None

        self.title("Edit profile" if self.is_editing else "Create profile")
        self.geometry("490x550")
        self.resizable(False, False)
        self.configure(fg_color=CREAM)
        self.transient(app)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)

        heading = "Update your profile" if self.is_editing else "Join the community"
        subtitle = (
            "Keep your skills up to date."
            if self.is_editing
            else "Share what you know. Discover what you can learn."
        )

        ctk.CTkLabel(
            self,
            text=heading,
            font=ctk.CTkFont(family="Segoe UI", size=25, weight="bold"),
            text_color=TEXT,
        ).grid(row=0, column=0, padx=30, pady=(28, 4), sticky="w")

        ctk.CTkLabel(
            self,
            text=subtitle,
            font=ctk.CTkFont(size=13),
            text_color=MUTED,
        ).grid(row=1, column=0, padx=30, pady=(0, 22), sticky="w")

        self.name_entry = self.make_field("Your name", 2)
        self.teach_entry = self.make_field("A skill you can teach", 4)
        self.learn_entry = self.make_field("A skill you want to learn", 6)

        if profile:
            self.name_entry.insert(0, profile.get("name", ""))
            self.teach_entry.insert(0, profile.get("teach", ""))
            self.learn_entry.insert(0, profile.get("learn", ""))

        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.grid(row=8, column=0, padx=30, pady=(24, 28), sticky="ew")
        button_row.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            button_row,
            text="Cancel",
            height=42,
            fg_color=WHITE,
            hover_color=SAGE_LIGHT,
            text_color=TEXT,
            border_width=1,
            border_color=BORDER,
            command=self.destroy,
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        ctk.CTkButton(
            button_row,
            text="Save profile",
            height=42,
            fg_color=SAGE,
            hover_color=SAGE_DARK,
            command=self.submit,
        ).grid(row=0, column=1, padx=(6, 0), sticky="ew")

        self.bind("<Return>", lambda event: self.submit())
        self.after(100, self.name_entry.focus_set)

    def make_field(self, label, row):
        ctk.CTkLabel(
            self,
            text=label,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT,
        ).grid(row=row, column=0, padx=30, pady=(0, 7), sticky="w")

        entry = ctk.CTkEntry(
            self,
            height=42,
            corner_radius=10,
            border_color=BORDER,
            fg_color=WHITE,
            text_color=TEXT,
            placeholder_text=label,
        )
        entry.grid(row=row + 1, column=0, padx=30, pady=(0, 16), sticky="ew")
        return entry

    def submit(self):
        name = self.name_entry.get().strip()
        teach = self.teach_entry.get().strip()
        learn = self.learn_entry.get().strip()

        if not name or not teach or not learn:
            messagebox.showwarning(
                "Missing information",
                "Please complete all three fields.",
                parent=self,
            )
            return

        if teach.casefold() == learn.casefold():
            messagebox.showwarning(
                "Choose different skills",
                "Your teaching skill and learning goal should be different.",
                parent=self,
            )
            return

        for user in self.app.users:
            if user is self.profile:
                continue

            if user["name"].casefold() == name.casefold():
                messagebox.showwarning(
                    "Name already exists",
                    "A profile with that name already exists.",
                    parent=self,
                )
                return

        self.result = {"name": name, "teach": teach, "learn": learn}
        self.destroy()


# --------------------------------------------------
# MAIN APPLICATION
# --------------------------------------------------

class Skill2RelayApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Skill2Relay | Skill-sharing community")
        self.geometry("1120x760")
        self.minsize(900, 620)
        self.configure(fg_color=CREAM)

        self.users = load_users()
        self.search_text = tk.StringVar()
        self.active_page = "home"

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.create_main_area()
        self.show_home()

    # ---------------- SIDEBAR ----------------

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self,
            width=225,
            corner_radius=0,
            fg_color=WHITE,
            border_width=1,
            border_color=BORDER,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(5, weight=1)

        logo = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo.grid(row=0, column=0, padx=20, pady=(28, 35), sticky="ew")

        ctk.CTkLabel(
            logo,
            text="↔",
            width=42,
            height=42,
            corner_radius=13,
            fg_color=SAGE_LIGHT,
            text_color=SAGE_DARK,
            font=ctk.CTkFont(size=25, weight="bold"),
        ).pack(side="left", padx=(0, 10))

        logo_text = ctk.CTkFrame(logo, fg_color="transparent")
        logo_text.pack(side="left")

        ctk.CTkLabel(
            logo_text,
            text="Skill2Relay",
            text_color=TEXT,
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            logo_text,
            text="LEARN TOGETHER",
            text_color=MUTED,
            font=ctk.CTkFont(size=9, weight="bold"),
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkLabel(
            self.sidebar,
            text="WORKSPACE",
            text_color=MUTED,
            font=ctk.CTkFont(size=10, weight="bold"),
        ).grid(row=1, column=0, padx=23, pady=(0, 10), sticky="w")

        self.nav_buttons = {}

        self.nav_buttons["home"] = self.nav_button(
            "⌂    Dashboard", 2, lambda: self.show_home()
        )
        self.nav_buttons["profiles"] = self.nav_button(
            "♙    Community profiles", 3, lambda: self.show_profiles()
        )
        self.nav_buttons["matches"] = self.nav_button(
            "⇄    Find skill matches", 4, lambda: self.show_matches()
        )

        footer = ctk.CTkFrame(
            self.sidebar,
            fg_color=SAGE_LIGHT,
            corner_radius=14,
        )
        footer.grid(row=6, column=0, padx=15, pady=18, sticky="ew")

        ctk.CTkLabel(
            footer,
            text="A little knowledge goes\na long way.",
            text_color=SAGE_DARK,
            justify="left",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=14, pady=(13, 5))

        ctk.CTkLabel(
            footer,
            text="Share a skill. Build a connection.",
            text_color=SAGE_DARK,
            font=ctk.CTkFont(size=10),
            wraplength=175,
        ).pack(anchor="w", padx=14, pady=(0, 13))

    def nav_button(self, label, row, command):
        button = ctk.CTkButton(
            self.sidebar,
            text=label,
            height=43,
            corner_radius=10,
            anchor="w",
            fg_color="transparent",
            hover_color=SAGE_LIGHT,
            text_color=TEXT,
            font=ctk.CTkFont(size=13),
            command=command,
        )
        button.grid(row=row, column=0, padx=13, pady=4, sticky="ew")
        return button

    def set_active_nav(self, page):
        for key, button in self.nav_buttons.items():
            button.configure(
                fg_color=SAGE_LIGHT if key == page else "transparent",
                text_color=SAGE_DARK if key == page else TEXT,
                font=ctk.CTkFont(
                    size=13,
                    weight="bold" if key == page else "normal",
                ),
            )

    # ---------------- MAIN LAYOUT ----------------

    def create_main_area(self):
        self.main = ctk.CTkFrame(self, fg_color=CREAM, corner_radius=0)
        self.main.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)

        self.topbar = ctk.CTkFrame(self.main, fg_color=CREAM)
        self.topbar.grid(row=0, column=0, padx=32, pady=(25, 10), sticky="ew")
        self.topbar.grid_columnconfigure(0, weight=1)

        self.page_title = ctk.CTkLabel(
            self.topbar,
            text="Your dashboard",
            text_color=TEXT,
            font=ctk.CTkFont(family="Segoe UI", size=27, weight="bold"),
        )
        self.page_title.grid(row=0, column=0, sticky="w")

        self.page_subtitle = ctk.CTkLabel(
            self.topbar,
            text="Grow your skills through your community.",
            text_color=MUTED,
            font=ctk.CTkFont(size=13),
        )
        self.page_subtitle.grid(row=1, column=0, pady=(4, 0), sticky="w")

        ctk.CTkButton(
            self.topbar,
            text="+  Create profile",
            height=42,
            corner_radius=11,
            fg_color=SAGE,
            hover_color=SAGE_DARK,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.create_profile,
        ).grid(row=0, column=1, rowspan=2, padx=(15, 0), sticky="e")

        self.content = ctk.CTkFrame(self.main, fg_color="transparent")
        self.content.grid(row=1, column=0, padx=32, pady=(8, 28), sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def update_heading(self, title, subtitle):
        self.page_title.configure(text=title)
        self.page_subtitle.configure(text=subtitle)

    # ---------------- DASHBOARD ----------------

    def show_home(self):
        self.active_page = "home"
        self.set_active_nav("home")
        self.update_heading(
            "Your dashboard",
            "Grow your skills through your community.",
        )
        self.clear_content()

        page = ctk.CTkScrollableFrame(
            self.content,
            fg_color="transparent",
            scrollbar_button_color="#C9D6CB",
        )
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure((0, 1, 2), weight=1, uniform="stats")

        cards = [
            ("Community members", str(len(self.users)), SAGE_LIGHT, SAGE_DARK),
            ("Skills to share", str(len({u["teach"].casefold() for u in self.users})),
             BLUE_LIGHT, BLUE),
            ("Possible exchanges", str(len(self.find_full_match_pairs())),
             "#F6EEDC", "#9B7936"),
        ]

        for column, (label, value, background, foreground) in enumerate(cards):
            card = ctk.CTkFrame(
                page,
                fg_color=WHITE,
                corner_radius=16,
                border_width=1,
                border_color=BORDER,
            )
            card.grid(row=0, column=column, padx=(0 if column == 0 else 8, 8),
                      pady=(4, 20), sticky="ew")

            ctk.CTkLabel(
                card,
                text=label,
                text_color=MUTED,
                font=ctk.CTkFont(size=12),
            ).pack(anchor="w", padx=17, pady=(16, 8))

            ctk.CTkLabel(
                card,
                text=value,
                text_color=TEXT,
                font=ctk.CTkFont(size=29, weight="bold"),
            ).pack(anchor="w", padx=17, pady=(0, 5))

            ctk.CTkFrame(
                card,
                height=4,
                corner_radius=3,
                fg_color=background,
            ).pack(fill="x", padx=17, pady=(3, 16))

        welcome = ctk.CTkFrame(
            page,
            fg_color=SAGE_LIGHT,
            corner_radius=18,
        )
        welcome.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 22))
        welcome.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            welcome,
            text="Everyone has something worth sharing.",
            text_color=SAGE_DARK,
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=0, padx=22, pady=(22, 7), sticky="w")

        ctk.CTkLabel(
            welcome,
            text="Teach what you know, learn something new, and find people "
                 "who can help you grow.",
            text_color=SAGE_DARK,
            font=ctk.CTkFont(size=13),
            wraplength=600,
            justify="left",
        ).grid(row=1, column=0, padx=22, pady=(0, 17), sticky="w")

        ctk.CTkButton(
            welcome,
            text="Explore skill matches  →",
            height=38,
            fg_color=SAGE,
            hover_color=SAGE_DARK,
            command=self.show_matches,
        ).grid(row=2, column=0, padx=22, pady=(0, 22), sticky="w")

        section = ctk.CTkFrame(page, fg_color="transparent")
        section.grid(row=2, column=0, columnspan=3, sticky="ew")
        section.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            section,
            text="Meet the community",
            text_color=TEXT,
            font=ctk.CTkFont(size=19, weight="bold"),
        ).grid(row=0, column=0, pady=(0, 12), sticky="w")

        if not self.users:
            self.empty_state(
                section,
                "Your community starts here",
                "Create the first profile and start building skill connections.",
                row=1,
            )
        else:
            for index, user in enumerate(self.users[:4]):
                self.profile_card(section, user, index + 1, row=index + 1)

            if len(self.users) > 4:
                ctk.CTkButton(
                    section,
                    text=f"View all {len(self.users)} profiles  →",
                    fg_color="transparent",
                    hover_color=SAGE_LIGHT,
                    text_color=SAGE_DARK,
                    command=self.show_profiles,
                ).grid(row=5, column=0, pady=10, sticky="w")

    # ---------------- PROFILE LIST ----------------

    def show_profiles(self):
        self.active_page = "profiles"
        self.set_active_nav("profiles")
        self.update_heading(
            "Community profiles",
            "Discover what people can teach and what they want to learn.",
        )
        self.clear_content()

        wrapper = ctk.CTkFrame(self.content, fg_color="transparent")
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.grid_columnconfigure(0, weight=1)
        wrapper.grid_rowconfigure(2, weight=1)

        self.search_entry = ctk.CTkEntry(
            wrapper,
            textvariable=self.search_text,
            placeholder_text="Search names or skills...",
            height=42,
            corner_radius=11,
            border_color=BORDER,
            fg_color=WHITE,
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        self.search_entry.bind("<KeyRelease>", lambda event: self.refresh_profile_list())

        self.profile_count = ctk.CTkLabel(
            wrapper,
            text="",
            text_color=MUTED,
            font=ctk.CTkFont(size=12),
        )
        self.profile_count.grid(row=1, column=0, sticky="w", pady=(0, 8))

        self.profile_list = ctk.CTkScrollableFrame(
            wrapper,
            fg_color="transparent",
            scrollbar_button_color="#C9D6CB",
        )
        self.profile_list.grid(row=2, column=0, sticky="nsew")
        self.profile_list.grid_columnconfigure(0, weight=1)

        self.refresh_profile_list()

    def refresh_profile_list(self):
        if not hasattr(self, "profile_list") or not self.profile_list.winfo_exists():
            return

        for widget in self.profile_list.winfo_children():
            widget.destroy()

        query = self.search_text.get().strip().casefold()
        filtered = [
            user for user in self.users
            if query in user["name"].casefold()
            or query in user["teach"].casefold()
            or query in user["learn"].casefold()
        ]

        self.profile_count.configure(
            text=f"{len(filtered)} profile{'s' if len(filtered) != 1 else ''}"
        )

        if not filtered:
            self.empty_state(
                self.profile_list,
                "No profiles found",
                "Try another search or create a new profile.",
                row=0,
            )
            return

        for index, user in enumerate(filtered):
            self.profile_card(self.profile_list, user, index + 1, row=index)

    def profile_card(self, parent, user, number, row):
        card = ctk.CTkFrame(
            parent,
            fg_color=WHITE,
            corner_radius=14,
            border_width=1,
            border_color=BORDER,
        )
        card.grid(row=row, column=0, padx=2, pady=6, sticky="ew")
        card.grid_columnconfigure(1, weight=1)

        initials = "".join(part[0] for part in user["name"].split()[:2]).upper()
        avatar_colours = [SAGE_LIGHT, BLUE_LIGHT, "#F6EEDC", "#F3E7EF"]
        avatar_text_colours = [SAGE_DARK, BLUE, "#9B7936", "#92617D"]
        colour_index = (number - 1) % len(avatar_colours)

        ctk.CTkLabel(
            card,
            text=initials or "?",
            width=48,
            height=48,
            corner_radius=15,
            fg_color=avatar_colours[colour_index],
            text_color=avatar_text_colours[colour_index],
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, rowspan=2, padx=15, pady=15)

        ctk.CTkLabel(
            card,
            text=user["name"],
            text_color=TEXT,
            font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=0, column=1, padx=(0, 10), pady=(15, 4), sticky="w")

        skill_row = ctk.CTkFrame(card, fg_color="transparent")
        skill_row.grid(row=1, column=1, padx=(0, 10), pady=(0, 15), sticky="w")

        ctk.CTkLabel(
            skill_row,
            text=f"TEACH  {user['teach']}",
            fg_color=SAGE_LIGHT,
            text_color=SAGE_DARK,
            corner_radius=7,
            padx=9,
            pady=5,
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(side="left", padx=(0, 6))

        ctk.CTkLabel(
            skill_row,
            text=f"LEARN  {user['learn']}",
            fg_color=BLUE_LIGHT,
            text_color=BLUE,
            corner_radius=7,
            padx=9,
            pady=5,
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(side="left")

        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.grid(row=0, column=2, rowspan=2, padx=12)

        ctk.CTkButton(
            actions,
            text="Edit",
            width=65,
            height=30,
            fg_color=SAGE_LIGHT,
            hover_color="#D5E5D8",
            text_color=SAGE_DARK,
            command=lambda person=user: self.edit_profile(person),
        ).pack(pady=(0, 6))

        ctk.CTkButton(
            actions,
            text="Delete",
            width=65,
            height=30,
            fg_color=RED_LIGHT,
            hover_color="#F0D6D3",
            text_color=RED,
            command=lambda person=user: self.delete_profile(person),
        ).pack()

    def empty_state(self, parent, heading, description, row):
        box = ctk.CTkFrame(
            parent,
            fg_color=WHITE,
            corner_radius=15,
            border_width=1,
            border_color=BORDER,
        )
        box.grid(row=row, column=0, padx=2, pady=6, sticky="ew")

        ctk.CTkLabel(
            box,
            text="🌱",
            font=ctk.CTkFont(size=29),
        ).pack(pady=(22, 5))

        ctk.CTkLabel(
            box,
            text=heading,
            text_color=TEXT,
            font=ctk.CTkFont(size=17, weight="bold"),
        ).pack(pady=(0, 5))

        ctk.CTkLabel(
            box,
            text=description,
            text_color=MUTED,
            font=ctk.CTkFont(size=12),
            wraplength=480,
        ).pack(padx=20, pady=(0, 22))

    # ---------------- CREATE / EDIT / DELETE ----------------

    def create_profile(self):
        dialog = ProfileDialog(self)
        self.wait_window(dialog)

        if not dialog.result:
            return

        self.users.append(dialog.result)
        if save_users(self.users):
            self.show_profiles()
            messagebox.showinfo(
                "Welcome aboard",
                f"{dialog.result['name']} has joined the community!",
                parent=self,
            )
        else:
            self.users.pop()

    def edit_profile(self, profile):
        dialog = ProfileDialog(self, profile)
        self.wait_window(dialog)

        if not dialog.result:
            return

        original = profile.copy()
        profile.update(dialog.result)

        if save_users(self.users):
            self.refresh_current_page()
            messagebox.showinfo(
                "Profile updated",
                f"{profile['name']}'s profile has been updated.",
                parent=self,
            )
        else:
            profile.clear()
            profile.update(original)

    def delete_profile(self, profile):
        confirmed = messagebox.askyesno(
            "Delete profile?",
            f"Are you sure you want to delete {profile['name']}'s profile?\n\n"
            "This action cannot be undone.",
            icon="warning",
            parent=self,
        )

        if not confirmed:
            return

        index = self.users.index(profile)
        self.users.pop(index)

        if save_users(self.users):
            self.refresh_current_page()
        else:
            self.users.insert(index, profile)

    def refresh_current_page(self):
        if self.active_page == "profiles":
            self.show_profiles()
        elif self.active_page == "matches":
            self.show_matches()
        else:
            self.show_home()

    # ---------------- MATCHING ----------------

    def find_full_match_pairs(self):
        """Return unique pairs where both people can exchange skills."""
        pairs = []

        for i, person_a in enumerate(self.users):
            for person_b in self.users[i + 1:]:
                a_teach = person_a["teach"].casefold()
                a_learn = person_a["learn"].casefold()
                b_teach = person_b["teach"].casefold()
                b_learn = person_b["learn"].casefold()

                if a_teach == b_learn and a_learn == b_teach:
                    pairs.append((person_a, person_b))

        return pairs

    def find_one_way_matches(self):
        """Find pairs where one person can teach the skill the other wants."""
        matches = []

        for person_a in self.users:
            for person_b in self.users:
                if person_a is person_b:
                    continue

                if person_a["learn"].casefold() == person_b["teach"].casefold():
                    matches.append((person_a, person_b))

        return matches

    def show_matches(self):
        self.active_page = "matches"
        self.set_active_nav("matches")
        self.update_heading(
            "Skill connections",
            "Find people who can help you learn something new.",
        )
        self.clear_content()

        page = ctk.CTkScrollableFrame(
            self.content,
            fg_color="transparent",
            scrollbar_button_color="#C9D6CB",
        )
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            page,
            text="Full skill exchanges",
            text_color=TEXT,
            font=ctk.CTkFont(size=19, weight="bold"),
        ).grid(row=0, column=0, sticky="w", pady=(4, 4))

        ctk.CTkLabel(
            page,
            text="Both people can teach each other the skill they want to learn.",
            text_color=MUTED,
            font=ctk.CTkFont(size=12),
        ).grid(row=1, column=0, sticky="w", pady=(0, 12))

        full_pairs = self.find_full_match_pairs()

        if not full_pairs:
            self.empty_state(
                page,
                "No full exchanges yet",
                "Add more profiles with complementary skills to discover mutual matches.",
                row=2,
            )
        else:
            for index, (a, b) in enumerate(full_pairs):
                card = ctk.CTkFrame(
                    page,
                    fg_color=WHITE,
                    corner_radius=14,
                    border_width=1,
                    border_color=BORDER,
                )
                card.grid(row=index + 2, column=0, sticky="ew", pady=5)
                card.grid_columnconfigure(0, weight=1)

                ctk.CTkLabel(
                    card,
                    text=f"{a['name']}  ↔  {b['name']}",
                    text_color=TEXT,
                    font=ctk.CTkFont(size=15, weight="bold"),
                ).grid(row=0, column=0, padx=16, pady=(14, 6), sticky="w")

                ctk.CTkLabel(
                    card,
                    text=f"{a['name']} teaches {a['teach']}  •  "
                         f"{b['name']} teaches {b['teach']}",
                    text_color=SAGE_DARK,
                    font=ctk.CTkFont(size=12),
                    wraplength=650,
                ).grid(row=1, column=0, padx=16, pady=(0, 14), sticky="w")

        start_row = len(full_pairs) + 3

        ctk.CTkLabel(
            page,
            text="One-way learning opportunities",
            text_color=TEXT,
            font=ctk.CTkFont(size=19, weight="bold"),
        ).grid(row=start_row, column=0, sticky="w", pady=(20, 4))

        ctk.CTkLabel(
            page,
            text="One person can teach a skill the other wants to learn.",
            text_color=MUTED,
            font=ctk.CTkFont(size=12),
        ).grid(row=start_row + 1, column=0, sticky="w", pady=(0, 12))

        one_way = self.find_one_way_matches()

        if not one_way:
            self.empty_state(
                page,
                "No one-way matches yet",
                "New members can create more learning opportunities.",
                row=start_row + 2,
            )
        else:
            for index, (learner, teacher) in enumerate(one_way):
                card = ctk.CTkFrame(
                    page,
                    fg_color=WHITE,
                    corner_radius=14,
                    border_width=1,
                    border_color=BORDER,
                )
                card.grid(
                    row=start_row + 2 + index,
                    column=0,
                    sticky="ew",
                    pady=5,
                )

                ctk.CTkLabel(
                    card,
                    text=f"{teacher['name']} can help {learner['name']}",
                    text_color=TEXT,
                    font=ctk.CTkFont(size=14, weight="bold"),
                ).pack(anchor="w", padx=16, pady=(13, 4))

                ctk.CTkLabel(
                    card,
                    text=f"{teacher['name']} teaches {teacher['teach']}  ·  "
                         f"{learner['name']} wants to learn {learner['learn']}",
                    text_color=BLUE,
                    font=ctk.CTkFont(size=12),
                    wraplength=650,
                ).pack(anchor="w", padx=16, pady=(0, 13))


# --------------------------------------------------
# START APPLICATION
# --------------------------------------------------

if __name__ == "__main__":
    app = Skill2RelayApp()
    app.mainloop()




#   py -m pip install customtkinter
