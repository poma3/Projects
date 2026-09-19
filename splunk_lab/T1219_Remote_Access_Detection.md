Description: Cài môi trường và viết Rules cho T1219-Remote Access Software, tạo Dashboard

### 1. Thiết lập môi trường

[https://github.com/redcanaryco/atomic-red-team/blob/master/atomics/T1219/T1219.md](https://github.com/redcanaryco/atomic-red-team/blob/master/atomics/T1219/T1219.md)

#### Test 1: TeamViewer Files Detected Test on Windows

- Attack Commands: Run with `powershell`! Elevation Required (e.g. root or admin)
  ```powershell
  Invoke-WebRequest -OutFile C:\Users\$env:username\Desktop\TeamViewer_Setup.exe https://download.teamviewer.com/download/TeamViewer_Setup.exe
  $file1 = "C:\Users\" + $env:username + "\Desktop\TeamViewer_Setup.exe"
  Start-Process -Wait $file1 /S;
  Start-Process 'C:\Program Files (x86)\TeamViewer\TeamViewer.exe'
  ```
- Cleanup Commands
  ```powershell
  $file = 'C:\Program Files (x86)\TeamViewer\uninstall.exe'
  if(Test-Path $file){ Start-Process $file "/S" -ErrorAction Ignore | Out-Null }
  $file1 = "C:\Users\" + $env:username + "\Desktop\TeamViewer_Setup.exe"
  Remove-Item $file1 -ErrorAction Ignore | Out-Null
  ```

#### Test 2: AnyDesk Files Detected Test on Windows

- Attack Commands: Run with `powershell`! Elevation Required (e.g. root or admin)
  ```powershell
  Invoke-WebRequest -OutFile C:\Users\$env:username\Desktop\AnyDesk.exe https://download.anydesk.com/AnyDesk.exe
  $file1 = "C:\Users\" + $env:username + "\Desktop\AnyDesk.exe"
  Start-Process $file1 /S;
  echo "password123" | & "C:\Users\$env:username\Desktop\AnyDesk.exe" --admin-settings --set-password
  ```
- Cleanup Commands
  ```powershell
  $file1 = "C:\Users\" + $env:username + "\Desktop\AnyDesk.exe"
  Remove-Item $file1 -ErrorAction Ignore
  ```

### 2. SPL

- Detect processes và commandline
  ```powershell
  index=sysmon sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=1
  ("TeamViewer" OR "AnyDesk" OR "ScreenConnect" OR "ammyy")
  | regex Image="(?i)(teamviewer.*|anydesk.*|screenconnect.*|ammyy.*)\.exe$"
  | table _time, host, Image, User, CommandLine
  ```
  ![image.png](images/image%206.png)
- Detect process và commandline chạy ở chế độ ẩn
  ```powershell
  index=sysmon sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=1
  ("TeamViewer" OR "AnyDesk" OR "ScreenConnect" OR "ammyy")
  | where match(lower(Image), "(teamviewer.*|anydesk.*|screenconnect.*|ammyy.*)\.exe$")
  | where match(lower(CommandLine), "\s+(\/s|\-\-silent|\-\-install|\-\-start\-with\-win|\-quiet|\-slient)(\s+|$)")
  | table _time, host, Image, User, CommandLine
  ```
  ![image.png](images/image%207.png)
- Phát hiện Pipe mật khẩu vào AnyDesk qua CLI
  ```powershell
  index=sysmon sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=1 CommandLine="*AnyDesk*"
  | where match(lower(CommandLine), "--set-password")
  | table _time, host, User, Image, CommandLine
  ```
  ![image.png](images/image%208.png)

### 3. Dashboard

![image.png](images/image%209.png)

- Ý nghĩa khi tạo Dashboard
  - Total Infected Host: có bao nhiêu máy bị xâm phạm
  - Malicious Activity:
    - Static Password Configured: Cảnh báo hacker đã thiết lập mật khẩu cố định để duy trì quyền truy cập vĩnh viễn.
    - Artefact Creation: Phát hiện dấu vết file cấu hình ngầm rơi xuống ổ cứng.
    - Other Remote Activity: Các hành vi kích hoạt thông thường.
  - Remote Access Activity Trend: giám sát dòng thời gian và xu hướng hoạt động của các phần mềm từ xa.
- Các data source
  ```powershell
  index=sysmon EventCode=1 $software_tok$ | stats dc(host) as count
  ```
  ```powershell
  index=sysmon (EventCode=1 OR EventCode=11) $software_tok$

  | eval Behavior=case(
      match(CommandLine, "powershell.*\.ps1"), "PowerShell Script Execution",
      match(CommandLine, "AnyDesk\.exe.*--set-password"), "Static Password Configured",

      (EventCode=11 AND (
          match(TargetFilename, "ScreenConnect") OR
          match(TargetFilename, "anydesk\.cfg") OR
          match(TargetFilename, "TeamViewer.*\.log") OR
          match(TargetFilename, "UltraViewer.*\.ini")
      )), "Artefact Creation",

      1=1, "Other Remote Activity"
    )
  | stats count by Behavior
  ```
  ```powershell
  index=sysmon EventCode=1 $software_tok$

  | eval Software=case(
      match(CommandLine, "AnyDesk"), "AnyDesk",
      match(CommandLine, "TeamViewer"), "TeamViewer",
      match(CommandLine, "ScreenConnect"), "ScreenConnect",
      1=1, "Other RMM"
    )
  | timechart span=1h count by Software
  ```
