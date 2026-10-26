import mysql.connector
import tkinter as tk
from tkinter import messagebox

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="patient_db"
)

if db.is_connected():
    print("Database Connected Successfully!")

db.close()
def save_appointment():
    name = name_entry.get()
    age = age_entry.get()
    date = date_entry.get()
    doctor = doctor_var.get()

    if name and age and date:
        messagebox.showinfo(
            "Appointment",
            f"Patient: {name}\nAge: {age}\n"
            f"Doctor: {doctor}\nDate: {date}"
        )
    else:
        messagebox.showerror(
            "Error", "Please fill all fields"
        )
root = tk.Tk()
root.title("Patient Appointment System")
root.geometry("400x350")

tk.Label(
    root,
    text="Patient Appointment System",
    font=("Arial", 16, "bold")
).pack(pady=15)

tk.Label(root, text="Patient Name").pack()
name_entry = tk.Entry(root)
name_entry.pack()

tk.Label(root, text="Patient Age").pack()
age_entry = tk.Entry(root)
age_entry.pack()

tk.Label(root, text="Appointment Date (YYYY-MM-DD)").pack()
date_entry = tk.Entry(root)
date_entry.pack()
tk.Label(root, text="Select Doctor").pack()

doctor_var = tk.StringVar(value="General Physician")
tk.OptionMenu(
    root, doctor_var,
    "General Physician",
    "Dermatologist",
    "Cardiologist"
).pack()
tk.Button(
    root,
    text="Save Appointment",
    command=save_appointment
).pack(pady=10)
root.mainloop()