import tkinter as tk
from tkinter import ttk

# 메인 윈도우 및 노트북(탭) 생성
root = tk.Tk()
notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

# 탭 프레임 생성 및 추가
frame1 = tk.Frame(notebook)
notebook.add(frame1, text="탭 1")

# 탭 내용 구성
tk.Label(frame1, text="첫 번째 화면").pack()

root.mainloop()
