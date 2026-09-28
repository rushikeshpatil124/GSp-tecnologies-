from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs
import json, os

HOST="0.0.0.0"
PORT=8080

class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("X-Frame-Options","DENY")
        self.send_header("Referrer-Policy","strict-origin-when-cross-origin")
        self.send_header("Permissions-Policy","camera=(), microphone=(), geolocation=()")
        self.send_header("Content-Security-Policy","default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self';")
        super().end_headers()

    def do_POST(self):
        if self.path == "/api/contact":
            length=int(self.headers.get("Content-Length",0))
            if length > 10000:
                self.send_json({"ok":False,"error":"Request too large"},413)
                return
            data=parse_qs(self.rfile.read(length).decode())
            name=data.get("name",[""])[0].strip()
            email=data.get("email",[""])[0].strip()
            message=data.get("message",[""])[0].strip()

            if len(name)>100 or len(email)>200 or len(message)>5000:
                self.send_json({"ok":False,"error":"Input too long"},400)
                return

            if "<script" in message.lower() or "<script" in name.lower():
                self.send_json({"ok":False,"error":"Invalid input"},400)
                return

            if not name or not email or not message:
                self.send_json({"ok":False,"error":"All fields are required"},400)
                return

            os.makedirs("messages",exist_ok=True)
            with open("messages/contact.jsonl","a",encoding="utf-8") as f:
                f.write(json.dumps({
                    "name":name,
                    "email":email,
                    "message":message
                },ensure_ascii=False)+"\n")

            self.send_json({
                "ok":True,
                "message":"Your enquiry has been received."
            })
            return

        self.send_json({"ok":False,"error":"Not found"},404)

    def send_json(self,obj,status=200):
        raw=json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
