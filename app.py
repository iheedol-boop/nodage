import flet as ft

# Flet을 활용한 간단한 이름 입력 앱 샘플 코드
def main(page: ft.Page):
    page.title = "Flet 앱"
    
    def button_clicked(e):
        page.add(ft.Text(f"안녕하세요, {txt_name.value}님!"))
        page.update()

    txt_name = ft.TextField(label="이름")
    page.add(txt_name, ft.ElevatedButton("인사", on_click=button_clicked))

ft.app(target=main)
