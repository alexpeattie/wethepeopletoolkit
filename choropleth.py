from bs4 import BeautifulSoup
import os
import sys
import tempfile
from PyQt4 import QtGui, QtSvg

class ChoroplethMap:
  def __init__(self):
    self.COLORS = ['#DC143C', '#32CD32', '#00BFFF', '#F0CE3E', '#9370DB', '#AFEEEE', '#FFA500', '#FFC0CB', '#EE82EE', '#BDB76B', '#E6E6FA', '#00008B', '#F5DEB3', '#40E0D0', '#800000']
    self.COLOR_NAMES = ['Red', 'Green', 'Blue', 'Yellow', 'Purple', 'Cyan', 'Orange', 'Pink', 'Magenta', 'Khaki', 'Lavender', 'Dark Blue', 'Beige', 'Turqouise', 'Maroon']

  def show_clustered_map(self, data):
    '''
    Parse svg map and set initial style
    '''
    svg_path = os.path.join(os.path.dirname(__file__), 'us_states.svg')
    svg = open(svg_path, 'r').read()
    soup = BeautifulSoup(svg, 'xml')
    paths = soup.findAll(['path','g'])

    path_style = '''font-size:12px;fill-rule:nonzero;stroke:#FFFFFF
      ;stroke-opacity:1;stroke-width:0.1;stroke-miterlimit:4
      ;stroke-dasharray:none;stroke-linecap:butt;marker-start:none
      ;stroke-linejoin:bevel;fill:'''
    
    '''
    Determine shade for each county and write appropriate path style
    '''
    for p in paths:
      if ['id'] not in ["State_Lines","separator"]:
        try:
          val = data[p['id']]
        except:
          continue

        color = self.COLORS[min(val, len(self.COLORS) - 1)]
        p['style'] = path_style + color

    with tempfile.NamedTemporaryFile() as temp:
      temp.write(soup.prettify())
      temp.flush()

      app = QtGui.QApplication(sys.argv) 
      svgWidget = QtSvg.QSvgWidget(temp.name)
      palette = svgWidget.palette()
      palette.setColor(svgWidget.backgroundRole(), QtGui.QColor('white'))
      svgWidget.setPalette(palette)
      # svgWidget.setGeometry(50,50)
      svgWidget.show()
      sys.exit(app.exec_())