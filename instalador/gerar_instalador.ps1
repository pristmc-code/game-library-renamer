# ============================================================
#  Gera o instalador do Game Library Renamer
#  Requisitos: Python com pyinstaller, paramiko e pillow; Inno Setup 6.
#  Uso (na pasta instalador):  powershell -ExecutionPolicy Bypass -File gerar_instalador.ps1
#  Saida: instalador\saida\GameLibraryRenamer_<versao>_Setup.exe (versao = VERSAO do ftp_ps5.py)
# ============================================================
$ErrorActionPreference = "Stop"
$instalador = $PSScriptRoot
$projeto    = Split-Path $instalador -Parent
$trabalho   = Join-Path $env:TEMP "GameLibraryRenamer_build"
$dist       = Join-Path $trabalho "dist"

# 0) Versao: fonte unica e o VERSAO do ftp_ps5.py; replica no recurso do .exe (versao.txt)
$versao = [regex]::Match((Get-Content (Join-Path $projeto "ftp_ps5.py") -Raw), 'VERSAO = "([\d.]+)"').Groups[1].Value
if (-not $versao) { throw "VERSAO nao encontrada no ftp_ps5.py" }
$partes = ($versao.Split(".") + @("0", "0", "0"))[0..3]
$arqVersao = Join-Path $instalador "versao.txt"
$conteudo = Get-Content $arqVersao -Raw
$conteudo = $conteudo -replace 'filevers=\([\d, ]+\)', "filevers=($($partes -join ', '))" `
                      -replace 'prodvers=\([\d, ]+\)', "prodvers=($($partes -join ', '))" `
                      -replace "'FileVersion', '[\d.]+'", "'FileVersion', '$($partes -join '.')'" `
                      -replace "'ProductVersion', '[\d.]+'", "'ProductVersion', '$versao'"
Set-Content -Path $arqVersao -Value $conteudo -Encoding UTF8 -NoNewline
Write-Host "Versao: $versao"

# Instaladores de versoes anteriores vao para saida\anteriores
$saida = Join-Path $instalador "saida"
if (Test-Path $saida) {
    $anteriores = Join-Path $saida "anteriores"
    Get-ChildItem $saida -Filter "*_Setup.exe" | Where-Object Name -ne "GameLibraryRenamer_${versao}_Setup.exe" | ForEach-Object {
        New-Item -ItemType Directory -Force $anteriores | Out-Null
        Move-Item $_.FullName $anteriores -Force
    }
}

# 1) Icone (gera de novo se faltar)
if (-not (Test-Path (Join-Path $instalador "icone.ico"))) { python (Join-Path $instalador "gerar_icone.py") }

# 2) Executavel (pasta com GameLibraryRenamer.exe + _internal), compilado fora do Google Drive
if (Test-Path $trabalho) { Remove-Item -Recurse -Force $trabalho }
Push-Location $projeto
try {
    python -m PyInstaller --noconfirm --clean --windowed --name GameLibraryRenamer `
        --icon "$instalador\icone.ico" --version-file "$instalador\versao.txt" `
        --add-data "$projeto\app_ps5.html;." --add-data "$instalador\icone.ico;." `
        --hidden-import paramiko `
        --distpath $dist --workpath "$trabalho\build" --specpath "$trabalho\build" app_ps5.py
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller falhou" }
} finally { Pop-Location }

# 3) Instalador (Inno Setup)
$iscc = @("$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
          "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
          "$env:ProgramFiles\Inno Setup 6\ISCC.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) { throw "Inno Setup 6 nao encontrado (winget install JRSoftware.InnoSetup)" }
& $iscc "/DDistDir=$dist\GameLibraryRenamer" "/DAppVersao=$versao" (Join-Path $instalador "GameLibraryRenamer.iss")
if ($LASTEXITCODE -ne 0) { throw "Inno Setup falhou" }

Get-ChildItem $saida -File | Select-Object Name, Length, LastWriteTime
