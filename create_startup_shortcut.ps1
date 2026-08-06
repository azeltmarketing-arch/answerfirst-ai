$WshShell = New-Object -ComObject WScript.Shell
$Startup = [Environment]::GetFolderPath('Startup')
$Shortcut = $WshShell.CreateShortcut("$Startup\AnswerFirst AI 24-7.lnk")
$Shortcut.TargetPath = 'C:\Users\azelt\answerfirst-ai\start_24_7.bat'
$Shortcut.WorkingDirectory = 'C:\Users\azelt\answerfirst-ai'
$Shortcut.WindowStyle = 7
$Shortcut.Save()
Write-Output "Shortcut created at $Startup\AnswerFirst AI 24-7.lnk"
