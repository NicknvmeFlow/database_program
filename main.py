import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import simpledialog
import sqlite3
import os

class DBGUIEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Графический редактор базы данных (SQLite)")
        self.root.geometry("1000x700")

        # Путь к файлу базы данных в той же папке, что и скрипт
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(script_dir, "DataBase08.db")

        self.conn = None
        self.cur = None

        # Автоматическое подключение и создание БД по твоему скрипту
        self.connect_and_setup()

    def connect_and_setup(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cur = self.conn.cursor()

            # Создаём таблицы строго по твоему оригинальному скрипту (адаптировано под SQLite)
            self.cur.executescript('''
                CREATE TABLE IF NOT EXISTS "Types" (
                    "typeID" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                    "type" TEXT NOT NULL UNIQUE
                );

                CREATE TABLE IF NOT EXISTS "Departments" (
                    "departmentID" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                    "department" TEXT NOT NULL UNIQUE
                );

                CREATE TABLE IF NOT EXISTS "Employees" (
                    "employeeID" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                    "fullname" TEXT NOT NULL,
                    "departmentID" INTEGER NOT NULL,
                    FOREIGN KEY("departmentID") REFERENCES "Departments"("departmentID") ON UPDATE CASCADE
                );

                CREATE TABLE IF NOT EXISTS "Cards" (
                    "docID" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                    "create_date" DATE NOT NULL DEFAULT (DATE('now')),
                    "name" TEXT NOT NULL,
                    "typeID" INTEGER NOT NULL,
                    FOREIGN KEY("typeID") REFERENCES "Types"("typeID") ON UPDATE CASCADE
                );

                CREATE TABLE IF NOT EXISTS "Strings" (
                    "docID" INTEGER NOT NULL,
                    "line_num" INTEGER NOT NULL,
                    "employeeID" INTEGER NOT NULL,
                    "planned_date" DATE,
                    "completed_date" DATE,
                    PRIMARY KEY("docID", "line_num"),
                    FOREIGN KEY("docID") REFERENCES "Cards"("docID") ON DELETE CASCADE,
                    FOREIGN KEY("employeeID") REFERENCES "Employees"("employeeID")
                );
            ''')

            self.conn.commit()

            # Переходим к главному интерфейсу
            self.create_main_interface()

            messagebox.showinfo("Готово!", 
                                f"База данных успешно создана/загружена!\n"
                                f"Файл: DataBase08.db\n"
                                f"Расположение: {os.path.dirname(self.db_path)}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать или открыть базу данных:\n{e}")
            self.root.quit()

    def create_main_interface(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        tab_refs = ttk.Frame(notebook)
        notebook.add(tab_refs, text="Справочники")

        btn_frame = tk.Frame(tab_refs)
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text="Типы документов", width=20, command=self.manage_types).grid(row=0, column=0, padx=10, pady=10)
        tk.Button(btn_frame, text="Отделы", width=20, command=self.manage_departments).grid(row=0, column=1, padx=10, pady=10)
        tk.Button(btn_frame, text="Сотрудники", width=20, command=self.manage_employees).grid(row=0, column=2, padx=10, pady=10)

        tab_docs = ttk.Frame(notebook)
        notebook.add(tab_docs, text="Документы")

        doc_btn_frame = tk.Frame(tab_docs)
        doc_btn_frame.pack(pady=20)

        tk.Button(doc_btn_frame, text="Создать новый документ", width=30, bg="#ffffcc",
                  command=self.create_new_card).pack(pady=10)
        tk.Button(doc_btn_frame, text="Просмотреть все документы", width=30,
                  command=self.view_all_cards).pack(pady=10)

    # === Остальной код остаётся таким же, как в предыдущей версии ===
    # (справочники, сотрудники, документы и т.д.)

    def manage_types(self):
        self.show_table_manager("Types", "typeID", "type", "Тип документа")

    def manage_departments(self):
        self.show_table_manager("Departments", "departmentID", "department", "Отдел")

    def show_table_manager(self, table_name, id_col, value_col, title):
        win = tk.Toplevel(self.root)
        win.title(f"Управление: {title}")
        win.geometry("650x550")

        tree = ttk.Treeview(win, columns=(id_col, value_col), show="headings")
        tree.heading(id_col, text="ID")
        tree.heading(value_col, text=title)
        tree.column(id_col, width=80, anchor="center")
        tree.column(value_col, width=400)
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        self.load_simple_table(tree, table_name, id_col, value_col)

        def edit_item(event):
            selected = tree.selection()
            if not selected: return
            item = tree.item(selected[0])
            current_value = item['values'][1]
            new_value = simpledialog.askstring("Редактирование", f"Измените {title.lower()}:", initialvalue=current_value)
            if new_value and new_value != current_value:
                try:
                    item_id = item['values'][0]
                    self.cur.execute(f'UPDATE "{table_name}" SET "{value_col}" = ? WHERE "{id_col}" = ?', (new_value, item_id))
                    self.conn.commit()
                    self.load_simple_table(tree, table_name, id_col, value_col)
                    messagebox.showinfo("Успех", "Запись обновлена!")
                except Exception as e:
                    messagebox.showerror("Ошибка", str(e))

        win.lift()               # Поднимает окно наверх
        win.attributes('-topmost', True)   # Делает окно всегда сверху
        win.after(100, lambda: win.attributes('-topmost', False))  # Через 0.1 сек убирает "всегда сверху"

        tree.bind("<Double-1>", edit_item)

        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=10)

        def add():
            value = simpledialog.askstring("Добавление", f"Введите новый {title.lower()}:")
            if value:
                try:
                    self.cur.execute(f'INSERT INTO "{table_name}" ("{value_col}") VALUES (?)', (value,))
                    self.conn.commit()
                    self.load_simple_table(tree, table_name, id_col, value_col)
                    messagebox.showinfo("Успех", "Запись добавлена!")
                except Exception as e:
                    messagebox.showerror("Ошибка", str(e))

        def delete():
            selected = tree.selection()
            if not selected: 
                messagebox.showwarning("Внимание", "Выберите строку")
                return
            item = tree.item(selected[0])
            id_val = item['values'][0]
            if messagebox.askyesno("Удалить", f"Удалить {title.lower()} с ID {id_val}?"):
                try:
                    self.cur.execute(f'DELETE FROM "{table_name}" WHERE "{id_col}" = ?', (id_val,))
                    self.conn.commit()
                    self.load_simple_table(tree, table_name, id_col, value_col)
                    messagebox.showinfo("Успех", "Запись удалена!")
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Нельзя удалить: есть зависимости\n{e}")

        tk.Button(btn_frame, text="Добавить", command=add, bg="#ccffcc").pack(side="left", padx=10)
        tk.Button(btn_frame, text="Удалить", command=delete, bg="#ffcccc").pack(side="left", padx=10)
        tk.Button(btn_frame, text="Обновить", command=lambda: self.load_simple_table(tree, table_name, id_col, value_col),
                  bg="#ccccff").pack(side="left", padx=10)

    def load_simple_table(self, tree, table_name, id_col, value_col):
        for item in tree.get_children():
            tree.delete(item)
        self.cur.execute(f'SELECT "{id_col}", "{value_col}" FROM "{table_name}" ORDER BY "{value_col}"')
        for row in self.cur.fetchall():
            tree.insert("", "end", values=row)

    def manage_employees(self):
        self.show_employee_manager()

    def show_employee_manager(self):
        win = tk.Toplevel(self.root)
        win.title("Управление: Сотрудники")
        win.geometry("850x650")

        tree = ttk.Treeview(win, columns=("employeeID", "fullname", "department"), show="headings")
        tree.heading("employeeID", text="ID")
        tree.heading("fullname", text="ФИО")
        tree.heading("department", text="Отдел")
        tree.column("employeeID", width=80, anchor="center")
        tree.column("fullname", width=300)
        tree.column("department", width=300)
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        self.load_employees(tree)

        def edit_employee(event):
            selected = tree.selection()
            if not selected: return
            item = tree.item(selected[0])
            emp_id = item['values'][0]
            current_fullname = item['values'][1]
            new_fullname = simpledialog.askstring("Редактирование ФИО", "Измените ФИО:", initialvalue=current_fullname)
            if new_fullname and new_fullname != current_fullname:
                try:
                    self.cur.execute('UPDATE "Employees" SET "fullname" = ? WHERE "employeeID" = ?', (new_fullname, emp_id))
                    self.conn.commit()
                    self.load_employees(tree)
                    messagebox.showinfo("Успех", "ФИО обновлено!")
                except Exception as e:
                    messagebox.showerror("Ошибка", str(e))

        tree.bind("<Double-1>", edit_employee)

        add_frame = tk.LabelFrame(win, text="Добавить нового сотрудника")
        add_frame.pack(pady=10, padx=10, fill="x")

        tk.Label(add_frame, text="ФИО:").grid(row=0, column=0, sticky="e", padx=10, pady=8)
        fullname_entry = tk.Entry(add_frame, width=50)
        fullname_entry.grid(row=0, column=1, padx=10, pady=8)

        def load_departments():
            self.cur.execute('SELECT "departmentID", "department" FROM "Departments" ORDER BY "department"')
            return self.cur.fetchall()

        departments = load_departments()
        dept_list = [d[1] for d in departments]
        dept_map = {d[1]: d[0] for d in departments}

        tk.Label(add_frame, text="Отдел:").grid(row=1, column=0, sticky="e", padx=10, pady=8)
        dept_var = tk.StringVar()
        if dept_list:
            dept_var.set(dept_list[0])

        dept_menu = ttk.Combobox(add_frame, textvariable=dept_var, values=dept_list, state="readonly", width=47)
        dept_menu.grid(row=1, column=1, padx=10, pady=8)

        def add_new_department():
            new_dept = simpledialog.askstring("Новый отдел", "Введите название нового отдела:")
            if not new_dept: return
            try:
                self.cur.execute('INSERT INTO "Departments" ("department") VALUES (?)', (new_dept,))
                self.conn.commit()

                departments = load_departments()
                new_list = [d[1] for d in departments]
                dept_menu['values'] = new_list
                dept_var.set(new_dept)
                dept_map[new_dept] = self.cur.lastrowid

                messagebox.showinfo("Успех", f"Отдел '{new_dept}' добавлен и выбран!")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

        tk.Button(add_frame, text="+ Добавить новый отдел", command=add_new_department,
                  bg="#a0ffa0").grid(row=1, column=2, padx=15)

        def add_employee():
            fullname = fullname_entry.get().strip()
            if not fullname:
                messagebox.showwarning("Внимание", "Введите ФИО!")
                return
            dept_name = dept_var.get()
            dept_id = dept_map.get(dept_name)
            if not dept_id:
                messagebox.showwarning("Внимание", "Выберите отдел!")
                return
            try:
                self.cur.execute('INSERT INTO "Employees" ("fullname", "departmentID") VALUES (?, ?)',
                                 (fullname, dept_id))
                self.conn.commit()
                self.load_employees(tree)
                fullname_entry.delete(0, tk.END)
                messagebox.showinfo("Успех", f"Сотрудник '{fullname}' добавлен!")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

        tk.Button(add_frame, text="Добавить сотрудника", command=add_employee,
                  bg="#ccffcc", font=("Arial", 11), width=25).grid(row=2, column=0, columnspan=3, pady=15)

        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Удалить выбранного", command=lambda: self.delete_employee(tree),
                  bg="#ffcccc").pack(side="left", padx=10)
        tk.Button(btn_frame, text="Обновить список", command=lambda: self.load_employees(tree),
                  bg="#ccccff").pack(side="left", padx=10)
        win.lift()               # Поднимает окно наверх
        win.attributes('-topmost', True)   # Делает окно всегда сверху
        win.after(100, lambda: win.attributes('-topmost', False))  # Через 0.1 сек убирает "всегда сверху"

    def delete_employee(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите сотрудника")
            return
        emp_id = tree.item(selected[0])['values'][0]
        if messagebox.askyesno("Удалить", "Удалить сотрудника?"):
            try:
                self.cur.execute('DELETE FROM "Employees" WHERE "employeeID" = ?', (emp_id,))
                self.conn.commit()
                self.load_employees(tree)
                messagebox.showinfo("Успех", "Сотрудник удалён!")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    def load_employees(self, tree):
        for item in tree.get_children():
            tree.delete(item)
        self.cur.execute('''
            SELECT e."employeeID", e."fullname", d."department" 
            FROM "Employees" e 
            JOIN "Departments" d ON e."departmentID" = d."departmentID"
            ORDER BY e."fullname"
        ''')
        for row in self.cur.fetchall():
            tree.insert("", "end", values=row)

    def create_new_card(self):
        win = tk.Toplevel(self.root)
        win.title("Создание нового документа")
        win.geometry("550x500")

        tk.Label(win, text="Название документа:", font=("Arial", 12)).pack(pady=15)
        name_entry = tk.Entry(win, width=50, font=("Arial", 11))
        name_entry.pack(pady=5)

        def load_types():
            self.cur.execute('SELECT "typeID", "type" FROM "Types" ORDER BY "type"')
            return self.cur.fetchall()

        types = load_types()
        type_list = [t[1] for t in types]
        type_map = {t[1]: t[0] for t in types}

        tk.Label(win, text="Тип документа:", font=("Arial", 12)).pack(pady=(20,10))
        type_var = tk.StringVar()
        if type_list:
            type_var.set(type_list[0])

        type_menu = ttk.Combobox(win, textvariable=type_var, values=type_list, state="readonly", width=47, font=("Arial", 11))
        type_menu.pack(pady=5)

        def add_new_type():
            new_type = simpledialog.askstring("Новый тип", "Введите название нового типа документа:")
            if not new_type: return
            try:
                self.cur.execute('INSERT INTO "Types" ("type") VALUES (?)', (new_type,))
                self.conn.commit()

                types = load_types()
                new_list = [t[1] for t in types]
                type_menu['values'] = new_list
                type_var.set(new_type)
                type_map[new_type] = self.cur.lastrowid

                messagebox.showinfo("Успех", f"Тип '{new_type}' добавлен и выбран!")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

        tk.Button(win, text="+ Добавить новый тип", command=add_new_type,
                  bg="#a0ffa0").pack(pady=8)

        def save_card():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Ошибка", "Введите название!")
                return
            type_name = type_var.get()
            type_id = type_map.get(type_name)
            if not type_id:
                messagebox.showwarning("Ошибка", "Выберите тип!")
                return
            try:
                self.cur.execute('INSERT INTO "Cards" ("name", "typeID") VALUES (?, ?)', (name, type_id))
                self.conn.commit()
                doc_id = self.cur.lastrowid
                messagebox.showinfo("Успех", f"Документ создан! ID: {doc_id}")
                win.destroy()
                self.edit_card_lines(doc_id)
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

        tk.Button(win, text="Создать документ", command=save_card,
                  bg="#ccffcc", font=("Arial", 12), width=25, height=2).pack(pady=30)
        win.lift()               # Поднимает окно наверх
        win.attributes('-topmost', True)   # Делает окно всегда сверху
        win.after(100, lambda: win.attributes('-topmost', False))  # Через 0.1 сек убирает "всегда сверху"

    def view_all_cards(self):
        win = tk.Toplevel(self.root)
        win.title("Все документы")
        win.geometry("900x600")

        tree = ttk.Treeview(win, columns=("docID", "create_date", "name", "type"), show="headings")
        tree.heading("docID", text="ID")
        tree.heading("create_date", text="Дата создания")
        tree.heading("name", text="Название")
        tree.heading("type", text="Тип")
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        self.load_all_cards(tree)

        def open_selected():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Внимание", "Выберите документ")
                return
            doc_id = tree.item(selected[0])['values'][0]
            win.destroy()
            self.edit_card_lines(doc_id)

        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Открыть документ", command=open_selected, bg="#ffffcc").pack(side="left", padx=10)
        tk.Button(btn_frame, text="Обновить", command=lambda: self.load_all_cards(tree), bg="#ccccff").pack(side="left", padx=10)
        win.lift()               # Поднимает окно наверх
        win.attributes('-topmost', True)   # Делает окно всегда сверху
        win.after(100, lambda: win.attributes('-topmost', False))  # Через 0.1 сек убирает "всегда сверху"

    def load_all_cards(self, tree):
        for item in tree.get_children():
            tree.delete(item)
        self.cur.execute('''
            SELECT c."docID", c."create_date", c."name", t."type"
            FROM "Cards" c
            JOIN "Types" t ON c."typeID" = t."typeID"
            ORDER BY c."docID" DESC
        ''')
        for row in self.cur.fetchall():
            tree.insert("", "end", values=row)

    def edit_card_lines(self, doc_id):
        win = tk.Toplevel(self.root)
        win.title(f"Строки документа ID {doc_id}")
        win.geometry("1000x650")

        self.cur.execute('SELECT "name" FROM "Cards" WHERE "docID" = ?', (doc_id,))
        doc_name = self.cur.fetchone()[0]
        tk.Label(win, text=f"Документ: {doc_name} (ID: {doc_id})", font=("Arial", 14, "bold")).pack(pady=10)

        tree = ttk.Treeview(win, columns=("line_num", "employee", "planned_date", "completed_date"), show="headings")
        tree.heading("line_num", text="№ строки")
        tree.heading("employee", text="Сотрудник")
        tree.heading("planned_date", text="Плановая дата")
        tree.heading("completed_date", text="Дата выполнения")
        tree.column("line_num", width=80, anchor="center")
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        self.load_card_lines(tree, doc_id)

        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=10)

        def add_line():
            self.cur.execute('SELECT "employeeID", "fullname" FROM "Employees" ORDER BY "fullname"')
            emps = self.cur.fetchall()
            if not emps:
                messagebox.showwarning("Внимание", "Сначала добавьте сотрудников!")
                return
            emp_str = "\n".join([f"{e[0]}: {e[1]}" for e in emps])
            emp_id = simpledialog.askinteger("Сотрудник", f"Выберите ID:\n\n{emp_str}")
            if emp_id is None: return

            planned = simpledialog.askstring("Плановая дата", "Введите дату (ГГГГ-ММ-ДД) или оставьте пустым:")
            completed = simpledialog.askstring("Дата выполнения", "Введите дату (ГГГГ-ММ-ДД) или оставьте пустым:")

            try:
                self.cur.execute('''
                    INSERT INTO "Strings" ("docID", "line_num", "employeeID", "planned_date", "completed_date")
                    VALUES (?, (SELECT COALESCE(MAX("line_num"),0)+1 FROM "Strings" WHERE "docID"=?), ?, ?, ?)
                ''', (doc_id, doc_id, emp_id, planned or None, completed or None))
                self.conn.commit()
                self.load_card_lines(tree, doc_id)
                messagebox.showinfo("Успех", "Строка добавлена!")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

        def delete_line():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Внимание", "Выберите строку")
                return
            line_num = tree.item(selected[0])['values'][0]
            if messagebox.askyesno("Удалить", f"Удалить строку №{line_num}?"):
                try:
                    self.cur.execute('DELETE FROM "Strings" WHERE "docID" = ? AND "line_num" = ?', (doc_id, line_num))
                    self.conn.commit()
                    self.load_card_lines(tree, doc_id)
                    messagebox.showinfo("Успех", "Строка удалена!")
                except Exception as e:
                    messagebox.showerror("Ошибка", str(e))

        tk.Button(btn_frame, text="Добавить строку", command=add_line, bg="#ccffcc").pack(side="left", padx=10)
        tk.Button(btn_frame, text="Удалить строку", command=delete_line, bg="#ffcccc").pack(side="left", padx=10)
        tk.Button(btn_frame, text="Обновить", command=lambda: self.load_card_lines(tree, doc_id), bg="#ccccff").pack(side="left", padx=10)
        win.lift()               # Поднимает окно наверх
        win.attributes('-topmost', True)   # Делает окно всегда сверху
        win.after(100, lambda: win.attributes('-topmost', False))  # Через 0.1 сек убирает "всегда сверху"

    def load_card_lines(self, tree, doc_id):
        for item in tree.get_children():
            tree.delete(item)
        self.cur.execute('''
            SELECT s."line_num", e."fullname", s."planned_date", s."completed_date"
            FROM "Strings" s
            JOIN "Employees" e ON s."employeeID" = e."employeeID"
            WHERE s."docID" = ?
            ORDER BY s."line_num"
        ''', (doc_id,))
        for row in self.cur.fetchall():
            tree.insert("", "end", values=row)


if __name__ == "__main__":
    root = tk.Tk()
    app = DBGUIEditor(root)
    root.mainloop()