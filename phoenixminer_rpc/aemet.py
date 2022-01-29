import requests
import xml.etree.ElementTree as ET
import pandas as pd


class Aemet():

    # http://www.aemet.es/xml/municipios_h/localidad_h_28079.xml
    def __init__(self, code="28079"):
        self.code = code

    def get_hourly_data(self, tipo="temperatura"):
        resp = requests.get(f"http://www.aemet.es/xml/municipios_h/localidad_h_{self.code}.xml")
        root = ET.fromstring(resp.content)
        today = pd.Timestamp.now(tz="Europe/Madrid")
        for elem_dia in root.getchildren()[-1].getchildren():
            fecha = elem_dia.get("fecha")
            if fecha == today.strftime("%Y-%m-%d"):
                elems = elem_dia.getchildren()
                data_elem = {int(e.get('periodo')): e.text for e in elems if e.tag == tipo}
                return data_elem

        return root


if __name__ == '__main__':
    a = Aemet()
    print(a.get_hourly_data())
