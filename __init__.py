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

@app.route('/fiche_nom', methods=['GET'])
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
                                                                                                                                       
if __name__ == "__main__":
  app.run(debug=True)
