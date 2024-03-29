#!/usr/bin/env python

import cgi
import httplib
import mimetypes
import os
import socket
import urlparse
import BaseHTTPServer


class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
  """Very simple web server.

  GET requests without parameters return files as-is from the www/ subdirecotry.
  POST requests and GET requests with parameters are sent to _action() for
    processing.
  """

  def do_GET(self):
    url_parts = urlparse.urlparse(self.path)
    params = urlparse.parse_qs(url_parts.query)
    if params:
      params['path'] = url_parts.path
      self._action(params)
    else:
      path = url_parts.path
      print 'path from url is "%s"' % path
      if path.endswith('/'):
        path = path + 'index.html'
        print 'New path is "%s"' % path
      self._send_file(path)

  def do_POST(self):
    self._action(self._parse_post())

  def _parse_post(self):
    ctype, pdict = cgi.parse_header(self.headers['content-type'])
    if ctype == 'multipart/form-data':
      postvars = cgi.parse_multipart(self.rfile, pdict)
    elif ctype == 'application/x-www-form-urlencoded':
      length = int(self.headers['content-length'])
      postvars = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
    else:
      postvars = {}
    return postvars

  def _send_file(self, path):
    file_path = 'www' + path
    if not os.path.exists(file_path):
      self.send_error(httplib.NOT_FOUND, 'No such file "%s"' % file_path)
    else:
      # Note: Totally insecure, but probably doesn't matter much.
      fp = open(file_path)
      data = fp.read()  # Assume small-ish files; probably reasonable.
      fp.close()
      self.send_response(httplib.OK)
      self.send_header('Content-Length', len(data))
      self.send_header('Content-Type', mimetypes.guess_type(path)[0])
      self.end_headers()
      self.wfile.write(data)

  def _action(self, params):
    self.send_response(httplib.OK)
    self.end_headers()
    self.wfile.write('I see you having %d parameters<br>\n' % len(params))
    for key, val in params.iteritems():
      self.wfile.write('post variable "%s": "%s"\n<br>\n' % (key, val))

    # TODO(anybody): Accept various commands and return content.
    # - No command returns a page displaying maps, robots to choose.
    # - POST specifying robots and a map runs a battle and returns results.



if __name__ == '__main__':
  port = int(os.environ.get('OPENSHIFT_INTERNAL_PORT', '8080'))
  host = os.environ.get('OPENSHIFT_INTERNAL_IP', socket.gethostname())
  print 'Server trying to bind to host "%s", port %d' % (host, port)
  server = BaseHTTPServer.HTTPServer((host, port), RequestHandler)
  try:
    server.serve_forever()
  except:
    pass
  server.server_close()
