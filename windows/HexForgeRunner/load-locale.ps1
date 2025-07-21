function Load-IniFile {
    param (
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $ini = @{}
    $section = ''

    foreach ($line in Get-Content $Path) {
        $trimmed = $line.Trim()

        if ($trimmed -match '^\[(.+?)\]$') {
            $section = $matches[1]
            $ini[$section] = @{}
        } elseif ($trimmed -match '^\s*([^=]+?)\s*=\s*(.*?)\s*$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            if ($section) {
                $ini[$section][$key] = $value
            }
        }
    }

    return $ini
}

# Set locale file path
$localeFile = Join-Path $PSScriptRoot "locale\en-US.ini"


# Verify existence
if (-Not (Test-Path $localeFile)) {
    [System.Windows.Forms.MessageBox]::Show("❌ Missing locale file: `n`n$localeFile", "HexForge Error", "OK", "Error")
    exit 1
}

# Load and return locale data
$Locale = Load-IniFile -Path $localeFile
return $Locale
