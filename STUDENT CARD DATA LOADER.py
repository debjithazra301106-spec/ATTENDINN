import tkinter as tk
from tkinter import messagebox, ttk
import pandas as pd
import serial
import time
import os
from tkcalendar import Calendar 

# --- CONFIGURATION ---
PORT = 'COM6' 
DB_FILE = 'STUDENT DATABASE 2025.csv'

class StudentRFIDSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("ATTENDINN : Student Data Loader")
        self.root.geometry("500x350")
        self.root.configure(bg="#f5f5f5")
        
        self.ser = None
        self.connect_serial()

        self.is_update_mode = False
        self.view_only_mode = False
        self.current_uid = None
        self.student_data = {}
        
        self.fields = ["UID", "NAME", "STREAM", "BLOOD GROUP", "ADDRESS", "ENROLLMENT NUMBER", 
                       "YEAR OF REGISTRATION", "STUDENT CONTACT", "EMERGENCY CONTACT", 
                       "DATE OF BIRTH", "CARD VALIDITY YEAR", "CAMPUS NAME"]
        self.entries = {}
        self.dob_btn = None 

        # --- REDESIGNED HEADER ---
        self.header = tk.Frame(self.root, bg="#1976D2", height=70)
        self.header.pack(fill="x")
        tk.Label(self.header, text="STUDENT DATA LOADER", font=("Arial", 16, "bold"), fg="white", bg="#1976D2").pack(pady=20)

        # --- SEARCH CONTENT ---
        self.search_frame = tk.Frame(self.root, padx=30, pady=30, bg="#f5f5f5")
        self.search_frame.pack(expand=True, fill="both")

        tk.Label(self.search_frame, text="Enter Enrollment Number to Begin", font=("Arial", 11), bg="#f5f5f5", fg="#555").pack(pady=5)
        
        self.enroll_search_ent = tk.Entry(self.search_frame, width=25, font=("Arial", 14), bd=0, highlightthickness=1, highlightbackground="#ccc")
        self.enroll_search_ent.pack(pady=10, ipady=5)
        self.enroll_search_ent.focus_set()

        self.btn_proceed = tk.Button(self.search_frame, text="CHECK & PROCEED", command=self.check_enrollment, 
                                    bg="#1976D2", fg="white", font=("Arial", 10, "bold"), width=25, height=2, 
                                    relief="flat", cursor="hand2")
        self.btn_proceed.pack(pady=20)

        self.root.update_idletasks()

    def connect_serial(self):
        try:
            self.ser = serial.Serial(PORT, 9600, timeout=1)
            time.sleep(1)
            self.ser.reset_input_buffer()
        except Exception:
            print("Offline Mode")

    def handle_others(self, event, combo_box):
        if combo_box.get() == "OTHERS":
            other_val_win = tk.Toplevel(self.main_win)
            other_val_win.title("Custom Entry")
            other_val_win.geometry("300x180")
            other_val_win.configure(bg="#f5f5f5")
            
            tk.Label(other_val_win, text="Enter Custom Detail", font=("Arial", 10, "bold"), bg="#f5f5f5").pack(pady=15)
            entry = tk.Entry(other_val_win, width=25, font=("Arial", 11))
            entry.pack(pady=5, ipady=3)
            entry.focus_set()

            def save_other():
                val = entry.get().strip().upper()
                if val:
                    current_values = list(combo_box['values'])
                    if val not in current_values:
                        combo_box['values'] = current_values + [val]
                    combo_box.config(state='normal')
                    combo_box.set(val)
                    combo_box.config(state='readonly')
                    other_val_win.destroy()

            tk.Button(other_val_win, text="SUBMIT", command=save_other, bg="#4CAF50", fg="white", font=("Arial", 9, "bold"), width=15).pack(pady=15)

    def open_calendar_popup(self, target_entry):
        top = tk.Toplevel(self.main_win)
        top.title("Select Date")
        cal = Calendar(top, selectmode='day', date_pattern='dd-mm-yyyy')
        cal.pack(padx=10, pady=10)
        def set_date():
            target_entry.delete(0, tk.END)
            target_entry.insert(0, cal.get_date())
            top.destroy()
        tk.Button(top, text="SELECT", command=set_date, bg="#1976D2", fg="white").pack(pady=5)

    def format_dob(self, event):
        if event.keysym == 'BackSpace': return
        text = self.entries["DATE OF BIRTH"].get().replace("-", "")
        new_text = ""
        if len(text) > 8: text = text[:8]
        for i, char in enumerate(text):
            if i == 2 or i == 4: new_text += "-"
            new_text += char
        self.entries["DATE OF BIRTH"].delete(0, tk.END)
        self.entries["DATE OF BIRTH"].insert(0, new_text)

    def check_enrollment(self):
        enroll_no = self.enroll_search_ent.get().strip()
        if not enroll_no:
            messagebox.showwarning("Input Required", "Please enter Enrollment Number.")
            return

        if not os.path.exists(DB_FILE):
            pd.DataFrame(columns=self.fields).to_csv(DB_FILE, index=False)

        df = pd.read_csv(DB_FILE)
        match = df[df['ENROLLMENT NUMBER'].astype(str) == enroll_no]

        if not match.empty:
            self.student_data = match.iloc[0].to_dict()
            choice = messagebox.askyesnocancel("Record Found", "Open in VIEW ONLY Mode?\n(Yes: View Only, No: Edit Mode)")
            if choice is True: 
                self.view_only_mode, self.is_update_mode = True, False
            elif choice is False:
                self.view_only_mode, self.is_update_mode = False, True
            else: return
            self.current_uid = self.student_data['UID']
        else:
            messagebox.showinfo("New Entry", "No record found. Creating a fresh entry.")
            self.view_only_mode, self.is_update_mode = False, False
            self.current_uid = self.generate_new_uid(df)
            self.student_data = {"ENROLLMENT NUMBER": enroll_no, "UID": self.current_uid}
        
        self.open_main_window()

    def generate_new_uid(self, df):
        if df.empty or 'UID' not in df.columns: return "1001"
        try: return str(int(df['UID'].max()) + 1)
        except: return "1001"

    def open_main_window(self):
        self.main_win = tk.Toplevel(self.root)
        self.main_win.title("ATTENDINN : Student Details Form")
        self.main_win.geometry("600x850")
        self.main_win.configure(bg="white")
        
        # Header for the secondary window
        header_form = tk.Frame(self.main_win, bg="#1976D2", height=50)
        header_form.pack(fill="x")
        mode_text = "VIEW MODE" if self.view_only_mode else "EDIT/NEW MODE"
        tk.Label(header_form, text=f"STUDENT PROFILE : {mode_text}", font=("Arial", 12, "bold"), fg="white", bg="#1976D2").pack(pady=10)

        container = tk.Frame(self.main_win, bg="white")
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, padx=30, pady=20, bg="white")

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        streams = ["CSE CORE", "CSE AIML", "CSBS", "IOT", "EE", "ME", "IOTCSBT", "ECE", "MBA", "BCA", "MCA", "BBA", "OTHERS"]
        blood_groups = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-", "OTHERS"]
        campuses = ["Kolkata", "New Town", "OTHERS"]

        for i, field in enumerate(self.fields):
            tk.Label(scrollable_frame, text=field, font=("Arial", 8, "bold"), fg="#777", bg="white").grid(row=i*2, column=0, sticky="w", pady=(10,0))
            
            if field in ["STREAM", "BLOOD GROUP", "CAMPUS NAME"]:
                vals = streams if field == "STREAM" else (blood_groups if field == "BLOOD GROUP" else campuses)
                ent = ttk.Combobox(scrollable_frame, values=vals, width=45, state="readonly")
                ent.bind("<<ComboboxSelected>>", lambda e, cb=ent: self.handle_others(e, cb))
                ent.grid(row=i*2+1, column=0, columnspan=2, pady=(2,10), ipady=3)
            elif field == "DATE OF BIRTH":
                dob_frame = tk.Frame(scrollable_frame, bg="white")
                dob_frame.grid(row=i*2+1, column=0, columnspan=2, sticky="w", pady=(2,10))
                ent = tk.Entry(dob_frame, width=35, font=("Arial", 10), bd=1, relief="solid")
                ent.pack(side="left", ipady=3)
                ent.bind("<KeyRelease>", self.format_dob)
                self.dob_btn = tk.Button(dob_frame, text="📅", command=lambda e=ent: self.open_calendar_popup(e), 
                                        bg="#f0f0f0", relief="flat", padx=10)
                self.dob_btn.pack(side="left", padx=5)
            else:
                ent = tk.Entry(scrollable_frame, width=48, font=("Arial", 10), bd=1, relief="solid")
                ent.grid(row=i*2+1, column=0, columnspan=2, pady=(2,10), ipady=3)
                if field not in ["UID", "ENROLLMENT NUMBER"]:
                    ph = f"Enter {field.lower()}"
                    ent.insert(0, ph)
                    ent.config(fg='grey')
                    ent.bind("<FocusIn>", lambda e, f=ent, p=ph: self.clear_placeholder(f, p))
                    ent.bind("<FocusOut>", lambda e, f=ent, p=ph: self.add_placeholder(f, p))

            self.entries[field] = ent

        self.populate_and_lock()

        # Action Button
        btn_color = "#4CAF50" if self.view_only_mode else "#1976D2"
        btn_text = "PUSH DATA TO CARD" if self.view_only_mode else "SAVE & PUSH DATA"
        self.btn_submit = tk.Button(scrollable_frame, text=btn_text, command=self.submit_workflow, 
                                   bg=btn_color, fg="white", font=("Arial", 11, "bold"), width=40, height=2, relief="flat")
        self.btn_submit.grid(row=len(self.fields)*2, column=0, columnspan=2, pady=30)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.main_win.grab_set()

    def clear_placeholder(self, entry, placeholder):
        if isinstance(entry, tk.Entry) and entry.get() == placeholder:
            entry.delete(0, tk.END)
            entry.config(fg='black')

    def add_placeholder(self, entry, placeholder):
        if isinstance(entry, tk.Entry) and entry.get() == "":
            entry.insert(0, placeholder)
            entry.config(fg='grey')

    def populate_and_lock(self):
        for field in self.fields:
            self.entries[field].config(state='normal')
            val = self.student_data.get(field, "")
            if pd.isna(val): val = ""
            if str(val) != "":
                if isinstance(self.entries[field], ttk.Combobox):
                    self.entries[field].set(str(val))
                else:
                    self.entries[field].delete(0, tk.END)
                    self.entries[field].insert(0, str(val))
                    if isinstance(self.entries[field], tk.Entry):
                        self.entries[field].config(fg='black')

            if self.view_only_mode or field in ["UID", "ENROLLMENT NUMBER"]:
                self.entries[field].config(state='disabled')
            elif field in ["STREAM", "BLOOD GROUP", "CAMPUS NAME"]:
                self.entries[field].config(state='readonly')
        
        if self.view_only_mode and self.dob_btn:
            self.dob_btn.config(state='disabled')

    def submit_workflow(self):
        if not self.ser: 
            messagebox.showwarning("Offline", "Serial Port not connected.")
            return
            
        self.ser.reset_input_buffer()
        self.ser.write(b"CHECK_SENSOR\n")
        time.sleep(1)
        resp = self.ser.readline().decode('utf-8', errors='ignore').strip()
        if "SENSOR_READY" in resp:
            self.done_popup = tk.Toplevel(self.main_win)
            self.done_popup.title("Card Sync")
            self.done_popup.geometry("300x150")
            tk.Label(self.done_popup, text="📡 Place RFID Card on Reader", font=("Arial", 10, "bold")).pack(pady=20)
            tk.Button(self.done_popup, text="DONE", width=15, command=self.write_and_save, bg="#1976D2", fg="white").pack()
        else: messagebox.showerror("Error", "Sensor not ready")

    def write_and_save(self):
        self.ser.write(f"WRITE:{self.current_uid}\n".encode())
        if hasattr(self, 'done_popup'): self.done_popup.destroy()
        time.sleep(2)
        resp = self.ser.readline().decode('utf-8', errors='ignore').strip()
        if "WRITE_SUCCESS" in resp:
            if not self.view_only_mode: self.save_to_csv()
            messagebox.showinfo("Success", "Card Loaded Successfully!")
            self.main_win.destroy()
            self.enroll_search_ent.delete(0, tk.END)
        else: messagebox.showerror("Error", "Write Failed. Try Again.")

    def save_to_csv(self):
        for f in self.fields: self.entries[f].config(state='normal')
        data_row = {f: ("" if "Enter " in str(self.entries[f].get()) else self.entries[f].get()) for f in self.fields}
        df = pd.read_csv(DB_FILE)
        if self.is_update_mode:
            mask = df['UID'].astype(str) == str(self.current_uid)
            for f in self.fields: df.loc[mask, f] = data_row[f]
        else:
            df = pd.concat([df, pd.DataFrame([data_row])], ignore_index=True)
        df.to_csv(DB_FILE, index=False)

if __name__ == "__main__":
    root = tk.Tk()
    app = StudentRFIDSystem(root)
    root.mainloop()
