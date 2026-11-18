# Empacota o projecto para entrega no Windows. Executar a partir de qualquer pasta.
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Name = 'IA1_PROJECTO_GRUPO_06_LAB'
$Destination = if ($args.Count -gt 0) {
    [System.IO.Path]::GetFullPath($args[0])
} else {
    Split-Path -Parent $ProjectRoot
}
$ZipPath = Join-Path $Destination ($Name + '.zip')

if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot '.git'))) {
    throw "Repositório .git não encontrado em $ProjectRoot"
}

$GitStatus = git -C $ProjectRoot status --short
if ($LASTEXITCODE -ne 0) {
    throw 'Não foi possível consultar o estado Git.'
}
if ($GitStatus) {
    Write-Warning 'Existem alterações por commitar. O ZIP incluirá os ficheiros, mas o histórico Git não incluirá essas alterações.'
}

New-Item -ItemType Directory -Force -Path $Destination | Out-Null
if (Test-Path -LiteralPath $ZipPath) {
    Remove-Item -LiteralPath $ZipPath -Force
}

$Exclude = @(
    '.venv', 'venv', 'env', '__pycache__', '.pytest_cache',
    '.mypy_cache', '.ruff_cache', 'lo_perfil'
)

$Files = Get-ChildItem -LiteralPath $ProjectRoot -Force -Recurse -File |
    Where-Object {
        $relative = [System.IO.Path]::GetRelativePath($ProjectRoot, $_.FullName)
        $parts = $relative -split '[\\/]'
        $relative -notmatch '\.py[co]$' -and
        $relative -notmatch '\.tmp$' -and
        -not ($parts | Where-Object { $_ -in $Exclude })
    }

if (-not ($Files | Where-Object { $_.Name -eq 'resultados.csv' })) {
    Write-Warning 'resultados.csv não foi encontrado.'
}
if (-not ($Files | Where-Object { $_.Name -eq 'Relatorio_Grupo06_P6.pdf' })) {
    Write-Warning 'Relatório PDF não encontrado.'
}

$ProjectFolder = Split-Path $ProjectRoot -Leaf
Add-Type -AssemblyName System.IO.Compression

$stream = [System.IO.File]::Open(
    $ZipPath,
    [System.IO.FileMode]::CreateNew
)

try {
    $archive = [System.IO.Compression.ZipArchive]::new(
        $stream,
        [System.IO.Compression.ZipArchiveMode]::Create
    )

    try {
        foreach ($file in $Files) {
            $relative = [System.IO.Path]::GetRelativePath(
                $ProjectRoot,
                $file.FullName
            ).Replace('\', '/')

            $entryName = "$ProjectFolder/$relative"

            [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
                $archive,
                $file.FullName,
                $entryName,
                [System.IO.Compression.CompressionLevel]::Optimal
            ) | Out-Null
        }
    }
    finally {
        $archive.Dispose()
    }
}
finally {
    $stream.Dispose()
}

$check = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)
try {
    $hasGit = [bool](
        $check.Entries |
            Where-Object { $_.FullName -like '*/.git/*' }
    )
    Write-Output "Criado: $ZipPath"
    Write-Output "Ficheiros incluídos: $($check.Entries.Count)"
    Write-Output "Inclui histórico .git: $hasGit"
}
finally {
    $check.Dispose()
}