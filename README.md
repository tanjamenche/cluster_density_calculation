# Cluster Density Calculation

Python script for calculating cluster densities from polygon-defined regions of interest (ROIs) and corresponding HDF5 cluster data, which were generated from single-molecule localization microscopy (SMLM) experiments, within a specified directory and its subdirectories. 

This script was developed to determine the density of detected clusters within user-defined regions of interest. Parts of this script were developed with assistance from OpenAI's ChatGPT and Cursor AI. The resulting code was reviewed, modified, and validated by the author.


## Overview

The script processes YAML and HDF5 files located in a specified directory and its subdirectories.

For each matching pair of files, it:

1. Reads polygon vertices from a YAML file.

2. Converts the polygon coordinates from pixels to nanometers using a user-defined pixel size.

3. Calculates the polygon area using the shoelace formula.

4. Converts the area from nm² to µm².

5. Reads the corresponding HDF5 file and counts the entries in the `locs` dataset.

6. Matches the YAML and HDF5 files based on their common base name.

7. Calculates the cluster density as:

   **cluster density = number of clusters / ROI area (µm²)**

8. Saves the results to a CSV file named `cluster_density.csv`.

## Requirements

* Python **3.11**
* PyYAML **6.0.1**
* pandas **2.1.4**
* h5py **3.9.0**

## Input Data

The script expects two types of files:

### YAML files

YAML files (.yaml) contain polygon vertex coordinates under the `Vertices` field. The script was tested on YAML files (polygonal ROIs) generated with the [Picasso Software](https://github.com/jungmannlab/picasso) version 7.3 (modul "Render": polygon pick).

### HDF5 files

HDF5 files (.hdf5) containing a list of cluster centers. The script was tested on HDF5 files with cluster centers generated from localization data via the clustering algorithm DBSCAN with the [Picasso Software](https://github.com/jungmannlab/picasso) version 7.3 and with the [PicassoBatchProcess](https://github.com/HeilemannLab/PicassoBatchProcess) Software.  
The number of rows in this dataset is interpreted as the number of clusters.

The script matches the YAML and HDF5 files by their base name. The base name is the filename without the suffix.
For example, consider the following pair of files:

protein1_ROI_picks.yaml

protein1_ROI_dbscan_centers.hdf5

With:

`file_suffix = "_ROI_picks"`

`hdf5_file_suffix = "_ROI_dbscan_centers"`

both files have the base name:

protein1

The script uses this common base name to associate the YAML file with the corresponding HDF5 file.
Because the script uses the base name to match files, each input file pair must have a unique base name within the folders being processed. For example:
```
input_data/ 

├── cell1/ 

│ ├── cell1_protein1_ROI_picks.yaml 

│ └── cell1_protein1_ROI_dbscan_centers.hdf5 

│ 
└── cell2/ 

  ├── cell2_protein1_ROI_picks.yaml 
  
  └── cell2_protein1_ROI_dbscan_centers.hdf5
```
  

## Configuration

Before running the script, edit the following variables in the **User Input Section** in `cluster_density.py`:
```python
folder_path = r"C:\cluster_density\example_data\input_data"  # <-- Set your folder path here: folder_path = r"C:\cluster_density\example_data\input_data"
yaml_file_suffix = "_ROI_picks"                                   # <-- Set your ROI YAML file suffix here: yaml_file_suffix = "_ROI_picks"
hdf5_file_suffix = "_ROI_dbscan_centers"                # <-- Set your HDF5 file suffix here: hdf5_file_suffix = "_ROI_dbscan_centers"
pixel_size_nm = 157.0                                        # <-- Set your pixel size in nanometers here: pixel_size_nm = 157.0
```


## Installation
```PowerShell
conda create --name cluster_density python=3.11
conda activate cluster_density
cd filepath\cluster_density
conda install --file requirements.txt
```

## Usage

1. Place the YAML and HDF5 input files in the specified folder and/or its subfolders.
2. Open `cluster_density.py`.
3. Set `folder_path`, `file_suffix`, `hdf5_file_suffix`, and `pixel_size_nm`.
4. Open environment:
```PowerShell
conda activate cluster_density
```
5. Navigate to the file path, where cluster_density.py is stored:
```PowerShell
cd filepath\cluster_density
```
6. Run:
```PowerShell
python cluster_density.py
```
The script searches recursively through the specified folder and its subfolders.

## Output

The script produces:
```text
cluster_density.csv
```
The output file contains the following columns:

| Column                           | Description                                        |
| -------------------------------- | -------------------------------------------------- |
| `Base Name`                      | Common base name used to match YAML and HDF5 files |
| `YAML File`                      | Name of the YAML input file                        |
| `Area (µm²)`                     | Calculated polygon area                            |
| `HDF5 File`                      | Name of the HDF5 input file                        |
| `Number of clusters`             | Number of rows in the HDF5 `locs` dataset          |
| `Cluster density (clusters/µm²)` | Number of clusters divided by ROI area             |

The output is saved in the input folder path.
