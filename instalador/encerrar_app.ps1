# ============================================================
#  Encerra o Game Library Renamer antes de atualizar ou desinstalar (chamado pelo instalador).
#  O app roda em segundo plano (sem janela propria), entao o Windows nao consegue fecha-lo
#  sozinho e os arquivos ficariam presos. So mexe nos processos DESTA instalacao.
#  Uso: powershell -NoProfile -ExecutionPolicy Bypass -File encerrar_app.ps1 -Pasta "<pasta do app>"
# ============================================================
param([Parameter(Mandatory = $true)][string]$Pasta)
$Pasta = $Pasta.TrimEnd('\')

# 1) Pede para o app sair (fecha a janela dele junto).
try {
    Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8765/api/sair' -ContentType 'application/json' `
        -Body '{}' -TimeoutSec 3 | Out-Null
    Start-Sleep -Seconds 2
} catch { }

# 2) Se ainda estiver rodando a partir desta pasta, encerra a forca.
Get-Process GameLibraryRenamer -ErrorAction SilentlyContinue |
    Where-Object { $_.Path -and $_.Path.StartsWith($Pasta, [StringComparison]::OrdinalIgnoreCase) } |
    Stop-Process -Force -ErrorAction SilentlyContinue

# 3) Fecha a janela do app (Edge/Chrome com o perfil 'janela' desta pasta) - nunca o navegador do usuario.
$perfil = "$Pasta\janela"
Get-CimInstance Win32_Process -Filter "Name='msedge.exe' or Name='chrome.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -and $_.CommandLine.IndexOf($perfil, [StringComparison]::OrdinalIgnoreCase) -ge 0 } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 1
