import sqlite3

connection = sqlite3.connect('database.db')

with open('schema.sql', encoding="utf-8") as f:
    connection.executescript(f.read())

cur = connection.cursor()

# --- Clients (optionnel) ---
clients = [
    ('DUPONT', 'Emilie', '123, Rue des Lilas, 75001 Paris'),
    ('LEROUX', 'Lucas', '456, Avenue du Soleil, 31000 Toulouse'),
    ('MARTIN', 'Amandine', '789, Rue des Érables, 69002 Lyon'),
    ('TREMBLAY', 'Antoine', '1010, Boulevard de la Mer, 13008 Marseille'),
    ('LAMBERT', 'Sarah', '222, Avenue de la Liberté, 59000 Lille'),
    ('GAGNON', 'Nicolas', '456, Boulevard des Cerisiers, 69003 Lyon'),
    ('DUBOIS', 'Charlotte', '789, Rue des Roses, 13005 Marseille'),
    ('LEFEVRE', 'Thomas', '333, Rue de la Paix, 75002 Paris'),
]

cur.executemany(
    "INSERT INTO clients (nom, prenom, adresse) VALUES (?, ?, ?)",
    clients
)

# --- Utilisateurs (évite les doublons) ---
cur.execute("INSERT OR IGNORE INTO utilisateurs (username, password, role) VALUES (?, ?, ?)",("admin", "password", "admin"))
cur.execute("INSERT OR IGNORE INTO utilisateurs (username, password, role) VALUES (?, ?, ?)",("user", "12345", "user"))

# --- Livres (évite doublons grâce à ISBN UNIQUE + INSERT OR IGNORE) ---
livres = [
    ("Le Petit Prince", "Antoine de Saint-Exupéry", "9782070612758", 3, 3),
    ("1984", "George Orwell", "9780451524935", 2, 2),
    ("L'Étranger", "Albert Camus", "9782070360024", 1, 1),
    ("Harry Potter à l'école des sorciers", "J.K. Rowling", "9782070584628", 4, 4),
    ("Les Misérables", "Victor Hugo", "9782253004226", 2, 2),
]

cur.executemany(
    "INSERT OR IGNORE INTO livres (titre, auteur, isbn, stock_total, stock_disponible) VALUES (?, ?, ?, ?, ?)",
    livres
)

# Tâches (exemples)
cur.execute("SELECT id FROM utilisateurs WHERE username='user'")
user_id = cur.fetchone()[0]

taches = [
    (user_id, "Finir le TP Flask", "Ajouter l'API et tester sur AlwaysData", "2026-02-20", 0),
    (user_id, "Relire le cours", "Sessions + SQLite + routes", "2026-02-22", 1),
]
cur.executemany(
    "INSERT INTO taches (utilisateur_id, titre, description, date_echeance, terminee) VALUES (?, ?, ?, ?, ?)",
    taches
)

connection.commit()
connection.close()

print("✅ Base créée / mise à jour avec utilisateurs + livres.")
