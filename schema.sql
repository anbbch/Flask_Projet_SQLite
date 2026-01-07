DROP TABLE IF EXISTS clients;
DROP TABLE IF EXISTS emprunts;
DROP TABLE IF EXISTS livres;
DROP TABLE IF EXISTS utilisateurs;


CREATE TABLE clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    adresse TEXT NOT NULL
);

-- Utilisateurs (admin / user)
CREATE TABLE utilisateurs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'user'))
);

-- Livres (stock = nombre d'exemplaires)
CREATE TABLE livres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    titre TEXT NOT NULL,
    auteur TEXT NOT NULL,
    isbn TEXT UNIQUE,
    stock_total INTEGER NOT NULL DEFAULT 1,
    stock_disponible INTEGER NOT NULL DEFAULT 1
);

-- Emprunts (un emprunt = 1 exemplaire emprunté)
CREATE TABLE emprunts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    utilisateur_id INTEGER NOT NULL,
    livre_id INTEGER NOT NULL,
    date_emprunt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_retour_prevue TIMESTAMP,
    date_retour_effective TIMESTAMP,
    statut TEXT NOT NULL DEFAULT 'EN_COURS' CHECK(statut IN ('EN_COURS', 'RETOURNE')),
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id),
    FOREIGN KEY (livre_id) REFERENCES livres(id)
);
