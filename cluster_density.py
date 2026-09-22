"""
Cluster Density Calculation

This script calculates the density of detected clusters (from single-molecule localization microscopy (SMLM) experiments) within user-defined polygonal regions of interest (ROIs). 
It processes all YAML and HDF5 files in a specified folder (and its subfolders) that match given file suffixes.
It reads polygon vertices from each YAML file, scales them by a user-provided pixel size (in nanometers),
calculates the area of each polygon (in square micrometers), and counts the number of clusters (rows) in the 'locs' dataset of each HDF5 file.
The script then matches files by their base name, calculates the cluster density (number of clusters per µm²), and saves all results to a CSV file. 
Parts of this script were developed with assistance from OpenAI's ChatGPT and Cursor AI. The resulting code was reviewed, modified, and validated by the author.


Author: Tanja Menche
Affiliation: Research group of Mike Heilemann, Goethe University Frankfurt am Main, Germany
Version: v1.0.0
Date: 2026-09-22


User Inputs (edit the variables below):
---------------------------------------
- folder_path: The root directory containing the YAML and HDF5 files. The script searches this folder and all of its subfolders for files matching YAML and HDF5 files.
- yaml_file_suffix: The suffix that the YAML files end with (e.g., '_ROI_picks').
- hdf5_file_suffix: The suffix that the HDF5 files end with (e.g., '_ROI_dbscan_centers.hdf5').
- pixel_size_nm: The pixel size in nanometers.

Information about the input data:
--------------------------------
The HDF5 files contain the cluster centers of the ROI. The cluster centers are used to calculate the number of clusters in the ROI.
The YAML files contain the polygon vertices of the ROI. The polygon vertices are used to calculate the area of the ROI.
Corresponding HDF5 files and YAML files can be generated with the Picasso Software version (https://github.com/jungmannlab/picasso) version 7.3 from SMLM data (find more information in the README.md file).
The script matches the YAML and HDF5 files by their base name. The base name is the filename without the suffix.
For example, consider the following pair of files:
protein1_ROI_picks.yaml
protein1_ROI_dbscan_centers.hdf5
With:
yaml_file_suffix = "_ROI_picks"
hdf5_file_suffix = "_ROI_dbscan_centers"
both files have the base name:
protein1
The script uses this common base name to associate the YAML file with the corresponding HDF5 file.
Because the script uses the base name to match files, each input file pair must have a unique base name within the folders being processed.


How to use:
-----------
1. Edit the variables in the User Input Section below to match your data and requirements.
2. Run the script.
3. The script will process the files and output a CSV file named 'cluster_density.csv' in the specified folder.
"""

# --- User Input Section (edit these variables) ---
folder_path = r"C:\cluster_density\example_data\input_data"  # <-- Set your folder path here; example: folder_path = r"C:\cluster_density\example_data\input_data"
yaml_file_suffix = "_ROI_picks"                     # <-- Set your ROI YAML file suffix here; example: yaml_file_suffix = "_ROI_picks"
hdf5_file_suffix = "_ROI_dbscan_centers"            # <-- Set your HDF5 file suffix here, example; hdf5_file_suffix = "_ROI_dbscan_centers"
pixel_size_nm = 157.0                               # <-- Set your pixel size in nanometers here; example: pixel_size_nm = 157.0



import yaml
import os
import glob
import pandas as pd
import h5py

def calculate_polygon_area(vertices):
    """
    Calculate the area of a polygon using the Shoelace formula.
    :param vertices: List of vertices [(x1, y1), (x2, y2), ...]
    :return: Area of the polygon
    """
    n = len(vertices)
    area = 0.0
    for i in range(n):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % n]  # Wrap around to the first vertex
        area += x1 * y2 - y1 * x2
    return abs(area) / 2.0

def read_yaml_file(file_path, pixel_size_nm):
    """
    Read vertices from a YAML file and scale them by the pixel size.
    :param file_path: Path to the YAML file
    :param pixel_size_nm: Size of each pixel in nanometers
    :return: List of vertices [(x1, y1), (x2, y2), ...] scaled by pixel size
    """
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
        # Flatten the nested structure of vertices and scale by pixel size
        return [
            (coord[0] * pixel_size_nm, coord[1] * pixel_size_nm)
            for coord_group in data['Vertices']
            for coord in coord_group
        ]

def get_base_name(filename, suffix):
    """Remove the suffix and extension from the filename to get the base name."""
    if filename.endswith(suffix):
        return filename[: -len(suffix)]
    return filename

def process_yaml_files(folder_path, yaml_file_suffix, pixel_size_nm):
    """
    Process all YAML files and return a dict: base_name -> (yaml_file, area)
    """
    search_pattern = f"**/*{yaml_file_suffix}.yaml"
    matching_files = glob.glob(os.path.join(folder_path, search_pattern), recursive=True)
    results = {}

    for yaml_file in matching_files:
        try:
            vertices = read_yaml_file(yaml_file, pixel_size_nm)
            area_nm2 = calculate_polygon_area(vertices)
            area_um2 = area_nm2 / 1e6
            file_name = os.path.basename(yaml_file)
            base_name = get_base_name(file_name, f"{yaml_file_suffix}.yaml")
            results[base_name] = (file_name, f"{area_um2:.6f}")
        except Exception as e:
            print(f"Error processing file {yaml_file}: {str(e)}")
    return results

def process_hdf5_files(folder_path, hdf5_file_suffix):
    """
    Process all HDF5 files and return a dict: base_name -> (hdf5_file, n_rows)
    """
    search_pattern = f"**/*{hdf5_file_suffix}.hdf5"
    matching_files = glob.glob(os.path.join(folder_path, search_pattern), recursive=True)
    results = {}

    for hdf5_file in matching_files:
        try:
            with h5py.File(hdf5_file, 'r') as f:
                if "locs" in f:
                    locs_dataset = f["locs"]
                    n_rows = locs_dataset.shape[0]
                    file_name = os.path.basename(hdf5_file)
                    base_name = get_base_name(file_name, f"{hdf5_file_suffix}.hdf5")
                    results[base_name] = (file_name, n_rows)
        except Exception as e:
            print(f"Error processing file {hdf5_file}: {str(e)}")
    return results

def merge_and_save_results(yaml_results, hdf5_results, folder_path):
    """
    Merge the results from YAML and HDF5 processing and save to a single CSV.
    Include all base names found in either YAML or HDF5 files.
    Also calculate cluster density (number of clusters / area).
    """
    all_base_names = set(yaml_results.keys()) | set(hdf5_results.keys())
    merged_rows = []
    for base in sorted(all_base_names):
        yaml_file, area = yaml_results.get(base, ("", ""))
        hdf5_file, n_clusters = hdf5_results.get(base, ("", ""))
        # Calculate cluster density if both area and n_clusters are present and valid
        try:
            area_val = float(area) if area != "" else None
            n_clusters_val = int(n_clusters) if n_clusters != "" else None
            if area_val and n_clusters_val is not None and area_val > 0:
                cluster_density = n_clusters_val / area_val
                cluster_density_str = f"{cluster_density:.6f}"
            else:
                cluster_density_str = ""
        except Exception:
            cluster_density_str = ""
        merged_rows.append({
            "Base Name": base,
            "YAML File": yaml_file,
            "Area (µm²)": area,
            "HDF5 File": hdf5_file,
            "Number of clusters": n_clusters,
            "Cluster density (clusters/µm²)": cluster_density_str
        })
    df = pd.DataFrame(merged_rows)
    output_path = os.path.join(folder_path, 'cluster_density.csv')
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"Merged results saved to: {output_path}")

if __name__ == "__main__":
    yaml_results = process_yaml_files(folder_path, yaml_file_suffix, pixel_size_nm)
    hdf5_results = process_hdf5_files(folder_path, hdf5_file_suffix)
    merge_and_save_results(yaml_results, hdf5_results, folder_path)
