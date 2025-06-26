#!/bin/bash

echo "🚀 Démarrage des conteneurs Docker..."
docker-compose up --build -d

echo "⏳ Vérification de l’état de la base de données PostgreSQL..."

# Attendre quelques secondes que Postgres soit prêt
sleep 5

# Vérifie si la table 'product' existe déjà
docker exec flask_app psql -U user -d api8inf349 -c '\dt' | grep product > /dev/null

if [ $? -ne 0 ]; then
  echo "📦 Base non initialisée, exécution de 'flask init-db'..."
  docker exec flask_app flask init-db
else
  echo "✅ Base de données déjà initialisée."
fi

echo "🟢 Projet prêt sur http://localhost:5050"
