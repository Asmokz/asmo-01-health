# 🤖 Claude Code Integration Guide (Phase 2)

## Vue d'ensemble

Cette phase ajoute l'analyse intelligente par Claude Code au système de monitoring. Au lieu d'avoir juste des statistiques brutes, Claude Code va :

1. **Analyser les patterns** : Détecter les corrélations entre événements
2. **Identifier les causes racines** : Relier les erreurs à leurs origines
3. **Proposer des solutions** : Recommandations concrètes et actionnables
4. **Prédire les problèmes** : Alerter avant que ça ne devienne critique

---

## 🎯 Architecture Phase 2

```
n8n Daily Report (9h) 
    ↓
1. Execute: reporter.py (génère rapport de base)
    ↓
2. Claude Code Analyze (analyse intelligente)
    ↓
3. Format & Enrich (combine analyse + métriques)
    ↓
4. Discord Webhook (rapport enrichi)
```

---

## 📝 Prompt Template pour Claude Code

Voici le prompt à utiliser dans n8n pour l'analyse Claude Code :

```
Tu es un expert en infrastructure et DevOps. Analyse ce rapport de santé serveur pour ASMO-01.

DONNÉES DES DERNIÈRES 24H:
{{ $json.analysis }}

CONTEXTE:
- Serveur homelab Ubuntu avec 24 containers Docker
- Services critiques : Jellyfin (media), Vaultwarden (passwords), Home Assistant
- Stack de monitoring : Grafana, Loki, Promtail, Netdata
- VPN via Gluetun pour certains services

TÂCHES:
1. Identifie les 3 problèmes les plus critiques
2. Pour chaque problème :
   - Explique la cause probable
   - Donne une solution concrète
   - Évalue l'urgence (basse/moyenne/haute)
3. Détecte les corrélations entre erreurs
4. Prédis les problèmes potentiels dans les 24h prochaines

FORMAT DE RÉPONSE:
Retourne un JSON avec cette structure:
{
  "summary": "Résumé en 2-3 phrases",
  "critical_issues": [
    {
      "container": "nom",
      "problem": "description",
      "cause": "cause probable",
      "solution": "action concrète",
      "urgency": "haute/moyenne/basse"
    }
  ],
  "correlations": [
    "Pattern 1: X cause Y",
    "Pattern 2: ..."
  ],
  "predictions": [
    "Risque 1: ...",
    "Risque 2: ..."
  ],
  "recommendations": [
    "Action 1: ...",
    "Action 2: ..."
  ]
}

Sois concis, technique, et actionnable. Focus sur les vraies causes, pas les symptômes.
```

---

## 🔧 Mise en place dans n8n

### Workflow mis à jour : Daily Report avec Claude Code

**Nodes** :

1. **Schedule Trigger**
   - Cron: `0 9 * * *`

2. **Execute Command** (SSH) - Reporter de base
   - Command: `python3 /home/asmo/scripts/asmo-health/src/reporter.py --debug`

3. **Code Node** - Prepare Claude Code Input
   ```javascript
   // Extraire les données d'analyse pour Claude
   const analysis = $input.item.json.analysis;
   
   return [{
     json: {
       analysis: JSON.stringify(analysis, null, 2)
     }
   }];
   ```

4. **Claude Code Node** (ou HTTP Request vers API Anthropic)
   - Utilise le prompt template ci-dessus
   - Model: `claude-sonnet-4-20250514`
   - Max tokens: 2000

5. **Code Node** - Parse Claude Response
   ```javascript
   // Parser la réponse de Claude
   const claudeResponse = $input.item.json.response;
   let analysis;
   
   try {
     // Claude retourne parfois du markdown avec ```json
     const jsonMatch = claudeResponse.match(/```json\n([\s\S]*?)\n```/);
     if (jsonMatch) {
       analysis = JSON.parse(jsonMatch[1]);
     } else {
       analysis = JSON.parse(claudeResponse);
     }
   } catch (e) {
     // Fallback si parsing échoue
     analysis = {
       summary: claudeResponse,
       error: "Could not parse JSON"
     };
   }
   
   return [{ json: { claude_analysis: analysis }}];
   ```

6. **Code Node** - Build Enhanced Embed
   ```javascript
   // Combiner les données du reporter + analyse Claude
   const baseData = $('Execute Command').item.json;
   const claudeAnalysis = $input.item.json.claude_analysis;
   
   const embed = {
     embeds: [{
       title: "🤖 ASMO-01 • Enhanced 24h Report (AI-Powered)",
       description: claudeAnalysis.summary || "Analysis complete",
       fields: [
         // Field 1: Critical Issues (Claude)
         {
           name: "🔥 Critical Issues (AI Analysis)",
           value: claudeAnalysis.critical_issues
             ?.slice(0, 3)
             .map(i => `**${i.container}**: ${i.problem}\n💡 ${i.solution}`)
             .join('\n\n') || "None detected",
           inline: false
         },
         // Field 2: Correlations
         {
           name: "🔗 Detected Patterns",
           value: claudeAnalysis.correlations
             ?.slice(0, 3)
             .map(c => `• ${c}`)
             .join('\n') || "None",
           inline: false
         },
         // Field 3: Predictions
         {
           name: "🔮 Predictive Alerts",
           value: claudeAnalysis.predictions
             ?.slice(0, 2)
             .map(p => `⚠️ ${p}`)
             .join('\n') || "All clear",
           inline: false
         },
         // Field 4: Original metrics (from reporter)
         {
           name: "📊 System Stats",
           value: `CPU: ${baseData.analysis.trends.cpu.avg}% avg\nRAM: ${baseData.analysis.trends.ram.avg}% avg\nContainers: ${baseData.analysis.trends.data_points} datapoints`,
           inline: true
         },
         // Field 5: Top recommendations
         {
           name: "✅ Recommendations",
           value: claudeAnalysis.recommendations
             ?.slice(0, 3)
             .map(r => `• ${r}`)
             .join('\n') || "Keep monitoring",
           inline: false
         }
       ],
       footer: {
         text: `AI Analysis by Claude Code • ${new Date().toLocaleString()}`
       },
       color: 5814783 // Purple for AI-enhanced
     }]
   };
   
   return [{ json: { embed }}];
   ```

7. **HTTP Request** - Discord Webhook
   - Method: POST
   - URL: `{{ $env.DISCORD_WEBHOOK_URL }}`
   - Body: `{{ $json.embed }}`

---

## 🧪 Test du workflow complet

```bash
# 1. Génère un rapport de base
python3 src/reporter.py --debug > /tmp/report.json

# 2. Copie l'analyse dans le clipboard

# 3. Paste dans claude.ai ou Claude Code avec le prompt

# 4. Vérifie que la réponse est bien en JSON

# 5. Test le workflow n8n en mode manuel
```

---

## 📊 Exemple de sortie enrichie

```json
{
  "summary": "Système globalement stable avec 3 points d'attention : Jellyfin subit des locks SQLite durant les scans nocturnes, Gluetun a des timeouts PMP intermittents, et Homarr consomme plus de RAM que nécessaire.",
  
  "critical_issues": [
    {
      "container": "jellyfin",
      "problem": "47 erreurs SQLite 'database locked' entre 2h-4h",
      "cause": "Concurrent access pendant les imports Radarr/Sonarr",
      "solution": "Décaler le scan Jellyfin à 5h OU utiliser PostgreSQL au lieu de SQLite",
      "urgency": "moyenne"
    },
    {
      "container": "gluetun",
      "problem": "Port forwarding errors (PMP connection refused)",
      "cause": "Configuration OpenVPN username manquante: besoin de +pmp suffix",
      "solution": "Ajouter +pmp à la fin de OPENVPN_USER dans docker-compose",
      "urgency": "basse"
    }
  ],
  
  "correlations": [
    "Jellyfin errors spike exactement quand Radarr/Sonarr sont actifs (2-4h)",
    "Homarr RAM usage élevé corrélé avec fetch errors vers services externes"
  ],
  
  "predictions": [
    "Si les scans restent simultanés, risque de corruption DB Jellyfin sous 7 jours",
    "Gluetun port forwarding va affecter les download speeds qBittorrent"
  ],
  
  "recommendations": [
    "Schedules: Décaler Jellyfin scan task dans settings à 5h du matin",
    "Gluetun: Éditer docker-compose.yml, ajouter +pmp au username, restart container",
    "Homarr: Activer module caching pour réduire fetch vers APIs externes",
    "Monitoring: Ajouter healthcheck SQLite pour Jellyfin dans docker-compose"
  ]
}
```

---

## 🚀 Avantages de l'approche Claude Code

### Avant (reporter.py seul)
```
⚠️ Issues Detected:
• jellyfin: Uptime: 98%, 0 restarts, 47 error types
• gluetun: 12 error types
```
→ On voit qu'il y a un problème, mais quoi faire ? 🤷

### Après (avec Claude Code)
```
🔥 Critical Issues (AI Analysis):
• jellyfin: 47 SQLite locks durant scans nocturnes
  💡 Solution: Décaler scan Jellyfin à 5h OU migrer vers PostgreSQL
  
🔗 Detected Patterns:
• Jellyfin errors spike when Radarr/Sonarr active (2-4h)

🔮 Predictive Alerts:
⚠️ Si les scans restent simultanés, risque de corruption DB sous 7 jours
```
→ Cause identifiée + solution concrète + prédiction ! ✨

---

## 🎯 Prochaines itérations

1. **Phase 2.1** : Ajouter analyse des tendances long-terme (7 jours)
2. **Phase 2.2** : Détection d'anomalies ML (patterns inhabituels)
3. **Phase 2.3** : Lien avec documentation interne (Bookstack)
4. **Phase 3** : Auto-remediation basée sur les recommandations Claude

---

## 💰 Coût estimé

- API Claude Code : ~$0.02 par analyse (1 appel/jour)
- Coût mensuel : ~$0.60
- Retour sur investissement : Gain de temps énorme + prévention d'incidents

---

## 📚 Ressources

- [Anthropic API Docs](https://docs.anthropic.com/claude/reference)
- [n8n Claude Node](https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.lmclaude/)
- [Prompt Engineering Guide](https://docs.anthropic.com/claude/docs/prompt-engineering)

---

Prêt à passer à la Phase 2 ? 🚀
