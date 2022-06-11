import requests
import xml.etree.ElementTree as ET
import pandas as pd


class Aemet():

    default_tipo = "temperatura"

    # http://www.aemet.es/xml/municipios_h/localidad_h_28079.xml
    def __init__(self, code="28079"):
        self.code = code

    def get_hourly_data(self, tipo=default_tipo) -> dict:
        """
        Gets hourly data for a type of data published in aemet website
        :param tipo: either temperatura (default), nieve, precipitacion...
        :return: a dictionary indexed by date (timestamp) and then by hour with the values
        (as floats). If res is the return value, the time of now is res[datetime.today()][datetime.now().hour]
        """
        resp = requests.get(f"http://www.aemet.es/xml/municipios_h/localidad_h_{self.code}.xml")
        root = ET.fromstring(resp.content)
        retval = dict()
        for elem_dia in root.find("prediccion").findall("dia"):
            fecha = pd.Timestamp(elem_dia.get("fecha"))
            elems = elem_dia.findall(tipo)
            retval[fecha] = {int(e.get('periodo')): float(e.text) for e in elems if e.tag == tipo}
        return retval

    def get_pred_date(self, when, tipo=default_tipo) -> float:
        return self.get_hourly_data(tipo)[when.normalize()][when.hour]

    def get_pred_hour(self, tipo=default_tipo, h_offset=0) -> float:
        """Gets value of a pred of the current hour plus the given offset"""
        now = pd.Timestamp.now() + pd.offsets.Hour(h_offset)
        return self.get_pred_date(now, tipo)


if __name__ == '__main__':
    a = Aemet()
    print(a.get_hourly_data())
    print(a.get_pred_hour())
    print(a.get_pred_hour(h_offset=-1))


