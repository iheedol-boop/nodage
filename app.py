import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("Tkinter Tab 예제")
root.geometry("400x300")

# 탭을 관리하는 Notebook 생성
notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

# 첫 번째 탭 화면 구성
tab1 = ttk.Frame(notebook)
notebook.add(tab1, text="첫 번째 탭")
label1 = tk.Label(tab1, text="여기는 1번 화면입니다.")
label1.pack(pady=20)

# 두 번째 탭 화면 구성
tab2 = ttk.Frame(notebook)
notebook.add(tab2, text="두 번째 탭")
label2 = tk.Label(tab2, text="여기는 2번 화면입니다.")
label2.pack(pady=20)

root.mainloop()
