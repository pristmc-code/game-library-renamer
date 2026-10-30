; ============================================================
;  Instalador do Game Library Renamer (Inno Setup 6)
;  Compilar:  "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" GameLibraryRenamer.iss
;  Entrada:   pasta do PyInstaller (GameLibraryRenamer.exe + _internal), passada em /DDistDir=...
;  Saida:     instalador\saida\GameLibraryRenamer_<versao>_Setup.exe
; ============================================================

#define AppNome    "Game Library Renamer"
#ifndef AppVersao
  #define AppVersao  "1.2"
#endif
#define AppExe     "GameLibraryRenamer.exe"
; Nome de atalho/pasta do menu: sem "/" (o Windows trataria como subpasta)
#define AppAtalho  "Game Library Renamer"
#ifndef DistDir
  #define DistDir  "dist\GameLibraryRenamer"
#endif

[Setup]
AppId={{6E2C1B8A-4F7D-4C1E-9A3B-2D5F8E7C9B10}
AppName={#AppNome}
AppVersion={#AppVersao}
AppVerName={#AppNome} {#AppVersao}
AppPublisher=PristMC
VersionInfoVersion={#AppVersao}
; Instala por usuario (sem pedir administrador): a pasta do app precisa ser gravavel,
; porque o INI, o cache, a base de titulos e os icones ficam ao lado do .exe.
PrivilegesRequired=lowest
; A pasta e so do app: instalar numa pasta que ja existe (ex.: vazia, de uma desinstalacao) e seguro.
DirExistsWarning=no
DefaultDirName={localappdata}\Programs\Game Library Renamer
DefaultGroupName={#AppAtalho}
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppNome} {#AppVersao}
SetupIconFile=icone.ico
OutputDir=saida
OutputBaseFilename=GameLibraryRenamer_{#AppVersao}_Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ShowLanguageDialog=yes
; Idioma padrao do instalador = ingles (o usuario ainda pode trocar na primeira tela).
LanguageDetectionMethod=none
; Fecha o app (que roda em segundo plano) antes de atualizar ou desinstalar.
CloseApplications=force

[Languages]
; Ingles primeiro = idioma padrao (com LanguageDetectionMethod=none o Windows nao escolhe outro).
Name: "en";   MessagesFile: "compiler:Default.isl"
Name: "ptbr"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "es";   MessagesFile: "compiler:Languages\Spanish.isl"

[CustomMessages]
ptbr.IdiomaApp=pt-BR
en.IdiomaApp=en
es.IdiomaApp=es
ptbr.AbrirApp=Abrir o {#AppNome}
en.AbrirApp=Open {#AppNome}
es.AbrirApp=Abrir {#AppNome}
; Tela "ja instalado" (%1 = versao instalada, %2 = versao deste instalador)
ptbr.JaInstaladoTitulo=O {#AppNome} já está instalado
en.JaInstaladoTitulo={#AppNome} is already installed
es.JaInstaladoTitulo={#AppNome} ya está instalado
ptbr.JaInstaladoTexto=Versão instalada: %1%nVersão deste instalador: %2%n%nO que você deseja fazer?
en.JaInstaladoTexto=Installed version: %1%nThis installer version: %2%n%nWhat would you like to do?
es.JaInstaladoTexto=Versión instalada: %1%nVersión de este instalador: %2%n%n¿Qué desea hacer?
ptbr.BtnAtualizar=Atualizar / reinstalar (mantém as configurações)
en.BtnAtualizar=Update / reinstall (keeps settings)
es.BtnAtualizar=Actualizar / reinstalar (mantiene la configuración)
ptbr.BtnDesinstalar=Desinstalar
en.BtnDesinstalar=Uninstall
es.BtnDesinstalar=Desinstalar
ptbr.BtnCancelar=Cancelar
en.BtnCancelar=Cancel
es.BtnCancelar=Cancelar
ptbr.ErroDesinstalar=Não foi possível iniciar o desinstalador:%n%1
en.ErroDesinstalar=Could not start the uninstaller:%n%1
es.ErroDesinstalar=No se pudo iniciar el desinstalador:%n%1
; Desinstalacao pedida pelo instalador (a pergunta fica nele, que esta em primeiro plano)
ptbr.ConfirmaDesinstalar=O {#AppNome} será desinstalado.%n%nDeseja apagar também todos os dados dele?%nConfigurações (incluindo endereço e senha do PS5), cache, base de jogos, capas e perfil da janela.%n%nSim = desinstalar e apagar os dados%nNão = desinstalar e manter as configurações%nCancelar = não desinstalar
en.ConfirmaDesinstalar={#AppNome} will be uninstalled.%n%nDo you also want to delete all of its data?%nSettings (including the PS5 address and password), cache, game database, covers and window profile.%n%nYes = uninstall and delete the data%nNo = uninstall and keep the settings%nCancel = do not uninstall
es.ConfirmaDesinstalar=Se desinstalará {#AppNome}.%n%n¿Desea borrar también todos sus datos?%nConfiguración (incluida la dirección y contraseña de la PS5), caché, base de juegos, portadas y perfil de la ventana.%n%nSí = desinstalar y borrar los datos%nNo = desinstalar y mantener la configuración%nCancelar = no desinstalar
ptbr.Desinstalado=O {#AppNome} foi desinstalado.
en.Desinstalado={#AppNome} has been uninstalled.
es.Desinstalado={#AppNome} se ha desinstalado.
ptbr.FalhaDesinstalar=A desinstalação terminou com erro (código %1).
en.FalhaDesinstalar=The uninstall finished with an error (code %1).
es.FalhaDesinstalar=La desinstalación terminó con error (código %1).
; Pergunta no fim da desinstalacao
ptbr.ApagarDados=Deseja apagar também todos os dados do {#AppNome}?%n%nConfigurações (incluindo endereço e senha do PS5), cache, base de jogos, capas e perfil da janela.%n%nEscolha "Não" para manter as configurações caso vá instalar de novo.
en.ApagarDados=Do you also want to delete all {#AppNome} data?%n%nSettings (including the PS5 address and password), cache, game database, covers and window profile.%n%nChoose "No" to keep the settings if you plan to install again.
es.ApagarDados=¿Desea borrar también todos los datos de {#AppNome}?%n%nConfiguración (incluida la dirección y contraseña de la PS5), caché, base de juegos, portadas y perfil de la ventana.%n%nElija "No" para conservar la configuración si va a instalar de nuevo.

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "{#DistDir}\{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#DistDir}\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
; Encerra o app antes de atualizar/desinstalar (usado pelo [Code]).
Source: "encerrar_app.ps1"; DestDir: "{app}"; Flags: ignoreversion

[INI]
; Idioma da tela = idioma escolhido na instalacao (so na primeira vez; depois vale o seletor do app).
Filename: "{app}\GameLibraryRenamer.ini"; Section: "app"; Key: "language"; String: "{cm:IdiomaApp}"; Flags: createkeyifdoesntexist

[Icons]
; AppUserModelID = o mesmo que o app grava na janela (identidade_janela.py): agrupa e fixa com o nosso icone.
Name: "{group}\{#AppAtalho}"; Filename: "{app}\{#AppExe}"; AppUserModelID: "PristMC.GameLibraryRenamer"
Name: "{group}\{cm:UninstallProgram,{#AppAtalho}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppAtalho}"; Filename: "{app}\{#AppExe}"; AppUserModelID: "PristMC.GameLibraryRenamer"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:AbrirApp}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove o que o app gerou (o GameLibraryRenamer.ini e mantido, pois guarda a configuracao do usuario).
Type: files;          Name: "{app}\cache_consultas.json"
Type: files;          Name: "{app}\cache_consultas.tmp"
Type: files;          Name: "{app}\base_titulos.tsv"
Type: files;          Name: "{app}\base_titulos.tmp"
Type: files;          Name: "{app}\base_titulos.json"
Type: filesandordirs; Name: "{app}\icones"
; Perfil da janela do app (Edge/Chrome em modo aplicativo).
Type: filesandordirs; Name: "{app}\janela"

[Code]
const
  { Chave de desinstalacao gravada pelo Inno: AppId + "_is1" }
  ChaveDesinstalar = 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{6E2C1B8A-4F7D-4C1E-9A3B-2D5F8E7C9B10}_is1';

{ Procura uma instalacao existente (por usuario e, por garantia, na maquina). }
function InstalacaoExistente(var Versao, Desinstalador: String): Boolean;
begin
  Result := RegQueryStringValue(HKCU, ChaveDesinstalar, 'UninstallString', Desinstalador) or
            RegQueryStringValue(HKLM, ChaveDesinstalar, 'UninstallString', Desinstalador);
  if Result then
  begin
    if not (RegQueryStringValue(HKCU, ChaveDesinstalar, 'DisplayVersion', Versao) or
            RegQueryStringValue(HKLM, ChaveDesinstalar, 'DisplayVersion', Versao)) then
      Versao := '?';
  end;
end;

{ Ao abrir o instalador: se o app ja existe, pergunta se atualiza, desinstala ou cancela. }
function InitializeSetup(): Boolean;
var
  Versao, Desinstalador, PastaApp: String;
  Escolha, Codigo, Espera: Integer;
begin
  Result := True;
  if WizardSilent() or not InstalacaoExistente(Versao, Desinstalador) then
    Exit;

  { Obs.: no Inno, linha que comeca com "[" e lida como secao; por isso o array fica no fim da linha. }
  Escolha := TaskDialogMsgBox(CustomMessage('JaInstaladoTitulo'),
    FmtMessage(CustomMessage('JaInstaladoTexto'), [Versao, '{#AppVersao}']),
    mbConfirmation, MB_YESNOCANCEL, [CustomMessage('BtnAtualizar'), CustomMessage('BtnDesinstalar'), CustomMessage('BtnCancelar')], IDYES);

  case Escolha of
    IDYES:
      Result := True;  { segue a instalacao por cima (mesma pasta, INI preservado) }
    IDNO:
      begin
        { A pergunta fica aqui: o desinstalador aberto por este processo nao recebe o foco do Windows
          e a confirmacao dele aparecia minimizada, piscando na barra de tarefas. }
        Result := False;
        Escolha := MsgBox(CustomMessage('ConfirmaDesinstalar'), mbConfirmation, MB_YESNOCANCEL or MB_DEFBUTTON2);
        if Escolha = IDCANCEL then
          Exit;
        PastaApp := '';
        if not RegQueryStringValue(HKCU, ChaveDesinstalar, 'InstallLocation', PastaApp) then
          RegQueryStringValue(HKLM, ChaveDesinstalar, 'InstallLocation', PastaApp);
        { /SILENT: sem a confirmacao e sem a pergunta dos dados (ja respondida acima); espera terminar. }
        if not Exec(RemoveQuotes(Desinstalador), '/SILENT /NORESTART /SUPPRESSMSGBOXES', '', SW_SHOW,
                    ewWaitUntilTerminated, Codigo) then
        begin
          MsgBox(FmtMessage(CustomMessage('ErroDesinstalar'), [SysErrorMessage(Codigo)]), mbError, MB_OK);
          Exit;
        end;
        if Codigo <> 0 then
        begin
          MsgBox(FmtMessage(CustomMessage('FalhaDesinstalar'), [IntToStr(Codigo)]), mbError, MB_OK);
          Exit;
        end;
        PastaApp := RemoveBackslashUnlessRoot(PastaApp);
        { O unins000.exe se copia para a pasta temporaria e sai na hora: o desinstalador de verdade ainda
          esta rodando. Espera ele terminar (o unins000.exe some da pasta) antes de apagar o resto. }
        Espera := 0;
        while (PastaApp <> '') and FileExists(PastaApp + '\unins000.exe') and (Espera < 60) do
        begin
          Sleep(500);
          Espera := Espera + 1;
        end;
        if (Escolha = IDYES) and (PastaApp <> '') and DirExists(PastaApp) then
          DelTree(PastaApp, True, True, True);
        MsgBox(CustomMessage('Desinstalado'), mbInformation, MB_OK);
      end;
  else
    Result := False;   { Cancelar }
  end;
end;

{ Roda o encerrar_app.ps1 (fecha o app e a janela dele, que prenderiam os arquivos). }
procedure EncerrarApp(Script, PastaApp: String);
var
  Codigo: Integer;
begin
  if FileExists(Script) then
    Exec(ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe'),
      '-NoProfile -ExecutionPolicy Bypass -File "' + Script + '" -Pasta "' + PastaApp + '"',
      '', SW_HIDE, ewWaitUntilTerminated, Codigo);
end;

{ Antes de copiar os arquivos (instalacao/atualizacao): encerra o app que estiver rodando. }
function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  ExtractTemporaryFile('encerrar_app.ps1');
  EncerrarApp(ExpandConstant('{tmp}\encerrar_app.ps1'), WizardDirValue());
  Result := '';
end;

{ Antes de desinstalar: encerra o app (versoes ate a 2.1 nao instalavam o script; nelas o passo e pulado). }
function InitializeUninstall(): Boolean;
var
  Script: String;
begin
  Script := ExpandConstant('{app}\encerrar_app.ps1');
  EncerrarApp(Script, ExpandConstant('{app}'));
  Result := True;
end;

{ No fim da desinstalacao: pergunta se apaga tambem configuracoes e dados (padrao = Nao). }
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if (CurUninstallStep = usPostUninstall) and not UninstallSilent() then
    if MsgBox(CustomMessage('ApagarDados'), mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
      DelTree(ExpandConstant('{app}'), True, True, True);
end;
