# Script per configurare GitHub per Cognitive PID Framework

Write-Host "=== Setup GitHub Repository ===" -ForegroundColor Cyan
Write-Host ""

# Chiedi l'URL del repository GitHub
$repoUrl = Read-Host "Incolla l'URL del tuo repository GitHub (es: https://github.com/tuousername/cognitive-pid-framework.git)"

if ([string]::IsNullOrWhiteSpace($repoUrl)) {
    Write-Host "Errore: URL del repository non fornito" -ForegroundColor Red
    exit 1
}

# Aggiungi remote
Write-Host "Aggiungo remote 'origin'..." -ForegroundColor Yellow
git remote add origin $repoUrl

if ($LASTEXITCODE -ne 0) {
    # Se esiste già, prova a cambiarlo
    Write-Host "Remote 'origin' esiste già, lo aggiorno..." -ForegroundColor Yellow
    git remote set-url origin $repoUrl
}

# Verifica remote
Write-Host ""
Write-Host "Remote configurato:" -ForegroundColor Green
git remote -v

# Push al repository
Write-Host ""
Write-Host "Eseguo push su GitHub..." -ForegroundColor Yellow
git branch -M main
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Successo! Il progetto è stato caricato su GitHub!" -ForegroundColor Green
    Write-Host "Visita: $repoUrl" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "❌ Errore durante il push. Verifica:" -ForegroundColor Red
    Write-Host "  1. Hai creato il repository su GitHub?" -ForegroundColor Yellow
    Write-Host "  2. Hai i permessi per pushare?" -ForegroundColor Yellow
    Write-Host "  3. L'URL del repository è corretto?" -ForegroundColor Yellow
}

