import calendar
from datetime import date, datetime
import os

from db import Database
from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ListProperty, ObjectProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.uix.stencilview import StencilView
from kivy.utils import get_color_from_hex, platform
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDIcon, MDLabel
from kivymd.uix.pickers import MDDatePicker
from kivymd.uix.relativelayout import MDRelativeLayout

# Ukuran jendela hanya dipaksa di desktop; di Android ikut layar
if platform != "android":
    Config.set("graphics", "width", "390")
    Config.set("graphics", "height", "844")
    Config.set("graphics", "resizable", "0")
    Config.set("graphics", "borderless", "0")
    Window.size = (390, 844)
    Window.minimum_width = 320
    Window.minimum_height = 560

Window.clearcolor = (0.96, 0.95, 0.91, 1)

db = Database()

MONTH_NAMES = (
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
)
MONTH_ABBREVIATIONS = (
    "",
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "Mei",
    "Jun",
    "Jul",
    "Agu",
    "Sep",
    "Okt",
    "Nov",
    "Des",
)
WEEKDAY_NAMES = (
    "Senin",
    "Selasa",
    "Rabu",
    "Kamis",
    "Jumat",
    "Sabtu",
    "Minggu",
)
WEEKDAY_ABBREVIATIONS = ("Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min")

calendar.month_name = MONTH_NAMES
calendar.month_abbr = MONTH_ABBREVIATIONS
calendar.day_name = WEEKDAY_NAMES
calendar.day_abbr = WEEKDAY_ABBREVIATIONS


class BaseScreen(Screen):
    def prepare_date_picker(self, selected, color):
        picker = getattr(self, "_date_picker", None)
        if picker is None:
            picker = IndonesianDatePicker(
                year=selected.year,
                month=selected.month,
                day=selected.day,
                primary_color=color,
                selector_color=color,
                show_duration=0,
                hide_duration=0,
            )
            picker.bind(on_save=self.set_date)
            picker.bind(on_dismiss=self.on_date_picker_dismiss)
            self._date_picker = picker
        picker.primary_color = color
        picker.selector_color = color
        picker_date = (picker.sel_year, picker.sel_month, picker.sel_day)
        selected_date = (selected.year, selected.month, selected.day)
        if picker_date != selected_date:
            picker.sel_year, picker.sel_month, picker.sel_day = selected_date
            picker.day = selected.day
            picker.update_calendar(selected.year, selected.month)
        return picker

    def show_date_picker(self, selected, color):
        if getattr(self, "_date_picker_opening", False):
            return
        active_picker = getattr(self, "_active_date_picker", None)
        if active_picker and active_picker.parent:
            return

        picker = self.prepare_date_picker(selected, color)
        self._active_date_picker = picker
        self._date_picker_opening = True
        try:
            picker.open()
        except Exception:
            if not picker.parent:
                self._date_picker_opening = False
                self._active_date_picker = None
            raise

    def on_date_picker_dismiss(self, picker, *_args):
        self._date_picker_opening = False
        if picker is self._active_date_picker:
            self._active_date_picker = None


class DirectionalScreenManager(ScreenManager):
    def navigate_to(self, screen_name):
        current = self.current
        if current == screen_name:
            return

        tab_order = {"home": 0, "statistic": 1, "history": 2}
        if current in tab_order and screen_name in tab_order:
            direction = (
                "left"
                if tab_order[screen_name] > tab_order[current]
                else "right"
            )
        elif (current in ("income", "expense") and screen_name == "home") or (
            current == "detail" and screen_name == "history"
        ) or (current == "register" and screen_name == "login"):
            direction = "right"
        elif current in ("home", "history", "login", "splash") or (
            current in ("income", "expense") and screen_name == "detail"
        ):
            direction = "left"
        else:
            direction = "left"

        self.transition.direction = direction
        self.current = screen_name


class BottomNavigation(MDBoxLayout):
    selected = StringProperty("home")
    manager = ObjectProperty(None, allownone=True)

    def attach(self, manager):
        self.manager = manager
        manager.bind(current=self.on_screen_change)
        self.on_screen_change(manager, manager.current)

    def on_screen_change(self, manager, screen_name):
        visible = screen_name in ("home", "history", "statistic")
        self.height = dp(64)
        self.opacity = 1 if visible else 0
        self.disabled = not visible
        if visible:
            self.selected = screen_name

    def navigate(self, screen_name):
        if self.manager:
            self.manager.navigate_to(screen_name)


class DatePickerField(MDBoxLayout):
    screen = ObjectProperty(None, allownone=True)
    picker_color = ListProperty((0.15, 0.55, 0.35, 1))
    date_text = StringProperty("")

    def open_picker(self):
        if self.screen and not getattr(
            self.screen, "_date_picker_opening", False
        ):
            self.screen.open_date_picker()


class IndonesianDatePicker(MDDatePicker):
    def set_text_full_date(self, year, month, day, orientation):
        horizontal = (
            orientation == "portrait" or self._input_date_dialog_open
        )

        def date_repr(selected_date):
            return (
                f"{MONTH_ABBREVIATIONS[selected_date.month]} "
                f"{selected_date.day}"
            )

        input_dates = self._get_dates_from_fields()
        if self.mode == "picker":
            selected_date = date(self.sel_year, self.sel_month, self.sel_day)
            if input_dates and input_dates[0]:
                selected_date = input_dates[0]
            separator = ", " if horizontal else ",\n"
            weekday = WEEKDAY_ABBREVIATIONS[selected_date.weekday()]
            return f"{weekday}{separator}{date_repr(selected_date)}"

        start, end = self.min_date, self.max_date
        if input_dates:
            start, end = input_dates[0] or start, input_dates[1] or end
        dates = sorted(value for value in (start, end) if value)
        if not dates:
            return "Mulai — Selesai"
        if len(dates) == 1:
            return date_repr(dates[0])
        separator = " — " if horizontal else ",\n"
        return f"{date_repr(dates[0])}{separator}{date_repr(dates[-1])}"


def get_logo_path():
    logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
    if os.path.exists(logo_path):
        return logo_path
    return "atlas://data/images/defaulttheme/filechooser_folder"


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
            self.manager.navigate_to("home")
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
                lambda dt: self.manager.navigate_to("login"), 1.5
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

    def on_enter(self):
        if self.ids:
            self.ids.user_greeting.text = f"Halo, {self.user_name}!"
        self.update_month_display()
        self.update_data()

    def update_month_display(self):
        bulan_text = MONTH_NAMES[self.current_date.month]
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
        self.manager.navigate_to("income")

    def open_expense(self):
        expense_screen = self.manager.get_screen("expense")
        expense_screen.prepare_for_month(self.current_date)
        self.manager.navigate_to("expense")

    def go_to_statistic(self):
        if self.manager:
            self.manager.navigate_to("statistic")

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
        self.manager.navigate_to("login")


class IncomeScreen(BaseScreen):
    picker_color = get_color_from_hex("#278B58")
    date_text = StringProperty(datetime.now().strftime("%d/%m/%Y"))
    selected_date = StringProperty(datetime.now().strftime("%Y-%m-%d"))

    def prepare_for_month(self, selected_month):
        today = datetime.now()
        day = min(
            today.day,
            calendar.monthrange(selected_month.year, selected_month.month)[1],
        )
        selected = datetime(selected_month.year, selected_month.month, day)
        self.selected_date = selected.strftime("%Y-%m-%d")
        self.date_text = selected.strftime("%d/%m/%Y")
        self.ids.amount_input.text = ""
        self.ids.desc_input.text = ""
        self.ids.amount_input.focus = False
        self.ids.desc_input.focus = False

    def open_date_picker(self):
        selected = datetime.strptime(self.selected_date, "%Y-%m-%d")
        self.show_date_picker(selected, self.picker_color)

    def set_date(self, instance, value, date_range):
        self.date_text = value.strftime("%d/%m/%Y")
        self.selected_date = value.strftime("%Y-%m-%d")

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
        self.manager.navigate_to("home")


class ExpenseScreen(BaseScreen):
    picker_color = get_color_from_hex("#F75A68")
    date_text = StringProperty(datetime.now().strftime("%d/%m/%Y"))
    selected_date = StringProperty(datetime.now().strftime("%Y-%m-%d"))

    def prepare_for_month(self, selected_month):
        today = datetime.now()
        day = min(
            today.day,
            calendar.monthrange(selected_month.year, selected_month.month)[1],
        )
        selected = datetime(selected_month.year, selected_month.month, day)
        self.selected_date = selected.strftime("%Y-%m-%d")
        self.date_text = selected.strftime("%d/%m/%Y")
        self.ids.amount_input.text = ""
        self.ids.desc_input.text = ""
        self.ids.amount_input.focus = False
        self.ids.desc_input.focus = False

    def open_date_picker(self):
        selected = datetime.strptime(self.selected_date, "%Y-%m-%d")
        self.show_date_picker(selected, self.picker_color)

    def set_date(self, instance, value, date_range):
        self.date_text = value.strftime("%d/%m/%Y")
        self.selected_date = value.strftime("%Y-%m-%d")

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
        self.manager.navigate_to("home")


class HistoryTransactionRow(ButtonBehavior, MDBoxLayout):
    pass


class StencilRelativeLayout(StencilView, RelativeLayout):
    pass


class StatisticScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_date = datetime.now()
        self._statistics_event = None
        self._chart_retry_event = None
        self._chart_retry_count = 0
        self._pending_chart_data = None
        self._last_chart_signature = None

    def on_enter(self):
        self.update_display()

    def on_leave(self):
        if self._statistics_event:
            self._statistics_event.cancel()
            self._statistics_event = None
        if self._chart_retry_event:
            self._chart_retry_event.cancel()
            self._chart_retry_event = None

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
        if self._statistics_event:
            self._statistics_event.cancel()
        self._chart_retry_count = 0
        self._statistics_event = Clock.schedule_once(
            self.run_scheduled_statistics, 0
        )

    def run_scheduled_statistics(self, _dt):
        self._statistics_event = None
        self.update_statistics()

    def update_month_label(self):
        self.ids.selected_month_label.text = (
            f"{MONTH_NAMES[self.current_date.month]} {self.current_date.year}"
        )

    def update_statistics(self):
        home_screen = self.manager.get_screen("home")
        email = home_screen.user_email
        data_bulan = []
        for offset in range(3):
            month = self.current_date.month - offset
            year = self.current_date.year
            if month < 1:
                month += 12
                year -= 1
            income, expense = db.get_monthly_summary(email, year, month)
            data_bulan.append({
                "name": MONTH_NAMES[month][:3],
                "inc": income,
                "exp": expense,
            })

        current = data_bulan[0]
        self.ids.stat_income_label.text = f"Rp {current['inc']:,.0f}".replace(
            ",", "."
        )
        self.ids.stat_expense_label.text = f"Rp {current['exp']:,.0f}".replace(
            ",", "."
        )

        chart_data = list(reversed(data_bulan))
        self._pending_chart_data = chart_data
        if self._chart_retry_event:
            self._chart_retry_event.cancel()
        self._chart_retry_event = Clock.schedule_once(
            self.render_scheduled_chart, 0.05
        )

    def render_scheduled_chart(self, _dt):
        self._chart_retry_event = None
        if self._pending_chart_data is not None:
            self.render_line_chart(self._pending_chart_data)

    def render_line_chart(self, data_bulan):
        chart = self.ids.chart_container
        w, h = chart.width, chart.height
        bx, by = chart.x, chart.y

        if w < 50 or h < 50:
            if (
                self.manager
                and self.manager.current == self.name
                and self._chart_retry_count < 5
            ):
                self._chart_retry_count += 1
                self._pending_chart_data = data_bulan
                self._chart_retry_event = Clock.schedule_once(
                    self.render_scheduled_chart, 0.1
                )
            return

        signature = (
            tuple(
                (item["name"], item["inc"], item["exp"])
                for item in data_bulan
            ),
            w,
            h,
            bx,
            by,
        )
        if signature == self._last_chart_signature:
            return

        chart.clear_widgets()
        chart.canvas.clear()
        chart.canvas.before.clear()
        chart.canvas.after.clear()
        padding_l, padding_r = 45, 25
        padding_b, padding_t = 30, 30

        plot_w = w - padding_l - padding_r
        plot_h = h - padding_b - padding_t

        all_vals = [item["inc"] for item in data_bulan] + [
            item["exp"] for item in data_bulan
        ]
        max_val = max(all_vals) if all_vals and max(all_vals) > 0 else 10000
        max_y = (
            ((int(max_val) // 10000) + 1) * 10000
            if max_val >= 10000
            else 10000
        )

        steps = [0, max_y // 2, max_y]

        with chart.canvas:
            Color(0.9, 0.9, 0.9, 1)
            for y_val in steps:
                y_pos = by + padding_b + (y_val / max_y) * plot_h
                Line(
                    points=[bx + padding_l, y_pos, bx + w - padding_r, y_pos],
                    width=1,
                )

        for y_val in steps:
            y_pos = padding_b + (y_val / max_y) * plot_h
            lbl_text = f"{y_val//1000}rb" if y_val >= 1000 else str(int(y_val))
            lbl_y = MDLabel(
                text=lbl_text,
                font_style="Caption",
                theme_text_color="Custom",
                text_color=get_color_from_hex("#8E8E93"),
                pos=(bx + 2, by + y_pos - 10),
                size_hint=(None, None),
                size=("38dp", "20dp"),
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

            lbl_x = MDLabel(
                text=item["name"],
                font_style="Caption",
                bold=True,
                theme_text_color="Custom",
                text_color=get_color_from_hex("#1A1A1A"),
                pos=(x_pos - 20, by + 2),
                size_hint=(None, None),
                size=("40dp", "20dp"),
                halign="center",
            )
            chart.add_widget(lbl_x)

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
                    pos=(x_pos - 25, min(by + h - 18, y_inc + 4)),
                    size_hint=(None, None),
                    size=("50dp", "18dp"),
                    halign="center",
                )
                chart.add_widget(lbl_inc)

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
                    pos=(x_pos - 25, max(by + padding_b - 12, y_exp - 18)),
                    size_hint=(None, None),
                    size=("50dp", "18dp"),
                    halign="center",
                )
                chart.add_widget(lbl_exp)

        with chart.canvas:
            Color(*get_color_from_hex("#278B58"))
            if len(pts_inc) >= 4:
                Line(points=pts_inc, width=2.5)
            for i in range(0, len(pts_inc), 2):
                Ellipse(
                    pos=(pts_inc[i] - 4, pts_inc[i + 1] - 4), size=(8, 8)
                )

            Color(*get_color_from_hex("#E53935"))
            if len(pts_exp) >= 4:
                Line(points=pts_exp, width=2.5)
            for i in range(0, len(pts_exp), 2):
                Ellipse(
                    pos=(pts_exp[i] - 4, pts_exp[i + 1] - 4), size=(8, 8)
                )
        self._last_chart_signature = signature
        self._chart_retry_count = 0


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
            f"{MONTH_NAMES[self.current_date.month]} {self.current_date.year}"
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
        if filter_type == self.current_filter:
            return
        self.current_filter = filter_type
        self.update_filter_button_styles()
        self.apply_history_filter()

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
        home_screen = self.manager.get_screen("home")
        transactions = db.get_transactions(
            home_screen.user_email,
            self.current_date.year,
            self.current_date.month,
        )
        if (
            transactions == self.transactions_data
            and hasattr(self, "transaction_rows")
        ):
            self.apply_history_filter()
            return

        container = self.ids.history_list_container
        container.clear_widgets()
        self.transaction_rows = []
        self.transactions_data = transactions

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

        for item in self.transactions_data:
            is_income = item["type"] == "income"
            theme_color = "#278B58" if is_income else "#F75A68"
            bg_icon_color = "#E8F5E9" if is_income else "#FFEBEE"
            sign = "+" if is_income else "-"
            icon_name = "plus" if is_income else "minus"

            row = HistoryTransactionRow(
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

            row.bind(on_release=lambda _instance, data=item: self.open_detail(data))
            container.add_widget(row)
            self.transaction_rows.append((item, row))

        self.apply_history_filter()

    def apply_history_filter(self):
        container = self.ids.history_list_container
        container.clear_widgets()
        has_visible_transactions = False
        for item, row in self.transaction_rows:
            visible = (
                self.current_filter == "all"
                or item["type"] == self.current_filter
            )
            if visible:
                row.height = dp(54)
                row.opacity = 1
                row.disabled = False
                container.add_widget(row)
                has_visible_transactions = True
            else:
                row.disabled = True

        empty_label = self.ids.history_empty_label
        empty_label.opacity = 0 if has_visible_transactions else 1
        empty_label.height = dp(0) if has_visible_transactions else dp(48)

    def open_detail(self, data):
        detail_screen = self.manager.get_screen("detail")
        detail_screen.set_detail_data(data)
        self.manager.navigate_to("detail")

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
            self.ids.detail_date_label.text = (
                f"{detail_date.day} {MONTH_NAMES[detail_date.month]} "
                f"{detail_date.year}"
            )
        except (TypeError, ValueError):
            self.ids.detail_date_label.text = data["date"]

        self.ids.detail_back_button.md_bg_color = get_color_from_hex(
            color_hex
        )


class MainApp(MDApp):
    def build(self):
        self.theme_cls.device_orientation = "portrait"
        if hasattr(db, "init_db"):
            db.init_db()
        elif hasattr(db, "create_tables"):
            db.create_tables()

        # Muat file cashflow.kv secara eksplisit saat app dibangun
        kv_path = os.path.join(os.path.dirname(__file__), "cashflow.kv")
        Builder.unload_file(kv_path)
        Builder.load_file(kv_path)

        sm = DirectionalScreenManager(
            transition=SlideTransition(direction="left", duration=0.22)
        )
        home_screen = HomeScreen(name="home")
        login_screen = LoginScreen(name="login")
        user = db.get_first_user()
        if user:
            home_screen.user_name, home_screen.user_email = user
            sm.add_widget(home_screen)
        else:
            sm.add_widget(login_screen)

        sm.add_widget(RegisterScreen(name="register"))
        if user:
            sm.add_widget(login_screen)
        else:
            sm.add_widget(home_screen)
        sm.add_widget(IncomeScreen(name="income"))
        sm.add_widget(ExpenseScreen(name="expense"))
        sm.add_widget(StatisticScreen(name="statistic"))
        sm.add_widget(HistoryScreen(name="history"))
        sm.add_widget(DetailScreen(name="detail"))
        self.screen_manager = sm
        self.awaiting_exit_confirmation = False
        self.exit_notice_timeout = None
        self.launch_splash = None
        sm.bind(current=self.on_screen_change)
        root = FloatLayout()
        content = MDBoxLayout(
            orientation="vertical",
            md_bg_color=get_color_from_hex("#FAF8F5"),
        )
        content.add_widget(sm)
        navigation = BottomNavigation(size_hint_y=None, height=dp(64))
        navigation.attach(sm)
        content.add_widget(navigation)
        root.add_widget(content)
        self.exit_notice = MDCard(
            size_hint=(0.92, None),
            height=dp(52),
            pos_hint={"center_x": 0.5, "y": 0.08},
            radius=[dp(12)] * 4,
            elevation=0,
            md_bg_color=get_color_from_hex("#323232"),
            opacity=0,
            disabled=True,
        )
        self.exit_notice.add_widget(
            MDLabel(
                text="Tekan kembali sekali lagi untuk keluar",
                halign="center",
                valign="middle",
                theme_text_color="Custom",
                text_color=(1, 1, 1, 1),
            )
        )
        root.add_widget(self.exit_notice)
        if platform == "android":
            self.launch_splash = Image(
                source=os.path.join(os.path.dirname(__file__), "presplash.png"),
                allow_stretch=True,
                keep_ratio=True,
            )
            root.add_widget(self.launch_splash)
        return root

    def on_start(self):
        Window.bind(on_keyboard=self.on_keyboard)
        Clock.schedule_once(self.prewarm_date_pickers, 0.1)
        if self.launch_splash:
            Clock.schedule_once(self.hide_launch_splash, 2)

    def prewarm_date_pickers(self, _dt):
        selected = datetime.now()
        for screen_name in ("income", "expense"):
            screen = self.screen_manager.get_screen(screen_name)
            screen.prepare_date_picker(selected, screen.picker_color)

    def hide_launch_splash(self, _dt):
        if self.launch_splash and self.root:
            self.root.remove_widget(self.launch_splash)
            self.launch_splash = None

    def on_screen_change(self, manager, screen_name):
        if screen_name != "home":
            self.cancel_exit_prompt()

    def on_keyboard(
        self, window, key, scancode=None, codepoint=None, modifier=None
    ):
        if key != 27:
            return False

        manager = self.screen_manager
        back_routes = {
            "register": "login",
            "income": "home",
            "expense": "home",
            "statistic": "home",
            "history": "home",
            "detail": "history",
        }
        destination = back_routes.get(manager.current)
        if destination:
            self.dismiss_exit_prompt()
            manager.navigate_to(destination)
            return True

        if self.awaiting_exit_confirmation:
            self.awaiting_exit_confirmation = False
            self.dismiss_exit_prompt()
            self.stop()
            return True

        self.awaiting_exit_confirmation = True
        self.show_exit_prompt()
        return True

    def show_exit_prompt(self):
        self.dismiss_exit_prompt()
        self.exit_notice.disabled = False
        self.exit_notice.opacity = 1
        self.exit_notice_timeout = Clock.schedule_once(
            lambda _dt: self.hide_exit_notice(), 2
        )

    def hide_exit_notice(self):
        if self.exit_notice_timeout:
            self.exit_notice_timeout.cancel()
            self.exit_notice_timeout = None
        self.exit_notice.opacity = 0
        self.exit_notice.disabled = True

    def dismiss_exit_prompt(self):
        self.hide_exit_notice()

    def cancel_exit_prompt(self):
        self.dismiss_exit_prompt()
        self.awaiting_exit_confirmation = False

    def on_stop(self):
        Window.unbind(on_keyboard=self.on_keyboard)
        self.dismiss_exit_prompt()
        db.close()


if __name__ == "__main__":
    MainApp().run()