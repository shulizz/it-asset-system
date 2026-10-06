const { app, BrowserWindow } = require('electron')
const path = require('path')

function createWindow() {
  const win = new BrowserWindow({
    width: 1440, height: 900, minWidth: 1200, minHeight: 700,
    title: "成都曙光固定资产管理系统",
    webPreferences: { nodeIntegration: false, contextIsolation: true }
  })
  win.loadFile(path.join(__dirname, 'index.html'))
}

app.whenReady().then(createWindow)
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit() })
