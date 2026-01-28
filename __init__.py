from flask import Flask, render_template_string, render_template, jsonify, request, redirect, url_for, session
from flask import render_template
from flask import json
from datetime import datetime
from urllib.request import urlopen
from werkzeug.utils import secure_filename
import sqlite3

app = Flask(__name__)                                                                                                                  
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'  # Clé secrète pour les sessions

# Fonction pour créer une clé "authentifie" dans la session utilisateur
def est_authentifie():
    return session.get('authentifie')

# *******************************************************************************

def user_required():
    auth = request.authorization
    if not auth or auth.username != "user" or auth.password != "12345":
        return False
    return True

def admin_required():
    # Ton admin est géré par la session (/authentification)
    return est_authentifie()

def get_user_id_basic():
    # Pour récupérer l'utilisateur (basic auth) dans la table utilisateurs
    auth = request.authorization
    if not auth:
        return None

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id FROM utilisateurs WHERE username=? AND password=? AND role='user'",
                (auth.username, auth.password))
    row = cur.fetchone()
    conn.close()
    return row["id"] if row else None




@app.route('/fiche_nom/', methods=['GET'])
def fiche_nom():
    # Contrôle d'accès USER (différent de l'admin)
    if not user_required():
        return ("Accès refusé", 401, {'WWW-Authenticate': 'Basic realm="User Area"'})

    nom = request.args.get('nom', '').strip()

    # Si aucun nom n'est donné, on affiche un mini formulaire
    if nom == "":
        return render_template_string("""
        <!doctype html>
        <html lang="fr">
          <head>
            <meta charset="UTF-8">
            <title>Recherche client</title>
            <style>
              body { font-family: Arial, sans-serif; margin: 40px; }
              .box { max-width: 520px; padding: 20px; border: 1px solid #ddd; border-radius: 10px; }
              input { width: 100%; padding: 10px; margin: 10px 0; }
              button { padding: 10px 14px; cursor: pointer; }
            </style>
          </head>
          <body>
            <div class="box">
              <h2>Rechercher un client par nom</h2>
              <form method="get" action="/fiche_nom/">
                <label for="nom">Nom du client</label>
                <input id="nom" name="nom" placeholder="Ex: Dupont" required>
                <button type="submit">Rechercher</button>
              </form>
              <p><i>Accès protégé : user / 12345</i></p>
            </div>
          </body>
        </html>
        """)

    # Recherche en base
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clients WHERE nom LIKE ?", (f"%{nom}%",))
    data = cursor.fetchall()
    conn.close()

    # Affichage des résultats (réutilise ton template si tu veux)
    return render_template('read_data.html', data=data)

#*************************************************************************************


@app.route('/')
def hello_world():
    return render_template('hello.html')

@app.route('/lecture')
def lecture():
    if not est_authentifie():
        # Rediriger vers la page d'authentification si l'utilisateur n'est pas authentifié
        return redirect(url_for('authentification'))

  # Si l'utilisateur est authentifié
    return "<h2>Bravo, vous êtes authentifié</h2>"

@app.route('/authentification', methods=['GET', 'POST'])
def authentification():
    if request.method == 'POST':
        # Vérifier les identifiants
        if request.form['username'] == 'admin' and request.form['password'] == 'password': # password à cacher par la suite
            session['authentifie'] = True
            # Rediriger vers la route lecture après une authentification réussie
            return redirect(url_for('lecture'))
        else:
            # Afficher un message d'erreur si les identifiants sont incorrects
            return render_template('formulaire_authentification.html', error=True)

    return render_template('formulaire_authentification.html', error=False)

@app.route('/fiche_client/<int:post_id>')
def Readfiche(post_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients WHERE id = ?', (post_id,))
    data = cursor.fetchall()
    conn.close()
    # Rendre le template HTML et transmettre les données
    return render_template('read_data.html', data=data)

@app.route('/consultation/')
def ReadBDD():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients;')
    data = cursor.fetchall()
    conn.close()
    return render_template('read_data.html', data=data)

@app.route('/enregistrer_client', methods=['GET'])
def formulaire_client():
    return render_template('formulaire.html')  # afficher le formulaire

@app.route('/enregistrer_client', methods=['POST'])
def enregistrer_client():
    nom = request.form['nom']
    prenom = request.form['prenom']

    # Connexion à la base de données
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Exécution de la requête SQL pour insérer un nouveau client
    cursor.execute('INSERT INTO clients (created, nom, prenom, adresse) VALUES (?, ?, ?, ?)', (1002938, nom, prenom, "ICI"))
    conn.commit()
    conn.close()
    return redirect('/consultation/')  # Rediriger vers la page d'accueil après l'enregistrement


# =========================================================
#               API BIBLIOTHEQUE (simple)
# =========================================================

# 1) Liste + recherche livres (q=...)
@app.route('/api/livres', methods=['GET'])
def api_livres():
    q = request.args.get('q', '').strip()

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
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


# 2) Livres disponibles uniquement
@app.route('/api/livres_disponibles', methods=['GET'])
def api_livres_disponibles():
    q = request.args.get('q', '').strip()

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
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


# 3) ADMIN : ajouter un livre
@app.route('/api/admin/ajouter_livre', methods=['POST'])
def api_admin_ajouter_livre():
    if not admin_required():
        return jsonify({"error": "admin_required"}), 401

    data = request.get_json(silent=True) or {}
    titre = (data.get("titre") or "").strip()
    auteur = (data.get("auteur") or "").strip()
    isbn = (data.get("isbn") or "").strip() or None
    stock_total = int(data.get("stock_total") or 1)

    if not titre or not auteur or stock_total < 0:
        return jsonify({"error": "invalid_payload"}), 400

    conn = sqlite3.connect('database.db')
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


# 4) ADMIN : supprimer un livre (si pas d'emprunt en cours)
@app.route('/api/admin/supprimer_livre/<int:livre_id>', methods=['DELETE'])
def api_admin_supprimer_livre(livre_id):
    if not admin_required():
        return jsonify({"error": "admin_required"}), 401

    conn = sqlite3.connect('database.db')
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


# 5) ADMIN : modifier stock_total (auto ajuste stock_disponible)
@app.route('/api/admin/stock/<int:livre_id>', methods=['PATCH'])
def api_admin_stock(livre_id):
    if not admin_required():
        return jsonify({"error": "admin_required"}), 401

    data = request.get_json(silent=True) or {}
    new_total = data.get("stock_total")
    if new_total is None:
        return jsonify({"error": "missing_stock_total"}), 400

    new_total = int(new_total)
    if new_total < 0:
        return jsonify({"error": "invalid_stock_total"}), 400

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
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


# 6) USER : emprunter un livre
@app.route('/api/user/emprunter', methods=['POST'])
def api_user_emprunter():
    if not user_required():
        return ("Accès refusé", 401, {'WWW-Authenticate': 'Basic realm="User Area"'})

    user_id = get_user_id_basic()
    if not user_id:
        return ("Accès refusé", 401, {'WWW-Authenticate': 'Basic realm="User Area"'})

    data = request.get_json(silent=True) or {}
    livre_id = data.get("livre_id")
    if not livre_id:
        return jsonify({"error": "missing_livre_id"}), 400

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT stock_disponible FROM livres WHERE id=?", (livre_id,))
    livre = cur.fetchone()
    if not livre:
        conn.close()
        return jsonify({"error": "book_not_found"}), 404
    if livre["stock_disponible"] <= 0:
        conn.close()
        return jsonify({"error": "no_stock"}), 409

    # stock -1 + emprunt
    cur.execute("UPDATE livres SET stock_disponible = stock_disponible - 1 WHERE id=?", (livre_id,))
    cur.execute("""
        INSERT INTO emprunts (utilisateur_id, livre_id, statut)
        VALUES (?, ?, 'EN_COURS')
    """, (user_id, livre_id))

    conn.commit()
    emprunt_id = cur.lastrowid
    conn.close()

    return jsonify({"message": "emprunt_ok", "emprunt_id": emprunt_id})


# 7) USER : retour d'un emprunt
@app.route('/api/user/retour/<int:emprunt_id>', methods=['POST'])
def api_user_retour(emprunt_id):
    if not user_required():
        return ("Accès refusé", 401, {'WWW-Authenticate': 'Basic realm="User Area"'})

    user_id = get_user_id_basic()
    if not user_id:
        return ("Accès refusé", 401, {'WWW-Authenticate': 'Basic realm="User Area"'})

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT livre_id FROM emprunts
        WHERE id=? AND utilisateur_id=? AND statut='EN_COURS'
    """, (emprunt_id, user_id))
    emp = cur.fetchone()

    if not emp:
        conn.close()
        return jsonify({"error": "emprunt_not_found"}), 404

    # set retour + stock +1
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


# 8) ADMIN : liste utilisateurs
@app.route('/api/admin/users', methods=['GET'])
def api_admin_users():
    if not admin_required():
        return jsonify({"error": "admin_required"}), 401

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, username, role FROM utilisateurs ORDER BY id DESC")
    data = cur.fetchall()
    conn.close()
    return jsonify([dict(r) for r in data])


# 9) ADMIN : ajouter utilisateur
@app.route('/api/admin/users', methods=['POST'])
def api_admin_add_user():
    if not admin_required():
        return jsonify({"error": "admin_required"}), 401

    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()
    role = (data.get("role") or "").strip()

    if not username or not password or role not in ("admin", "user"):
        return jsonify({"error": "invalid_payload"}), 400

    conn = sqlite3.connect('database.db')
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

                                                                                                                                       
if __name__ == "__main__":
  app.run(debug=True)
