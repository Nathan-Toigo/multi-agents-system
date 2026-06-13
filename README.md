# 🏭 Usine de Cartons — Microservices

Application de gestion d'usine de cartons composée de **4 microservices indépendants**, chacun exposant une API REST documentée via Swagger.

## Architecture

```
multi-agents-system/
├── docker-compose.yml          ← Orchestration globale
├── stock-service/              ← Port 8001
├── production-service/         ← Port 8002
├── order-service/              ← Port 8003
└── machine-service/            ← Port 8004
```

## Services

| Service | Port | Description | Swagger |
|---|---|---|---|
| **stock-service** | `8001` | Stock de matières premières et produits finis | http://localhost:8001/docs |
| **production-service** | `8002` | Ordres de fabrication (pending→in_progress→completed) | http://localhost:8002/docs |
| **order-service** | `8003` | Commandes clients | http://localhost:8003/docs |
| **machine-service** | `8004` | Machines de l'usine et leur état | http://localhost:8004/docs |

## Démarrage rapide

### Tout lancer (depuis la racine)
```bash
docker compose up --build
```

### Lancer un service individuellement
```bash
cd stock-service
docker compose up --build
```

## Endpoints clés

### 📦 Stock Service (`localhost:8001`)
| Méthode | Route | Description |
|---|---|---|
| `GET` | `/stocks` | Liste tout le stock |
| `POST` | `/stocks` | Créer un article |
| `PUT` | `/stocks/{id}/add` | **Incrémenter** le stock |
| `PUT` | `/stocks/{id}/remove` | **Décrémenter** le stock |
| `GET` | `/stocks/alerts` | Articles sous le seuil critique |

### 🏭 Production Service (`localhost:8002`)
| Méthode | Route | Description |
|---|---|---|
| `GET` | `/productions` | Liste des ordres |
| `POST` | `/productions` | Créer un ordre |
| `PUT` | `/productions/{id}/start` | Démarrer |
| `PUT` | `/productions/{id}/complete` | Terminer |
| `PUT` | `/productions/{id}/progress` | Mettre à jour la quantité produite |

### 📋 Order Service (`localhost:8003`)
| Méthode | Route | Description |
|---|---|---|
| `GET` | `/orders` | Liste des commandes |
| `POST` | `/orders` | Créer une commande |
| `PUT` | `/orders/{id}/status` | Changer le statut |

### ⚙️ Machine Service (`localhost:8004`)
| Méthode | Route | Description |
|---|---|---|
| `GET` | `/machines` | Liste des machines |
| `POST` | `/machines` | Ajouter une machine |
| `PUT` | `/machines/{id}/status` | `running` / `stopped` / `maintenance` |

## Health Checks

Chaque service expose `/health` :
```bash
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
```

## Stack technique

- **Runtime** : Python 3.12
- **Framework** : FastAPI + Uvicorn
- **ORM** : SQLAlchemy 2.0
- **Base de données** : SQLite (par service, persistée via volume Docker)
- **Container** : Docker + Docker Compose
