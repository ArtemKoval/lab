// Window creation with the sandbox flags, the content security policy,
// popup denial, and external links handed to the system browser.

export const CONTENT_SECURITY_POLICY = [
  "default-src 'self'",
  "script-src 'self'",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data:",
  "connect-src 'none'",
].join('; ')

export function isWebUrl(url) {
  return url.startsWith('http://') || url.startsWith('https://')
}

export function createChatWindow({
  BrowserWindow,
  session,
  preloadPath,
  rendererFile,
  openExternal,
  width = 1080,
  height = 720,
}) {
  const win = new BrowserWindow({
    width,
    height,
    show: false,
    backgroundColor: '#1e1e1e',
    webPreferences: {
      sandbox: true,
      contextIsolation: true,
      nodeIntegration: false,
      preload: preloadPath,
    },
  })

  win.once('ready-to-show', () => win.show())

  session.webRequest.onHeadersReceived((details, callback) => {
    callback({
      responseHeaders: {
        ...details.responseHeaders,
        'Content-Security-Policy': [CONTENT_SECURITY_POLICY],
      },
    })
  })

  win.webContents.setWindowOpenHandler(({ url }) => {
    if (isWebUrl(url)) {
      openExternal(url)
    }
    return { action: 'deny' }
  })

  win.webContents.on('will-navigate', (event, url) => {
    event.preventDefault()
    if (isWebUrl(url)) {
      openExternal(url)
    }
  })

  win.loadFile(rendererFile)
  return win
}
