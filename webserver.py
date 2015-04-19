#!/usr/bin/python

import yaml
import glob
import json
import os.path
import SimpleHTTPServer
import BaseHTTPServer
import urlparse

class PslWebServerRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    Behaviors = None

    def do_POST(self): 
        var_len = int(self.headers['Content-Length'])
        d =  self.rfile.read(var_len)
        self.post_vars = json.loads(d)
        return self.do_GET()

    def do_GET(self):
        if self.path.startswith('/behaviors'):
            self.send_response(200)
            try: self.do_Behavior()
            except Exception as e:
                import traceback; traceback.print_exc()
                import pdb; pdb.post_mortem()
        elif self.path.startswith('/deploy'):
            self.send_response(200)
            try: self.do_Deploy()
            except Exception as e:
                import traceback; traceback.print_exc()
                import pdb; pdb.post_mortem()
        elif self.command in ('GET', 'POST'):
            return SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

    def do_Deploy(self):
        p = self.path.strip('/').split('/')
        if len(p) == 1 and self.command=='POST':
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            return self.do_DeployPromo()

    def do_Behavior(self):
        p = self.path.strip('/').split('/')
        if len(p) == 1 and self.command=='GET':
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            return self.do_ListBehaviors()
        elif len(p) == 1 and self.command=='POST':
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            return self.__ensure_behaviors(True)
        elif len(p) == 3 and p[2] in ('init', 'web_chooser', 'widget'):
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            return self.do_GetBehaviorCode(*p[-2:])
        else:
            self.send_response(404)

    @classmethod
    def __ensure_behaviors(cls, reload=False):
        if reload or cls.Behaviors is None:
            cls.Behaviors = dict(map(lambda f: (os.path.basename(f), yaml.load(open(f))), glob.glob(os.path.join('behaviors', '*.yml'))))


    def do_ListBehaviors(self):
        self.__ensure_behaviors()
        self.wfile.write(json.dumps( dict(map(lambda i: (i[0], json.loads(i[1]['on_init'])), self.Behaviors.items())) ) )

    def do_GetBehaviorCode(self, behavior, what):
        self.__ensure_behaviors()
        self.wfile.write(self.Behaviors[behavior]['on_%s' % what])
        

    def do_DeployPromo(self):
        self.__ensure_behaviors()
        for b in self.post_vars['behavior']:
            b['trigger'] = self.Behaviors[b['id']].copy()
            del b['id']
            del b['trigger']['on_init']
            del b['trigger']['on_widget']
        self.send_promo(self.post_vars)

    def send_promo(self, data):
     # [compile(b['trigger']['on_deploy'],'', 'exec') for b in self.post_vars['behavior']] 
        ev = pev.promo_def.PslEvent(data=data)
        ev.enqueue()
        pev.post()
        from pprint import pformat
        print pformat(self.post_vars)
        

def webserver(port):
    httpd = BaseHTTPServer.HTTPServer(("", int(port)), PslWebServerRequestHandler)
    print "serving at port", port
    httpd.serve_forever()


if __name__ == '__main__':
    import sys
    webserver(sys.argv[1])