import sqlite3

connection = sqlite3.connect('database.db')

with open('schema.sql') as f:
    connection.executescript(f.read())

cur = connection.cursor()

cur.execute("INSERT INTO clients (nom, prenom, adresse) VALUES (?, ?, ?)",('DUPONT', 'Emilie', '123, Rue des Lilas, 75001 Paris'))
cur.execute("INSERT INTO clients (nom, prenom, adresse) VALUES (?, ?, ?)",('LEROUX', 'Lucas', '456, Avenue du Soleil, 31000 Toulouse'))
cur.execute("INSERT INTO clients (nom, prenom, adresse) VALUES (?, ?, ?)",('MARTIN', 'Amandine', '789, Rue des Érables, 69002 Lyon'))
cur.execute("INSERT INTO clients (nom, prenom, adresse) VALUES (?, ?, ?)",('TREMBLAY', 'Antoine', '1010, Boulevard de la Mer, 13008 Marseille'))
cur.execute("INSERT INTO clients (nom, prenom, adresse) VALUES (?, ?, ?)",('LAMBERT', 'Sarah', '222, Avenue de la Liberté, 59000 Lille'))
cur.execute("INSERT INTO clients (nom, prenom, adresse) VALUES (?, ?, ?)",('GAGNON', 'Nicolas', '456, Boulevard des Cerisiers, 69003 Lyon'))
cur.execute("INSERT INTO clients (nom, prenom, adresse) VALUES (?, ?, ?)",('DUBOIS', 'Charlotte', '789, Rue des Roses, 13005 Marseille'))
cur.execute("INSERT INTO clients (nom, prenom, adresse) VALUES (?, ?, ?)",('LEFEVRE', 'Thomas', '333, Rue de la Paix, 75002 Paris'))

# Utilisateurs
cur.execute("INSERT INTO utilisateurs (username, password, role) VALUES (?, ?, ?)",("admin", "password", "admin"))
cur.execute("INSERT INTO utilisateurs (username, password, role) VALUES (?, ?, ?)",("user", "12345", "user"))

# Livres (exemples)
livres = [
    ("Le Petit Prince", "Antoine de Saint-Exupéry", "9782070612758", 3, 3),
    ("1984", "George Orwell", "9780451524935", 2, 2),
    ("L'Étranger", "Albert Camus", "9782070360024", 1, 1),
    ("Harry Potter à l'école des sorciers", "J.K. Rowling", "9782070584628", 4, 4),
    ("Les Misérables", "Victor Hugo", "9782253004226", 2, 2),
]

cur.executemany("INSERT INTO livres (titre, auteur, isbn, stock_total, stock_disponible) VALUES (?, ?, ?, ?, ?)",livres)

connection.commit()
connection.close()
