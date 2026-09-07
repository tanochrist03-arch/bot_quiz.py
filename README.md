# Telegram Quiz Bot

Bot interactif de culture générale développé en Python (`pyTelegramBotAPI`) et déployable sur Railway.

## Variables d'Environnement

* `TELEGRAM_BOT_TOKEN` : Jeton d'authentification fourni par @BotFather (**Obligatoire**).
* `PORT` : Port réseau attribué automatiquement par Railway (défaut : `8080`).

## Avertissement Déploiement

Ce bot utilise le **Long Polling**. Vous devez déployer **une seule instance (1 réplique)** du conteneur. Si plusieurs instances s'exécutent simultanément, Telegram renverra une erreur `401/409 Conflict`.