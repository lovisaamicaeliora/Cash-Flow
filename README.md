# Cash Flow

Cash Flow adalah aplikasi pengelola keuangan pribadi berbasis Kivy/KivyMD yang dibuat untuk membantu pengguna mencatat pemasukan, pengeluaran, saldo, serta melihat statistik dan riwayat transaksi bulanan.

Aplikasi ini cocok digunakan untuk kebutuhan pribadi seperti monitoring pengeluaran harian, bulanan, serta mengevaluasi kondisi keuangan secara cepat.


## Fitur utama

- Pendaftaran akun dan login pengguna
- Dashboard saldo, pemasukan, dan pengeluaran
- Input transaksi pemasukan
- Input transaksi pengeluaran
- Navigasi bulan untuk melihat data per periode
- Statistik bulanan dalam bentuk grafik garis
- Riwayat transaksi dengan filter semua/pemasukan/pengeluaran
- Detail transaksi per item
- Logout akun


## Struktur folder project

- `main.py` : logika aplikasi, screen, dan tampilan utama
- `db.py` : koneksi database SQLite dan operasi CRUD transaksi
- `cashflow.kv` : layout UI Kivy/KivyMD
- `buildozer.spec` : konfigurasi build Android
- `requirements.txt` : daftar dependency Python
- `cashflow.db` : database lokal aplikasi
- `logo.png` : logo aplikasi



## Panduan penggunaan aplikasi

### 1. Halaman Splash

Saat aplikasi dibuka, akan muncul layar splash selama beberapa detik. Setelah itu aplikasi akan otomatis menuju:

- halaman Home jika akun sudah terdaftar dan login terakhir tersimpan
- halaman Login jika belum ada akun atau data pengguna belum ada


### 2. Membuat akun baru

1. Pilih menu atau tombol untuk masuk ke halaman register.
2. Isi data:
   - Nama lengkap
   - Email yang berakhiran `@gmail.com`
   - Password
   - Konfirmasi password
3. Tekan tombol daftar/register.
4. Jika berhasil, aplikasi akan menampilkan pesan pendaftaran berhasil dan otomatis membawa ke halaman login.

Catatan:
- Email harus diakhiri dengan `@gmail.com`.
- Password tidak boleh kosong.
- Konfirmasi password harus sama dengan password awal.


### 3. Login ke aplikasi

1. Masukkan email akun.
2. Masukkan password.
3. Tekan tombol login.
4. Jika benar, aplikasi akan masuk ke halaman home/dashboard.


### 4. Dashboard utama (Home)

Halaman Home menampilkan informasi keuangan utama, yaitu:

- Saldo saat ini
- Total pemasukan pada bulan yang dipilih
- Total pengeluaran pada bulan yang dipilih
- Nama pengguna dan ucapan selamat datang

Pada halaman ini juga tersedia navigasi bulan:

- Tombol sebelumnya untuk melihat bulan sebelumya
- Tombol berikutnya untuk melihat bulan berikutnya


### 5. Menambah pemasukan

1. Dari halaman Home, pilih menu atau tombol tambah pemasukan.
2. Isi form:
   - jumlah nominal
   - deskripsi/keterangan
   - tanggal transaksi
3. Tekan tombol simpan.
4. Data otomatis akan masuk ke database dan dashboard akan terupdate.

Catatan:
- Nominal dapat diisi dalam format angka normal, misalnya `1500000` atau `1.500.000`.
- Sistem akan menyesuaikan format tampilan menjadi format rupiah.


### 6. Menambah pengeluaran

1. Pilih menu atau tombol tambah pengeluaran.
2. Isi form:
   - jumlah nominal
   - deskripsi/keterangan
   - tanggal transaksi
3. Tekan tombol simpan.
4. Data akan tersimpan dan menghitung saldo yang baru.


### 7. Statistik bulanan

1. Masuk ke menu statistik.
2. Aplikasi akan menampilkan data bulan yang sedang aktif.
3. Terdapat tombol untuk berpindah bulan.
4. Grafik baris menampilkan tren pemasukan dan pengeluaran selama beberapa bulan terakhir.
5. Label juga menampilkan total pemasukan dan total pengeluaran untuk bulan yang sedang dipilih.


### 8. Riwayat transaksi

1. Buka halaman riwayat transaksi.
2. Aplikasi menampilkan semua data transaksi per bulan.
3. Gunakan filter:
   - Semua
   - Pemasukan
   - Pengeluaran
4. Klik item transaksi untuk membuka detail.


### 9. Detail transaksi

Di halaman detail Anda dapat melihat:

- jenis transaksi (pemasukan atau pengeluaran)
- jumlah nominal
- keterangan
- tanggal


### 10. Logout

1. Tekan tombol logout yang ada di halaman home.
2. Konfirmasi keluar dari akun.
3. Aplikasi akan kembali ke halaman login.


## Catatan penting

- Database aplikasi menggunakan SQLite dan disimpan lokal di folder project (`cashflow.db`).
- Data bersifat lokal di perangkat, sehingga tidak langsung terhubung ke internet atau server cloud.
- Aplikasi dibuat untuk kebutuhan penggunaan pribadi.