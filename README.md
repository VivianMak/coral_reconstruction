# 3D Dynamic Coral Reconstruction with a Light Field Approach

This project is part of CREST Lab advised by Dr. Victoria Preston.

### Motivation
Coral reef systems, especially soft corals, are a very vulnerable ecosystem that changes frequently with each pass of ocean wave movement. Unlike hard corals, soft corals lack a calcium carbonate skeleton, making them particularly sensitive to external environmental factors. Being able to model these ecosystems over multiple expeditions provides a valuable opportunity to compare changes and enhance our understanding of overall ecosystem dynamics and the effects of climate change.

This research project aims to answer the question: <u>__“Through scientific experiments and design, can a single light field camera (Lytro Illum) be used for accurate 3D dynamic reconstruction of soft corals?”__</u>

Light field cameras have been prevalent in urban environment applications, however, there seems to be a lack of continuous research using these cameras and in underwater settings. This sensor provides internal depth map properties and refocusing capabilities unlike traditional cameras. The need for a multi-camera system introduces complexity, especially in uncontrollable underwater environments, that may be resolved with just one light field sensor.

To structure the usefulness of a light field camera for reconstruction, I will integrate and apply scientific background into my design workflow. This includes focusing on areas like: understanding the optics of water refraction, dynamics of soft body corals, and diversity of species. This initial research will scaffold the reconstruction pipeline from knowing what information to capture, to extracting useful data, to building an accurate representation. The project, then can be broken down into the following challenges:
1) Capture and extract useful data from lab setup with scientific context, focusing on
    1) Water optics and the interaction of this sensor through water
    2) Understanding the dynamic motions of soft corals in response to currents across different species
2) Build a reconstruction pipeline by reverse engineering what is needed for a dynamic reconstruction
3) Reconstruct one scene with x timesteps
4) Compare reconstruction with list of useful metrics
5) Adjust the reconstruction algorithm for it to be useful


# CURRENT STATUS
- working on `src/extract_depths.py`
- need to figure out the "squashing" of depth values when converting to a metric depth map


# Dependencies
Requires to install the python lpf reader below.
### Python LPF Reader
Follow instructions on this page to install
>https://github.com/behnam/python-lfp-reader/blob/master/README.rst 

```
$ cd ~/coral_reconstruction/python-lfp-reader/
```
To extract depth maps, raw images, and metadata run the following line.

```
$ ./lfp-file.py export ~/path-to-.LFP file
```
This will create the following files:

`IMG_0001.LFP_lfp_meta.json`
`IMG_0001.LFP__1e21bd1fd7ca64a915cf2579359ad5509aa3d6ec.data`
`IMG_0116.LFP__46512476093ff1d160623fff06bba22991e121d0.data`

Useful note: to know which file is the depth map or raw image, check the `.json` file.


# Repo Structure
```
Project/
├── data_raw/
│   ├── IMG_0001.LFP
│   ├── IMG_0002.LFP
│   └── IMG_0003.LFP
├── data_extracted/
│   ├── IMG_0001/
│   │   ├── IMG_0001.LFP__lfp_meta.json
│   │   ├── IMG_0001.LFP__a2f4b.data
│   ├── IMG_0002/
│   │   ├── IMG_0002.LFP__lfp_meta.json
│   │   └── IMG_0002.LFP__c1a7e.data
│   └── IMG_0003/
│       ├── IMG_0003.LFP__lfp_meta.json
│       └── IMG_0003.LFP__b8d2f.data
├── src/
│   ├── extract_depths.py
├── README.md
└── requirements.txt

```