# coral_reconstruction

# Resources Used
## Python LPF Reader
Follow instructions on this page to install
>https://github.com/behnam/python-lfp-reader/blob/master/README.rst 

To extract depth maps, raw images, and metadata run the following line.

`$ cd ~/coral_reconstruction.python-lfp-reader/`

`$ ./lfp-file.py export ~/path to .LFP file`

This will create the following files:

`IMG_0001.LFP_lfp_meta.json`
`IMG_0001.LFP__1e21bd1fd7ca64a915cf2579359ad5509aa3d6ec.data`
`IMG_0116.LFP__46512476093ff1d160623fff06bba22991e121d0.data`

Useful note: to know which file is the depth map or raw image, check the `.json` file.