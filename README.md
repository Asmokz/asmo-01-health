# 🏥 ASMO-01 Health Monitoring System

Système de monitoring intelligent pour serveur homelab avec analyse par Claude Code et alertes Discord.

## 📋 Architecture

```
┌─────────────────────────────────────────────┐
│  n8n Workflow #1: Hourly Monitor (cron)     │
│  Exécute: monitor.py toutes les heures      │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
      ┌────────────────────────┐
      │  Collecte métriques    │
      │  - Docker stats        │
      │  - CPU/RAM/Disk        │
      │  - Logs d'erreurs      │
      └────────┬───────────────┘
               │
               ▼
    ┌──────────────────────┐
    │ health_history.json  │
    │ (historique 7 jours) │
    └──────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│  n8n Workflow #2: Daily Report (9h00)       │
│  Exécute: reporter.py avec Claude Code      │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
      ┌────────────────────────┐
      │  Analyse intelligente  │
      │  - Trends 24h          │
      │  - Corrélations        │
      │  - Recommandations     │
      └────────┬───────────────┘
               │
               ▼
    ┌──────────────────────┐
    │  Discord Webhook     │
    │  (embed enrichi)     │
    └──────────────────────┘
```

## 🚀 Installation

### Prérequis
- Python 3.8+
- Docker en cours d'exécution
- n8n configuré
- Accès SSH à la machine Ubuntu

### Setup

1. **Clone le repo sur ta machine Ubuntu**
```bash
cd /home/scripts
git clone <ton-repo-url> asmo-health
cd asmo-health
```

2. **Installe les dépendances**
```bash
pip3 install -r requirements.txt --break-system-packages
```

3. **Configure le fichier config.json**
```bash
cp config.example.json config.json
nano config.json  # Ajuste les chemins et seuils
```

4. **Teste l'installation**
```bash
python3 src/monitor.py --test
python3 src/reporter.py --test
```

5. **Configure n8n** (voir section dédiée ci-dessous)

## 🔧 Configuration n8n

### Workflow #1: Hourly Monitor

**Nodes:**
1. **Schedule Trigger**
   - Cron: `0 * * * *` (toutes les heures)
   
2. **Execute Command** (SSH)
   - Command: `python3 /home/scripts/asmo-health/src/monitor.py`
   - Cwd: `/home/scripts/asmo-health`

3. **IF** (optionnel - alertes critiques)
   - Condition: `{{ $json.critical_alert === true }}`
   - True → Discord Webhook immédiat

### Workflow #2: Daily Report

**Nodes:**
1. **Schedule Trigger**
   - Cron: `0 9 * * *` (tous les jours à 9h)

2. **Execute Command** (SSH)
   - Command: `python3 /home/scripts/asmo-health/src/reporter.py`
   - Cwd: `/home/scripts/asmo-health`

3. **Code Node** (optionnel - format embed)
   - Parse le JSON retourné
   - Formate pour Discord

4. **HTTP Request** (Discord Webhook)
   - Method: POST
   - URL: `https://discord.com/api/webhooks/...`
   - Body: `{{ $json.embed }}`

## 📁 Structure des fichiers

```
asmo-health/
├── README.md                    # Ce fichier
├── requirements.txt             # Dépendances Python
├── config.json                  # Configuration (gitignored)
├── config.example.json          # Template de config
├── src/
│   ├── monitor.py              # Script de monitoring horaire
│   ├── reporter.py             # Script de rapport journalier
│   ├── remediate.py            # Actions correctives (future)
│   └── utils/
│       ├── __init__.py
│       ├── docker_client.py    # Interface Docker
│       ├── metrics.py          # Parsing métriques
│       └── storage.py          # Gestion historique JSON
├── data/
│   └── health_history.json     # Historique des métriques
└── logs/
    └── asmo.log                # Logs d'exécution
```

## 📊 Format des données stockées

```json
{
  "timestamp": "2026-01-11T09:00:00Z",
  "system": {
    "cpu_percent": 15.3,
    "ram_used_gb": 5.5,
    "ram_total_gb": 15.0,
    "disk": [
      {"mount": "/", "used_percent": 27, "used_gb": 115, "total_gb": 457},
      {"mount": "/mnt/nas", "used_percent": 31, "used_gb": 1100, "total_gb": 3600}
    ]
  },
  "containers": [
    {
      "name": "jellyfin",
      "status": "running",
      "health": "healthy",
      "cpu_percent": 0.21,
      "mem_mb": 308.2,
      "restarts": 0,
      "errors": ["SQLite Error 5: database is locked"]
    }
  ]
}
```

## 🎯 Fonctionnalités

### Monitor.py (Horaire)
- ✅ Collecte des métriques système
- ✅ Stats Docker détaillées
- ✅ Parsing des logs d'erreurs
- ✅ Détection d'anomalies temps réel
- ✅ Stockage dans historique JSON
- 🔄 Alertes critiques immédiates (optionnel)

### Reporter.py (Journalier)
- ✅ Analyse des tendances sur 24h
- ✅ Corrélation d'erreurs
- ✅ Recommandations intelligentes (Claude Code)
- ✅ Génération embed Discord enrichi
- ✅ Métriques agrégées (uptime, pics, etc.)

### Remediate.py (Future)
- 🔄 Redémarrage automatique des services
- 🔄 Nettoyage des caches
- 🔄 Ajustement de configs
- 🔄 Rollback automatique

## 🐛 Debugging

```bash
# Test monitor sans stockage
python3 src/monitor.py --test --verbose

# Test reporter avec données simulées
python3 src/reporter.py --test --debug

# Vérifier l'historique
cat data/health_history.json | jq '.[-1]'  # Dernière entrée

# Logs d'exécution
tail -f logs/asmo.log
```

## 🔒 Sécurité

- `config.json` est gitignored (contient des secrets potentiels)
- Les logs sont limités à 7 jours
- L'historique JSON est limité à 7 jours (auto-cleanup)
- Pas de credentials Docker en clair (utilise socket Unix)

## 📝 TODO / Roadmap

- [ ] Phase 1: Monitoring de base (monitor.py + reporter.py)
- [ ] Phase 2: Intégration Claude Code pour analyses
- [ ] Phase 3: Remédiation automatique (remediate.py)
- [ ] Phase 4: Dashboard web (optionnel)
- [ ] Phase 5: Alertes Telegram/Email (optionnel)

## 🤝 Contribution

Ce projet est personnel mais ouvert aux améliorations. N'hésite pas à proposer des PRs !

## 📄 License

MIT - Fais-en ce que tu veux ! 🚀

---

**Créé avec ❤️ pour ASMO-01**
*"Parce qu'un serveur heureux est un serveur qui tourne"*
