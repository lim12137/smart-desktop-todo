# Claude Code Updater 本地测试报告

## 测试目标

验证本地 Action 构建产物 `C:\Users\hopemyl\Downloads\claude-code-2.1.146-win-x64-updater.exe` 是否可正常解包并安装。

## 测试环境

- 时间：2026-05-22
- 系统：Windows
- 仓库：`C:\Users\hopemyl\Downloads\smart-desktop-todo\components\project\todo_reminder`

## 测试命令

```powershell
$exe='C:\Users\hopemyl\Downloads\claude-code-2.1.146-win-x64-updater.exe'
$dir=Join-Path $env:TEMP 'claude-updater-test'
Remove-Item $dir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $dir | Out-Null
$out=Join-Path $dir 'stdout.txt'
$err=Join-Path $dir 'stderr.txt'
$proc=Start-Process -FilePath $exe -ArgumentList $dir -RedirectStandardOutput $out -RedirectStandardError $err -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 12
if (-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force; Start-Sleep -Seconds 1 }
Get-Content $out
Get-Content $err
Get-ChildItem $dir -Force
```

## 测试结果摘要

- 产物可启动。
- 安装流程在读取内嵌资源阶段失败。
- 标准输出出现错误：`[ERROR] Embedded payload not found!`
- 未生成 `claude.exe`。

## 根因判断

GitHub Actions 工作流 `.github/workflows/claude-code-updater.yml` 中，安装器运行时代码用 `asm.GetName().Name + ".payload.b64"` 拼接资源名。

这个假设不稳定：SDK 风格 `csproj` 的嵌入资源名通常受 `RootNamespace`、目录结构、`LogicalName` 影响，不保证等于程序集名加文件名。因此运行时拿不到 `payload.b64`，导致产物启动后立即失败。

## 修复内容

1. 运行时代码改为遍历 `GetManifestResourceNames()`，按后缀匹配 `payload.b64`。
2. `csproj` 显式设置：
   - `RootNamespace` 为 `ClaudeUpdater`
   - `EmbeddedResource` 的 `LogicalName` 为 `payload.b64`
3. 当资源缺失时，额外打印可用资源名，便于后续排障。

## 当前验证状态

- 已完成失败复现。
- 已完成根因修复补丁。
- 当前机器未安装 .NET SDK，无法在本地重新执行 `dotnet publish` 验证修复后的新产物。

## 建议复验命令

在具备 .NET 8 SDK 的 Windows 环境或 GitHub Actions 中重新构建后，执行：

```powershell
.\claude-code-<version>-win-x64-updater.exe $env:TEMP\claude-updater-verify
```

预期结果：

- 不再出现 `Embedded payload not found`
- 目标目录下生成 `claude.exe`
- 控制台输出 `Success!`
