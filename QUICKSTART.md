# 🚀 ASMO-01 Health Monitoring - Quick Start Guide

## ⚡ Installation rapide (5 minutes)

### 1. Clone sur ta machine Ubuntu

```bash
cd /home/scripts
git clone <ton-repo-url> asmo-health
cd asmo-health
```

### 2. Installe les dépendances

```bash
pip3 install -r requirements.txt --break-system-packages
```

### 3. Crée ta configuration

```bash
python3 src/monitor.py --create-config
nano config.json  # Ajuste si besoin (optionnel)
```

### 4. Test rapide

```bash
# Test le monitor
python3 src/monitor.py --test --verbose

# Test le reporter
python3 src/reporter.py --test --verbose
```

Si tout fonctionne, tu devrais voir des métriques JSON s'afficher ! ✅

---

## 🔧 Configuration n8n

### Workflow #1: Monitoring Horaire

**Nom**: `ASMO-01 Hourly Monitor`

**Nodes**:

1. **Schedule Trigger**
   - Type: `Cron`
   - Expression: `0 * * * *` (toutes les heures)
   
2. **Execute Command** (SSH)
   - Command: `python3 /home/scripts/asmo-health/src/monitor.py`
   - Working Directory: `/home/scripts/asmo-health`

3. **IF** (optionnel - pour alertes critiques)
   - Condition: `{{ $json.critical_alert }} === true`
   - **True branch** → Discord Webhook (alerte immédiate)

**Test**: Clique sur "Execute Workflow" et vérifie que ça fonctionne !

---

### Workflow #2: Rapport Journalier

**Nom**: `ASMO-01 Daily Report`

**Nodes**:

1. **Schedule Trigger**
   - Type: `Cron`
   - Expression: `0 9 * * *` (9h du matin)

2. **Execute Command** (SSH)
   - Command: `python3 /home/scripts/asmo-health/src/reporter.py`
   - Working Directory: `/home/scripts/asmo-health`

3. **Code Node** (Parse le JSON)
   ```javascript
   // Simple passthrough ou transformations si besoin
   return [$input.item.json];
   ```

4. **HTTP Request** (Discord Webhook)
   - Method: `POST`
   - URL: `https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN`
   - Body Type: `JSON`
   - Body: `{{ $json.embed }}`

**Test**: Clique sur "Execute Workflow" et vérifie ton salon Discord !

---

## 🎯 Vérifications

### Vérifier que les données sont collectées

```bash
# Voir le dernier snapshot
cat /home/scripts/asmo-health/data/health_history.json | tail -50

# Compter les entrées
cat /home/scripts/asmo-health/data/health_history.json | jq '. | length'

# Voir la dernière entrée (jq requis: apt install jq)
cat /home/scripts/asmo-health/data/health_history.json | jq '.[-1]'
```

### Vérifier les logs

```bash
tail -f /home/scripts/asmo-health/logs/asmo.log
```

### Forcer un monitoring maintenant

```bash
cd /home/scripts/asmo-health
python3 src/monitor.py
```

---

## 🐛 Troubleshooting

### Erreur "Permission denied" avec Docker

```bash
# Ajoute ton user au groupe docker
sudo usermod -aG docker $USER

# Puis reconnecte-toi (ou redémarre la session SSH)
```

### Erreur "No module named 'docker'"

```bash
pip3 install -r requirements.txt --break-system-packages
```

### Le fichier history.json n'existe pas

C'est normal au premier lancement ! Il sera créé automatiquement.

### Les workflows n8n ne fonctionnent pas

1. Vérifie que tu utilises le bon chemin absolu
2. Teste d'abord la commande en SSH manuel
3. Vérifie les logs: `tail -f /home/scripts/asmo-health/logs/asmo.log`

---

## 📊 Exemple de sortie

### Monitor.py (horaire)

```json
{
  "success": true,
  "timestamp": "2026-01-11T10:00:00",
  "critical_alert": false,
  "summary": {
    "cpu_percent": 15.3,
    "ram_percent": 35.2,
    "containers_running": 24,
    "containers_total": 24,
    "critical_issues": [],
    "warnings": []
  }
}
```

### Reporter.py (journalier)

```json
{
  "success": true,
  "embed": {
    "embeds": [{
      "title": "✅ ASMO-01 • 24h Health Report",
      "description": "CPU: Avg 12.5% (peak 45%) • RAM: Avg 38% (peak 52%)",
      "fields": [...]
    }]
  }
}
```

---

## 🎓 Prochaines étapes

1. ✅ Setup initial + test
2. ✅ Configure workflows n8n
3. ⏳ Attendre 24h pour avoir des données
4. 🚀 Phase 2: Intégration Claude Code pour analyses avancées
5. 🤖 Phase 3: Auto-remediation

---

## 💬 Support

Si tu as des questions ou des problèmes:
1. Vérifie les logs
2. Lance les scripts en mode `--verbose` 
3. Teste en `--test` mode d'abord

Bon monitoring ! 🏥✨
