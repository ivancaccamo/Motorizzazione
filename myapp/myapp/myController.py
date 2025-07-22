from django.shortcuts import render
from django.http import HttpResponse
def index(request):
    o1 = "<html> <body>"
    o2 = "<p>Welcome to DJANGO</p>"
    o3 = "</body> </html>"
    return HttpResponse(o1 + o2 + o3)
def index2(request):
    response = HttpResponse(
    content_type="text/html")
    response.write("<html> <body>")
    response.write(
    "<p>Welcome to DJANGO again</p>")
    response.write("</body> </html>")
    return response

