# 🚀 Guida per Caricare il Progetto su GitHub

## Passo 1: Crea il Repository su GitHub

1. Vai su [https://github.com/new](https://github.com/new)
2. Compila i campi:
   - **Repository name**: `cognitive-pid-framework` (o un altro nome)
   - **Description**: "Autonomous AI-driven software development using PID feedback control"
   - **Visibility**: Scegli Public o Private
   - ⚠️ **NON** selezionare:
     - ❌ Add a README file
     - ❌ Add .gitignore
     - ❌ Choose a license
   (Questi file esistono già nel progetto)
3. Clicca **"Create repository"**

## Passo 2: Configura il Remote e Fai Push

### Opzione A: Usa lo Script Automatico (Consigliato)

```powershell
# Esegui lo script
.\setup_github.ps1

# Quando richiesto, incolla l'URL del tuo repository GitHub
# Esempio: https://github.com/tuousername/cognitive-pid-framework.git
```

### Opzione B: Comandi Manuali

```powershell
# 1. Aggiungi il remote (sostituisci con il tuo URL)
git remote add origin https://github.com/TUO_USERNAME/cognitive-pid-framework.git

# Se il remote esiste già, aggiornalo:
# git remote set-url origin https://github.com/TUO_USERNAME/cognitive-pid-framework.git

# 2. Rinomina il branch in 'main' (se necessario)
git branch -M main

# 3. Fai push
git push -u origin main
```

## Passo 3: Verifica

Dopo il push, visita il tuo repository su GitHub:
- Dovresti vedere tutti i file del progetto
- Il README.md dovrebbe essere visualizzato correttamente
- I commit dovrebbero essere visibili nella cronologia

## 🔐 Autenticazione GitHub

Se GitHub richiede autenticazione:

### Opzione 1: Personal Access Token (Consigliato)
1. Vai su [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Clicca "Generate new token (classic)"
3. Seleziona gli scope: `repo` (tutti)
4. Copia il token generato
5. Quando Git chiede la password, usa il token invece della password

### Opzione 2: GitHub CLI
```powershell
# Installa GitHub CLI
winget install GitHub.cli

# Autenticati
gh auth login

# Poi fai push normalmente
git push -u origin main
```

### Opzione 3: SSH Key
```powershell
# Genera una chiave SSH (se non ce l'hai)
ssh-keygen -t ed25519 -C "tua-email@example.com"

# Aggiungi la chiave pubblica a GitHub
# Settings > SSH and GPG keys > New SSH key

# Usa l'URL SSH invece di HTTPS:
git remote set-url origin git@github.com:TUO_USERNAME/cognitive-pid-framework.git
```

## 📝 Note Importanti

- **Non committare file sensibili**: Il file `.env` è già nel `.gitignore`
- **Non committare il venv**: La cartella `venv/` è già ignorata
- **Logs e checkpoints**: Le cartelle `logs/` e `checkpoints/` sono ignorate

## 🐛 Risoluzione Problemi

### Errore: "remote origin already exists"
```powershell
git remote remove origin
git remote add origin https://github.com/TUO_USERNAME/cognitive-pid-framework.git
```

### Errore: "failed to push some refs"
```powershell
# Se il repository GitHub ha già dei file, fai pull prima:
git pull origin main --allow-unrelated-histories
# Risolvi eventuali conflitti, poi:
git push -u origin main
```

### Errore di autenticazione
- Verifica di avere i permessi sul repository
- Usa un Personal Access Token invece della password
- Controlla che l'URL del repository sia corretto

## ✅ Checklist Finale

- [ ] Repository creato su GitHub
- [ ] Remote configurato
- [ ] Push completato con successo
- [ ] File visibili su GitHub
- [ ] README.md visualizzato correttamente

## 🎉 Fatto!

Il tuo progetto è ora su GitHub! Puoi condividerlo, collaborare e ricevere contributi.

