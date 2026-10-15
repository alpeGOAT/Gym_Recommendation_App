import queue
import threading
from pathlib import Path

import tkinter as tk
from tkinter import ttk, messagebox

from main import (
    prepare_transactions,
    create_rules,
    get_exercise_recommendation,
)


def normalize_name(name):
    return " ".join(str(name).split()).casefold()


class GymRecommendationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gym Recommendation System")
        self.root.geometry("1000x650")
        self.root.minsize(800, 550)

        self.rules = None
        self.exercise_names = []
        self.filtered_names = []
        self.load_queue = queue.Queue()

        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(
            value="Veri yükleniyor ve öneri kuralları hazırlanıyor..."
        )

        self.configure_style()
        self.create_widgets()

        self.search_var.trace_add("write", self.filter_exercises)

        threading.Thread(
            target=self.load_data,
            daemon=True
        ).start()

        self.root.after(100, self.check_loading)

    def configure_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Title.TLabel", font=("Segoe UI", 21, "bold"))
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10), padding=8)
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=30)
        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 10, "bold")
        )

    def create_widgets(self):
        container = ttk.Frame(self.root, padding=20)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text="Gym Recommendation System",
            style="Title.TLabel"
        ).pack(anchor="w")

        ttk.Label(
            container,
            text="Bir egzersiz seçerek geçmiş antrenmanlara dayalı öneriler al."
        ).pack(anchor="w", pady=(5, 15))

        selection_frame = ttk.LabelFrame(
            container,
            text="Egzersiz seçimi",
            padding=12
        )
        selection_frame.pack(fill="x")

        ttk.Label(
            selection_frame,
            text="Egzersiz ara:"
        ).pack(anchor="w")

        self.search_entry = ttk.Entry(
            selection_frame,
            textvariable=self.search_var,
            state="disabled"
        )
        self.search_entry.pack(fill="x", pady=(5, 8))

        list_frame = ttk.Frame(selection_frame)
        list_frame.pack(fill="x")

        self.exercise_list = tk.Listbox(
            list_frame,
            height=6,
            selectmode=tk.SINGLE,
            exportselection=False,
            font=("Segoe UI", 11),
            state="disabled"
        )
        self.exercise_list.pack(side="left", fill="both", expand=True)

        list_scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.exercise_list.yview
        )
        list_scrollbar.pack(side="right", fill="y")
        self.exercise_list.configure(
            yscrollcommand=list_scrollbar.set
        )

        self.exercise_list.bind(
            "<Double-Button-1>",
            self.show_recommendations
        )
        self.exercise_list.bind(
            "<Return>",
            self.show_recommendations
        )

        button_frame = ttk.Frame(selection_frame)
        button_frame.pack(fill="x", pady=(10, 0))

        self.recommend_button = ttk.Button(
            button_frame,
            text="Öneri Getir",
            command=self.show_recommendations,
            state="disabled"
        )
        self.recommend_button.pack(side="left")

        self.clear_button = ttk.Button(
            button_frame,
            text="Temizle",
            command=self.clear_selection,
            state="disabled"
        )
        self.clear_button.pack(side="left", padx=8)

        self.results_title = ttk.Label(
            container,
            text="Öneriler",
            font=("Segoe UI", 12, "bold")
        )
        self.results_title.pack(anchor="w", pady=(18, 8))
        ttk.Label(
            container,
            text=(
                "Support: percentage of all workouts containing both exercises.\n"
                "Confidence: percentage of workouts with your selected exercise "
                "that also contain the recommended exercise.\n"
                "Lift: how much more common the recommended exercise is in workouts "
                "containing your selection compared with all workouts. "
                "A value above 1 indicates a positive association."
            ),
            wraplength=740,
            justify="left"
        ).pack(anchor="w", pady=(0, 10))

        ttk.Label(
            container,
            text=(
                "Recommendations reflect patterns in the dataset. "
                "They are not personalized training prescriptions."
            ),
            wraplength=740,
            justify="left"
        ).pack(anchor="w", pady=(0, 10))

        table_frame = ttk.Frame(container)
        table_frame.pack(fill="both", expand=True)

        columns = ("exercise", "support", "confidence", "lift")

        self.results_table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=5
        )

        self.results_table.heading("exercise", text="Önerilen Egzersiz")
        self.results_table.heading("support", text="Support (%)")
        self.results_table.heading("confidence", text="Confidence (%)")
        self.results_table.heading("lift", text="Lift")

        self.results_table.column("exercise", width=400, minwidth=220)
        self.results_table.column("support", width=110, anchor="center")
        self.results_table.column("confidence", width=130, anchor="center")
        self.results_table.column("lift", width=90, anchor="center")

        self.results_table.pack(side="left", fill="both", expand=True)

        table_scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.results_table.yview
        )
        table_scrollbar.pack(side="right", fill="y")
        self.results_table.configure(
            yscrollcommand=table_scrollbar.set
        )

        ttk.Label(
            container,
            textvariable=self.status_var,
            wraplength=850
        ).pack(anchor="w", pady=(12, 0))

    def load_data(self):
        try:
            file_path = (
                Path(__file__).resolve().parent
                / "weightlifting_721_workouts.csv"
            )

            transactions = prepare_transactions(file_path)

            rules, exercise_names = create_rules(
                transactions,
                min_support=0.02,
                min_confidence=0.2
            )

            self.load_queue.put(
                ("success", rules, exercise_names, len(transactions))
            )
        except Exception as error:
            self.load_queue.put(("error", str(error)))

    def check_loading(self):
        try:
            result = self.load_queue.get_nowait()
        except queue.Empty:
            self.root.after(100, self.check_loading)
            return

        if result[0] == "error":
            self.status_var.set("Veri yüklenemedi.")
            messagebox.showerror("Veri yükleme hatası", result[1])
            return

        _, self.rules, self.exercise_names, workout_count = result

        self.search_entry.configure(state="normal")
        self.exercise_list.configure(state="normal")
        self.recommend_button.configure(state="normal")
        self.clear_button.configure(state="normal")

        self.filter_exercises()

        self.status_var.set(
            f"Hazır: {workout_count} antrenman, "
            f"{len(self.exercise_names)} egzersiz, "
            f"{len(self.rules)} kural."
        )

        if self.rules.empty:
            self.status_var.set(
                "Veri yüklendi ancak mevcut eşiklerle öneri kuralı bulunamadı."
            )

        self.search_entry.focus_set()

    def filter_exercises(self, *_):
        query = normalize_name(self.search_var.get())

        self.filtered_names = [
            name for name in self.exercise_names
            if query in normalize_name(name)
        ]

        self.exercise_list.delete(0, tk.END)

        for name in self.filtered_names:
            self.exercise_list.insert(tk.END, name)

    def show_recommendations(self, event=None):
        selected_indices = self.exercise_list.curselection()

        if not selected_indices:
            messagebox.showinfo(
                "Egzersiz seç",
                "Önce listeden bir egzersiz seç."
            )
            return

        exercise_name = self.filtered_names[selected_indices[0]]

        recommendations = get_exercise_recommendation(
            exercise_name,
            self.rules,
            top_n=5
        )

        self.clear_results()
        self.results_title.configure(
            text=f"Öneriler — {exercise_name}"
        )

        if recommendations.empty:
            self.status_var.set(
                f"{exercise_name} için mevcut eşiklerde öneri bulunamadı."
            )
            return

        for _, row in recommendations.iterrows():
            self.results_table.insert(
                "",
                tk.END,
                values=(
                    row["consequents_text"],
                    f'{row["support"] * 100:.1f}',
                    f'{row["confidence"] * 100:.1f}',
                    f'{row["lift"]:.3f}'
                )
            )

        self.status_var.set(
            f"{exercise_name} için {len(recommendations)} öneri bulundu. "
            "Sonuçlar lift, ardından confidence değerine göre sıralandı."
        )

    def clear_results(self):
        for item in self.results_table.get_children():
            self.results_table.delete(item)

    def clear_selection(self):
        self.search_var.set("")
        self.exercise_list.selection_clear(0, tk.END)
        self.clear_results()
        self.results_title.configure(text="Öneriler")
        self.status_var.set("You can choose a new exercise.")
        self.search_entry.focus_set()


if __name__ == "__main__":
    root = tk.Tk()
    app = GymRecommendationApp(root)
    root.mainloop()