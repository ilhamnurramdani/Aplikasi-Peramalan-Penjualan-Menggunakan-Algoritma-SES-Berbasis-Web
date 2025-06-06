import pandas as pd
from flask import Flask, render_template, url_for, request, redirect, flash
from flask_mysqldb import MySQL
import os 
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from flask import make_response
from xhtml2pdf import pisa
from flask import session
from flask_bcrypt import Bcrypt
from functools import wraps

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'peramalan_ses'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'aman'

mysql = MySQL(app)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'id' not in session:
            flash('Harap login terlebih dahulu.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT id, username, password, hak_akses FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and bcrypt.check_password_hash(user[2], password):
            session['id'] = user[0]
            session['username'] = user[1]
            session['hak_akses'] = user[3]
            return redirect(url_for('index'))
        else:
            flash('Login gagal, periksa username atau password.', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Anda telah logout.', 'success')
    return redirect(url_for('login'))

@app.context_processor
def inject_user():
    return {
        'user': session.get('username', 'Guest'),
        'hak_akses': session.get('hak_akses', None)
    }


@app.route('/users')
@login_required
def users():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, hak_akses FROM users")
    users = cur.fetchall()
    cur.close()
    return render_template('users.html', users=users)

@app.route('/tambah_user', methods=['GET', 'POST'])
@login_required
def tambah_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hak_akses = request.form['hak_akses']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        try:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO users (username, password, hak_akses) VALUES (%s, %s, %s)", 
                        (username, hashed_password, hak_akses))
            mysql.connection.commit()
            cur.close()

            flash('User berhasil ditambahkan!', 'success')
            return redirect(url_for('users'))
        except Exception as e:
            flash(f'Gagal menambahkan user: {str(e)}', 'error')
            return redirect(url_for('tambah_user'))

    return render_template('tambah_user.html')

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, hak_akses FROM users WHERE id = %s", [user_id])
    user = cur.fetchone()
    cur.close()

    if not user:
        flash('User tidak ditemukan.', 'error')
        return redirect(url_for('manage_users'))

    if request.method == 'POST':
        username = request.form['username']
        hak_akses = request.form['hak_akses']
        password = request.form.get('password')  

        cur = mysql.connection.cursor()
        if password:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            cur.execute("UPDATE users SET username = %s, hak_akses = %s, password = %s WHERE id = %s", 
                        (username, hak_akses, hashed_password, user_id))
        else:
            cur.execute("UPDATE users SET username = %s, hak_akses = %s WHERE id = %s", 
                        (username, hak_akses, user_id))
        mysql.connection.commit()
        cur.close()

        flash('User berhasil diperbarui!', 'success')
        return redirect(url_for('users'))

    return render_template('edit_user.html', user=user)

@app.route('/hapus_user/<int:user_id>', methods=['POST', 'GET'])
@login_required
def hapus_user(user_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM users WHERE id = %s", [user_id])
    mysql.connection.commit()
    cur.close()

    flash('User berhasil dihapus!', 'success')
    return redirect(url_for('users'))

@app.route('/')
@login_required
def index():
    user = session.get('hak_akses', 'Guest')
    cur = mysql.connection.cursor()
    cur.execute("SELECT DISTINCT  count(name) FROM produk")
    total_produk = cur.fetchone()
    
    cur.execute("SELECT sum(quantity) as total FROM penjualan")
    total_penjualan = cur.fetchone()
    urutan_bulan = ['januari', 'februari', 'maret', 'april', 'mei', 'juni',
                        'juli', 'agustus', 'september', 'oktober', 'november', 'desember']
    cur.execute("SELECT LOWER(bulan) as bulan, tahun, quantity FROM penjualan")
    data = cur.fetchall()
    data = sorted(data, key=lambda x: (x[1], urutan_bulan.index(x[0])))
    penjualan = [int(row[2]) for row in data]  
    bulan_tahun = [f"{row[0].capitalize()} {row[1]}" for row in data]
    img = io.BytesIO()
    plt.figure(figsize=(15, 5.5))  
    plt.plot(bulan_tahun, penjualan, marker='o', color='blue', label='Data Aktual')
    for i, txt in enumerate(penjualan):
        plt.annotate(txt, (i, penjualan[i]), textcoords="offset points", xytext=(0, 5), ha='center', fontsize=8, color='blue')
    plt.title("Grafik Penjualan perbulan", fontsize=14)
    plt.xlabel("Waktu (Bulan dan Tahun)", fontsize=12)
    plt.ylabel("Jumlah Penjualan", fontsize=12)
    plt.grid(color='gray', linestyle='--', linewidth=0.5)
    plt.xticks( rotation=45)
    plt.legend(loc='upper left')
    plt.tight_layout()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return render_template('index.html' ,total_produk = total_produk[0], total_penjualan = total_penjualan[0], plot_url= plot_url, user=user)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.xlsx'):
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"{timestamp}_{file.filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
    
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO dataset (namafile) VALUES (%s)", [file.filename])
            mysql.connection.commit()
            id_dataset = cur.lastrowid

            df = pd.read_excel(filepath)
            group_sales = {}

            for _, row in df.iterrows():
                nama = row['Menu']
                quantity = row['Terjual']
                bulan = row['Bulan']
                tahun = row['Tahun']
                
          
                cur.execute("SELECT id FROM produk WHERE name = %s AND id_dataset = %s", (nama, id_dataset))
                produk = cur.fetchone()

                if not produk:
                    cur.execute("INSERT INTO produk(name, id_dataset) VALUES(%s, %s)", (nama, id_dataset))
                    mysql.connection.commit()
                    id_produk = cur.lastrowid
                else:
                    id_produk = produk[0]

              
                sales_key = (bulan, tahun)
                if sales_key not in group_sales:
                    group_sales[sales_key] = {
                        'produk': [],
                        'total_quantity': 0
                    }
                group_sales[sales_key]['produk'].append({'id_produk': id_produk, 'quantity': quantity})
                group_sales[sales_key]['total_quantity'] += quantity

          
            for (bulan, tahun), data in group_sales.items():
                cur.execute("INSERT INTO penjualan (bulan, tahun, quantity) VALUES (%s, %s, %s)", (bulan, tahun, data['total_quantity']))
                mysql.connection.commit()
                id_penjualan = cur.lastrowid

                for produk in data['produk']:
                    cur.execute("INSERT INTO detil_penjualan (id_penjualan, id_produk, quantity) VALUES (%s, %s, %s)", (id_penjualan, produk['id_produk'], produk['quantity']))
                    mysql.connection.commit()
            cur.close()
            flash('Data berhasil diupload', 'success')
            return redirect(url_for('upload'))
        else:
            flash('Upload gagal, pastikan file berformat .xlsx!', 'error')
            return redirect(url_for('upload'))

    return render_template('upload.html')

@app.route('/produk')
@login_required
def produk():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM produk")
    mysql.connection.commit()
    produk = cur.fetchall()
    return render_template('produk.html', products = produk)

@app.route('/tambah_produk', methods=['POST', 'GET'])
@login_required
def tambah_produk():
    if request.method == 'POST' :
        try :
            nama = request.form['name']
            
            cur = mysql.connection.cursor()
            cur.execute("SELECT id FROM dataset ORDER BY tanggal_upload DESC LIMIT 1")
            dataset = cur.fetchone()
            
            if not dataset :
                cur.execute("INSERT INTO dataset (namafile) VALUES (%s)", ['DEFAULT_DATASET'])
                mysql.connection.commit()
                id_dataset = cur.lastrowid
            else :
                id_dataset = dataset[0]
            
            cur.execute("INSERT INTO produk (name, id_dataset) VALUES (%s, %s)", (nama, id_dataset))
            mysql.connection.commit()
            cur.close()
            flash('Data Berhasil Di input', 'success')  
            return redirect(url_for('produk'))
        
        except :
            flash('Data Gagal Di input', 'error')        
            return redirect(url_for('produk'))
        
    return render_template('tambah_produk.html')

@app.route('/edit_produk/<int:id>', methods=['POST', 'GET'])
@login_required
def edit_produk(id):
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        try :
            nama = request.form['name']
            cur.execute("UPDATE produk SET name= %s WHERE id = %s", (nama, id))
            mysql.connection.commit()
            flash('Data Berhasil di ubah', 'success')
            return redirect(url_for('produk'))
        except :
            flash('Data Gagal Di ubah', 'error')        
            return redirect(url_for('produk'))
    else :
        cur.execute("SELECT id, name FROM produk WHERE id = %s", [id])
        produk = cur.fetchone()
        cur.close()
        return render_template('edit_produk.html', produk=produk)
    
@app.route('/hapus_produk/<int:id>', methods=['GET'])
@login_required
def hapus_produk(id) :
    try : 
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM produk WHERE id = %s", [id])
        mysql.connection.commit()
        cur.close()
        flash('Data Berhasil di hapus', 'success')
        return redirect(url_for('produk'))
    except : 
        flash('Data Gagal Di hapus', 'error')        
        return redirect(url_for('produk'))
    
@app.route('/penjualan')
@login_required
def penjualan():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM penjualan")
    penjualan = cur.fetchall()
    cur.close()
    return render_template('penjualan.html', penjualans=penjualan)

@app.route('/tambah_penjualan', methods=['POST', 'GET'])
@login_required
def tambah_penjualan():
    if request.method == "POST" :
        try :
            bulan = request.form['bulan']
            tahun = request.form['tahun']
            total_quantity = 0
            
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO penjualan(bulan, tahun, quantity) VALUES(%s, %s, %s)", (bulan, tahun, total_quantity))
            mysql.connection.commit()
            id_penjualan = cur.lastrowid
            
            produk_quantities = request.form.getlist('produk_quantity')
            for produk_quantity in produk_quantities :
                id_produk, quantity = produk_quantity.split(":")
                quantity = int(quantity)
                total_quantity += quantity
                cur.execute("INSERT INTO detil_penjualan(id_penjualan, id_produk, quantity) VALUES (%s, %s, %s)", (id_penjualan, id_produk, quantity))
            
            cur.execute("UPDATE penjualan SET quantity = %s WHERE id = %s", (total_quantity, id_penjualan))
            mysql.connection.commit()
            cur.close()
            flash('Data Berhasil di tambah', 'success')
            return redirect(url_for('penjualan'))
        except Exception as e:
            flash(f'Data gagal di tambah: {str(e)}', 'error')
            return redirect(url_for('penjualan'))
    else:    
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM produk")
        produk = cur.fetchall()
        return render_template('tambah_penjualan.html', produks=produk)

@app.route('/edit_penjualan/<int:id>', methods= ['POST', 'GET'])
@login_required
def edit_penjualan(id):
    cur = mysql.connection.cursor()
    if request.method == "POST" :
        try :
            bulan = request.form['bulan']
            tahun = request.form['tahun']
            
            cur.execute("UPDATE penjualan SET bulan =%s, tahun = %s WHERE id = %s", (bulan, tahun, id))
            mysql.connection.commit()
            
            cur.execute("DELETE FROM detil_penjualan WHERE id_penjualan = %s", [id])
            produk_quantities = request.form.getlist('produk_quantity')
            total_quantity = 0
            for produk_quantity in produk_quantities :
                id_produk, quantity = produk_quantity.split(":")
                quantity = int(quantity)
                total_quantity += quantity
                cur.execute("INSERT INTO detil_penjualan(id_penjualan, id_produk, quantity) VALUES (%s, %s, %s)", (id, id_produk, quantity))
            
            cur.execute("UPDATE penjualan SET quantity = %s WHERE id = %s", (total_quantity, id))
            mysql.connection.commit()
            cur.close()
            flash('Data Berhasil di tambah', 'success')
            return redirect(url_for('penjualan'))
        except Exception as e:
            flash(f'Data gagal di tambah: {str(e)}', 'error')
            return redirect(url_for('penjualan'))
        
    
    cur.execute("SELECT bulan, tahun, quantity FROM penjualan WHERE id = %s", [id])
    info_penjualan = cur.fetchone()
    
    cur.execute("SELECT p.id, p.name, dp.quantity FROM produk p JOIN detil_penjualan dp ON p.id = dp.id_produk WHERE id_penjualan = %s", [id])
    details_penjualan = cur.fetchall()
    
    detail_produk = {produk[0] : produk[2] for produk in details_penjualan}
    
    cur.execute("SELECT * FROM produk")
    produks = cur.fetchall()
    cur.close()
    return render_template('edit_penjualan.html', id_penjualan = id,  info_penjualan = info_penjualan, detail_produk = detail_produk, produks = produks)
    
@app.route('/hapus_penjualan/<int:id>', methods=['POST', 'GET'])
@login_required
def hapus_penjualan(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM detil_penjualan WHERE id_penjualan = %s", [id])
    mysql.connection.commit()
    
    cur.execute("DELETE FROM penjualan WHERE id = %s", [id])
    mysql.connection.commit()
    flash('Data Berhasil di hapus', 'success')
    return redirect(url_for('penjualan'))

@app.route('/detil_penjualan/<int:id>')
@login_required
def detil_penjualan(id):
    cur = mysql.connection.cursor()
    
    cur.execute("SELECT bulan, tahun, quantity FROM penjualan WHERE id = %s", [id])
    info_penjualan = cur.fetchone()
    
    cur.execute("SELECT p.name, dp.quantity FROM produk p JOIN detil_penjualan dp ON p.id = dp.id_produk WHERE dp.id_penjualan = %s", [id])
    detail_produk = cur.fetchall()
    
    cur.close()
    
    return render_template('detil_penjualan.html', info_penjualan=info_penjualan, detail_produk=detail_produk)

@app.route('/hasil_peramalan_produk', methods=['GET', 'POST'])
@login_required
def hasil_peramalan_produk():
    alpha = 0.5 
    if request.method == 'POST':
        alpha = float(request.form['alpha'])
        id_produk = request.form['id_produk']

      
    urutan_bulan = ['januari', 'februari', 'maret', 'april', 'mei', 'juni',
                    'juli', 'agustus', 'september', 'oktober', 'november', 'desember']

   
    cur = mysql.connection.cursor()
    cur.execute("""SELECT dp.quantity, LOWER(p.bulan) AS bulan, p.tahun
                FROM penjualan p
                JOIN detil_penjualan dp ON p.id = dp.id_penjualan
                WHERE id_produk = %s
                ORDER BY p.tahun""", [id_produk]) 
    data = cur.fetchall()
    data = sorted(data, key=lambda x: (x[2], urutan_bulan.index(x[1])))

    penjualan = [row[0] for row in data]  
    bulan_tahun = [f"{row[1].capitalize()} {row[2]}" for row in data] 


    if len(penjualan) < 2:
        return "Data tidak cukup untuk peramalan."

    peramalan = [penjualan[0]]
    for i in range(1, len(penjualan)):
        next_value = alpha * penjualan[i - 1] + (1 - alpha) * peramalan[i - 1]
        peramalan.append(round(next_value, 2))
        

    

    peramalan_selanjutnya = alpha * penjualan[-1] + (1 - alpha) * peramalan[-1]
    peramalan_selanjutnya = round(peramalan_selanjutnya)
    
    combine_data = []
    for bulan, actual_value, forecast_value in zip(bulan_tahun,penjualan, peramalan):
        if actual_value != 0:
            mape = abs(actual_value - forecast_value) / actual_value * 100
        else:
            mape = 0 
        combine_data.append({
            'bulan' : bulan,
            'actual': actual_value,
            'forecast': forecast_value,
            'mape': round(mape) 
        })
    
    

    actual = penjualan  
    mad = sum(abs(a - f) for a, f in zip(actual, peramalan)) / len(actual) 
    round_mad = round(mad)
    mse = sum((a - f) ** 2 for a, f in zip(actual, peramalan)) / len(actual) 
    round_mse = round(mse)
    mape = sum(abs(a - f) / a for a, f in zip(actual, peramalan) if a != 0) / len(actual) * 100 
    round_mape = round(mape)
    

    last_bulan, last_tahun = bulan_tahun[-1].split() 
    last_index = urutan_bulan.index(last_bulan.lower())  

    if last_index == 11:
        next_bulan = urutan_bulan[0] 
        next_tahun = int(last_tahun) + 1  
    else:
        next_bulan = urutan_bulan[last_index + 1]  
        next_tahun = int(last_tahun) 

    cur.execute("INSERT INTO peramalan_produk (id_produk, alpha, bulan, tahun,  peramalan, error) VALUES (%s, %s, %s, %s, %s, %s)",
                (id_produk, alpha, next_bulan, next_tahun, peramalan_selanjutnya, round_mape))
    mysql.connection.commit()
    cur.close()
    
    img = io.BytesIO()
    plt.figure(figsize=(10, 6)) 
    plt.plot(bulan_tahun, penjualan, marker='o', color='blue', label='Data Aktual')
    plt.plot(bulan_tahun, peramalan, marker='x', linestyle='--', color='orange', label='Peramalan')
    plt.scatter(len(bulan_tahun), peramalan_selanjutnya, color='red', marker='o', label=f'Prediksi Selanjutnya: {peramalan_selanjutnya}')
    plt.annotate(f"{peramalan_selanjutnya}", 
             (len(bulan_tahun), peramalan_selanjutnya), 
             textcoords="offset points", xytext=(0, 10), ha='center', fontsize=10, color='red')
    for i, txt in enumerate(penjualan):
        plt.annotate(txt, (i, penjualan[i]), textcoords="offset points", xytext=(0, 5), ha='center', fontsize=8, color='blue')
    for i, txt in enumerate(peramalan):
        plt.annotate(txt, (i, peramalan[i]), textcoords="offset points", xytext=(0, -10), ha='center', fontsize=8, color='orange')
    plt.title("Grafik Peramalan Penjualan dengan Single Exponential Smoothing", fontsize=14)
    plt.xlabel("Waktu (Bulan dan Tahun)", fontsize=12)
    plt.ylabel("Jumlah Penjualan", fontsize=12)
    plt.grid(color='gray', linestyle='--', linewidth=0.5)
    plt.xticks(range(len(bulan_tahun) + 1) , bulan_tahun + ['prediksi'],  rotation=45)
    plt.legend(loc='upper left')
    plt.tight_layout()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()


    return render_template('hasil_peramalan_produk.html', penjualan=penjualan, peramalan=peramalan, peramalan_selanjutnya=peramalan_selanjutnya, alpha=alpha, mad=round_mad, mse=round_mse, mape=round_mape, plot_url=plot_url, combine_data=combine_data)
    
@app.route('/tambah_peramalan_produk')
@login_required
def tambah_peramalan_produk():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name FROM produk")
    produks = cur.fetchall()
    cur.close()
    return render_template('tambah_peramalan_produk.html', produks = produks)

@app.route('/peramalan_produk')
@login_required
def peramalan_produk():
    cur = mysql.connection.cursor()
    cur.execute("SELECT pr.id, p.name, pr.alpha, pr.bulan, pr.tahun, pr.peramalan, pr.tanggal_peramalan, pr.error  FROM produk p JOIN peramalan_produk pr ON p.id = pr.id_produk")
    peramalans = cur.fetchall()
    return render_template('peramalan_produk.html', peramalans = peramalans)


@app.route('/hapus_peramalan_produk/<int:id>', methods=['POST', 'GET'])
@login_required
def hapus_peramalan_produk(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM peramalan_produk WHERE id = %s", [id])
    mysql.connection.commit()
    flash('Data Berhasil di hapus', 'success')
    return redirect(url_for('peramalan_produk'))

@app.route('/peramalan_penjualan')
@login_required
def peramalan_penjualan():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM peramalan_penjualan")
    peramalans = cur.fetchall()
    
    return render_template('peramalan_penjualan.html', peramalans = peramalans)

@app.route('/tambah_peramalan_penjualan')
@login_required
def tambah_peramalan_penjualan():
    
    return render_template('tambah_peramalan_penjualan.html')

@app.route('/hasil_peramalan_penjualan', methods=['POST', 'GET'])
@login_required
def hasil_peramalan_penjualan():
    alpha = 0.5
    if request.method == "POST":
        alpha = float(request.form['alpha'])  
        cur = mysql.connection.cursor()
        urutan_bulan = ['januari', 'februari', 'maret', 'april', 'mei', 'juni',
                        'juli', 'agustus', 'september', 'oktober', 'november', 'desember']
        cur.execute("SELECT LOWER(bulan) as bulan, tahun, quantity FROM penjualan")
        data = cur.fetchall()
        if not data:
            return "Tidak ada data untuk peramalan."

        data = sorted(data, key=lambda x: (x[1], urutan_bulan.index(x[0])))

        penjualan = [int(row[2]) for row in data]  
        bulan_tahun = [f"{row[0].capitalize()} {row[1]}" for row in data]

        if len(penjualan) < 2:
            return "Data tidak cukup untuk peramalan."

        peramalan = [penjualan[0]]
        for i in range(1, len(penjualan)):
            next_value = alpha * penjualan[i - 1] + (1 - alpha) * peramalan[i - 1]
            peramalan.append(round(next_value))

        peramalan_selanjutnya = alpha * penjualan[-1] + (1 - alpha) * peramalan[-1]
        peramalan_selanjutnya = round(peramalan_selanjutnya)

        combine_data = []
        for bulan, actual, forecast in zip(bulan_tahun, penjualan, peramalan):
            if actual != 0:
                mape = round(abs(actual - forecast) / actual * 100)
            else:
                mape = 0
            combine_data.append({'bulan': bulan, 'actual': actual, 'peramalan': forecast, 'mape': round(mape, 2)})

        mape = sum(abs(a - f) / a for a, f in zip(penjualan, peramalan) if a != 0) / len(penjualan) * 100
        round_mape = round(mape)
        last_bulan, last_tahun = bulan_tahun[-1].split()
        last_index = urutan_bulan.index(last_bulan.lower()) 

        if last_index == 11:  
            next_bulan = urutan_bulan[0]  
            next_tahun = int(last_tahun) + 1  
        else:
            next_bulan = urutan_bulan[last_index + 1] 
            next_tahun = int(last_tahun) 

      
        cur.execute("INSERT INTO peramalan_penjualan (alpha,bulan, tahun,  peramalan, error) VALUES(%s,%s,%s,%s,%s)", [alpha,next_bulan, next_tahun, peramalan_selanjutnya, round_mape])
        mysql.connection.commit()
        cur.close()
        
        img = io.BytesIO()
        plt.figure(figsize=(10, 6)) 
        plt.plot(bulan_tahun, penjualan, marker='o', color='blue', label='Data Aktual')
        plt.plot(bulan_tahun, peramalan, marker='x', linestyle='--', color='orange', label='Peramalan')
        plt.scatter(len(bulan_tahun), peramalan_selanjutnya, color='red', marker='o', label=f'Prediksi Selanjutnya: {peramalan_selanjutnya}')
        plt.annotate(f"{peramalan_selanjutnya}", 
                (len(bulan_tahun), peramalan_selanjutnya), 
                textcoords="offset points", xytext=(0, 10), ha='center', fontsize=10, color='red')
        for i, txt in enumerate(penjualan):
            plt.annotate(txt, (i, penjualan[i]), textcoords="offset points", xytext=(0, 5), ha='center', fontsize=8, color='blue')
        for i, txt in enumerate(peramalan):
            plt.annotate(txt, (i, peramalan[i]), textcoords="offset points", xytext=(0, -10), ha='center', fontsize=8, color='orange')
        plt.title("Grafik Peramalan Penjualan dengan Single Exponential Smoothing", fontsize=14)
        plt.xlabel("Waktu (Bulan dan Tahun)", fontsize=12)
        plt.ylabel("Jumlah Penjualan", fontsize=12)
        plt.grid(color='gray', linestyle='--', linewidth=0.5)
        plt.xticks(range(len(bulan_tahun) + 1) , bulan_tahun + ['prediksi'],  rotation=45)
        plt.legend(loc='upper left')
        plt.tight_layout()
        plt.savefig(img, format='png')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close()
    return render_template(
            'hasil_peramalan_penjualan.html',
            penjualan=penjualan,
            peramalan=peramalan,
            peramalan_selanjutnya=peramalan_selanjutnya,
            alpha=alpha,
            mape=round_mape,
            combine_data=combine_data,
            plot_url = plot_url
        )

@app.route('/hapus_peramalan_penjualan/<int:id>', methods=['POST', 'GET'])
@login_required
def hapus_peramalan_penjualan(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM peramalan_penjualan WHERE id=%s", [id])
    mysql.connection.commit()
    cur.close()
    flash('Data Berhasil di hapus', 'success')
    return redirect(url_for('peramalan_penjualan'))  

@app.route('/tambah_laporan')
@login_required
def tambah_laporan():
    return render_template('tambah_laporan.html')

@app.route('/laporan_pdf', methods=['POST'])
@login_required
def laporan_pdf():
    if request.method == 'POST':
        bulan = request.form['bulan'].lower() 
        tahun = int(request.form['tahun']) 

        cur = mysql.connection.cursor()

        cur.execute("""
            SELECT prod.name, per.alpha, per.bulan, per.tahun, per.peramalan, per.error
            FROM peramalan_produk per
            JOIN produk prod ON per.id_produk = prod.id
            WHERE per.bulan = %s AND per.tahun = %s
        """, (bulan, tahun))
        laporan_produk = cur.fetchall()

        cur.execute("""
            SELECT alpha, bulan, tahun, peramalan, error
            FROM peramalan_penjualan 
            WHERE bulan = %s AND tahun = %s
        """, (bulan, tahun))
        laporan_penjualan = cur.fetchall()

        cur.close()
        rendered_html = render_template(
            'laporan_pdf.html',
            laporan_produk=laporan_produk,
            laporan_penjualan=laporan_penjualan,
            bulan=bulan.capitalize(),
            tahun=tahun
        )

        pdf = io.BytesIO()
        pisa_status = pisa.CreatePDF(io.StringIO(rendered_html), dest=pdf)
        pdf.seek(0)

        if pisa_status.err:
            return "Error saat menghasilkan PDF"

        response = make_response(pdf.read())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=laporan_{bulan}_{tahun}.pdf'
        return response
        
if __name__ == '__main__' : 
    app.run(debug=True)
    