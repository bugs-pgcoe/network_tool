"""
this library has code to generate svg templates.
code is enhanced to read json files formats and further generate the svg

hence this code is a json to svg generator code

"""
import json
import pathlib
from xml.dom import minidom


class FileHandler:
    def __init__(self, file_name):
        self._filename = file_name
        self._fw = None
        if not pathlib.Path(file_name).is_file():
            self._fw = open(self._filename, "w")

    def write_json(self, content):
        if self._fw is None:
            self._fw = open(self._filename, "w")
        if isinstance(content, dict):
            self._fw.write(json.dumps(content, indent=4))

    def read_json(self):
        if self._filename.split(".")[-1].lower() == "json":
            try:
                with open(self._filename, "r") as fr:
                    return json.loads(fr.read())
            except json.JSONDecodeError as E:
                return {"json_error": E}
            except UnicodeDecodeError as E:
                return {"json_error": E}


class SvgDocument:
    def __init__(self):
        self._template_input = FileHandler("template_.json").read_json()
        self._layer_input = FileHandler("layer_mapping.json").read_json()
        self._layer_calcs = {}
        self._doc = minidom.Document()
        self._svg = self._doc.createElement("svg")
        self._svg.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
        self._doc.appendChild(self._svg)
        self._element_type_mapping = {
            "rect": self._create_rectagle
        }
        self._translates = {}

    def _create_rectagle(self, properties, id):
        element = self._doc.createElement("rect")
        element.setAttribute('id', f"{id}-{properties['id']}")
        element.setAttribute("x", properties["x"])
        element.setAttribute("y", properties["y"])
        element.setAttribute("width", properties["width"])
        element.setAttribute("height", properties["height"])
        if properties.get("style") is not None:
            element.setAttribute("style", properties["style"])
        return element

    def _create_group(self, _group_properties, id):
        element = self._doc.createElement("g")
        element.setAttribute("transform", "translate(0,0)")
        element.setAttribute("id", id)
        for item in _group_properties:
            for item_type, item_details in item.items():
                func = self._element_type_mapping.get(item_type, None)
                if func is not None:
                    element.appendChild(func(item_details, id))
        self._svg.appendChild(element)


    def set_overall_dimension(self, w, h):
        self._svg.setAttribute('width', w)
        self._svg.setAttribute('height', h)

    def create_network(self, network_properties):
        for device, properties in network_properties.items():
            type = properties["type"]
            self._create_group(self._template_input[type], device)
        self._arrange_components(network_properties)
        return self._doc

    def _arrange_components(self, network_properties):
        for device, properties in network_properties.items():
            type = properties["type"]
            if self._layer_calcs.get(type) is None:
                self._layer_calcs.update({type: {
                    "x": 5,
                    "y": int(self._layer_input[type]["y"]),
                }})
            else:
                var = int(self._template_input[type][0]['rect']['width']) + int(
                    self._layer_calcs[type]["x"])
                self._layer_calcs[type]["x"] = var
            element = self._get_element_by_id_g(device)
            element.setAttribute("transform", f"translate({self._layer_calcs[type]["x"]},"
                                              f"{self._layer_calcs[type]["y"]})")

    def _get_element_by_id_g(self, id):
        for item in self._doc.getElementsByTagName("g"):
            if item.getAttribute("id") == id:
                return item

if __name__ == "__main__":
    g = SvgDocument()
    network_input = FileHandler("network.json").read_json()
    doc = g.create_network(network_input)
    g.set_overall_dimension("500", "500")
    doc_indented = doc.toprettyxml(indent="\t")
    with open("test.svg", "w") as fw:
        fw.write(doc_indented)