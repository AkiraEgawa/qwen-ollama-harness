import json
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox


class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Agent Manager")
        self.root.geometry("400x400")
        self.launch_config = None

        self.start_button = tk.Button(root, text="Start Agent", command=self.start_agent)
        self.start_button.pack(pady=10)

        self.folder_label = tk.Label(root, text="Project Root Folder:", font=("Helvetica", 12))
        self.folder_label.pack()

        self.folder_var = tk.StringVar()
        self.folder_entry = tk.Entry(root, textvariable=self.folder_var, width=30)
        self.folder_entry.pack(pady=5)

        self.select_folder_button = tk.Button(root, text="Select Folder", command=self.select_folder)
        self.select_folder_button.pack(pady=5)

        self.settings_button = tk.Button(root, text="Settings", command=self.open_settings)
        self.settings_button.pack(pady=10)

        self.file_label = tk.Label(root, text="Choose Session File:", font=("Helvetica", 12))
        self.file_label.pack()

        self.file_var = tk.StringVar()
        self.file_entry = tk.Entry(root, textvariable=self.file_var, width=30)
        self.file_entry.pack(pady=5)

        self.select_file_button = tk.Button(root, text="Select File", command=self.select_file)
        self.select_file_button.pack(pady=5)

        self.session_label = tk.Label(root, text="Session Name:", font=("Helvetica", 12))
        self.session_label.pack()

        self.session_var = tk.StringVar()
        self.session_entry = tk.Entry(root, textvariable=self.session_var, width=30)
        self.session_entry.pack(pady=5)

    def select_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.folder_var.set(folder_path)

    def select_file(self):
        sessions_dir = Path("data/sessions")
        sessions_dir.mkdir(parents=True, exist_ok=True)
        file_path = filedialog.askopenfilename(
            initialdir=str(sessions_dir),
            title="Select Session File",
            filetypes=(("JSONL files", "*.jsonl"), ("All files", "*.*")),
        )
        if file_path:
            self.file_var.set(file_path)

    def open_settings(self):
        settings_path = Path("util/settings.json")
        try:
            subprocess.Popen(["notepad", str(settings_path)])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open settings file: {e}")

    def start_agent(self):
        root_path = self.folder_var.get().strip()
        if not root_path:
            messagebox.showwarning("Warning", "Please select a project root folder.")
            return

        # 1. Load settings.json
        settings_path = Path("util/settings.json")
        try:
            with settings_path.open("r", encoding="utf-8") as f:
                settings = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Could not load util/settings.json: {e}")
            return

        # 2. Resolve session file (existing file vs. session name)
        selected_file = self.file_var.get().strip()
        session_name = self.session_var.get().strip()

        if selected_file:
            session_path = Path(selected_file)
            if not session_path.exists():
                messagebox.showerror("Error", f"Selected session file does not exist:\n{session_path}")
                return
        elif session_name:
            # Strip .jsonl if the user typed it manually
            clean_name = session_name[:-6] if session_name.endswith(".jsonl") else session_name
            session_path = Path("data/sessions") / f"{clean_name}.jsonl"
            session_path.parent.mkdir(parents=True, exist_ok=True)

            # Try opening; if missing, create it and then open
            try:
                with session_path.open("r", encoding="utf-8"):
                    pass
            except FileNotFoundError:
                session_path.touch()
                with session_path.open("r", encoding="utf-8"):
                    pass
        else:
            messagebox.showwarning("Warning", "Please provide a session name or choose a session file.")
            return

        result = {
            "root": root_path,
            "settings": settings,
            "session": session_path.name,
        }

        self.launch_config = result
        print(json.dumps(result, indent=4))
        return result


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()