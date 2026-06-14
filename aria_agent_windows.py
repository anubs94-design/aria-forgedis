import os, sys, time, json, subprocess
import http.server, socketserver

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    HAS_GUI = True
except:
    HAS_GUI = False

PORT = 7842

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args): pass
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0))
        data = json.loads(self.rfile.read(n))
        action = data.get('action', '')
        params = data.get('params', {})
        result = self.run(action, params)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())
    def run(self, action, params):
        if action == 'ping':
            return {'ok': True, 'os': 'windows'}
        elif action == 'ouvrir_application':
            app = params.get('app', '')
            urls = {'gmail':'https://mail.google.com','outlook':'https://outlook.live.com'}
            apps = {'word':'winword','excel':'excel','calculatrice':'calc','explorateur':'explorer','bloc-notes':'notepad'}
            if app in urls:
                subprocess.Popen(['start', 'chrome', urls[app]], shell=True)
                return {'ok': True}
            elif app in apps:
                subprocess.Popen([apps[app]], shell=True)
                return {'ok': True}
        elif action == 'notification':
            msg = params.get('message', '')
            titre = params.get('titre', 'Aria')
            subprocess.Popen(['powershell','-WindowStyle','Hidden','-Command',
                f'Add-Type -AssemblyName System.Windows.Forms; =New-Object System.Windows.Forms.NotifyIcon; .Icon=[System.Drawing.SystemIcons]::Information; .Visible=True; .ShowBalloonTip(4000,\"{titre}\",\"{msg}\",[System.Windows.Forms.ToolTipIcon]::Info); Start-Sleep 5; .Dispose()'])
            return {'ok': True}
        return {'ok': False, 'error': 'Action inconnue'}

print('Agent Forgedis Windows v1.0 - Port', PORT)
print('Ouverture de Chrome sur Aria...')
time.sleep(1)
subprocess.Popen(['start', 'chrome', 'https://aria-forgedis.netlify.app/senior'], shell=True)
with socketserver.TCPServer(('localhost', PORT), Handler) as s:
    print('En attente des ordres Aria...')
    s.serve_forever()
