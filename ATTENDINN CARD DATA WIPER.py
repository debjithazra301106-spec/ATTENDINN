import tkinter as tk
from tkinter import messagebox
import serial
import time

# --- CONFIGURATION ---
PORT = 'COM6'  
BAUD_RATE = 9600

class RFIDWiper:
    def __init__(self, root):
        self.root = root
        self.root.title("ATTENDINN : Card Wiper Tool")
        self.root.geometry("400x350")
        self.root.configure(bg="#fbe9e7") 

        self.ser = None
        self.connect_serial()
        self.setup_ui()

    def connect_serial(self):
        try:
            self.ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
            time.sleep(2)
            self.ser.reset_input_buffer()
        except Exception as e:
            print(f"Serial Error: {e}")

    def setup_ui(self):
        header = tk.Frame(self.root, bg="#d32f2f")
        header.pack(fill="x")
        tk.Label(header, text="CARD ERASER TOOL", font=("Arial", 14, "bold"), fg="white", bg="#d32f2f").pack(pady=15)

        content = tk.Frame(self.root, bg="#fbe9e7", padx=20, pady=20)
        content.pack(expand=True, fill="both")

        tk.Label(content, text="This process will overwrite the \nStudent UID on the card with '0'.", 
                 font=("Arial", 10), bg="#fbe9e7", fg="#b71c1c").pack(pady=10)

        self.status_var = tk.StringVar(value="Status: Ready")
        tk.Label(content, textvariable=self.status_var, font=("Arial", 10, "italic"), bg="#fbe9e7").pack(pady=20)

        self.btn_wipe = tk.Button(content, text="WIPE CARD DATA", command=self.confirm_wipe, 
                                  bg="#d32f2f", fg="white", font=("Arial", 12, "bold"), width=20, height=2)
        self.btn_wipe.pack(pady=10)

    def confirm_wipe(self):
        # FIXED: Changed askwarning to askyesno
        confirm = messagebox.askyesno("Confirm Format", "Are you sure you want to clear this card?\nThis cannot be undone.")
        if confirm: # If user clicks 'Yes'
            self.execute_wipe()

    def execute_wipe(self):
        if not self.ser:
            messagebox.showerror("Error", "ESP32 not connected!")
            return

        try:
            self.status_var.set("Status: Waiting for card...")
            self.btn_wipe.config(state="disabled")
            self.root.update()

            self.ser.write(b"WRITE:0\n") 
            
            # Allow time for user to place card and ESP32 to write
            time.sleep(3) 
            resp = self.ser.readline().decode('utf-8', errors='ignore').strip()

            if "WRITE_SUCCESS" in resp:
                self.status_var.set("Status: Card Wiped Successfully! ✅")
                messagebox.showinfo("Success", "The card is now blank (UID reset to 0).")
            else:
                self.status_var.set("Status: Wipe Failed ❌")
                messagebox.showerror("Error", "Could not clear card. Ensure it is placed correctly.")

        except Exception as e:
            messagebox.showerror("Error", f"Operation failed: {e}")
        finally:
            self.btn_wipe.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = RFIDWiper(root)
    root.mainloop()
