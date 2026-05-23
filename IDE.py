import tkinter as tk
from tkinter import scrolledtext, filedialog, Menu, Listbox, Frame
import subprocess
import re
import os

class TinyCIDEPRO:
    def __init__(self, root):
        self.root = root
        self.root.configure(bg="#1E1E2E")
        self.root.geometry("1250x720")

        self.current_file = ""
        self.compiler_path = r".\gcc\bin\gcc.exe"
        self.lang = {}
        self.kw_colors = {}
        self.kw_list = []
        self.tab_size = 4
        self.load_keywords("Tips.tip")
        self.load_last_language()
        self.root.title(self.t("gui.tkinter.title"))
        try:
            self.root.iconbitmap(self.t("gui.tkinter.title.icon"))
        except:
            pass

        self.tab_size = int(self.lang.get("key.tab", 4))

        self.build_menu()
        self.build_ui()
        self.bind_hotkeys()
        self.highlight_all()
    def load_last_language(self):
        try:
            if os.path.exists("lastlang.cfg"):
                with open("lastlang.cfg", "r", encoding="utf-8") as f:
                    path = f.read().strip()
                    if os.path.exists(path):
                        self.load_language(path)
                        return
        except:
            pass
        self.load_language("Language/chinese.l")

    def save_last_language(self, path):
        try:
            with open("lastlang.cfg", "w", encoding="utf-8") as f:
                f.write(path)
        except:
            pass
    def load_language(self, path):
        self.lang = {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("#") or not line:
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        self.lang[k.strip()] = v.strip().strip('"')
        except:
            pass

    def t(self, key):
        return self.lang.get(key, key)
    def load_keywords(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if "{" not in line:
                        continue
                    kw, c = line.split("{", 1)
                    kw = kw.strip()
                    color = c.strip().rstrip("}")
                    self.kw_colors[kw] = color
                    self.kw_list.append(kw)
        except:
            pass

    def build_menu(self):
        menubar = Menu(self.root, bg="#2B2B3B", fg="white", activebackground="#4A4A6A", font=("Segoe UI", 10))
        self.root.config(menu=menubar)

        file_menu = Menu(menubar, tearoff=0, bg="#333345", fg="white")
        file_menu.add_command(label=self.t("menu.new"), command=self.new_file)
        file_menu.add_command(label=self.t("menu.open"), command=self.open_file)
        file_menu.add_command(label=self.t("menu.save"), command=self.save_file)
        file_menu.add_separator()
        file_menu.add_command(label=self.t("menu.setlanguage"), command=self.switch_lang)
        file_menu.add_separator()
        file_menu.add_command(label=self.t("menu.exit"), command=self.root.quit)
        menubar.add_cascade(label=self.t("menu.file"), menu=file_menu)
        run_menu = Menu(menubar, tearoff=0, bg="#333345", fg="white")
        run_menu.add_command(label=f"{self.t('menu.compilerun')} (F5)", command=self.compile_run)
        menubar.add_cascade(label=self.t("menu.run"), menu=run_menu)
    def build_ui(self):
        for w in self.root.winfo_children():
            if not isinstance(w, Menu):
                w.destroy()

        self.editor = scrolledtext.ScrolledText(
            self.root, font=("Consolas", 11), wrap=tk.WORD,
            bg="#2D2D3F", fg="#E2E8F0", insertbackground="white"
        )
        self.editor.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)
        self.editor.insert("end", '// Tiny C IDE\n#include <stdio.h>\nint main(){\n    printf("Hello\\n");\n    return 0;\n}')

        tk.Label(
            self.root, text=self.t("gui.tkinter.label.output"),
            bg="#1E1E2E", fg="#E2E8F0", font=("Segoe UI", 10)
        ).pack(anchor=tk.W, padx=12)

        self.output = scrolledtext.ScrolledText(
            self.root, height=9, font=("Consolas", 10),
            bg="#252535", fg="#E2E8F0"
        )
        self.output.pack(fill=tk.X, padx=12, pady=6)

        self.ac_frame = Frame(self.root, bg="#383850")
        self.ac_list = Listbox(
            self.ac_frame, bg="#383850", fg="white", font=("Consolas", 10),
            relief=tk.FLAT, highlightcolor="white"
        )
        self.ac_list.pack()
        self.ac_frame.place_forget()
    def bind_hotkeys(self):
        self.editor.bind("<KeyRelease>", self.on_type)
        self.editor.bind("<Tab>", self.do_tab)
        self.ac_list.bind("<ButtonRelease-1>", self.confirm_select)
        self.ac_list.bind("<Return>", self.confirm_select)
        self.root.bind("<F5>", lambda e: self.compile_run())
        self.root.bind("<Control-n>", lambda e: self.new_file())
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())
    def do_tab(self, e):
        self.editor.insert(tk.INSERT, " " * self.tab_size)
        return "break"
    def on_type(self, e):
        self.highlight_all()
        self.update_autocomplete()

    def update_autocomplete(self):
        pos = self.editor.index(tk.INSERT)
        line = self.editor.get(f"{pos} linestart", pos)
        match = re.search(r"\w+$", line)

        if not match:
            self.ac_frame.place_forget()
            return

        word = match.group()
        matches = [kw for kw in self.kw_list if kw.lower().startswith(word.lower())]

        if not matches:
            self.ac_frame.place_forget()
            return

        self.ac_list.delete(0, tk.END)
        for item in matches[:8]:
            self.ac_list.insert(tk.END, item)

        self.ac_list.selection_clear(0, tk.END)
        self.ac_list.selection_set(0)

        bbox = self.editor.bbox(pos)
        if bbox:
            self.ac_frame.place(x=bbox[0]+60, y=bbox[1]+35)

    def confirm_select(self, e=None):
        try:
            selected = self.ac_list.get(self.ac_list.curselection())
            pos = self.editor.index(tk.INSERT)
            line = self.editor.get(f"{pos} linestart", pos)
            match = re.search(r"\w+$", line)
            if match:
                self.editor.delete(f"{pos}-{len(match.group())}c", pos)
            self.editor.insert(pos, selected)
            self.ac_frame.place_forget()
        except:
            pass
        return "break"
    def highlight_all(self):
        for tag in self.editor.tag_names():
            self.editor.tag_remove(tag, "1.0", tk.END)
        text = self.editor.get("1.0", tk.END)

        for kw, color in self.kw_colors.items():
            pat = re.compile(r"\b" + re.escape(kw) + r"\b")
            for m in pat.finditer(text):
                self.editor.tag_add(kw, f"1.0+{m.start()}c", f"1.0+{m.end()}c")
                self.editor.tag_config(kw, foreground=color)

        for m in re.finditer(r"//.*", text):
            self.editor.tag_add("comment", f"1.0+{m.start()}c", f"1.0+{m.end()}c")
            self.editor.tag_config("comment", foreground="#727288")

        for m in re.finditer(r'"[^"\\]*"', text):
            self.editor.tag_add("string", f"1.0+{m.start()}c", f"1.0+{m.end()}c")
            self.editor.tag_config("string", foreground="#70D670")

    def new_file(self):
        self.editor.delete("1.0", tk.END)
        self.current_file = ""

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("C Files", "*.c")])
        if path:
            with open(path, "r", encoding="utf-8") as f:
                self.editor.delete("1.0", tk.END)
                self.editor.insert("1.0", f.read())
            self.current_file = path
            self.highlight_all()

    def save_file(self):
        if not self.current_file:
            self.current_file = filedialog.asksaveasfilename(defaultextension=".c")
        if self.current_file:
            with open(self.current_file, "w", encoding="utf-8") as f:
                f.write(self.editor.get("1.0", tk.END))

    def switch_lang(self):
        f = filedialog.askopenfilename(initialdir="Language", filetypes=[("Language", "*.l")])
        if f:
            self.load_language(f)
            self.save_last_language(f)
            self.root.title(self.t("gui.tkinter.title"))
            self.build_menu()
            self.build_ui()
            self.highlight_all()
    def compile_run(self):
        self.save_file()
        self.output.delete("1.0", tk.END)
        if not self.current_file:
            self.output.insert("end", "请先保存文件")
            return

        exe = self.current_file.replace(".c", ".exe")
        cmd = f'"{self.compiler_path}" "{self.current_file}" -o "{exe}"'
        res = subprocess.run(cmd, capture_output=True, text=True, shell=True)

        if res.stderr:
            self.output.insert("end", self.t("gui.tkinter.output.failure") + ":\n" + res.stderr)
            return

        run_res = subprocess.run(f'"{exe}"', capture_output=True, text=True, shell=True)
        self.output.insert("end", self.t("gui.tkinter.output.success") + ":\n" + run_res.stdout)

if __name__ == "__main__":
    root = tk.Tk()
    app = TinyCIDEPRO(root)
    root.mainloop()