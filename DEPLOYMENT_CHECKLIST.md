# 🚀 ASMO-01 - Checklist de Déploiement

## ✅ Étape par étape

### 1️⃣ Préparation (sur ton poste dev)
- [ ] Clone ce repo dans VSCode
- [ ] Lis le README.md pour comprendre l'architecture
- [ ] Lis le QUICKSTART.md pour le setup
- [ ] Personnalise le config.example.json si besoin (voir CUSTOMIZATION.md)
- [ ] Commit + Push sur ton repo Git

### 2️⃣ Installation (sur ta machine Ubuntu via SSH)
```bash
# Connecte-toi en SSH
ssh user@asmo-01.local

# Clone le repo
cd /home/scripts
git clone <ton-repo-url> asmo-health
cd asmo-health

# Installe les dépendances
pip3 install -r requirements.txt --break-system-packages

# Crée le fichier config
python3 src/monitor.py --create-config

# Optionnel: ajuste la config
nano config.json
```

### 3️⃣ Tests (toujours en SSH)
```bash
# Test de setup
python3 src/test_setup.py

# Test du monitoring
python3 src/monitor.py --test --verbose

# Test du reporter
python3 src/reporter.py --test --verbose
```

Si tous les tests passent → ✅ Continue

### 4️⃣ Configuration n8n

#### Workflow 1: Hourly Monitor
- [ ] Crée un nouveau workflow "ASMO-01 Hourly Monitor"
- [ ] Ajoute Schedule Trigger (cron: `0 * * * *`)
- [ ] Ajoute Execute Command (SSH):
  - Command: `python3 /home/scripts/asmo-health/src/monitor.py`
  - Working Dir: `/home/scripts/asmo-health`
- [ ] Optionnel: Ajoute IF node pour alertes critiques
- [ ] Test en mode manuel (Execute Workflow)
- [ ] Active le workflow

#### Workflow 2: Daily Report
- [ ] Crée un nouveau workflow "ASMO-01 Daily Report"
- [ ] Ajoute Schedule Trigger (cron: `0 9 * * *`)
- [ ] Ajoute Execute Command (SSH):
  - Command: `python3 /home/scripts/asmo-health/src/reporter.py`
  - Working Dir: `/home/scripts/asmo-health`
- [ ] Ajoute HTTP Request (Discord Webhook):
  - Method: POST
  - URL: `https://discord.com/api/webhooks/...`
  - Body: `{{ $json.embed }}`
- [ ] Test en mode manuel
- [ ] Active le workflow

### 5️⃣ Validation (attendre quelques heures)
```bash
# Vérifie que les données sont collectées
cat /home/scripts/asmo-health/data/health_history.json | jq '.[-1]'

# Vérifie les logs
tail -f /home/scripts/asmo-health/logs/asmo.log

# Compte les entrées d'historique
cat /home/scripts/asmo-health/data/health_history.json | jq '. | length'
```

- [ ] Au moins 1 entrée dans health_history.json
- [ ] Pas d'erreurs dans les logs
- [ ] Discord reçoit bien le rapport du matin

### 6️⃣ Phase 2 (optionnel - Claude Code)
- [ ] Lis CLAUDE_CODE_INTEGRATION.md
- [ ] Configure l'API Anthropic dans n8n
- [ ] Modifie le workflow Daily Report
- [ ] Teste l'analyse AI

---

## 📊 Stats du projet

- **Lignes de code Python**: ~1577 lignes
- **Fichiers Python**: 8 fichiers
- **Documentation**: 5 fichiers Markdown
- **Temps d'installation**: ~5 minutes
- **Temps de config n8n**: ~10 minutes

---

## 🎯 Résultat attendu

### Après 1 heure:
- ✅ 1 entrée dans health_history.json
- ✅ Logs montrant "Monitor completed successfully"

### Après 24 heures:
- ✅ 24 entrées dans health_history.json
- ✅ Premier rapport Discord reçu à 9h
- ✅ Analyse des tendances sur 24h

### Après 7 jours:
- ✅ Historique complet de 7 jours
- ✅ Détection de patterns fiable
- ✅ Prêt pour Phase 2 (Claude Code)

---

## 🐛 En cas de problème

1. **Check les logs**: `tail -f logs/asmo.log`
2. **Test manuel**: `python3 src/monitor.py --test --verbose`
3. **Vérifie Docker**: `docker ps`
4. **Vérifie les permissions**: `ls -la data/ logs/`

### Problèmes courants

| Problème | Solution |
|----------|----------|
| "Permission denied" Docker | `sudo usermod -aG docker $USER` + reconnexion |
| "No module 'docker'" | `pip3 install -r requirements.txt --break-system-packages` |
| n8n ne trouve pas le script | Vérifie le chemin absolu `/home/scripts/...` |
| Pas de données après 1h | Vérifie que le workflow n8n est bien activé |

---

## 📞 Contact / Support

- Lis la doc complète dans README.md
- Check CUSTOMIZATION.md pour personnaliser
- Lis CLAUDE_CODE_INTEGRATION.md pour Phase 2

---

Bonne installation ! 🎉
