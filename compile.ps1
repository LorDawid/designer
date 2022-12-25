cd ..\designercompiled
pyinstaller --noconfirm --windowed "..\designer\launcher.py"
xcopy ..\designer\icons\light\ .\dist\launcher\icons\light\
xcopy ..\designer\icons\dark\ .\dist\launcher\icons\dark\
xcopy ..\designer\styles\ .\dist\launcher\styles\
xcopy ..\designer\recentProjects.json .\dist\launcher\ 
xcopy ..\designer\settings.json .\dist\launcher\