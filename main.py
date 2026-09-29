import calendar
from datetime import datetime
import os

from db import Database
from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.uix.stencilview import StencilView
from kivy.utils import get_color_from_hex
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDIcon, MDLabel
from kivymd.uix.pickers import MDDatePicker
from kivymd.uix.relativelayout import MDRelativeLayout

# Tentukan Ukuran Window
Config.set("graphics", "width", "390")
Config.set("graphics", "height", "844")
Config.set("graphics", "resizable", "0")
Config.set("graphics", "borderless", "0")

Window.size = (390, 844)
Window.minimum_width = 320
Window.minimum_height = 560
Window.clearcolor = (0.96, 0.95, 0.91, 1)

db = Database()

class BaseScreen(Screen):
    pass


def get_logo_path():
    logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
    if os.path.exists(logo_path):
        return logo_path
    return "atlas://data/images/defaulttheme/filechooser_folder"


class SplashScreen(Screen):
    logo_path = StringProperty(get_logo_path())

    def on_enter(self):
        Clock.schedule_once(self.go_to_next_screen, 4)

    def go_to_next_screen(self, dt):
        user = db.get_first_user()
        if user:
            home_screen = self.manager.get_screen("home")
            home_screen.user_name, home_screen.user_email = user
            self.manager.current = "home"
        else:
            self.manager.current = "login"


class LoginScreen(Screen):
    logo_path = StringProperty(get_logo_path())

    def do_login(self):
        email = self.ids.login_email.text.strip()
        password = self.ids.login_password.text.strip()
        message_label = self.ids.login_message

        if not email.endswith("@gmail.com"):
            message_label.text = "Email harus diakhiri dengan @gmail.com!"
            return

        if not password:
            message_label.text = "Password tidak boleh kosong!"
            return

        success, user_name = db.login_user(email, password)
        if success:
            message_label.text = ""
            main_screen = self.manager.get_screen("home")
            main_screen.user_email = email
            main_screen.user_name = user_name
            self.manager.current = "home"
        else:
            message_label.text = user_name


class RegisterScreen(Screen):
    logo_path = StringProperty(get_logo_path())

    def do_register(self):
        name = self.ids.reg_name.text.strip()
        email = self.ids.reg_email.text.strip()
        password = self.ids.reg_password.text.strip()
        confirm_password = self.ids.reg_confirm_password.text.strip()
        message_label = self.ids.reg_message

        if not name:
            message_label.text = "Nama wajib diisi!"
            return

        if not email.endswith("@gmail.com"):
            message_label.text = "Email harus diakhiri dengan @gmail.com!"
            return

        if not password:
            message_label.text = "Password tidak boleh kosong!"
            return

        if password != confirm_password:
            message_label.text = "Konfirmasi password tidak cocok!"
            return

        success, msg = db.register_user(name, email, password)
        if success:
            message_label.color = (0.2, 0.7, 0.2, 1)
            message_label.text = "Pendaftaran berhasil! Silakan masuk."

            self.ids.reg_name.text = ""
            self.ids.reg_email.text = ""
            self.ids.reg_password.text = ""
            self.ids.reg_confirm_password.text = ""

            Clock.schedule_once(
                lambda dt: setattr(self.manager, "current", "login"), 1.5
            )
        else:
            message_label.color = (0.9, 0.2, 0.2, 1)
            message_label.text = msg


class HomeScreen(BaseScreen):
    dialog = None
    user_name = StringProperty("User")
    user_email = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_date = datetime.now()
        self.nama_bulan = [
            "",
            "Januari",
            "Februari",
            "Maret",
            "April",
            "Mei",
            "Juni",
            "Juli",
            "Agustus",
            "September",
            "Oktober",
            "November",
            "Desember",
        ]

    def on_enter(self):
        if self.ids:
            self.ids.user_greeting.text = f"Halo, {self.user_name}!"
        self.update_month_display()
        self.update_data()

    def update_month_display(self):
        bulan_text = self.nama_bulan[self.current_date.month]
        tahun_text = self.current_date.year
        if "current_month_label" in self.ids:
            self.ids.current_month_label.text = f"{bulan_text} {tahun_text}"

    def prev_month(self):
        month = self.current_date.month - 1
        year = self.current_date.year
        if month < 1:
            month = 12
            year -= 1
        self.current_date = self.current_date.replace(year=year, month=month)
        self.update_month_display()
        self.update_data()

    def next_month(self):
        month = self.current_date.month + 1
        year = self.current_date.year
        if month > 12:
            month = 1
            year += 1
        self.current_date = self.current_date.replace(year=year, month=month)
        self.update_month_display()
        self.update_data()

    def update_data(self):
        try:
            email = self.user_email.strip()
            if email and hasattr(db, "get_summary"):
                saldo, income, expense = db.get_summary(
                    email, self.current_date.year, self.current_date.month
                )
            else:
                saldo, income, expense = 0.0, 0.0, 0.0

            if "saldo_label" in self.ids:
                self.ids.saldo_label.text = f"Rp {float(saldo):,.0f}".replace(
                    ",", "."
                )
            if "income_label" in self.ids:
                self.ids.income_label.text = f"Rp {float(income):,.0f}".replace(
                    ",", "."
                )
            if "expense_label" in self.ids:
                self.ids.expense_label.text = (
                    f"Rp {float(expense):,.0f}".replace(",", ".")
                )
        except Exception as e:
            print(f"Error saat memuat data beranda: {e}")
            if "saldo_label" in self.ids:
                self.ids.saldo_label.text = "Rp 0"
            if "income_label" in self.ids:
                self.ids.income_label.text = "Rp 0"
            if "expense_label" in self.ids:
                self.ids.expense_label.text = "Rp 0"

    def open_income(self):
        income_screen = self.manager.get_screen("income")
        income_screen.prepare_for_month(self.current_date)
        self.manager.current = "income"

    def open_expense(self):
        expense_screen = self.manager.get_screen("expense")
        expense_screen.prepare_for_month(self.current_date)
        self.manager.current = "expense"

    def go_to_statistic(self):
        if self.manager:
            self.manager.current = "statistic"

    def show_logout_dialog(self):
        if not self.dialog:
            self.dialog = MDDialog(
                title="Keluar dari Akun?",
                text="Apakah kamu yakin ingin keluar dari akun ini?",
                buttons=[
                    MDFlatButton(
                        text="Batal",
                        on_release=lambda x: self.dialog.dismiss(),
                    ),
                    MDRaisedButton(
                        text="Keluar",
                        md_bg_color=("#E53935"),
                        on_release=self.confirm_logout,
                    ),
                ],
            )
        self.dialog.open()

    def confirm_logout(self, instance):
        self.dialog.dismiss()
        self.manager.current = "login"


class IncomeScreen(BaseScreen):
    date_text = StringProperty(datetime.now().strftime("%d %B %Y"))
    selected_date = StringProperty(datetime.now().strftime("%Y-%m-%d"))

    def prepare_for_month(self, selected_month):
        today = datetime.now()
        if (selected_month.year, selected_month.month) == (
            today.year,
            today.month,
        ):
            selected = today
        else:
            selected = selected_month.replace(day=1)
        self.selected_date = selected.strftime("%Y-%m-%d")
        self.date_text = selected.strftime("%d %B %Y")

    def open_date_picker(self):
        selected = datetime.strptime(self.selected_date, "%Y-%m-%d")
        picker = MDDatePicker(
            year=selected.year,
            month=selected.month,
            day=selected.day,
            primary_color=get_color_from_hex("#278B58"),
            selector_color=get_color_from_hex("#278B58"),
        )
        picker.theme_cls.device_orientation = "portrait"
        picker.size_hint = (None, None)
        picker.size = (dp(328), dp(512))
        picker.radius = [16, 16, 16, 16]
        picker.bind(on_save=self.set_date)
        picker.open()

    def set_date(self, instance, value, date_range):
        self.date_text = value.strftime("%d %B %Y")
        self.selected_date = value.strftime("%Y-%m-%d")
        self.ids.date_input.focus = False

    def save_income(self):
        amount_text = (
            self.ids.amount_input.text.strip()
            .replace(".", "")
            .replace(",", "")
        )
        if not amount_text:
            return

        try:
            amount = float(amount_text)
        except ValueError:
            return

        home_screen = self.manager.get_screen("home")
        db.add_transaction(
            home_screen.user_email,
            "in",
            amount,
            self.ids.desc_input.text.strip(),
            self.selected_date,
        )
        self.ids.amount_input.text = ""
        self.ids.desc_input.text = ""
        home_screen.update_data()
        self.manager.current = "home"


class ExpenseScreen(BaseScreen):
    date_text = StringProperty(datetime.now().strftime("%d %B %Y"))
    selected_date = StringProperty(datetime.now().strftime("%Y-%m-%d"))

    def prepare_for_month(self, selected_month):
        today = datetime.now()
        if (selected_month.year, selected_month.month) == (
            today.year,
            today.month,
        ):
            selected = today
        else:
            selected = selected_month.replace(day=1)
        self.selected_date = selected.strftime("%Y-%m-%d")
        self.date_text = selected.strftime("%d %B %Y")

    def open_date_picker(self):
        selected = datetime.strptime(self.selected_date, "%Y-%m-%d")
        picker = MDDatePicker(
            year=selected.year,
            month=selected.month,
            day=selected.day,
            primary_color=get_color_from_hex("#F75A68"),
            selector_color=get_color_from_hex("#F75A68"),
        )
        picker.theme_cls.device_orientation = "portrait"
        picker.size_hint = (None, None)
        picker.size = (dp(328), dp(512))
        picker.radius = [16, 16, 16, 16]
        picker.bind(on_save=self.set_date)
        picker.open()

    def set_date(self, instance, value, date_range):
        self.date_text = value.strftime("%d %B %Y")
        self.selected_date = value.strftime("%Y-%m-%d")
        self.ids.date_input.focus = False

    def save_expense(self):
        amount_text = (
            self.ids.amount_input.text.strip()
            .replace(".", "")
            .replace(",", "")
        )
        if not amount_text:
            return

        try:
            amount = float(amount_text)
        except ValueError:
            return

        home_screen = self.manager.get_screen("home")
        db.add_transaction(
            home_screen.user_email,
            "out",
            amount,
            self.ids.desc_input.text.strip(),
            self.selected_date,
        )
        self.ids.amount_input.text = ""
        self.ids.desc_input.text = ""
        home_screen.update_data()
        self.manager.current = "home"


class StencilRelativeLayout(StencilView, RelativeLayout):
    pass


class StatisticScreen(Screen):
    current_date = datetime.now()
    _current_chart_data = []  # Menyimpan data grafik terakhir untuk re-draw saat resize

    def on_enter(self):
        # Bind event resize & pos dari chart_container agar grafik otomatis ter-update
        chart = self.ids.chart_container
        chart.unbind(size=self.on_chart_resize, pos=self.on_chart_resize)
        chart.bind(size=self.on_chart_resize, pos=self.on_chart_resize)

        self.update_display()

    def on_chart_resize(self, instance, value):
        # Panggil render ulang grafik hanya jika data sudah tersedia
        if self._current_chart_data:
            # Gunakan Clock agar penggambaran ulang tidak mengganggu proses rendering Kivy
            Clock.schedule_once(
                lambda dt: self.render_line_chart(self._current_chart_data), 0.01
            )

    def change_month(self, direction):
        year = self.current_date.year
        month = self.current_date.month + direction

        if month > 12:
            month = 1
            year += 1
        elif month < 1:
            month = 12
            year -= 1

        max_days = calendar.monthrange(year, month)[1]
        day = min(self.current_date.day, max_days)

        self.current_date = datetime(year, month, day)
        self.update_display()

    def update_display(self):
        self.update_month_label()
        Clock.schedule_once(lambda dt: self.update_statistics(), 0.05)

    def update_month_label(self):
        month_names = [
            "",
            "Januari",
            "Februari",
            "Maret",
            "April",
            "Mei",
            "Juni",
            "Juli",
            "Agustus",
            "September",
            "Oktober",
            "November",
            "Desember",
        ]
        self.ids.selected_month_label.text = (
            f"{month_names[self.current_date.month]} {self.current_date.year}"
        )

    def update_statistics(self):
        home_screen = self.manager.get_screen("home")
        email = home_screen.user_email
        data_bulan = []
        month_names = [
            "",
            "Januari",
            "Februari",
            "Maret",
            "April",
            "Mei",
            "Juni",
            "Juli",
            "Agustus",
            "September",
            "Oktober",
            "November",
            "Desember",
        ]

        for offset in range(3):
            month = self.current_date.month - offset
            year = self.current_date.year
            if month < 1:
                month += 12
                year -= 1
            income, expense = db.get_monthly_summary(email, year, month)
            data_bulan.append(
                {
                    "name": month_names[month][:3],
                    "inc": income,
                    "exp": expense,
                }
            )

        current = data_bulan[0]
        self.ids.stat_income_label.text = f"Rp {current['inc']:,.0f}".replace(
            ",", "."
        )
        self.ids.stat_expense_label.text = f"Rp {current['exp']:,.0f}".replace(
            ",", "."
        )

        # Simpan data terbaru ke variabel kelas
        self._current_chart_data = list(reversed(data_bulan))
        Clock.schedule_once(
            lambda dt: self.render_line_chart(self._current_chart_data), 0.05
        )

    def render_line_chart(self, data_bulan):
        chart = self.ids.chart_container

        chart.clear_widgets()
        chart.canvas.clear()
        chart.canvas.before.clear()
        chart.canvas.after.clear()

        w, h = chart.width, chart.height
        bx, by = chart.x, chart.y

        # Batalkan gambar jika ukuran kontainer belum siap/terlalu kecil
        if w < 50 or h < 50:
            return

        padding_l, padding_r = dp(40), dp(20)
        padding_b, padding_t = dp(25), dp(25)

        plot_w = w - padding_l - padding_r
        plot_h = h - padding_b - padding_t

        all_vals = [item["inc"] for item in data_bulan] + [
            item["exp"] for item in data_bulan
        ]
        max_val = max(all_vals) if all_vals and max(all_vals) > 0 else 10000
        max_y = (
            ((int(max_val) // 10000) + 1) * 10000 if max_val >= 10000 else 10000
        )

        steps = [0, max_y // 2, max_y]

        # 1. Buat Garis Grid Bantu
        with chart.canvas:
            Color(0.92, 0.92, 0.92, 1)
            for y_val in steps:
                y_pos = by + padding_b + (y_val / max_y) * plot_h
                Line(
                    points=[bx + padding_l, y_pos, bx + w - padding_r, y_pos],
                    width=1,
                )

        # 2. Label Sumbu Y
        for y_val in steps:
            y_pos = padding_b + (y_val / max_y) * plot_h
            lbl_text = (
                f"{y_val//1000}rb" if y_val >= 1000 else str(int(y_val))
            )
            lbl_y = MDLabel(
                text=lbl_text,
                font_style="Caption",
                theme_text_color="Custom",
                text_color=get_color_from_hex("#8E8E93"),
                pos=(bx, by + y_pos - dp(10)),
                size_hint=(None, None),
                size=(padding_l - dp(5), dp(20)),
                halign="right",
            )
            chart.add_widget(lbl_y)

        pts_inc, pts_exp = [], []
        step_x = (
            plot_w / (len(data_bulan) - 1) if len(data_bulan) > 1 else plot_w
        )

        for idx, item in enumerate(data_bulan):
            x_pos = bx + padding_l + (idx * step_x)
            y_inc = by + padding_b + (min(item["inc"], max_y) / max_y) * plot_h
            y_exp = by + padding_b + (min(item["exp"], max_y) / max_y) * plot_h

            pts_inc.extend([x_pos, y_inc])
            pts_exp.extend([x_pos, y_exp])

            # Label Nama Bulan di Bawah
            lbl_x = MDLabel(
                text=item["name"],
                font_style="Caption",
                bold=True,
                theme_text_color="Custom",
                text_color=get_color_from_hex("#1A1A1A"),
                pos=(x_pos - dp(20), by),
                size_hint=(None, None),
                size=(dp(40), dp(20)),
                halign="center",
            )
            chart.add_widget(lbl_x)

            # Angka Pemasukan di Atas Titik
            if item["inc"] > 0:
                txt_inc = (
                    f"{int(item['inc'])//1000}rb"
                    if item["inc"] >= 1000
                    else str(int(item["inc"]))
                )
                lbl_inc = MDLabel(
                    text=txt_inc,
                    font_style="Caption",
                    bold=True,
                    theme_text_color="Custom",
                    text_color=get_color_from_hex("#278B58"),
                    pos=(x_pos - dp(25), min(by + h - dp(18), y_inc + dp(6))),
                    size_hint=(None, None),
                    size=(dp(50), dp(18)),
                    halign="center",
                )
                chart.add_widget(lbl_inc)

            # Angka Pengeluaran di Bawah Titik
            if item["exp"] > 0:
                txt_exp = (
                    f"{int(item['exp'])//1000}rb"
                    if item["exp"] >= 1000
                    else str(int(item["exp"]))
                )
                lbl_exp = MDLabel(
                    text=txt_exp,
                    font_style="Caption",
                    bold=True,
                    theme_text_color="Custom",
                    text_color=get_color_from_hex("#E53935"),
                    pos=(
                        x_pos - dp(25),
                        max(by + padding_b - dp(14), y_exp - dp(18)),
                    ),
                    size_hint=(None, None),
                    size=(dp(50), dp(18)),
                    halign="center",
                )
                chart.add_widget(lbl_exp)

        # 3. Draw Lines & Circles (Garis & Titik)
        with chart.canvas:
            # Line & Circle Pemasukan
            Color(*get_color_from_hex("#278B58"))
            if len(pts_inc) >= 4:
                Line(points=pts_inc, width=2.5)
            for i in range(0, len(pts_inc), 2):
                Ellipse(
                    pos=(pts_inc[i] - dp(4), pts_inc[i + 1] - dp(4)),
                    size=(dp(8), dp(8)),
                )

            # Line & Circle Pengeluaran
            Color(*get_color_from_hex("#E53935"))
            if len(pts_exp) >= 4:
                Line(points=pts_exp, width=2.5)
            for i in range(0, len(pts_exp), 2):
                Ellipse(
                    pos=(pts_exp[i] - dp(4), pts_exp[i + 1] - dp(4)),
                    size=(dp(8), dp(8)),
                )
                

class HistoryScreen(BaseScreen):
    current_filter = StringProperty("all")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_date = datetime.now()
        self.transactions_data = []

    def on_enter(self):
        self.update_month_label()
        self.load_history()

    def update_month_label(self):
        self.ids.history_month_label.text = (
            f"{self.current_date.strftime('%B')} {self.current_date.year}"
        )

    def change_month(self, direction):
        month = self.current_date.month + direction
        year = self.current_date.year
        if month < 1:
            month, year = 12, year - 1
        elif month > 12:
            month, year = 1, year + 1
        self.current_date = self.current_date.replace(year=year, month=month)
        self.update_month_label()
        self.load_history()

    def filter_transactions(self, filter_type):
        self.current_filter = filter_type
        self.update_filter_button_styles() # Perbarui warna tombol saat diklik
        self.load_history()

    def update_filter_button_styles(self):
        # Daftar tombol dan tipe filternya
        buttons = [
            (self.ids.btn_filter_all, "all"),
            (self.ids.btn_filter_income, "income"),
            (self.ids.btn_filter_expense, "expense"),
        ]

        active_bg = get_color_from_hex("#278B58")
        active_text = [1, 1, 1, 1]
        inactive_bg = [1, 1, 1, 1]
        inactive_text = get_color_from_hex("#8E8E93")

        for btn, f_type in buttons:
            if f_type == self.current_filter:
                btn.md_bg_color = active_bg
                btn.text_color = active_text
            else:
                btn.md_bg_color = inactive_bg
                btn.text_color = inactive_text

    def load_history(self):
        container = self.ids.history_list_container
        container.clear_widgets()

        home_screen = self.manager.get_screen("home")
        self.transactions_data = db.get_transactions(
            home_screen.user_email,
            self.current_date.year,
            self.current_date.month,
        )

        visible_transactions = [
            item
            for item in self.transactions_data
            if self.current_filter == "all"
            or item["type"] == self.current_filter
        ]
        total_income = sum(
            item["amount"]
            for item in self.transactions_data
            if item["type"] == "income"
        )
        total_expense = sum(
            item["amount"]
            for item in self.transactions_data
            if item["type"] == "expense"
        )
        saldo_akhir = total_income - total_expense

        self.ids.history_total_balance.text = f"Rp {saldo_akhir:,.0f}".replace(
            ",", "."
        )

        self.ids.history_empty_label.opacity = (
            0 if visible_transactions else 1
        )
        self.ids.history_empty_label.height = (
            "0dp" if visible_transactions else "48dp"
        )

        for item in visible_transactions:
            is_income = item["type"] == "income"
            theme_color = "#278B58" if is_income else "#F75A68"
            bg_icon_color = "#E8F5E9" if is_income else "#FFEBEE"
            sign = "+" if is_income else "-"
            icon_name = "plus" if is_income else "minus"

            row = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height="54dp",
                spacing="12dp",
            )

            icon_card = MDCard(
                radius=[12, 12, 12, 12],
                elevation=0,
                md_bg_color=get_color_from_hex(bg_icon_color),
                size_hint=(None, None),
                size=("42dp", "42dp"),
                pos_hint={"center_y": 0.5},
            )
            icon_layout = MDRelativeLayout(size=icon_card.size)
            icon_layout.add_widget(
                MDIcon(
                    icon=icon_name,
                    size_hint=(None, None),
                    size=("24dp", "24dp"),
                    pos_hint={"center_x": 0.5, "center_y": 0.5},
                    theme_text_color="Custom",
                    text_color=get_color_from_hex(theme_color),
                )
            )
            icon_card.add_widget(icon_layout)

            info_box = MDBoxLayout(
                orientation="vertical", spacing="2dp", pos_hint={"center_y": 0.5}
            )
            info_box.add_widget(
                MDLabel(
                    text=item["desc"],
                    bold=True,
                    font_style="Subtitle2",
                    theme_text_color="Custom",
                    text_color=get_color_from_hex("#1A1A1A"),
                )
            )
            info_box.add_widget(
                MDLabel(
                    text=f"{'Pemasukan' if is_income else 'Pengeluaran'} · {item['date']}",
                    font_style="Caption",
                    theme_text_color="Custom",
                    text_color=get_color_from_hex("#8E8E93"),
                )
            )

            amount_lbl = MDLabel(
                text=f"{sign} Rp {item['amount']:,.0f}".replace(",", "."),
                bold=True,
                font_style="Subtitle2",
                adaptive_width=True,
                pos_hint={"center_y": 0.5},
                theme_text_color="Custom",
                text_color=get_color_from_hex(theme_color),
            )

            row.add_widget(icon_card)
            row.add_widget(info_box)
            row.add_widget(amount_lbl)

            row.bind(
                on_touch_down=lambda instance, touch, data=item: self.open_detail(
                    instance, touch, data
                )
            )
            container.add_widget(row)

    def open_detail(self, instance, touch, data):
        if instance.collide_point(*touch.pos):
            detail_screen = self.manager.get_screen("detail")
            detail_screen.set_detail_data(data)
            self.manager.current = "detail"

class DetailScreen(BaseScreen):

    def set_detail_data(self, data):
        is_income = data["type"] == "income"
        color_hex = "#278B58" if is_income else "#F75A68"
        sign = "" if is_income else "-"

        self.ids.detail_icon_bg.md_bg_color = get_color_from_hex(color_hex)
        self.ids.detail_icon.icon = "plus" if is_income else "minus"
        self.ids.detail_type_label.text = (
            "Pemasukan" if is_income else "Pengeluaran"
        )

        self.ids.detail_amount_label.text = f"{sign}Rp {data['amount']:,.0f}".replace(
            ",", "."
        )
        self.ids.detail_desc_label.text = data["desc"]
        try:
            detail_date = datetime.strptime(data["date"], "%Y-%m-%d")
            self.ids.detail_date_label.text = detail_date.strftime("%d %B %Y")
        except (TypeError, ValueError):
            self.ids.detail_date_label.text = data["date"]

        self.ids.detail_back_button.md_bg_color = get_color_from_hex(
            color_hex
        )


class MainApp(MDApp):
    def build(self):
        if hasattr(db, "init_db"):
            db.init_db()
        elif hasattr(db, "create_tables"):
            db.create_tables()

        # Muat file cashflow.kv secara eksplisit saat app dibangun
        kv_path = os.path.join(os.path.dirname(__file__), "cashflow.kv")
        Builder.unload_file(kv_path)
        Builder.load_file(kv_path)

        sm = ScreenManager(
            transition=SlideTransition(direction="left", duration=0.22)
        )
        sm.add_widget(SplashScreen(name="splash"))
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(RegisterScreen(name="register"))
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(IncomeScreen(name="income"))
        sm.add_widget(ExpenseScreen(name="expense"))
        sm.add_widget(StatisticScreen(name="statistic"))
        sm.add_widget(HistoryScreen(name="history"))
        sm.add_widget(DetailScreen(name="detail"))
        return sm

    def on_stop(self):
        db.close()


if __name__ == "__main__":
    MainApp().run()