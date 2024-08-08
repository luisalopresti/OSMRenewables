import osmium
import shapely.wkb as wkblib

'''
OSMium Classes:
- PowerSourceHandler: collects generators and plants infrastructure (NOTE: for the analysis the output was filtered to retain only wind and solar sources).
- RelationPowerHandler: handle relationships among generators and plants infrastructures (e.g., if they belong to a wind farm).
- ImpactFactorsHandler: collects important factors influencing infrastructures location.
- BuildingHandler: collects buildings geometries - used to enstablish whether a solar infrastructure is on a rooftop.
'''


class PowerSourceHandler(osmium.SimpleHandler):
    '''
    This class aims at collecting all the generators and plants in the considered pbf file,
    returning a dictionary object *power_sources*, which can be easily converted into a single dataframe.

    The *power* tag may assume values "generator" or "plant", 
    and in the tags column you may find dictionary-like strings with keys such as "generator:method" or "plant:method", 
    or "generator:source" or "plant:source", that add information about generators and plants.
    Generators and plants can be nodes, ways or areas/multipolygons relations (e.g., cfr. https://wiki.openstreetmap.org/wiki/Key:generator:method); 
    thus, methods to handle nodes, ways and areas are implemented.

    NOTE: according to OSM Tag Wiki, "power=plant" may be a multipolygon/area or a relation, 
    while "power=generator" may be a node, a way or a multipolygon/area.
    This class collects nodes, ways and multypolygons/areas, for both generators and plants, to account for possible mapping errors.
    '''
    def __init__(self):
        super(PowerSourceHandler, self).__init__()
        self.power_sources = []
        self.node_coordinates = {} # store nodes coords as {node_id : coords}
        self.wkbfab = osmium.geom.WKBFactory() # shapely geometry

    def node(self, n):
        self.node_coordinates[n.id] = (n.location.lat, n.location.lon)  # store node coordinates

        if 'power' in n.tags:
            # create geometry
            try:
                wkb = self.wkbfab.create_point(n)
                geometry = wkblib.loads(wkb, hex=True)
            except:
                geometry = None
            
            power_tag = n.tags['power']
            if power_tag in ['generator', 'plant']: # == 'generator': # generator can be nodes, plant shouldn't --> but look for both to account for potential mappint errors
                power_method = n.tags.get('generator:method', None) or n.tags.get('plant:method', None)
                power_source = n.tags.get('generator:source', None) or n.tags.get('plant:source', None)
                power_type = n.tags.get('generator:type', None) or n.tags.get('plant:type', None)
                self.power_sources.append({
                    'id': 'n'+str(n.id),
                    'lat': n.location.lat,
                    'lon': n.location.lon,
                    'power_tag': power_tag,
                    'power_method': power_method,
                    'power_source': power_source,
                    'power_type': power_type,
                    'geometry': geometry
                })
    
    def way(self, w):
        # w.nodes # list of ID of nodes in the way
        # w.tags # obj: osmium.osm.types.TagList ; tags dict - all ways, filter by generator and plant
        
        if 'power' in w.tags:
            power_tag = w.tags['power']
            # create geometry
            try:
                wkb = self.wkbfab.create_linestring(w)
                geometry = wkblib.loads(wkb, hex=True)
            except:
                geometry = None
            
            # select power-values as generator or plant
            if power_tag in ['generator', 'plant']: # == 'generator': # generator may be way, plant shouldn't --> but look for both to account for potential mappint errors
                nodes_in_way = [node.ref for node in w.nodes] # ID of nodes in the way
                way_coordinates = [(self.node_coordinates[node_id][0], self.node_coordinates[node_id][1]) for node_id in nodes_in_way] # coords of nodes in the way
                power_method = w.tags.get('generator:method', None) or w.tags.get('plant:method', None) # get values of method if available
                power_source = w.tags.get('generator:source', None) or w.tags.get('plant:source', None) # get values of source if available
                power_type = w.tags.get('generator:type', None) or w.tags.get('plant:type', None) # get values of type if available
                self.power_sources.append({
                    'id': 'w'+str(w.id),
                    'nodesID_in_way': nodes_in_way,
                    'way_coordinates': way_coordinates,
                    'power_tag': power_tag,
                    'power_method': power_method,
                    'power_source': power_source,
                    'power_type': power_type,
                    'geometry': geometry
                })

    def area(self, a):
        if 'power' in a.tags:

            # create geometry
            try:
                wkb = self.wkbfab.create_multipolygon(a)
                geometry = wkblib.loads(wkb, hex=True)
            except:
                geometry = None
            
            power_tag = a.tags['power']
            if power_tag in ['generator', 'plant']: # both generators and plants can be areas

                nodes_in_area = []  # store nodes constituting the area
                for ring in a.outer_rings(): # outer ring
                    for node in ring:
                        nodes_in_area.append(node.ref)
                area_coordinates = [(self.node_coordinates[node_id][0], self.node_coordinates[node_id][1]) for node_id in nodes_in_area] 

                power_method = a.tags.get('generator:method', None) or a.tags.get('plant:method', None)
                power_source = a.tags.get('generator:source', None) or a.tags.get('plant:source', None)
                power_type = a.tags.get('generator:type', None) or a.tags.get('plant:type', None)
                self.power_sources.append({
                    'id': 'a'+str(a.id),
                    'nodesID_in_area': nodes_in_area,
                    'area_coordinates': area_coordinates,
                    'power_tag': power_tag,
                    'power_method': power_method,
                    'power_source': power_source,
                    'power_type': power_type,
                    'geometry': geometry
                })

    
    def relation(self, r):
        # group objects belonging to the same farm (according to OSM relations):
        # fields are added to objects belonging to same relation
        if 'power' in r.tags:
            power_tag = r.tags['power']
            if power_tag in ['generator', 'plant']:
                ids_in_relation = [relation.type + str(relation.ref) for relation in r.members] # starts with n for nodes, w for ways, a for areas + the respective ID

                for power_obj in self.power_sources:
                    if power_obj.get('id') in ids_in_relation:
                        power_obj['relation_id'] = r.id # same relation_id if belonging to same group
                        power_obj['relation_type'] = r.tags.get('type', None)
                        power_obj['relation_info'] = r.tags.get('site', None)
    





# CLASS TO HANDLE POWER-RELATIONS ONLY
class RelationPowerHandler(osmium.SimpleHandler):
    '''
    Create class to handle relations of OSM power-tagged objects.
    This method allows, for instance, to detect wind farms, and therefore understand when nodes 
    or other types of OSM objects are grouped together.
    '''
    def __init__(self):
        super(RelationPowerHandler, self).__init__()
        self.power_sources = []

    def relation(self, r):
        if 'power' in r.tags:
            power_tag = r.tags['power']
            if power_tag in ['generator', 'plant']:
                relation_type = r.tags.get('type', None)
                ids_in_relation = [relation.type + str(relation.ref) for relation in r.members] # starts with n for nodes, w for ways, a for areas + the respective ID
                power_method = r.tags.get('generator:method', None) or r.tags.get('plant:method', None)
                power_source = r.tags.get('generator:source', None) or r.tags.get('plant:source', None)
                power_type = r.tags.get('generator:type', None) or r.tags.get('plant:type', None)
                site = r.tags.get('site', None) 
                self.power_sources.append({
                    'relation_id': r.id,
                    'objectsID_in_relation': ids_in_relation,
                    'power_tag': power_tag,
                    'power_method': power_method,
                    'power_source': power_source,
                    'power_type': power_type,
                    'relation_type':relation_type,
                    'site': site,
                    'other_tags': dict(r.tags)
                })



# HANDLE OSM OBJECTS INFLUENTING INFRASTRUCTURES LOCATION
class ImpactFactorsHandler(osmium.SimpleHandler):
    '''
    Collect OSM objects that may impact the existance of a wind/solar infrastructure.

    Important factors for infrastructures locations:
    1. ENVIRONMENTAL: 
        - terrain slope
        - distance from protected areas
        - distance from water bodies
        - exposure index
    2. CLIMATIC:
        - avg annual precipitation
        - avg annual temperature
        - average annual solar radiation power
        - average annual wind velocity
        - photovoltaic energy potential
    3. ANTHROPOGENIC:
        - distance from industrial buildings
        - distance from industrial areas
        - distance from medium voltage grid (powerline)
        - distance from housing developments
        - distance from road
        - landuse
    4. SOCIAL:
        - shadow flicker
        - sound impact (noise)
        - visual impact (landscape)
        - propriety values
        - level of economic benefit

    References: 
    - Impacts, procedural processes, and local context: Rethinking the social acceptance of wind energy projects in the Netherlands (https://doi.org/10.1016/j.erss.2023.103044)
    - Optimising Photovoltaic Farm Location Using a Capabilities Matrix and GIS (https://doi.org/10.3390/en15186693)
    - The Social Acceptance of Wind Energy: Where we stand and the path ahead (https://publications.jrc.ec.europa.eu/repository/handle/JRC103743)
    

    According to the above findings, select the followings from OSM:
        - power tags - substations and towers (NODES, AREAS)
        - roads (as WAYS - for connection)
        - protected areas (as AREAS)
        - water bodies (AREAS - might be PT but undesirable)
        - residential & industrial buildings (usually AREAS but might be central PT)
        - residential & industrial landuse (usually AREAS but might be central PT)
        - (other landuse may be added but for now keep only industrial and residential for now)

    '''
    def __init__(self):
        super(ImpactFactorsHandler, self).__init__()
        self.osm_objects = []
        self.wkbfab = osmium.geom.WKBFactory() 

    def node(self, n):
        def get_node():
            try:
                wkb = self.wkbfab.create_point(n)
                geometry = wkblib.loads(wkb, hex=True)
                self.osm_objects.append({'id': 'n'+str(n.id),
                                        'tags':dict(n.tags),
                                        'geometry':geometry})
            except:
                pass

        # POWERLINE (nodes power-tags according to wiki)
        if 'power' in n.tags:
            if n.tags['power'] in [
                                   'tower', # node
                                   'substation' # node, poly, or multi-poly
                                   ]:
                get_node()
                
        # WATER BODIES (natural=water or water=smth) --> usually areas
        # NATURAL=WATER WIKI -> It is acceptable, but undesirable, to map this feature with a single node, if its extents aren't known.
        if 'natural' in n.tags:
            if n.tags['natural'] in ['water']:
                get_node()

        # INDUSTRIAL AND RESIDENTIAL BUILDINGS (sometimes pt according to wiki)
        if 'building' in n.tags:
            if n.tags['building'] in ['industrial', 'residential']:
                get_node()
        
        # INDUSTRIAL AND RESIDENTIAL LANDUSE/AREAS (sometimes central pt according to wiki)
        if 'landuse' in n.tags:
            if n.tags['landuse'] in ['industrial', 'residential']:
                get_node()

    
    def way(self, w):
        def get_way():
            try:
                wkb = self.wkbfab.create_linestring(w)
                geometry = wkblib.loads(wkb, hex=True)
                self.osm_objects.append({'id': 'n'+str(w.id),
                                        'tags':dict(w.tags),
                                        'geometry':geometry})
            except:
                pass

        # ROADS --> BUT ONLY WANT WAYS (cfr. https://wiki.openstreetmap.org/wiki/Key:highway)
        # (pts may be traffic lights, areas might be pedestrian areas --> only want highways for connection purposes)
        if 'highway' in w.tags:
            get_way()


    def area(self, a):
        def get_area():
            try:
                wkb = self.wkbfab.create_multipolygon(a)
                geometry = wkblib.loads(wkb, hex=True)
                self.osm_objects.append({'id': 'n'+str(a.id),
                                        'tags':dict(a.tags),
                                        'geometry':geometry})
            except:
                pass

        # PROTECTED AREAS (leisure=nature_reserve or boundary=protected_area)
        # can only be areas (cfr. https://wiki.openstreetmap.org/wiki/Tag:leisure%3Dnature_reserve
        # and https://wiki.openstreetmap.org/wiki/Tag:boundary%3Dprotected_area)
        if 'boundary' in a.tags:
            if a.tags['boundary'] in ['protected_area']:
                get_area()
        elif 'leisure' in a.tags:
            if a.tags['leisure'] in ['nature_reserve']:
                get_area()

        # POWERLINE (areas power-tags according to wiki)
        if 'power' in a.tags:
            if a.tags['power'] in [
                                   'substation' # can be pt or area
                                   ]:
                get_area()

        # WATER BODIES (natural=water or water=smth)
        if 'natural' in a.tags:
            if a.tags['natural'] in ['water']:
                get_area()
        elif 'water' in a.tags:
            get_area()

        # INDUSTRIAL AND RESIDENTIAL BUILDINGS 
        if 'building' in a.tags:
            if a.tags['building'] in ['industrial', 'residential']:
                get_area()

        # INDUSTRIAL AND RESIDENTIAL LANDUSE/AREAS 
        if 'landuse' in a.tags:
            if a.tags['landuse'] in ['industrial', 'residential']:
                get_area()


           
class BuildingHandler(osmium.SimpleHandler):
    '''
    Collects geometries of areas tagged as buildings.
    '''
    def __init__(self):
        super(BuildingHandler, self).__init__()
        self.buildings = []
        self.wkbfab = osmium.geom.WKBFactory() # shapely geometry

    def area(self, a):
        if 'building' in a.tags: # and 'roof:solar_panel' in a.tags:

            # create geometry
            try:
                wkb = self.wkbfab.create_multipolygon(a)
                geometry = wkblib.loads(wkb, hex=True)
            except:
                geometry = None
            
            # add to data
            self.buildings.append({
                    'id': 'a'+str(a.id),
                    'geometry': geometry
                })
     