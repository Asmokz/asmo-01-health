# 🎨 ASMO-01 - Guide de Personnalisation

Ce guide t'explique comment adapter le système de monitoring à tes besoins spécifiques.

---

## 🎯 Ajuster les seuils d'alerte

Édite `config.json` :

```json
{
  "thresholds": {
    "cpu_warning": 80,      // ⚠️ Warning si CPU > 80%
    "cpu_critical": 95,     // 🔥 Critical si CPU > 95%
    "ram_warning": 85,      // ⚠️ Warning si RAM > 85%
    "ram_critical": 95,     // 🔥 Critical si RAM > 95%
    "disk_warning": 80,     // ⚠️ Warning si Disque > 80%
    "disk_critical": 90,    // 🔥 Critical si Disque > 90%
    "container_restart_warning": 3,   // ⚠️ Si 3+ restarts
    "container_restart_critical": 5   // 🔥 Si 5+ restarts
  }
}
```

**Exemples d'ajustements** :
- Serveur puissant → Monte les seuils (90/98)
- Serveur limité → Baisse les seuils (70/85)
- Environnement de prod → Seuils plus stricts
- Homelab perso → Seuils plus souples

---

## 🐳 Ignorer certains containers

Si tu veux exclure des containers du monitoring :

```json
{
  "docker": {
    "containers_to_ignore": [
      "test-container",
      "temporary-db",
      "dev-environment"
    ]
  }
}
```

**Cas d'usage** :
- Containers de test éphémères
- Services qui crashent volontairement (chaos testing)
- Containers de développement

---

## 📊 Personnaliser le rapport Discord

### Modifier le nombre de top containers

Dans `config.json` :

```json
{
  "reporting": {
    "top_memory_containers": 5,    // Top 5 RAM consumers
    "top_cpu_containers": 5,        // Top 5 CPU consumers
    "max_errors_in_report": 10      // Max 10 erreurs par container
  }
}
```

### Changer les emojis et couleurs

Édite `src/reporter.py`, fonction `generate_discord_embed()` :

```python
# Ligne ~270
if critical_count > 0:
    status_emoji = "🔴"  # Change ici
    status_text = "Critical Issues"
elif warning_count > 0:
    status_emoji = "⚠️"   # Change ici
    status_text = "Warnings"
else:
    status_emoji = "✅"  # Change ici
    status_text = "All Systems Nominal"
```

**Couleurs Discord** (ligne ~290) :
```python
"color": 15158332  # Rouge pour critical
"color": 16776960  # Jaune pour warnings  
"color": 3066993   # Vert pour OK
```

### Ajouter des fields personnalisés

Dans `generate_discord_embed()`, ajoute :

```python
embed["embeds"][0]["fields"].append({
    "name": "🌐 Network Stats",
    "value": f"RX: {latest_entry.get('network', {}).get('bytes_recv_mb', 0)} MB",
    "inline": True
})
```

---

## 🕐 Ajuster la fréquence de collecte

### Monitoring plus fréquent (toutes les 30 min)

Dans n8n, change le cron :
```
*/30 * * * *  # Au lieu de 0 * * * *
```

⚠️ **Attention** : Plus de collectes = fichier history plus gros

### Monitoring moins fréquent (toutes les 2h)

```
0 */2 * * *
```

💡 **Conseil** : Pour un homelab, 1h est un bon compromis.

---

## 💾 Ajuster la rétention des données

Dans `config.json` :

```json
{
  "monitoring": {
    "history_retention_days": 7,    // Garde 7 jours d'historique
    "log_retention_days": 7         // Garde 7 jours de logs
  }
}
```

**Considérations** :
- Plus de jours = meilleure analyse des tendances
- Plus de jours = fichier plus gros
- 7 jours = ~168 entrées (si toutes les heures)
- Taille estimée : ~1-2 MB par semaine

---

## 🎨 Personnaliser les personas (Mythologics)

Si tu veux associer les services à tes personas :

### Ajouter des tags dans le rapport

Édite `reporter.py`, ajoute un mapping :

```python
PERSONA_MAPPING = {
    'jellyfin': 'GIORGIO (Artiste/Média)',
    'vaultwarden': 'PROWLER (Sécurité)',
    'home-assistant': 'ALITA (Assistante)',
    'grafana': 'FEMTO (Superviseur)',
    'homarr': 'MELINA (Guide)',
    'stirling-pdf': 'FORGE (Créateur)',
}

def get_persona(container_name):
    return PERSONA_MAPPING.get(container_name, 'Unknown')
```

Puis dans le rapport :

```python
problems_text += f"{icon} **{p['name']}** ({get_persona(p['name'])}): ..."
```

---

## 📈 Ajouter des métriques personnalisées

### Exemple : Température du CPU

1. **Installe lm-sensors** :
```bash
sudo apt install lm-sensors
sudo sensors-detect
```

2. **Ajoute dans `metrics.py`** :

```python
@staticmethod
def get_cpu_temperature() -> float:
    """Get CPU temperature"""
    try:
        temps = psutil.sensors_temperatures()
        if 'coretemp' in temps:
            return round(temps['coretemp'][0].current, 1)
    except:
        pass
    return None
```

3. **Utilise dans `monitor.py`** :

```python
metrics['cpu_temp'] = SystemMetrics.get_cpu_temperature()
```

4. **Affiche dans le rapport** :

```python
embed["embeds"][0]["fields"].append({
    "name": "🌡️ Temperature",
    "value": f"{latest_entry.get('cpu_temp', 'N/A')}°C",
    "inline": True
})
```

---

## 🔔 Ajouter d'autres canaux de notification

### Telegram

Installe le package :
```bash
pip3 install python-telegram-bot --break-system-packages
```

Ajoute dans `reporter.py` :

```python
from telegram import Bot

async def send_telegram(message):
    bot = Bot(token='YOUR_BOT_TOKEN')
    await bot.send_message(chat_id='YOUR_CHAT_ID', text=message)
```

### Email (SMTP)

```python
import smtplib
from email.mime.text import MIMEText

def send_email(subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = 'asmo@example.com'
    msg['To'] = 'you@example.com'
    
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login('user', 'password')
        server.send_message(msg)
```

### Ntfy.sh (Push notifications)

```bash
curl -d "ASMO-01 Critical Alert" ntfy.sh/asmo-alerts
```

Ou dans Python :
```python
import requests
requests.post('https://ntfy.sh/asmo-alerts', data='Alert message')
```

---

## 🎭 Modes d'exécution avancés

### Mode silencieux (pas de sortie sauf erreurs)

```bash
python3 src/monitor.py > /dev/null 2>&1
```

### Mode verbeux avec timestamp

```bash
python3 src/monitor.py --verbose 2>&1 | ts '[%Y-%m-%d %H:%M:%S]'
```

### Test avec données simulées

Crée `src/test_data.json` :

```json
{
  "cpu_percent": 85.5,
  "ram_percent": 92.3,
  "containers": [...]
}
```

Modifie `reporter.py` pour charger depuis ce fichier en mode test.

---

## 🔧 Debugging avancé

### Activer logs détaillés

```json
{
  "logging": {
    "level": "DEBUG",
    "include_docker_api_calls": true
  }
}
```

### Profiler les performances

Ajoute en début de `monitor.py` :

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# ... ton code ...

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumtime')
stats.print_stats(10)  # Top 10 fonctions les plus lentes
```

---

## 🚀 Intégrations futures

### Grafana Dashboard

1. Exporte les métriques vers Prometheus format
2. Configure un scraper
3. Crée un dashboard custom

### API REST

Enveloppe le monitoring dans Flask :

```python
from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/health')
def health():
    storage = HealthStorage(...)
    latest = storage.get_latest_entry()
    return jsonify(latest)

app.run(port=5000)
```

### Webhook sortant

Au lieu de Discord uniquement, POST vers ton propre endpoint :

```python
import requests

def send_webhook(data):
    requests.post(
        'https://your-api.com/asmo-webhook',
        json=data,
        headers={'Authorization': 'Bearer YOUR_TOKEN'}
    )
```

---

## 💡 Tips & Tricks

### Réduire la consommation de ressources

1. Augmente l'intervalle de collecte (2h au lieu de 1h)
2. Réduis `error_log_lines_to_check` de 50 à 20
3. Limite `history_retention_days` à 3 jours

### Améliorer la précision

1. Collecte plus fréquente (30min)
2. Augmente `error_log_lines_to_check` à 100
3. Ajoute des healthchecks personnalisés par service

### Optimiser pour mobile

1. Réduis le nombre de fields dans Discord embed
2. Utilise des emojis clairs
3. Limite le texte à 1-2 lignes par field

---

## 📞 Support personnalisé

Si tu veux ajouter une feature spécifique non couverte ici, les points d'entrée principaux sont :

- **Collecte de métriques** : `src/utils/metrics.py`
- **Analyse Docker** : `src/utils/docker_client.py`
- **Logique de rapport** : `src/reporter.py`
- **Format Discord** : `generate_discord_embed()` dans `reporter.py`

---

Bon customizing ! 🎨✨
