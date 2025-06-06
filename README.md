# Aplikasi-Peramalan-Penjualan-Menggunakan-Algoritma-SES-Berbasis-Web

##📌 Judul Proyek
Sales Forecasting Web App using Single Exponential Smoothing (SES)
(Aplikasi Peramalan Penjualan Menggunakan Algoritma SES Berbasis Web)

##📖 Deskripsi Singkat
Proyek ini merupakan aplikasi berbasis web untuk memprediksi penjualan menggunakan algoritma Single Exponential Smoothing (SES). Sistem ini mengambil data historis penjualan, melakukan proses peramalan, dan menampilkan hasil prediksi secara visual kepada pengguna.
Proyek ini menggabungkan konsep data science, analisis time series, dan web development, serta bertujuan untuk membantu pelaku usaha dalam pengambilan keputusan berbasis data.

##🎯 Fitur Utama : 
📝Login dan Manajemen Pengguna
📈 Upload data penjualan (Excel)
⚙️ Peramalan menggunakan algoritma Single Exponential Smoothing
📊 Visualisasi data historis dan hasil prediksi (Matplotlib)
🌐 Antarmuka web interaktif (Flask)
📤 Ekspor hasil prediksi ke file

## 🛠 Teknologi

- Python Flask
- MySQL
- Pandas & Matplotlib
- Bcrypt (password hashing)
- XHTML2PDF
- HTML + CSS

##🧠 Algoritma: Single Exponential Smoothing
SES adalah metode time series sederhana yang menggunakan parameter alpha (𝛼) untuk memberikan bobot lebih pada data terbaru. Cocok untuk pola data yang tidak memiliki tren atau musiman.
Rumus:
F(t+1)=α∗A(t)+(1−α)∗F(t)
𝛼 = smoothing constant (0 < 𝛼 < 1)
A(t) = actual value at time t
F(t) = forecast value at time t
