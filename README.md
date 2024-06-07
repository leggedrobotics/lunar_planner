# Lunar Planner

The Lunar Planner is a tool developed for planetary researchers to simplify mission planning for lunar exploration. This repository includes:

* A path planning tool to create paths for a quadruped robot on the lunar surface
* A path analysis tool to analyze paths and extract interesting statistics

This repo comes with examples for a quadruped robot and three different map locations (Aristarchus Irregular Mare Patch, Aristarchus Central Peak and Herodotus Mons).

**Main Contact:** Julia Richter ([jurichter@ethz.ch](mailto:jurichter@ethz.ch?subject=[GitHub:LunarPlanner]))

**Documentation:** [Wiki](https://github.com/leggedrobotics/lunar_planner/wiki)

![Visualization](images/viz.gif)

## Getting Started

### Installation

To install the Lunar Planner, follow these steps:

* Cloning the repository: `git clone https://github.com/leggedrobotics/lunar_planner.git`
* Navigating to the repository: `cd lunar_planner`
* Creating a virtual environment: `python3.8 -m venv env`
* Activating the virtual environment: `source env/bin/activate`
* Installing dependencies: `pip install -r requirements.txt`
* Installing the Lunar Planner package: `pip3 install -e .`

### Usage

#### Entering and Leaving the Virtual Environment

* Activate with `source env/bin/activate`
* Deactivate with `deactivate`

#### Run GUI

* To create a database, run: `python src/user_interface/path_creator.py`
* To analyze paths, run: `python src/user_interface/path_analysis.py`
* To create paths manually, run: `python src/user_interface/path_planning_widget.py`

## Wiki

For more detailed information, please refer to our [wiki](https://github.com/leggedrobotics/lunar_planner/wiki), which includes:

* [Downloading Map Data](https://github.com/leggedrobotics/lunar_planner/wiki/Downloading-Map-Data)
* [Optional Scripts for Map Preprocessing](https://github.com/leggedrobotics/lunar_planner/wiki/Optional-Scripts-for-Map-Preprocessing)
* [Adding Further Maps and Robot Files](https://github.com/leggedrobotics/lunar_planner/wiki/Adding-Further-Maps-and-Robot-Files)

## Citation

If you find this work useful or use it for your research, please consider citing the corresponding work:

```
@inproceedings{richter2024multi,
  title={Multi-Objective Global Path Planning for Lunar Exploration With a Quadruped Robot},
  author={Richter, Julia and Kolvenbach, Hendrik and Valsecchi, Giorgio and Hutter, Marco},
  booktitle={Proceedings of the 2024 iSpaRo Conference},
  year={2024},
  organization={IEEE}
}
```
