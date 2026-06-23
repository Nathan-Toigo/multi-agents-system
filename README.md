# 🏭 Usine de Cartons — Système Multi-Agents & Microservices

Bienvenue dans le projet **Usine de Cartons**. Il s'agit d'une plateforme de gestion complète pour une usine de fabrication de cartons, reposant sur une architecture en microservices et intégrant un **Agent IA** (LLM) capable de piloter l'usine, d'interroger les bases de données et de consulter la documentation technique.

---

## 🏗️ Architecture et Services

Le système est découpé en 7 microservices distincts, orchestrés via Docker Compose :

### 1. Les Microservices Métiers (Backend)
Ces services gèrent la logique métier et stockent leurs données dans des bases de données SQLite individuelles.
* **📦 Stock Service (Port 8001)** : Gestion des matières premières (carton, colle, encre) et des produits finis.
* **🏭 Production Service (Port 8002)** : Gestion du cycle de vie des ordres de fabrication (en attente, en cours, terminés).
* **📋 Order Service (Port 8003)** : Gestion des commandes clients.
* **⚙️ Machine Service (Port 8004)** : Gestion du parc de machines (découpeuses, plieuses, imprimeuses) et de leurs statuts (en marche, arrêtée, maintenance).

### 2. Les Services d'Intelligence Artificielle
* **🤖 Agent Service (Port 8005)** : Le cœur intelligent. Il utilise un LLM Azure OpenAI (`gpt-5.2`) avec des capacités de *Function Calling* (Outils). Il est capable de traduire le langage naturel de l'utilisateur en appels d'API vers les autres microservices.
* **📚 RAG Service (Port 8006)** : Service de *Retrieval-Augmented Generation*. Il indexe automatiquement les documentations techniques (format Markdown) dans une base de données vectorielle ChromaDB grâce à un modèle d'embedding (`text-embedding-3-small`). L'agent IA utilise ce service pour répondre aux questions techniques complexes sur les machines ou la qualité.

### 3. L'Interface Utilisateur
* **🖥️ Frontend Service (Port 8080)** : Un tableau de bord moderne et dynamique (HTML/JS/CSS natif) servi par NGINX. Il agrège les données des services métiers et propose une interface de chat flottante pour dialoguer avec l'Agent IA.

---

## 🔄 Comment les services interagissent-ils ?

L'architecture repose sur des communications asynchrones via des requêtes HTTP (REST) :

1. **Utilisateur ↔ Dashboard** : L'utilisateur accède au frontend qui interroge directement les services métiers (`stock`, `order`, etc.) pour afficher les statistiques et les listes interactives.
2. **Utilisateur ↔ Agent IA** : Depuis le chat du Dashboard, l'utilisateur pose une question (ex: *"Met la machine Delta en maintenance"*). Le Frontend envoie le message à l'`Agent Service`.
3. **Agent IA ↔ Microservices Métiers** : Grâce à ses *Tools*, l'agent IA détermine qu'il doit interroger le `Machine Service`. Il exécute une requête `GET /machines` pour trouver l'ID de la machine, puis une requête `PUT /machines/{id}/status` pour la mettre en maintenance, avant de répondre à l'utilisateur.
4. **Agent IA ↔ RAG Service** : Si l'utilisateur pose une question de procédure (ex: *"Comment réparer l'imprimeuse ?"*), l'agent appelle le `RAG Service`. Ce dernier compare sémantiquement la question avec son index vectoriel (ChromaDB), extrait le paragraphe pertinent du document Markdown, et le renvoie à l'agent qui synthétise la réponse.

---

## 🚀 Faire fonctionner l'application (Pas à Pas)

### Prérequis
- [Docker](https://docs.docker.com/get-docker/) et Docker Compose installés.
- Une clé d'API Azure OpenAI valide.

### Étape 1 : Configuration de l'environnement
1. À la racine du projet, vous trouverez un fichier `.env`.
2. Ouvrez-le et renseignez vos paramètres Azure OpenAI :
   ```env
   AZURE_OPENAI_API_KEY="votre_cle_api"
   AZURE_OPENAI_ENDPOINT="votre_endpoint_azure"
   AZURE_OPENAI_API_VERSION="2024-05-01-preview"
   AZURE_OPENAI_DEPLOYMENT="gpt-5.2"
   AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-3-small"
   ```

### Étape 2 : Lancement des conteneurs Docker
Dans le dossier racine du projet (où se trouve le `docker-compose.yml`), ouvrez un terminal et exécutez :
```bash
docker compose up --build
```
Cette commande va télécharger les dépendances, construire les 7 conteneurs et les lancer.

*(Le premier lancement peut prendre quelques minutes le temps que l'indexation ChromaDB du RAG se fasse).*


### Étape 4 : Accéder à l'application
Ouvrez votre navigateur web et rendez-vous à l'adresse suivante :
👉 **http://localhost:8080**

Vous verrez apparaître le tableau de bord de l'usine. En bas à droite, cliquez sur l'icône de **Chat (💬)** pour commencer à dialoguer avec l'agent IA.

---

## 💡 Exemples de requêtes pour l'IA

Vous pouvez tester le système en demandant à l'IA :
- *"Donne-moi l'état de nos stocks."*
- *"Crée une commande pour le client IKEA (2000 boîtes)."*
- *"La machine BOBST L1 fait un bruit de claquement anormal, que dois-je faire selon la doc ?"*
- *"Met l'Imprimeuse Couleur Gamma en maintenance."*

---
*Ce projet a été généré dans le cadre d'un PoC d'Architecture d'Entreprise.*
