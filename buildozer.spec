[app]
title = CashFlow
package.name = cashflow
package.domain = org.cashflow

source.dir = .
source.include_exts = py,png,jpg,kv,atlas
source.exclude_dirs = bin,.buildozer,venv,__pycache__,.git
source.exclude_patterns = *.db,*.pyc,requirements.txt

version = 1.0

# Python 3 + Kivy/KivyMD + Pillow
# SQLite adalah modul bawaan Python, jadi tidak perlu ditambahkan ke requirements
requirements = python3,kivy==2.3.0,kivymd==1.2.0,pillow

orientation = portrait
fullscreen = 0

presplash.filename = %(source.dir)s/logo.png
android.presplash_color = #F5F2E8

# Aplikasi ini offline dan hanya menyimpan data di folder privat,
# jadi tidak butuh izin apa pun.
android.permissions =
android.api = 33
android.minapi = 24
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a
android.release_artifact = apk
android.icon = %(source.dir)s/logo.png

[buildozer]
log_level = 2
warn_on_root = 1
android.logcat_filters = *:S python:D
