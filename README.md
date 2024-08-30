# Analysis of Renewable Energy Infrastructure Representations in OpenStreetMap

This projects evaluates the accuracy and completeness of wind and solar energy infrastructure data in OpenStreetMap (OSM) for Belgium and Ireland, identifying common mapping errors and proposing techniques to enrich available data. By combining OSM data with CORINE Land Cover inventory, we study land use patterns around renewable energy infrastructures, facilitating environmental planning.

### Introduction
Renewable energy is crucial for building a more sustainable future, but supporting the energy transition requires reliable data on energy supply, infrastructure, and environmental impact.  
OpenStreetMap (OSM) serves as a valuable source of open data to meet these needs, especially in contexts where ufficial data are lacking, potentially having a significant impact. OSM energy-related objects are widely reported under the *“power”* tag, with available key-value combinations to identify wind and solar sources. Wind turbines are commonly tagged as *“power=generator”* and *“generator:source=wind”*, while solar farms are identiﬁed as *“power=plant”* and *“plant:source=solar”*.  
In this work, we describe our research on evaluating the OSM database as a source of data for the study of wind and solar energy infrastructures. As a case-study, we consider two European countries, namely Belgium and Ireland.  
Firstly, we seek to identify common mapping errors and tagging issues associated with wind and solar energy infrastructures representation within OSM. This involves examining geometries and tagging mistakes while evaluating the accuracy and completeness of infrastructures data. We also propose geocomputation methods and spatial clustering application for internal evaluation and enhancement of OSM data.  
Secondly, by combining OSM data with the CORINE Land Cover (CLC) inventory, we perform a geographical analysis to consider the distribution of infrastructures across various CLC, seeking to detect patterns around land covers and renewable energy infrastructures.  
Overall, we propose a structured methodology and practical tools to assess and enhance overall OSM data quality, particularly useful in case of scarce or not publicly available data on renewables.

### Data Description
OSM data for Ireland and Belgium are downloaded in PBF format from `GeoFabrik` (www.geofabrik.de), and parsed for relevant infrastructures using the *PowerSourceHandler* class (OSMHandlers.py), inheriting from *osmium.SimpleHandler*.  
CORINE data are downloaded in vector format and are freely available (prior registration to the website) on the `Copernicus initiative portal` (www.land.copernicus.eu/en/products/corine-land-cover).  
The developed code is designed to be easily replicable in other countries.

### Project Structure
- [`OSMHandlers.py`](https://github.com/luisalopresti/OSMRenewables/blob/main/src/OSMHandlers.py): this script contains classes developed by inheritance from osmium.SimpleHandler. The most relevant one is the *PowerSourceHandler* class, extracting *generator* and *plant* objects from a PBF file.  
- [`utils.py`](https://github.com/luisalopresti/OSMRenewables/blob/main/src/utils.py): useful functions for spatial computations and plots; applied in the notebooks.
- [`IE_power.ipynb`](https://github.com/luisalopresti/OSMRenewables/blob/main/src/IE_power.ipynb): analysis and enhancement of the completeness and accuracy of OSM data on solar and wind infrastructure in Ireland.
- [`IE_CORINE.ipynb`](https://github.com/luisalopresti/OSMRenewables/blob/main/src/IE_CORINE.ipynb): analysis of CORINE land cover surrounding OSM-reported solar and wind infrastructures in Ireland.
- [`BE_power.ipynb`](https://github.com/luisalopresti/OSMRenewables/blob/main/src/BE_power.ipynb): analysis and enhancement of the completeness and accuracy of OSM data on solar and wind infrastructure in Belgium.
- [`BE_CORINE.ipynb`](https://github.com/luisalopresti/OSMRenewables/blob/main/src/BE_CORINE.ipynb): analysis of CORINE land cover surrounding OSM-reported solar and wind infrastructures in Belgium.

### Related Publication
This code is associated with the research paper titled *"Analysis of Renewable Energy Infrastructure Representations in OpenStreetMap"*, which has been accepted for the proceedings of OSM Science 2024. Full details will be updated once the paper is published.

### Acknowledgments
This work has emanated from research conducted with the financial support of Science Foundation Ireland under Grant number 18/CRT/6049.  
The code in this repository is licensed under a CC BY 4.0 license.
