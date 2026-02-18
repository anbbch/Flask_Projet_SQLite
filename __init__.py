from flask import Flask, render_template_string, render_template, jsonify, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# =========================
#   DB PATH (AlwaysData)
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# =========================
#   SESSION / ROLES
# =========================
def current_user():
    # {"id": 2, "username": "user", "role": "user"}
    return session.get("user")

def is_user():
    u = current_user()
    return u is not None and u.get("role") in ("user", "admin")

def is_admin():
    u = current_user()
    return u is not None and u.get("role") == "admin"

def get_user_id():
    u = current_user()
    return u["id"] if u else None

# =========================
#   HOME (accessible)
# =========================
@app.route('/')
def hello_world():
    return render_template('hello.html', user=current_user())

# =========================
#   AUTH (user + admin)
# =========================
@app.route('/authentification', methods=['GET', 'POST'])
def authentification():
    if request.method == 'POST':
        username = (request.form.get('username') or "").strip()
        password = (request.form.get('password') or "").strip()

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, role FROM utilisateurs WHERE username=? AND password=?",
            (username, password)
        )
        u = cur.fetchone()
        conn.close()

        if u:
            session["user"] = {"id": u["id"], "username": u["username"], "role": u["role"]}
            return redirect(url_for("hello_world"))

        return render_template('formulaire_authentification.html', error=True)

    return render_template('formulaire_authentification.html', error=False)

@app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect(url_for("hello_world"))

# =========================
#   PAGE LIVRES (HTML)
# =========================
@app.route('/livres')
def livres_page():
    q = (request.args.get("q") or "").strip()

    conn = get_db()
    cur = conn.cursor()

    if q:
        cur.execute("""
            SELECT * FROM livres
            WHERE stock_disponible > 0
            AND (titre LIKE ? OR auteur LIKE ? OR isbn LIKE ?)
            ORDER BY titre
        """, (f"%{q}%", f"%{q}%", f"%{q}%"))
    else:
        cur.execute("SELECT * FROM livres WHERE stock_disponible > 0 ORDER BY titre")

    livres = cur.fetchall()
    conn.close()
    return render_template("livres.html", livres=livres, user=current_user(), q=q)



# =========================
#   PAGE ADMIN : USERS
# =========================
@app.route('/admin/users', methods=['GET'])
def admin_users_page():
    if not is_admin():
        return redirect(url_for("authentification"))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, username, role FROM utilisateurs ORDER BY id DESC")
    users = cur.fetchall()
    conn.close()

    return render_template("admin_users.html", users=users, user=current_user())


@app.route('/admin/users/ajouter', methods=['POST'])
def admin_users_add_page():
    if not is_admin():
        return redirect(url_for("authentification"))

    username = (request.form.get("username") or "").strip()
    password = (request.form.get("password") or "").strip()
    role = (request.form.get("role") or "").strip()

    if not username or not password or role not in ("admin", "user"):
        return redirect(url_for("admin_users_page"))

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO utilisateurs (username, password, role) VALUES (?, ?, ?)",
                    (username, password, role))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

    return redirect(url_for("admin_users_page"))


# =========================
#   ACTIONS BIBLIOTHEQUE (HTML -> DB)
# =========================
@app.route('/admin/livres/ajouter', methods=['POST'])
def admin_livre_add_form():
    if not is_admin():
        return redirect(url_for("authentification"))

    titre = (request.form.get("titre") or "").strip()
    auteur = (request.form.get("auteur") or "").strip()
    isbn = (request.form.get("isbn") or "").strip() or None
    stock_total = int(request.form.get("stock_total") or 1)

    if not titre or not auteur or stock_total < 0:
        return redirect(url_for("livres_page"))

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO livres (titre, auteur, isbn, stock_total, stock_disponible)
            VALUES (?, ?, ?, ?, ?)
        """, (titre, auteur, isbn, stock_total, stock_total))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

    return redirect(url_for("livres_page"))


@app.route('/admin/livres/stock/<int:livre_id>', methods=['POST'])
def admin_livre_update_stock_form(livre_id):
    if not is_admin():
        return redirect(url_for("authentification"))

    new_total = request.form.get("stock_total")
    if new_total is None:
        return redirect(url_for("livres_page"))

    new_total = int(new_total)
    if new_total < 0:
        return redirect(url_for("livres_page"))

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT stock_total, stock_disponible FROM livres WHERE id=?", (livre_id,))
    livre = cur.fetchone()
    if not livre:
        conn.close()
        return redirect(url_for("livres_page"))

    borrowed = livre["stock_total"] - livre["stock_disponible"]
    if new_total < borrowed:
        conn.close()
        return redirect(url_for("livres_page"))

    new_dispo = new_total - borrowed
    cur.execute("UPDATE livres SET stock_total=?, stock_disponible=? WHERE id=?",
                (new_total, new_dispo, livre_id))
    conn.commit()
    conn.close()

    return redirect(url_for("livres_page"))


@app.route('/admin/livres/supprimer/<int:livre_id>', methods=['POST'])
def admin_livre_delete_form(livre_id):
    if not is_admin():
        return redirect(url_for("authentification"))

    conn = get_db()
    cur = conn.cursor()

    # Bloque suppression si emprunt en cours
    cur.execute("SELECT COUNT(*) FROM emprunts WHERE livre_id=? AND statut='EN_COURS'", (livre_id,))
    if cur.fetchone()[0] > 0:
        conn.close()
        return redirect(url_for("livres_page"))

    cur.execute("DELETE FROM livres WHERE id=?", (livre_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("livres_page"))


@app.route('/livres/emprunter/<int:livre_id>', methods=['POST'])
def emprunter_livre_form(livre_id):
    if not is_user():
        return redirect(url_for("authentification"))

    user_id = get_user_id()

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT stock_disponible FROM livres WHERE id=?", (livre_id,))
    livre = cur.fetchone()
    if not livre or livre["stock_disponible"] <= 0:
        conn.close()
        return redirect(url_for("livres_page"))

    cur.execute("UPDATE livres SET stock_disponible = stock_disponible - 1 WHERE id=?", (livre_id,))
    cur.execute("""
        INSERT INTO emprunts (utilisateur_id, livre_id, statut)
        VALUES (?, ?, 'EN_COURS')
    """, (user_id, livre_id))
    conn.commit()
    conn.close()

    return redirect(url_for("livres_page"))


@app.route('/mes-emprunts', methods=['GET'])
def mes_emprunts_page():
    if not is_user():
        return redirect(url_for("authentification"))

    user_id = get_user_id()

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT e.id AS emprunt_id, e.statut, e.date_emprunt,
               l.titre, l.auteur, l.isbn
        FROM emprunts e
        JOIN livres l ON l.id = e.livre_id
        WHERE e.utilisateur_id=?
        ORDER BY e.id DESC
    """, (user_id,))
    emprunts = cur.fetchall()
    conn.close()

    return render_template("emprunts.html", emprunts=emprunts, user=current_user())


@app.route('/mes-emprunts/retour/<int:emprunt_id>', methods=['POST'])
def retour_emprunt_form(emprunt_id):
    if not is_user():
        return redirect(url_for("authentification"))

    user_id = get_user_id()

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT livre_id FROM emprunts
        WHERE id=? AND utilisateur_id=? AND statut='EN_COURS'
    """, (emprunt_id, user_id))
    emp = cur.fetchone()
    if not emp:
        conn.close()
        return redirect(url_for("mes_emprunts_page"))

    cur.execute("""
        UPDATE emprunts
        SET statut='RETOURNE', date_retour_effective=CURRENT_TIMESTAMP
        WHERE id=?
    """, (emprunt_id,))
    cur.execute("UPDATE livres SET stock_disponible = stock_disponible + 1 WHERE id=?",
                (emp["livre_id"],))
    conn.commit()
    conn.close()

    return redirect(url_for("mes_emprunts_page"))


# =========================================================
#               API BIBLIOTHEQUE (inchangée)
# =========================================================

@app.route('/api/livres', methods=['GET'])
def api_livres():
    q = request.args.get('q', '').strip()

    conn = get_db()
    cur = conn.cursor()

    if q:
        cur.execute("""
            SELECT * FROM livres
            WHERE titre LIKE ? OR auteur LIKE ? OR isbn LIKE ?
            ORDER BY titre
        """, (f"%{q}%", f"%{q}%", f"%{q}%"))
    else:
        cur.execute("SELECT * FROM livres ORDER BY titre")

    data = cur.fetchall()
    conn.close()
    return jsonify([dict(r) for r in data])

@app.route('/api/livres_disponibles', methods=['GET'])
def api_livres_disponibles():
    q = request.args.get('q', '').strip()

    conn = get_db()
    cur = conn.cursor()

    if q:
        cur.execute("""
            SELECT * FROM livres
            WHERE stock_disponible > 0
            AND (titre LIKE ? OR auteur LIKE ? OR isbn LIKE ?)
            ORDER BY titre
        """, (f"%{q}%", f"%{q}%", f"%{q}%"))
    else:
        cur.execute("SELECT * FROM livres WHERE stock_disponible > 0 ORDER BY titre")

    data = cur.fetchall()
    conn.close()
    return jsonify([dict(r) for r in data])

# ===== ADMIN : ajouter un livre
@app.route('/api/admin/ajouter_livre', methods=['POST'])
def api_admin_ajouter_livre():
    if not is_admin():
        return jsonify({"error": "admin_required"}), 401

    data = request.get_json(silent=True) or {}
    titre = (data.get("titre") or "").strip()
    auteur = (data.get("auteur") or "").strip()
    isbn = (data.get("isbn") or "").strip() or None
    stock_total = int(data.get("stock_total") or 1)

    if not titre or not auteur or stock_total < 0:
        return jsonify({"error": "invalid_payload"}), 400

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO livres (titre, auteur, isbn, stock_total, stock_disponible)
            VALUES (?, ?, ?, ?, ?)
        """, (titre, auteur, isbn, stock_total, stock_total))
        conn.commit()
        new_id = cur.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "isbn_exists"}), 409

    conn.close()
    return jsonify({"message": "livre_ajoute", "id": new_id})

# ===== ADMIN : supprimer livre
@app.route('/api/admin/supprimer_livre/<int:livre_id>', methods=['DELETE'])
def api_admin_supprimer_livre(livre_id):
    if not is_admin():
        return jsonify({"error": "admin_required"}), 401

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM emprunts WHERE livre_id=? AND statut='EN_COURS'", (livre_id,))
    if cur.fetchone()[0] > 0:
        conn.close()
        return jsonify({"error": "emprunt_en_cours"}), 409

    cur.execute("DELETE FROM livres WHERE id=?", (livre_id,))
    conn.commit()
    deleted = cur.rowcount
    conn.close()

    if deleted == 0:
        return jsonify({"error": "not_found"}), 404
    return jsonify({"message": "livre_supprime"})

# ===== ADMIN : stock
@app.route('/api/admin/stock/<int:livre_id>', methods=['PATCH'])
def api_admin_stock(livre_id):
    if not is_admin():
        return jsonify({"error": "admin_required"}), 401

    data = request.get_json(silent=True) or {}
    new_total = data.get("stock_total")
    if new_total is None:
        return jsonify({"error": "missing_stock_total"}), 400

    new_total = int(new_total)
    if new_total < 0:
        return jsonify({"error": "invalid_stock_total"}), 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT stock_total, stock_disponible FROM livres WHERE id=?", (livre_id,))
    livre = cur.fetchone()
    if not livre:
        conn.close()
        return jsonify({"error": "not_found"}), 404

    borrowed = livre["stock_total"] - livre["stock_disponible"]
    if new_total < borrowed:
        conn.close()
        return jsonify({"error": "stock_too_low", "borrowed": borrowed}), 409

    new_dispo = new_total - borrowed
    cur.execute("UPDATE livres SET stock_total=?, stock_disponible=? WHERE id=?",
                (new_total, new_dispo, livre_id))
    conn.commit()
    conn.close()

    return jsonify({"message": "stock_ok", "stock_total": new_total, "stock_disponible": new_dispo})

# ===== USER : emprunter
@app.route('/api/user/emprunter', methods=['POST'])
def api_user_emprunter():
    if not is_user():
        return jsonify({"error": "login_required"}), 401

    user_id = get_user_id()
    data = request.get_json(silent=True) or {}
    livre_id = data.get("livre_id")
    if not livre_id:
        return jsonify({"error": "missing_livre_id"}), 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT stock_disponible FROM livres WHERE id=?", (livre_id,))
    livre = cur.fetchone()
    if not livre:
        conn.close()
        return jsonify({"error": "book_not_found"}), 404
    if livre["stock_disponible"] <= 0:
        conn.close()
        return jsonify({"error": "no_stock"}), 409

    cur.execute("UPDATE livres SET stock_disponible = stock_disponible - 1 WHERE id=?", (livre_id,))
    cur.execute("""
        INSERT INTO emprunts (utilisateur_id, livre_id, statut)
        VALUES (?, ?, 'EN_COURS')
    """, (user_id, livre_id))

    conn.commit()
    emprunt_id = cur.lastrowid
    conn.close()

    return jsonify({"message": "emprunt_ok", "emprunt_id": emprunt_id})

# ===== USER : retour
@app.route('/api/user/retour/<int:emprunt_id>', methods=['POST'])
def api_user_retour(emprunt_id):
    if not is_user():
        return jsonify({"error": "login_required"}), 401

    user_id = get_user_id()

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT livre_id FROM emprunts
        WHERE id=? AND utilisateur_id=? AND statut='EN_COURS'
    """, (emprunt_id, user_id))
    emp = cur.fetchone()

    if not emp:
        conn.close()
        return jsonify({"error": "emprunt_not_found"}), 404

    cur.execute("""
        UPDATE emprunts
        SET statut='RETOURNE', date_retour_effective=CURRENT_TIMESTAMP
        WHERE id=?
    """, (emprunt_id,))
    cur.execute("UPDATE livres SET stock_disponible = stock_disponible + 1 WHERE id=?",
                (emp["livre_id"],))

    conn.commit()
    conn.close()

    return jsonify({"message": "retour_ok"})

# ===== ADMIN : users
@app.route('/api/admin/users', methods=['GET'])
def api_admin_users():
    if not is_admin():
        return jsonify({"error": "admin_required"}), 401

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, username, role FROM utilisateurs ORDER BY id DESC")
    data = cur.fetchall()
    conn.close()
    return jsonify([dict(r) for r in data])

@app.route('/api/admin/users', methods=['POST'])
def api_admin_add_user():
    if not is_admin():
        return jsonify({"error": "admin_required"}), 401

    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()
    role = (data.get("role") or "").strip()

    if not username or not password or role not in ("admin", "user"):
        return jsonify({"error": "invalid_payload"}), 400

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO utilisateurs (username, password, role) VALUES (?, ?, ?)",
                    (username, password, role))
        conn.commit()
        new_id = cur.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "username_exists"}), 409

    conn.close()
    return jsonify({"message": "user_added", "id": new_id})

# =========================================================
#               MINI GESTIONNAIRE DE TÂCHES
# =========================================================

@app.route('/taches', methods=['GET'])
def page_taches():
    if not is_user():
        return redirect(url_for("authentification"))

    user_id = get_user_id()

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM taches
        WHERE utilisateur_id=?
        ORDER BY terminee ASC, date_echeance IS NULL, date_echeance ASC, id DESC
    """, (user_id,))
    taches = cur.fetchall()
    conn.close()

    return render_template('taches.html', taches=taches, user=current_user())

@app.route('/taches/ajouter', methods=['POST'])
def ajouter_tache():
    if not is_user():
        return redirect(url_for("authentification"))

    user_id = get_user_id()

    titre = (request.form.get('titre') or "").strip()
    description = (request.form.get('description') or "").strip()
    date_echeance = (request.form.get('date_echeance') or "").strip() or None

    if titre == "" or description == "":
        return redirect('/taches')

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO taches (utilisateur_id, titre, description, date_echeance, terminee) VALUES (?, ?, ?, ?, 0)",
        (user_id, titre, description, date_echeance)
    )
    conn.commit()
    conn.close()

    return redirect('/taches')

@app.route('/taches/supprimer/<int:tache_id>', methods=['POST'])
def supprimer_tache(tache_id):
    if not is_user():
        return redirect(url_for("authentification"))

    user_id = get_user_id()

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM taches WHERE id=? AND utilisateur_id=?", (tache_id, user_id))
    conn.commit()
    conn.close()

    return redirect('/taches')

@app.route('/taches/terminer/<int:tache_id>', methods=['POST'])
def toggle_terminee(tache_id):
    if not is_user():
        return redirect(url_for("authentification"))

    user_id = get_user_id()

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT terminee FROM taches WHERE id=? AND utilisateur_id=?", (tache_id, user_id))
    row = cur.fetchone()
    if row:
        new_value = 0 if row["terminee"] == 1 else 1
        cur.execute("UPDATE taches SET terminee=? WHERE id=? AND utilisateur_id=?", (new_value, tache_id, user_id))
        conn.commit()

    conn.close()
    return redirect('/taches')

if __name__ == "__main__":
    app.run(debug=True)
