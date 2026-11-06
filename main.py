"""
Beginner-friendly Expense Tracker
GUI: Tkinter | Database: SQLite (built into Python)

Run:
    python main.py

The database file (expenses.db) is created automatically in this folder.
"""

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

DB_NAME = "expenses.db"


def connect_db():
    """Open a connection to the SQLite database."""
    return sqlite3.connect(DB_NAME)


def create_table():
    """Create the expenses table if it does not already exist."""
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                expense_date TEXT NOT NULL,
                note TEXT
            )
        """)


def save_expense(title, amount, category, expense_date, note):
    """Save one expense in the database."""
    with connect_db() as conn:
        conn.execute(
            """INSERT INTO expenses
               (title, amount, category, expense_date, note)
               VALUES (?, ?, ?, ?, ?)""",
            (title, amount, category, expense_date, note)
        )


def get_expenses(search_text=""):
    """Return all expenses, or expenses matching the search text."""
    with connect_db() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if search_text:
            keyword = f"%{search_text}%"
            cursor.execute("""
                SELECT * FROM expenses
                WHERE title LIKE ? OR category LIKE ? OR note LIKE ?
                ORDER BY expense_date DESC, id DESC
            """, (keyword, keyword, keyword))
        else:
            cursor.execute("""
                SELECT * FROM expenses
                ORDER BY expense_date DESC, id DESC
            """)

        return cursor.fetchall()


def delete_expense(expense_id):
    """Delete an expense using its database ID."""
    with connect_db() as conn:
        conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))


def get_total():
    """Calculate the total of all recorded expenses."""
    with connect_db() as conn:
        result = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM expenses"
        ).fetchone()
        return result[0]


class ExpenseTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker")
        self.root.geometry("900x620")
        self.root.minsize(760, 540)

        self.selected_id = None

        self.build_interface()
        self.refresh_table()

    def build_interface(self):
        """Create all labels, input fields, buttons and the expense table."""
        heading = ttk.Label(
            self.root,
            text="Expense Tracker",
            font=("Arial", 22, "bold")
        )
        heading.pack(pady=(15, 5))

        form = ttk.LabelFrame(self.root, text="Add a New Expense", padding=12)
        form.pack(fill="x", padx=15, pady=10)

        ttk.Label(form, text="Expense name:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.title_entry = ttk.Entry(form, width=25)
        self.title_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form, text="Amount:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.amount_entry = ttk.Entry(form, width=18)
        self.amount_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(form, text="Category:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.category_box = ttk.Combobox(
            form,
            values=["Food", "Travel", "Shopping", "Bills", "Education", "Health", "Other"],
            width=22,
            state="normal"
        )
        self.category_box.grid(row=1, column=1, padx=5, pady=5)
        self.category_box.set("Food")

        ttk.Label(form, text="Date (YYYY-MM-DD):").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.date_entry = ttk.Entry(form, width=18)
        self.date_entry.grid(row=1, column=3, padx=5, pady=5)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ttk.Label(form, text="Note:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.note_entry = ttk.Entry(form, width=65)
        self.note_entry.grid(row=2, column=1, columnspan=3, sticky="ew", padx=5, pady=5)

        ttk.Button(form, text="Add Expense", command=self.add_expense).grid(
            row=3, column=1, sticky="w", padx=5, pady=10
        )
        ttk.Button(form, text="Clear Fields", command=self.clear_fields).grid(
            row=3, column=2, sticky="w", padx=5, pady=10
        )

        search_frame = ttk.Frame(self.root, padding=(15, 5))
        search_frame.pack(fill="x")

        ttk.Label(search_frame, text="Search by name, category or note:").pack(side="left")
        self.search_entry = ttk.Entry(search_frame, width=28)
        self.search_entry.pack(side="left", padx=7)
        self.search_entry.bind("<KeyRelease>", lambda event: self.refresh_table())

        ttk.Button(search_frame, text="Show All", command=self.show_all).pack(side="left")

        table_frame = ttk.Frame(self.root, padding=(15, 5))
        table_frame.pack(fill="both", expand=True)

        columns = ("id", "title", "amount", "category", "date", "note")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=12
        )

        headings = {
            "id": "ID",
            "title": "Expense",
            "amount": "Amount",
            "category": "Category",
            "date": "Date",
            "note": "Note"
        }
        widths = {"id": 45, "title": 170, "amount": 100,
                  "category": 110, "date": 110, "note": 230}

        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

        action_frame = ttk.Frame(self.root, padding=(15, 5))
        action_frame.pack(fill="x")

        ttk.Button(
            action_frame,
            text="Delete Selected Expense",
            command=self.remove_expense
        ).pack(side="left")

        self.total_label = ttk.Label(
            action_frame,
            text="Total expenses: 0.00",
            font=("Arial", 13, "bold")
        )
        self.total_label.pack(side="right", padx=5, pady=8)

        ttk.Label(
            self.root,
            text="Your records are saved locally in expenses.db",
            foreground="gray"
        ).pack(pady=(0, 10))

    def add_expense(self):
        """Check the form and add the expense."""
        title = self.title_entry.get().strip()
        amount_text = self.amount_entry.get().strip()
        category = self.category_box.get().strip()
        expense_date = self.date_entry.get().strip()
        note = self.note_entry.get().strip()

        if not title or not amount_text or not category or not expense_date:
            messagebox.showwarning("Missing information", "Please fill in all required fields.")
            return

        try:
            amount = float(amount_text)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid amount", "Enter an amount greater than zero.")
            return

        try:
            datetime.strptime(expense_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Invalid date", "Use the date format YYYY-MM-DD.")
            return

        try:
            save_expense(title, amount, category, expense_date, note)
            messagebox.showinfo("Success", "Expense added successfully.")
            self.clear_fields()
            self.refresh_table()
        except sqlite3.Error as error:
            messagebox.showerror("Database error", str(error))

    def refresh_table(self):
        """Reload the table and update the total."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        search_text = self.search_entry.get().strip() if hasattr(self, "search_entry") else ""
        try:
            for expense in get_expenses(search_text):
                self.tree.insert("", "end", values=(
                    expense["id"],
                    expense["title"],
                    f'{expense["amount"]:.2f}',
                    expense["category"],
                    expense["expense_date"],
                    expense["note"] or ""
                ))

            self.total_label.config(text=f"Total expenses: {get_total():.2f}")
        except sqlite3.Error as error:
            messagebox.showerror("Database error", str(error))

    def clear_fields(self):
        """Empty the form and restore today's date."""
        self.title_entry.delete(0, tk.END)
        self.amount_entry.delete(0, tk.END)
        self.category_box.set("Food")
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.note_entry.delete(0, tk.END)
        self.selected_id = None
        self.tree.selection_remove(self.tree.selection())

    def on_row_select(self, event):
        """Remember the ID of the selected row."""
        selected = self.tree.selection()
        if selected:
            values = self.tree.item(selected[0], "values")
            self.selected_id = int(values[0])

    def remove_expense(self):
        """Delete the selected expense after confirmation."""
        if self.selected_id is None:
            messagebox.showwarning("No selection", "Please select an expense first.")
            return

        confirm = messagebox.askyesno(
            "Confirm deletion",
            "Are you sure you want to delete this expense?"
        )
        if confirm:
            try:
                delete_expense(self.selected_id)
                self.selected_id = None
                self.refresh_table()
                messagebox.showinfo("Deleted", "Expense deleted successfully.")
            except sqlite3.Error as error:
                messagebox.showerror("Database error", str(error))

    def show_all(self):
        """Clear the search box and show every expense."""
        self.search_entry.delete(0, tk.END)
        self.refresh_table()


if __name__ == "__main__":
    create_table()
    root = tk.Tk()
    app = ExpenseTracker(root)
    root.mainloop()
