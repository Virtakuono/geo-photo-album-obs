#!/usr/bin/python

import sys
import os
import cgi
import urllib2
import datetime
import time
import mgrs
import copy
import PIL.Image
import PIL.ExifTags
import sys
import random
import math

class img():

    def __init__(self,filename='',title='No title.',defcoord=[47.92,106.92],randamp=0.5):
        self.filename = '%s'%(filename,)
        self.title = '%s'%(title,)
        img = PIL.Image.open(filename)
        exif = {PIL.ExifTags.TAGS[k]: v for k,v in img._getexif().items() if k in PIL.ExifTags.TAGS}
        try:
            g = exif['GPSInfo']
            self.lon = 1.0
            self.lat = 1.0
            self.lat *= g[2][0][0]/float(g[2][0][1])
            self.lat += g[2][1][0]/float(g[2][1][1]*60)
            self.lat += g[2][2][0]/float(g[2][2][1]*3600)
            self.lon *= g[4][0][0]/float(g[4][0][1])
            self.lon += g[4][1][0]/float(g[4][1][1]*60)
            self.lon += g[4][2][0]/float(g[4][2][1]*3600)
            if not (g[1] == 'N'):
                self.lat *= -1
            if not (g[3] == 'E'):
                self.lon *= -1
            self.gpsRandom = False
        except KeyError:
            r = randamp*random.random()
            an = 2*math.pi*random.random()
            self.lat = defcoord[0]+r*math.sin(an)
            self.lon = defcoord[1]+r*math.cos(an)/math.cos(defcoord[1]/180.0)
            self.gpsRandom = True
        try:
            self.timeString = exif['DateTimeOriginal']
        except KeyError:
            self.timeString = 'no DateTimeOriginal'

    def htmlCoords(self):
        latC = 'N'
        lonC = 'E'
        if self.lat < 0.0:
            latC = 'S'
        if self.lon < 0.0:
            lonC = 'W'
        return '%.8f &deg; %s, %.8f &deg; %s'%(abs(self.lat),latC,abs(self.lon),lonC)

    def markerstr(self):
        if not self.gpsRandom:
            return '   L.marker([%.8f, %.8f]).addTo(map).bindPopup(\"<b>%s</b><br /><a href=\\"%s\\"><img src=\\"./%s\\" width=\\"150\\" height=\\"150\\"></a><br />%s<br />%s \");\n'%(self.lat,self.lon,self.filename,self.filename,self.thumbNailName(),self.timeString,self.htmlCoords())
        return '   L.marker([%.8f, %.8f]).addTo(map).bindPopup(\"<b>%s</b><br /><a href=\\"%s\\"><img src=\\"./%s\\" width=\\"150\\" height=\\"150\\"></a>\
<br />No geodata available.\");\n'%(self.lat,self.lon,self.filename,self.filename,self.thumbNailName())

    def thumbNailName(self,append='_TN'):
        return './thumbs/' + self.filename[:-4] + append + self.filename[-4:]

    def makeThumbNail(self,size=[100,100],append='_TN'):
        source = self.filename
        output = self.thumbNailName(append=append)
        command = 'convert -define jpeg:size=%dx%d ./%s  -thumbnail 100x100^ -gravity center -extent %dx%d  %s'%(size[0]*2,size[1]*2,source,size[0],size[1],output)
        os.system(command)

class photoSet():
    
    def nowString(self,):
        # we want something like '2007-10-18 14:00+0100'
        mytz="%+4.4d" % (time.timezone / -(60*60) * 100) # time.timezone counts westwards!
        dt  = datetime.datetime.now()
        dts = dt.strftime('%Y-%m-%d %H:%M')  # %Z (timezone) would be empty
        nowstring="%s%s" % (dts,mytz)
        return nowstring

    def centerPoint(self):
        return (sum([p.lat for p in self.photos])/float(len(self.photos)), sum([p.lon for p in self.photos])/float(len(self.photos)))

    def __init__(self,photos,name='',desc='',filename='album.htm',tileUrl='http://{s}.tile.thunderforest.com/cycle/{z}/{x}/{y}.png',zoom=5):
        self.photos = copy.deepcopy(photos)
        self.name = '%s'%(name,)
        self.desc = '%s'%(desc,)
        self.filename = '%s'%(filename,)
        self.defZoom = int(1*zoom)
        self.tileUrl = '%s'%(tileUrl,)

    def osmhtmlstr(self,submaps=[],noText=False):

        rv = '<!DOCTYPE html>\n'
        rv += '<html>\n'
        rv += '<head>\n'
        rv += '  <title>%s</title>\n'%(self.name)
        rv += '  <meta charset=\"utf-8\" />\n'
        rv += '  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n'
        #rv += '  <link href=\"http://leafletjs.com/atom.xml\" type=\"application/atom+xml\" rel=\"alternate\" title=\"Leaflet Dev Blog Atom Feed\" />\n'
        #rv += '  <link rel=\"stylesheet\" href=\"https://rawgit.com/Virtakuono/.kml-repository/master/leaflet-0.7.3/leaflet.css\" />\n'
        #rv += '  <link rel=\"stylesheet\" href=\"https://rawgit.com/Virtakuono/.kml-repository/master/screen.css\" />\n'
        #rv += '  <script src=\"https://rawgit.com/Virtakuono/.kml-repository/master/leaflet-0.7.3/leaflet.js\"></script>\n'
        

        rv += '  <link rel=\"stylesheet\" href=\"./leaflet-0.7.3/leaflet.css\" />\n'
        rv += '  <link rel=\"stylesheet\" href=\"./master/screen.css\" />\n'
        rv += '  <script src=\"./leaflet-0.7.3/leaflet.js\"></script>\n'

        rv += '</head>\n'
        rv += '<body>\n'
        rv += '  <div class=\"container\">\n'
        rv += '  <div id=\"map\" class=\"map\" style=\"width: %dem; height: %dem\"></div>\n'%(60,40)
        rv += '  <script>\n'
        rv += '\n'
        rv += '\n'
        cp = self.centerPoint()
        rv += '   var map = L.map(\'map\').setView([%.6f, %.6f], %d);\n'%(cp[0],cp[1],self.defZoom)
        rv += '   \n'

        rv += '   L.tileLayer(\'%s\', {\n     maxZoom: 18,\n     attribution: \'Map &copy; <a href="http://osm.org/">OSM</a>\',\n     id: \'tehTile\'}).addTo(map);\n\n'%(self.tileUrl,)

        for photo in self.photos:
            rv += photo.markerstr()

        rv += '</script>\n'

        #rv += '   \n'
        #rv += '  <p>Page generated on %s</p>\n'%(self.nowString(),)
        rv += '</body>\n'
        rv += '</html>\n'
        return [rv]

def main():
    
    filenames = []
    for fn in os.listdir('./'):
        if fn[-4:].lower() == '.jpg':
            filenames.append(fn)
            #print('found photo %s'%(fn))
    ps = [img(filename=fn,title=fn) for fn in filenames]
    for photo in ps:
        photo.makeThumbNail()
    ps = photoSet(ps)
    f=open(ps.filename,'w')
    f.writelines(ps.osmhtmlstr())
    f.close()
    

main()
