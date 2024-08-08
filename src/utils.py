import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.colors import ListedColormap
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import geopandas as gpd

#### WIND/SOLAR POWER

def check_equal_geometries(gdf, tolerance):
    '''
    Check if in the passed geodataframe (gdf), there are duplicated geometries, with a given tollerance.
    Returns a boolean.
    '''
    for i in range(len(gdf)):
        for j in range(i + 1, len(gdf)):
            if gdf.loc[i, 'geometry'].equals_exact(gdf.loc[j, 'geometry'], tolerance=tolerance):
                return True
    return False



def point_in_polygon_with_spatial_index(source_gdf, intersecting_gdf, 
                                        source_id_col='id', intersecting_id_col='id',
                                        pt_in_poly_function = 'intersects'):
    '''
    Conduct spatial intersection using spatial index for fast point-in-polygon search.

    Returns a DataFrame that matched points and their corresponding intersecting area identifiers
    
    DataFrame columns: 
        point_id (from source_gdf);
        area_id (from intersecting_gdf), representing the ids of the area that point belongs to.
    
    NOTE: if a node from source_gdf belongs to multple areas, 
    the node will appear in multiple rows associated with the different areas.
    '''
    source_sindex = source_gdf.sindex
    matches = []  # store matched points and their intersecting areas
    
    # iterate over each geometry in intersecting_df
    for area in intersecting_gdf.itertuples():
        bounds = area.geometry.bounds
        # find potential matches in source_df's spatial index
        potential_matches_idx = list(source_sindex.intersection(bounds))
        
        # iterate over potential matches
        for idx in potential_matches_idx:
            point = source_gdf.iloc[idx]

            if pt_in_poly_function == 'intersects':

                # IF INTERSECTION IS USED
                # check if point intersects area
                if point.geometry.intersects(area.geometry):
                    # add matched point and area ids to list
                    matches.append({'node_id': point[source_id_col], 
                                    'area_id': getattr(area, intersecting_id_col)})
            
            elif pt_in_poly_function == 'contains':
                
                # IF CONTAINED --> full containement, not just intersection
                # only geometries completely contained in the second gdf 
                # (not just intersecting) are returned.
    
                # check if point is completely contained within the area
                if area.geometry.contains(point.geometry): # CONTAINS
                    # add matched point and area ids to list
                    matches.append({'gdf1_geom_id': point[source_id_col], 
                                    'gdf2_area_id': getattr(area, intersecting_id_col)})
                    
            else:
                raise ValueError('Unknown point-in-polygon function to use. Got {}.'.format(pt_in_poly_function))
    
    
    return pd.DataFrame(matches)



#### CORINE

def parse_color(color_str):
    '''
    Function that gets as input the RGB color code (in string format XXX-XXX-XXX),
    and returns a tuple with floats for each RGB color,
    for plotting purposes.
    '''
    r, g, b = color_str.split('-')
    return (int(r) / 255, int(g) / 255, int(b) / 255)


def map_by_label(gdf, lab='LABEL2'):
    '''
    Plot map based on landuse.
    Take as input a geodataframe and landuse column (according to which the map should be colored).
    '''
    # unique labels 
    unique_labels = gdf[lab].unique()
    num_labels = len(unique_labels)
    
    # map label to colors (ensure there are enough unique colors for all unique labels --> max num labels in LABEL3 equal to 35)
    colors = plt.cm.tab20.colors + plt.cm.tab20b.colors + plt.cm.tab20c.colors
    cmap = ListedColormap(colors[:num_labels])
    color_map = {label: cmap(i) for i, label in enumerate(unique_labels)}

    # plot
    fig, ax = plt.subplots(figsize=(10, 10))
    for label, color in color_map.items():
        gdf[gdf[lab] == label].plot(ax=ax, facecolor=color, edgecolor='black', lw=0.5)

    # legend 
    legend_elements = [Patch(facecolor=color_map[label], edgecolor='black', label=label) for label in unique_labels]
    ax.legend(handles=legend_elements, title='Legend', title_fontsize='large', fontsize='large', bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.title('Landuse')
    plt.axis('off')
    plt.show()


def get_landuse_share(gdf, grp_by_landuse_col):
    '''
    Get as input geodataframe and column to group by (as string).
    For each grp_by_landuse_col category, 
    returns the percentage of the total area covered by that category (as a pandas Series).
    '''
    # group by landuse and calculate the area covered by each landuse
    area_by_landuse = gdf.groupby(grp_by_landuse_col).geometry.apply(lambda x: x.area.sum())

    total_area_gdf = gdf.geometry.area.sum()
    percentage_area_by_landuse = (area_by_landuse / total_area_gdf) * 100

    return percentage_area_by_landuse.sort_values(ascending=False)


def find_landuses_within_buffer(infrastructure_gdf1, landuse_gdf2, unique_id_gdf1, label_column_gdf2, buffer_distance):
    '''
    Function that associated with each geometry contained in infrastructure_gdf, 
    all the categories in landuse_gdf (in column label_column) that are found 
    within buffer_distance meters from the geometry themselves.

    Takes as input:
        - infrastructure_gdf1, landuse_gdf2: two geodataframes (in metric crs)
        - unique_id_gdf1: (str) name of the column containing infrastructures unique identifier in infrastructure_gdf1
        - label_column_gdf2: column in landuse_gdf representing the category to find within the surrounding of each element in infrastructure_gdf
        - buffer_distance: integer, expressed in meters, used to compute the buffer around each geometry in infrastructure_gdf

    Returns:
        - a pandas dataframe with two column: 
                1. unique_id_gdf1 (id of the infrastructure, from infrastructure_gdf)
                2. label_column_gdf2 (containing a set with all categories found within the given buffer)
    
    '''
    infrastructure_gdf_buffered = infrastructure_gdf1.copy()
    infrastructure_gdf_buffered['geometry'] = infrastructure_gdf_buffered.geometry.buffer(buffer_distance)

    # use spatial join to find all landuses available within a buffer_radius distance from each infrastructure geometry
    landuse_around_infrastructures = gpd.sjoin(landuse_gdf2, infrastructure_gdf_buffered, how='inner', predicate='intersects')
    return landuse_around_infrastructures.groupby([unique_id_gdf1]).aggregate({label_column_gdf2:set}).reset_index()


def freq_landuse_types(counter_object, title_plot='Frequency of Landuses Occurrences'): 
    '''
    Produce a barchart of occurrences of landtypes (keys in counter_object)

    Input:
        - counter_object (dictionary or collections.Counter object): dict having as keys landuse categories and as values num of occurrences (int)
        - title_plot (str): title to give to the plot

    Output:
        Plot a barchart
    '''
    plt.figure(figsize=(10, 6))
    elements = list(counter_object.keys())
    counts = list(counter_object.values())
    elements, counts = zip(*sorted(zip(elements, counts), key=lambda x: x[1], reverse=True))

    bars = plt.bar(elements, counts, color='skyblue')

    plt.title(title_plot)
    plt.xlabel('')
    plt.ylabel('Count')
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # for bar in bars.patches:
    #     plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5, f'{int(bar.get_height())}', 
    #             ha='center', va='bottom')

    total = sum(counts)
    for bar, count in zip(bars, counts):
        percentage = count / total * 100
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5, f'{int(count)}\n({percentage:.1f}%)', 
                    ha='center', va='bottom')

    plt.ylim([0, max(counts)+50])
    plt.tight_layout()
    plt.show()



def bubble_map(gdf_mercator, 
               bubble_sizes_column, 
               zoom_area = [0., 0., 0., 0.],
               max_bubble_size = 300, 
               min_bubble_size = 2,
               title = 'Bubble map of landuses counts around infrastructures'):
    
    '''
    Produce a bubble-map:
    each bubble representing an infrastructures;
    the bigger the bubbles, the more diverse landtypes are present around the infrastructure.

    Input:
        - gdf_mercator (GeoDataFrame): containing at least "geometry" and bubble_sizes_column columns
        - bubble_sizes_column (str): column according to which the size of the bubbles is defined
        - zoom_area (list): list of 4 floats elements, representing the area in which to focus on the map - in mercator coordinates
        - max_bubble_size (int): maximum size of bubbles (optional)
        - min_bubble_size (int): minimum size of bubbles (optional)
        - title (str): plot title (optional)

    Output:
        - Bubble-map plot

    '''
    
    fig, ax = plt.subplots(figsize=(10, 8), subplot_kw={'projection': ccrs.PlateCarree()})
    ax.set_extent(zoom_area)
    ax.add_feature(cfeature.COASTLINE, edgecolor='black', linewidth=0.5)
    ax.add_feature(cfeature.BORDERS, linestyle=':', edgecolor='black', linewidth=0.5)
    ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', linestyle='--')

    # compute bubble sizes based on the length of the sets in LABEL2
    bubble_sizes = gdf_mercator[bubble_sizes_column]

    # normalize bubble sizes for visualization
    normalized_sizes = (bubble_sizes - bubble_sizes.min()) / (bubble_sizes.max() - bubble_sizes.min())
    normalized_sizes = normalized_sizes * (max_bubble_size - min_bubble_size) + min_bubble_size


    for idx, row in gdf_mercator.iterrows():
        plt.scatter(row.geometry.centroid.x, row.geometry.centroid.y, s=normalized_sizes[idx], alpha=0.5, color='green')

    plt.title(title)

    plt.show()



def find_area_covered_by_landuse_within_buffer(landuse_around_infra_gdf1_metric, 
                                                landuse_gdf2_metric, 
                                                unique_id_gdf1, 
                                                label_column_gdf2, 
                                                buffer_radius,
                                                aggregate_by_id = False):
    '''
    Function that associates with each geometry contained in landuse_around_infra_gdf1_metric, 
    all the categories in landuse_gdf2_metric (in column label_column_gdf2) that are found 
    within buffer_radius meters from the geometry themselves, 
    computes buffer total area and the percentage occupied by each landuse available in the buffer.

    Takes as input:
        - landuse_around_infra_gdf1_metric, landuse_gdf2_metric: two geodataframes (in metric crs)
        - unique_id_gdf1: (str) name of infrastructure_gdf1 column containing infrastructure's unique identifiers
        - label_column_gdf2: column in landuse_gdf representing the category to find within the surrounding of each elements in infrastructure_gdf
        - buffer_radius: integer, expressed in meters, used to compute the buffer around each geometry in infrastructure_gdf

    Returns:
    If aggregate_by_id == False:
        - a GeoDataFrame with columns: 
            1. unique_id_gdf1: infrastructure ids (each infrastructure-id repeating as many times as the number of landtypes found within its buffer)
            2. label_column_gdf2: label of the landtype category
            3. area_intersection: total area within buffer with landuse data available (in squared-meters)
            4. landuse_share_by_id: percentage of the total buffer-area (area_intersection) occupied by the landtype (label_column_gdf2) 
                                    within the respective infrastructure-surroundings (unique_id_gdf1)

    If aggregate_by_id == True:
        - a GeoDataFrame with columns: 
            1. unique_id_gdf1: unique identifier of the infrastructure (from infrastructure_gdf1)
            2. landuse_within_{buffer_radius}_meters: column containing set of all categories found within the given buffer
            3. area_landuse_around_id_in_m2: total area within the buffer (in squared-meters)
            4. landuse_share_by_id: each cell contains list of tuples; tuples contain landtype category and the respective percentage of buffer-area occupied 
    '''
        
    # compute buffer
    landuse_around_infra_gdf1_metric['buffered'] = landuse_around_infra_gdf1_metric.buffer(buffer_radius)

    # spatial join
    merged = gpd.sjoin(landuse_gdf2_metric, landuse_around_infra_gdf1_metric, how='inner', predicate='intersects')

    # compute total area of intersection between landuses geometries and infrastructures (which corresponds to total buffer area as CORINE cover all territory)
    merged['area_intersection'] = merged.geometry.intersection(merged.buffered).area

    # group by infrastructure id and landuse, and compute area in m2 occupied by each landtype in each infrastructure-buffer
    grouped = merged.groupby([unique_id_gdf1, label_column_gdf2])['area_intersection'].sum().reset_index()

    # compute total area in infrastructure-buffer
    total_area_by_id = grouped.groupby(unique_id_gdf1)['area_intersection'].sum()

    # compute percentage of total area occupied by each landtype (for each infrastructure-buffer)
    grouped['landuse_share_by_id'] = grouped.apply(lambda row: (row['area_intersection'] / total_area_by_id[row[unique_id_gdf1]]) * 100, axis=1)

    # results
    if aggregate_by_id:
        # aggregate final results (to have a unique id for each row)
        aggregated = grouped.groupby(unique_id_gdf1).agg({
            label_column_gdf2: lambda x: set(x), 
            'area_intersection': 'sum',
            'landuse_share_by_id': lambda x: list(zip(grouped.loc[x.index, label_column_gdf2], x))  # combine landuse and percentage of covered area into tuples
        }).reset_index()


        aggregated.rename(columns={label_column_gdf2: f'landuse_within_{buffer_radius}_meters',
                                'area_intersection': 'area_landuse_around_id_in_m2'}, inplace=True)

        return aggregated
    
    else:
        # returned df with each infrastructure-id repeating for as many rows as the number of landtypes found within its buffer 
        return grouped