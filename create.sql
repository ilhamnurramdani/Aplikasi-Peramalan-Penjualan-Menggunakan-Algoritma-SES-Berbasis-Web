CREATE DATABASE peramalan_ses;

USE peramalan_ses;

CREATE OR REPLACE TABLE dataset (
    id INT AUTO_INCREMENT PRIMARY KEY,
    namafile VARCHAR(255),
    tanggal_upload DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE OR REPLACE TABLE produk (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    id_dataset INT,
    FOREIGN KEY (id_dataset) REFERENCES dataset(id)
);

CREATE TABLE penjualan (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bulan VARCHAR(50) NOT NULL,
    tahun INT NOT NULL,
    quantity INT NOT NULL
);

CREATE TABLE detil_penjualan (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_penjualan INT NOT NULL,
    id_produk INT NOT NULL,
    quantity INT NOT NULL,
    FOREIGN KEY (id_penjualan) REFERENCES penjualan(id) ON DELETE CASCADE,
    FOREIGN KEY (id_produk) REFERENCES produk(id) ON DELETE CASCADE
);

CREATE OR REPLACE TABLE peramalan_produk(
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_produk INT,
    alpha FLOAT,
    bulan VARCHAR(20),
    tahun INT,
    peramalan INT,
    tanggal_peramalan DATETIME DEFAULT CURRENT_TIMESTAMP,
    error VARCHAR(100),
    FOREIGN KEY (id_produk) REFERENCES produk(id)
);

CREATE OR REPLACE TABLE peramalan_penjualan(
    id INT AUTO_INCREMENT PRIMARY KEY,
    alpha FLOAT,
    bulan VARCHAR(20),
    tahun INT,
    peramalan INT,
    tanggal_peramalan DATETIME DEFAULT CURRENT_TIMESTAMP,
    error VARCHAR(100)
);

CREATE OR REPLACE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    hak_akses VARCHAR(255) NOT NULL
);