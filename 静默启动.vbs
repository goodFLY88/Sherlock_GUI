' Start Sherlock GUI with no console window at all.
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
base = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = base
script = fso.BuildPath(base, "gui.pyw")
pyw = fso.BuildPath(base, ".venv\Scripts\pythonw.exe")
If fso.FileExists(pyw) Then
    WshShell.Run """" & pyw & """ """ & script & """", 0, False
Else
    WshShell.Run "pythonw """ & script & """", 0, False
End If
