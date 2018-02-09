function ZipFiles( $zipfilename, $sourcedir ) {
   Add-Type -Assembly System.IO.Compression.FileSystem
   $compressionLevel = [System.IO.Compression.CompressionLevel]::Optimal
   [System.IO.Compression.ZipFile]::CreateFromDirectory(
     $sourcedir, $zipfilename, $compressionLevel, $true)
}

function Clean( $projectroot, $version ) {
    Remove-Item "$projectroot\build" -Recurse -ErrorAction Ignore
    Remove-Item "$projectroot\dist" -Recurse -ErrorAction Ignore
    Remove-Item "$projectroot\pyportify.zip" -ErrorAction Ignore
    Remove-Item "$projectroot\pyportify-$version" -Recurse -ErrorAction Ignore
}

function BuildAndRunExe( $pyroot ) {
  Invoke-Expression "$pyroot\pyinstaller --onefile pyportify.spec"
  dist\pyportify.exe
}

function Build( $projectroot, $version, $pyroot ) {
    Invoke-Expression "$pyroot\pyinstaller --onefile pyportify.spec"
    move-item dist pyportify-$version
    ZipFiles "$projectroot\pyportify.zip" "$projectroot\pyportify-$version"
}

$version = "0.4.1"

$pyroot = "c:\Users\josh\virtualenvs\pyportify36\Scripts"
$projectroot = $PSScriptRoot
$env:PYTHONPATH = "$projectroot"

Clean $projectroot $version
Build $projectroot $version $pyroot
# BuildAndRunExe $pyroot
